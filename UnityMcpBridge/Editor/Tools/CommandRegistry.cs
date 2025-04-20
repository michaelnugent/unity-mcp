using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;

namespace UnityMcpBridge.Editor.Tools
{
    /// <summary>
    /// Registry for all MCP command handlers (Refactored Version)
    /// </summary>
    public static class CommandRegistry
    {
        // Maps command names (matching those called from Python via ctx.bridge.unity_editor.HandlerName)
        // to the corresponding static HandleCommand method in the appropriate tool class.
        private static readonly Dictionary<string, Func<JObject, object>> _handlers = new()
        {
            // Original handlers with "Handle" prefix
            { "HandleManageScript", ManageScript.HandleCommand },
            { "HandleManageScene", ManageScene.HandleCommand },
            { "HandleManageEditor", ManageEditor.HandleCommand },
            { "HandleManageGameObject", ManageGameObject.HandleCommand },
            { "HandleManageAsset", ManageAsset.HandleCommand },
            { "HandleReadConsole", ReadConsole.HandleCommand },
            { "HandleExecuteMenuItem", ExecuteMenuItem.HandleCommand },
            
            // Map Python tool names directly to handlers (as used in Python tools)
            { "manage_script", ManageScript.HandleCommand },
            { "manage_scene", ManageScene.HandleCommand },
            { "manage_editor", ManageEditor.HandleCommand },
            { "manage_game_objects", ManageGameObjects.HandleCommand },
            { "manage_asset", ManageAsset.HandleCommand },
            { "manage_assets", ManageAsset.HandleCommand }, // Allow both singular and plural
            { "read_console", ReadConsole.HandleCommand },
            { "execute_menu_item", ExecuteMenuItem.HandleCommand },
            
            // New tool handlers
            { "manage_prefabs", ManagePrefabs.HandleCommand }, // Use our new ManagePrefabs handler
            { "manage_scenes", ManageScene.HandleCommand }   // For backward compatibility, map plural to singular
        };

        /// <summary>
        /// Gets a command handler by name.
        /// </summary>
        /// <param name="commandName">Name of the command handler (e.g., "HandleManageAsset").</param>
        /// <returns>The command handler function if found, null otherwise.</returns>
        public static Func<JObject, object> GetHandler(string commandName)
        {
            // Use case-insensitive comparison for flexibility, although Python side should be consistent
            if (_handlers.TryGetValue(commandName, out var handler))
            {
                return handler;
            }
            else
            {
                UnityEngine.Debug.LogWarning($"[CommandRegistry] No handler found for command: {commandName}");
                return null;
            }
        }
    }
}

