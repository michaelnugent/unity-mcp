"""
Defines the read_console tool for accessing Unity Editor console messages.
"""
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP, Context
from .base_tool import BaseTool
from exceptions import ParameterValidationError

class ConsoleTool(BaseTool):
    """Tool for reading and manipulating the Unity console."""
    
    tool_name = "read_console"
    
    # Define required parameters for each action
    required_params = {
        "get": {},
        "clear": {},
    }
    
    def additional_validation(self, action: str, params: Dict[str, Any]) -> None:
        """Additional validation specific to the console tool."""
        if action == "get" and "types" in params:
            if not isinstance(params["types"], list):
                raise ParameterValidationError(
                    f"{self.tool_name} 'get' parameter 'types' must be a list"
                )

    @staticmethod
    def register_read_console_tools(mcp: FastMCP):
        """Registers the read_console tool with the MCP server."""

        @mcp.tool()
        async def read_console(
            ctx: Context,
            action: str = None,
            types: List[str] = None,
            count: int = None,
            filter_text: str = None,
            since_timestamp: str = None,
            format: str = None,
            include_stacktrace: bool = None
        ) -> Dict[str, Any]:
            """Gets messages from or clears the Unity Editor console.

            Args:
                ctx: The MCP context.
                action: Operation ('get' or 'clear').
                types: Message types to get ('error', 'warning', 'log', 'all').
                count: Max messages to return.
                filter_text: Text filter for messages.
                since_timestamp: Get messages after this timestamp (ISO 8601).
                format: Output format ('plain', 'detailed', 'json').
                include_stacktrace: Include stack traces in output.

            Returns:
                Dictionary with results. For 'get', includes 'data' (messages).
            """
            # Create tool instance
            console_tool = ConsoleTool(ctx)
            
            # Set defaults if values are None
            action = action if action is not None else 'get'
            types = types if types is not None else ['error', 'warning', 'log']
            format = format if format is not None else 'detailed'
            include_stacktrace = include_stacktrace if include_stacktrace is not None else True

            # Normalize action if it's a string
            if isinstance(action, str):
                action = action.lower()
            
            # Prepare parameters for the C# handler
            params_dict = {
                "action": action,
                "types": types,
                "count": count,
                "filterText": filter_text,
                "sinceTimestamp": since_timestamp,
                "format": format.lower() if isinstance(format, str) else format,
                "includeStacktrace": include_stacktrace
            }

            # Remove None values unless it's 'count' (as None might mean 'all')
            params_dict = {k: v for k, v in params_dict.items() if v is not None or k == 'count'} 
            
            # Add count back if it was None, explicitly sending null might be important for C# logic
            if 'count' not in params_dict:
                 params_dict['count'] = None 

            try:
                # Send command with validation through the tool
                return await console_tool.send_command_async("read_console", params_dict)
            except ParameterValidationError as e:
                return {"success": False, "message": str(e), "validation_error": True} 