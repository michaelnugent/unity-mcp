using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;
using UnityEngine;

namespace UnityMcpBridge.Editor.Tools
{
    /// <summary>
    /// Registry for all MCP command handlers (Refactored Version)
    /// </summary>
    public static class CommandRegistry
    {
        // Maps command names (matching those called from Python via ctx.bridge.unity_editor.HandlerName)
        // to the corresponding static HandleCommand method in the appropriate tool class.
        private static readonly Dictionary<string, Func<JObject, object>> _handlers = new();

        /// <summary>  
        /// Registers a command handler with a specified name.  
        /// </summary>  
        /// <param name="name">The name of the command to register.</param>  
        /// <param name="commandHandler">The function to handle the command.</param>  
        public static void RegisterCommand(string name, Func<JObject, object> commandHandler)
        {
            // Use case-insensitive comparison for flexibility, although Python side should be consistent
            string normalizedName = name.ToLower();
            if (!_handlers.ContainsKey(normalizedName))
            {
                _handlers.Add(normalizedName, commandHandler);
                Debug.Log($"Command '{name}' registered.");
            }
            else
            {
                Debug.LogWarning($"Command '{name}' already registered. Skipping duplicate registration.");
            }
        }

        /// <summary>  
        /// Executes a registered command by name with the provided parameters.  
        /// </summary>  
        /// <param name="name">The name of the command to execute.</param>  
        /// <param name="paramsObject">The parameters to pass to the command handler.</param>  
        /// <returns>The result of the command execution or an error message if the command is not found.</returns>  
        public static object ExecuteCommand(string name, JObject paramsObject)
        {
            if (_handlers.TryGetValue(name.ToLower(), out var command))
            {
                return command(paramsObject);
            }
            else
            {
                Debug.LogWarning($"Command '{name}' not found.");
                return $"Command '{name}' not found.";
            }
        }

        /// <summary>  
        /// Retrieves a list of all registered command names.  
        /// </summary>  
        /// <returns>A list of registered command names.</returns>  
        public static List<string> GetRegisteredCommands()
        {
            // Return a list of registered command names
            return new List<string>(_handlers.Keys);
        }

        /// <summary>
        /// Gets a command handler by name.
        /// </summary>
        /// <param name="commandName">Name of the command handler (e.g., "HandleManageAsset").</param>
        /// <returns>The command handler function if found, null otherwise.</returns>
        public static Func<JObject, object> GetHandler(string commandName)
        {
            // Use case-insensitive comparison for flexibility, although Python side should be consistent
            if (_handlers.TryGetValue(commandName.ToLower(), out var handler))
            {
                return handler;
            }
            else
            {
                Debug.LogWarning($"[CommandRegistry] No handler found for command: {commandName}");
                return null;
            }
        }
    }
}

