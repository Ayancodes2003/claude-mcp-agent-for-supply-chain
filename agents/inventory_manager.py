"""
Inventory Manager Agent for the warehouse simulation.
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from simulation.inventory import InventoryManager, InventoryItem
from simulation.warehouse import Warehouse


class InventoryManagerAgent:
    """
    Agent responsible for managing inventory in the warehouse.
    Handles inventory checks, restock recommendations, and inventory optimization.
    """
    
    def __init__(self, warehouse: Warehouse, logger: Optional[logging.Logger] = None):
        self.warehouse = warehouse
        self.inventory_manager = warehouse.inventory_manager
        self.logger = logger or logging.getLogger(__name__)
    
    def get_inventory_status(self) -> Dict[str, Any]:
        """Get the current inventory status."""
        items = self.inventory_manager.get_all_items()
        
        return {
            "total_items": len(items),
            "items": [item.to_dict() for item in items],
            "items_below_threshold": [
                item.to_dict() for item in self.inventory_manager.get_items_below_threshold()
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    def get_restock_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for items that need to be restocked."""
        items_below_threshold = self.inventory_manager.get_items_below_threshold()
        
        recommendations = []
        for item in items_below_threshold:
            restock_amount = item.max_capacity - item.quantity
            recommendations.append({
                "product_id": item.product_id,
                "name": item.name,
                "current_quantity": item.quantity,
                "min_threshold": item.min_threshold,
                "max_capacity": item.max_capacity,
                "recommended_restock": restock_amount,
                "location": item.location
            })
        
        return recommendations
    
    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an inventory-related action."""
        action_type = action.get("action")
        
        if action_type == "check_inventory":
            product_id = action.get("product_id")
            if product_id:
                item = self.inventory_manager.get_item(product_id)
                if item:
                    self.logger.info(f"Checked inventory for {product_id}: {item.quantity} units")
                    return {
                        "success": True,
                        "product_id": product_id,
                        "quantity": item.quantity,
                        "location": item.location,
                        "needs_restock": item.needs_restock()
                    }
                else:
                    self.logger.warning(f"Product {product_id} not found in inventory")
                    return {
                        "success": False,
                        "message": f"Product {product_id} not found"
                    }
            else:
                self.logger.warning("No product_id provided for check_inventory action")
                return {
                    "success": False,
                    "message": "No product_id provided"
                }
        
        elif action_type == "update_inventory":
            product_id = action.get("product_id")
            quantity = action.get("quantity")
            
            if product_id is not None and quantity is not None:
                success = self.inventory_manager.update_quantity(product_id, quantity)
                if success:
                    self.logger.info(f"Updated inventory for {product_id} to {quantity} units")
                    return {
                        "success": True,
                        "product_id": product_id,
                        "new_quantity": quantity
                    }
                else:
                    self.logger.warning(f"Failed to update inventory for {product_id}")
                    return {
                        "success": False,
                        "message": f"Failed to update inventory for {product_id}"
                    }
            else:
                self.logger.warning("Missing product_id or quantity for update_inventory action")
                return {
                    "success": False,
                    "message": "Missing product_id or quantity"
                }
        
        elif action_type == "add_inventory":
            product_id = action.get("product_id")
            quantity = action.get("quantity", 0)
            
            if product_id and quantity > 0:
                success = self.inventory_manager.add_quantity(product_id, quantity)
                if success:
                    self.logger.info(f"Added {quantity} units to inventory for {product_id}")
                    return {
                        "success": True,
                        "product_id": product_id,
                        "added_quantity": quantity,
                        "new_quantity": self.inventory_manager.get_item(product_id).quantity
                    }
                else:
                    self.logger.warning(f"Failed to add {quantity} units to inventory for {product_id}")
                    return {
                        "success": False,
                        "message": f"Failed to add {quantity} units to inventory for {product_id}"
                    }
            else:
                self.logger.warning("Invalid product_id or quantity for add_inventory action")
                return {
                    "success": False,
                    "message": "Invalid product_id or quantity"
                }
        
        elif action_type == "remove_inventory":
            product_id = action.get("product_id")
            quantity = action.get("quantity", 0)
            
            if product_id and quantity > 0:
                success = self.inventory_manager.remove_quantity(product_id, quantity)
                if success:
                    self.logger.info(f"Removed {quantity} units from inventory for {product_id}")
                    return {
                        "success": True,
                        "product_id": product_id,
                        "removed_quantity": quantity,
                        "new_quantity": self.inventory_manager.get_item(product_id).quantity
                    }
                else:
                    self.logger.warning(f"Failed to remove {quantity} units from inventory for {product_id}")
                    return {
                        "success": False,
                        "message": f"Failed to remove {quantity} units from inventory for {product_id}"
                    }
            else:
                self.logger.warning("Invalid product_id or quantity for remove_inventory action")
                return {
                    "success": False,
                    "message": "Invalid product_id or quantity"
                }
        
        elif action_type == "add_new_product":
            product_data = action.get("product_data", {})
            
            if product_data and "product_id" in product_data and "name" in product_data:
                try:
                    new_item = InventoryItem(
                        product_id=product_data["product_id"],
                        name=product_data["name"],
                        quantity=product_data.get("quantity", 0),
                        location=product_data.get("location", "storage_a"),
                        min_threshold=product_data.get("min_threshold", 5),
                        max_capacity=product_data.get("max_capacity", 100)
                    )
                    
                    self.inventory_manager.add_item(new_item)
                    self.logger.info(f"Added new product {new_item.product_id} to inventory")
                    return {
                        "success": True,
                        "product": new_item.to_dict()
                    }
                except Exception as e:
                    self.logger.error(f"Error adding new product: {str(e)}")
                    return {
                        "success": False,
                        "message": f"Error adding new product: {str(e)}"
                    }
            else:
                self.logger.warning("Invalid product data for add_new_product action")
                return {
                    "success": False,
                    "message": "Invalid product data"
                }
        
        else:
            self.logger.warning(f"Unknown inventory action type: {action_type}")
            return {
                "success": False,
                "message": f"Unknown action type: {action_type}"
            }
