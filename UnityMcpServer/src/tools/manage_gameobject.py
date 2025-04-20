"""
Defines tools for managing GameObjects within Unity scenes through the MCP server.

This module provides functionality for creating, modifying, and manipulating GameObjects
in Unity scenes, including standard operations like instantiation, destruction,
and property modification.
"""
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal, TypedDict
from mcp.server.fastmcp import FastMCP, Context
from .base_tool import BaseTool
from unity_connection import ParameterValidationError

class GameObjectInfo(TypedDict, total=False):
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

class GameObjectTool(BaseTool):
    """Tool for managing Unity GameObjects."""
    
    tool_name = "manage_gameobject"
    
    # Define required parameters for each action
    required_params = {
        "create": {"name": str},
        "modify": {"target": str},
        "delete": {"target": str},
        "find": {"search_term": str},
        "add_component": {"target": str, "components_to_add": list},
        "remove_component": {"target": str, "components_to_remove": list},
        "set_component_property": {"target": str, "component_properties": dict},
        "instantiate": {"prefab_path": str},
    }
    
    # Define parameters that should be validated as Vector3
    vector3_params = ["position", "rotation", "scale"]
    
    def additional_validation(self, action: str, params: Dict[str, Any]) -> None:
        """Additional validation specific to the GameObject tool."""
        if action == "create" and params.get("saveAsPrefab"):
            if "prefabPath" not in params and "name" not in params:
                raise ParameterValidationError(
                    "Cannot create default prefab path: 'name' parameter is missing."
                )
            if "prefabPath" in params and params["prefabPath"] is not None and not params["prefabPath"].lower().endswith(".prefab"):
                raise ParameterValidationError(
                    f"{self.tool_name} 'create' parameter 'prefabPath' must end with '.prefab'"
                )
    
    @staticmethod
    def register_manage_gameobject_tools(mcp: FastMCP):
        """Register all GameObject management tools with the MCP server."""

        @mcp.tool()
        async def manage_gameobject(
            ctx: Context,
            action: Literal['create', 'modify', 'delete', 'find', 'get_children', 'get_components', 
                         'add_component', 'remove_component', 'set_component_property', 
                         'set_active', 'set_position', 'set_rotation', 'set_scale', 
                         'set_parent', 'instantiate', 'duplicate'],
            target: Optional[str] = None,  # GameObject identifier by name or path
            search_method: Optional[str] = None,
            # --- Combined Parameters for Create/Modify ---
            name: Optional[str] = None,  # Used for both 'create' (new object name) and 'modify' (rename)
            tag: Optional[str] = None,  # Used for both 'create' (initial tag) and 'modify' (change tag)
            parent: Optional[str] = None,  # Used for both 'create' (initial parent) and 'modify' (change parent)
            position: Optional[List[float]] = None,
            rotation: Optional[List[float]] = None,
            scale: Optional[List[float]] = None,
            components_to_add: Optional[List[str]] = None,  # List of component names to add
            primitive_type: Optional[str] = None,
            save_as_prefab: bool = False,
            prefab_path: Optional[str] = None,
            prefab_folder: str = "Assets/Prefabs",
            # --- Parameters for 'modify' ---
            set_active: Optional[bool] = None,
            layer: Optional[str] = None,  # Layer name
            components_to_remove: Optional[List[str]] = None,
            component_properties: Optional[Dict[str, Dict[str, Any]]] = None,
            # --- Parameters for 'find' ---
            search_term: Optional[str] = None,
            find_all: bool = False,
            search_in_children: bool = False,
            search_inactive: bool = False,
            # -- Component Management Arguments --
            component_name: Optional[str] = None,
            # -- Additional Parameters from game_object_management --
            object_id: Optional[str] = None,
            parent_id: Optional[str] = None,
            include_inactive: Optional[bool] = None,
            recursive: Optional[bool] = None,
        ) -> Dict[str, Any]:
            """Manages GameObjects: create, modify, delete, find, and component operations.

            This tool provides functionality to create, modify, and manipulate GameObjects
            in Unity scenes, including operations like instantiation, property changes,
            hierarchy management, and more.

            Args:
                ctx: The MCP context, containing runtime information.
                action: The GameObject operation to perform. Valid options include:
                    - 'create': Create a new empty GameObject (requires name)
                    - 'modify': Modify an existing GameObject (requires target)
                    - 'delete': Delete a GameObject (requires target)
                    - 'find': Find GameObjects by name or other criteria
                    - 'get_children': Get children of a GameObject (requires target)
                    - 'get_components': Get components of a GameObject (requires target)
                    - 'add_component': Add a component to a GameObject (requires target, components_to_add)
                    - 'remove_component': Remove a component from a GameObject (requires target, components_to_remove)
                    - 'set_component_property': Set properties on a component (requires target, component_properties)
                    - 'set_active': Set a GameObject's active state (requires target and set_active)
                    - 'set_position': Set a GameObject's position (requires target and position)
                    - 'set_rotation': Set a GameObject's rotation (requires target and rotation)
                    - 'set_scale': Set a GameObject's scale (requires target and scale)
                    - 'set_parent': Set a GameObject's parent (requires target and parent)
                    - 'instantiate': Instantiate a GameObject from a prefab (requires prefab_path)
                    - 'duplicate': Duplicate an existing GameObject (requires target)
                target: GameObject identifier (name or path string) for modify/delete/component actions.
                search_method: How to find objects ('by_name', 'by_id', 'by_path', etc.). Used with 'find' and some 'target' lookups.
                name: GameObject name - used for both 'create' (initial name) and 'modify' (rename).
                tag: Tag name - used for both 'create' (initial tag) and 'modify' (change tag).
                parent: Parent GameObject reference - used for both 'create' (initial parent) and 'modify' (change parent).
                layer: Layer name - used for both 'create' (initial layer) and 'modify' (change layer).
                component_properties: Dict mapping Component names to their properties to set.
                                      Example: {"Rigidbody": {"mass": 10.0, "useGravity": True}},
                                      To set references:
                                      - Use asset path string for Prefabs/Materials, e.g., {"MeshRenderer": {"material": "Assets/Materials/MyMat.mat"}}
                                      - Use a dict for scene objects/components, e.g.:
                                        {"MyScript": {"otherObject": {"find": "Player", "method": "by_name"}}} (assigns GameObject)
                                        {"MyScript": {"playerHealth": {"find": "Player", "component": "HealthComponent"}}} (assigns Component)
                                      Example set nested property:
                                      - Access shared material: {"MeshRenderer": {"sharedMaterial.color": [1, 0, 0, 1]}}
                components_to_add: List of component names to add.
                position: Position coordinates as a list of [x, y, z] values.
                rotation: Rotation as a list of [x, y, z] Euler angles or quaternion [x, y, z, w] values.
                scale: Scale as a list of [x, y, z] values.
                parent_id: Alternative to parent - ID of the parent GameObject to set.
                prefab_path: Path to the prefab asset for instantiation, relative to Assets folder.
                save_as_prefab: Whether to save the created GameObject as a prefab.
                prefab_folder: Folder to save the prefab in if save_as_prefab is true.
                set_active: Boolean to set the GameObject's active state.
                primitive_type: Type of primitive to create ('Cube', 'Sphere', etc.)
                search_term: Name pattern to search for when finding GameObjects.
                find_all: Whether to return all matching GameObjects or just the first.
                search_in_children: Whether to search in child GameObjects.
                search_inactive: Whether to include inactive GameObjects in search results.
                include_inactive: Alternative to search_inactive - include inactive objects.
                recursive: Whether to perform operations recursively.
                component_name: Name of a specific component to target.
                object_id: Alternative to target - ID of the GameObject to operate on.
                
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
                  action="create", name="Player", position=[0, 1, 0]
                  
                - Instantiate a prefab:
                  action="instantiate", prefab_path="Prefabs/Enemy.prefab", position=[5, 0, 5]
                  
                - Find all GameObjects with a specific name:
                  action="find", search_term="Enemy", find_all=True
                  
                - Set a GameObject's position:
                  action="set_position", target="Player", position=[10, 2, 3]
                  
                - Set a GameObject's parent:
                  action="set_parent", target="Weapon", parent="PlayerHand"
                  
                - Add a component to a GameObject:
                  action="add_component", target="Player", components_to_add=["UnityEngine.BoxCollider"]
                  
                - Set component properties:
                  action="set_component_property", target="Enemy", 
                  component_properties={"Rigidbody": {"mass": 10.0, "useGravity": True}}
            """
            # Create tool instance
            gameobject_tool = GameObjectTool(ctx)
            
            # Handle parameter compatibility between older and newer versions
            if object_id is not None and target is None:
                target = object_id
            
            if parent_id is not None and parent is None:
                parent = parent_id
                
            if include_inactive is not None and search_inactive is False:
                search_inactive = include_inactive
            
            # Prepare parameters, removing None values
            params = {
                "action": action,
                "target": target,
                "searchMethod": search_method,
                "name": name,
                "tag": tag,
                "parent": parent,
                "position": position,
                "rotation": rotation,
                "scale": scale,
                "componentsToAdd": components_to_add,
                "primitiveType": primitive_type,
                "saveAsPrefab": save_as_prefab,
                "prefabPath": prefab_path,
                "prefabFolder": prefab_folder,
                "setActive": set_active,
                "layer": layer,
                "componentsToRemove": components_to_remove,
                "componentProperties": component_properties,
                "searchTerm": search_term,
                "findAll": find_all,
                "searchInChildren": search_in_children,
                "searchInactive": search_inactive,
                "componentName": component_name,
                "recursive": recursive
            }
            
            # --- Handle Prefab Path Logic ---
            if action == "create" and params.get("saveAsPrefab"): 
                if "prefabPath" not in params:
                    if "name" not in params or not params["name"]:
                        return {"success": False, "message": "Cannot create default prefab path: 'name' parameter is missing."}
                    # Use the provided prefab_folder (which has a default) and the name to construct the path
                    constructed_path = f"{prefab_folder}/{params['name']}.prefab"
                    # Ensure clean path separators (Unity prefers '/')
                    params["prefabPath"] = constructed_path.replace("\\", "/")
                elif not params["prefabPath"].lower().endswith(".prefab"):
                    return {"success": False, "message": f"Invalid prefab_path: '{params['prefabPath']}' must end with .prefab"}
            
            # Ensure prefab_folder itself isn't sent if prefabPath was constructed or provided
            # The C# side only needs the final prefabPath
            params.pop("prefabFolder", None) 

            try:
                # Send command with validation through the tool
                return await gameobject_tool.send_command_async("manage_gameobject", params)
            except ParameterValidationError as e:
                return {"success": False, "message": str(e), "validation_error": True} 