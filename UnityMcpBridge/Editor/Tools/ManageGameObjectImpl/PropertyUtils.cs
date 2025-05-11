using System;
using System.Collections.Generic;
using System.Reflection;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityMcpBridge.Editor.Helpers;

namespace UnityMcpBridge.Editor.Tools.ManageGameObjectImpl
{
    /// <summary>
    /// Utility methods for handling property operations on Unity objects.
    /// Part of the ManageGameObject tool's internal implementation.
    /// </summary>
    internal static class PropertyUtils
    {
        /// <summary>
        /// Helper to set a property or field via reflection, handling basic types.
        /// </summary>
        public static bool SetProperty(object target, string memberName, JToken value)
        {
            Type type = target.GetType();
            BindingFlags flags = BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase;

            try
            {
                // Handle special case for materials with dot notation (material.property)
                // Examples: material.color, sharedMaterial.color, materials[0].color
                if (memberName.Contains('.') || memberName.Contains('['))
                {
                    return SetNestedProperty(target, memberName, value);
                }

                PropertyInfo propInfo = type.GetProperty(memberName, flags);
                if (propInfo != null && propInfo.CanWrite)
                {
                    object convertedValue = ConvertJTokenToType(value, propInfo.PropertyType);
                    if (convertedValue != null)
                    {
                        propInfo.SetValue(target, convertedValue);
                        return true;
                    }
                }
                else
                {
                    FieldInfo fieldInfo = type.GetField(memberName, flags);
                    if (fieldInfo != null)
                    {
                        object convertedValue = ConvertJTokenToType(value, fieldInfo.FieldType);
                        if (convertedValue != null)
                        {
                            fieldInfo.SetValue(target, convertedValue);
                            return true;
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[SetProperty] Failed to set '{memberName}' on {type.Name}: {ex.Message}");
            }
            return false;
        }

        /// <summary>
        /// Sets a nested property using dot notation (e.g., "material.color") or array access (e.g., "materials[0]")
        /// </summary>
        public static bool SetNestedProperty(object target, string path, JToken value)
        {
            try
            {
                // Split the path into parts (handling both dot notation and array indexing)
                string[] pathParts = SplitPropertyPath(path);
                if (pathParts.Length == 0)
                    return false;

                object currentObject = target;
                Type currentType = currentObject.GetType();
                BindingFlags flags = BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase;

                // Traverse the path until we reach the final property
                for (int i = 0; i < pathParts.Length - 1; i++)
                {
                    string part = pathParts[i];
                    bool isArray = false;
                    int arrayIndex = -1;

                    // Check if this part contains array indexing
                    if (part.Contains("["))
                    {
                        int startBracket = part.IndexOf('[');
                        int endBracket = part.IndexOf(']');
                        if (startBracket > 0 && endBracket > startBracket)
                        {
                            string indexStr = part.Substring(startBracket + 1, endBracket - startBracket - 1);
                            if (int.TryParse(indexStr, out arrayIndex))
                            {
                                isArray = true;
                                part = part.Substring(0, startBracket);
                            }
                        }
                    }

                    // Get the property/field
                    PropertyInfo propInfo = currentType.GetProperty(part, flags);
                    FieldInfo fieldInfo = null;
                    if (propInfo == null)
                    {
                        fieldInfo = currentType.GetField(part, flags);
                        if (fieldInfo == null)
                        {
                            Debug.LogWarning($"[SetNestedProperty] Could not find property or field '{part}' on type '{currentType.Name}'");
                            return false;
                        }
                    }

                    // Get the value
                    currentObject = propInfo != null
                        ? propInfo.GetValue(currentObject)
                        : fieldInfo.GetValue(currentObject);

                    // If the current property is null, we need to stop
                    if (currentObject == null)
                    {
                        Debug.LogWarning($"[SetNestedProperty] Property '{part}' is null, cannot access nested properties.");
                        return false;
                    }

                    // If this is an array/list access, get the element at the index
                    if (isArray)
                    {
                        if (currentObject is Material[])
                        {
                            var materials = currentObject as Material[];
                            if (arrayIndex < 0 || arrayIndex >= materials.Length)
                            {
                                Debug.LogWarning($"[SetNestedProperty] Material index {arrayIndex} out of range (0-{materials.Length - 1})");
                                return false;
                            }
                            currentObject = materials[arrayIndex];
                        }
                        else if (currentObject is System.Collections.IList)
                        {
                            var list = currentObject as System.Collections.IList;
                            if (arrayIndex < 0 || arrayIndex >= list.Count)
                            {
                                Debug.LogWarning($"[SetNestedProperty] Index {arrayIndex} out of range (0-{list.Count - 1})");
                                return false;
                            }
                            currentObject = list[arrayIndex];
                        }
                        else
                        {
                            Debug.LogWarning($"[SetNestedProperty] Property '{part}' is not an array or list, cannot access by index.");
                            return false;
                        }
                    }

                    // Update type for next iteration
                    currentType = currentObject.GetType();
                }

                // Set the final property
                string finalPart = pathParts[pathParts.Length - 1];

                // Special handling for Material properties (shader properties)
                if (currentObject is Material material && finalPart.StartsWith("_"))
                {
                    // Handle various material property types
                    if (value is JArray jArray)
                    {
                        if (jArray.Count == 4) // Color with alpha
                        {
                            Color color = new Color(
                                jArray[0].ToObject<float>(),
                                jArray[1].ToObject<float>(),
                                jArray[2].ToObject<float>(),
                                jArray[3].ToObject<float>()
                            );
                            material.SetColor(finalPart, color);
                            return true;
                        }
                        else if (jArray.Count == 3) // Color without alpha
                        {
                            Color color = new Color(
                                jArray[0].ToObject<float>(),
                                jArray[1].ToObject<float>(),
                                jArray[2].ToObject<float>(),
                                1.0f
                            );
                            material.SetColor(finalPart, color);
                            return true;
                        }
                        else if (jArray.Count == 2) // Vector2
                        {
                            Vector2 vec = new Vector2(
                                jArray[0].ToObject<float>(),
                                jArray[1].ToObject<float>()
                            );
                            material.SetVector(finalPart, vec);
                            return true;
                        }
                        else if (jArray.Count == 4) // Vector4
                        {
                            Vector4 vec = new Vector4(
                                jArray[0].ToObject<float>(),
                                jArray[1].ToObject<float>(),
                                jArray[2].ToObject<float>(),
                                jArray[3].ToObject<float>()
                            );
                            material.SetVector(finalPart, vec);
                            return true;
                        }
                    }
                    else if (value.Type == JTokenType.Float || value.Type == JTokenType.Integer)
                    {
                        material.SetFloat(finalPart, value.ToObject<float>());
                        return true;
                    }
                    else if (value.Type == JTokenType.Boolean)
                    {
                        material.SetFloat(finalPart, value.ToObject<bool>() ? 1f : 0f);
                        return true;
                    }
                    else if (value.Type == JTokenType.String)
                    {
                        // Might be a texture path
                        string texturePath = value.ToString();
                        if (texturePath.EndsWith(".png") || texturePath.EndsWith(".jpg") || texturePath.EndsWith(".tga"))
                        {
                            Texture2D texture = AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
                            if (texture != null)
                            {
                                material.SetTexture(finalPart, texture);
                                return true;
                            }
                        }
                        else
                        {
                            // Materials don't have SetString, use SetTextureOffset as workaround or skip
                            Debug.LogWarning($"[SetNestedProperty] String values not directly supported for material property {finalPart}");
                            return false;
                        }
                    }

                    Debug.LogWarning($"[SetNestedProperty] Unsupported material property value type: {value.Type} for {finalPart}");
                    return false;
                }

                // For standard properties (not shader specific)
                PropertyInfo finalPropInfo = currentType.GetProperty(finalPart, flags);
                if (finalPropInfo != null && finalPropInfo.CanWrite)
                {
                    object convertedValue = ConvertJTokenToType(value, finalPropInfo.PropertyType);
                    if (convertedValue != null)
                    {
                        finalPropInfo.SetValue(currentObject, convertedValue);
                        return true;
                    }
                }
                else
                {
                    FieldInfo finalFieldInfo = currentType.GetField(finalPart, flags);
                    if (finalFieldInfo != null)
                    {
                        object convertedValue = ConvertJTokenToType(value, finalFieldInfo.FieldType);
                        if (convertedValue != null)
                        {
                            finalFieldInfo.SetValue(currentObject, convertedValue);
                            return true;
                        }
                    }
                    else
                    {
                        Debug.LogWarning($"[SetNestedProperty] Could not find final property or field '{finalPart}' on type '{currentType.Name}'");
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.LogError($"[SetNestedProperty] Error setting nested property '{path}': {ex.Message}");
            }

            return false;
        }

        /// <summary>
        /// Split a property path into parts, handling both dot notation and array indexers
        /// </summary>
        public static string[] SplitPropertyPath(string path)
        {
            // Handle complex paths with both dots and array indexers
            List<string> parts = new List<string>();
            int startIndex = 0;
            bool inBrackets = false;

            for (int i = 0; i < path.Length; i++)
            {
                char c = path[i];

                if (c == '[')
                {
                    inBrackets = true;
                }
                else if (c == ']')
                {
                    inBrackets = false;
                }
                else if (c == '.' && !inBrackets)
                {
                    // Found a dot separator outside of brackets
                    parts.Add(path.Substring(startIndex, i - startIndex));
                    startIndex = i + 1;
                }
            }

            // Add the final part
            if (startIndex < path.Length)
            {
                parts.Add(path.Substring(startIndex));
            }

            return parts.ToArray();
        }

        /// <summary>
        /// Simple JToken to Type conversion for common Unity types.
        /// </summary>
        public static object ConvertJTokenToType(JToken token, Type targetType)
        {
            try
            {
                // Unwrap nested material properties if we're assigning to a Material
                if (typeof(Material).IsAssignableFrom(targetType) && token is JObject materialProps)
                {
                    // Handle case where we're passing shader properties directly in a nested object
                    string materialPath = materialProps["path"]?.ToString();
                    if (!string.IsNullOrEmpty(materialPath))
                    {
                        // Load the material by path
                        Material material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
                        if (material != null)
                        {
                            // If there are additional properties, set them
                            foreach (var prop in materialProps.Properties())
                            {
                                if (prop.Name != "path")
                                {
                                    SetProperty(material, prop.Name, prop.Value);
                                }
                            }
                            return material;
                        }
                        else
                        {
                            Debug.LogWarning($"[ConvertJTokenToType] Could not load material at path: '{materialPath}'");
                            return null;
                        }
                    }

                    // If no path is specified, could be a dynamic material or instance set by reference
                    return null;
                }

                // Basic types first
                if (targetType == typeof(string))
                    return token.ToObject<string>();
                if (targetType == typeof(int))
                    return token.ToObject<int>();
                if (targetType == typeof(float))
                    return token.ToObject<float>();
                if (targetType == typeof(bool))
                    return token.ToObject<bool>();

                // Replace direct Vector/Quaternion/Color conversions with UnityTypeHelper methods
                if (targetType == typeof(Vector2))
                    return UnityTypeHelper.ParseVector2(token);
                if (targetType == typeof(Vector3))
                    return UnityTypeHelper.ParseVector3(token);
                if (targetType == typeof(Vector4))
                    return UnityTypeHelper.ParseVector4(token);
                if (targetType == typeof(Quaternion))
                    return UnityTypeHelper.ParseQuaternion(token);
                if (targetType == typeof(Color))
                    return UnityTypeHelper.ParseColor(token);
                if (targetType == typeof(Rect))
                    return UnityTypeHelper.ParseRect(token);
                if (targetType == typeof(Bounds))
                    return UnityTypeHelper.ParseBounds(token);

                // Enum types
                if (targetType.IsEnum)
                    return Enum.Parse(targetType, token.ToString(), true); // Case-insensitive enum parsing

                // Handle assigning Unity Objects (Assets, Scene Objects, Components)
                if (typeof(UnityEngine.Object).IsAssignableFrom(targetType))
                {
                    // CASE 1: Reference is a JSON Object specifying a scene object/component find criteria
                    if (token is JObject refObject)
                    {
                        JToken findToken = refObject["find"];
                        string findMethod = refObject["method"]?.ToString() ?? "by_id_or_name_or_path"; // Default search
                        string componentTypeName = refObject["component"]?.ToString();

                        if (findToken == null)
                        {
                            Debug.LogWarning($"[ConvertJTokenToType] Reference object missing 'find' property: {token}");
                            return null;
                        }

                        // Find the target GameObject
                        // Pass 'search_inactive: true' for internal lookups to be more robust
                        JObject findParams = new JObject
                        {
                            ["search_inactive"] = true
                        };
                        
                        // Use GameObjectFinder to find the object
                        GameObject foundGo = GameObjectFinder.FindSingleObject(findToken, findMethod, findParams);

                        if (foundGo == null)
                        {
                            Debug.LogWarning($"[ConvertJTokenToType] Could not find GameObject specified by reference object: {token}");
                            return null;
                        }

                        // If a component type is specified, try to get it
                        if (!string.IsNullOrEmpty(componentTypeName))
                        {
                            Type compType = FindType(componentTypeName);
                            if (compType == null)
                            {
                                Debug.LogWarning($"[ConvertJTokenToType] Could not find component type '{componentTypeName}' specified in reference object: {token}");
                                return null;
                            }

                            // Ensure the targetType is assignable from the found component type
                            if (!targetType.IsAssignableFrom(compType))
                            {
                                Debug.LogWarning($"[ConvertJTokenToType] Found component '{componentTypeName}' but it is not assignable to the target property type '{targetType.Name}'. Reference: {token}");
                                return null;
                            }

                            Component foundComp = foundGo.GetComponent(compType);
                            if (foundComp == null)
                            {
                                Debug.LogWarning($"[ConvertJTokenToType] Found GameObject '{foundGo.name}' but could not find component '{componentTypeName}' on it. Reference: {token}");
                                return null;
                            }
                            return foundComp; // Return the found component
                        }
                        else
                        {
                            // Otherwise, return the GameObject itself, ensuring it's assignable
                            if (!targetType.IsAssignableFrom(typeof(GameObject)))
                            {
                                Debug.LogWarning($"[ConvertJTokenToType] Found GameObject '{foundGo.name}' but it is not assignable to the target property type '{targetType.Name}' (component name was not specified). Reference: {token}");
                                return null;
                            }
                            return foundGo; // Return the found GameObject
                        }
                    }
                    // CASE 2: Reference is a string, assume it's an asset path
                    else if (token.Type == JTokenType.String)
                    {
                        string assetPath = token.ToString();
                        if (!string.IsNullOrEmpty(assetPath))
                        {
                            // Attempt to load the asset from the provided path using the target type
                            UnityEngine.Object loadedAsset = AssetDatabase.LoadAssetAtPath(assetPath, targetType);
                            if (loadedAsset != null)
                            {
                                return loadedAsset; // Return the loaded asset if successful
                            }
                            else
                            {
                                // Log a warning if the asset could not be found at the path
                                Debug.LogWarning($"[ConvertJTokenToType] Could not load asset of type '{targetType.Name}' from path: '{assetPath}'. Make sure the path is correct and the asset exists.");
                                return null;
                            }
                        }
                        else
                        {
                            // Handle cases where an empty string might be intended to clear the reference
                            return null; // Assign null if the path is empty
                        }
                    }
                    // CASE 3: Reference is null or empty JToken, assign null
                    else if (token.Type == JTokenType.Null || string.IsNullOrEmpty(token.ToString()))
                    {
                        return null;
                    }
                    // CASE 4: Invalid format for Unity Object reference
                    else
                    {
                        Debug.LogWarning($"[ConvertJTokenToType] Expected a string asset path or a reference object to assign Unity Object of type '{targetType.Name}', but received token type '{token.Type}'. Value: {token}");
                        return null;
                    }
                }

                // Fallback: Try direct conversion (might work for other simple value types)
                // Be cautious here, this might throw errors for complex types not handled above
                try
                {
                    return token.ToObject(targetType);
                }
                catch (Exception directConversionEx)
                {
                    Debug.LogWarning($"[ConvertJTokenToType] Direct conversion failed for JToken '{token}' to type '{targetType.Name}': {directConversionEx.Message}. Specific handling might be needed.");
                    return null;
                }
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"[ConvertJTokenToType] Could not convert JToken '{token}' to type '{targetType.Name}': {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Helper to find a Type by name, searching relevant assemblies.
        /// </summary>
        public static Type FindType(string typeName)
        {
            if (string.IsNullOrEmpty(typeName))
                return null;

            // Handle common Unity namespaces implicitly
            var type = Type.GetType($"UnityEngine.{typeName}, UnityEngine.CoreModule")
                ?? Type.GetType($"UnityEngine.{typeName}, UnityEngine.PhysicsModule") // Example physics
                ?? Type.GetType($"UnityEngine.UI.{typeName}, UnityEngine.UI") // Example UI
                ?? Type.GetType($"UnityEditor.{typeName}, UnityEditor.CoreModule")
                ?? Type.GetType(typeName); // Try direct name (if fully qualified or in mscorlib)

            if (type != null)
                return type;

            // If not found, search all loaded assemblies (slower)
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                type = assembly.GetType(typeName);
                if (type != null)
                    return type;
                // Also check with namespaces if simple name given
                type = assembly.GetType("UnityEngine." + typeName);
                if (type != null)
                    return type;
                type = assembly.GetType("UnityEditor." + typeName);
                if (type != null)
                    return type;
                type = assembly.GetType("UnityEngine.UI." + typeName);
                if (type != null)
                    return type;
            }

            return null; // Not found
        }

        /// <summary>
        /// Parses a JArray like [x, y, z] into a Vector3.
        /// </summary>
        public static Vector3? ParseVector3(JArray array)
        {
            if (array != null)
            {
                try
                {
                    Debug.Log($"[MCP-DEBUG] ParseVector3 input array: {array}");
                    // Use UnityTypeHelper.ParseVector3 instead of direct parsing
                    Vector3 result = UnityTypeHelper.ParseVector3(array);
                    Debug.Log($"[MCP-DEBUG] ParseVector3 result: {result}");
                    return result;
                }
                catch (Exception e)
                {
                    Debug.LogError($"[MCP-DEBUG] ParseVector3 error: {e.Message}");
                    /* Ignore parsing errors */
                }
            }
            else
            {
                Debug.LogWarning("[MCP-DEBUG] ParseVector3 received null array");
            }
            return null;
        }
    }
} 