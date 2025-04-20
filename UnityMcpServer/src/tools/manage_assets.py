"""
Defines the manage_assets tool for working with Unity assets and the Asset Database.
"""
import asyncio
from typing import Dict, Any, Optional, List, Union, Literal, TypedDict
from mcp.server.fastmcp import FastMCP, Context
from unity_connection import get_unity_connection

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

def register_manage_assets_tools(mcp: FastMCP):
    """Registers the manage_assets tool with the MCP server."""

    @mcp.tool()
    async def manage_assets(
        ctx: Context,
        action: Literal['import', 'export', 'delete', 'move', 'copy', 'rename', 'create_folder', 'get_info', 'get_dependencies', 'set_labels', 'get_labels', 'create_asset', 'find_assets', 'refresh', 'save_assets', 'load_asset_at_path', 'set_bundle', 'get_bundle'],
        path: Optional[str] = None,
        destination_path: Optional[str] = None,
        new_name: Optional[str] = None,
        asset_type: Optional[str] = None,
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
        """Manages assets in the Unity project using the Asset Database.

        This tool provides functionality to work with assets in a Unity project,
        including importing, exporting, moving, and querying asset information.
        It interfaces with Unity's AssetDatabase system to perform operations.

        Args:
            ctx: The MCP context, containing runtime information.
            action: The asset operation to perform. Valid options include:
                - 'import': Import a file into the asset database
                - 'export': Export an asset to a file outside the project
                - 'delete': Delete an asset from the project
                - 'move': Move an asset to a new location
                - 'copy': Copy an asset to a new location
                - 'rename': Rename an asset
                - 'create_folder': Create a new folder in the project
                - 'get_info': Get information about an asset
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
            path: Path to the asset within the project, e.g., "Assets/Textures/background.png"
            destination_path: Destination path for move, copy, or export operations
            new_name: New name for rename operations
            asset_type: Type of asset for creation or filtering, e.g., "Texture2D", "Material"
            source_file: Path to a source file outside the project for import operations
            guid: Asset GUID for operations that work with GUIDs
            filter: Filter string for find operations, e.g., "t:Texture2D"
            include_dependencies: Whether to include dependencies in operations
            recursive: Whether to perform operations recursively (for folders)
            labels: List of labels to set on an asset
            bundle_name: Asset bundle name for set_bundle operations
            variant: Asset bundle variant for set_bundle operations
            search_query: Search query for find_assets operation
            import_options: Dictionary of import options for import operations
            creation_params: Parameters for asset creation

        Returns:
            A dictionary with the following fields:
            - success: Boolean indicating if the operation succeeded
            - message: Success message if the operation was successful
            - error: Error message if the operation failed
            - data: Additional data about the operation result, which varies by action:
              - For 'get_info': Asset information as an AssetInfo object
              - For 'get_dependencies': List of dependent asset paths
              - For 'get_labels': List of labels on the asset
              - For 'find_assets': List of matching asset paths
              - For 'get_bundle': Asset bundle name

        Examples:
            - Import an external file as an asset:
              action="import", source_file="/path/to/external/texture.png", path="Assets/Textures/texture.png"
              
            - Get information about an asset:
              action="get_info", path="Assets/Prefabs/Player.prefab"
              
            - Move an asset to a different folder:
              action="move", path="Assets/Textures/old.png", destination_path="Assets/Textures/Folder/new.png"
              
            - Find all texture assets:
              action="find_assets", search_query="t:Texture2D"
              
            - Set labels on an asset:
              action="set_labels", path="Assets/Models/Character.fbx", labels=["character", "player"]
              
            - Create a new folder:
              action="create_folder", path="Assets/NewFolder"
              
            - Set asset bundle:
              action="set_bundle", path="Assets/Prefabs/Enemy.prefab", bundle_name="enemies"
        """
        # Prepare parameters for the C# handler
        params_dict = {
            "action": action.lower(),
            "path": path,
            "destinationPath": destination_path,
            "newName": new_name,
            "assetType": asset_type,
            "sourceFile": source_file,
            "guid": guid,
            "filter": filter,
            "includeDependencies": include_dependencies,
            "recursive": recursive,
            "labels": labels,
            "bundleName": bundle_name,
            "variant": variant,
            "searchQuery": search_query,
            "importOptions": import_options,
            "creationParams": creation_params
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
            "manage_assets",  # First argument for send_command
            params_dict  # Second argument for send_command
        )
        
        # Return the result obtained from Unity
        return result 