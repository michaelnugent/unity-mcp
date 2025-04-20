"""
Defines tools for managing GameObjects within Unity scenes through the MCP server.

This module provides functionality for creating, modifying, and manipulating GameObjects
in Unity scenes, including standard operations like instantiation, destruction,
and property modification.
"""
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal, TypedDict
from mcp.server.fastmcp import FastMCP, Context
from unity_connection import get_unity_connection

class GameObjectInfo(TypedDict):
    """Information about a Unity GameObject"""
    name: str
    id: str
    active: bool
    tag: str
    layer: int
    components: List[str]
    children: List[str]
    position: Dict[str, float]
    rotation: Dict[str, float]
    scale: Dict[str, float]
    path: str

def register_game_object_tools(mcp: FastMCP):
    """Registers GameObject management tools with the MCP server."""

    @mcp.tool()
    async def manage_game_objects(
        ctx: Context,
        action: Literal['create', 'destroy', 'find', 'get_children', 'get_components', 'set_active', 'set_position', 'set_rotation', 'set_scale', 'set_parent', 'instantiate', 'duplicate'],
        name: Optional[str] = None,
        object_id: Optional[str] = None,
        position: Optional[Dict[str, float]] = None,
        rotation: Optional[Dict[str, float]] = None,
        scale: Optional[Dict[str, float]] = None,
        parent_id: Optional[str] = None,
        prefab_path: Optional[str] = None,
        active: Optional[bool] = None,
        tag: Optional[str] = None,
        layer: Optional[int] = None,
        include_inactive: Optional[bool] = None,
        recursive: Optional[bool] = None,
        component_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Manages Unity GameObject operations.
        
        This tool provides functionality to create, modify, and manipulate GameObjects
        in Unity scenes, including operations like instantiation, property changes,
        hierarchy management, and more.
        
        Args:
            ctx: The MCP context, containing runtime information.
            action: The GameObject operation to perform. Valid options include:
                - 'create': Create a new empty GameObject (requires name)
                - 'destroy': Destroy a GameObject (requires object_id)
                - 'find': Find GameObjects by name or other criteria
                - 'get_children': Get children of a GameObject (requires object_id)
                - 'get_components': Get components of a GameObject (requires object_id)
                - 'set_active': Set a GameObject's active state (requires object_id and active)
                - 'set_position': Set a GameObject's position (requires object_id and position)
                - 'set_rotation': Set a GameObject's rotation (requires object_id and rotation)
                - 'set_scale': Set a GameObject's scale (requires object_id and scale)
                - 'set_parent': Set a GameObject's parent (requires object_id and parent_id)
                - 'instantiate': Instantiate a GameObject from a prefab (requires prefab_path)
                - 'duplicate': Duplicate an existing GameObject (requires object_id)
            name: Name for a new or instantiated GameObject.
            object_id: ID of the GameObject to operate on.
            position: Position coordinates as a dictionary with 'x', 'y', 'z' keys.
            rotation: Rotation as a dictionary with 'x', 'y', 'z' or 'x', 'y', 'z', 'w' keys.
            scale: Scale as a dictionary with 'x', 'y', 'z' keys.
            parent_id: ID of the parent GameObject to set.
            prefab_path: Path to the prefab asset for instantiation, relative to Assets folder.
            active: Boolean to set the GameObject's active state.
            tag: Tag to assign to the GameObject.
            layer: Layer to assign to the GameObject.
            include_inactive: Whether to include inactive GameObjects in search results.
            recursive: Whether to perform operations recursively.
            component_name: Name of a specific component to target.
            
        Returns:
            A dictionary with the following fields:
            - success: Boolean indicating if the operation succeeded
            - message: Success message if the operation was successful
            - error: Error message if the operation failed
            - data: Additional data about the operation result, which varies by action:
              - For 'find': List of matching GameObjects
              - For 'get_children': List of child GameObjects
              - For 'get_components': List of component information
              - For 'create'/'instantiate': Information about the created GameObject
              
        Examples:
            - Create a new empty GameObject:
              action="create", name="Player", position={"x": 0, "y": 1, "z": 0}
              
            - Instantiate a prefab:
              action="instantiate", prefab_path="Prefabs/Enemy.prefab", position={"x": 5, "y": 0, "z": 5}
              
            - Find all GameObjects with a specific name:
              action="find", name="Enemy", include_inactive=True
              
            - Set a GameObject's position:
              action="set_position", object_id="abc123", position={"x": 10, "y": 2, "z": 3}
              
            - Set a GameObject's parent:
              action="set_parent", object_id="abc123", parent_id="def456"
              
            - Get all children of a GameObject:
              action="get_children", object_id="abc123", recursive=True
        """
        # Prepare parameters for the C# handler
        params_dict = {
            "action": action.lower(),
            "name": name,
            "objectId": object_id,
            "position": position,
            "rotation": rotation,
            "scale": scale,
            "parentId": parent_id,
            "prefabPath": prefab_path,
            "active": active,
            "tag": tag,
            "layer": layer,
            "includeInactive": include_inactive,
            "recursive": recursive,
            "componentName": component_name
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
            "manage_game_objects",  # First argument for send_command
            params_dict  # Second argument for send_command
        )
        
        # Return the result obtained from Unity
        return result 