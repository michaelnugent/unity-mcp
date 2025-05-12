"""
Defines the manage_asset tool for interacting with Unity assets.
"""
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal, TypedDict
from mcp.server.fastmcp import FastMCP, Context
from .base_tool import BaseTool
from unity_connection import ParameterValidationError
# Import validation layer functions
from .validation_layer import (
    validate_asset_path, validate_action, validate_parameters_by_action
)
import os

class AssetInfo(TypedDict, total=False):
    """Type definition for asset information."""
    guid: str
    path: str
    type: str
    size: int
    lastModified: str
    dependencies: List[str]
    labels: List[str]
    bundle: Optional[str]

class AssetTool(BaseTool):
    """Tool for managing Unity assets."""
    
    tool_name = "manage_asset"
    
    # Define required parameters for each action
    required_params = {
        "import": {"path": str},
        "create": {"path": str, "asset_type": str},
        "modify": {"path": str},
        "delete": {"path": str},
        "duplicate": {"path": str, "destination": str},
        "move": {"path": str, "destination": str},
        "rename": {"path": str, "destination": str},
        "search": {"path": str},
        "get_info": {"path": str},
        "create_folder": {"path": str},
        "get_components": {"path": str},
        "export": {"path": str, "destination_path": str},
        "copy": {"path": str, "destination_path": str},
        "get_dependencies": {"path": str},
        "set_labels": {"path": str, "labels": list},
        "get_labels": {"path": str},
        "create_asset": {"path": str, "asset_type": str},
        "set_bundle": {"path": str, "bundle_name": str},
    }
    
    # Define parameters that might contain Vector2 values for asset properties
    vector2_params = ["tiling", "offset", "texelSize", "textureDimensions"]
    
    # Define parameters that might contain Vector3 values for asset properties
    vector3_params = ["position", "scale", "boundingBoxSize", "center"]
    
    # Define parameters that might contain Euler angles (will be converted to Quaternion)
    euler_params = ["rotation"]
    
    # Define parameters that might contain Color values for asset properties
    color_params = ["color", "specular", "emission", "rimColor", "backgroundColor", "tint"]
    
    # Define parameters that might contain Rect values for asset properties
    rect_params = ["rect", "textureRect", "spriteRect", "uvRect"]
    
    # Valid asset types for validation
    _valid_asset_types = [
        "Material", "Texture", "Texture2D", "Cubemap", "Prefab", "Model", "FBX", 
        "Animation", "AnimationClip", "AnimatorController", "AudioClip", "Font", 
        "Script", "ScriptableObject", "Shader", "ComputeShader", "PhysicMaterial",
        "PhysicsMaterial2D", "Scene", "Folder", "Sprite", "SpriteAtlas"
    ]
    
    def additional_validation(self, action: str, params: Dict[str, Any]) -> None:
        """Additional validation specific to the asset tool."""
        # Validate action is in supported actions
        valid_actions = [
            'import', 'create', 'modify', 'delete', 'duplicate', 'move', 'rename', 
            'search', 'get_info', 'create_folder', 'get_components', 'export', 'copy', 
            'get_dependencies', 'set_labels', 'get_labels', 'create_asset', 'find_assets', 
            'refresh', 'save_assets', 'load_asset_at_path', 'set_bundle', 'get_bundle'
        ]
        validate_action(action, valid_actions)
        
        # Validate path format for all actions requiring a path
        if "path" in params and params.get("path"):
            # For create/create_folder, path doesn't need to exist
            must_exist = action not in ["create", "create_folder", "create_asset", "import"]
            
            # For actions that create specific asset types, validate appropriate extension
            extension = None
            if action in ["create", "create_asset"] and "asset_type" in params:
                asset_type = params["asset_type"]
                # Map asset types to extensions
                extension_map = {
                    "Material": ".mat",
                    "Prefab": ".prefab",
                    "Scene": ".unity",
                    "AnimatorController": ".controller",
                    "AnimationClip": ".anim",
                    "Script": ".cs",
                    "ScriptableObject": ".asset"
                    # Add more mappings as needed
                }
                extension = extension_map.get(asset_type)
            
            # Validate the asset path
            validate_asset_path(params["path"], must_exist=must_exist, extension=extension)
        
        # Validate destination path for actions that require it
        if (action in ["duplicate", "move", "rename", "copy", "export"] and 
            "destination" not in params and "destination_path" not in params):
            raise ParameterValidationError(
                f"{self.tool_name} '{action}' action requires 'destination' or 'destination_path' parameter"
            )
        
        # Validate destination path format
        if "destination" in params and params.get("destination"):
            validate_asset_path(params["destination"], must_exist=False)
        
        if "destination_path" in params and params.get("destination_path"):
            # For export, destination is outside project
            if action == "export":
                dest_path = params["destination_path"]
                if not os.path.isabs(dest_path):
                    raise ParameterValidationError(
                        f"Export destination_path must be an absolute path outside the project: {dest_path}"
                    )
            else:
                validate_asset_path(params["destination_path"], must_exist=False)
        
        # Validate properties for modify/create actions
        if action in ["modify", "create", "create_asset"] and "properties" not in params:
            raise ParameterValidationError(
                f"{self.tool_name} '{action}' action requires 'properties' parameter"
            )
        
        # Validate asset_type for create actions
        if action in ["create", "create_asset"] and "asset_type" in params:
            if params["asset_type"] not in self._valid_asset_types:
                raise ParameterValidationError(
                    f"Invalid asset_type: '{params['asset_type']}'. "
                    f"Valid types include: {', '.join(self._valid_asset_types)}"
                )
        
        # Validate labels for set_labels
        if action == "set_labels" and "labels" in params:
            if not isinstance(params["labels"], list):
                raise ParameterValidationError(
                    "labels parameter must be a list of strings"
                )
            
            for label in params["labels"]:
                if not isinstance(label, str):
                    raise ParameterValidationError(
                        f"All labels must be strings, got {type(label).__name__}"
                    )
        
        # Validate bundle_name for set_bundle
        if action == "set_bundle" and "bundle_name" in params:
            if not isinstance(params["bundle_name"], str):
                raise ParameterValidationError(
                    f"bundle_name must be a string, got {type(params['bundle_name']).__name__}"
                )
            
            # Bundle names should not contain invalid characters
            invalid_chars = r'[<>:"/\\|?*]'
            if any(c in params["bundle_name"] for c in invalid_chars):
                raise ParameterValidationError(
                    f"bundle_name contains invalid characters: '{params['bundle_name']}'"
                )
    
    @staticmethod
    def register_manage_asset_tools(mcp: FastMCP):
        """Registers the manage_asset tool with the MCP server."""

        @mcp.tool()
        async def manage_asset(
            ctx: Context,
            action: Literal[
                # Original manage_asset actions
                'import', 'modify', 'delete', 'duplicate', 'move', 'rename', 'search', 
                'get_info', 'create_folder', 'get_components',
                # Additional actions from manage_assets
                'export', 'copy', 'get_dependencies', 'set_labels', 'get_labels', 'create_asset', 
                'find_assets', 'refresh', 'save_assets', 'load_asset_at_path', 'set_bundle', 'get_bundle'
            ],
            path: str,
            # Original manage_asset parameters
            asset_type: Optional[str] = None,
            properties: Optional[Dict[str, Any]] = None,
            destination: Optional[str] = None,
            generate_preview: bool = False,
            search_pattern: Optional[str] = None,
            filter_type: Optional[str] = None,
            filter_date_after: Optional[str] = None,
            page_size: Optional[int] = None,
            page_number: Optional[int] = None,
            # Additional parameters from manage_assets
            destination_path: Optional[str] = None,
            new_name: Optional[str] = None,
            source_file: Optional[str] = None,
            guid: Optional[str] = None,
            filter: Optional[str] = None,
            include_dependencies: Optional[bool] = None,
            recursive: Optional[bool] = None,
            labels: Optional[List[str]] = None,
            bundle_name: Optional[str] = None,
            variant: Optional[str] = None,
            search_query: Optional[str] = None,
            import_options: Optional[Dict[str, Any]] = None,
            creation_params: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """Performs asset operations (import, modify, delete, etc.) in Unity.

            This tool provides a comprehensive interface for managing assets in the Unity project,
            allowing LLMs to create, modify, and query assets programmatically.

            Args:
                ctx: The MCP context, containing runtime information.
                action: Operation to perform. Valid options:
                    - 'import': Import external files into Unity as assets
                    - 'modify': Modify properties of an existing asset
                    - 'delete': Delete an asset
                    - 'duplicate': Create a copy of an asset at the destination path
                    - 'move': Move an asset to a new location
                    - 'rename': Rename an asset
                    - 'search': Find assets matching criteria
                    - 'get_info': Get detailed information about an asset
                    - 'create_folder': Create a new folder in the project
                    - 'get_components': List available components on a prefab asset
                    - 'export': Export an asset to a file outside the project
                    - 'copy': Copy an asset to a new location
                    - 'get_dependencies': Get dependencies of an asset
                    - 'set_labels': Set labels on an asset
                    - 'get_labels': Get labels from an asset
                    - 'create_asset': Create a new asset
                    - 'find_assets': Find assets matching a search query
                    - 'refresh': Refresh the asset database
                    - 'save_assets': Save all unsaved asset changes
                    - 'load_asset_at_path': Load an asset at a specific path
                    - 'set_bundle': Set the asset bundle for an asset
                    - 'get_bundle': Get the asset bundle name for an asset
                path: Asset path (e.g., "Assets/Materials/MyMaterial.mat") or search scope.
                     For 'search', this specifies the root directory to search in.
                asset_type: Asset type (e.g., 'Material', 'Texture', 'Prefab', 'Model', 'Script', 'Folder'). 
                           Required for 'create_asset' action.
                properties: Dictionary of properties for 'modify' actions. The keys and values
                           depend on the asset_type. Examples:
                           - For Material: {"color": [1.0, 0.5, 0.5, 1.0], "shader": "Standard"}
                           - For Animation: {"wrapMode": "Loop", "frameRate": 30}
                destination: Target path for 'duplicate'/'move'/'rename' operations. Should be the complete
                            path including filename for the destination.
                destination_path: Alternative name for destination parameter.
                generate_preview: When true, generates a preview image for the asset (if supported).
                search_pattern: Search pattern for 'search' action (e.g., '*.prefab', '*Player*').
                              Supports standard Unity search syntax.
                filter_type: Filter assets by type during search (e.g., 'Material', 'Prefab').
                filter_date_after: ISO 8601 timestamp (e.g., '2023-06-15T00:00:00Z') to filter assets
                                  modified after a specific date.
                page_size: Number of results per page for paginated 'search' results.
                page_number: Page number for paginated 'search' results (0-based indexing).
                new_name: New name for rename operations.
                source_file: Path to a source file outside the project for import operations.
                guid: Asset GUID for operations that work with GUIDs.
                filter: Filter string for find operations, e.g., "t:Texture2D".
                include_dependencies: Whether to include dependencies in operations.
                recursive: Whether to perform operations recursively (for folders).
                labels: List of labels to set on an asset.
                bundle_name: Asset bundle name for set_bundle operations.
                variant: Asset bundle variant for set_bundle operations.
                search_query: Search query for find_assets operation.
                import_options: Dictionary of import options for import operations.
                creation_params: Parameters for asset creation.

            Returns:
                A dictionary with the following fields:
                - success: Boolean indicating if the operation succeeded
                - message: Success message if the operation was successful
                - error: Error message if the operation failed
                - data: Additional data about the operation result, which varies by action:
                  - For 'get_info': Complete asset metadata
                  - For 'search': Array of matching asset paths and metadata
                  - For 'get_components': List of available component types
                  - For 'get_dependencies': List of dependent asset paths
                  - For 'get_labels': List of labels on the asset
                  - For 'find_assets': List of matching asset paths
                  - For 'get_bundle': Asset bundle name
                
            Examples:
                - Create a new material:
                  action="create_asset", path="Assets/Materials/NewMaterial.mat", asset_type="Material",
                  properties={"color": [1.0, 0.0, 0.0, 1.0]}
                  
                - Modify an existing texture:
                  action="modify", path="Assets/Textures/Background.png",
                  properties={"wrapMode": "Repeat", "filterMode": "Bilinear"}
                  
                - Search for prefabs:
                  action="search", path="Assets/Prefabs", search_pattern="*.prefab"
                  
                - Move an asset:
                  action="move", path="Assets/Textures/OldFolder/texture.png",
                  destination="Assets/Textures/NewFolder/texture.png"
                  
                - Create a folder:
                  action="create_folder", path="Assets/NewFolder"
                  
                - Set asset bundle:
                  action="set_bundle", path="Assets/Prefabs/Enemy.prefab", bundle_name="enemies"
            """
            # Create tool instance
            asset_tool = AssetTool(ctx)
            
            # Ensure properties is a dict if None
            if properties is None:
                properties = {}
                
            # Handle alternative parameter names for compatibility
            if destination_path is not None and destination is None:
                destination = destination_path
                
            if search_query is not None and search_pattern is None:
                search_pattern = search_query
                
            if filter is not None and filter_type is None:
                filter_type = filter
                
            # Prepare parameters for the C# handler
            params_dict = {
                "action": action.lower(),
                "path": path,
                "asset_type": asset_type,
                "properties": properties,
                "destination": destination,
                "generate_preview": generate_preview,
                "search_pattern": search_pattern,
                "filter_type": filter_type,
                "filter_date_after": filter_date_after,
                "page_size": page_size,
                "page_number": page_number,
                # Additional parameters from manage_assets
                "new_name": new_name,
                "source_file": source_file,
                "guid": guid,
                "include_dependencies": include_dependencies,
                "recursive": recursive,
                "labels": labels,
                "bundle_name": bundle_name,
                "variant": variant,
                "import_options": import_options,
                "creation_params": creation_params
            }
            
            # Remove None values to avoid sending unnecessary nulls
            params_dict = {k: v for k, v in params_dict.items() if v is not None}

            try:
                # Send command with validation through the tool
                return await asset_tool.send_command_async("manage_asset", params_dict)
            except ParameterValidationError as e:
                return {"success": False, "message": str(e), "validation_error": True} 