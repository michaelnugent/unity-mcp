using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
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
    /// This adds a specialized handler for the manage_scene command.
    /// </summary>
    [InitializeOnLoad]
    public static class ManageScene
    {
        private static readonly List<string> ValidActions = new List<string>
        {
            "open", "create", "save", "save_as", "add_to_build", "get_scene_info", "get_open_scenes", 
            "close", "instantiate", "delete", "move", "rotate", "scale", "find", "get_component", 
            "set_component", "add_component", "remove_component", "get_position", "get_rotation", 
            "get_scale", "set_parent", "set_active", "capture_screenshot"
        };

        static ManageScene()
        {
            CommandRegistry.RegisterCommand("manage_scene", HandleCommand);
        }

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

                // Extract common parameters
                string path = @params["path"]?.ToString();
                string name = @params["name"]?.ToString();
                int? buildIndex = @params["buildIndex"]?.ToObject<int>();
                bool? additive = @params["additive"]?.ToObject<bool>();
                string prefabPath = @params["prefabPath"]?.ToString();
                string gameObjectName = @params["gameObjectName"]?.ToString();
                string componentType = @params["componentType"]?.ToString();
                JObject componentProperties = @params["componentProperties"] as JObject;
                JArray positionArray = @params["position"] as JArray;
                JArray rotationArray = @params["rotation"] as JArray;
                JArray scaleArray = @params["scale"] as JArray;
                string parentName = @params["parentName"]?.ToString();
                bool? activeState = @params["activeState"]?.ToObject<bool>();
                string query = @params["query"]?.ToString();
                bool? includeChildren = @params["includeChildren"]?.ToObject<bool>();
                string screenshotPath = @params["screenshotPath"]?.ToString();

                // For backward compatibility
                string scenePath = @params["scenePath"]?.ToString() ?? path;
                string sceneName = @params["sceneName"]?.ToString() ?? name;
                bool? saveCurrent = @params["saveCurrent"]?.ToObject<bool>();

                // Route to specific action handlers
                switch (action)
                {
                    // Scene file operations
                    case "open":
                        if (string.IsNullOrEmpty(scenePath))
                            return Response.Error("Path is required for opening a scene.");
                        return LoadScene(scenePath, additive, saveCurrent);

                    case "create":
                        if (string.IsNullOrEmpty(name) && string.IsNullOrEmpty(sceneName))
                            return Response.Error("Name is required for creating a scene.");
                        return CreateScene(scenePath ?? path, sceneName ?? name, true);

                    case "save":
                        return SaveScene(scenePath);

                    case "save_as":
                        if (string.IsNullOrEmpty(scenePath))
                            return Response.Error("Path is required for save_as operation.");
                        return SaveScene(scenePath);

                    case "close":
                        return CloseScene(scenePath);

                    case "add_to_build":
                        if (string.IsNullOrEmpty(scenePath))
                            return Response.Error("Path is required for adding to build settings.");
                        return AddSceneToBuild(scenePath, buildIndex);

                    case "get_scene_info":
                        return GetActiveSceneInfo();

                    case "get_open_scenes":
                        return GetLoadedScenesInfo();

                    // GameObject operations
                    case "instantiate":
                        if (string.IsNullOrEmpty(prefabPath))
                            return Response.Error("Prefab path is required for instantiating a GameObject.");
                        return InstantiatePrefab(prefabPath, positionArray, rotationArray, scaleArray, parentName);

                    case "delete":
                        if (string.IsNullOrEmpty(gameObjectName))
                            return Response.Error("GameObject name is required for delete operation.");
                        return DeleteGameObject(gameObjectName);

                    case "move":
                        if (string.IsNullOrEmpty(gameObjectName) || positionArray == null)
                            return Response.Error("GameObject name and position are required for move operation.");
                        return MoveGameObject(gameObjectName, positionArray);

                    case "rotate":
                        if (string.IsNullOrEmpty(gameObjectName) || rotationArray == null)
                            return Response.Error("GameObject name and rotation are required for rotate operation.");
                        return RotateGameObject(gameObjectName, rotationArray);

                    case "scale":
                        if (string.IsNullOrEmpty(gameObjectName) || scaleArray == null)
                            return Response.Error("GameObject name and scale are required for scale operation.");
                        return ScaleGameObject(gameObjectName, scaleArray);

                    case "find":
                        if (string.IsNullOrEmpty(query) && string.IsNullOrEmpty(gameObjectName))
                            return Response.Error("Query or GameObject name is required for find operation.");
                        return FindGameObjects(query ?? gameObjectName, includeChildren ?? false);

                    case "get_component":
                        if (string.IsNullOrEmpty(gameObjectName) || string.IsNullOrEmpty(componentType))
                            return Response.Error("GameObject name and component type are required for get_component operation.");
                        return GetComponent(gameObjectName, componentType);

                    case "set_component":
                        if (string.IsNullOrEmpty(gameObjectName) || string.IsNullOrEmpty(componentType) || componentProperties == null)
                            return Response.Error("GameObject name, component type, and properties are required for set_component operation.");
                        return SetComponent(gameObjectName, componentType, componentProperties);

                    case "add_component":
                        if (string.IsNullOrEmpty(gameObjectName) || string.IsNullOrEmpty(componentType))
                            return Response.Error("GameObject name and component type are required for add_component operation.");
                        return AddComponent(gameObjectName, componentType, componentProperties);

                    case "remove_component":
                        if (string.IsNullOrEmpty(gameObjectName) || string.IsNullOrEmpty(componentType))
                            return Response.Error("GameObject name and component type are required for remove_component operation.");
                        return RemoveComponent(gameObjectName, componentType);

                    case "get_position":
                        if (string.IsNullOrEmpty(gameObjectName))
                            return Response.Error("GameObject name is required for get_position operation.");
                        return GetGameObjectPosition(gameObjectName);

                    case "get_rotation":
                        if (string.IsNullOrEmpty(gameObjectName))
                            return Response.Error("GameObject name is required for get_rotation operation.");
                        return GetGameObjectRotation(gameObjectName);

                    case "get_scale":
                        if (string.IsNullOrEmpty(gameObjectName))
                            return Response.Error("GameObject name is required for get_scale operation.");
                        return GetGameObjectScale(gameObjectName);

                    case "set_parent":
                        if (string.IsNullOrEmpty(gameObjectName))
                            return Response.Error("GameObject name is required for set_parent operation.");
                        return SetGameObjectParent(gameObjectName, parentName);

                    case "set_active":
                        if (string.IsNullOrEmpty(gameObjectName) || activeState == null)
                            return Response.Error("GameObject name and active state are required for set_active operation.");
                        return SetGameObjectActive(gameObjectName, activeState.Value);

                    case "capture_screenshot":
                        if (string.IsNullOrEmpty(screenshotPath))
                            return Response.Error("Screenshot path is required for capture_screenshot operation.");
                        return CaptureScreenshot(screenshotPath);

                    default:
                        return Response.Error($"Scene action '{action}' is recognized but not yet implemented.");
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Exception during {(@params["action"] ?? "unknown")} operation: {e}");
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
                Debug.LogError($"[ManageScene] Error creating scene: {e}");
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
                Debug.LogError($"[ManageScene] Error loading scene: {e}");
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
                Debug.LogError($"[ManageScene] Error saving scene: {e}");
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
                Debug.LogError($"[ManageScene] Error closing scene: {e}");
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
                Debug.LogError($"[ManageScene] Error creating new scene: {e}");
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
                Debug.LogError($"[ManageScene] Error getting active scene info: {e}");
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
                Debug.LogError($"[ManageScene] Error getting loaded scenes info: {e}");
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
                Debug.LogError($"[ManageScene] Error setting active scene: {e}");
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
                Debug.LogError($"[ManageScene] Error adding scene to build: {e}");
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
                Debug.LogError($"[ManageScene] Error removing scene from build: {e}");
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

        // --- GameObject Operations ---

        private static object InstantiatePrefab(string prefabPath, JArray position, JArray rotation, JArray scale, string parentName)
        {
            try
            {
                // Load the prefab
                GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
                if (prefab == null)
                {
                    return Response.Error($"Could not load prefab at path '{prefabPath}'.");
                }

                // Instantiate the prefab
                GameObject instance = UnityEngine.Object.Instantiate(prefab);
                if (instance == null)
                {
                    return Response.Error($"Failed to instantiate prefab '{prefabPath}'.");
                }

                // Set position if provided
                if (position != null && position.Count >= 3)
                {
                    Vector3 pos = new Vector3(
                        position[0].ToObject<float>(),
                        position[1].ToObject<float>(),
                        position[2].ToObject<float>()
                    );
                    instance.transform.position = pos;
                }

                // Set rotation if provided
                if (rotation != null && rotation.Count >= 3)
                {
                    Vector3 rot = new Vector3(
                        rotation[0].ToObject<float>(),
                        rotation[1].ToObject<float>(),
                        rotation[2].ToObject<float>()
                    );
                    instance.transform.eulerAngles = rot;
                }

                // Set scale if provided
                if (scale != null && scale.Count >= 3)
                {
                    Vector3 scl = new Vector3(
                        scale[0].ToObject<float>(),
                        scale[1].ToObject<float>(),
                        scale[2].ToObject<float>()
                    );
                    instance.transform.localScale = scl;
                }

                // Set parent if provided
                if (!string.IsNullOrEmpty(parentName))
                {
                    GameObject parent = GameObject.Find(parentName);
                    if (parent != null)
                    {
                        instance.transform.SetParent(parent.transform, false);
                    }
                    else
                    {
                        Debug.LogWarning($"Parent GameObject '{parentName}' not found. The prefab instance will be at the root level.");
                    }
                }

                return Response.Success($"Prefab '{prefabPath}' instantiated successfully.", new { 
                    instanceID = instance.GetInstanceID(),
                    name = instance.name,
                    path = GetGameObjectPath(instance)
                });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error instantiating prefab: {e}");
                return Response.Error($"Error instantiating prefab: {e.Message}");
            }
        }

        private static object DeleteGameObject(string gameObjectName)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                UnityEngine.Object.DestroyImmediate(go);
                return Response.Success($"GameObject '{gameObjectName}' deleted successfully.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error deleting GameObject: {e}");
                return Response.Error($"Error deleting GameObject: {e.Message}");
            }
        }

        private static object MoveGameObject(string gameObjectName, JArray position)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                if (position.Count < 3)
                {
                    return Response.Error("Position array must contain 3 elements (x, y, z).");
                }

                Vector3 pos = new Vector3(
                    position[0].ToObject<float>(),
                    position[1].ToObject<float>(),
                    position[2].ToObject<float>()
                );
                go.transform.position = pos;

                return Response.Success($"GameObject '{gameObjectName}' moved to {pos}.", new {
                    position = new float[] { pos.x, pos.y, pos.z }
                });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error moving GameObject: {e}");
                return Response.Error($"Error moving GameObject: {e.Message}");
            }
        }

        private static object RotateGameObject(string gameObjectName, JArray rotation)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                if (rotation.Count < 3)
                {
                    return Response.Error("Rotation array must contain 3 elements (x, y, z).");
                }

                Vector3 rot = new Vector3(
                    rotation[0].ToObject<float>(),
                    rotation[1].ToObject<float>(),
                    rotation[2].ToObject<float>()
                );
                go.transform.eulerAngles = rot;

                return Response.Success($"GameObject '{gameObjectName}' rotated to {rot}.", new {
                    rotation = new float[] { rot.x, rot.y, rot.z }
                });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error rotating GameObject: {e}");
                return Response.Error($"Error rotating GameObject: {e.Message}");
            }
        }

        private static object ScaleGameObject(string gameObjectName, JArray scale)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                if (scale.Count < 3)
                {
                    return Response.Error("Scale array must contain 3 elements (x, y, z).");
                }

                Vector3 scl = new Vector3(
                    scale[0].ToObject<float>(),
                    scale[1].ToObject<float>(),
                    scale[2].ToObject<float>()
                );
                go.transform.localScale = scl;

                return Response.Success($"GameObject '{gameObjectName}' scaled to {scl}.", new {
                    scale = new float[] { scl.x, scl.y, scl.z }
                });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error scaling GameObject: {e}");
                return Response.Error($"Error scaling GameObject: {e.Message}");
            }
        }

        private static object FindGameObjects(string query, bool includeChildren)
        {
            try
            {
                var foundObjects = new List<GameObject>();
                GameObject rootObject = GameObject.Find(query);
                
                if (rootObject != null)
                {
                    foundObjects.Add(rootObject);
                    
                    if (includeChildren)
                    {
                        // Add all children recursively
                        foundObjects.AddRange(GetAllChildren(rootObject.transform));
                    }
                }
                else
                {
                    // Try finding by tag
                    GameObject[] taggedObjects = GameObject.FindGameObjectsWithTag(query);
                    if (taggedObjects != null && taggedObjects.Length > 0)
                    {
                        foundObjects.AddRange(taggedObjects);
                        
                        if (includeChildren)
                        {
                            foreach (var taggedObject in taggedObjects)
                            {
                                foundObjects.AddRange(GetAllChildren(taggedObject.transform));
                            }
                        }
                    }
                    else
                    {
                        // If still not found, search all GameObjects in the scene
                        var allGameObjects = Resources.FindObjectsOfTypeAll<GameObject>();
                        foreach (var go in allGameObjects)
                        {
                            if (go.scene.IsValid() && go.name.Contains(query))
                            {
                                foundObjects.Add(go);
                                
                                if (includeChildren)
                                {
                                    foundObjects.AddRange(GetAllChildren(go.transform));
                                }
                            }
                        }
                    }
                }

                if (foundObjects.Count == 0)
                {
                    return Response.Error($"No GameObjects found matching '{query}'.");
                }

                var result = foundObjects.Select(go => new {
                    name = go.name,
                    path = GetGameObjectPath(go),
                    instanceID = go.GetInstanceID(),
                    isActive = go.activeInHierarchy
                }).ToList();

                return Response.Success($"Found {foundObjects.Count} GameObjects matching '{query}'.", result);
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error finding GameObjects: {e}");
                return Response.Error($"Error finding GameObjects: {e.Message}");
            }
        }
        
        private static List<GameObject> GetAllChildren(Transform parent)
        {
            var children = new List<GameObject>();
            foreach (Transform child in parent)
            {
                children.Add(child.gameObject);
                children.AddRange(GetAllChildren(child));
            }
            return children;
        }

        private static object GetComponent(string gameObjectName, string componentType)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                Type type = FindType(componentType);
                if (type == null)
                {
                    return Response.Error($"Component type '{componentType}' not found.");
                }

                Component component = go.GetComponent(type);
                if (component == null)
                {
                    return Response.Error($"Component '{componentType}' not found on GameObject '{gameObjectName}'.");
                }

                // A completely different approach - use a manually constructed dictionary with 
                // carefully selected properties to avoid serialization issues
                var result = new Dictionary<string, object>();

                // Common properties for all components
                result["componentType"] = type.FullName;
                result["enabled"] = component is Behaviour behaviour ? behaviour.enabled : true;
                result["name"] = component.name;

                // Handle specific component types
                if (component is Camera camera)
                {
                    // Carefully cherry-pick Camera properties
                    var cameraProps = new Dictionary<string, object>();
                    
                    // Basic Camera properties that are safe to serialize
                    AddSafeProperty(cameraProps, "fieldOfView", camera.fieldOfView);
                    AddSafeProperty(cameraProps, "nearClipPlane", camera.nearClipPlane);
                    AddSafeProperty(cameraProps, "farClipPlane", camera.farClipPlane);
                    AddSafeProperty(cameraProps, "depth", camera.depth);
                    AddSafeProperty(cameraProps, "orthographic", camera.orthographic);
                    AddSafeProperty(cameraProps, "orthographicSize", camera.orthographicSize);
                    AddSafeProperty(cameraProps, "aspect", camera.aspect);
                    AddSafeProperty(cameraProps, "useOcclusionCulling", camera.useOcclusionCulling);
                    AddSafeProperty(cameraProps, "allowHDR", camera.allowHDR);
                    AddSafeProperty(cameraProps, "allowMSAA", camera.allowMSAA);
                    AddSafeProperty(cameraProps, "clearFlags", camera.clearFlags.ToString());
                    AddSafeProperty(cameraProps, "cullingMask", camera.cullingMask);
                    AddSafeProperty(cameraProps, "backgroundColor", 
                        new { r = camera.backgroundColor.r, g = camera.backgroundColor.g, 
                              b = camera.backgroundColor.b, a = camera.backgroundColor.a });
                    
                    result["properties"] = cameraProps;
                }
                else if (component is Transform transform)
                {
                    // Carefully cherry-pick Transform properties
                    var transformProps = new Dictionary<string, object>();
                    
                    // Position as flat array to avoid nested vectors
                    AddSafeProperty(transformProps, "position", 
                        new float[] { transform.position.x, transform.position.y, transform.position.z });
                    
                    // Rotation as flat array
                    AddSafeProperty(transformProps, "rotation", 
                        new float[] { transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w });
                    
                    // Euler angles as flat array
                    AddSafeProperty(transformProps, "eulerAngles", 
                        new float[] { transform.eulerAngles.x, transform.eulerAngles.y, transform.eulerAngles.z });
                    
                    // Local position as flat array
                    AddSafeProperty(transformProps, "localPosition", 
                        new float[] { transform.localPosition.x, transform.localPosition.y, transform.localPosition.z });
                    
                    // Local scale as flat array
                    AddSafeProperty(transformProps, "localScale", 
                        new float[] { transform.localScale.x, transform.localScale.y, transform.localScale.z });
                    
                    // Parent info if there is one
                    if (transform.parent != null)
                    {
                        AddSafeProperty(transformProps, "parent", transform.parent.name);
                    }
                    
                    result["properties"] = transformProps;
                }
                else
                {
                    // For other component types, use reflection but be very selective
                    var objProps = new Dictionary<string, object>();
                    
                    var properties = type.GetProperties(BindingFlags.Public | BindingFlags.Instance)
                                        .Where(p => p.CanRead && p.GetIndexParameters().Length == 0)
                                        .Where(p => !IsComplexOrProblematicType(p.PropertyType))
                                        .Where(p => !IsProblematicPropertyName(p.Name))
                                        .ToList();
                    
                    foreach (var prop in properties)
                    {
                        try
                        {
                            var value = prop.GetValue(component);
                            
                            // Skip null values
                            if (value == null) continue;
                            
                            // Skip Unity Object references (to avoid circular dependencies)
                            if (value is UnityEngine.Object) continue;
                            
                            // Handle basic types
                            if (value is int || value is float || value is double || 
                                value is bool || value is string || value is Enum)
                            {
                                AddSafeProperty(objProps, prop.Name, value);
                            }
                            // Handle Vector3
                            else if (value is Vector3 v3)
                            {
                                AddSafeProperty(objProps, prop.Name, new float[] { v3.x, v3.y, v3.z });
                            }
                            // Handle Vector2
                            else if (value is Vector2 v2)
                            {
                                AddSafeProperty(objProps, prop.Name, new float[] { v2.x, v2.y });
                            }
                            // Handle Quaternion
                            else if (value is Quaternion q)
                            {
                                AddSafeProperty(objProps, prop.Name, new float[] { q.x, q.y, q.z, q.w });
                            }
                            // Handle Color
                            else if (value is Color c)
                            {
                                AddSafeProperty(objProps, prop.Name, new float[] { c.r, c.g, c.b, c.a });
                            }
                            // Other types - just use string representation to be safe
                            else if (value.GetType().IsValueType)
                            {
                                AddSafeProperty(objProps, prop.Name, value.ToString());
                            }
                        }
                        catch (Exception ex)
                        {
                            Debug.LogWarning($"Error getting property {prop.Name}: {ex.Message}");
                        }
                    }
                    
                    result["properties"] = objProps;
                }

                return Response.Success($"Retrieved component '{componentType}' from GameObject '{gameObjectName}'.", result);
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error getting component: {e}");
                return Response.Error($"Error getting component: {e.Message}");
            }
        }

        private static void AddSafeProperty(Dictionary<string, object> dict, string name, object value)
        {
            if (value != null)
            {
                dict[name] = value;
            }
        }

        private static bool IsComplexOrProblematicType(Type type)
        {
            // List of types known to cause serialization issues
            Type[] problematicTypes = new[] {
                typeof(Matrix4x4),
                typeof(Mesh),
                typeof(Material),
                typeof(Texture),
                typeof(AnimationCurve),
                typeof(Gradient),
                typeof(GUIStyle),
                typeof(RenderTexture),
                typeof(Transform),
                typeof(GameObject),
                typeof(Component)
            };
            
            if (problematicTypes.Contains(type))
                return true;
                
            // Check if it's a Unity type (could be complex)
            if (type.Assembly == typeof(UnityEngine.Object).Assembly && 
                !type.IsPrimitive && 
                type != typeof(string) &&
                !type.IsEnum &&
                type != typeof(Vector2) &&
                type != typeof(Vector3) &&
                type != typeof(Vector4) &&
                type != typeof(Quaternion) &&
                type != typeof(Color))
            {
                return true;
            }
            
            return false;
        }

        private static bool IsProblematicPropertyName(string propertyName)
        {
            // Names known to cause issues
            string[] problematicNames = new[] {
                "cullingMatrix", "projectionMatrix", "worldToCameraMatrix", "cameraToWorldMatrix",
                "localToWorldMatrix", "worldToLocalMatrix", "matrix", "parent", "normalized",
                "mesh", "material", "sharedMesh", "sharedMaterial", "gameObject", "transform",
                "root", "hierarchyCount", "hierarchyCapacity", "components"
            };
            
            if (problematicNames.Contains(propertyName))
                return true;
            
            // Suffixes that often indicate complex/problematic properties
            string[] problematicSuffixes = new[] {
                "Matrix", "Matrices", "Quaternion", "GameObject", "Transform", "Component", "Object",
                "List", "Array", "Collection", "Dictionary", "Map", "Lookup"
            };
            
            foreach (var suffix in problematicSuffixes)
            {
                if (propertyName.EndsWith(suffix, StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            
            return false;
        }

        private static object SetComponent(string gameObjectName, string componentType, JObject properties)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                Type type = FindType(componentType);
                if (type == null)
                {
                    return Response.Error($"Component type '{componentType}' not found.");
                }

                Component component = go.GetComponent(type);
                if (component == null)
                {
                    return Response.Error($"Component '{componentType}' not found on GameObject '{gameObjectName}'.");
                }

                bool anyPropertySet = false;
                foreach (var prop in properties.Properties())
                {
                    try
                    {
                        var property = type.GetProperty(prop.Name, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance);
                        if (property != null && property.CanWrite)
                        {
                            object convertedValue = ConvertJTokenToPropertyType(prop.Value, property.PropertyType);
                            property.SetValue(component, convertedValue);
                            anyPropertySet = true;
                        }
                        else
                        {
                            Debug.LogWarning($"Property '{prop.Name}' not found or not writable on {componentType}.");
                        }
                    }
                    catch (Exception propEx)
                    {
                        Debug.LogWarning($"Error setting property {prop.Name} on {componentType}: {propEx.Message}");
                    }
                }

                if (!anyPropertySet)
                {
                    return Response.Error($"No properties were set on component '{componentType}'. Check property names and types.");
                }

                return Response.Success($"Updated component '{componentType}' on GameObject '{gameObjectName}'.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error setting component: {e}");
                return Response.Error($"Error setting component: {e.Message}");
            }
        }

        private static object ConvertJTokenToPropertyType(JToken token, Type targetType)
        {
            if (token.Type == JTokenType.Null)
                return null;
                
            if (targetType == typeof(string))
                return token.ToString();
                
            if (targetType == typeof(int) || targetType == typeof(int?))
                return token.ToObject<int>();
                
            if (targetType == typeof(float) || targetType == typeof(float?))
                return token.ToObject<float>();
                
            if (targetType == typeof(bool) || targetType == typeof(bool?))
                return token.ToObject<bool>();
                
            if (targetType == typeof(Vector2) && token is JArray arr && arr.Count >= 2)
                return new Vector2(arr[0].ToObject<float>(), arr[1].ToObject<float>());
                
            if (targetType == typeof(Vector3) && token is JArray arr3 && arr3.Count >= 3)
                return new Vector3(arr3[0].ToObject<float>(), arr3[1].ToObject<float>(), arr3[2].ToObject<float>());
                
            if (targetType == typeof(Vector4) && token is JArray arr4 && arr4.Count >= 4)
                return new Vector4(arr4[0].ToObject<float>(), arr4[1].ToObject<float>(), arr4[2].ToObject<float>(), arr4[3].ToObject<float>());
                
            if (targetType == typeof(Quaternion) && token is JArray arrQ && arrQ.Count >= 4)
                return new Quaternion(arrQ[0].ToObject<float>(), arrQ[1].ToObject<float>(), arrQ[2].ToObject<float>(), arrQ[3].ToObject<float>());
                
            if (targetType == typeof(Color) && token is JArray arrC && arrC.Count >= 3)
                return new Color(arrC[0].ToObject<float>(), arrC[1].ToObject<float>(), arrC[2].ToObject<float>(), arrC.Count > 3 ? arrC[3].ToObject<float>() : 1f);
                
            // For enums, parse the string representation
            if (targetType.IsEnum)
                return Enum.Parse(targetType, token.ToString(), true);
                
            // Default case: try direct conversion
            return token.ToObject(targetType);
        }

        private static object AddComponent(string gameObjectName, string componentType, JObject properties = null)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                Type type = FindType(componentType);
                if (type == null)
                {
                    return Response.Error($"Component type '{componentType}' not found.");
                }

                if (go.GetComponent(type) != null)
                {
                    return Response.Error($"Component '{componentType}' already exists on GameObject '{gameObjectName}'.");
                }

                Component component = go.AddComponent(type);
                if (component == null)
                {
                    return Response.Error($"Failed to add component '{componentType}' to GameObject '{gameObjectName}'.");
                }

                // Set properties if provided
                if (properties != null && properties.Count > 0)
                {
                    foreach (var prop in properties.Properties())
                    {
                        try
                        {
                            var property = type.GetProperty(prop.Name, System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.Instance);
                            if (property != null && property.CanWrite)
                            {
                                object convertedValue = ConvertJTokenToPropertyType(prop.Value, property.PropertyType);
                                property.SetValue(component, convertedValue);
                            }
                        }
                        catch (Exception propEx)
                        {
                            Debug.LogWarning($"Error setting property {prop.Name} on new {componentType}: {propEx.Message}");
                        }
                    }
                }

                return Response.Success($"Added component '{componentType}' to GameObject '{gameObjectName}'.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error adding component: {e}");
                return Response.Error($"Error adding component: {e.Message}");
            }
        }

        private static object RemoveComponent(string gameObjectName, string componentType)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                Type type = FindType(componentType);
                if (type == null)
                {
                    return Response.Error($"Component type '{componentType}' not found.");
                }

                Component component = go.GetComponent(type);
                if (component == null)
                {
                    return Response.Error($"Component '{componentType}' not found on GameObject '{gameObjectName}'.");
                }

                if (type == typeof(Transform))
                {
                    return Response.Error("Cannot remove Transform component from GameObject.");
                }

                UnityEngine.Object.DestroyImmediate(component);
                return Response.Success($"Removed component '{componentType}' from GameObject '{gameObjectName}'.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error removing component: {e}");
                return Response.Error($"Error removing component: {e.Message}");
            }
        }

        private static object GetGameObjectPosition(string gameObjectName)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                Vector3 position = go.transform.position;
                return Response.Success($"Retrieved position of GameObject '{gameObjectName}'.", new {
                    position = new float[] { position.x, position.y, position.z }
                });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error getting GameObject position: {e}");
                return Response.Error($"Error getting GameObject position: {e.Message}");
            }
        }

        private static object GetGameObjectRotation(string gameObjectName)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                Vector3 rotation = go.transform.eulerAngles;
                return Response.Success($"Retrieved rotation of GameObject '{gameObjectName}'.", new {
                    rotation = new float[] { rotation.x, rotation.y, rotation.z }
                });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error getting GameObject rotation: {e}");
                return Response.Error($"Error getting GameObject rotation: {e.Message}");
            }
        }

        private static object GetGameObjectScale(string gameObjectName)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                Vector3 scale = go.transform.localScale;
                return Response.Success($"Retrieved scale of GameObject '{gameObjectName}'.", new {
                    scale = new float[] { scale.x, scale.y, scale.z }
                });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error getting GameObject scale: {e}");
                return Response.Error($"Error getting GameObject scale: {e.Message}");
            }
        }

        private static object SetGameObjectParent(string gameObjectName, string parentName)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                if (string.IsNullOrEmpty(parentName))
                {
                    // Set to root (no parent)
                    go.transform.SetParent(null);
                    return Response.Success($"GameObject '{gameObjectName}' set to root (no parent).");
                }
                else
                {
                    GameObject parent = GameObject.Find(parentName);
                    if (parent == null)
                    {
                        return Response.Error($"Parent GameObject '{parentName}' not found.");
                    }

                    go.transform.SetParent(parent.transform);
                    return Response.Success($"GameObject '{gameObjectName}' parented to '{parentName}'.");
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error setting GameObject parent: {e}");
                return Response.Error($"Error setting GameObject parent: {e.Message}");
            }
        }

        private static object SetGameObjectActive(string gameObjectName, bool active)
        {
            try
            {
                GameObject go = GameObject.Find(gameObjectName);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectName}' not found.");
                }

                go.SetActive(active);
                return Response.Success($"GameObject '{gameObjectName}' set {(active ? "active" : "inactive")}.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error setting GameObject active state: {e}");
                return Response.Error($"Error setting GameObject active state: {e.Message}");
            }
        }

        private static object CaptureScreenshot(string screenshotPath)
        {
            try
            {
                // Ensure path is valid
                if (!screenshotPath.ToLower().EndsWith(".png"))
                {
                    screenshotPath += ".png";
                }
                
                string directory = Path.GetDirectoryName(screenshotPath);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                // Capture screenshot
                ScreenCapture.CaptureScreenshot(screenshotPath);
                
                return Response.Success($"Screenshot captured and saved to '{screenshotPath}'.", new {
                    path = screenshotPath
                });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManageScene] Error capturing screenshot: {e}");
                return Response.Error($"Error capturing screenshot: {e.Message}");
            }
        }

        // Helper method to find a type by name
        private static Type FindType(string typeName)
        {
            // First try direct type lookup
            Type type = Type.GetType(typeName);
            if (type != null)
                return type;
            
            // If not found, try with UnityEngine namespace
            if (!typeName.StartsWith("UnityEngine."))
            {
                type = Type.GetType($"UnityEngine.{typeName}");
                if (type != null)
                    return type;
            }
            
            // Search in all loaded assemblies
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                type = assembly.GetType(typeName);
                if (type != null)
                    return type;
                
                // Try with UnityEngine namespace if not already specified
                if (!typeName.StartsWith("UnityEngine."))
                {
                    type = assembly.GetType($"UnityEngine.{typeName}");
                    if (type != null)
                        return type;
                }
            }
            
            return null;
        }

        // Helper method to get the full path of a GameObject in the hierarchy
        private static string GetGameObjectPath(GameObject gameObject)
        {
            string path = gameObject.name;
            Transform parent = gameObject.transform.parent;
            
            while (parent != null)
            {
                path = parent.name + "/" + path;
                parent = parent.parent;
            }
            
            return path;
        }
    }
} 