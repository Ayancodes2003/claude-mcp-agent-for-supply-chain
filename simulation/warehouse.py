"""
Warehouse simulation module that integrates inventory, AGVs, and orders.
"""
from typing import Dict, List, Optional, Any
import os
import json
from datetime import datetime

from simulation.inventory import InventoryManager, InventoryItem
from simulation.agv import AGVManager, AGV, AGVStatus
from simulation.order import OrderManager, Order, OrderStatus


class Warehouse:
    """Simulates a warehouse with inventory, AGVs, and orders."""
    
    def __init__(
        self,
        name: str,
        data_dir: str = "data",
        inventory_file: Optional[str] = None,
        agv_file: Optional[str] = None,
        order_file: Optional[str] = None
    ):
        self.name = name
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Initialize managers with file paths
        self.inventory_manager = InventoryManager(
            inventory_file or os.path.join(data_dir, "inventory.json")
        )
        self.agv_manager = AGVManager(
            agv_file or os.path.join(data_dir, "agvs.json")
        )
        self.order_manager = OrderManager(
            order_file or os.path.join(data_dir, "orders.json")
        )
        
        # Warehouse locations
        self.locations = {
            "receiving": {"type": "dock", "capacity": 10},
            "shipping": {"type": "dock", "capacity": 10},
            "storage_a": {"type": "storage", "capacity": 100},
            "storage_b": {"type": "storage", "capacity": 100},
            "storage_c": {"type": "storage", "capacity": 100},
            "picking_station": {"type": "workstation", "capacity": 5},
            "packing_station": {"type": "workstation", "capacity": 5},
            "charging_station": {"type": "charging", "capacity": 3}
        }
        
        # Warehouse statistics
        self.stats = {
            "orders_processed": 0,
            "items_picked": 0,
            "items_restocked": 0,
            "agv_movements": 0,
            "last_updated": datetime.now().isoformat()
        }
    
    def initialize_demo_data(self) -> None:
        """Initialize the warehouse with demo data."""
        # Add inventory items
        products = [
            {
                "product_id": "P001",
                "name": "Smartphone",
                "quantity": 50,
                "location": "storage_a",
                "min_threshold": 10,
                "max_capacity": 100
            },
            {
                "product_id": "P002",
                "name": "Laptop",
                "quantity": 20,
                "location": "storage_a",
                "min_threshold": 5,
                "max_capacity": 50
            },
            {
                "product_id": "P003",
                "name": "Tablet",
                "quantity": 30,
                "location": "storage_b",
                "min_threshold": 8,
                "max_capacity": 80
            },
            {
                "product_id": "P004",
                "name": "Headphones",
                "quantity": 100,
                "location": "storage_b",
                "min_threshold": 20,
                "max_capacity": 200
            },
            {
                "product_id": "P005",
                "name": "Smartwatch",
                "quantity": 15,
                "location": "storage_c",
                "min_threshold": 5,
                "max_capacity": 50
            }
        ]
        
        for product in products:
            self.inventory_manager.add_item(InventoryItem(**product))
        
        # Add AGVs
        agvs = [
            {
                "agv_id": "AGV001",
                "name": "Picker Bot 1",
                "location": "charging_station",
                "status": AGVStatus.IDLE,
                "battery_level": 100.0,
                "max_capacity": 50.0
            },
            {
                "agv_id": "AGV002",
                "name": "Picker Bot 2",
                "location": "storage_a",
                "status": AGVStatus.IDLE,
                "battery_level": 85.0,
                "max_capacity": 50.0
            },
            {
                "agv_id": "AGV003",
                "name": "Heavy Lifter 1",
                "location": "receiving",
                "status": AGVStatus.IDLE,
                "battery_level": 90.0,
                "max_capacity": 100.0
            }
        ]
        
        for agv_data in agvs:
            self.agv_manager.add_agv(AGV(**agv_data))
        
        # Add sample orders
        orders = [
            {
                "customer_id": "C001",
                "items": [
                    {"product_id": "P001", "quantity": 2},
                    {"product_id": "P004", "quantity": 1}
                ],
                "priority": 2
            },
            {
                "customer_id": "C002",
                "items": [
                    {"product_id": "P002", "quantity": 1},
                    {"product_id": "P003", "quantity": 1},
                    {"product_id": "P005", "quantity": 1}
                ],
                "priority": 1
            }
        ]
        
        for order_data in orders:
            self.order_manager.create_order(**order_data)
    
    def get_warehouse_state(self) -> Dict[str, Any]:
        """Get the current state of the warehouse."""
        return {
            "name": self.name,
            "inventory": {
                item.product_id: {
                    "name": item.name,
                    "quantity": item.quantity,
                    "location": item.location,
                    "min_threshold": item.min_threshold,
                    "needs_restock": item.needs_restock()
                }
                for item in self.inventory_manager.get_all_items()
            },
            "agvs": {
                agv.agv_id: {
                    "name": agv.name,
                    "location": agv.location,
                    "status": agv.status,
                    "battery_level": agv.battery_level,
                    "current_load": agv.current_load,
                    "is_available": agv.is_available()
                }
                for agv in self.agv_manager.get_all_agvs()
            },
            "orders": {
                order.order_id: {
                    "customer_id": order.customer_id,
                    "status": order.status,
                    "priority": order.priority,
                    "items": [
                        {
                            "product_id": item.product_id,
                            "quantity": item.quantity
                        }
                        for item in order.items
                    ],
                    "created_at": order.created_at
                }
                for order in self.order_manager.get_all_orders()
                if order.status != OrderStatus.COMPLETED and order.status != OrderStatus.CANCELLED
            },
            "locations": self.locations,
            "stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def process_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process an action in the warehouse."""
        action_type = action.get("type")
        result = {"success": False, "message": "Unknown action type"}
        
        if action_type == "move_agv":
            agv_id = action.get("agv_id")
            location = action.get("location")
            if agv_id and location:
                success = self.agv_manager.move_agv(agv_id, location)
                if success:
                    self.stats["agv_movements"] += 1
                    self.stats["last_updated"] = datetime.now().isoformat()
                    result = {
                        "success": True,
                        "message": f"AGV {agv_id} moved to {location}"
                    }
                else:
                    result = {
                        "success": False,
                        "message": f"Failed to move AGV {agv_id} to {location}"
                    }
        
        elif action_type == "pick_item":
            agv_id = action.get("agv_id")
            product_id = action.get("product_id")
            quantity = action.get("quantity", 1)
            
            if agv_id and product_id:
                # Get the AGV and inventory item
                agv = self.agv_manager.get_agv(agv_id)
                item = self.inventory_manager.get_item(product_id)
                
                if not agv:
                    result = {
                        "success": False,
                        "message": f"AGV {agv_id} not found"
                    }
                elif not item:
                    result = {
                        "success": False,
                        "message": f"Product {product_id} not found"
                    }
                elif agv.location != item.location:
                    result = {
                        "success": False,
                        "message": f"AGV {agv_id} is not at the same location as product {product_id}"
                    }
                else:
                    # Remove from inventory and load onto AGV
                    if self.inventory_manager.remove_quantity(product_id, quantity):
                        if self.agv_manager.load_agv(agv_id, product_id, quantity):
                            self.stats["items_picked"] += quantity
                            self.stats["last_updated"] = datetime.now().isoformat()
                            result = {
                                "success": True,
                                "message": f"Picked {quantity} units of {product_id} with AGV {agv_id}"
                            }
                        else:
                            # Revert inventory change if AGV loading fails
                            self.inventory_manager.add_quantity(product_id, quantity)
                            result = {
                                "success": False,
                                "message": f"Failed to load {quantity} units of {product_id} onto AGV {agv_id}"
                            }
                    else:
                        result = {
                            "success": False,
                            "message": f"Not enough inventory of {product_id} to pick {quantity} units"
                        }
        
        elif action_type == "restock_item":
            agv_id = action.get("agv_id")
            product_id = action.get("product_id")
            quantity = action.get("quantity", 1)
            
            if agv_id and product_id:
                # Get the AGV and inventory item
                agv = self.agv_manager.get_agv(agv_id)
                item = self.inventory_manager.get_item(product_id)
                
                if not agv:
                    result = {
                        "success": False,
                        "message": f"AGV {agv_id} not found"
                    }
                elif not item:
                    result = {
                        "success": False,
                        "message": f"Product {product_id} not found"
                    }
                elif agv.location != item.location:
                    result = {
                        "success": False,
                        "message": f"AGV {agv_id} is not at the same location as product {product_id}"
                    }
                else:
                    # Unload from AGV and add to inventory
                    product_id, unloaded = self.agv_manager.unload_agv(agv_id, product_id, quantity)
                    if unloaded > 0:
                        if self.inventory_manager.add_quantity(product_id, unloaded):
                            self.stats["items_restocked"] += unloaded
                            self.stats["last_updated"] = datetime.now().isoformat()
                            result = {
                                "success": True,
                                "message": f"Restocked {unloaded} units of {product_id} from AGV {agv_id}"
                            }
                        else:
                            # Revert AGV change if inventory update fails
                            self.agv_manager.load_agv(agv_id, product_id, unloaded)
                            result = {
                                "success": False,
                                "message": f"Failed to restock {unloaded} units of {product_id} to inventory"
                            }
                    else:
                        result = {
                            "success": False,
                            "message": f"No {product_id} available on AGV {agv_id} to restock"
                        }
        
        elif action_type == "process_order":
            order_id = action.get("order_id")
            new_status = action.get("status")
            
            if order_id and new_status:
                try:
                    status = OrderStatus(new_status)
                    if self.order_manager.update_order_status(order_id, status):
                        if status == OrderStatus.COMPLETED:
                            self.stats["orders_processed"] += 1
                            self.stats["last_updated"] = datetime.now().isoformat()
                        result = {
                            "success": True,
                            "message": f"Updated order {order_id} status to {new_status}"
                        }
                    else:
                        result = {
                            "success": False,
                            "message": f"Failed to update order {order_id} status"
                        }
                except ValueError:
                    result = {
                        "success": False,
                        "message": f"Invalid order status: {new_status}"
                    }
        
        elif action_type == "charge_agv":
            agv_id = action.get("agv_id")
            amount = action.get("amount", 100.0)
            
            if agv_id:
                agv = self.agv_manager.get_agv(agv_id)
                if not agv:
                    result = {
                        "success": False,
                        "message": f"AGV {agv_id} not found"
                    }
                elif agv.location != "charging_station":
                    result = {
                        "success": False,
                        "message": f"AGV {agv_id} is not at a charging station"
                    }
                else:
                    if self.agv_manager.charge_agv(agv_id, amount):
                        result = {
                            "success": True,
                            "message": f"Charged AGV {agv_id} to {agv.battery_level}%"
                        }
                    else:
                        result = {
                            "success": False,
                            "message": f"Failed to charge AGV {agv_id}"
                        }
        
        return result
