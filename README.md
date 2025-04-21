# Claude-Powered MCP Agent for Smart Supply Chain

This project simulates a smart warehouse system powered by Claude using Model Context Protocol (MCP) patterns. The system manages inventory, automated guided vehicles (AGVs), and order processing through a set of specialized agents coordinated by Claude.

## Project Structure

```
claude-mcp-agent-for-supply-chain/
├── agents/                # MCP agent modules
├── simulation/            # Warehouse simulation logic
├── api/                   # FastAPI endpoints
├── logs/                  # Action and decision logs
├── claude_interface.py    # Interface to Claude API
├── main.py                # Main application entry point
```

## Features

- **MCP-style Modular Agents**: InventoryManager, AGVPlanner, RestockAgent, Coordinator
- **Warehouse Simulation**: Inventory tracking, AGV movement, order processing
- **Claude Integration**: Uses Anthropic's Claude API for decision-making
- **API Endpoints**: FastAPI-based endpoints for interacting with the system

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   cp claude.env.template claude.env
   ```
   Then edit `claude.env` to add your Anthropic API key.

5. Run the application:
   ```
   python main.py
   ```

## API Endpoints

- `GET /inventory`: Get current inventory status
- `GET /agvs`: Get status of all AGVs
- `POST /orders`: Create a new order
- `POST /ask-agent`: Send a query to Claude agent
- `GET /logs`: Get recent action logs

## Example Usage

Example prompt to Claude:
> The inventory for Product X is at 5 units, below the threshold of 10. Two AGVs are available. Suggest an optimal action.

Claude will analyze the situation and return structured actions that the system can execute.

## License

MIT
