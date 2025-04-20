using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityMcpBridge.Editor.Helpers;

namespace UnityMcpBridge.Editor.Tools
{
    /// <summary>
    /// Handles scene management operations in Unity.
    /// This adds a specialized handler for the manage_scenes command.
    /// </summary>
    public static class ManageScenes
    {
        private static readonly List<string> ValidActions = new List<string>
        {
            "create", "load", "save", "close", "new", "get_active", "get_loaded",
            "set_active", "add_to_build", "remove_from_build"
        };

        /// <summary>
        /// Main handler for scene management operations.
        /// </summary>
        public static object HandleCommand(JObject @params)
        {
            try
            {
                string action = @params["action"]?.ToString()?.ToLower();

                if (string.IsNullOrEmpty(action))
                {
                    return Response.Error("No action specified for scene management operation.");
                }

                if (!ValidActions.Contains(action))
                {
                    return Response.Error($"Invalid scene action: '{action}'. Valid actions are: {string.Join(", ", ValidActions)}");
                }

                string scenePath = @params["scenePath"]?.ToString();
                string sceneName = @params["sceneName"]?.ToString();
                bool? addToBuild = @params["addToBuild"]?.ToObject<bool?>();
                int? buildIndex = @params["buildIndex"]?.ToObject<int?>();
                bool? additive = @params["additive"]?.ToObject<bool?>();
                bool? saveCurrent = @params["saveCurrent"]?.ToObject<bool?>();

                // Route to specific action handlers
                switch (action)
                {
                    case "create":
                        if (string.IsNullOrEmpty(scenePath))
                            return Response.Error("Scene path is required for creating a scene.");
                        return CreateScene(scenePath, sceneName, addToBuild);

                    case "load":
                        if (string.IsNullOrEmpty(scenePath))
                            return Response.Error("Scene path is required for loading a scene.");
                        return LoadScene(scenePath, additive, saveCurrent);

                    case "save":
                        return SaveScene(scenePath);

                    case "close":
                        return CloseScene(scenePath);

                    case "new":
                        return CreateNewScene(saveCurrent);

                    case "get_active":
                        return GetActiveSceneInfo();

                    case "get_loaded":
                        return GetLoadedScenesInfo();

                    case "set_active":
                        if (string.IsNullOrEmpty(scenePath))
                            return Response.Error("Scene path is required for setting active scene.");
                        return SetActiveScene(scenePath);

                    case "add_to_build":
                        if (string.IsNullOrEmpty(scenePath))
                            return Response.Error("Scene path is required for adding to build settings.");
                        return AddSceneToBuild(scenePath, buildIndex);

                    case "remove_from_build":
                        if (string.IsNullOrEmpty(scenePath))
                            return Response.Error("Scene path is required for removing from build settings.");
                        return RemoveSceneFromBuild(scenePath);

                    default:
                        return Response.Error($"Scene action '{action}' is recognized but not yet implemented.");
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Exception during {(@params["action"] ?? "unknown")} operation: {e}");
                return Response.Error($"Error handling scene operation: {e.Message}");
            }
        }

        private static object CreateScene(string scenePath, string sceneName, bool? addToBuild)
        {
            try
            {
                // Ensure scene name exists
                if (string.IsNullOrEmpty(sceneName))
                {
                    sceneName = System.IO.Path.GetFileNameWithoutExtension(scenePath);
                    if (string.IsNullOrEmpty(sceneName))
                    {
                        return Response.Error("Scene name is required for creating a scene.");
                    }
                }

                // Create a new scene
                Scene newScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                
                // Set scene name in the Scene object - not directly possible, so we'll save it with the name
                bool saved = EditorSceneManager.SaveScene(newScene, scenePath);
                if (!saved)
                {
                    return Response.Error($"Failed to save new scene at '{scenePath}'.");
                }

                // Add to build settings if requested
                if (addToBuild == true)
                {
                    AddSceneToBuildInternal(scenePath);
                }

                return Response.Success($"Scene created successfully at '{scenePath}'.", new { path = scenePath });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Error creating scene: {e}");
                return Response.Error($"Error creating scene: {e.Message}");
            }
        }

        private static object LoadScene(string scenePath, bool? additive, bool? saveCurrent)
        {
            try
            {
                // Save current scene if requested
                if (saveCurrent == true)
                {
                    if (EditorSceneManager.GetActiveScene().isDirty)
                    {
                        bool saved = EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo();
                        if (!saved)
                        {
                            return Response.Error("User cancelled saving the current scene.");
                        }
                    }
                }

                // Get the scene open mode
                OpenSceneMode mode = (additive == true) ? OpenSceneMode.Additive : OpenSceneMode.Single;

                // Try to open the scene
                Scene scene = EditorSceneManager.OpenScene(scenePath, mode);
                if (!scene.IsValid())
                {
                    return Response.Error($"Failed to open scene at '{scenePath}'. Scene may not exist or is invalid.");
                }

                return Response.Success($"Scene '{scenePath}' loaded successfully.", GetSceneData(scene));
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Error loading scene: {e}");
                return Response.Error($"Error loading scene: {e.Message}");
            }
        }

        private static object SaveScene(string scenePath = null)
        {
            try
            {
                bool saved;
                
                if (string.IsNullOrEmpty(scenePath))
                {
                    // Save the current active scene
                    Scene scene = EditorSceneManager.GetActiveScene();
                    if (!scene.isDirty)
                    {
                        return Response.Success("Scene has no unsaved changes.");
                    }
                    
                    saved = EditorSceneManager.SaveScene(scene);
                    scenePath = scene.path;
                }
                else
                {
                    // Save the specified scene
                    Scene scene = default;
                    for (int i = 0; i < SceneManager.sceneCount; i++)
                    {
                        Scene s = SceneManager.GetSceneAt(i);
                        if (s.path == scenePath)
                        {
                            scene = s;
                            break;
                        }
                    }

                    if (!scene.IsValid())
                    {
                        return Response.Error($"Scene '{scenePath}' is not currently loaded.");
                    }

                    saved = EditorSceneManager.SaveScene(scene);
                }

                if (!saved)
                {
                    return Response.Error($"Failed to save scene at '{scenePath}'.");
                }

                return Response.Success($"Scene saved successfully at '{scenePath}'.", new { path = scenePath });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Error saving scene: {e}");
                return Response.Error($"Error saving scene: {e.Message}");
            }
        }

        private static object CloseScene(string scenePath = null)
        {
            try
            {
                if (string.IsNullOrEmpty(scenePath))
                {
                    // Close the active scene if no path specified
                    Scene scene = EditorSceneManager.GetActiveScene();
                    scenePath = scene.path;
                    
                    // If it's the only scene, create a new empty one first
                    if (SceneManager.sceneCount == 1)
                    {
                        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                        return Response.Success($"Scene '{scenePath}' closed and replaced with a new empty scene.");
                    }
                    else
                    {
                        // Get a different scene to make active
                        Scene newActiveScene = default;
                        for (int i = 0; i < SceneManager.sceneCount; i++)
                        {
                            Scene s = SceneManager.GetSceneAt(i);
                            if (s != scene)
                            {
                                newActiveScene = s;
                                break;
                            }
                        }
                        
                        // Set another scene active before closing
                        if (newActiveScene.IsValid())
                        {
                            EditorSceneManager.SetActiveScene(newActiveScene);
                        }
                        
                        bool closed = EditorSceneManager.CloseScene(scene, true);
                        if (!closed)
                        {
                            return Response.Error($"Failed to close scene '{scenePath}'.");
                        }
                    }
                }
                else
                {
                    // Find and close the specified scene
                    Scene scene = default;
                    bool isActiveScene = false;
                    
                    for (int i = 0; i < SceneManager.sceneCount; i++)
                    {
                        Scene s = SceneManager.GetSceneAt(i);
                        if (s.path == scenePath)
                        {
                            scene = s;
                            isActiveScene = s == EditorSceneManager.GetActiveScene();
                            break;
                        }
                    }

                    if (!scene.IsValid())
                    {
                        return Response.Error($"Scene '{scenePath}' is not currently loaded.");
                    }

                    // If closing the active scene, make another scene active first
                    if (isActiveScene && SceneManager.sceneCount > 1)
                    {
                        for (int i = 0; i < SceneManager.sceneCount; i++)
                        {
                            Scene s = SceneManager.GetSceneAt(i);
                            if (s != scene)
                            {
                                EditorSceneManager.SetActiveScene(s);
                                break;
                            }
                        }
                    }
                    else if (isActiveScene)
                    {
                        // If it's the only scene, create a new empty one
                        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                        return Response.Success($"Scene '{scenePath}' closed and replaced with a new empty scene.");
                    }

                    bool closed = EditorSceneManager.CloseScene(scene, true);
                    if (!closed)
                    {
                        return Response.Error($"Failed to close scene '{scenePath}'.");
                    }
                }

                return Response.Success($"Scene '{scenePath}' closed successfully.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Error closing scene: {e}");
                return Response.Error($"Error closing scene: {e.Message}");
            }
        }

        private static object CreateNewScene(bool? saveCurrent)
        {
            try
            {
                // Save current scene if requested
                if (saveCurrent == true)
                {
                    if (EditorSceneManager.GetActiveScene().isDirty)
                    {
                        bool saved = EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo();
                        if (!saved)
                        {
                            return Response.Error("User cancelled saving the current scene.");
                        }
                    }
                }

                // Create a new scene
                Scene newScene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                
                return Response.Success("New empty scene created.", GetSceneData(newScene));
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Error creating new scene: {e}");
                return Response.Error($"Error creating new scene: {e.Message}");
            }
        }

        private static object GetActiveSceneInfo()
        {
            try
            {
                Scene activeScene = EditorSceneManager.GetActiveScene();
                if (!activeScene.IsValid())
                {
                    return Response.Error("No active scene found.");
                }

                return Response.Success("Retrieved active scene information.", GetSceneData(activeScene));
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Error getting active scene info: {e}");
                return Response.Error($"Error getting active scene info: {e.Message}");
            }
        }

        private static object GetLoadedScenesInfo()
        {
            try
            {
                int sceneCount = SceneManager.sceneCount;
                if (sceneCount == 0)
                {
                    return Response.Success("No scenes are currently loaded.", new { scenes = new object[0] });
                }

                var sceneDataList = new List<object>();
                for (int i = 0; i < sceneCount; i++)
                {
                    Scene scene = SceneManager.GetSceneAt(i);
                    sceneDataList.Add(GetSceneData(scene));
                }

                return Response.Success($"Retrieved information for {sceneCount} loaded scenes.", new { scenes = sceneDataList });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Error getting loaded scenes info: {e}");
                return Response.Error($"Error getting loaded scenes info: {e.Message}");
            }
        }

        private static object SetActiveScene(string scenePath)
        {
            try
            {
                // Find the scene by path
                Scene targetScene = default;
                bool found = false;
                
                for (int i = 0; i < SceneManager.sceneCount; i++)
                {
                    Scene scene = SceneManager.GetSceneAt(i);
                    if (scene.path == scenePath)
                    {
                        targetScene = scene;
                        found = true;
                        break;
                    }
                }

                if (!found || !targetScene.IsValid())
                {
                    return Response.Error($"Scene '{scenePath}' is not currently loaded. Load it first before setting as active.");
                }

                // Set as active
                bool success = EditorSceneManager.SetActiveScene(targetScene);
                if (!success)
                {
                    return Response.Error($"Failed to set scene '{scenePath}' as active.");
                }

                return Response.Success($"Scene '{scenePath}' set as active.", GetSceneData(targetScene));
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Error setting active scene: {e}");
                return Response.Error($"Error setting active scene: {e.Message}");
            }
        }

        private static object AddSceneToBuild(string scenePath, int? buildIndex)
        {
            try
            {
                int result = AddSceneToBuildInternal(scenePath, buildIndex);
                
                if (result < 0)
                {
                    return Response.Error($"Failed to add scene '{scenePath}' to build settings.");
                }

                return Response.Success($"Scene '{scenePath}' added to build settings at index {result}.", new { buildIndex = result });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Error adding scene to build: {e}");
                return Response.Error($"Error adding scene to build: {e.Message}");
            }
        }

        private static int AddSceneToBuildInternal(string scenePath, int? buildIndex = null)
        {
            // Get the current scenes in build settings
            EditorBuildSettingsScene[] scenes = EditorBuildSettings.scenes;
            
            // Check if the scene is already in build settings
            for (int i = 0; i < scenes.Length; i++)
            {
                if (scenes[i].path == scenePath)
                {
                    return i; // Already in build at this index
                }
            }
            
            // Create a new array with space for the new scene
            EditorBuildSettingsScene[] newScenes = new EditorBuildSettingsScene[scenes.Length + 1];
            
            // Set the insertion index
            int insertIndex = buildIndex.HasValue && buildIndex.Value >= 0 && buildIndex.Value <= scenes.Length 
                ? buildIndex.Value 
                : scenes.Length; // Default to the end
            
            // Copy existing scenes, inserting the new one at the desired index
            for (int i = 0, j = 0; i < newScenes.Length; i++)
            {
                if (i == insertIndex)
                {
                    newScenes[i] = new EditorBuildSettingsScene(scenePath, true);
                }
                else
                {
                    newScenes[i] = scenes[j++];
                }
            }
            
            // Apply the new build settings
            EditorBuildSettings.scenes = newScenes;
            
            return insertIndex;
        }

        private static object RemoveSceneFromBuild(string scenePath)
        {
            try
            {
                // Get the current scenes in build settings
                EditorBuildSettingsScene[] scenes = EditorBuildSettings.scenes;
                
                // Check if the scene is in build settings
                int sceneIndex = -1;
                for (int i = 0; i < scenes.Length; i++)
                {
                    if (scenes[i].path == scenePath)
                    {
                        sceneIndex = i;
                        break;
                    }
                }
                
                if (sceneIndex < 0)
                {
                    return Response.Error($"Scene '{scenePath}' is not in build settings.");
                }
                
                // Create a new array without the scene
                EditorBuildSettingsScene[] newScenes = new EditorBuildSettingsScene[scenes.Length - 1];
                
                // Copy all except the one to remove
                for (int i = 0, j = 0; i < scenes.Length; i++)
                {
                    if (i != sceneIndex)
                    {
                        newScenes[j++] = scenes[i];
                    }
                }
                
                // Apply the new build settings
                EditorBuildSettings.scenes = newScenes;
                
                return Response.Success($"Scene '{scenePath}' removed from build settings.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScenes] Error removing scene from build: {e}");
                return Response.Error($"Error removing scene from build: {e.Message}");
            }
        }

        private static object GetSceneData(Scene scene)
        {
            // Get all root GameObjects in the scene
            var rootObjects = scene.GetRootGameObjects();
            var rootObjectNames = rootObjects.Select(go => go.name).ToList();

            // Create the scene data object
            return new
            {
                name = scene.name,
                path = scene.path,
                buildIndex = scene.buildIndex,
                isDirty = scene.isDirty,
                isLoaded = scene.isLoaded,
                isActive = scene == EditorSceneManager.GetActiveScene(),
                rootGameObjects = rootObjectNames
            };
        }
    }
} 