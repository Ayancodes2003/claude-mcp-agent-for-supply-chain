"""
Order management module for the warehouse simulation.
"""
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import json
import os
import uuid


class OrderStatus(str, Enum):
    """Status of an order."""
    PENDING = "pending"
    PROCESSING = "processing"
    PICKING = "picking"
    PACKING = "packing"
    SHIPPING = "shipping"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderItem:
    """Represents an item in an order."""
    
    def __init__(self, product_id: str, quantity: int):
        self.product_id = product_id
        self.quantity = quantity
    
    def to_dict(self) -> Dict:
        """Convert the order item to a dictionary."""
        return {
            "product_id": self.product_id,
            "quantity": self.quantity
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OrderItem':
        """Create an order item from a dictionary."""
        return cls(
            product_id=data["product_id"],
            quantity=data["quantity"]
        )


class Order:
    """Represents an order in the warehouse."""
    
    def __init__(
        self,
        order_id: Optional[str] = None,
        customer_id: str = "",
        items: Optional[List[OrderItem]] = None,
        status: OrderStatus = OrderStatus.PENDING,
        priority: int = 1,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.order_id = order_id or str(uuid.uuid4())
        self.customer_id = customer_id
        self.items = items or []
        self.status = status
        self.priority = priority
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
    
    def to_dict(self) -> Dict:
        """Convert the order to a dictionary."""
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "items": [item.to_dict() for item in self.items],
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Order':
        """Create an order from a dictionary."""
        return cls(
            order_id=data["order_id"],
            customer_id=data["customer_id"],
            items=[OrderItem.from_dict(item) for item in data["items"]],
            status=OrderStatus(data["status"]),
            priority=data["priority"],
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        )
    
    def add_item(self, product_id: str, quantity: int) -> None:
        """Add an item to the order."""
        for item in self.items:
            if item.product_id == product_id:
                item.quantity += quantity
                self.updated_at = datetime.now().isoformat()
                return
        
        self.items.append(OrderItem(product_id, quantity))
        self.updated_at = datetime.now().isoformat()
    
    def remove_item(self, product_id: str) -> bool:
        """Remove an item from the order."""
        for i, item in enumerate(self.items):
            if item.product_id == product_id:
                self.items.pop(i)
                self.updated_at = datetime.now().isoformat()
                return True
        return False
    
    def update_status(self, status: OrderStatus) -> None:
        """Update the status of the order."""
        self.status = status
        self.updated_at = datetime.now().isoformat()
    
    def get_total_items(self) -> int:
        """Get the total number of items in the order."""
        return sum(item.quantity for item in self.items)


class OrderManager:
    """Manages orders in the warehouse."""
    
    def __init__(self, order_file: Optional[str] = None):
        self.orders: Dict[str, Order] = {}
        self.order_file = order_file
        if order_file and os.path.exists(order_file):
            self.load_orders()
    
    def create_order(
        self,
        customer_id: str,
        items: List[Dict[str, any]],
        priority: int = 1
    ) -> Order:
        """Create a new order."""
        order_items = [
            OrderItem(item["product_id"], item["quantity"])
            for item in items
        ]
        
        order = Order(
            customer_id=customer_id,
            items=order_items,
            priority=priority
        )
        
        self.orders[order.order_id] = order
        
        if self.order_file:
            self.save_orders()
        
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID."""
        return self.orders.get(order_id)
    
    def get_all_orders(self) -> List[Order]:
        """Get all orders."""
        return list(self.orders.values())
    
    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Get all orders with the specified status."""
        return [
            order for order in self.orders.values()
            if order.status == status
        ]
    
    def update_order_status(self, order_id: str, status: OrderStatus) -> bool:
        """Update the status of an order."""
        order = self.get_order(order_id)
        if not order:
            return False
        
        order.update_status(status)
        
        if self.order_file:
            self.save_orders()
        
        return True
    
    def add_item_to_order(self, order_id: str, product_id: str, quantity: int) -> bool:
        """Add an item to an order."""
        order = self.get_order(order_id)
        if not order:
            return False
        
        order.add_item(product_id, quantity)
        
        if self.order_file:
            self.save_orders()
        
        return True
    
    def remove_item_from_order(self, order_id: str, product_id: str) -> bool:
        """Remove an item from an order."""
        order = self.get_order(order_id)
        if not order:
            return False
        
        result = order.remove_item(product_id)
        
        if result and self.order_file:
            self.save_orders()
        
        return result
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        return self.update_order_status(order_id, OrderStatus.CANCELLED)
    
    def complete_order(self, order_id: str) -> bool:
        """Mark an order as completed."""
        return self.update_order_status(order_id, OrderStatus.COMPLETED)
    
    def save_orders(self) -> None:
        """Save the orders to a file."""
        if not self.order_file:
            return
        
        data = {
            order_id: order.to_dict()
            for order_id, order in self.orders.items()
        }
        
        with open(self.order_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_orders(self) -> None:
        """Load the orders from a file."""
        if not self.order_file or not os.path.exists(self.order_file):
            return
        
        with open(self.order_file, 'r') as f:
            data = json.load(f)
        
        self.orders = {
            order_id: Order.from_dict(order_data)
            for order_id, order_data in data.items()
        }
    
    def to_dict(self) -> Dict:
        """Convert the order manager to a dictionary."""
        return {
            order_id: order.to_dict()
            for order_id, order in self.orders.items()
        }
