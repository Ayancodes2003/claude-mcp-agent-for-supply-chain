"""
Interface to the Google Gemini API for the warehouse simulation.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import google.generativeai as genai
from dotenv import load_dotenv


class GeminiInterface:
    """Interface to the Google Gemini API for the warehouse simulation."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        # Load environment variables
        load_dotenv("gemini.env")
        
        # Set up API key and model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key not provided and not found in environment variables")
        
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        
        # Initialize Gemini
        genai.configure(api_key=self.api_key)
        
        # Set up logger
        self.logger = logger or logging.getLogger(__name__)
    
    def ask(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        warehouse_state: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Ask Gemini a question and get a response.
        
        Args:
            prompt: The user prompt to send to Gemini
            system_prompt: Optional system prompt to provide context
            warehouse_state: Optional warehouse state to include in the prompt
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Dict containing Gemini's response and metadata
        """
        try:
            # Construct the system prompt if not provided
            if system_prompt is None:
                system_prompt = self._get_default_system_prompt()
            
            # Add warehouse state to the prompt if provided
            full_prompt = system_prompt
            if warehouse_state:
                state_json = json.dumps(warehouse_state, indent=2)
                full_prompt += f"\n\nCurrent warehouse state:\n```json\n{state_json}\n```"
            
            full_prompt += f"\n\nUser query: {prompt}"
            
            # Log the request
            self.logger.info(f"Sending request to Gemini ({self.model})")
            self.logger.debug(f"Full prompt: {full_prompt}")
            
            # Create a Gemini model
            model = genai.GenerativeModel(self.model)
            
            # Send request to Gemini
            response = model.generate_content(full_prompt, generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40
            })
            
            # Extract the response content
            content = response.text
            
            # Log the response
            self.logger.info(f"Received response from Gemini ({len(content)} chars)")
            self.logger.debug(f"Response: {content}")
            
            # Parse the response to extract actions if possible
            actions = self._extract_actions(content)
            
            return {
                "prompt": prompt,
                "response": content,
                "actions": actions,
                "model": self.model,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error querying Gemini: {str(e)}")
            return {
                "prompt": prompt,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for Gemini."""
        return """
        You are an AI assistant managing a smart warehouse system. Your role is to analyze the warehouse state and suggest optimal actions for inventory management, AGV routing, and order processing.

        When responding, follow these guidelines:
        1. Analyze the current warehouse state provided in JSON format
        2. Identify any issues that need attention (low inventory, pending orders, etc.)
        3. Suggest specific actions to address these issues
        4. Format your action suggestions in a structured way that can be parsed by the system

        For action suggestions, use the following JSON format within your response:
        ```json
        {
          "actions": [
            {
              "type": "move_agv",
              "agent": "agv",
              "action": "move_agv",
              "agv_id": "AGV001",
              "destination": "storage_a"
            },
            {
              "type": "restock_item",
              "agent": "inventory",
              "action": "add_inventory",
              "product_id": "P001",
              "quantity": 10
            }
          ]
        }
        ```

        Available action types:
        - move_agv: Move an AGV to a new location
        - pick_item: Pick an item from inventory using an AGV
        - restock_item: Restock an item in inventory
        - process_order: Update the status of an order
        - charge_agv: Charge an AGV's battery

        Available agents:
        - inventory: For inventory-related actions
        - agv: For AGV-related actions
        - restock: For restocking operations
        - warehouse: For direct warehouse actions

        Be specific and practical in your suggestions, considering the current state of the warehouse.
        """
    
    def _extract_actions(self, response: str) -> List[Dict[str, Any]]:
        """
        Extract structured actions from Gemini's response.
        
        Looks for JSON blocks in the response that contain action definitions.
        """
        actions = []
        
        try:
            # Look for JSON blocks in the response
            json_blocks = []
            in_json_block = False
            current_block = []
            
            for line in response.split('\n'):
                if line.strip() == '```json' or line.strip() == '```':
                    if in_json_block:
                        # End of a JSON block
                        json_blocks.append('\n'.join(current_block))
                        current_block = []
                    in_json_block = not in_json_block
                elif in_json_block:
                    current_block.append(line)
            
            # Parse each JSON block
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    if "actions" in data and isinstance(data["actions"], list):
                        actions.extend(data["actions"])
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse JSON block: {block}")
            
            # Also try to find a complete JSON object in the response
            if not actions:
                # Look for content between curly braces
                import re
                json_matches = re.findall(r'\{[^{}]*\}', response)
                for match in json_matches:
                    try:
                        data = json.loads(match)
                        if "actions" in data and isinstance(data["actions"], list):
                            actions.extend(data["actions"])
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            self.logger.error(f"Error extracting actions from response: {str(e)}")
        
        return actions
