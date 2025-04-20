"""Unity MCP tools module."""

from .manage_script import ScriptTool
from .manage_scene import SceneTool
from .manage_editor import EditorTool
from .manage_gameobject import GameObjectTool
from .manage_asset import AssetTool
from .read_console import ConsoleTool
from .execute_menu_item import MenuItemTool
from .manage_prefabs import PrefabsTool

def register_all_tools(mcp):
    """Register all tools with the MCP server."""
    print("Registering Unity MCP Server tools...")
    ScriptTool.register_manage_script_tools(mcp)
    SceneTool.register_manage_scene_tools(mcp)
    EditorTool.register_manage_editor_tools(mcp)
    GameObjectTool.register_manage_gameobject_tools(mcp)
    AssetTool.register_manage_asset_tools(mcp)
    ConsoleTool.register_read_console_tools(mcp)
    MenuItemTool.register_execute_menu_item_tools(mcp)
    PrefabsTool.register_manage_prefabs_tools(mcp)
    print("Unity MCP Server tool registration complete.")
