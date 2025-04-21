"""
API data models for the warehouse simulation.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class QueryRequest(BaseModel):
    """Request model for querying the Claude agent."""
    query: str = Field(..., description="The query to send to the Claude agent")
    include_state: bool = Field(True, description="Whether to include the warehouse state in the prompt")


class ActionRequest(BaseModel):
    """Request model for executing an action."""
    type: str = Field(..., description="The type of action to execute")
    agent: str = Field(..., description="The agent to execute the action")
    action: str = Field(..., description="The specific action to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the action")


class PlanRequest(BaseModel):
    """Request model for executing a plan (sequence of actions)."""
    actions: List[ActionRequest] = Field(..., description="The actions to execute")


class OrderItem(BaseModel):
    """Model for an item in an order."""
    product_id: str = Field(..., description="The ID of the product")
    quantity: int = Field(..., description="The quantity of the product")


class OrderRequest(BaseModel):
    """Request model for creating a new order."""
    customer_id: str = Field(..., description="The ID of the customer")
    items: List[OrderItem] = Field(..., description="The items in the order")
    priority: int = Field(1, description="The priority of the order (1-10)")


class InventoryItemRequest(BaseModel):
    """Request model for adding a new inventory item."""
    product_id: str = Field(..., description="The ID of the product")
    name: str = Field(..., description="The name of the product")
    quantity: int = Field(0, description="The initial quantity of the product")
    location: str = Field("storage_a", description="The location of the product")
    min_threshold: int = Field(5, description="The minimum threshold for restocking")
    max_capacity: int = Field(100, description="The maximum capacity for the product")


class AGVRequest(BaseModel):
    """Request model for adding a new AGV."""
    agv_id: str = Field(..., description="The ID of the AGV")
    name: str = Field(..., description="The name of the AGV")
    location: str = Field("charging_station", description="The initial location of the AGV")
    battery_level: float = Field(100.0, description="The initial battery level of the AGV")
    max_capacity: float = Field(50.0, description="The maximum capacity of the AGV")


class LogRequest(BaseModel):
    """Request model for retrieving logs."""
    limit: int = Field(10, description="The maximum number of logs to retrieve")
    action_type: Optional[str] = Field(None, description="Filter logs by action type")
    agent: Optional[str] = Field(None, description="Filter logs by agent")


class Response(BaseModel):
    """Base response model."""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="A message describing the result")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="The timestamp of the response")


class QueryResponse(Response):
    """Response model for querying the Claude agent."""
    query: str = Field(..., description="The original query")
    response: str = Field(..., description="The response from the Claude agent")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Actions extracted from the response")


class ActionResponse(Response):
    """Response model for executing an action."""
    action: Dict[str, Any] = Field(..., description="The action that was executed")
    result: Dict[str, Any] = Field(..., description="The result of the action")


class PlanResponse(Response):
    """Response model for executing a plan."""
    actions: List[Dict[str, Any]] = Field(..., description="The actions that were executed")
    results: List[Dict[str, Any]] = Field(..., description="The results of the actions")


class WarehouseStateResponse(Response):
    """Response model for retrieving the warehouse state."""
    state: Dict[str, Any] = Field(..., description="The current state of the warehouse")


class LogResponse(Response):
    """Response model for retrieving logs."""
    logs: List[Dict[str, Any]] = Field(..., description="The requested logs")
