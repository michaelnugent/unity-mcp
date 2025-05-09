from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, Any
from .base_tool import BaseTool
import os
import base64
from exceptions import ParameterValidationError
# Import the validation layer functions
from .validation_layer import validate_script_code, validate_asset_path

class ScriptTool(BaseTool):
    """Tool for managing Unity scripts."""
    
    tool_name = "manage_script"
    
    # Define required parameters for each action
    required_params = {
        "create": {"name": str, "path": str, "contents": str},
        "read": {"name": str, "path": str},
        "update": {"name": str, "path": str, "contents": str},
        "delete": {"name": str, "path": str},
    }
    
    # Script operations don't typically use Unity-specific types, but for consistency with other tools:
    vector2_params = []
    vector3_params = []
    euler_params = []
    quaternion_params = []
    color_params = []
    rect_params = []
    bounds_params = []
    
    def additional_validation(self, action: str, params: Dict[str, Any]) -> None:
        """Additional validation specific to the script tool."""
        if action in ["create", "update"]:
            # Check for contents or encodedContents
            if not params.get("contents") and not params.get("encodedContents"):
                raise ParameterValidationError(
                    f"{self.tool_name} '{action}' action requires 'contents' parameter"
                )
            
            # Validate script contents if provided directly (not encoded)
            if params.get("contents") and params.get("scriptType"):
                validate_script_code(
                    params["contents"], 
                    params.get("scriptType", "MonoBehaviour")
                )
            
            # Validate script name for C# standards
            if params.get("name") and not params["name"].endswith(".cs"):
                # Check for valid C# identifier name 
                import re
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', params["name"]):
                    raise ParameterValidationError(
                        f"Script name '{params['name']}' must be a valid C# identifier "
                        f"(starting with letter or underscore, containing only letters, numbers, and underscores)"
                    )
        
        # Validate path format for all actions
        if params.get("path"):
            validate_asset_path(params["path"], must_exist=(action != "create"))

    @staticmethod
    def register_manage_script_tools(mcp: FastMCP):
        """Register all script management tools with the MCP server."""

        @mcp.tool()
        async def manage_script(
            ctx: Context,
            action: str,
            name: str,
            path: str,
            contents: str,
            script_type: str,
            namespace: str
        ) -> Dict[str, Any]:
            """Manages C# scripts in Unity (create, read, update, delete).
            Make reference variables public for easier access in the Unity Editor.

            Args:
                action: Operation ('create', 'read', 'update', 'delete').
                name: Script name (no .cs extension).
                path: Asset path (default: "Assets/").
                contents: C# code for 'create'/'update'.
                script_type: Type hint (e.g., 'MonoBehaviour').
                namespace: Script namespace.

            Returns:
                Dictionary with results ('success', 'message', 'data').
            """
            try:
                # Create tool instance
                script_tool = ScriptTool(ctx)
                
                # Prepare parameters for Unity
                params = {
                    "action": action,
                    "name": name,
                    "path": path,
                    "namespace": namespace,
                    "scriptType": script_type
                }
                
                # Base64 encode the contents if they exist to avoid JSON escaping issues
                if contents is not None:
                    if action in ['create', 'update']:
                        # Encode content for safer transmission
                        params["encodedContents"] = base64.b64encode(contents.encode('utf-8')).decode('utf-8')
                        params["contentsEncoded"] = True
                    else:
                        params["contents"] = contents
                
                # Remove None values so they don't get sent as null
                params = {k: v for k, v in params.items() if v is not None}

                # Send command to Unity with validation (using async version)
                response = await script_tool.send_command_async("manage_script", params)
                
                # Process response from Unity
                if response.get("success"):
                    # If the response contains base64 encoded content, decode it
                    if response.get("data", {}).get("contentsEncoded"):
                        decoded_contents = base64.b64decode(response["data"]["encodedContents"]).decode('utf-8')
                        response["data"]["contents"] = decoded_contents
                        del response["data"]["encodedContents"]
                        del response["data"]["contentsEncoded"]
                    
                    return {"success": True, "message": response.get("message", "Operation successful."), "data": response.get("data")}
                else:
                    return {"success": False, "message": response.get("error", "An unknown error occurred.")}

            except ParameterValidationError as e:
                return {"success": False, "message": str(e), "validation_error": True}
            except Exception as e:
                # Handle Python-side errors (e.g., connection issues)
                return {"success": False, "message": f"Python error managing script: {str(e)}"}

def validate_script_code(code: Any) -> None:
    """Validate a script code parameter.

    Args:
        code: The script code to validate
    
    Returns:
        None: This function doesn't return anything but raises exceptions on validation failure
    
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(code, str):
        raise ParameterValidationError(f"Script code must be a string, got {type(code).__name__}: {code}")
    
    # Check for empty code
    if not code:
        raise ParameterValidationError("Script code cannot be empty")