"""
Inventory management module for the warehouse simulation.
"""
from typing import Dict, List, Optional
import json
import os
from datetime import datetime


class InventoryItem:
    """Represents a single inventory item in the warehouse."""
    
    def __init__(
        self,
        product_id: str,
        name: str,
        quantity: int,
        location: str,
        min_threshold: int,
        max_capacity: int
    ):
        self.product_id = product_id
        self.name = name
        self.quantity = quantity
        self.location = location
        self.min_threshold = min_threshold
        self.max_capacity = max_capacity
        self.last_updated = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert the inventory item to a dictionary."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "quantity": self.quantity,
            "location": self.location,
            "min_threshold": self.min_threshold,
            "max_capacity": self.max_capacity,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InventoryItem':
        """Create an inventory item from a dictionary."""
        item = cls(
            product_id=data["product_id"],
            name=data["name"],
            quantity=data["quantity"],
            location=data["location"],
            min_threshold=data["min_threshold"],
            max_capacity=data["max_capacity"]
        )
        item.last_updated = data.get("last_updated", datetime.now().isoformat())
        return item
    
    def needs_restock(self) -> bool:
        """Check if the item needs to be restocked."""
        return self.quantity <= self.min_threshold
    
    def can_add(self, amount: int) -> bool:
        """Check if the specified amount can be added to inventory."""
        return self.quantity + amount <= self.max_capacity
    
    def add(self, amount: int) -> bool:
        """Add the specified amount to inventory if possible."""
        if not self.can_add(amount):
            return False
        self.quantity += amount
        self.last_updated = datetime.now().isoformat()
        return True
    
    def remove(self, amount: int) -> bool:
        """Remove the specified amount from inventory if possible."""
        if amount > self.quantity:
            return False
        self.quantity -= amount
        self.last_updated = datetime.now().isoformat()
        return True


class InventoryManager:
    """Manages the inventory of the warehouse."""
    
    def __init__(self, inventory_file: Optional[str] = None):
        self.items: Dict[str, InventoryItem] = {}
        self.inventory_file = inventory_file
        if inventory_file and os.path.exists(inventory_file):
            self.load_inventory()
    
    def add_item(self, item: InventoryItem) -> None:
        """Add a new item to the inventory."""
        self.items[item.product_id] = item
        if self.inventory_file:
            self.save_inventory()
    
    def get_item(self, product_id: str) -> Optional[InventoryItem]:
        """Get an item from the inventory by product ID."""
        return self.items.get(product_id)
    
    def get_all_items(self) -> List[InventoryItem]:
        """Get all items in the inventory."""
        return list(self.items.values())
    
    def update_quantity(self, product_id: str, new_quantity: int) -> bool:
        """Update the quantity of an item in the inventory."""
        item = self.get_item(product_id)
        if not item:
            return False
        
        if new_quantity < 0:
            return False
        
        if new_quantity > item.max_capacity:
            return False
        
        item.quantity = new_quantity
        item.last_updated = datetime.now().isoformat()
        
        if self.inventory_file:
            self.save_inventory()
        
        return True
    
    def add_quantity(self, product_id: str, amount: int) -> bool:
        """Add a quantity of an item to the inventory."""
        item = self.get_item(product_id)
        if not item:
            return False
        
        result = item.add(amount)
        if result and self.inventory_file:
            self.save_inventory()
        
        return result
    
    def remove_quantity(self, product_id: str, amount: int) -> bool:
        """Remove a quantity of an item from the inventory."""
        item = self.get_item(product_id)
        if not item:
            return False
        
        result = item.remove(amount)
        if result and self.inventory_file:
            self.save_inventory()
        
        return result
    
    def get_items_below_threshold(self) -> List[InventoryItem]:
        """Get all items that are below their minimum threshold."""
        return [item for item in self.items.values() if item.needs_restock()]
    
    def save_inventory(self) -> None:
        """Save the inventory to a file."""
        if not self.inventory_file:
            return
        
        data = {
            product_id: item.to_dict() 
            for product_id, item in self.items.items()
        }
        
        with open(self.inventory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_inventory(self) -> None:
        """Load the inventory from a file."""
        if not self.inventory_file or not os.path.exists(self.inventory_file):
            return
        
        with open(self.inventory_file, 'r') as f:
            data = json.load(f)
        
        self.items = {
            product_id: InventoryItem.from_dict(item_data)
            for product_id, item_data in data.items()
        }
    
    def to_dict(self) -> Dict:
        """Convert the inventory to a dictionary."""
        return {
            product_id: item.to_dict()
            for product_id, item in self.items.items()
        }
