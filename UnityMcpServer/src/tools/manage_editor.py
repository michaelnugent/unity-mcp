"""
Defines the manage_editor tool for interacting with the Unity Editor.
"""
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal
from mcp.server.fastmcp import FastMCP, Context
from unity_connection import get_unity_connection

def register_manage_editor_tools(mcp: FastMCP):
    """Registers the manage_editor tool with the MCP server."""

    @mcp.tool()
    async def manage_editor(
        ctx: Context,
        action: Literal['play', 'pause', 'stop', 'get_state', 'get_windows', 'get_active_tool', 
                        'get_selection', 'set_active_tool', 'add_tag', 'remove_tag', 'get_tags', 
                        'add_layer', 'remove_layer', 'get_layers'],
        tagName: Optional[str] = None,
        layerName: Optional[str] = None,
        toolName: Optional[str] = None,
        waitForCompletion: Optional[bool] = None,
        playback_speed: Optional[float] = None,
        frames: Optional[int] = None,
        save_as_path: Optional[str] = None,
        preferences_path: Optional[str] = None,
        preferences_value: Optional[Union[str, int, float, bool, Dict[str, Any], List[Any]]] = None,
        screenshot_path: Optional[str] = None,
        screenshot_width: Optional[int] = None,
        screenshot_height: Optional[int] = None,
        camera_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Manages and controls the Unity Editor state (play mode, preferences, etc).

        This tool allows LLMs to control the Unity Editor programmatically, changing play mode,
        adjusting settings, saving assets, capturing screenshots, and more. It provides a
        high-level interface to common editor operations.

        Args:
            ctx: The MCP context, containing runtime information.
            action: The editor action to perform. Valid options include:
                - 'play': Enter play mode
                - 'pause': Pause or resume play mode
                - 'stop': Exit play mode
                - 'get_state': Get current editor status (playing, paused, etc.)
                - 'get_windows': Get information about open editor windows
                - 'get_active_tool': Get the currently active tool
                - 'get_selection': Get information about the current selection
                - 'set_active_tool': Set the active tool (requires toolName)
                - 'add_tag': Add a tag to the project (requires tagName)
                - 'remove_tag': Remove a tag from the project (requires tagName)
                - 'get_tags': Get a list of all tags in the project
                - 'add_layer': Add a layer to the project (requires layerName)
                - 'remove_layer': Remove a layer from the project (requires layerName)
                - 'get_layers': Get a list of all layers in the project
            tagName: Name of the tag to add or remove (for 'add_tag' and 'remove_tag' actions)
            layerName: Name of the layer to add or remove (for 'add_layer' and 'remove_layer' actions)
            toolName: Name of the tool to activate (for 'set_active_tool' action)
            waitForCompletion: Whether to wait for completion of the action
            playback_speed: Playback speed multiplier (e.g., 0.5 for half speed, 2.0 for double speed)
                           Valid range is typically 0.0 to 10.0.
            frames: Number of frames to step.
            save_as_path: Path to save scene.
                        Example: "Assets/Scenes/NewScene.unity"
            preferences_path: Path for accessing editor or project preferences.
                            Uses Unity's preference path format,
                            e.g., "General/Auto Refresh" or "Editor/Script Changes While Playing".
            preferences_value: Value to set for preferences or settings.
            screenshot_path: File path for saving the screenshot. Should include filename and extension
                           (e.g., "C:/temp/screenshot.png" or relative to project: "Assets/screenshot.png").
            screenshot_width: Width of the screenshot in pixels. If not specified, uses the current game view size.
            screenshot_height: Height of the screenshot in pixels. If not specified, uses the current game view size.
            camera_name: Name of the camera to use for taking a screenshot. If not specified, uses the main camera.

        Returns:
            A dictionary with the following fields:
            - success: Boolean indicating if the operation succeeded
            - message: Success message if the operation was successful
            - error: Error message if the operation failed
            - data: Additional data about the operation result, which varies by action:
              - For 'get_state': Current editor state (e.g., {"isPlaying": true, "isPaused": false})
              - For 'get_windows': List of open editor windows
              - For 'get_active_tool': Information about the active tool
              - For 'get_selection': Information about the current selection
              - For 'get_tags': List of all tags in the project
              - For 'get_layers': List of all layers in the project
            
        Examples:
            - Enter play mode:
              action="play"
              
            - Pause play mode:
              action="pause"
              
            - Get editor state:
              action="get_state"
              
            - Get current selection:
              action="get_selection"
              
            - Add a tag:
              action="add_tag", tagName="Enemy"
              
            - Get all tags:
              action="get_tags"
              
            - Add a layer:
              action="add_layer", layerName="Obstacles"
        """
        # Prepare parameters for the C# handler (convert from Python snake_case to C# camelCase where needed)
        params_dict = {
            "action": action.lower(),
            "tagName": tagName,
            "layerName": layerName,
            "toolName": toolName,
            "waitForCompletion": waitForCompletion,
            "playbackSpeed": playback_speed,
            "frames": frames,
            "saveAsPath": save_as_path,
            "preferencesPath": preferences_path,
            "preferencesValue": preferences_value,
            "screenshotPath": screenshot_path,
            "screenshotWidth": screenshot_width,
            "screenshotHeight": screenshot_height,
            "cameraName": camera_name
        }
        
        # Remove None values to avoid sending unnecessary nulls
        params_dict = {k: v for k, v in params_dict.items() if v is not None}

        # Get the current asyncio event loop
        loop = asyncio.get_running_loop()
        # Get the Unity connection instance
        connection = get_unity_connection()
        
        # Run the synchronous send_command in the default executor (thread pool)
        # This prevents blocking the main async event loop
        result = await loop.run_in_executor(
            None,  # Use default executor
            connection.send_command,  # The function to call
            "manage_editor",  # First argument for send_command
            params_dict  # Second argument for send_command
        )
        
        # Return the result obtained from Unity
        return result