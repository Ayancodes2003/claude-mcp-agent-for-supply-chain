"""
Restock Agent for the warehouse simulation.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from simulation.warehouse import Warehouse
from simulation.inventory import InventoryItem
from simulation.agv import AGVStatus


class RestockAgent:
    """
    Agent responsible for restocking inventory in the warehouse.
    Monitors inventory levels and coordinates restocking operations.
    """
    
    def __init__(self, warehouse: Warehouse, logger: Optional[logging.Logger] = None):
        self.warehouse = warehouse
        self.inventory_manager = warehouse.inventory_manager
        self.agv_manager = warehouse.agv_manager
        self.logger = logger or logging.getLogger(__name__)
    
    def get_restock_needs(self) -> List[Dict[str, Any]]:
        """Get a list of items that need to be restocked."""
        items_below_threshold = self.inventory_manager.get_items_below_threshold()
        
        restock_needs = []
        for item in items_below_threshold:
            restock_amount = item.max_capacity - item.quantity
            restock_needs.append({
                "product_id": item.product_id,
                "name": item.name,
                "current_quantity": item.quantity,
                "min_threshold": item.min_threshold,
                "restock_amount": restock_amount,
                "location": item.location,
                "priority": self._calculate_restock_priority(item)
            })
        
        # Sort by priority (higher priority first)
        restock_needs.sort(key=lambda x: x["priority"], reverse=True)
        
        return restock_needs
    
    def _calculate_restock_priority(self, item: InventoryItem) -> int:
        """
        Calculate the priority for restocking an item.
        
        Priority is higher when:
        - Quantity is zero or very low
        - Item is far below its threshold
        """
        if item.quantity == 0:
            # Highest priority if completely out of stock
            return 10
        
        # Calculate how far below threshold as a percentage
        threshold_percentage = (item.min_threshold - item.quantity) / item.min_threshold
        
        # Scale to a priority between 1-9
        return min(9, max(1, int(threshold_percentage * 10)))
    
    def plan_restock_operation(self, product_id: str) -> Dict[str, Any]:
        """Plan a restock operation for a specific product."""
        item = self.inventory_manager.get_item(product_id)
        
        if not item:
            self.logger.warning(f"Product {product_id} not found")
            return {
                "success": False,
                "message": f"Product {product_id} not found"
            }
        
        if not item.needs_restock():
            self.logger.info(f"Product {product_id} does not need restocking")
            return {
                "success": True,
                "message": f"Product {product_id} does not need restocking",
                "restock_needed": False
            }
        
        # Find available AGVs
        available_agvs = self.agv_manager.get_available_agvs()
        
        if not available_agvs:
            self.logger.warning("No available AGVs for restocking")
            return {
                "success": False,
                "message": "No available AGVs for restocking"
            }
        
        # Select the first available AGV (in a real system, we would use more sophisticated selection)
        selected_agv = available_agvs[0]
        
        # Calculate restock amount
        restock_amount = item.max_capacity - item.quantity
        
        # Create restock plan
        restock_plan = {
            "success": True,
            "restock_needed": True,
            "product_id": product_id,
            "product_name": item.name,
            "current_quantity": item.quantity,
            "restock_amount": restock_amount,
            "location": item.location,
            "agv_id": selected_agv.agv_id,
            "agv_name": selected_agv.name,
            "agv_location": selected_agv.location,
            "steps": [
                {
                    "step": "move_agv_to_receiving",
                    "agv_id": selected_agv.agv_id,
                    "destination": "receiving"
                },
                {
                    "step": "load_inventory",
                    "agv_id": selected_agv.agv_id,
                    "product_id": product_id,
                    "quantity": restock_amount
                },
                {
                    "step": "move_agv_to_storage",
                    "agv_id": selected_agv.agv_id,
                    "destination": item.location
                },
                {
                    "step": "unload_inventory",
                    "agv_id": selected_agv.agv_id,
                    "product_id": product_id,
                    "quantity": restock_amount
                }
            ]
        }
        
        self.logger.info(f"Created restock plan for {product_id}")
        return restock_plan
    
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a restock-related action."""
        action_type = action.get("action")
        
        if action_type == "get_restock_needs":
            restock_needs = self.get_restock_needs()
            
            self.logger.info(f"Found {len(restock_needs)} items that need restocking")
            return {
                "success": True,
                "restock_needs": restock_needs
            }
        
        elif action_type == "plan_restock":
            product_id = action.get("product_id")
            
            if product_id:
                restock_plan = self.plan_restock_operation(product_id)
                return restock_plan
            else:
                self.logger.warning("No product_id provided for plan_restock action")
                return {
                    "success": False,
                    "message": "No product_id provided"
                }
        
        elif action_type == "execute_restock":
            product_id = action.get("product_id")
            agv_id = action.get("agv_id")
            restock_amount = action.get("restock_amount")
            
            if not product_id or not agv_id or not restock_amount:
                self.logger.warning("Missing parameters for execute_restock action")
                return {
                    "success": False,
                    "message": "Missing parameters (product_id, agv_id, or restock_amount)"
                }
            
            # Get the item and AGV
            item = self.inventory_manager.get_item(product_id)
            agv = self.agv_manager.get_agv(agv_id)
            
            if not item:
                self.logger.warning(f"Product {product_id} not found")
                return {
                    "success": False,
                    "message": f"Product {product_id} not found"
                }
            
            if not agv:
                self.logger.warning(f"AGV {agv_id} not found")
                return {
                    "success": False,
                    "message": f"AGV {agv_id} not found"
                }
            
            # Check if AGV is available
            if agv.status != AGVStatus.IDLE:
                self.logger.warning(f"AGV {agv_id} is not idle (current status: {agv.status})")
                return {
                    "success": False,
                    "message": f"AGV {agv_id} is not idle (current status: {agv.status})"
                }
            
            # Execute restock steps
            
            # 1. Move AGV to receiving
            self.logger.info(f"Moving AGV {agv_id} to receiving")
            move_to_receiving = self.agv_manager.move_agv(agv_id, "receiving")
            
            if not move_to_receiving:
                self.logger.warning(f"Failed to move AGV {agv_id} to receiving")
                return {
                    "success": False,
                    "message": f"Failed to move AGV {agv_id} to receiving"
                }
            
            # 2. Load inventory onto AGV
            self.logger.info(f"Loading {restock_amount} units of {product_id} onto AGV {agv_id}")
            # In a real system, this would involve getting the inventory from an external source
            # For this simulation, we'll just load it directly onto the AGV
            load_success = self.agv_manager.load_agv(agv_id, product_id, restock_amount)
            
            if not load_success:
                self.logger.warning(f"Failed to load {restock_amount} units of {product_id} onto AGV {agv_id}")
                return {
                    "success": False,
                    "message": f"Failed to load {restock_amount} units of {product_id} onto AGV {agv_id}"
                }
            
            # 3. Move AGV to storage location
            self.logger.info(f"Moving AGV {agv_id} to {item.location}")
            move_to_storage = self.agv_manager.move_agv(agv_id, item.location)
            
            if not move_to_storage:
                self.logger.warning(f"Failed to move AGV {agv_id} to {item.location}")
                return {
                    "success": False,
                    "message": f"Failed to move AGV {agv_id} to {item.location}"
                }
            
            # 4. Unload inventory from AGV to storage
            self.logger.info(f"Unloading {restock_amount} units of {product_id} from AGV {agv_id}")
            unloaded_product, unloaded_quantity = self.agv_manager.unload_agv(agv_id, product_id, restock_amount)
            
            if unloaded_quantity > 0:
                # Add to inventory
                add_success = self.inventory_manager.add_quantity(product_id, unloaded_quantity)
                
                if add_success:
                    self.logger.info(f"Successfully restocked {unloaded_quantity} units of {product_id}")
                    return {
                        "success": True,
                        "product_id": product_id,
                        "restocked_quantity": unloaded_quantity,
                        "new_quantity": self.inventory_manager.get_item(product_id).quantity,
                        "agv_id": agv_id
                    }
                else:
                    self.logger.warning(f"Failed to add {unloaded_quantity} units of {product_id} to inventory")
                    return {
                        "success": False,
                        "message": f"Failed to add {unloaded_quantity} units of {product_id} to inventory"
                    }
            else:
                self.logger.warning(f"Failed to unload {product_id} from AGV {agv_id}")
                return {
                    "success": False,
                    "message": f"Failed to unload {product_id} from AGV {agv_id}"
                }
        
        else:
            self.logger.warning(f"Unknown restock action type: {action_type}")
            return {
                "success": False,
                "message": f"Unknown action type: {action_type}"
            }
