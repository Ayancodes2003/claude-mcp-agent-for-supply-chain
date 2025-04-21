"""
AGV Planner Agent for the warehouse simulation.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from simulation.agv import AGVManager, AGVStatus
from simulation.warehouse import Warehouse


class AGVPlannerAgent:
    """
    Agent responsible for planning and managing AGV movements in the warehouse.
    Handles AGV assignments, route planning, and task scheduling.
    """
    
    def __init__(self, warehouse: Warehouse, logger: Optional[logging.Logger] = None):
        self.warehouse = warehouse
        self.agv_manager = warehouse.agv_manager
        self.logger = logger or logging.getLogger(__name__)
    
    def get_agv_status(self) -> Dict[str, Any]:
        """Get the current status of all AGVs."""
        agvs = self.agv_manager.get_all_agvs()
        
        return {
            "total_agvs": len(agvs),
            "available_agvs": len(self.agv_manager.get_available_agvs()),
            "agvs": [agv.to_dict() for agv in agvs],
            "timestamp": datetime.now().isoformat()
        }
    
    def find_nearest_available_agv(self, location: str) -> Optional[Dict[str, Any]]:
        """Find the nearest available AGV to a location."""
        available_agvs = self.agv_manager.get_available_agvs()
        
        if not available_agvs:
            return None
        
        # In a real system, we would calculate actual distances
        # For this simulation, we'll just return the first available AGV
        nearest_agv = available_agvs[0]
        
        return {
            "agv_id": nearest_agv.agv_id,
            "name": nearest_agv.name,
            "current_location": nearest_agv.location,
            "battery_level": nearest_agv.battery_level
        }
    
    def plan_route(self, agv_id: str, destination: str) -> List[str]:
        """
        Plan a route for an AGV from its current location to a destination.
        
        In a real system, this would use pathfinding algorithms.
        For this simulation, we'll just return a direct route.
        """
        agv = self.agv_manager.get_agv(agv_id)
        if not agv:
            return []
        
        # Simple direct route (in a real system, this would be more complex)
        return [agv.location, destination]
    
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an AGV-related action."""
        action_type = action.get("action")
        
        if action_type == "move_agv":
            agv_id = action.get("agv_id")
            destination = action.get("destination")
            
            if agv_id and destination:
                agv = self.agv_manager.get_agv(agv_id)
                
                if not agv:
                    self.logger.warning(f"AGV {agv_id} not found")
                    return {
                        "success": False,
                        "message": f"AGV {agv_id} not found"
                    }
                
                if agv.status != AGVStatus.IDLE:
                    self.logger.warning(f"AGV {agv_id} is not idle (current status: {agv.status})")
                    return {
                        "success": False,
                        "message": f"AGV {agv_id} is not idle (current status: {agv.status})"
                    }
                
                if destination not in self.warehouse.locations:
                    self.logger.warning(f"Invalid destination: {destination}")
                    return {
                        "success": False,
                        "message": f"Invalid destination: {destination}"
                    }
                
                # Plan route (in a real system, this would be more complex)
                route = self.plan_route(agv_id, destination)
                
                # Move the AGV
                success = self.agv_manager.move_agv(agv_id, destination)
                
                if success:
                    self.logger.info(f"Moved AGV {agv_id} to {destination}")
                    return {
                        "success": True,
                        "agv_id": agv_id,
                        "from_location": route[0],
                        "to_location": destination,
                        "route": route
                    }
                else:
                    self.logger.warning(f"Failed to move AGV {agv_id} to {destination}")
                    return {
                        "success": False,
                        "message": f"Failed to move AGV {agv_id} to {destination}"
                    }
            else:
                self.logger.warning("Missing agv_id or destination for move_agv action")
                return {
                    "success": False,
                    "message": "Missing agv_id or destination"
                }
        
        elif action_type == "charge_agv":
            agv_id = action.get("agv_id")
            amount = action.get("amount", 100.0)
            
            if agv_id:
                agv = self.agv_manager.get_agv(agv_id)
                
                if not agv:
                    self.logger.warning(f"AGV {agv_id} not found")
                    return {
                        "success": False,
                        "message": f"AGV {agv_id} not found"
                    }
                
                # Check if AGV is at a charging station
                if agv.location != "charging_station":
                    # First move the AGV to a charging station
                    move_success = self.agv_manager.move_agv(agv_id, "charging_station")
                    if not move_success:
                        self.logger.warning(f"Failed to move AGV {agv_id} to charging station")
                        return {
                            "success": False,
                            "message": f"Failed to move AGV {agv_id} to charging station"
                        }
                
                # Charge the AGV
                success = self.agv_manager.charge_agv(agv_id, amount)
                
                if success:
                    self.logger.info(f"Charged AGV {agv_id} to {agv.battery_level}%")
                    return {
                        "success": True,
                        "agv_id": agv_id,
                        "new_battery_level": agv.battery_level
                    }
                else:
                    self.logger.warning(f"Failed to charge AGV {agv_id}")
                    return {
                        "success": False,
                        "message": f"Failed to charge AGV {agv_id}"
                    }
            else:
                self.logger.warning("Missing agv_id for charge_agv action")
                return {
                    "success": False,
                    "message": "Missing agv_id"
                }
        
        elif action_type == "load_agv":
            agv_id = action.get("agv_id")
            product_id = action.get("product_id")
            quantity = action.get("quantity", 1)
            
            if agv_id and product_id and quantity > 0:
                # Get the AGV
                agv = self.agv_manager.get_agv(agv_id)
                
                if not agv:
                    self.logger.warning(f"AGV {agv_id} not found")
                    return {
                        "success": False,
                        "message": f"AGV {agv_id} not found"
                    }
                
                # Get the inventory item
                item = self.warehouse.inventory_manager.get_item(product_id)
                
                if not item:
                    self.logger.warning(f"Product {product_id} not found")
                    return {
                        "success": False,
                        "message": f"Product {product_id} not found"
                    }
                
                # Check if AGV is at the same location as the item
                if agv.location != item.location:
                    # Move the AGV to the item's location
                    move_success = self.agv_manager.move_agv(agv_id, item.location)
                    if not move_success:
                        self.logger.warning(f"Failed to move AGV {agv_id} to {item.location}")
                        return {
                            "success": False,
                            "message": f"Failed to move AGV {agv_id} to {item.location}"
                        }
                
                # Check if there's enough inventory
                if item.quantity < quantity:
                    self.logger.warning(f"Not enough inventory of {product_id} (requested: {quantity}, available: {item.quantity})")
                    return {
                        "success": False,
                        "message": f"Not enough inventory of {product_id} (requested: {quantity}, available: {item.quantity})"
                    }
                
                # Remove from inventory
                inventory_success = self.warehouse.inventory_manager.remove_quantity(product_id, quantity)
                
                if not inventory_success:
                    self.logger.warning(f"Failed to remove {quantity} units of {product_id} from inventory")
                    return {
                        "success": False,
                        "message": f"Failed to remove {quantity} units of {product_id} from inventory"
                    }
                
                # Load onto AGV
                load_success = self.agv_manager.load_agv(agv_id, product_id, quantity)
                
                if load_success:
                    self.logger.info(f"Loaded {quantity} units of {product_id} onto AGV {agv_id}")
                    return {
                        "success": True,
                        "agv_id": agv_id,
                        "product_id": product_id,
                        "quantity": quantity,
                        "location": agv.location
                    }
                else:
                    # Revert inventory change if AGV loading fails
                    self.warehouse.inventory_manager.add_quantity(product_id, quantity)
                    self.logger.warning(f"Failed to load {quantity} units of {product_id} onto AGV {agv_id}")
                    return {
                        "success": False,
                        "message": f"Failed to load {quantity} units of {product_id} onto AGV {agv_id}"
                    }
            else:
                self.logger.warning("Invalid parameters for load_agv action")
                return {
                    "success": False,
                    "message": "Invalid parameters for load_agv action"
                }
        
        elif action_type == "unload_agv":
            agv_id = action.get("agv_id")
            product_id = action.get("product_id")
            quantity = action.get("quantity")
            
            if agv_id and product_id:
                # Get the AGV
                agv = self.agv_manager.get_agv(agv_id)
                
                if not agv:
                    self.logger.warning(f"AGV {agv_id} not found")
                    return {
                        "success": False,
                        "message": f"AGV {agv_id} not found"
                    }
                
                # Check if the AGV has the product
                if product_id not in agv.current_load:
                    self.logger.warning(f"AGV {agv_id} does not have product {product_id}")
                    return {
                        "success": False,
                        "message": f"AGV {agv_id} does not have product {product_id}"
                    }
                
                # Unload from AGV
                unloaded_product, unloaded_quantity = self.agv_manager.unload_agv(agv_id, product_id, quantity)
                
                if unloaded_quantity > 0:
                    # Add to inventory
                    item = self.warehouse.inventory_manager.get_item(product_id)
                    
                    if item:
                        # Add to existing inventory
                        add_success = self.warehouse.inventory_manager.add_quantity(product_id, unloaded_quantity)
                        
                        if add_success:
                            self.logger.info(f"Unloaded {unloaded_quantity} units of {product_id} from AGV {agv_id}")
                            return {
                                "success": True,
                                "agv_id": agv_id,
                                "product_id": product_id,
                                "quantity": unloaded_quantity,
                                "location": agv.location
                            }
                        else:
                            # Revert AGV change if inventory update fails
                            self.agv_manager.load_agv(agv_id, product_id, unloaded_quantity)
                            self.logger.warning(f"Failed to add {unloaded_quantity} units of {product_id} to inventory")
                            return {
                                "success": False,
                                "message": f"Failed to add {unloaded_quantity} units of {product_id} to inventory"
                            }
                    else:
                        # Create new inventory item
                        new_item = self.warehouse.inventory_manager.add_item({
                            "product_id": product_id,
                            "name": f"Product {product_id}",
                            "quantity": unloaded_quantity,
                            "location": agv.location,
                            "min_threshold": 5,
                            "max_capacity": 100
                        })
                        
                        self.logger.info(f"Unloaded {unloaded_quantity} units of {product_id} from AGV {agv_id} and created new inventory item")
                        return {
                            "success": True,
                            "agv_id": agv_id,
                            "product_id": product_id,
                            "quantity": unloaded_quantity,
                            "location": agv.location,
                            "new_inventory_item": True
                        }
                else:
                    self.logger.warning(f"Failed to unload {product_id} from AGV {agv_id}")
                    return {
                        "success": False,
                        "message": f"Failed to unload {product_id} from AGV {agv_id}"
                    }
            else:
                self.logger.warning("Missing agv_id or product_id for unload_agv action")
                return {
                    "success": False,
                    "message": "Missing agv_id or product_id"
                }
        
        elif action_type == "get_available_agvs":
            available_agvs = self.agv_manager.get_available_agvs()
            
            self.logger.info(f"Found {len(available_agvs)} available AGVs")
            return {
                "success": True,
                "available_agvs": [agv.to_dict() for agv in available_agvs]
            }
        
        else:
            self.logger.warning(f"Unknown AGV action type: {action_type}")
            return {
                "success": False,
                "message": f"Unknown action type: {action_type}"
            }
