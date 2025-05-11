using System;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityMcpBridge.Editor.Helpers;
using UnityMcpBridge.Editor.Tools.ManageGameObject.Models;

namespace UnityMcpBridge.Editor.Tools.ManageGameObject.Implementation
{
    /// <summary>
    /// Handles component operations on GameObjects.
    /// Part of the ManageGameObject tool's internal implementation.
    /// </summary>
    internal static class ComponentManager
    {
        /// <summary>
        /// Gets components from a target GameObject.
        /// </summary>
        public static object GetComponentsFromTarget(JObject @params)
        {
            JToken targetToken = @params["target"];
            string searchMethod = @params["search_method"]?.ToString().ToLower();
            string target = targetToken?.ToString();
            
            if (string.IsNullOrEmpty(target))
                return Response.Error("'target' parameter required for get_components.");
                
            GameObject go = GameObjectFinder.FindSingleObject(targetToken, searchMethod);
            if (go == null)
                return Response.Error($"Failed to find GameObject with {searchMethod}: '{target}'.");

            var components = go.GetComponents<Component>();
            
            // Use SerializationUtilities instead of manually serializing each component
            var serializedComponents = SerializationUtilities.SerializeUnityObjects(components, "manage_gameobject");
            
            // Use dictionary approach for consistency
            var response = new Dictionary<string, object>
            {
                ["success"] = true,
                ["message"] = $"Found {components.Length} components on {go.name}.",
                ["data"] = serializedComponents
            };
            return response;
        }

        /// <summary>
        /// Adds a component to a target GameObject.
        /// </summary>
        public static object AddComponentToTarget(JObject @params)
        {
            GameObjectQueryParams queryParams = GameObjectQueryParams.FromJObject(@params);
            ComponentParams componentParams = ComponentParams.FromJObject(@params);
            
            GameObject targetGo = GameObjectFinder.FindSingleObject(queryParams.TargetToken, queryParams.SearchMethod);
            if (targetGo == null)
            {
                return Response.Error(
                    $"Target GameObject ('{queryParams.TargetToken}') not found using method '{queryParams.SearchMethod ?? "default"}'."
                );
            }

            string typeName = null;
            JObject properties = null;

            // Allow adding component specified directly or via componentsToAdd array (take first)
            if (!string.IsNullOrEmpty(componentParams.ComponentName))
            {
                typeName = componentParams.ComponentName;
                properties = componentParams.ComponentProperties?[typeName] as JObject; // Check if props are nested under name
            }
            else if (componentParams.ComponentsToAdd?.Count > 0)
            {
                var compToken = componentParams.ComponentsToAdd.First;
                if (compToken.Type == JTokenType.String)
                    typeName = compToken.ToString();
                else if (compToken is JObject compObj)
                {
                    typeName = compObj["type_name"]?.ToString();
                    properties = compObj["properties"] as JObject;
                }
            }

            if (string.IsNullOrEmpty(typeName))
            {
                return Response.Error(
                    "Component type name ('component_name' or first element in 'components_to_add') is required."
                );
            }

            var addResult = AddComponentInternal(targetGo, typeName, properties);
            if (addResult != null)
                return addResult; // Return error

            EditorUtility.SetDirty(targetGo);
            return Response.Success(
                $"Component '{typeName}' added to '{targetGo.name}'.",
                GameObjectSerializer.GetGameObjectData(targetGo)
            );
        }

        /// <summary>
        /// Removes a component from a target GameObject.
        /// </summary>
        public static object RemoveComponentFromTarget(JObject @params)
        {
            GameObjectQueryParams queryParams = GameObjectQueryParams.FromJObject(@params);
            ComponentParams componentParams = ComponentParams.FromJObject(@params);
            
            GameObject targetGo = GameObjectFinder.FindSingleObject(queryParams.TargetToken, queryParams.SearchMethod);
            if (targetGo == null)
            {
                return Response.Error(
                    $"Target GameObject ('{queryParams.TargetToken}') not found using method '{queryParams.SearchMethod ?? "default"}'."
                );
            }

            string typeName = null;
            // Allow removing component specified directly or via componentsToRemove array (take first)
            if (!string.IsNullOrEmpty(componentParams.ComponentName))
            {
                typeName = componentParams.ComponentName;
            }
            else if (componentParams.ComponentsToRemove?.Count > 0)
            {
                typeName = componentParams.ComponentsToRemove.First?.ToString();
            }

            if (string.IsNullOrEmpty(typeName))
            {
                return Response.Error(
                    "Component type name ('component_name' or first element in 'components_to_remove') is required."
                );
            }

            var removeResult = RemoveComponentInternal(targetGo, typeName);
            if (removeResult != null)
                return removeResult; // Return error

            EditorUtility.SetDirty(targetGo);
            return Response.Success(
                $"Component '{typeName}' removed from '{targetGo.name}'.",
                GameObjectSerializer.GetGameObjectData(targetGo)
            );
        }

        /// <summary>
        /// Sets property values on a component.
        /// </summary>
        public static object SetComponentPropertyOnTarget(JObject @params)
        {
            GameObjectQueryParams queryParams = GameObjectQueryParams.FromJObject(@params);
            ComponentParams componentParams = ComponentParams.FromJObject(@params);
            
            GameObject targetGo = GameObjectFinder.FindSingleObject(queryParams.TargetToken, queryParams.SearchMethod);
            if (targetGo == null)
            {
                return Response.Error(
                    $"Target GameObject ('{queryParams.TargetToken}') not found using method '{queryParams.SearchMethod ?? "default"}'."
                );
            }

            string compName = componentParams.ComponentName;
            JObject propertiesToSet = null;

            if (!string.IsNullOrEmpty(compName))
            {
                // Properties might be directly under componentProperties or nested under the component name
                if (componentParams.ComponentProperties != null)
                {
                    propertiesToSet = componentParams.ComponentProperties[compName] as JObject ?? componentParams.ComponentProperties; // Allow flat or nested structure
                }
            }
            else
            {
                return Response.Error("'component_name' parameter is required.");
            }

            if (propertiesToSet == null || !propertiesToSet.HasValues)
            {
                return Response.Error(
                    "'component_properties' dictionary for the specified component is required and cannot be empty."
                );
            }

            var setResult = SetComponentPropertiesInternal(targetGo, compName, propertiesToSet);
            if (setResult != null)
                return setResult; // Return error

            EditorUtility.SetDirty(targetGo);
            return Response.Success(
                $"Properties set for component '{compName}' on '{targetGo.name}'.",
                GameObjectSerializer.GetGameObjectData(targetGo)
            );
        }

        /// <summary>
        /// Adds a component by type name and optionally sets properties.
        /// Returns null on success, or an error response object on failure.
        /// </summary>
        internal static object AddComponentInternal(
            GameObject targetGo,
            string typeName,
            JObject properties
        )
        {
            Type componentType = PropertyUtils.FindType(typeName);
            if (componentType == null)
            {
                return Response.Error(
                    $"Component type '{typeName}' not found or is not a valid Component."
                );
            }
            if (!typeof(Component).IsAssignableFrom(componentType))
            {
                return Response.Error($"Type '{typeName}' is not a Component.");
            }

            // Prevent adding Transform again
            if (componentType == typeof(Transform))
            {
                return Response.Error("Cannot add another Transform component.");
            }

            // Check for 2D/3D physics component conflicts
            bool isAdding2DPhysics =
                typeof(Rigidbody2D).IsAssignableFrom(componentType)
                || typeof(Collider2D).IsAssignableFrom(componentType);
            bool isAdding3DPhysics =
                typeof(Rigidbody).IsAssignableFrom(componentType)
                || typeof(Collider).IsAssignableFrom(componentType);

            if (isAdding2DPhysics)
            {
                // Check if the GameObject already has any 3D Rigidbody or Collider
                if (
                    targetGo.GetComponent<Rigidbody>() != null
                    || targetGo.GetComponent<Collider>() != null
                )
                {
                    return Response.Error(
                        $"Cannot add 2D physics component '{typeName}' because the GameObject '{targetGo.name}' already has a 3D Rigidbody or Collider."
                    );
                }
            }
            else if (isAdding3DPhysics)
            {
                // Check if the GameObject already has any 2D Rigidbody or Collider
                if (
                    targetGo.GetComponent<Rigidbody2D>() != null
                    || targetGo.GetComponent<Collider2D>() != null
                )
                {
                    return Response.Error(
                        $"Cannot add 3D physics component '{typeName}' because the GameObject '{targetGo.name}' already has a 2D Rigidbody or Collider."
                    );
                }
            }

            try
            {
                // Use Undo.AddComponent for undo support
                Component newComponent = Undo.AddComponent(targetGo, componentType);
                if (newComponent == null)
                {
                    return Response.Error(
                        $"Failed to add component '{typeName}' to '{targetGo.name}'. It might be disallowed (e.g., adding script twice)."
                    );
                }

                // Set default values for specific component types
                if (newComponent is Light light)
                {
                    // Default newly added lights to directional
                    light.type = LightType.Directional;
                }

                // Set properties if provided
                if (properties != null)
                {
                    var setResult = SetComponentPropertiesInternal(
                        targetGo,
                        typeName,
                        properties,
                        newComponent
                    ); // Pass the new component instance
                    if (setResult != null)
                    {
                        // If setting properties failed, maybe remove the added component?
                        Undo.DestroyObjectImmediate(newComponent);
                        return setResult; // Return the error from setting properties
                    }
                }

                return null; // Success
            }
            catch (Exception e)
            {
                return Response.Error(
                    $"Error adding component '{typeName}' to '{targetGo.name}': {e.Message}"
                );
            }
        }

        /// <summary>
        /// Removes a component by type name.
        /// Returns null on success, or an error response object on failure.
        /// </summary>
        internal static object RemoveComponentInternal(GameObject targetGo, string typeName)
        {
            Type componentType = PropertyUtils.FindType(typeName);
            if (componentType == null)
            {
                return Response.Error($"Component type '{typeName}' not found for removal.");
            }

            // Prevent removing essential components
            if (componentType == typeof(Transform))
            {
                return Response.Error("Cannot remove the Transform component.");
            }

            Component componentToRemove = targetGo.GetComponent(componentType);
            if (componentToRemove == null)
            {
                return Response.Error(
                    $"Component '{typeName}' not found on '{targetGo.name}' to remove."
                );
            }

            try
            {
                // Use Undo.DestroyObjectImmediate for undo support
                Undo.DestroyObjectImmediate(componentToRemove);
                return null; // Success
            }
            catch (Exception e)
            {
                return Response.Error(
                    $"Error removing component '{typeName}' from '{targetGo.name}': {e.Message}"
                );
            }
        }

        /// <summary>
        /// Sets properties on a component.
        /// Returns null on success, or an error response object on failure.
        /// </summary>
        internal static object SetComponentPropertiesInternal(
            GameObject targetGo,
            string compName,
            JObject propertiesToSet,
            Component targetComponentInstance = null
        )
        {
            Component targetComponent = targetComponentInstance ?? targetGo.GetComponent(compName);
            if (targetComponent == null)
            {
                return Response.Error(
                    $"Component '{compName}' not found on '{targetGo.name}' to set properties."
                );
            }

            Undo.RecordObject(targetComponent, "Set Component Properties");

            foreach (var prop in propertiesToSet.Properties())
            {
                string propName = prop.Name;
                JToken propValue = prop.Value;

                try
                {
                    if (!PropertyUtils.SetProperty(targetComponent, propName, propValue))
                    {
                        // Log warning if property could not be set
                        Debug.LogWarning(
                            $"[ManageGameObject] Could not set property '{propName}' on component '{compName}' ('{targetComponent.GetType().Name}'). Property might not exist, be read-only, or type mismatch."
                        );
                        // Optionally return an error here instead of just logging
                        // return Response.Error($"Could not set property '{propName}' on component '{compName}'.");
                    }
                }
                catch (Exception e)
                {
                    Debug.LogError(
                        $"[ManageGameObject] Error setting property '{propName}' on '{compName}': {e.Message}"
                    );
                    // Optionally return an error here
                    // return Response.Error($"Error setting property '{propName}' on '{compName}': {e.Message}");
                }
            }
            EditorUtility.SetDirty(targetComponent);
            return null; // Success (or partial success if warnings were logged)
        }
    }
} 