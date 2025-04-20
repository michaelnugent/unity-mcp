using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityMcpBridge.Editor.Helpers;

namespace UnityMcpBridge.Editor.Tools
{
    /// <summary>
    /// Handles GameObject operations within Unity.
    /// This adds a specialized handler for manage_game_objects command distinct from ManageGameObject.
    /// </summary>
    public static class ManageGameObjects
    {
        private static readonly List<string> ValidActions = new List<string>
        {
            "create", "destroy", "find", "get_children", "get_components", "set_active",
            "set_position", "set_rotation", "set_scale", "set_parent", "instantiate", "duplicate"
        };

        /// <summary>
        /// Main handler for GameObject operations.
        /// </summary>
        public static object HandleCommand(JObject @params)
        {
            try
            {
                string action = @params["action"]?.ToString()?.ToLower();
                
                if (string.IsNullOrEmpty(action))
                {
                    return Response.Error("No action specified for GameObject operation.");
                }

                if (!ValidActions.Contains(action))
                {
                    return Response.Error($"Invalid GameObject action: '{action}'. Valid actions are: {string.Join(", ", ValidActions)}");
                }

                // For now, delegate all operations to the existing ManageGameObject implementation
                // This acts as a compatibility bridge between the manage_game_objects command
                // and the existing ManageGameObject handler
                
                return ManageGameObject.HandleCommand(@params);
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageGameObjects] Exception during {(@params["action"] ?? "unknown")} operation: {e}");
                return Response.Error($"Error handling GameObject operation: {e.Message}");
            }
        }
    }
} 