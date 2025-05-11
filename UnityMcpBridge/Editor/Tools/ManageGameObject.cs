using System;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityMcpBridge.Editor.Helpers;
using UnityMcpBridge.Editor.Tools.ManageGameObject.Implementation;

namespace UnityMcpBridge.Editor.Tools
{
    /// <summary>
    /// Handles GameObject manipulation within the current scene.
    /// Provides functionality for creating, modifying, deleting, and finding GameObjects,
    /// as well as for managing their components and properties.
    /// </summary>
    [InitializeOnLoad]
    public static class GameObjectManager
    {
        // Note: We've kept all the public API surface and registration exactly the same,
        // but refactored the implementation into specialized classes to improve maintainability.

        static GameObjectManager()
        {
            CommandRegistry.RegisterCommand("manage_game_object", HandleCommand);
        }

        /// <summary>
        /// Handles commands for GameObject manipulation.
        /// Commands include: create, find, modify, delete, get_components
        /// </summary>
        /// <param name="params">JSON parameters for the command</param>
        public static object HandleCommand(JObject @params)
        {
            Debug.Log($"[ManageGameObject] Received command with params: {JsonConvert.SerializeObject(@params)}");

            try
            {
                if (@params == null)
                {
                    return Response.Error("Invalid JSON parameters.");
                }

                // Get the action parameter
                string action = @params["action"]?.ToString()?.ToLowerInvariant();
                if (string.IsNullOrEmpty(action))
                {
                    return Response.Error("'action' parameter is required.");
                }

                // Route to the appropriate handler based on action
                return ProcessAction(action, @params);
            }
            catch (JsonException ex)
            {
                return Response.Error($"Invalid JSON: {ex.Message}");
            }
            catch (Exception ex)
            {
                // Log the full exception for debugging
                Debug.LogError($"[ManageGameObject] Error: {ex}");
                return Response.Error($"Error: {ex.Message}");
            }
        }

        /// <summary>
        /// Process the action and route to appropriate handler
        /// </summary>
        private static object ProcessAction(string action, JObject @params)
        {
            // Ensure we're in a valid edit mode
            if (!CheckEditorState())
            {
                return Response.Error("This command can only be used in Edit mode with a valid scene open.");
            }

            // Route the command to the appropriate specialized class
            switch (action)
            {
                case "create":
                    return GameObjectCreator.CreateGameObject(@params);

                case "modify":
                    return GameObjectModifier.ModifyGameObject(@params);

                case "delete":
                    return GameObjectDeleter.DeleteGameObject(@params);

                case "find":
                    return GameObjectFinder.FindGameObjects(@params);

                case "get_components":
                    return ComponentManager.GetComponentsFromTarget(@params);

                case "add_component":
                    return ComponentManager.AddComponentToTarget(@params);

                case "remove_component":
                    return ComponentManager.RemoveComponentFromTarget(@params);

                case "set_component_property":
                    return ComponentManager.SetComponentPropertyOnTarget(@params);

                default:
                    return Response.Error($"Unknown action: '{action}'.");
            }
        }

        /// <summary>
        /// Check if the editor is in a valid state for GameObject operations
        /// </summary>
        private static bool CheckEditorState()
        {
            // Only allow editing in play mode if specifically configured
            if (EditorApplication.isPlaying)
            {
                Debug.LogWarning("[ManageGameObject] Attempting to use ManageGameObject in Play mode. This is not recommended.");
            }

            // Verify a scene is open
            if (UnityEngine.SceneManagement.SceneManager.sceneCount == 0)
            {
                return false;
            }

            return true;
        }
    }
}

