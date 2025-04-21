"""
Demo script to showcase the Claude-powered MCP Agent for Smart Supply Chain.
"""
import os
import json
import logging
from dotenv import load_dotenv

from simulation.warehouse import Warehouse
from agents.coordinator import CoordinatorAgent
from gemini_interface import GeminiInterface


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run a demo of the warehouse system."""
    # Load environment variables
    load_dotenv("gemini.env")

    # Check if Gemini API key is available
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("No Google API key found. Please set GOOGLE_API_KEY in gemini.env")
        logger.warning("Continuing with demo but Gemini integration will not work")

    # Create data directory if it doesn't exist
    if not os.path.exists("data"):
        os.makedirs("data")

    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Initialize the warehouse
    logger.info("Initializing warehouse")
    warehouse = Warehouse(
        name="Smart Warehouse Demo",
        data_dir="data"
    )

    # Initialize with demo data
    warehouse.initialize_demo_data()

    # Initialize the coordinator agent
    coordinator = CoordinatorAgent(
        warehouse=warehouse,
        log_file="logs/demo_actions.log",
        logger=logger
    )

    # Initialize Gemini interface if API key is available
    gemini = None
    if api_key:
        try:
            gemini = GeminiInterface(
                api_key=api_key,
                logger=logger
            )
            logger.info("Gemini interface initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini interface: {str(e)}")

    # Print the initial warehouse state
    print_warehouse_state(warehouse)

    # Demo scenario 1: Check inventory levels and identify items that need restocking
    logger.info("\n=== Scenario 1: Check inventory levels ===")
    items_below_threshold = warehouse.inventory_manager.get_items_below_threshold()

    if items_below_threshold:
        logger.info(f"Found {len(items_below_threshold)} items below threshold:")
        for item in items_below_threshold:
            logger.info(f"  - {item.name} (ID: {item.product_id}): {item.quantity}/{item.min_threshold}")
    else:
        logger.info("No items are below threshold")

    # Demo scenario 2: Find available AGVs
    logger.info("\n=== Scenario 2: Find available AGVs ===")
    available_agvs = warehouse.agv_manager.get_available_agvs()

    if available_agvs:
        logger.info(f"Found {len(available_agvs)} available AGVs:")
        for agv in available_agvs:
            logger.info(f"  - {agv.name} (ID: {agv.agv_id}) at {agv.location}, battery: {agv.battery_level}%")
    else:
        logger.info("No AGVs are available")

    # Demo scenario 3: Process an order
    logger.info("\n=== Scenario 3: Process an order ===")
    orders = warehouse.order_manager.get_all_orders()

    if orders:
        # Get the first order
        order = orders[0]
        logger.info(f"Processing order {order.order_id} for customer {order.customer_id}")
        logger.info(f"Order contains {len(order.items)} items:")

        for item in order.items:
            logger.info(f"  - Product {item.product_id}: {item.quantity} units")

        # Update order status
        from simulation.order import OrderStatus
        warehouse.order_manager.update_order_status(order.order_id, OrderStatus.PROCESSING)
        logger.info(f"Updated order status to {OrderStatus.PROCESSING}")
    else:
        logger.info("No orders to process")

    # Demo scenario 4: Move an AGV and pick an item
    logger.info("\n=== Scenario 4: Move an AGV and pick an item ===")

    if available_agvs and warehouse.inventory_manager.get_all_items():
        # Get the first available AGV
        agv = available_agvs[0]

        # Get the first inventory item
        item = warehouse.inventory_manager.get_all_items()[0]

        logger.info(f"Moving AGV {agv.agv_id} to {item.location}")
        warehouse.agv_manager.move_agv(agv.agv_id, item.location)

        # Pick the item
        pick_quantity = min(item.quantity, 1)
        if pick_quantity > 0:
            logger.info(f"Picking {pick_quantity} units of {item.product_id}")

            # Remove from inventory
            warehouse.inventory_manager.remove_quantity(item.product_id, pick_quantity)

            # Load onto AGV
            warehouse.agv_manager.load_agv(agv.agv_id, item.product_id, pick_quantity)

            logger.info(f"Successfully picked {pick_quantity} units of {item.product_id}")
        else:
            logger.info(f"Cannot pick {item.product_id}: insufficient quantity")
    else:
        logger.info("No available AGVs or inventory items")

    # Demo scenario 5: Ask Gemini for a recommendation (if available)
    if gemini:
        logger.info("\n=== Scenario 5: Ask Gemini for a recommendation ===")

        # Get the current warehouse state
        state = warehouse.get_warehouse_state()

        # Example query
        query = "The inventory for Product P001 is at 5 units, below the threshold of 10. Two AGVs are available. Suggest an optimal action."

        logger.info(f"Asking Gemini: {query}")
        response = gemini.ask(query, warehouse_state=state)

        if "error" in response:
            logger.error(f"Error from Gemini: {response['error']}")
        else:
            logger.info("Gemini's response:")
            print(f"\n{response['response']}\n")

            # Check if any actions were extracted
            actions = response.get("actions", [])
            if actions:
                logger.info(f"Extracted {len(actions)} actions from Gemini's response")
                for i, action in enumerate(actions):
                    logger.info(f"Action {i+1}: {json.dumps(action)}")

                # Execute the first action as a demo
                if actions:
                    logger.info("Executing the first action:")
                    result = coordinator.execute_action(actions[0])
                    logger.info(f"Result: {json.dumps(result)}")
            else:
                logger.info("No actions were extracted from Gemini's response")

    # Print the final warehouse state
    logger.info("\n=== Final Warehouse State ===")
    print_warehouse_state(warehouse)


def print_warehouse_state(warehouse: Warehouse):
    """Print the current state of the warehouse."""
    state = warehouse.get_warehouse_state()

    logger.info(f"Warehouse: {state['name']}")

    logger.info(f"Inventory: {len(state['inventory'])} items")
    for product_id, item in state['inventory'].items():
        logger.info(f"  - {item['name']} (ID: {product_id}): {item['quantity']} units at {item['location']}")

    logger.info(f"AGVs: {len(state['agvs'])} vehicles")
    for agv_id, agv in state['agvs'].items():
        logger.info(f"  - {agv['name']} (ID: {agv_id}): {agv['status']} at {agv['location']}, battery: {agv['battery_level']}%")

    logger.info(f"Orders: {len(state['orders'])} active orders")
    for order_id, order in state['orders'].items():
        logger.info(f"  - Order {order_id} (Customer: {order['customer_id']}): {order['status']}")


if __name__ == "__main__":
    main()
