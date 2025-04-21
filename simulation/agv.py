"""
Automated Guided Vehicle (AGV) module for the warehouse simulation.
"""
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime
import json
import os


class AGVStatus(str, Enum):
    """Status of an AGV."""
    IDLE = "idle"
    MOVING = "moving"
    LOADING = "loading"
    UNLOADING = "unloading"
    CHARGING = "charging"
    MAINTENANCE = "maintenance"


class AGV:
    """Represents an Automated Guided Vehicle in the warehouse."""
    
    def __init__(
        self,
        agv_id: str,
        name: str,
        location: str,
        status: AGVStatus = AGVStatus.IDLE,
        battery_level: float = 100.0,
        max_capacity: float = 100.0,
        current_load: Optional[Dict] = None
    ):
        self.agv_id = agv_id
        self.name = name
        self.location = location
        self.status = status
        self.battery_level = battery_level
        self.max_capacity = max_capacity
        self.current_load = current_load or {}
        self.last_updated = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert the AGV to a dictionary."""
        return {
            "agv_id": self.agv_id,
            "name": self.name,
            "location": self.location,
            "status": self.status,
            "battery_level": self.battery_level,
            "max_capacity": self.max_capacity,
            "current_load": self.current_load,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AGV':
        """Create an AGV from a dictionary."""
        agv = cls(
            agv_id=data["agv_id"],
            name=data["name"],
            location=data["location"],
            status=AGVStatus(data["status"]),
            battery_level=data["battery_level"],
            max_capacity=data["max_capacity"],
            current_load=data.get("current_load", {})
        )
        agv.last_updated = data.get("last_updated", datetime.now().isoformat())
        return agv
    
    def is_available(self) -> bool:
        """Check if the AGV is available for a new task."""
        return (
            self.status == AGVStatus.IDLE and 
            self.battery_level > 20.0 and
            not self.current_load
        )
    
    def move_to(self, new_location: str) -> None:
        """Move the AGV to a new location."""
        self.status = AGVStatus.MOVING
        self.location = new_location
        # Simulate battery usage
        self.battery_level = max(0, self.battery_level - 5.0)
        self.status = AGVStatus.IDLE
        self.last_updated = datetime.now().isoformat()
    
    def load_item(self, product_id: str, quantity: int) -> bool:
        """Load an item onto the AGV."""
        if self.status != AGVStatus.IDLE:
            return False
        
        current_weight = sum(self.current_load.values())
        if current_weight + quantity > self.max_capacity:
            return False
        
        self.status = AGVStatus.LOADING
        
        if product_id in self.current_load:
            self.current_load[product_id] += quantity
        else:
            self.current_load[product_id] = quantity
        
        # Simulate battery usage
        self.battery_level = max(0, self.battery_level - 2.0)
        self.status = AGVStatus.IDLE
        self.last_updated = datetime.now().isoformat()
        return True
    
    def unload_item(self, product_id: str, quantity: Optional[int] = None) -> Tuple[str, int]:
        """Unload an item from the AGV."""
        if self.status != AGVStatus.IDLE:
            return product_id, 0
        
        if product_id not in self.current_load:
            return product_id, 0
        
        self.status = AGVStatus.UNLOADING
        
        if quantity is None or quantity >= self.current_load[product_id]:
            unloaded_quantity = self.current_load[product_id]
            del self.current_load[product_id]
        else:
            unloaded_quantity = quantity
            self.current_load[product_id] -= quantity
            if self.current_load[product_id] == 0:
                del self.current_load[product_id]
        
        # Simulate battery usage
        self.battery_level = max(0, self.battery_level - 2.0)
        self.status = AGVStatus.IDLE
        self.last_updated = datetime.now().isoformat()
        return product_id, unloaded_quantity
    
    def charge(self, amount: float = 100.0) -> None:
        """Charge the AGV's battery."""
        self.status = AGVStatus.CHARGING
        self.battery_level = min(100.0, self.battery_level + amount)
        self.status = AGVStatus.IDLE
        self.last_updated = datetime.now().isoformat()


class AGVManager:
    """Manages the AGVs in the warehouse."""
    
    def __init__(self, agv_file: Optional[str] = None):
        self.agvs: Dict[str, AGV] = {}
        self.agv_file = agv_file
        if agv_file and os.path.exists(agv_file):
            self.load_agvs()
    
    def add_agv(self, agv: AGV) -> None:
        """Add a new AGV to the manager."""
        self.agvs[agv.agv_id] = agv
        if self.agv_file:
            self.save_agvs()
    
    def get_agv(self, agv_id: str) -> Optional[AGV]:
        """Get an AGV by ID."""
        return self.agvs.get(agv_id)
    
    def get_all_agvs(self) -> List[AGV]:
        """Get all AGVs."""
        return list(self.agvs.values())
    
    def get_available_agvs(self) -> List[AGV]:
        """Get all available AGVs."""
        return [agv for agv in self.agvs.values() if agv.is_available()]
    
    def update_agv_status(self, agv_id: str, status: AGVStatus) -> bool:
        """Update the status of an AGV."""
        agv = self.get_agv(agv_id)
        if not agv:
            return False
        
        agv.status = status
        agv.last_updated = datetime.now().isoformat()
        
        if self.agv_file:
            self.save_agvs()
        
        return True
    
    def move_agv(self, agv_id: str, location: str) -> bool:
        """Move an AGV to a new location."""
        agv = self.get_agv(agv_id)
        if not agv:
            return False
        
        agv.move_to(location)
        
        if self.agv_file:
            self.save_agvs()
        
        return True
    
    def load_agv(self, agv_id: str, product_id: str, quantity: int) -> bool:
        """Load an item onto an AGV."""
        agv = self.get_agv(agv_id)
        if not agv:
            return False
        
        result = agv.load_item(product_id, quantity)
        
        if result and self.agv_file:
            self.save_agvs()
        
        return result
    
    def unload_agv(self, agv_id: str, product_id: str, quantity: Optional[int] = None) -> Tuple[str, int]:
        """Unload an item from an AGV."""
        agv = self.get_agv(agv_id)
        if not agv:
            return product_id, 0
        
        result = agv.unload_item(product_id, quantity)
        
        if result[1] > 0 and self.agv_file:
            self.save_agvs()
        
        return result
    
    def charge_agv(self, agv_id: str, amount: float = 100.0) -> bool:
        """Charge an AGV's battery."""
        agv = self.get_agv(agv_id)
        if not agv:
            return False
        
        agv.charge(amount)
        
        if self.agv_file:
            self.save_agvs()
        
        return True
    
    def save_agvs(self) -> None:
        """Save the AGVs to a file."""
        if not self.agv_file:
            return
        
        data = {
            agv_id: agv.to_dict() 
            for agv_id, agv in self.agvs.items()
        }
        
        with open(self.agv_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_agvs(self) -> None:
        """Load the AGVs from a file."""
        if not self.agv_file or not os.path.exists(self.agv_file):
            return
        
        with open(self.agv_file, 'r') as f:
            data = json.load(f)
        
        self.agvs = {
            agv_id: AGV.from_dict(agv_data)
            for agv_id, agv_data in data.items()
        }
    
    def to_dict(self) -> Dict:
        """Convert the AGV manager to a dictionary."""
        return {
            agv_id: agv.to_dict()
            for agv_id, agv in self.agvs.items()
        }
