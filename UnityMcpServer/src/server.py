from mcp.server.fastmcp import FastMCP, Context, Image
import logging
import sys
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List
from config import config, load_config_from_args
from tools import register_all_tools
from unity_connection import get_unity_connection, UnityConnection

# Load config from command line arguments
load_config_from_args()

# Configure logging using settings from config
# Explicitly use stderr for logging since stdout is used for protocol communication
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format=config.log_format,
    stream=sys.stderr  # Force all logs to stderr
)
logger = logging.getLogger("unity-mcp-server")
logger.info(f"Starting server with Unity connection to {config.unity_host}:{config.unity_port}")

# Global connection state
_unity_connection: UnityConnection = None

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Handle server startup and shutdown."""
    global _unity_connection
    logger.info("Unity MCP Server starting up")
    try:
        _unity_connection = get_unity_connection()
        logger.info("Connected to Unity on startup")
    except Exception as e:
        logger.warning(f"Could not connect to Unity on startup: {str(e)}")
        _unity_connection = None
    try:
        # Yield the connection object so it can be attached to the context
        # The key 'bridge' matches how tools like read_console expect to access it (ctx.bridge)
        yield {"bridge": _unity_connection}
    finally:
        if _unity_connection:
            _unity_connection.disconnect()
            _unity_connection = None
        logger.info("Unity MCP Server shut down")

# Initialize MCP server
mcp = FastMCP(
    "unity-mcp-server",
    description="Unity Editor integration via Model Context Protocol",
    lifespan=server_lifespan
)

# Register all tools
register_all_tools(mcp)

# Asset Creation Strategy

@mcp.prompt()
def asset_creation_strategy() -> str:
    """Guide for discovering and using Unity MCP tools effectively."""
    return (
        "Available Unity MCP Server Tools:\\n\\n"
        "- `manage_editor`: Controls editor state and queries info.\\n"
        "- `execute_menu_item`: Executes Unity Editor menu items by path.\\n"
        "- `read_console`: Reads or clears Unity console messages, with filtering options.\\n"
        "- `manage_scene`: Manages scenes.\\n"
        "- `manage_gameobject`: Manages GameObjects in the scene.\\n"
        "- `manage_script`: Manages C# script files.\\n"
        "- `manage_asset`: Manages prefabs and assets.\\n\\n"
        "Tips:\\n"
        "- Create prefabs for reusable GameObjects.\\n"
        "- Always include a camera and main light in your scenes.\\n"
    )

# Run the server
if __name__ == "__main__":
    # Add MCP-specific logging instruction
    logger.info("Starting MCP server with stdio transport, all logs will be sent to stderr")
    mcp.run(transport='stdio')
