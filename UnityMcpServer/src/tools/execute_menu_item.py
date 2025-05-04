"""
Defines the execute_menu_item tool for running Unity Editor menu commands.
"""
from typing import Dict, Any, Optional, List
from mcp.server.fastmcp import FastMCP, Context
from .base_tool import BaseTool
from exceptions import ParameterValidationError
# Import validation layer functions
from .validation_layer import validate_menu_path

class MenuItemTool(BaseTool):
    """Tool for executing Unity Editor menu items."""
    
    tool_name = "execute_menu_item"
    
    # Define required parameters for each action
    required_params = {
        "execute": {"menuPath": str},
        "get_available_menus": {},
    }
    
    # Menu item operations don't typically use Unity-specific types, but for consistency with other tools:
    vector2_params = []
    vector3_params = []
    euler_params = []
    quaternion_params = []
    color_params = []
    rect_params = []
    bounds_params = []
    
    def additional_validation(self, action: str, params: Dict[str, Any]) -> None:
        """Additional validation specific to the menu item tool."""
        if action == "execute":
            if not params.get("menuPath"):
                raise ParameterValidationError(
                    f"{self.tool_name} 'execute' action requires 'menuPath' parameter"
                )
            
            # Validate menu path format using the validation layer
            validate_menu_path(params["menuPath"])

    @staticmethod
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
            # Create tool instance
            menu_tool = MenuItemTool(ctx)
            
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
            
            try:
                # Send command with validation through the tool
                return await menu_tool.send_command_async("execute_menu_item", params_dict)
            except ParameterValidationError as e:
                return {"success": False, "message": str(e), "validation_error": True} 

def validate_menu_path(menu_path: Any) -> None:
    """Validate a menu path parameter.

    Args:
        menu_path: The menu path to validate
    
    Returns:
        None: This function doesn't return anything but raises exceptions on validation failure
    
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(menu_path, str):
        raise ParameterValidationError(f"Menu path must be a string, got {type(menu_path).__name__}: {menu_path}")
    
    # Check for empty path
    if not menu_path:
        raise ParameterValidationError("Menu path cannot be empty")
    
    # Check for menu separator
    if "/" not in menu_path:
        raise ParameterValidationError(f"Menu path must contain at least one '/' separator, got: {menu_path}") 