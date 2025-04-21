"""
Coordinator Agent for the warehouse simulation.
"""
from typing import Dict, List, Any, Optional
import logging
import json
from datetime import datetime

from simulation.warehouse import Warehouse
from agents.inventory_manager import InventoryManagerAgent
from agents.agv_planner import AGVPlannerAgent
from agents.restock_agent import RestockAgent


class CoordinatorAgent:
    """
    Coordinator agent that orchestrates the actions of other agents.
    Acts as the central decision-making component that delegates tasks to specialized agents.
    """
    
    def __init__(
        self,
        warehouse: Warehouse,
        log_file: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.warehouse = warehouse
        self.logger = logger or logging.getLogger(__name__)
        self.log_file = log_file
        
        # Initialize specialized agents
        self.inventory_agent = InventoryManagerAgent(warehouse, self.logger)
        self.agv_agent = AGVPlannerAgent(warehouse, self.logger)
        self.restock_agent = RestockAgent(warehouse, self.logger)
        
        # Action history
        self.action_history = []
    
    def process_query(self, query: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a natural language query and return a response.
        This is a placeholder for the Claude integration.
        """
        self.logger.info(f"Received query: {query}")
        
        # In a real implementation, this would call Claude
        # For now, we'll just return a simple response
        return {
            "query": query,
            "response": "This is a placeholder response. In the real implementation, this would be processed by Claude.",
            "timestamp": datetime.now().isoformat()
        }
    
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an action by delegating to the appropriate agent."""
        action_type = action.get("type")
        agent_type = action.get("agent")
        
        if not action_type:
            self.logger.warning("No action type specified")
            return {
                "success": False,
                "message": "No action type specified"
            }
        
        # Log the action
        self._log_action(action)
        
        # Route to the appropriate agent
        if agent_type == "inventory":
            result = self.inventory_agent.execute_action(action)
        elif agent_type == "agv":
            result = self.agv_agent.execute_action(action)
        elif agent_type == "restock":
            result = self.restock_agent.execute_action(action)
        elif agent_type == "warehouse":
            # Direct warehouse actions
            result = self.warehouse.process_action(action)
        else:
            self.logger.warning(f"Unknown agent type: {agent_type}")
            result = {
                "success": False,
                "message": f"Unknown agent type: {agent_type}"
            }
        
        # Log the result
        self._log_result(action, result)
        
        return result
    
    def execute_plan(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a sequence of actions as a plan."""
        results = []
        
        for action in plan:
            result = self.execute_action(action)
            results.append(result)
            
            # Stop execution if an action fails
            if not result.get("success", False):
                self.logger.warning(f"Plan execution stopped due to failed action: {action}")
                break
        
        return results
    
    def get_warehouse_state(self) -> Dict[str, Any]:
        """Get the current state of the warehouse."""
        return self.warehouse.get_warehouse_state()
    
    def get_action_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the recent action history."""
        return self.action_history[-limit:] if limit > 0 else self.action_history
    
    def _log_action(self, action: Dict[str, Any]) -> None:
        """Log an action to the action history and log file."""
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "type": "action",
            "action": action
        }
        
        self.action_history.append(log_entry)
        
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception as e:
                self.logger.error(f"Failed to write to log file: {str(e)}")
    
    def _log_result(self, action: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Log an action result to the action history and log file."""
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "type": "result",
            "action": action,
            "result": result
        }
        
        self.action_history.append(log_entry)
        
        if self.log_file:
            try:
                with open(self.log_file, 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
            except Exception as e:
                self.logger.error(f"Failed to write to log file: {str(e)}")
    
    def analyze_warehouse_state(self) -> Dict[str, Any]:
        """
        Analyze the current warehouse state and provide recommendations.
        This would typically be done by Claude in the real implementation.
        """
        state = self.get_warehouse_state()
        
        # Get items that need restocking
        items_below_threshold = [
            item for item_id, item in state["inventory"].items()
            if item["needs_restock"]
        ]
        
        # Get available AGVs
        available_agvs = [
            agv for agv_id, agv in state["agvs"].items()
            if agv["is_available"]
        ]
        
        # Get pending orders
        pending_orders = [
            order for order_id, order in state.get("orders", {}).items()
            if order["status"] == "pending"
        ]
        
        # Generate recommendations
        recommendations = []
        
        if items_below_threshold:
            recommendations.append({
                "type": "restock",
                "message": f"{len(items_below_threshold)} items need restocking",
                "items": items_below_threshold
            })
        
        if not available_agvs:
            recommendations.append({
                "type": "agv_availability",
                "message": "No AGVs are currently available",
                "suggestion": "Consider freeing up AGVs or adding more to the fleet"
            })
        
        if pending_orders:
            recommendations.append({
                "type": "order_processing",
                "message": f"{len(pending_orders)} orders are pending",
                "orders": pending_orders
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations,
            "summary": {
                "inventory_items": len(state["inventory"]),
                "items_below_threshold": len(items_below_threshold),
                "agvs": len(state["agvs"]),
                "available_agvs": len(available_agvs),
                "pending_orders": len(pending_orders)
            }
        }
