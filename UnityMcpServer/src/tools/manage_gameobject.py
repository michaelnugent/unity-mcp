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
import serialization_utils
from type_converters import (
    is_serialized_unity_object, extract_type_info, get_unity_components,
    get_unity_children, find_component_by_type
)
# Import validation layer functions
from .validation_layer import (
    validate_asset_path, validate_gameobject_path, 
    validate_component_type, validate_action,
    validate_parameters_by_action, create_action_validator
)

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
    """Tool for managing Unity GameObjects.
    
    This tool provides operations for creating, modifying, finding, and manipulating 
    GameObjects in Unity scenes. It includes methods for managing properties, components,
    hierarchies, and transformations.
    """
    
    tool_name = "manage_gameobject"
    
    # Define required parameters for each action
    required_params = {
        "create": {"name": str},
        "modify": {"target": str},
        "delete": {"target": str},
        "find": {"searchTerm": str},
        "get_children": {"target": str},
        "get_components": {"target": str},
        "add_component": {"target": str, "componentsToAdd": list},
        "remove_component": {"target": str, "componentsToRemove": list},
        "set_component_property": {"target": str, "componentProperties": dict},
        "set_active": {"target": str, "setActive": bool},
        "set_position": {"target": str, "position": list},
        "set_rotation": {"target": str, "rotation": list},
        "set_scale": {"target": str, "scale": list},
        "set_parent": {"target": str, "parent": str},
        "instantiate": {"prefabPath": str},
        "duplicate": {"target": str},
    }
    
    # Define parameters that should be validated as Vector3
    vector3_params = ["position", "scale"]
    
    # Define parameters that should be validated as Euler angles (will be converted to Quaternion)
    euler_params = ["rotation"]
    
    # Define parameters expected to be serialized Unity objects
    gameobject_params = ["gameobject", "parent_gameobject", "child_gameobject"]
    component_params = ["component", "target_component"]
    transform_params = ["transform"]
    
    # Define valid primitive types for validation
    _valid_primitive_types = [
        "Cube", "Sphere", "Capsule", "Cylinder", "Plane", "Quad"
    ]
    
    # Define valid search methods for validation
    _valid_search_methods = [
        "by_name", "by_tag", "by_path", "by_id", "by_type", "by_component"
    ]
    
    def additional_validation(self, action: str, params: Dict[str, Any]) -> None:
        """Additional validation specific to the GameObject tool.
        
        Args:
            action: The action being performed
            params: The parameters to validate
            
        Raises:
            ParameterValidationError: If validation fails
        """
        try:
            # Validate action is supported
            valid_actions = [
                "create", "modify", "delete", "find", "get_children", "get_components", 
                "add_component", "remove_component", "set_component_property", 
                "set_active", "set_position", "set_rotation", "set_scale", 
                "set_parent", "instantiate", "duplicate"
            ]
            validate_action(action, valid_actions)
            
            # Validate prefab path format and extension
            if action in ["create", "instantiate"] and params.get("prefabPath"):
                try:
                    validate_asset_path(
                        params["prefabPath"], 
                        must_exist=(action == "instantiate"),
                        extension=".prefab"
                    )
                except Exception as e:
                    raise ParameterValidationError(f"Invalid prefab path: {str(e)}")
            
            # Validate save_as_prefab requires prefab_path or name
            if action == "create" and params.get("saveAsPrefab"):
                if "prefabPath" not in params and "name" not in params:
                    raise ParameterValidationError(
                        "Cannot create default prefab path: 'name' parameter is missing"
                    )
            
            # Validate GameObject target
            if "target" in params and params.get("target"):
                try:
                    validate_gameobject_path(
                        params["target"],
                        must_exist=(action not in ["create", "instantiate"])
                    )
                except Exception as e:
                    raise ParameterValidationError(f"Invalid target GameObject: {str(e)}")
            
            # Validate parent reference
            if "parent" in params and params.get("parent"):
                try:
                    validate_gameobject_path(params["parent"], must_exist=True)
                except Exception as e:
                    raise ParameterValidationError(f"Invalid parent GameObject: {str(e)}")
            
            # Validate components to add/remove
            if "componentsToAdd" in params and params.get("componentsToAdd"):
                for component_type in params["componentsToAdd"]:
                    try:
                        validate_component_type(component_type)
                    except Exception as e:
                        raise ParameterValidationError(f"Invalid component type to add: {component_type} - {str(e)}")
                    
            if "componentsToRemove" in params and params.get("componentsToRemove"):
                for component_type in params["componentsToRemove"]:
                    try:
                        validate_component_type(component_type)
                    except Exception as e:
                        raise ParameterValidationError(f"Invalid component type to remove: {component_type} - {str(e)}")
                    
            # Validate component_properties format and structure
            if "componentProperties" in params and params.get("componentProperties"):
                if not isinstance(params["componentProperties"], dict):
                    raise ParameterValidationError(
                        "componentProperties must be a dictionary mapping component types to property dictionaries"
                    )
                
                # Check each component's properties
                for component_type, properties in params["componentProperties"].items():
                    try:
                        validate_component_type(component_type)
                    except Exception as e:
                        raise ParameterValidationError(f"Invalid component type in properties: {component_type} - {str(e)}")
                    
                    if not isinstance(properties, dict):
                        raise ParameterValidationError(
                            f"Properties for component '{component_type}' must be a dictionary"
                        )
            
            # Validate primitive type
            if "primitiveType" in params and params.get("primitiveType"):
                if params["primitiveType"] not in self._valid_primitive_types:
                    raise ParameterValidationError(
                        f"Invalid primitiveType: '{params['primitiveType']}'. "
                        f"Valid types are: {', '.join(self._valid_primitive_types)}"
                    )
                    
            # Validate search method
            if "searchMethod" in params and params.get("searchMethod"):
                if params["searchMethod"] not in self._valid_search_methods:
                    raise ParameterValidationError(
                        f"Invalid searchMethod: '{params['searchMethod']}'. "
                        f"Valid methods are: {', '.join(self._valid_search_methods)}"
                    )
            
            # Validate position, rotation, and scale for vector3 format
            # (Base validation will convert these, but we can do additional checks here)
            for vector_param in ["position", "rotation", "scale"]:
                if vector_param in params and params.get(vector_param) is not None:
                    value = params[vector_param]
                    
                    # Check if it's a list/tuple of 3 numbers
                    if isinstance(value, (list, tuple)):
                        if len(value) != 3:
                            raise ParameterValidationError(
                                f"{vector_param} must be a list/tuple of 3 values, got {len(value)}"
                            )
                        
                        for i, component in enumerate(value):
                            if not isinstance(component, (int, float)):
                                raise ParameterValidationError(
                                    f"{vector_param}[{i}] must be a number, got {type(component).__name__}: {component}"
                                )
                                
        except ParameterValidationError:
            # Re-raise ParameterValidationError as is to maintain the original message
            raise
        except Exception as e:
            # Wrap other exceptions with more context
            raise ParameterValidationError(f"Error validating GameObject parameters: {str(e)}")
    
    def post_process_response(self, response: Dict[str, Any], action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process the response to handle serialized GameObject objects.
        
        For certain actions like 'find', 'get_children', or 'instantiate', the response
        may contain serialized GameObject objects that need special handling.
        
        Args:
            response: The response from Unity
            action: The action that was performed
            params: The parameters that were sent
            
        Returns:
            The processed response
        """
        try:
            # Process responses containing GameObjects
            if action in ["find", "get_children", "get_components", "instantiate", "create"]:
                # Check if this is a successful response with data
                if response.get("success") and "data" in response:
                    data = response["data"]
                    
                    # For find/get_children, the data might be a list of GameObjects
                    if isinstance(data, list):
                        processed_list = []
                        for item in data:
                            if is_serialized_unity_object(item):
                                processed_list.append(self.process_serialized_unity_object(item))
                            else:
                                processed_list.append(item)
                        response["data"] = processed_list
                        
                    # For single GameObject responses
                    elif isinstance(data, dict) and is_serialized_unity_object(data):
                        response["data"] = self.process_serialized_unity_object(data)
                    
                    # Add count information to message for list results
                    if isinstance(response["data"], list):
                        count = len(response["data"])
                        if action == "find":
                            search_term = params.get("searchTerm", "")
                            search_method = params.get("searchMethod", "by_name")
                            if count == 0:
                                response["message"] = f"No GameObjects found matching '{search_term}' using method '{search_method}'"
                            elif count == 1:
                                response["message"] = f"Found 1 GameObject matching '{search_term}' using method '{search_method}'"
                            else:
                                response["message"] = f"Found {count} GameObjects matching '{search_term}' using method '{search_method}'"
                        
                        elif action == "get_children":
                            target = params.get("target", "")
                            if count == 0:
                                response["message"] = f"GameObject '{target}' has no children"
                            elif count == 1:
                                response["message"] = f"GameObject '{target}' has 1 child"
                            else:
                                response["message"] = f"GameObject '{target}' has {count} children"
                        
                        elif action == "get_components":
                            target = params.get("target", "")
                            if count == 0:
                                response["message"] = f"GameObject '{target}' has no components"
                            elif count == 1:
                                response["message"] = f"GameObject '{target}' has 1 component"
                            else:
                                response["message"] = f"GameObject '{target}' has {count} components"
            
            # Enhanced messages for creation and manipulation actions
            elif action in ["create", "instantiate", "duplicate", "modify"]:
                if response.get("success"):
                    if action == "create":
                        name = params.get("name", "GameObject")
                        response["message"] = f"Created new GameObject '{name}'"
                    elif action == "instantiate":
                        prefab_path = params.get("prefabPath", "")
                        response["message"] = f"Instantiated GameObject from prefab '{prefab_path}'"
                    elif action == "duplicate":
                        target = params.get("target", "")
                        response["message"] = f"Duplicated GameObject '{target}'"
                    elif action == "modify":
                        target = params.get("target", "")
                        response["message"] = f"Modified GameObject '{target}'"
            
            # Enhanced messages for component operations
            elif action in ["add_component", "remove_component", "set_component_property"]:
                if response.get("success"):
                    target = params.get("target", "")
                    if action == "add_component":
                        components = params.get("componentsToAdd", [])
                        if len(components) == 1:
                            response["message"] = f"Added component '{components[0]}' to GameObject '{target}'"
                        else:
                            response["message"] = f"Added {len(components)} components to GameObject '{target}'"
                    elif action == "remove_component":
                        components = params.get("componentsToRemove", [])
                        if len(components) == 1:
                            response["message"] = f"Removed component '{components[0]}' from GameObject '{target}'"
                        else:
                            response["message"] = f"Removed {len(components)} components from GameObject '{target}'"
                    elif action == "set_component_property":
                        component_count = len(params.get("componentProperties", {}))
                        response["message"] = f"Updated properties on {component_count} components on GameObject '{target}'"
                    
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Error in post_process_response: {str(e)}")
            # If we already have a failure response, don't overwrite it
            if not response.get("success", True):
                response["message"] = f"Error processing response: {str(e)}"
                
        return response
        
    def process_serialized_unity_object(self, obj: Any) -> Any:
        """Process a serialized Unity GameObject object for client consumption.
        
        Args:
            obj: The serialized GameObject object
            
        Returns:
            A processed version of the GameObject with enhanced metadata
        """
        if not is_serialized_unity_object(obj):
            return obj
            
        try:
            # Extract metadata for easy access
            metadata = serialization_utils.get_serialization_info(obj)
            
            # Create a processed version with key GameObject information highlighted
            result = {
                # Include the base serialized object
                **obj,
                
                # Add computed properties for easier access
                "components_summary": self._get_components_summary(obj),
                "children_count": len(get_unity_children(obj)),
                "full_path": serialization_utils.get_gameobject_path(obj),
                "transform_data": self._get_transform_data(obj)
            }
            
            return result
        except Exception as e:
            # On error, return the original object with an error note
            if isinstance(obj, dict):
                obj["processing_error"] = str(e)
            return obj
    
    def _get_components_summary(self, gameobject: Dict[str, Any]) -> List[str]:
        """Get a summary of the components on a GameObject.
        
        Args:
            gameobject: The serialized GameObject
            
        Returns:
            List of component type names
        """
        try:
            components = get_unity_components(gameobject)
            summary = []
            
            for component in components:
                type_info = extract_type_info(component)
                if type_info and "unity_type" in type_info:
                    # Get the short name (without namespace)
                    full_type = type_info["unity_type"]
                    short_type = full_type.split(".")[-1] if "." in full_type else full_type
                    summary.append(short_type)
                    
            return summary
        except Exception as e:
            # On error, return an empty list with a note
            print(f"Error getting component summary: {str(e)}")
            return ["Error: " + str(e)]
    
    def _get_transform_data(self, gameobject: Dict[str, Any]) -> Dict[str, Any]:
        """Extract transform data from a GameObject.
        
        Args:
            gameobject: The serialized GameObject
            
        Returns:
            Dictionary with position, rotation, and scale information
        """
        try:
            transform = find_component_by_type(gameobject, "Transform")
            if not transform:
                return {}
                
            result = {}
            
            # Try to get position, rotation, and scale using dot notation
            position = serialization_utils.get_serialized_value(transform, "position")
            if position:
                result["position"] = position
                
            local_position = serialization_utils.get_serialized_value(transform, "localPosition")
            if local_position:
                result["localPosition"] = local_position
                
            rotation = serialization_utils.get_serialized_value(transform, "rotation")
            if rotation:
                result["rotation"] = rotation
                
            euler_angles = serialization_utils.get_serialized_value(transform, "eulerAngles")
            if euler_angles:
                result["eulerAngles"] = euler_angles
                
            local_scale = serialization_utils.get_serialized_value(transform, "localScale")
            if local_scale:
                result["localScale"] = local_scale
                
            return result
        except Exception as e:
            # On error, return an empty dict with a note
            return {"error": str(e)}
    
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
            
            # Convert snake_case parameter names to camelCase for Unity-side compatibility
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
            
            # Remove None values to avoid sending unnecessary parameters
            params = {k: v for k, v in params.items() if v is not None}
            
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

def validate_component_type(component_type: Any) -> None:
    """Validate a component type parameter.

    Args:
        component_type: The component type to validate
    
    Returns:
        None: This function doesn't return anything but raises exceptions on validation failure
    
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(component_type, str):
        raise ParameterValidationError(f"Component type must be a string, got {type(component_type).__name__}: {component_type}")
    
    # Check for empty type
    if not component_type:
        raise ParameterValidationError("Component type cannot be empty")
        
    # If no namespace is provided, assume the component name is valid
    # Unity components often use shorthand names like "Transform" instead of "UnityEngine.Transform"
    if "." not in component_type:
        # Ensure it's not empty after split
        if not component_type.strip():
            raise ParameterValidationError("Component name cannot be empty")
        return
        
    # Validate component type format (should be like UnityEngine.Transform or FullNamespace.ComponentName)
    if not (component_type.split(".")[-1] and component_type.split(".")[0]):
        raise ParameterValidationError(f"Component type must be in format 'Namespace.ComponentName', got: {component_type}")

def validate_gameobject_path(path: Any, must_exist: bool = False) -> None:
    """Validate a GameObject path parameter.

    Args:
        path: The path value to validate
        must_exist: Whether the GameObject must exist (cannot be validated client-side, only format check)
    
    Returns:
        None: This function doesn't return anything but raises exceptions on validation failure
    
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(path, str):
        raise ParameterValidationError(f"GameObject path must be a string, got {type(path).__name__}: {path}")
    
    # Check for empty path
    if not path:
        raise ParameterValidationError("GameObject path cannot be empty")
    
    # Check for valid path format (should not contain invalid characters like \ or ")
    invalid_chars = ['\\', '"', '*', '<', '>', '|', ':', '?']
    for char in invalid_chars:
        if char in path:
            raise ParameterValidationError(f"GameObject path contains invalid character '{char}': {path}") 