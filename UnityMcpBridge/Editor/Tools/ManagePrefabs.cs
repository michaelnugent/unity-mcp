using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityMcpBridge.Editor.Helpers;

namespace UnityMcpBridge.Editor.Tools
{
    /// <summary>
    /// Handles operations related to Unity Prefabs, such as creating, editing, and instantiating.
    /// </summary>
    [InitializeOnLoad]
    public static class ManagePrefabs
    {
        private static readonly List<string> ValidActions = new List<string>
        {
            "create", "open", "save", "revert", "apply", "update", "create_variant",
            "unpack", "list_overrides", "add_component", "remove_component", "instantiate"
        };

        static ManagePrefabs()
        {
            CommandRegistry.RegisterCommand("manage_prefabs", HandleCommand);
        }

        /// <summary>
        /// Main handler for prefab operations.
        /// </summary>
        public static object HandleCommand(JObject @params)
        {
            try
            {
                string action = @params["action"]?.ToString()?.ToLower();

                if (string.IsNullOrEmpty(action))
                {
                    return Response.Error("No action specified for prefab operation.");
                }

                if (!ValidActions.Contains(action))
                {
                    return Response.Error($"Invalid prefab action: '{action}'. Valid actions are: {string.Join(", ", ValidActions)}");
                }

                string prefabPath = @params["prefab_path"]?.ToString();
                string destinationPath = @params["destination_path"]?.ToString();
                string gameObjectPath = @params["game_object_path"]?.ToString();
                string componentType = @params["component_type"]?.ToString();
                JObject componentProperties = @params["component_properties"] as JObject;
                JArray position = @params["position"] as JArray;
                JArray rotation = @params["rotation"] as JArray;
                JArray scale = @params["scale"] as JArray;
                string parentPath = @params["parent_path"]?.ToString();
                JArray overrides = @params["overrides"] as JArray;
                string variantName = @params["variant_name"]?.ToString();
                JObject modifiedProperties = @params["modified_properties"] as JObject;

                Debug.Log($"[ManagePrefabs] Action: {action}");

                // Route to specific action handlers
                switch (action)
                {
                    case "create":
                        if (string.IsNullOrEmpty(gameObjectPath))
                            return Response.Error("GameObject path is required for creating a prefab.");
                        if (string.IsNullOrEmpty(destinationPath))
                            return Response.Error("Destination path is required for creating a prefab.");
                        return CreatePrefab(gameObjectPath, destinationPath);

                    case "instantiate":
                        if (string.IsNullOrEmpty(prefabPath))
                            return Response.Error("Prefab path is required for instantiation.");
                        return InstantiatePrefab(prefabPath, position, rotation, scale, parentPath);

                    case "add_component":
                        if (string.IsNullOrEmpty(prefabPath))
                            return Response.Error("Prefab path is required for adding a component.");
                        if (string.IsNullOrEmpty(componentType))
                            return Response.Error("Component type is required for adding a component.");
                        return AddComponentToPrefab(prefabPath, componentType, componentProperties);

                    case "remove_component":
                        if (string.IsNullOrEmpty(prefabPath))
                            return Response.Error("Prefab path is required for removing a component.");
                        if (string.IsNullOrEmpty(componentType))
                            return Response.Error("Component type is required for removing a component.");
                        return RemoveComponentFromPrefab(prefabPath, componentType);

                    case "create_variant":
                        if (string.IsNullOrEmpty(prefabPath))
                            return Response.Error("Prefab path is required for creating a variant.");
                        if (string.IsNullOrEmpty(destinationPath))
                            return Response.Error("Destination path is required for creating a prefab variant.");
                        return CreatePrefabVariant(prefabPath, destinationPath, variantName);

                    case "apply":
                        if (string.IsNullOrEmpty(gameObjectPath))
                            return Response.Error("GameObject path is required for applying prefab changes.");
                        return ApplyPrefabChanges(gameObjectPath, prefabPath);

                    case "unpack":
                        if (string.IsNullOrEmpty(gameObjectPath))
                            return Response.Error("GameObject path is required for unpacking a prefab.");
                        return UnpackPrefab(gameObjectPath);

                    case "list_overrides":
                        if (string.IsNullOrEmpty(gameObjectPath))
                            return Response.Error("GameObject path is required for listing prefab overrides.");
                        return ListPrefabOverrides(gameObjectPath);

                    // TODO: Implement remaining actions (open, save, revert, update) as needed
                    default:
                        return Response.Error($"Prefab action '{action}' is recognized but not yet implemented.");
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManagePrefabs] Exception during {(@params["action"] ?? "unknown")} operation: {e}");
                return Response.Error($"Error handling prefab operation: {e.Message}");
            }
        }

        private static object CreatePrefab(string gameObjectPath, string destinationPath)
        {
            try
            {
                // Find the GameObject in the scene
                GameObject go = GameObject.Find(gameObjectPath);
                if (go == null)
                {
                    return Response.Error($"GameObject '{gameObjectPath}' not found in the scene.");
                }

                // Ensure the folder exists
                string directory = System.IO.Path.GetDirectoryName(destinationPath);
                if (!string.IsNullOrEmpty(directory) && !AssetDatabase.IsValidFolder(directory))
                {
                    return Response.Error($"Directory '{directory}' does not exist. Create it first.");
                }

                // Create the prefab
                GameObject prefab = PrefabUtility.SaveAsPrefabAsset(go, destinationPath);
                if (prefab == null)
                {
                    return Response.Error($"Failed to create prefab at '{destinationPath}'.");
                }

                return Response.Success($"Prefab created successfully at '{destinationPath}'.", 
                    new { path = destinationPath });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManagePrefabs] Error creating prefab: {e}");
                return Response.Error($"Error creating prefab: {e.Message}");
            }
        }

        private static object InstantiatePrefab(string prefabPath, JArray position, JArray rotation, JArray scale, string parentPath)
        {
            try
            {
                // Load the prefab asset
                GameObject prefabAsset = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
                if (prefabAsset == null)
                {
                    return Response.Error($"Prefab not found at '{prefabPath}'.");
                }

                // Get the parent GameObject if specified
                Transform parent = null;
                if (!string.IsNullOrEmpty(parentPath))
                {
                    GameObject parentGo = GameObject.Find(parentPath);
                    if (parentGo == null)
                    {
                        return Response.Error($"Parent GameObject '{parentPath}' not found.");
                    }
                    parent = parentGo.transform;
                }

                // Instantiate the prefab
                GameObject instance = PrefabUtility.InstantiatePrefab(prefabAsset) as GameObject;
                if (instance == null)
                {
                    return Response.Error($"Failed to instantiate prefab '{prefabPath}'.");
                }

                // Set parent if specified
                if (parent != null)
                {
                    instance.transform.SetParent(parent, false);
                }

                // Set position if specified
                if (position != null && position.Count >= 3)
                {
                    Vector3 pos = new Vector3(
                        position[0].Value<float>(),
                        position[1].Value<float>(),
                        position[2].Value<float>()
                    );
                    instance.transform.position = pos;
                }

                // Set rotation if specified
                if (rotation != null && rotation.Count >= 3)
                {
                    Vector3 rot = new Vector3(
                        rotation[0].Value<float>(),
                        rotation[1].Value<float>(),
                        rotation[2].Value<float>()
                    );
                    instance.transform.eulerAngles = rot;
                }

                // Set scale if specified
                if (scale != null && scale.Count >= 3)
                {
                    Vector3 scl = new Vector3(
                        scale[0].Value<float>(),
                        scale[1].Value<float>(),
                        scale[2].Value<float>()
                    );
                    instance.transform.localScale = scl;
                }

                // Build the full hierarchy path to the new instance
                string path = GetGameObjectPath(instance);
                
                // Extract the prefab name for easier reference
                string prefabName = System.IO.Path.GetFileNameWithoutExtension(prefabPath);
                
                Debug.Log($"[ManagePrefabs] Instantiated prefab '{prefabPath}' as GameObject '{instance.name}' at path '{path}'");

                return Response.Success($"Prefab '{prefabPath}' instantiated successfully.", 
                    new { 
                        path = path, 
                        gameObjectName = instance.name,
                        prefabName = prefabName,
                        prefabPath = prefabPath,
                        instanceId = instance.GetInstanceID()
                    });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManagePrefabs] Error instantiating prefab: {e}");
                return Response.Error($"Error instantiating prefab: {e.Message}");
            }
        }

        private static object AddComponentToPrefab(string prefabPath, string componentType, JObject properties)
        {
            try
            {
                // Use PrefabUtility to open the prefab for editing
                GameObject prefabAsset = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
                if (prefabAsset == null)
                {
                    return Response.Error($"Prefab not found at '{prefabPath}'.");
                }

                // We'll need to use prefab staging or temporary instantiation
                GameObject prefabInstance = PrefabUtility.InstantiatePrefab(prefabAsset) as GameObject;
                
                // Find the component type
                Type type = FindTypeHelper(componentType);
                if (type == null)
                {
                    GameObject.DestroyImmediate(prefabInstance);
                    return Response.Error($"Component type '{componentType}' not found.");
                }

                // Add the component
                Component component = prefabInstance.AddComponent(type);
                if (component == null)
                {
                    GameObject.DestroyImmediate(prefabInstance);
                    return Response.Error($"Failed to add component '{componentType}'.");
                }

                // Set properties if specified
                if (properties != null)
                {
                    // Use a helper method to set component properties
                    // This would require additional implementation
                    SetComponentProperties(component, properties);
                }

                // Apply changes back to the prefab asset
                PrefabUtility.SaveAsPrefabAsset(prefabInstance, prefabPath);
                GameObject.DestroyImmediate(prefabInstance);

                return Response.Success($"Component '{componentType}' added to prefab '{prefabPath}'.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManagePrefabs] Error adding component to prefab: {e}");
                return Response.Error($"Error adding component to prefab: {e.Message}");
            }
        }

        private static object RemoveComponentFromPrefab(string prefabPath, string componentType)
        {
            try
            {
                // Load the prefab asset
                GameObject prefabAsset = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
                if (prefabAsset == null)
                {
                    return Response.Error($"Prefab not found at '{prefabPath}'.");
                }

                // We'll need to use prefab staging or temporary instantiation
                GameObject prefabInstance = PrefabUtility.InstantiatePrefab(prefabAsset) as GameObject;
                
                // Find the component type
                Type type = FindTypeHelper(componentType);
                if (type == null)
                {
                    GameObject.DestroyImmediate(prefabInstance);
                    return Response.Error($"Component type '{componentType}' not found.");
                }

                // Find the component
                Component component = prefabInstance.GetComponent(type);
                if (component == null)
                {
                    GameObject.DestroyImmediate(prefabInstance);
                    return Response.Error($"Component '{componentType}' not found on prefab '{prefabPath}'.");
                }

                // Remove the component
                GameObject.DestroyImmediate(component);

                // Apply changes back to the prefab asset
                PrefabUtility.SaveAsPrefabAsset(prefabInstance, prefabPath);
                GameObject.DestroyImmediate(prefabInstance);

                return Response.Success($"Component '{componentType}' removed from prefab '{prefabPath}'.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManagePrefabs] Error removing component from prefab: {e}");
                return Response.Error($"Error removing component from prefab: {e.Message}");
            }
        }

        private static object CreatePrefabVariant(string prefabPath, string destinationPath, string variantName)
        {
            try
            {
                // Load the original prefab
                GameObject originalPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
                if (originalPrefab == null)
                {
                    return Response.Error($"Original prefab not found at '{prefabPath}'.");
                }

                // Ensure destination directory exists
                string directory = System.IO.Path.GetDirectoryName(destinationPath);
                if (!string.IsNullOrEmpty(directory) && !AssetDatabase.IsValidFolder(directory))
                {
                    return Response.Error($"Directory '{directory}' does not exist. Create it first.");
                }

                // Create a temporary instance of the original prefab
                GameObject tempInstance = PrefabUtility.InstantiatePrefab(originalPrefab) as GameObject;
                
                // Set a new name if specified
                if (!string.IsNullOrEmpty(variantName))
                {
                    tempInstance.name = variantName;
                }

                // Create the variant prefab asset
                GameObject variantPrefab = PrefabUtility.SaveAsPrefabAsset(tempInstance, destinationPath);
                GameObject.DestroyImmediate(tempInstance);

                if (variantPrefab == null)
                {
                    return Response.Error($"Failed to create prefab variant at '{destinationPath}'.");
                }

                return Response.Success($"Prefab variant created successfully at '{destinationPath}'.", 
                    new { path = destinationPath });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManagePrefabs] Error creating prefab variant: {e}");
                return Response.Error($"Error creating prefab variant: {e.Message}");
            }
        }

        private static object ApplyPrefabChanges(string gameObjectPath, string prefabPath = null)
        {
            try
            {
                // Find the GameObject in the scene
                GameObject instance = GameObject.Find(gameObjectPath);
                if (instance == null)
                {
                    return Response.Error($"GameObject '{gameObjectPath}' not found in the scene.");
                }

                // Check if the GameObject is a prefab instance
                if (!PrefabUtility.IsPartOfPrefabInstance(instance))
                {
                    return Response.Error($"GameObject '{gameObjectPath}' is not a prefab instance.");
                }

                // Apply prefab changes
                PrefabUtility.ApplyPrefabInstance(instance, InteractionMode.UserAction);

                return Response.Success($"Prefab changes applied from '{gameObjectPath}' to source prefab.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManagePrefabs] Error applying prefab changes: {e}");
                return Response.Error($"Error applying prefab changes: {e.Message}");
            }
        }

        private static object UnpackPrefab(string gameObjectPath)
        {
            try
            {
                // Find the GameObject in the scene
                GameObject instance = GameObject.Find(gameObjectPath);
                if (instance == null)
                {
                    return Response.Error($"GameObject '{gameObjectPath}' not found in the scene.");
                }

                // Check if the GameObject is a prefab instance
                if (!PrefabUtility.IsPartOfPrefabInstance(instance))
                {
                    return Response.Error($"GameObject '{gameObjectPath}' is not a prefab instance.");
                }

                // Unpack the prefab instance
                PrefabUtility.UnpackPrefabInstance(instance, PrefabUnpackMode.Completely, InteractionMode.UserAction);

                return Response.Success($"Prefab instance '{gameObjectPath}' unpacked successfully.");
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManagePrefabs] Error unpacking prefab: {e}");
                return Response.Error($"Error unpacking prefab: {e.Message}");
            }
        }

        private static object ListPrefabOverrides(string gameObjectPath)
        {
            try
            {
                // Find the GameObject in the scene
                GameObject instance = GameObject.Find(gameObjectPath);
                if (instance == null)
                {
                    return Response.Error($"GameObject '{gameObjectPath}' not found in the scene.");
                }

                // Check if the GameObject is a prefab instance
                if (!PrefabUtility.IsPartOfPrefabInstance(instance))
                {
                    return Response.Error($"GameObject '{gameObjectPath}' is not a prefab instance.");
                }

                // Get prefab modifications
                PropertyModification[] modifications = PrefabUtility.GetPropertyModifications(instance);
                if (modifications == null || modifications.Length == 0)
                {
                    return Response.Success($"No overrides found on prefab instance '{gameObjectPath}'.", 
                        new { overrides = new object[0] });
                }

                // Convert modifications to a more readable format
                var overrides = modifications.Select(mod => new {
                    targetObject = mod.target != null ? mod.target.name : "unknown",
                    targetObjectType = mod.target != null ? mod.target.GetType().Name : "unknown",
                    propertyPath = mod.propertyPath,
                    value = mod.value
                }).ToArray();

                return Response.Success($"Found {overrides.Length} overrides on prefab instance '{gameObjectPath}'.", 
                    new { overrides = overrides });
            }
            catch (Exception e)
            {
                Debug.LogError($"[ManagePrefabs] Error listing prefab overrides: {e}");
                return Response.Error($"Error listing prefab overrides: {e.Message}");
            }
        }

        /// <summary>
        /// Helper method to find a type by name.
        /// </summary>
        /// <param name="typeName">The name of the type to find.</param>
        /// <returns>The Type object if found, null otherwise.</returns>
        private static Type FindTypeHelper(string typeName)
        {
            // First, try a simple Type.GetType as it's fastest
            Type type = Type.GetType(typeName);
            if (type != null) return type;

            // Check if it's a built-in Unity type
            if (typeName.StartsWith("UnityEngine."))
            {
                type = typeof(UnityEngine.Object).Assembly.GetType(typeName);
                if (type != null) return type;
            }

            // Search through all loaded assemblies
            foreach (Assembly assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                try
                {
                    // Try to find the exact type
                    type = assembly.GetType(typeName);
                    if (type != null) return type;

                    // If no exact match, try to find a type whose name matches (without namespace)
                    foreach (Type t in assembly.GetTypes())
                    {
                        if (t.Name == typeName || t.FullName == typeName)
                            return t;
                    }
                }
                catch (Exception)
                {
                    // Some assemblies might throw exceptions when getting types
                    continue;
                }
            }

            return null;
        }

        /// <summary>
        /// Helper method to set properties on a component from a JObject.
        /// </summary>
        private static void SetComponentProperties(Component component, JObject properties)
        {
            if (component == null || properties == null)
                return;

            Type componentType = component.GetType();

            foreach (var prop in properties)
            {
                string propertyName = prop.Key;
                JToken value = prop.Value;

                // Try to find a property with this name
                PropertyInfo property = componentType.GetProperty(propertyName);
                if (property != null && property.CanWrite)
                {
                    try
                    {
                        // Convert JToken to the property's type
                        object convertedValue = ConvertJTokenToType(value, property.PropertyType);
                        property.SetValue(component, convertedValue);
                    }
                    catch (Exception ex)
                    {
                        Debug.LogWarning($"Failed to set property {propertyName}: {ex.Message}");
                    }
                    continue;
                }

                // Try to find a field with this name
                FieldInfo field = componentType.GetField(propertyName);
                if (field != null)
                {
                    try
                    {
                        // Convert JToken to the field's type
                        object convertedValue = ConvertJTokenToType(value, field.FieldType);
                        field.SetValue(component, convertedValue);
                    }
                    catch (Exception ex)
                    {
                        Debug.LogWarning($"Failed to set field {propertyName}: {ex.Message}");
                    }
                }
            }
        }

        /// <summary>
        /// Helper method to convert a JToken to a specific type.
        /// </summary>
        private static object ConvertJTokenToType(JToken token, Type targetType)
        {
            if (token == null)
                return null;

            // Handle primitive types
            if (targetType == typeof(int) || targetType == typeof(Int32))
                return token.Value<int>();
            if (targetType == typeof(float) || targetType == typeof(Single))
                return token.Value<float>();
            if (targetType == typeof(double))
                return token.Value<double>();
            if (targetType == typeof(bool))
                return token.Value<bool>();
            if (targetType == typeof(string))
                return token.Value<string>();

            // Handle Vector2
            if (targetType == typeof(Vector2) && token is JArray arr && arr.Count >= 2)
            {
                return new Vector2(arr[0].Value<float>(), arr[1].Value<float>());
            }

            // Handle Vector3
            if (targetType == typeof(Vector3) && token is JArray arr2 && arr2.Count >= 3)
            {
                return new Vector3(
                    arr2[0].Value<float>(),
                    arr2[1].Value<float>(),
                    arr2[2].Value<float>()
                );
            }

            // Handle Color
            if (targetType == typeof(Color) && token is JArray colorArr && colorArr.Count >= 3)
            {
                if (colorArr.Count >= 4)
                {
                    return new Color(
                        colorArr[0].Value<float>(),
                        colorArr[1].Value<float>(),
                        colorArr[2].Value<float>(),
                        colorArr[3].Value<float>()
                    );
                }
                else
                {
                    return new Color(
                        colorArr[0].Value<float>(),
                        colorArr[1].Value<float>(),
                        colorArr[2].Value<float>()
                    );
                }
            }

            // Handle Quaternion
            if (targetType == typeof(Quaternion) && token is JArray quatArr && quatArr.Count >= 4)
            {
                return new Quaternion(
                    quatArr[0].Value<float>(),
                    quatArr[1].Value<float>(),
                    quatArr[2].Value<float>(),
                    quatArr[3].Value<float>()
                );
            }

            // Handle enums
            if (targetType.IsEnum)
            {
                try
                {
                    // If the token is a string, try to parse it directly
                    if (token.Type == JTokenType.String)
                    {
                        return Enum.Parse(targetType, token.Value<string>(), true);
                    }
                    // If the token is a number, convert it to the enum
                    else if (token.Type == JTokenType.Integer)
                    {
                        return Enum.ToObject(targetType, token.Value<int>());
                    }
                }
                catch
                {
                    Debug.LogWarning($"Failed to convert {token} to enum type {targetType.Name}");
                }
            }

            // Default: let JSON.NET try to convert
            try
            {
                return token.ToObject(targetType);
            }
            catch
            {
                Debug.LogWarning($"Could not convert {token} to type {targetType.Name}");
                return null;
            }
        }

        private static string GetGameObjectPath(GameObject obj)
        {
            string path = obj.name;
            Transform parent = obj.transform.parent;
            
            while (parent != null)
            {
                path = parent.name + "/" + path;
                parent = parent.parent;
            }
            
            return path;
        }
    }
} 