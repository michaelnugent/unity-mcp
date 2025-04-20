"""
Defines the manage_scene tool for working with Unity scenes.
"""
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal, Tuple
from mcp.server.fastmcp import FastMCP, Context
from unity_connection import get_unity_connection

def register_manage_scene_tools(mcp: FastMCP):
    """Registers the manage_scene tool with the MCP server."""

    @mcp.tool()
    async def manage_scene(
        ctx: Context,
        action: Literal['open', 'create', 'save', 'save_as', 'add_to_build', 'get_scene_info', 'get_open_scenes', 'close', 'instantiate', 'delete', 'move', 'rotate', 'scale', 'find', 'get_component', 'set_component', 'add_component', 'remove_component', 'get_position', 'get_rotation', 'get_scale', 'set_parent', 'set_active', 'capture_screenshot'],
        path: Optional[str] = None,
        name: Optional[str] = None,
        build_index: Optional[int] = None,
        additive: Optional[bool] = None,
        prefab_path: Optional[str] = None,
        game_object_name: Optional[str] = None,
        component_type: Optional[str] = None,
        component_properties: Optional[Dict[str, Any]] = None,
        position: Optional[Union[List[float], Tuple[float, float, float]]] = None,
        rotation: Optional[Union[List[float], Tuple[float, float, float]]] = None,
        scale: Optional[Union[List[float], Tuple[float, float, float]]] = None,
        parent_name: Optional[str] = None,
        active_state: Optional[bool] = None,
        query: Optional[str] = None,
        include_children: Optional[bool] = None,
        screenshot_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Manages Unity scenes and GameObjects within them.

        This tool allows manipulation of Unity scenes including scene operations (open, save, etc.),
        GameObject manipulation (instantiate, move, rotate, scale), component management,
        and hierarchical operations. It provides a comprehensive interface for scene-related tasks.

        Args:
            ctx: The MCP context, containing runtime information.
            action: The scene action to perform. Valid options include:
                - 'open': Open an existing scene
                - 'create': Create a new scene
                - 'save': Save the current scene
                - 'save_as': Save the current scene to a new path
                - 'add_to_build': Add a scene to the build settings
                - 'get_scene_info': Get information about the current scene
                - 'get_open_scenes': List all currently open scenes
                - 'close': Close the current scene
                - 'instantiate': Instantiate a prefab or primitive in the scene
                - 'delete': Delete a GameObject from the scene
                - 'move': Move a GameObject to a new position
                - 'rotate': Rotate a GameObject
                - 'scale': Scale a GameObject
                - 'find': Find a GameObject by name or tag
                - 'get_component': Get component data from a GameObject
                - 'set_component': Modify component properties on a GameObject
                - 'add_component': Add a component to a GameObject
                - 'remove_component': Remove a component from a GameObject
                - 'get_position': Get the position of a GameObject
                - 'get_rotation': Get the rotation of a GameObject
                - 'get_scale': Get the scale of a GameObject
                - 'set_parent': Set the parent of a GameObject
                - 'set_active': Set the active state of a GameObject
                - 'capture_screenshot': Take a screenshot of the scene view
            path: Path to the scene file (for 'open', 'save_as', 'add_to_build')
                e.g., "Assets/Scenes/MainLevel.unity"
            name: Name for a new scene or for a GameObject to find, create, or modify
            build_index: Index in the build settings for 'add_to_build' action
            additive: Whether to open a scene additively (true) or replace the current scene (false)
            prefab_path: Path to a prefab to instantiate, e.g., "Assets/Prefabs/Enemy.prefab"
            game_object_name: Name of the GameObject to manipulate
            component_type: Type of component to get, set, add, or remove
                e.g., "UnityEngine.Transform", "UnityEngine.Rigidbody", "MyCustomComponent"
            component_properties: Dictionary of property names and values to set on a component
            position: 3D position coordinates as [x, y, z] for move operations
            rotation: Rotation euler angles as [x, y, z] for rotate operations
            scale: Scale values as [x, y, z] for scale operations
            parent_name: Name of the GameObject to set as parent
            active_state: Boolean to set GameObject's active state (true/false)
            query: Search query for finding GameObjects
            include_children: Whether to include children in operations like find
            screenshot_path: Path to save a screenshot, e.g., "Assets/Screenshots/scene_view.png"

        Returns:
            A dictionary with the following fields:
            - success: Boolean indicating if the operation succeeded
            - message: Success message if the operation was successful
            - error: Error message if the operation failed
            - data: Additional data about the operation result, which varies by action:
              - For 'get_scene_info': Scene information (name, path, etc.)
              - For 'get_open_scenes': List of open scenes
              - For 'find': List of found GameObjects
              - For 'get_component'/'get_position'/'get_rotation'/'get_scale': Requested data
              - For 'capture_screenshot': Path to the saved screenshot
              
        Examples:
            - Open a scene:
              action="open", path="Assets/Scenes/Level1.unity"
              
            - Create a new empty scene:
              action="create", name="NewLevel"
              
            - Save the current scene:
              action="save"
              
            - Instantiate a prefab:
              action="instantiate", prefab_path="Assets/Prefabs/Player.prefab", position=[0, 0, 0]
              
            - Move a GameObject:
              action="move", game_object_name="Player", position=[10, 0, 5]
              
            - Get component data:
              action="get_component", game_object_name="Enemy", component_type="UnityEngine.AI.NavMeshAgent"
              
            - Add a component:
              action="add_component", game_object_name="Cube", component_type="UnityEngine.Rigidbody"
              
            - Find GameObjects:
              action="find", query="Player", include_children=True
        """
        # Prepare parameters for the C# handler
        params_dict = {
            "action": action.lower(),
            "path": path,
            "name": name,
            "buildIndex": build_index,
            "additive": additive,
            "prefabPath": prefab_path,
            "gameObjectName": game_object_name,
            "componentType": component_type,
            "componentProperties": component_properties,
            "position": position,
            "rotation": rotation,
            "scale": scale,
            "parentName": parent_name,
            "activeState": active_state,
            "query": query,
            "includeChildren": include_children,
            "screenshotPath": screenshot_path
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
            "manage_scene",  # First argument for send_command
            params_dict  # Second argument for send_command
        )
        
        # Return the result obtained from Unity
        return result