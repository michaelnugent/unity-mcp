"""
Defines the manage_prefabs tool for working with Unity prefab assets.
"""
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal, Tuple
from mcp.server.fastmcp import FastMCP, Context
from .base_tool import BaseTool
from exceptions import ParameterValidationError

class PrefabsTool(BaseTool):
    """Tool for managing Unity prefabs."""
    
    tool_name = "manage_prefabs"
    
    # Define required parameters for each action
    required_params = {
        "create": {"game_object_path": str, "destination_path": str},
        "open": {"prefab_path": str},
        "apply": {"game_object_path": str, "prefab_path": str},
        "update": {"prefab_path": str},
        "create_variant": {"prefab_path": str, "destination_path": str},
        "unpack": {"game_object_path": str},
        "list_overrides": {"game_object_path": str},
        "add_component": {"prefab_path": str, "component_type": str},
        "remove_component": {"prefab_path": str, "component_type": str},
        "instantiate": {"prefab_path": str},
    }
    
    # Define parameters that should be validated as Vector3
    vector3_params = ["position", "scale"]
    
    # Define parameters that should be validated as Euler angles (will be converted to Quaternion)
    euler_params = ["rotation"]
    
    def additional_validation(self, action: str, params: Dict[str, Any]) -> None:
        """Additional validation specific to the prefabs tool."""
        if action == "add_component" and "component_properties" in params:
            if not isinstance(params["component_properties"], dict):
                raise ParameterValidationError(
                    f"{self.tool_name} 'add_component' parameter 'component_properties' must be of type dict"
                )
    
    @staticmethod
    def register_manage_prefabs_tools(mcp: FastMCP):
        """Registers the manage_prefabs tool with the MCP server."""

        @mcp.tool()
        async def manage_prefabs(
            ctx: Context,
            action: Literal['create', 'open', 'save', 'revert', 'apply', 'update', 'create_variant', 'unpack', 'list_overrides', 'add_component', 'remove_component', 'instantiate'],
            prefab_path: Optional[str] = None,
            destination_path: Optional[str] = None,
            game_object_path: Optional[str] = None,
            component_type: Optional[str] = None,
            component_properties: Optional[Dict[str, Any]] = None,
            position: Optional[List[float]] = None,
            rotation: Optional[List[float]] = None,
            scale: Optional[List[float]] = None,
            parent_path: Optional[str] = None,
            overrides: Optional[List[Dict[str, Any]]] = None,
            variant_name: Optional[str] = None,
            modified_properties: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """Manages Unity prefab operations.

            This tool provides functionality to work with prefabs in Unity, including
            creating, editing, saving, instantiating, and other prefab operations. It
            interfaces with Unity's prefab system to handle various prefab workflows.

            Args:
                ctx: The MCP context, containing runtime information.
                action: The prefab operation to perform. Valid options include:
                    - 'create': Create a new prefab from a GameObject
                    - 'open': Open a prefab for editing in Prefab Mode
                    - 'save': Save current changes to a prefab being edited
                    - 'revert': Revert changes made to a prefab in edit mode
                    - 'apply': Apply modifications from a prefab instance back to the source prefab
                    - 'update': Update instances of a prefab with the latest from source
                    - 'create_variant': Create a prefab variant from an existing prefab
                    - 'unpack': Unpack a prefab instance, breaking the prefab connection
                    - 'list_overrides': List property overrides on a prefab instance
                    - 'add_component': Add a component to a prefab
                    - 'remove_component': Remove a component from a prefab
                    - 'instantiate': Create an instance of a prefab in the scene
                prefab_path: Path to the prefab asset, e.g., "Assets/Prefabs/Player.prefab"
                destination_path: Destination path for creating prefabs or variants
                game_object_path: Path to the GameObject in the hierarchy
                component_type: Type of component to add or remove, e.g., "UnityEngine.BoxCollider"
                component_properties: Initial property values for added components
                position: Position for instanced prefabs as [x, y, z]
                rotation: Rotation for instanced prefabs as [x, y, z] in degrees
                scale: Scale for instanced prefabs as [x, y, z]
                parent_path: Path to the parent GameObject for instantiated prefabs
                overrides: List of property overrides when applying changes
                variant_name: Name for prefab variants
                modified_properties: Dictionary of properties to modify

            Returns:
                A dictionary with the following fields:
                - success: Boolean indicating if the operation succeeded
                - message: Success message if the operation was successful
                - error: Error message if the operation failed
                - data: Additional data about the operation result, which varies by action:
                  - For 'list_overrides': List of property overrides on the prefab instance
                  - For 'instantiate': Path to the instantiated GameObject
                  - For 'create' or 'create_variant': Path to the new prefab asset

            Examples:
                - Create a new prefab from a GameObject:
                  action="create", game_object_path="Player", destination_path="Assets/Prefabs/Player.prefab"
                  
                - Instantiate a prefab in the scene:
                  action="instantiate", prefab_path="Assets/Prefabs/Enemy.prefab", position=[0, 0, 0], 
                  rotation=[0, 90, 0], scale=[1, 1, 1]
                  
                - Add a component to a prefab:
                  action="add_component", prefab_path="Assets/Prefabs/Player.prefab", 
                  component_type="UnityEngine.BoxCollider", component_properties={"isTrigger": True, "size": [1, 2, 1]}
                  
                - Create a prefab variant:
                  action="create_variant", prefab_path="Assets/Prefabs/Enemy.prefab", 
                  destination_path="Assets/Prefabs/Variants/FastEnemy.prefab"
                  
                - Apply prefab instance changes back to source:
                  action="apply", game_object_path="EnemyInstance", prefab_path="Assets/Prefabs/Enemy.prefab"
            """
            # Create tool instance
            prefabs_tool = PrefabsTool(ctx)
            
            # Prepare parameters for the C# handler
            params_dict = {
                "action": action.lower(),
                "prefab_path": prefab_path,
                "destination_path": destination_path,
                "game_object_path": game_object_path,
                "component_type": component_type,
                "component_properties": component_properties,
                "position": position,
                "rotation": rotation,
                "scale": scale,
                "parent_path": parent_path,
                "overrides": overrides,
                "variant_name": variant_name,
                "modified_properties": modified_properties
            }
            
            # Remove None values to avoid sending unnecessary nulls
            params_dict = {k: v for k, v in params_dict.items() if v is not None}

            try:                
                # Send command with validation through the tool
                return await prefabs_tool.send_command_async("manage_prefabs", params_dict)
            except ParameterValidationError as e:
                return {"success": False, "message": str(e), "validation_error": True} 