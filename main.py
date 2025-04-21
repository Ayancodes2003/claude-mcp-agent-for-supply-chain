"""
Main application for the Claude-powered MCP Agent for Smart Supply Chain.
"""
import os
import logging
import json
from typing import Dict, Any
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from simulation.warehouse import Warehouse
from agents.coordinator import CoordinatorAgent
from gemini_interface import GeminiInterface
from api.routes import router


# Load environment variables
load_dotenv("gemini.env")

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/app.log")
    ]
)
logger = logging.getLogger(__name__)

# Create data directory if it doesn't exist
if not os.path.exists("data"):
    os.makedirs("data")

# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

# Initialize the warehouse
warehouse = Warehouse(
    name="Smart Warehouse",
    data_dir="data"
)

# Initialize the coordinator agent
coordinator = CoordinatorAgent(
    warehouse=warehouse,
    log_file="logs/actions.log",
    logger=logger
)

# Initialize the Gemini interface
gemini = GeminiInterface(
    logger=logger
)

# Create the FastAPI application
app = FastAPI(
    title="Claude-powered MCP Agent for Smart Supply Chain",
    description="A smart warehouse system powered by Claude using Model Context Protocol patterns",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize the warehouse with demo data on startup."""
    logger.info("Initializing warehouse with demo data")
    warehouse.initialize_demo_data()

    # Log the initial state
    state = warehouse.get_warehouse_state()
    logger.info(f"Warehouse initialized with {len(state['inventory'])} inventory items and {len(state['agvs'])} AGVs")

    # Save the initial state to a file
    with open("data/initial_state.json", "w") as f:
        json.dump(state, f, indent=2)


def run_server():
    """Run the server."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )


if __name__ == "__main__":
    run_server()
