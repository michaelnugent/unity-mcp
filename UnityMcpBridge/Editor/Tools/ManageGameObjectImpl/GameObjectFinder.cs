using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityMcpBridge.Editor.Helpers;
using UnityMcpBridge.Editor.Helpers.Serialization;
using UnityMcpBridge.Editor.Tools.ManageGameObjectImpl.Models;

namespace UnityMcpBridge.Editor.Tools.ManageGameObjectImpl
{
    /// <summary>
    /// Handles searching and locating GameObjects in the Unity scene.
    /// Part of the ManageGameObject tool's internal implementation.
    /// </summary>
    internal static class GameObjectFinder
    {
        /// <summary>
        /// Main entry point for the find action from the ManageGameObject class.
        /// </summary>
        public static object FindGameObjects(JObject @params)
        {
            Debug.Log($"[MCP-DEBUG] FindGameObjects: @params: {@params}");
            GameObjectQueryParams queryParams = GameObjectQueryParams.FromJObject(@params);
            JToken targetToken = queryParams.TargetToken;
            string searchMethod = queryParams.SearchMethod;
            
            // Basic validation for empty search term when required
            bool searchTermEmpty = string.IsNullOrEmpty(queryParams.SearchTerm) && string.IsNullOrEmpty(targetToken?.ToString());
            bool isIdSearch = targetToken?.Type == JTokenType.Integer || 
                             (searchMethod == "by_id" && int.TryParse(targetToken?.ToString(), out _));
                              
            // Check if we need a search term
            if (searchTermEmpty && !isIdSearch && !queryParams.FindAll)
            {
                Debug.Log($"[MCP-DEBUG] FindGameObjects: Search term is empty and not searching by ID.");
                return Response.Error("Search term is required when find_all is false and not searching by ID.");
            }

            JObject findParams = new JObject
            {
                ["search_inactive"] = queryParams.SearchInactive,
                ["search_in_children"] = queryParams.SearchInChildren,
                ["search_term"] = queryParams.SearchTerm,
            };

            Debug.Log($"[MCP-DEBUG] FindGameObjects: findParams: {findParams}");

            List<GameObject> results = FindObjects(
                targetToken,
                searchMethod,
                queryParams.FindAll,
                findParams
            );

            // log results details
            Debug.Log($"[MCP-DEBUG] FindGameObjects: results: {results.Count}");
            foreach (var result in results)
            {
                Debug.Log($"[MCP-DEBUG] FindGameObjects: result: {result.name}");
            }

            // Handle empty results with better error messages
            if (results.Count == 0)
            {
                string errorMessage;
                if (searchTermEmpty)
                {
                    errorMessage = queryParams.FindAll 
                        ? "No game objects found in the scene." 
                        : "Search term is required for non-ID searches when find_all is false.";
                }
                else
                {
                    errorMessage = $"No game objects found with search method '{searchMethod}' and term '{(queryParams.SearchTerm ?? targetToken?.ToString())}'.";
                }
                return Response.Error(errorMessage);
            }

            // Use SerializationUtilities instead of manually serializing each GameObject
            var serializedResults = SerializationUtilities.SerializeUnityObjects(results, "manage_gameobject");
            
            // debug log serializedResults in detail
            Debug.Log($"[MCP-DEBUG] serializedResults count: {serializedResults.Count}");
            foreach(var item in serializedResults)
            {
                Debug.Log($"[MCP-DEBUG] serializedResult item type: {item.GetType()}, ToString: {item}");
            }
            
            // Process each serialization result to add basic properties
            var processedResults = new List<object>();
            
            foreach (var result in serializedResults)
            {
                if (result is SerializationResult<object> serializationResult)
                {
                    // Create a dictionary with both the serialization data and basic properties
                    var processedObj = new Dictionary<string, object>();
                    
                    // Start with basic properties from the GameObject
                    int index = processedResults.Count;
                    if (index < results.Count)
                    {
                        GameObject go = results[index];
                        processedObj["name"] = go.name;
                        processedObj["active"] = go.activeSelf;
                        processedObj["tag"] = go.tag;
                        processedObj["layer"] = go.layer;
                        processedObj["instanceID"] = go.GetInstanceID();
                        processedObj["__type"] = typeof(GameObject).FullName;
                        processedObj["__unity_type"] = typeof(GameObject).FullName;
                        
                        // Get transform data using TransformHandler
                        var transformHandler = new Helpers.Serialization.TransformHandler();
                        var transformData = transformHandler.Serialize(go.transform, SerializationHelper.SerializationDepth.Standard);
                        
                        // Make sure transform data has the correct type fields
                        if (!transformData.ContainsKey("__type"))
                            transformData["__type"] = typeof(Transform).FullName;
                        if (!transformData.ContainsKey("__unity_type"))
                            transformData["__unity_type"] = typeof(Transform).FullName;
                        
                        // Create components list that we will send
                        var componentsList = new List<Dictionary<string, object>>();
                        
                        // Add the transform as the first component
                        componentsList.Add(transformData);
                        
                        // Add other components using SerializationHelper to ensure we use registered handlers
                        var components = go.GetComponents<Component>();
                        foreach (var component in components)
                        {
                            // Skip null components and Transform (which we already added)
                            if (component == null || component is Transform)
                                continue;
                                
                            try
                            {
                                // Use SerializationHelper to get the right handler
                                var handler = SerializationHandlerRegistry.GetHandler(component.GetType());
                                Dictionary<string, object> componentData = null;
                                
                                if (handler != null)
                                {
                                    componentData = handler.Serialize(component, SerializationHelper.SerializationDepth.Standard);
                                }
                                else
                                {
                                    // Fallback to using SerializationHelper directly
                                    var serializedComponent = SerializationHelper.CreateSerializationResult(
                                        component, SerializationHelper.SerializationDepth.Standard);
                                    
                                    if (serializedComponent.IntrospectedProperties != null)
                                    {
                                        componentData = serializedComponent.IntrospectedProperties;
                                    }
                                }
                                
                                if (componentData != null)
                                {
                                    // Ensure component has type information
                                    if (!componentData.ContainsKey("__type"))
                                        componentData["__type"] = component.GetType().FullName;
                                    if (!componentData.ContainsKey("__unity_type"))
                                        componentData["__unity_type"] = component.GetType().FullName;
                                        
                                    componentsList.Add(componentData);
                                }
                            }
                            catch (Exception ex)
                            {
                                Debug.LogWarning($"Could not serialize component {component.GetType().Name}: {ex.Message}");
                            }
                        }
                        
                        // Add the components list to our result
                        processedObj["components"] = componentsList;
                        
                        // Also add transform_data directly for compatibility
                        if (transformData != null)
                        {
                            // Do not manually duplicate transform serialization logic here
                            // The TransformHandler already properly serializes all transform data
                            processedObj["transform_data"] = transformData;
                        }
                        
                        // Add a summary of component types for convenience
                        var componentSummary = new List<string>();
                        componentSummary.Add("Transform"); // Always have Transform
                        foreach (var comp in components)
                        {
                            if (comp != null && !(comp is Transform))
                            {
                                componentSummary.Add(comp.GetType().Name);
                            }
                        }
                        processedObj["components_summary"] = componentSummary;
                        
                        // Add hierarchical information
                        processedObj["children_count"] = go.transform.childCount;
                        processedObj["full_path"] = GameObjectSerializer.GetFullPath(go.transform);
                        
                        // Use SerializationHelper to serialize the GameObject for additional properties
                        var serializedGameObject = SerializationHelper.CreateSerializationResult(
                            go, SerializationHelper.SerializationDepth.Standard);
                            
                        // Copy relevant properties from the serialized GameObject
                        if (serializedGameObject.IntrospectedProperties != null)
                        {
                            foreach (var kvp in serializedGameObject.IntrospectedProperties)
                            {
                                // Skip properties we've already handled
                                if (kvp.Key != "components" && !processedObj.ContainsKey(kvp.Key))
                                {
                                    processedObj[kvp.Key] = kvp.Value;
                                }
                            }
                        }
                    }
                    
                    // If we have Data, copy it
                    if (serializationResult.Data is Dictionary<string, object> serializationData)
                    {
                        // Copy all serialization data to the processed object
                        foreach (var kvp in serializationData)
                        {
                            // Skip properties we've already handled
                            if (!processedObj.ContainsKey(kvp.Key))
                            {
                                processedObj[kvp.Key] = kvp.Value;
                            }
                        }
                    }
                    
                    // Copy all properties from SerializationResult using reflection
                    foreach (var prop in typeof(SerializationResult<object>).GetProperties())
                    {
                        if (prop.CanRead && prop.Name != "Data") // Skip Data as we already handled it
                        {
                            try
                            {
                                var value = prop.GetValue(serializationResult);
                                if (value != null && !processedObj.ContainsKey(prop.Name))
                                {
                                    processedObj[prop.Name] = value;
                                }
                            }
                            catch (Exception ex)
                            {
                                // Log but continue if a property can't be accessed
                                Debug.LogWarning($"Could not get property {prop.Name}: {ex.Message}");
                            }
                        }
                    }
                    
                    // Add to processed results
                    processedResults.Add(processedObj);
                }
                else
                {
                    // If not a SerializationResult, keep as-is
                    processedResults.Add(result);
                }
            }
            
            // If we only have one result and we're not explicitly looking for all, return just that one
            object dataToReturn;
            if (processedResults.Count == 1 && !queryParams.FindAll)
            {
                dataToReturn = processedResults[0];
                Debug.Log($"[MCP-DEBUG] Returning single gameObject: {dataToReturn}");
            }
            else
            {
                dataToReturn = processedResults;
                Debug.Log($"[MCP-DEBUG] Returning {processedResults.Count} gameObjects");
            }
            
            // Create the response
            var response = new Dictionary<string, object>
            {
                ["success"] = true,
                ["message"] = $"Found {results.Count} game objects.",
                ["data"] = dataToReturn
            };
            Debug.Log($"[MCP-DEBUG] response with data: {response["data"]}");
            return response;
        }

        /// <summary>
        /// Finds a single GameObject based on the search criteria.
        /// </summary>
        public static GameObject FindSingleObject(JToken targetToken, string searchMethod, JObject findParams = null)
        {
            // Validate inputs before proceeding
            if (targetToken == null && (findParams == null || findParams["search_term"] == null))
            {
                Debug.LogWarning("[ManageGameObject.Find] Both targetToken and searchTerm are null or empty.");
                return null;
            }
            
            // If find_all is not explicitly false, we still want only one for most single-target operations.
            bool findAll = findParams?["findAll"]?.ToObject<bool>() ?? false;
            
            // If a specific target ID is given, always find just that one.
            if (
                targetToken?.Type == JTokenType.Integer
                || (searchMethod == "by_id" && int.TryParse(targetToken?.ToString(), out _))
            )
            {
                findAll = false;
            }
            
            List<GameObject> results = FindObjects(
                targetToken,
                searchMethod,
                findAll,
                findParams
            );
            
            return results.Count > 0 ? results[0] : null;
        }

        /// <summary>
        /// Core logic for finding GameObjects based on various criteria.
        /// </summary>
        public static List<GameObject> FindObjects(
            JToken targetToken,
            string searchMethod,
            bool findAll,
            JObject findParams = null
        )
        {
            List<GameObject> results = new List<GameObject>();
            string searchTerm = findParams?["search_term"]?.ToString() ?? targetToken?.ToString(); // Use searchTerm if provided, else the target itself
            bool searchInChildren = findParams?["searchInChildren"]?.ToObject<bool>() ?? findParams?["search_in_children"]?.ToObject<bool>() ?? false;
            bool searchInactive = findParams?["searchInactive"]?.ToObject<bool>() ?? findParams?["search_inactive"]?.ToObject<bool>() ?? false;

            // Default search method if not specified
            if (string.IsNullOrEmpty(searchMethod))
            {
                if (targetToken?.Type == JTokenType.Integer)
                    searchMethod = "by_id";
                else if (!string.IsNullOrEmpty(searchTerm) && searchTerm.Contains('/'))
                    searchMethod = "by_path";
                else
                    searchMethod = "by_name"; // Default fallback
            }

            // Validate search term based on search method
            bool requiresSearchTerm = searchMethod != "by_id_or_name_or_path" &&
                                    !int.TryParse(searchTerm, out _); // ID can be parsed directly
            
            // Handle case where search term is required but missing
            if (requiresSearchTerm && string.IsNullOrEmpty(searchTerm))
            {
                // Special case: if findAll is true and no search term is provided,
                // default to returning all objects in the scene
                if (findAll)
                {
                    Debug.Log($"[ManageGameObject.Find] No search term provided with findAll=true, returning all scene objects");
                    return GetAllSceneObjects(searchInactive).ToList();
                }
                else
                {
                    // For single-object searches, we still need a search term or ID
                    Debug.LogWarning($"[ManageGameObject.Find] Search method '{searchMethod}' requires a search term, but none was provided.");
                    return results; // Return empty list
                }
            }

            GameObject rootSearchObject = null;
            // If searching in children, find the initial target first
            if (searchInChildren && targetToken != null)
            {
                rootSearchObject = FindSingleObject(targetToken, "by_id_or_name_or_path"); // Find the root for child search
                if (rootSearchObject == null)
                {
                    Debug.LogWarning(
                        $"[ManageGameObject.Find] Root object '{targetToken}' for child search not found."
                    );
                    return results; // Return empty if root not found
                }
            }

            switch (searchMethod)
            {
                case "by_id":
                    if (int.TryParse(searchTerm, out int instanceId))
                    {
                        // EditorUtility.InstanceIDToObject is slow, iterate manually if possible
                        // GameObject obj = EditorUtility.InstanceIDToObject(instanceId) as GameObject;
                        var allObjects = GetAllSceneObjects(searchInactive); // More efficient
                        GameObject obj = allObjects.FirstOrDefault(go =>
                            go.GetInstanceID() == instanceId
                        );
                        if (obj != null)
                            results.Add(obj);
                    }
                    break;
                case "by_name":
                    // Ensure we have a valid search term for name searches
                    if (string.IsNullOrEmpty(searchTerm))
                    {
                        Debug.LogWarning("[ManageGameObject.Find] Empty search term provided for by_name search.");
                        break;
                    }
                    
                    var searchPoolName = rootSearchObject
                        ? rootSearchObject
                            .GetComponentsInChildren<Transform>(searchInactive)
                            .Select(t => t.gameObject)
                        : GetAllSceneObjects(searchInactive);
                    
                    results.AddRange(searchPoolName.Where(go => go.name == searchTerm));
                    break;
                case "by_path":
                    // Ensure we have a valid path for path searches
                    if (string.IsNullOrEmpty(searchTerm))
                    {
                        Debug.LogWarning("[ManageGameObject.Find] Empty path provided for by_path search.");
                        break;
                    }
                    
                    // Path is relative to scene root or rootSearchObject
                    Transform foundTransform = rootSearchObject
                        ? rootSearchObject.transform.Find(searchTerm)
                        : GameObject.Find(searchTerm)?.transform;
                    if (foundTransform != null)
                        results.Add(foundTransform.gameObject);
                    break;
                case "by_tag":
                    // Ensure we have a valid tag for tag searches
                    if (string.IsNullOrEmpty(searchTerm))
                    {
                        Debug.LogWarning("[ManageGameObject.Find] Empty tag provided for by_tag search.");
                        break;
                    }
                    
                    var searchPoolTag = rootSearchObject
                        ? rootSearchObject
                            .GetComponentsInChildren<Transform>(searchInactive)
                            .Select(t => t.gameObject)
                        : GetAllSceneObjects(searchInactive);
                    results.AddRange(searchPoolTag.Where(go => go.CompareTag(searchTerm)));
                    break;
                case "by_layer":
                    var searchPoolLayer = rootSearchObject
                        ? rootSearchObject
                            .GetComponentsInChildren<Transform>(searchInactive)
                            .Select(t => t.gameObject)
                        : GetAllSceneObjects(searchInactive);
                    
                    if (string.IsNullOrEmpty(searchTerm))
                    {
                        Debug.LogWarning("[ManageGameObject.Find] Empty layer name/index provided for by_layer search.");
                        break;
                    }
                    
                    if (int.TryParse(searchTerm, out int layerIndex))
                    {
                        results.AddRange(searchPoolLayer.Where(go => go.layer == layerIndex));
                    }
                    else
                    {
                        int namedLayer = LayerMask.NameToLayer(searchTerm);
                        if (namedLayer != -1)
                            results.AddRange(searchPoolLayer.Where(go => go.layer == namedLayer));
                        else
                            Debug.LogWarning($"[ManageGameObject.Find] Layer name '{searchTerm}' not found.");
                    }
                    break;
                case "by_component":
                    if (string.IsNullOrEmpty(searchTerm))
                    {
                        Debug.LogWarning("[ManageGameObject.Find] Empty component type provided for by_component search.");
                        break;
                    }
                    
                    Type componentType = PropertyUtils.FindType(searchTerm);
                    if (componentType != null)
                    {
                        // Determine FindObjectsInactive based on the searchInactive flag
                        FindObjectsInactive findInactive = searchInactive
                            ? FindObjectsInactive.Include
                            : FindObjectsInactive.Exclude;
                        // Replace FindObjectsOfType with FindObjectsByType, specifying the sorting mode and inactive state
                        var searchPoolComp = rootSearchObject
                            ? rootSearchObject
                                .GetComponentsInChildren(componentType, searchInactive)
                                .Select(c => (c as Component).gameObject)
                            : UnityEngine
                                .Object.FindObjectsByType(
                                    componentType,
                                    findInactive,
                                    FindObjectsSortMode.None
                                )
                                .Select(c => (c as Component).gameObject);
                        results.AddRange(searchPoolComp.Where(go => go != null)); // Ensure GO is valid
                    }
                    else
                    {
                        Debug.LogWarning(
                            $"[ManageGameObject.Find] Component type not found: {searchTerm}"
                        );
                    }
                    break;
                case "by_id_or_name_or_path": // Helper method used internally
                    if (string.IsNullOrEmpty(searchTerm))
                    {
                        Debug.LogWarning("[ManageGameObject.Find] Empty search term provided for by_id_or_name_or_path search.");
                        break;
                    }
                    
                    if (int.TryParse(searchTerm, out int id))
                    {
                        var allObjectsId = GetAllSceneObjects(true); // Search inactive for internal lookup
                        GameObject objById = allObjectsId.FirstOrDefault(go =>
                            go.GetInstanceID() == id
                        );
                        if (objById != null)
                        {
                            results.Add(objById);
                            break;
                        }
                    }
                    GameObject objByPath = GameObject.Find(searchTerm);
                    if (objByPath != null)
                    {
                        results.Add(objByPath);
                        break;
                    }

                    var allObjectsName = GetAllSceneObjects(true);
                    results.AddRange(allObjectsName.Where(go => go.name == searchTerm));
                    break;
                default:
                    Debug.LogWarning(
                        $"[ManageGameObject.Find] Unknown search method: {searchMethod}"
                    );
                    break;
            }

            // Log a message if no results were found
            if (results.Count == 0)
            {
                Debug.LogWarning($"[ManageGameObject.Find] No objects found with search method '{searchMethod}' and term '{searchTerm}'.");
            }

            // If only one result is needed, return just the first one found.
            if (!findAll && results.Count > 1)
            {
                return new List<GameObject> { results[0] };
            }

            return results.Distinct().ToList(); // Ensure uniqueness
        }

        /// <summary>
        /// Helper to get all scene objects efficiently
        /// </summary>
        public static IEnumerable<GameObject> GetAllSceneObjects(bool includeInactive)
        {
            // SceneManager.GetActiveScene().GetRootGameObjects() is faster than FindObjectsOfType<GameObject>()
            var rootObjects = SceneManager.GetActiveScene().GetRootGameObjects();
            var allObjects = new List<GameObject>();
            foreach (var root in rootObjects)
            {
                allObjects.AddRange(
                    root.GetComponentsInChildren<Transform>(includeInactive)
                        .Select(t => t.gameObject)
                );
            }
            return allObjects;
        }
    }
} 