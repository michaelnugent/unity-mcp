using System;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditorInternal;
using UnityEngine;
using UnityMcpBridge.Editor.Helpers;
using UnityMcpBridge.Editor.Tools.ManageGameObjectImpl.Models;

namespace UnityMcpBridge.Editor.Tools.ManageGameObjectImpl
{
    /// <summary>
    /// Handles creation of GameObjects in the scene.
    /// Part of the ManageGameObject tool's internal implementation.
    /// </summary>
    internal static class GameObjectCreator
    {
        /// <summary>
        /// Creates a new GameObject based on the provided parameters
        /// </summary>
        public static object CreateGameObject(JObject @params)
        {
            GameObjectParams goParams = GameObjectParams.FromJObject(@params);
            string name = goParams.Name;
            
            if (string.IsNullOrEmpty(name))
            {
                return Response.Error("'name' parameter is required for 'create' action.");
            }

            // Get prefab creation parameters
            bool saveAsPrefab = @params["save_as_prefab"]?.ToObject<bool>() ?? false;
            string prefabPath = @params["prefab_path"]?.ToString();
            string tag = goParams.Tag; // Get tag for creation
            string primitiveType = @params["primitive_type"]?.ToString(); // Keep primitiveType check
            GameObject newGo = null; // Initialize as null

            // --- Try Instantiating Prefab First ---
            string originalPrefabPath = prefabPath; // Keep original for messages
            if (!string.IsNullOrEmpty(prefabPath))
            {
                // If no extension, search for the prefab by name
                if (
                    !prefabPath.Contains("/")
                    && !prefabPath.EndsWith(".prefab", StringComparison.OrdinalIgnoreCase)
                )
                {
                    string prefabNameOnly = prefabPath;
                    Debug.Log(
                        $"[ManageGameObject.Create] Searching for prefab named: '{prefabNameOnly}'"
                    );
                    string[] guids = AssetDatabase.FindAssets($"t:Prefab {prefabNameOnly}");
                    if (guids.Length == 0)
                    {
                        return Response.Error(
                            $"Prefab named '{prefabNameOnly}' not found anywhere in the project."
                        );
                    }
                    else if (guids.Length > 1)
                    {
                        string foundPaths = string.Join(
                            ", ",
                            guids.Select(g => AssetDatabase.GUIDToAssetPath(g))
                        );
                        return Response.Error(
                            $"Multiple prefabs found matching name '{prefabNameOnly}': {foundPaths}. Please provide a more specific path."
                        );
                    }
                    else // Exactly one found
                    {
                        prefabPath = AssetDatabase.GUIDToAssetPath(guids[0]); // Update prefabPath with the full path
                        Debug.Log(
                            $"[ManageGameObject.Create] Found unique prefab at path: '{prefabPath}'"
                        );
                    }
                }
                else if (!prefabPath.EndsWith(".prefab", StringComparison.OrdinalIgnoreCase))
                {
                    // If it looks like a path but doesn't end with .prefab, assume user forgot it and append it.
                    Debug.LogWarning(
                        $"[ManageGameObject.Create] Provided prefabPath '{prefabPath}' does not end with .prefab. Assuming it's missing and appending."
                    );
                    prefabPath += ".prefab";
                }

                GameObject prefabAsset = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
                if (prefabAsset != null)
                {
                    try
                    {
                        // Instantiate the prefab, initially place it at the root
                        // Parent will be set later if specified
                        newGo = PrefabUtility.InstantiatePrefab(prefabAsset) as GameObject;

                        if (newGo == null)
                        {
                            // This might happen if the asset exists but isn't a valid GameObject prefab somehow
                            Debug.LogError(
                                $"[ManageGameObject.Create] Failed to instantiate prefab at '{prefabPath}', asset might be corrupted or not a GameObject."
                            );
                            return Response.Error(
                                $"Failed to instantiate prefab at '{prefabPath}'."
                            );
                        }

                        // Name the instance based on the 'name' parameter, not the prefab's default name
                        if (!string.IsNullOrEmpty(name))
                        {
                            newGo.name = name;
                        }

                        // Register Undo for prefab instantiation
                        Undo.RegisterCreatedObjectUndo(
                            newGo,
                            $"Instantiate Prefab '{prefabAsset.name}' as '{newGo.name}'"
                        );
                        Debug.Log(
                            $"[ManageGameObject.Create] Instantiated prefab '{prefabAsset.name}' from path '{prefabPath}' as '{newGo.name}'."
                        );
                    }
                    catch (Exception e)
                    {
                        return Response.Error(
                            $"Error instantiating prefab '{prefabPath}': {e.Message}"
                        );
                    }
                }
                else
                {
                    // Only return error if prefabPath was specified but not found.
                    // If prefabPath was empty/null, we proceed to create primitive/empty.
                    Debug.LogWarning(
                        $"[ManageGameObject.Create] Prefab asset not found at path: '{prefabPath}'. Will proceed to create new object if specified."
                    );
                    // Do not return error here, allow fallback to primitive/empty creation
                }
            }

            // --- Fallback: Create Primitive or Empty GameObject ---
            bool createdNewObject = false; // Flag to track if we created (not instantiated)
            if (newGo == null) // Only proceed if prefab instantiation didn't happen
            {
                if (!string.IsNullOrEmpty(primitiveType))
                {
                    try
                    {
                        PrimitiveType type = (PrimitiveType)
                            Enum.Parse(typeof(PrimitiveType), primitiveType, true);
                        newGo = GameObject.CreatePrimitive(type);
                        // Set name *after* creation for primitives
                        if (!string.IsNullOrEmpty(name))
                            newGo.name = name;
                        else
                            return Response.Error(
                                "'name' parameter is required when creating a primitive."
                            ); // Name is essential
                        createdNewObject = true;
                    }
                    catch (ArgumentException)
                    {
                        return Response.Error(
                            $"Invalid primitive type: '{primitiveType}'. Valid types: {string.Join(", ", Enum.GetNames(typeof(PrimitiveType)))}"
                        );
                    }
                    catch (Exception e)
                    {
                        return Response.Error(
                            $"Failed to create primitive '{primitiveType}': {e.Message}"
                        );
                    }
                }
                else // Create empty GameObject
                {
                    if (string.IsNullOrEmpty(name))
                    {
                        return Response.Error(
                            "'name' parameter is required for 'create' action when not instantiating a prefab or creating a primitive."
                        );
                    }
                    newGo = new GameObject(name);
                    createdNewObject = true;
                }

                // Record creation for Undo *only* if we created a new object
                if (createdNewObject)
                {
                    Undo.RegisterCreatedObjectUndo(newGo, $"Create GameObject '{newGo.name}'");
                }
            }

            // --- Common Setup (Parent, Transform, Tag, Components) - Applied AFTER object exists ---
            if (newGo == null)
            {
                // Should theoretically not happen if logic above is correct, but safety check.
                return Response.Error("Failed to create or instantiate the GameObject.");
            }

            // Record potential changes to the existing prefab instance or the new GO
            // Record transform separately in case parent changes affect it
            Undo.RecordObject(newGo.transform, "Set GameObject Transform");
            Undo.RecordObject(newGo, "Set GameObject Properties");

            // Set Parent
            JToken parentToken = goParams.ParentToken;
            if (parentToken != null)
            {
                GameObject parentGo = GameObjectFinder.FindSingleObject(parentToken, "by_id_or_name_or_path"); // Flexible parent finding
                if (parentGo == null)
                {
                    UnityEngine.Object.DestroyImmediate(newGo); // Clean up created object
                    return Response.Error($"Parent specified ('{parentToken}') but not found.");
                }
                newGo.transform.SetParent(parentGo.transform, true); // worldPositionStays = true
            }

            // Set Transform
            Vector3? position = PropertyUtils.ParseVector3(goParams.Position);
            Vector3? rotation = PropertyUtils.ParseVector3(goParams.Rotation);
            Vector3? scale = PropertyUtils.ParseVector3(goParams.Scale);

            // Always set transform values if they're provided
            if (position.HasValue)
            {
                Debug.Log($"[MCP-DEBUG] Setting new GameObject position to {position.Value}");
                newGo.transform.localPosition = position.Value;
            }
            if (rotation.HasValue)
            {
                Debug.Log($"[MCP-DEBUG] Setting new GameObject rotation to {rotation.Value}");
                newGo.transform.localEulerAngles = rotation.Value;
            }
            if (scale.HasValue)
            {
                Debug.Log($"[MCP-DEBUG] Setting new GameObject scale to {scale.Value}");
                newGo.transform.localScale = scale.Value;
            }

            // Set Tag (added for create action)
            if (!string.IsNullOrEmpty(tag))
            {
                // Similar logic as in ModifyGameObject for setting/creating tags
                string tagToSet = string.IsNullOrEmpty(tag) ? "Untagged" : tag;
                try
                {
                    newGo.tag = tagToSet;
                }
                catch (UnityException ex)
                {
                    if (ex.Message.Contains("is not defined"))
                    {
                        Debug.LogWarning(
                            $"[ManageGameObject.Create] Tag '{tagToSet}' not found. Attempting to create it."
                        );
                        try
                        {
                            InternalEditorUtility.AddTag(tagToSet);
                            newGo.tag = tagToSet; // Retry
                            Debug.Log(
                                $"[ManageGameObject.Create] Tag '{tagToSet}' created and assigned successfully."
                            );
                        }
                        catch (Exception innerEx)
                        {
                            UnityEngine.Object.DestroyImmediate(newGo); // Clean up
                            return Response.Error(
                                $"Failed to create or assign tag '{tagToSet}' during creation: {innerEx.Message}."
                            );
                        }
                    }
                    else
                    {
                        UnityEngine.Object.DestroyImmediate(newGo); // Clean up
                        return Response.Error(
                            $"Failed to set tag to '{tagToSet}' during creation: {ex.Message}."
                        );
                    }
                }
            }

            // Set Layer (new for create action)
            string layerName = goParams.Layer;
            if (!string.IsNullOrEmpty(layerName))
            {
                int layerId = LayerMask.NameToLayer(layerName);
                if (layerId != -1)
                {
                    newGo.layer = layerId;
                }
                else
                {
                    Debug.LogWarning(
                        $"[ManageGameObject.Create] Layer '{layerName}' not found. Using default layer."
                    );
                }
            }

            // Add Components
            ComponentParams componentParams = ComponentParams.FromJObject(@params);
            if (componentParams.ComponentsToAdd != null)
            {
                foreach (var compToken in componentParams.ComponentsToAdd)
                {
                    string typeName = null;
                    JObject properties = null;

                    if (compToken.Type == JTokenType.String)
                    {
                        typeName = compToken.ToString();
                    }
                    else if (compToken is JObject compObj)
                    {
                        typeName = compObj["type_name"]?.ToString();
                        properties = compObj["properties"] as JObject;
                    }

                    if (!string.IsNullOrEmpty(typeName))
                    {
                        var addResult = ComponentManager.AddComponentInternal(newGo, typeName, properties);
                        if (addResult != null) // Check if AddComponentInternal returned an error object
                        {
                            UnityEngine.Object.DestroyImmediate(newGo); // Clean up
                            return addResult; // Return the error response
                        }
                    }
                    else
                    {
                        Debug.LogWarning(
                            $"[ManageGameObject] Invalid component format in components_to_add: {compToken}"
                        );
                    }
                }
            }

            // Save as Prefab ONLY if we *created* a new object AND saveAsPrefab is true
            GameObject finalInstance = newGo; // Use this for selection and return data
            if (createdNewObject && saveAsPrefab)
            {
                string finalPrefabPath = prefabPath; // Use a separate variable for saving path
                // This check should now happen *before* attempting to save
                if (string.IsNullOrEmpty(finalPrefabPath))
                {
                    // Clean up the created object before returning error
                    UnityEngine.Object.DestroyImmediate(newGo);
                    return Response.Error(
                        "'prefab_path' is required when 'save_as_prefab' is true and creating a new object."
                    );
                }
                // Ensure the *saving* path ends with .prefab
                if (!finalPrefabPath.EndsWith(".prefab", StringComparison.OrdinalIgnoreCase))
                {
                    Debug.Log(
                        $"[ManageGameObject.Create] Appending .prefab extension to save path: '{finalPrefabPath}' -> '{finalPrefabPath}.prefab'"
                    );
                    finalPrefabPath += ".prefab";
                }

                try
                {
                    // Ensure directory exists using the final saving path
                    string directoryPath = Path.GetDirectoryName(finalPrefabPath);
                    if (
                        !string.IsNullOrEmpty(directoryPath)
                        && !Directory.Exists(directoryPath)
                    )
                    {
                        Directory.CreateDirectory(directoryPath);
                        AssetDatabase.Refresh(); // Refresh asset database to recognize the new folder
                        Debug.Log(
                            $"[ManageGameObject.Create] Created directory for prefab: {directoryPath}"
                        );
                    }

                    // Use SaveAsPrefabAssetAndConnect with the final saving path
                    finalInstance = PrefabUtility.SaveAsPrefabAssetAndConnect(
                        newGo,
                        finalPrefabPath,
                        InteractionMode.UserAction
                    );

                    if (finalInstance == null)
                    {
                        // Destroy the original if saving failed somehow (shouldn't usually happen if path is valid)
                        UnityEngine.Object.DestroyImmediate(newGo);
                        return Response.Error(
                            $"Failed to save GameObject '{name}' as prefab at '{finalPrefabPath}'. Check path and permissions."
                        );
                    }
                    Debug.Log(
                        $"[ManageGameObject.Create] GameObject '{name}' saved as prefab to '{finalPrefabPath}' and instance connected."
                    );
                }
                catch (Exception e)
                {
                    // Clean up the instance if prefab saving fails
                    UnityEngine.Object.DestroyImmediate(newGo); // Destroy the original attempt
                    return Response.Error($"Error saving prefab '{finalPrefabPath}': {e.Message}");
                }
            }

            // Select the instance in the scene (either prefab instance or newly created/saved one)
            Selection.activeGameObject = finalInstance;

            // Determine appropriate success message
            string messagePrefabPath =
                finalInstance == null
                    ? originalPrefabPath
                    : AssetDatabase.GetAssetPath(
                        PrefabUtility.GetCorrespondingObjectFromSource(finalInstance)
                            ?? (UnityEngine.Object)finalInstance
                    );
            string successMessage;
            if (!createdNewObject && !string.IsNullOrEmpty(messagePrefabPath)) // Instantiated existing prefab
            {
                successMessage =
                    $"Prefab '{messagePrefabPath}' instantiated successfully as '{finalInstance.name}'.";
            }
            else if (createdNewObject && saveAsPrefab && !string.IsNullOrEmpty(messagePrefabPath)) // Created new and saved as prefab
            {
                successMessage =
                    $"GameObject '{finalInstance.name}' created and saved as prefab to '{messagePrefabPath}'.";
            }
            else // Created new primitive or empty GO, didn't save as prefab
            {
                successMessage =
                    $"GameObject '{finalInstance.name}' created successfully in scene.";
            }

            // Return data for the instance in the scene
            return Response.Success(successMessage, GameObjectSerializer.GetGameObjectData(finalInstance));
        }
    }
} 