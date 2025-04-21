"""
API routes for the warehouse simulation.
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import logging
from datetime import datetime

from simulation.warehouse import Warehouse
from agents.coordinator import CoordinatorAgent
from gemini_interface import GeminiInterface
from api.models import (
    QueryRequest, ActionRequest, PlanRequest, OrderRequest,
    InventoryItemRequest, AGVRequest, LogRequest,
    QueryResponse, ActionResponse, PlanResponse, WarehouseStateResponse,
    LogResponse, Response
)


# Create a router
router = APIRouter()

# Logger
logger = logging.getLogger(__name__)


# Dependency to get the warehouse
def get_warehouse():
    # This would typically be a singleton or stored in a database
    # For simplicity, we'll create a new instance each time
    from main import warehouse
    return warehouse


# Dependency to get the coordinator agent
def get_coordinator(warehouse: Warehouse = Depends(get_warehouse)):
    # This would typically be a singleton or stored in a database
    # For simplicity, we'll create a new instance each time
    from main import coordinator
    return coordinator


# Dependency to get the Gemini interface
def get_gemini():
    # This would typically be a singleton or stored in a database
    # For simplicity, we'll create a new instance each time
    from main import gemini
    return gemini


@router.get("/", response_model=Response)
async def root():
    """Root endpoint that returns a welcome message."""
    return {
        "success": True,
        "message": "Welcome to the Claude-powered MCP Agent for Smart Supply Chain",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/ask-agent", response_model=QueryResponse)
async def ask_agent(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    coordinator: CoordinatorAgent = Depends(get_coordinator),
    gemini: GeminiInterface = Depends(get_gemini)
):
    """
    Ask the Gemini agent a question and get a response.

    Optionally executes any actions suggested by Gemini in the background.
    """
    try:
        # Get the warehouse state if requested
        warehouse_state = coordinator.get_warehouse_state() if request.include_state else None

        # Ask Gemini
        result = gemini.ask(request.query, warehouse_state=warehouse_state)

        # Extract actions from the response
        actions = result.get("actions", [])

        # Execute actions in the background if any were found
        if actions:
            background_tasks.add_task(execute_actions_in_background, actions, coordinator)

        return {
            "success": True,
            "message": "Query processed successfully",
            "query": request.query,
            "response": result["response"],
            "actions": actions,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-action", response_model=ActionResponse)
async def execute_action(
    request: ActionRequest,
    coordinator: CoordinatorAgent = Depends(get_coordinator)
):
    """Execute a single action in the warehouse."""
    try:
        # Convert the request to an action dictionary
        action = {
            "type": request.type,
            "agent": request.agent,
            "action": request.action,
            **request.params
        }

        # Execute the action
        result = coordinator.execute_action(action)

        return {
            "success": result.get("success", False),
            "message": result.get("message", "Action executed"),
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error executing action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-plan", response_model=PlanResponse)
async def execute_plan(
    request: PlanRequest,
    coordinator: CoordinatorAgent = Depends(get_coordinator)
):
    """Execute a plan (sequence of actions) in the warehouse."""
    try:
        # Convert the request to a list of action dictionaries
        actions = []
        for action_request in request.actions:
            action = {
                "type": action_request.type,
                "agent": action_request.agent,
                "action": action_request.action,
                **action_request.params
            }
            actions.append(action)

        # Execute the plan
        results = coordinator.execute_plan(actions)

        # Check if all actions were successful
        all_successful = all(result.get("success", False) for result in results)

        return {
            "success": all_successful,
            "message": "Plan executed successfully" if all_successful else "Plan execution had errors",
            "actions": actions,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error executing plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/warehouse-state", response_model=WarehouseStateResponse)
async def get_warehouse_state(
    coordinator: CoordinatorAgent = Depends(get_coordinator)
):
    """Get the current state of the warehouse."""
    try:
        state = coordinator.get_warehouse_state()

        return {
            "success": True,
            "message": "Warehouse state retrieved successfully",
            "state": state,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting warehouse state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory", response_model=Response)
async def get_inventory(
    warehouse: Warehouse = Depends(get_warehouse)
):
    """Get the current inventory."""
    try:
        inventory = {
            item.product_id: item.to_dict()
            for item in warehouse.inventory_manager.get_all_items()
        }

        return {
            "success": True,
            "message": "Inventory retrieved successfully",
            "inventory": inventory,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting inventory: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inventory", response_model=Response)
async def add_inventory_item(
    request: InventoryItemRequest,
    warehouse: Warehouse = Depends(get_warehouse)
):
    """Add a new item to the inventory."""
    try:
        from simulation.inventory import InventoryItem

        # Create a new inventory item
        item = InventoryItem(
            product_id=request.product_id,
            name=request.name,
            quantity=request.quantity,
            location=request.location,
            min_threshold=request.min_threshold,
            max_capacity=request.max_capacity
        )

        # Add the item to the inventory
        warehouse.inventory_manager.add_item(item)

        return {
            "success": True,
            "message": f"Added inventory item {request.product_id}",
            "item": item.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error adding inventory item: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agvs", response_model=Response)
async def get_agvs(
    warehouse: Warehouse = Depends(get_warehouse)
):
    """Get all AGVs."""
    try:
        agvs = {
            agv.agv_id: agv.to_dict()
            for agv in warehouse.agv_manager.get_all_agvs()
        }

        return {
            "success": True,
            "message": "AGVs retrieved successfully",
            "agvs": agvs,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting AGVs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agvs", response_model=Response)
async def add_agv(
    request: AGVRequest,
    warehouse: Warehouse = Depends(get_warehouse)
):
    """Add a new AGV."""
    try:
        from simulation.agv import AGV, AGVStatus

        # Create a new AGV
        agv = AGV(
            agv_id=request.agv_id,
            name=request.name,
            location=request.location,
            status=AGVStatus.IDLE,
            battery_level=request.battery_level,
            max_capacity=request.max_capacity
        )

        # Add the AGV to the manager
        warehouse.agv_manager.add_agv(agv)

        return {
            "success": True,
            "message": f"Added AGV {request.agv_id}",
            "agv": agv.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error adding AGV: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", response_model=Response)
async def get_orders(
    warehouse: Warehouse = Depends(get_warehouse)
):
    """Get all orders."""
    try:
        orders = {
            order.order_id: order.to_dict()
            for order in warehouse.order_manager.get_all_orders()
        }

        return {
            "success": True,
            "message": "Orders retrieved successfully",
            "orders": orders,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting orders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders", response_model=Response)
async def create_order(
    request: OrderRequest,
    warehouse: Warehouse = Depends(get_warehouse)
):
    """Create a new order."""
    try:
        # Convert the request items to the format expected by the order manager
        items = [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in request.items
        ]

        # Create the order
        order = warehouse.order_manager.create_order(
            customer_id=request.customer_id,
            items=items,
            priority=request.priority
        )

        return {
            "success": True,
            "message": f"Created order {order.order_id}",
            "order": order.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_model=LogResponse)
async def get_logs(
    request: LogRequest = Depends(),
    coordinator: CoordinatorAgent = Depends(get_coordinator)
):
    """Get action logs."""
    try:
        # Get the action history
        logs = coordinator.get_action_history(request.limit)

        # Filter by action type if specified
        if request.action_type:
            logs = [
                log for log in logs
                if log.get("action", {}).get("type") == request.action_type
            ]

        # Filter by agent if specified
        if request.agent:
            logs = [
                log for log in logs
                if log.get("action", {}).get("agent") == request.agent
            ]

        return {
            "success": True,
            "message": f"Retrieved {len(logs)} logs",
            "logs": logs,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze", response_model=Response)
async def analyze_warehouse(
    coordinator: CoordinatorAgent = Depends(get_coordinator)
):
    """Analyze the warehouse state and provide recommendations."""
    try:
        analysis = coordinator.analyze_warehouse_state()

        return {
            "success": True,
            "message": "Warehouse analysis completed",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error analyzing warehouse: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper function to execute actions in the background
async def execute_actions_in_background(
    actions: List[Dict[str, Any]],
    coordinator: CoordinatorAgent
):
    """Execute a list of actions in the background."""
    try:
        for action in actions:
            coordinator.execute_action(action)
    except Exception as e:
        logger.error(f"Error executing background actions: {str(e)}")
