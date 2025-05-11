using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditorInternal;
using UnityEngine;
using UnityMcpBridge.Editor.Helpers;
using UnityMcpBridge.Editor.Tools.ManageGameObjectImpl.Models;

namespace UnityMcpBridge.Editor.Tools.ManageGameObjectImpl
{
    /// <summary>
    /// Handles modification of existing GameObjects in the scene.
    /// Part of the ManageGameObject tool's internal implementation.
    /// </summary>
    internal static class GameObjectModifier
    {
        /// <summary>
        /// Modifies an existing GameObject based on the provided parameters
        /// </summary>
        public static object ModifyGameObject(JObject @params)
        {
            GameObjectParams goParams = GameObjectParams.FromJObject(@params);
            JToken targetToken = goParams.TargetToken;
            
            if (targetToken == null)
            {
                return Response.Error("'target' parameter is required for modify action.");
            }

            // Find the target
            GameObject targetObj = GameObjectFinder.FindSingleObject(targetToken, "by_id_or_name_or_path");
            if (targetObj == null)
            {
                return Response.Error($"Target GameObject '{targetToken}' not found.");
            }

            Debug.Log($"[ManageGameObject.Modify] Found target: {targetObj.name}");

            // Record for Undo (GameObject and Transform separately)
            Undo.RecordObject(targetObj, $"Modify GameObject '{targetObj.name}'");
            Undo.RecordObject(targetObj.transform, $"Modify Transform of '{targetObj.name}'");

            // --- Set properties on the object ---
            bool hasChanges = false;
            string errorMessage = null;

            // Set Name
            if (!string.IsNullOrEmpty(goParams.Name) && targetObj.name != goParams.Name)
            {
                targetObj.name = goParams.Name;
                hasChanges = true;
                Debug.Log($"[ManageGameObject.Modify] Set name to '{goParams.Name}'");
            }

            // Set Tag
            string tag = goParams.Tag;
            if (!string.IsNullOrEmpty(tag) && targetObj.tag != tag)
            {
                // First check if the tag exists, if not, create it
                string tagToSet = string.IsNullOrEmpty(tag) ? "Untagged" : tag;
                try
                {
                    targetObj.tag = tagToSet;
                    hasChanges = true;
                    Debug.Log($"[ManageGameObject.Modify] Set tag to '{tagToSet}'");
                }
                catch (UnityException ex)
                {
                    if (ex.Message.Contains("is not defined"))
                    {
                        Debug.LogWarning($"[ManageGameObject.Modify] Tag '{tagToSet}' not found. Attempting to create it.");
                        try
                        {
                            InternalEditorUtility.AddTag(tagToSet);
                            targetObj.tag = tagToSet; // Retry
                            hasChanges = true;
                            Debug.Log($"[ManageGameObject.Modify] Tag '{tagToSet}' created and assigned successfully.");
                        }
                        catch (Exception tagEx)
                        {
                            errorMessage = $"Failed to create or assign tag '{tagToSet}': {tagEx.Message}.";
                            Debug.LogError($"[ManageGameObject.Modify] {errorMessage}");
                        }
                    }
                    else
                    {
                        errorMessage = $"Failed to set tag to '{tagToSet}': {ex.Message}.";
                        Debug.LogError($"[ManageGameObject.Modify] {errorMessage}");
                    }
                }
            }

            // Set Layer
            string layerName = goParams.Layer;
            if (!string.IsNullOrEmpty(layerName))
            {
                int layerId = LayerMask.NameToLayer(layerName);
                if (layerId != -1 && targetObj.layer != layerId)
                {
                    targetObj.layer = layerId;
                    hasChanges = true;
                    Debug.Log($"[ManageGameObject.Modify] Set layer to '{layerName}' (ID: {layerId})");
                }
                else if (layerId == -1)
                {
                    Debug.LogWarning($"[ManageGameObject.Modify] Layer '{layerName}' not found. Layer not changed.");
                }
            }

            // Set Parent - only if specifically requesting a parent change
            JToken parentToken = goParams.ParentToken;
            if (parentToken != null)
            {
                // Special case: null or "null" means set to scene root
                if (parentToken.Type == JTokenType.Null || 
                    (parentToken.Type == JTokenType.String && (string)parentToken == "null"))
                {
                    if (targetObj.transform.parent != null)
                    {
                        targetObj.transform.SetParent(null, true); // Keep world position
                        hasChanges = true;
                        Debug.Log($"[ManageGameObject.Modify] Set parent to scene root");
                    }
                }
                else
                {
                    GameObject parentObj = GameObjectFinder.FindSingleObject(parentToken, "by_id_or_name_or_path");
                    if (parentObj != null)
                    {
                        // Ensure we're not parenting to itself or a child of itself
                        if (parentObj == targetObj)
                        {
                            Debug.LogError("[ManageGameObject.Modify] Cannot parent an object to itself.");
                            errorMessage = "Cannot parent an object to itself.";
                        }
                        else if (IsChildOf(parentObj.transform, targetObj.transform))
                        {
                            Debug.LogError("[ManageGameObject.Modify] Cannot parent an object to its own descendant.");
                            errorMessage = "Cannot parent an object to its own descendant.";
                        }
                        else if (targetObj.transform.parent != parentObj.transform)
                        {
                            targetObj.transform.SetParent(parentObj.transform, true); // Keep world position
                            hasChanges = true;
                            Debug.Log($"[ManageGameObject.Modify] Set parent to '{parentObj.name}'");
                        }
                    }
                    else
                    {
                        Debug.LogError($"[ManageGameObject.Modify] Parent '{parentToken}' not found, cannot reparent.");
                        errorMessage = $"Parent '{parentToken}' not found, cannot reparent.";
                    }
                }
            }

            // Set Transform Properties
            Vector3? position = PropertyUtils.ParseVector3(goParams.Position);
            Vector3? rotation = PropertyUtils.ParseVector3(goParams.Rotation);
            Vector3? scale = PropertyUtils.ParseVector3(goParams.Scale);

            if (position.HasValue)
            {
                targetObj.transform.localPosition = position.Value;
                hasChanges = true;
                Debug.Log($"[ManageGameObject.Modify] Set position to {position.Value}");
            }

            if (rotation.HasValue)
            {
                targetObj.transform.localEulerAngles = rotation.Value;
                hasChanges = true;
                Debug.Log($"[ManageGameObject.Modify] Set rotation to {rotation.Value}");
            }

            if (scale.HasValue)
            {
                targetObj.transform.localScale = scale.Value;
                hasChanges = true;
                Debug.Log($"[ManageGameObject.Modify] Set scale to {scale.Value}");
            }

            // Set active state only if explicitly specified
            bool? isActive = goParams.IsActive;
            if (isActive.HasValue && targetObj.activeSelf != isActive.Value)
            {
                targetObj.SetActive(isActive.Value);
                hasChanges = true;
                Debug.Log($"[ManageGameObject.Modify] Set active state to {isActive.Value}");
            }

            // Set static state only if explicitly specified
            bool? isStatic = goParams.IsStatic;
            if (isStatic.HasValue && targetObj.isStatic != isStatic.Value)
            {
                targetObj.isStatic = isStatic.Value;
                hasChanges = true;
                Debug.Log($"[ManageGameObject.Modify] Set static state to {isStatic.Value}");
            }

            // Process component operations
            ComponentParams componentParams = ComponentParams.FromJObject(@params);
            
            // Get target components
            JToken componentTargetToken = componentParams.ComponentTarget;
            List<Component> targetComponents = new List<Component>();
            
            if (componentTargetToken != null)
            {
                // Handle component_target param and process properties
                var compResult = GetTargetComponents(targetObj, componentTargetToken);
                if (compResult.Item1 != null) // Error
                {
                    return compResult.Item1;
                }
                else
                {
                    targetComponents = compResult.Item2;
                    
                    // Apply properties to target components if specified
                    JObject properties = componentParams.Properties;
                    if (properties != null && properties.Count > 0 && targetComponents.Count > 0)
                    {
                        foreach (Component component in targetComponents)
                        {
                            // Record component for Undo
                            Undo.RecordObject(component, $"Modify Component '{component.GetType().Name}' on '{targetObj.name}'");
                            
                            foreach (var prop in properties)
                            {
                                string propName = prop.Key;
                                JToken valueToken = prop.Value;

                                try
                                {
                                    PropertyUtils.SetProperty(component, propName, valueToken);
                                    hasChanges = true;
                                }
                                catch (Exception ex)
                                {
                                    string errorDetail = $"Error setting property '{propName}' on component '{component.GetType().Name}': {ex.Message}";
                                    Debug.LogError($"[ManageGameObject.Modify] {errorDetail}");
                                    
                                    if (errorMessage == null)
                                    {
                                        errorMessage = errorDetail;
                                    }
                                }
                            }
                        }
                        
                        if (targetComponents.Count > 0)
                        {
                            Debug.Log($"[ManageGameObject.Modify] Set properties on {targetComponents.Count} components of type '{targetComponents[0].GetType().Name}'");
                        }
                    }
                }
            }

            // Add components if specified
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
                        var addResult = ComponentManager.AddComponentInternal(targetObj, typeName, properties);
                        if (addResult != null) // Error object
                        {
                            return addResult;
                        }
                        hasChanges = true;
                    }
                }
            }

            // Remove components if specified
            if (componentParams.ComponentsToRemove != null)
            {
                foreach (var compToken in componentParams.ComponentsToRemove)
                {
                    string typeName = null;
                    
                    if (compToken.Type == JTokenType.String)
                    {
                        typeName = compToken.ToString();
                    }
                    else if (compToken is JObject compObj)
                    {
                        typeName = compObj["type_name"]?.ToString();
                    }

                    if (!string.IsNullOrEmpty(typeName))
                    {
                        var removeResult = ComponentManager.RemoveComponentInternal(targetObj, typeName);
                        if (removeResult != null) // Error object
                        {
                            return removeResult;
                        }
                        hasChanges = true;
                    }
                }
            }

            // Select the object
            Selection.activeGameObject = targetObj;

            // Generate response
            if (!hasChanges && errorMessage == null)
            {
                return Response.Warning("No changes were made to the GameObject.", GameObjectSerializer.GetGameObjectData(targetObj));
            }
            else if (errorMessage != null)
            {
                if (hasChanges)
                {
                    return Response.Warning($"Some changes were applied but with errors: {errorMessage}", GameObjectSerializer.GetGameObjectData(targetObj));
                }
                else
                {
                    return Response.Error(errorMessage);
                }
            }
            else
            {
                EditorUtility.SetDirty(targetObj);
                if (targetComponents.Count > 0)
                {
                    foreach (var comp in targetComponents)
                    {
                        EditorUtility.SetDirty(comp);
                    }
                }
                
                return Response.Success($"Successfully modified GameObject '{targetObj.name}'.", GameObjectSerializer.GetGameObjectData(targetObj));
            }
        }

        /// <summary>
        /// Gets the target components from a GameObject based on the provided component target parameter.
        /// </summary>
        /// <returns>Tuple containing error response (if any) and list of components</returns>
        private static Tuple<object, List<Component>> GetTargetComponents(GameObject targetObj, JToken componentTargetToken)
        {
            List<Component> targetComponents = new List<Component>();
            
            if (componentTargetToken == null)
            {
                return Tuple.Create<object, List<Component>>(null, targetComponents);
            }

            if (componentTargetToken.Type == JTokenType.String)
            {
                string componentTypeName = componentTargetToken.ToString();
                Type componentType = ComponentManager.GetComponentType(componentTypeName);

                if (componentType == null)
                {
                    return Tuple.Create<object, List<Component>>(
                        Response.Error($"Component type '{componentTypeName}' not found."), 
                        new List<Component>()
                    );
                }

                Component component = targetObj.GetComponent(componentType);
                if (component == null)
                {
                    return Tuple.Create<object, List<Component>>(
                        Response.Error($"Component of type '{componentTypeName}' not found on GameObject '{targetObj.name}'."), 
                        new List<Component>()
                    );
                }

                targetComponents.Add(component);
            }
            else if (componentTargetToken.Type == JTokenType.Array)
            {
                foreach (var compTypeToken in componentTargetToken.Children())
                {
                    if (compTypeToken.Type != JTokenType.String)
                    {
                        continue;
                    }

                    string componentTypeName = compTypeToken.ToString();
                    Type componentType = ComponentManager.GetComponentType(componentTypeName);

                    if (componentType == null)
                    {
                        Debug.LogWarning($"[ManageGameObject.Modify] Component type '{componentTypeName}' not found.");
                        continue;
                    }

                    Component component = targetObj.GetComponent(componentType);
                    if (component == null)
                    {
                        Debug.LogWarning($"[ManageGameObject.Modify] Component of type '{componentTypeName}' not found on GameObject '{targetObj.name}'.");
                        continue;
                    }

                    targetComponents.Add(component);
                }

                if (targetComponents.Count == 0)
                {
                    return Tuple.Create<object, List<Component>>(
                        Response.Error("None of the specified component types were found on the target GameObject."), 
                        new List<Component>()
                    );
                }
            }
            
            return Tuple.Create<object, List<Component>>(null, targetComponents);
        }

        /// <summary>
        /// Checks if a transform is a child of another transform
        /// </summary>
        private static bool IsChildOf(Transform child, Transform parent)
        {
            Transform current = child;
            while (current != null)
            {
                if (current == parent)
                {
                    return true;
                }
                current = current.parent;
            }
            return false;
        }
    }
} 