"""
Defines the manage_asset tool for interacting with Unity assets.
"""
import asyncio  # Added: Import asyncio for running sync code in async
from typing import Dict, Any, Optional, List, Union, Literal
from mcp.server.fastmcp import FastMCP, Context
# from ..unity_connection import get_unity_connection  # Original line that caused error
from unity_connection import get_unity_connection  # Use absolute import relative to Python dir

def register_manage_asset_tools(mcp: FastMCP):
    """Registers the manage_asset tool with the MCP server."""

    @mcp.tool()
    async def manage_asset(
        ctx: Context,
        action: Literal['import', 'create', 'modify', 'delete', 'duplicate', 'move', 'rename', 'search', 'get_info', 'create_folder', 'get_components'],
        path: str,
        asset_type: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        destination: Optional[str] = None,
        generate_preview: bool = False,
        search_pattern: Optional[str] = None,
        filter_type: Optional[str] = None,
        filter_date_after: Optional[str] = None,
        page_size: Optional[int] = None,
        page_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """Performs asset operations (import, create, modify, delete, etc.) in Unity.

        This tool provides a comprehensive interface for managing assets in the Unity project,
        allowing LLMs to create, modify, and query assets programmatically.

        Args:
            ctx: The MCP context, containing runtime information.
            action: Operation to perform. Valid options:
                - 'import': Import external files into Unity as assets
                - 'create': Create a new asset of specified type
                - 'modify': Modify properties of an existing asset
                - 'delete': Delete an asset
                - 'duplicate': Create a copy of an asset at the destination path
                - 'move': Move an asset to a new location
                - 'rename': Rename an asset
                - 'search': Find assets matching criteria
                - 'get_info': Get detailed information about an asset
                - 'create_folder': Create a new folder in the project
                - 'get_components': List available components on a prefab asset
            path: Asset path (e.g., "Assets/Materials/MyMaterial.mat") or search scope.
                 For 'create', this specifies where to create the asset.
                 For 'search', this specifies the root directory to search in.
            asset_type: Asset type (e.g., 'Material', 'Texture', 'Prefab', 'Model', 'Script', 'Folder'). 
                       Required for 'create' action.
            properties: Dictionary of properties for 'create'/'modify' actions. The keys and values
                       depend on the asset_type. Examples:
                       - For Material: {"color": [1.0, 0.5, 0.5, 1.0], "shader": "Standard"}
                       - For Animation: {"wrapMode": "Loop", "frameRate": 30}
            destination: Target path for 'duplicate'/'move'/'rename' operations. Should be the complete
                        path including filename for the destination.
            generate_preview: When true, generates a preview image for the asset (if supported).
            search_pattern: Search pattern for 'search' action (e.g., '*.prefab', '*Player*').
                          Supports standard Unity search syntax.
            filter_type: Filter assets by type during search (e.g., 'Material', 'Prefab').
            filter_date_after: ISO 8601 timestamp (e.g., '2023-06-15T00:00:00Z') to filter assets
                              modified after a specific date.
            page_size: Number of results per page for paginated 'search' results.
            page_number: Page number for paginated 'search' results (0-based indexing).

        Returns:
            A dictionary with the following fields:
            - success: Boolean indicating if the operation succeeded
            - message: Success message if the operation was successful
            - error: Error message if the operation failed
            - data: Additional data about the operation result, which varies by action:
              - For 'get_info': Complete asset metadata
              - For 'search': Array of matching asset paths and metadata
              - For 'get_components': List of available component types
            
        Examples:
            - Create a new material:
              action="create", path="Assets/Materials/NewMaterial.mat", asset_type="Material",
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
        """
        # Ensure properties is a dict if None
        if properties is None:
            properties = {}
            
        # Prepare parameters for the C# handler
        params_dict = {
            "action": action.lower(),
            "path": path,
            "assetType": asset_type,
            "properties": properties,
            "destination": destination,
            "generatePreview": generate_preview,
            "searchPattern": search_pattern,
            "filterType": filter_type,
            "filterDateAfter": filter_date_after,
            "pageSize": page_size,
            "pageNumber": page_number
        }
        
        # Remove None values to avoid sending unnecessary nulls
        params_dict = {k: v for k, v in params_dict.items() if v is not None}

        # Get the current asyncio event loop
        loop = asyncio.get_running_loop()
        # Get the Unity connection instance
        connection = get_unity_connection()
        
        # Run the synchronous send_command in the default executor (thread pool)
        # This prevents blocking the main async event loop.
        result = await loop.run_in_executor(
            None,  # Use default executor
            connection.send_command, # The function to call
            "manage_asset", # First argument for send_command
            params_dict # Second argument for send_command
        )
        # Return the result obtained from Unity
        return result 