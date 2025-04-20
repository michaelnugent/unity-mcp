"""
Defines the execute_menu_item tool for running Unity Editor menu commands.
"""
from typing import Dict, Any, Optional, List
from mcp.server.fastmcp import FastMCP, Context
from unity_connection import get_unity_connection  # Import unity_connection module

def register_execute_menu_item_tools(mcp: FastMCP):
    """Registers the execute_menu_item tool with the MCP server."""

    @mcp.tool()
    async def execute_menu_item(
        ctx: Context,
        menu_path: str,
        action: str = 'execute',
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Executes a Unity Editor menu item via its path (e.g., "File/Save Project").

        This tool allows LLMs to trigger Unity Editor menu commands programmatically,
        providing access to the full range of Unity's built-in functionality through
        its menu system.

        Args:
            ctx: The MCP context, containing runtime information.
            menu_path: The full path of the menu item to execute (e.g., "GameObject/Create Empty",
                      "Window/Package Manager", "Assets/Create/Material").
            action: The operation to perform (default: 'execute'). Currently only 'execute' 
                   is supported but future versions may support additional actions.
            parameters: Optional parameters for the menu item. Most menu items don't require
                       parameters, but some specialized commands might accept additional data.

        Returns:
            A dictionary with the following fields:
            - success: Boolean indicating if the operation succeeded
            - message: Success message if the operation was successful
            - error: Error message if the operation failed
            - data: Additional data returned by the menu command (if any)
            
        Examples:
            - Execute menu item to save the project:
              menu_path="File/Save Project"
              
            - Create a new empty GameObject:
              menu_path="GameObject/Create Empty"
              
            - Open the Animation window:
              menu_path="Window/Animation/Animation"
              
            - Create a new material:
              menu_path="Assets/Create/Material"
        """
        
        action = action.lower() if action else 'execute'
        
        # Prepare parameters for the C# handler
        params_dict = {
            "action": action,
            "menuPath": menu_path,
            "parameters": parameters if parameters else {},
        }

        # Remove None values
        params_dict = {k: v for k, v in params_dict.items() if v is not None}

        if "parameters" not in params_dict:
            params_dict["parameters"] = {} # Ensure parameters dict exists

        # Get Unity connection and send the command
        # We use the unity_connection module to communicate with Unity
        unity_conn = get_unity_connection()
        
        # Send command to the ExecuteMenuItem C# handler
        # The command type should match what the Unity side expects
        return unity_conn.send_command("execute_menu_item", params_dict) 