"""
Defines the scene management tools for working with Unity scenes.

These tools provide functionality for creating, loading, saving, and manipulating
Unity scenes through the MCP server.
"""
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal, TypedDict
from mcp.server.fastmcp import FastMCP, Context
from unity_connection import get_unity_connection

class SceneInfo(TypedDict):
    """Information about a Unity scene"""
    path: str
    name: str
    buildIndex: int
    isDirty: bool
    isLoaded: bool
    isActive: bool
    rootGameObjects: List[str]

def register_scene_management_tools(mcp: FastMCP):
    """Registers the scene management tools with the MCP server."""

    @mcp.tool()
    async def manage_scenes(
        ctx: Context,
        action: Literal['create', 'load', 'save', 'close', 'new', 'get_active', 'get_loaded', 'set_active', 'add_to_build', 'remove_from_build'],
        scene_path: Optional[str] = None,
        scene_name: Optional[str] = None,
        add_to_build: Optional[bool] = None,
        build_index: Optional[int] = None,
        additive: Optional[bool] = None,
        save_current: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Manages Unity scene operations.
        
        This tool provides functionality to work with scenes in Unity, including
        creating, loading, saving, and performing other scene-related operations.
        It interfaces with Unity's scene management system.
        
        Args:
            ctx: The MCP context, containing runtime information.
            action: The scene operation to perform. Valid options include:
                - 'create': Create a new scene file (requires scene_path)
                - 'load': Load a scene (requires scene_path)
                - 'save': Save current scene or specific scene if scene_path is provided
                - 'close': Close a loaded scene (requires scene_path if multiple scenes loaded)
                - 'new': Create a new empty scene
                - 'get_active': Get information about the currently active scene
                - 'get_loaded': Get information about all loaded scenes
                - 'set_active': Set a loaded scene as the active scene (requires scene_path)
                - 'add_to_build': Add a scene to the build settings (requires scene_path)
                - 'remove_from_build': Remove a scene from build settings (requires scene_path)
            scene_path: Path to the scene file relative to Assets folder, e.g. "Scenes/Level1.unity"
            scene_name: Name for a new scene when using 'create' action
            add_to_build: Whether to add a new scene to build settings when creating
            build_index: The build index to use when adding a scene to build settings
            additive: Whether to load a scene additively (multiple scenes at once)
            save_current: Whether to save the current scene before loading/creating a new one
            
        Returns:
            A dictionary with the following fields:
            - success: Boolean indicating if the operation succeeded
            - message: Success message if the operation was successful
            - error: Error message if the operation failed
            - data: Additional data about the operation result, which varies by action:
              - For 'get_active': Information about the active scene
              - For 'get_loaded': List of information about all loaded scenes
            
        Examples:
            - Create a new scene:
              action="create", scene_path="Assets/Scenes/Level2.unity", scene_name="Level 2", add_to_build=True
              
            - Load a scene:
              action="load", scene_path="Assets/Scenes/MainMenu.unity", additive=False, save_current=True
              
            - Get information about the active scene:
              action="get_active"
              
            - Save the current scene:
              action="save"
              
            - Add a scene to build settings at a specific index:
              action="add_to_build", scene_path="Assets/Scenes/Credits.unity", build_index=5
        """
        # Prepare parameters for the C# handler
        params_dict = {
            "action": action.lower(),
            "scenePath": scene_path,
            "sceneName": scene_name,
            "addToBuild": add_to_build,
            "buildIndex": build_index,
            "additive": additive,
            "saveCurrent": save_current
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
            "manage_scenes",  # First argument for send_command
            params_dict  # Second argument for send_command
        )
        
        # Return the result obtained from Unity
        return result 