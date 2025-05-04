"""
Defines tools for managing the Unity Editor through the MCP server.

This module provides functionality for controlling the Unity Editor state and settings,
including play mode, editor tools, and editor window management.
"""
import asyncio
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from .base_tool import BaseTool
from unity_connection import ParameterValidationError
import serialization_utils

class EditorTool(BaseTool):
    """Tool for managing Unity Editor state and settings."""
    
    tool_name = "manage_editor"
    
    # Define required parameters for each action
    required_params = {
        "get_state": {},
        "enter_play_mode": {},
        "exit_play_mode": {},
        "pause": {},
        "step": {},
        "get_active_tool": {},
        "set_active_tool": {"tool_name": str},
        "get_selection": {},
        "set_selection": {"object_paths": list},
        "take_screenshot": {"save_path": str},
        "set_editor_pref": {"pref_name": str, "pref_value": object, "pref_type": str},
        "get_editor_pref": {"pref_name": str, "pref_type": str},
    }
    
    # Define parameters that might contain Vector3 values for editor operations
    vector3_params = ["camera_position", "gizmo_position"]
    
    # Define parameters that might contain Euler angles (will be converted to Quaternion)
    euler_params = ["camera_rotation", "gizmo_rotation"]
    
    # Define parameters that might contain Color values for editor settings
    color_params = ["wireframe_color", "selection_color", "background_color", "grid_color"]
    
    def post_process_response(self, response: Dict[str, Any], action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance response data with additional information.
        
        Args:
            response: The raw response from Unity
            action: The action that was performed
            params: The parameters that were sent
            
        Returns:
            The processed response with enhanced data
        """
        # For successful responses, enhance with additional data
        if response.get("success") and action in ["get_state", "get_selection", "get_active_tool", "get_editor_pref"]:
            if "data" not in response:
                response["data"] = {}
            
            # For state retrieval, add comprehensive state information
            if action == "get_state":
                # If data is not already present, add default state data
                if not response["data"]:
                    response["data"] = {
                        "isPlaying": False,
                        "isPaused": False,
                        "activeScene": "Unknown",
                        "scenePath": "",
                        "selectedObjects": [],
                        "activeTool": "None",
                        "projectName": "Unknown",
                        "editorVersion": "Unknown",
                        "platform": "Unknown"
                    }
                
                # Add message with information summary
                play_state = "Playing" if response["data"].get("isPlaying") else "Editing"
                pause_state = " (Paused)" if response["data"].get("isPaused") else ""
                active_scene = response["data"].get("activeScene", "Unknown")
                
                response["message"] = f"Editor state retrieved. Mode: {play_state}{pause_state}, Scene: {active_scene}"
            
            # For selection retrieval, add selection details
            elif action == "get_selection":
                selection = response["data"].get("selectedObjects", [])
                selection_count = len(selection)
                
                if selection_count == 0:
                    response["message"] = "No objects selected"
                elif selection_count == 1:
                    response["message"] = f"1 object selected: {selection[0]}"
                else:
                    response["message"] = f"{selection_count} objects selected"
                
                # Make sure selectedObjects is always present
                if "selectedObjects" not in response["data"]:
                    response["data"]["selectedObjects"] = []
            
            # For active tool retrieval, add tool details
            elif action == "get_active_tool":
                tool_name = response["data"].get("activeTool", "Unknown")
                response["message"] = f"Active tool: {tool_name}"
                
                # Make sure activeTool is always present
                if "activeTool" not in response["data"]:
                    response["data"]["activeTool"] = "Unknown"
            
            # For editor preference retrieval, include type information
            elif action == "get_editor_pref":
                pref_name = params.get("pref_name", "Unknown")
                pref_value = response["data"].get("prefValue")
                pref_type = response["data"].get("prefType", "Unknown")
                
                response["message"] = f"Editor preference '{pref_name}' ({pref_type}): {pref_value}"
                
                # Make sure preference data is always present
                if "prefValue" not in response["data"]:
                    response["data"]["prefValue"] = None
                if "prefType" not in response["data"]:
                    response["data"]["prefType"] = "Unknown"
                if "prefName" not in response["data"]:
                    response["data"]["prefName"] = pref_name
        
        return response

    @staticmethod
    def register_manage_editor_tools(mcp: FastMCP):
        """Register editor management tools with the MCP server.
        
        Args:
            mcp: The FastMCP server to register with
        """
        @mcp.tool()
        async def manage_editor(
            ctx: Context,
            action: str,
            tool_name: Optional[str] = None,
            object_paths: Optional[List[str]] = None,
            save_path: Optional[str] = None,
            pref_name: Optional[str] = None,
            pref_value: Optional[Any] = None,
            pref_type: Optional[str] = None,
            supersize: Optional[int] = None,
            width: Optional[int] = None,
            height: Optional[int] = None,
            capture_alpha: Optional[bool] = None,
            disable_post_effects: Optional[bool] = None
        ) -> Dict[str, Any]:
            """Manage Unity Editor state and settings.
            
            Args:
                ctx: The MCP context
                action: Action to perform:
                    - get_state: Get the current editor state
                    - enter_play_mode: Enter play mode
                    - exit_play_mode: Exit play mode
                    - pause: Pause the editor
                    - step: Step the editor frame
                    - get_active_tool: Get the current active editor tool
                    - set_active_tool: Set the active editor tool
                    - get_selection: Get the currently selected GameObjects
                    - set_selection: Set the selection to the given GameObjects
                    - take_screenshot: Take a screenshot
                    - set_editor_pref: Set an editor preference
                    - get_editor_pref: Get an editor preference
                tool_name: Name of the editor tool to activate (for set_active_tool)
                object_paths: List of GameObject paths to select (for set_selection)
                save_path: Path to save screenshot to (for take_screenshot)
                pref_name: Name of the editor preference (for get/set_editor_pref)
                pref_value: Value to set the editor preference to (for set_editor_pref)
                pref_type: Type of editor preference (for get/set_editor_pref)
                supersize: Supersize factor for screenshot (for take_screenshot)
                width: Width for screenshot (for take_screenshot)
                height: Height for screenshot (for take_screenshot)
                capture_alpha: Whether to capture alpha channel (for take_screenshot)
                disable_post_effects: Whether to disable post-processing effects (for take_screenshot)
                
            Returns:
                Success or failure with detailed state information when appropriate
            """
            # Create a tool instance with the context
            tool = EditorTool(ctx)
            
            # Prepare parameters
            params = {
                "action": action,
            }
            
            # Add optional parameters if specified
            if tool_name is not None:
                params["tool_name"] = tool_name
                
            if object_paths is not None:
                params["object_paths"] = object_paths
                
            if save_path is not None:
                params["save_path"] = save_path
                
            if pref_name is not None:
                params["pref_name"] = pref_name
                
            if pref_value is not None:
                params["pref_value"] = pref_value
                
            if pref_type is not None:
                params["pref_type"] = pref_type
                
            if supersize is not None:
                params["supersize"] = supersize
                
            if width is not None:
                params["width"] = width
                
            if height is not None:
                params["height"] = height
                
            if capture_alpha is not None:
                params["capture_alpha"] = capture_alpha
                
            if disable_post_effects is not None:
                params["disable_post_effects"] = disable_post_effects
            
            # Send the command to Unity
            return await tool.send_command_async(tool.tool_name, params)