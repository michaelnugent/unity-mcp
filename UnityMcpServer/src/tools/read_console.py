"""
Defines tools for reading or clearing the Unity Editor console output.
"""
from typing import Dict, Any, Optional, List, Union, Literal
from mcp.server.fastmcp import FastMCP, Context
from .base_tool import BaseTool
from unity_connection import ParameterValidationError
# Import validation layer functions
from .validation_layer import validate_action

class ConsoleTool(BaseTool):
    """Tool for reading and clearing the Unity console."""
    
    tool_name = "read_console"
    
    # Define required parameters for each action
    required_params = {
        "get": {},
        "clear": {},
    }
    
    # Console operations don't typically use Unity-specific types, but for consistency with other tools:
    vector2_params = []
    vector3_params = []
    euler_params = []
    quaternion_params = []
    color_params = []
    rect_params = []
    bounds_params = []
    
    # Valid message types for validation
    _valid_message_types = ["error", "warning", "log", "exception", "assertion", "all"]
    
    # Valid format types for validation
    _valid_formats = ["plain", "detailed", "json"]
    
    def additional_validation(self, action: str, params: Dict[str, Any]) -> None:
        """Additional validation specific to the console tool."""
        # Validate action is in supported actions
        valid_actions = ["get", "clear"]
        validate_action(action, valid_actions)
        
        # Validate message types if specified
        if "types" in params and params.get("types"):
            types = params["types"]
            if isinstance(types, list):
                for msg_type in types:
                    if msg_type not in self._valid_message_types:
                        raise ParameterValidationError(
                            f"Invalid message type: '{msg_type}'. "
                            f"Valid types are: {', '.join(self._valid_message_types)}"
                        )
            elif isinstance(types, str):
                if types not in self._valid_message_types:
                    raise ParameterValidationError(
                        f"Invalid message type: '{types}'. "
                        f"Valid types are: {', '.join(self._valid_message_types)}"
                    )
        
        # Validate format if specified
        if "format" in params and params.get("format"):
            format_val = params["format"]
            if format_val not in self._valid_formats:
                raise ParameterValidationError(
                    f"Invalid format: '{format_val}'. "
                    f"Valid formats are: {', '.join(self._valid_formats)}"
                )
        
        # Validate count parameter
        if "count" in params and params.get("count") is not None:
            count = params["count"]
            if not isinstance(count, int) or count <= 0:
                raise ParameterValidationError(
                    f"count must be a positive integer, got {count}"
                )
        
        # Validate timestamp format if specified
        if "since_timestamp" in params and params.get("since_timestamp"):
            # Basic ISO 8601 timestamp validation
            timestamp = params["since_timestamp"]
            if not isinstance(timestamp, str):
                raise ParameterValidationError(
                    f"since_timestamp must be a string in ISO 8601 format, got {type(timestamp).__name__}"
                )
            
            # Simple check for ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
            import re
            if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', timestamp):
                raise ParameterValidationError(
                    f"since_timestamp must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS...), got '{timestamp}'"
                )

    @staticmethod
    def register_read_console_tools(mcp: FastMCP):
        """Register console reading tools with the MCP server."""

        @mcp.tool()
        async def read_console(
            ctx: Context,
            action: Optional[str] = "get",
            types: Optional[Union[List[str], str]] = None,
            count: Optional[int] = None,
            filter_text: Optional[str] = None,
            since_timestamp: Optional[str] = None,
            format: Optional[str] = None,
            include_stacktrace: Optional[bool] = None
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
            
            # Default action to 'get' if not specified
            action = action.lower() if action else 'get'
            
            # Prepare parameters for Unity
            params = {
                "action": action,
            }
            
            # Add optional parameters if they exist
            if types is not None:
                params["types"] = types
            if count is not None:
                params["count"] = count
            if filter_text is not None:
                params["filterText"] = filter_text
            if since_timestamp is not None:
                params["sinceTimestamp"] = since_timestamp
            if format is not None:
                params["format"] = format
            if include_stacktrace is not None:
                params["includeStacktrace"] = include_stacktrace
            
            # Send command to Unity
            try:
                response = await console_tool.send_command_async("read_console", params)
                return response
            except ParameterValidationError as e:
                return {"success": False, "message": str(e), "validation_error": True}
            except Exception as e:
                return {"success": False, "message": f"Error reading console: {str(e)}"} 