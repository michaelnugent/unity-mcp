"""
Defines the manage_scene tool for working with Unity scenes.
"""
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal, Tuple
from mcp.server.fastmcp import FastMCP, Context
from .base_tool import BaseTool
from exceptions import ParameterValidationError
# Import the validation layer functions
from .validation_layer import (
    validate_asset_path, validate_gameobject_path, 
    validate_component_type, validate_screenshot_path
)

class SceneTool(BaseTool):
    """Tool for managing Unity scenes."""
    
    tool_name = "manage_scene"
    
    # Define required parameters for each action
    required_params = {
        "open": {"path": str},
        "save_as": {"path": str},
        "instantiate": {"prefab_path": str},
        "move": {"game_object_name": str, "position": (list, tuple, dict)},
        "rotate": {"game_object_name": str, "rotation": (list, tuple, dict)},
        "scale": {"game_object_name": str, "scale": (list, tuple, dict)},
        "delete": {"game_object_name": str},
        "get_component": {"game_object_name": str, "component_type": str},
        "set_component": {"game_object_name": str, "component_type": str, "component_properties": dict},
        "add_component": {"game_object_name": str, "component_type": str},
        "remove_component": {"game_object_name": str, "component_type": str},
        "set_parent": {"game_object_name": str, "parent_name": str},
        "set_active": {"game_object_name": str, "active_state": bool},
        "capture_screenshot": {"screenshot_path": str},
    }
    
    # Define parameters that should be validated as Vector3
    vector3_params = ["position", "scale"]
    
    # Define parameters that should be validated as Euler angles (will be converted to Quaternion)
    euler_params = ["rotation"]
    
    def additional_validation(self, action: str, params: Dict[str, Any]) -> None:
        """Additional validation specific to the scene tool."""
        # Validate paths for scene files
        if action in ["open", "save_as", "add_to_build"] and "path" in params:
            validate_asset_path(
                params["path"], 
                must_exist=(action == "open"), 
                extension=".unity"
            )
        
        # Validate prefab path
        if action == "instantiate" and "prefab_path" in params:
            validate_asset_path(
                params["prefab_path"], 
                must_exist=True, 
                extension=".prefab"
            )
        
        # Validate GameObject references
        if "game_object_name" in params and params.get("game_object_name"):
            validate_gameobject_path(
                params["game_object_name"],
                must_exist=(action not in ["instantiate"])
            )
        
        # Validate parent name if provided
        if "parent_name" in params and params.get("parent_name"):
            validate_gameobject_path(params["parent_name"], must_exist=True)
        
        # Validate component type
        if "component_type" in params and params.get("component_type"):
            validate_component_type(params["component_type"])
        
        # Validate screenshot path
        if action == "capture_screenshot" and "screenshot_path" in params:
            validate_screenshot_path(params["screenshot_path"])
        
        # Validate component properties format
        if action == "set_component" and "component_properties" in params:
            if not isinstance(params["component_properties"], dict):
                raise ParameterValidationError(
                    f"component_properties must be a dictionary of property names and values"
                )
    
    def needs_unity_validation(self, action: str, params: Dict[str, Any]) -> bool:
        """Determine if a validate_only request needs to go to Unity for validation.
        
        Most Scene operations need Unity-side validation to check resource existence 
        (GameObjects, Components, Prefabs, etc.). However, we can optimize for 
        some simple cases where only parameter type validation is needed.
        
        Args:
            action: The scene action being performed
            params: Action parameters
            
        Returns:
            True if Unity-side validation is needed, False otherwise
        """
        # Parameter type validations can be handled on Python side
        # These are the only validations we can completely handle without Unity:
        
        # Simple parameter validation can be done entirely on Python side
        simple_validation_actions = {
            "save",         # No required parameters
            "close",        # No required parameters
            "get_scene_info", # No required parameters
            "get_open_scenes", # No required parameters
        }
        
        if action in simple_validation_actions:
            return False
            
        # For other actions, we need Unity-side validation to check:
        # - If scene paths are valid
        # - If GameObjects exist
        # - If Components exist
        # - If prefabs exist
        # - If parent-child relationships are valid
        return True
    
    @staticmethod
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
            screenshot_path: Optional[str] = None,
            validate_only: Optional[bool] = None
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
                validate_only: When true, only validates parameters without executing the operation.
                    Use this for preflight validation to check if parameters are valid.

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
                  
                - Validate operation without executing:
                  action="move", game_object_name="Player", position=[10, 0, 5], validate_only=True
            """
            # Create tool instance
            scene_tool = SceneTool(ctx)
            
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
                "screenshotPath": screenshot_path,
                "validateOnly": validate_only
            }
            
            # Remove None values to avoid sending unnecessary nulls
            params_dict = {k: v for k, v in params_dict.items() if v is not None}

            try:
                # Send command with validation through the tool
                return await scene_tool.send_command_async("manage_scene", params_dict)
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
    
    # Validate component type format (should be like UnityEngine.Transform or FullNamespace.ComponentName)
    if not ("." in component_type and component_type.split(".")[-1] and component_type.split(".")[0]):
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

def validate_screenshot_path(path: Any) -> None:
    """Validate a screenshot save path parameter.

    Args:
        path: The path to validate
    
    Returns:
        None: This function doesn't return anything but raises exceptions on validation failure
    
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(path, str):
        raise ParameterValidationError(f"Screenshot path must be a string, got {type(path).__name__}: {path}")
    
    # Check for empty path
    if not path:
        raise ParameterValidationError("Screenshot path cannot be empty")
    
    # Check file extension
    valid_extensions = ['.png', '.jpg', '.jpeg']
    if not any(path.lower().endswith(ext) for ext in valid_extensions):
        raise ParameterValidationError(f"Screenshot path must end with one of {valid_extensions}, got: {path}")