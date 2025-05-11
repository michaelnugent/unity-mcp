using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;
using UnityMcpBridge.Editor.Helpers.Serialization;
using UnityObject = UnityEngine.Object;

namespace UnityMcpBridge.Editor.Helpers
{
    /// <summary>
    /// Provides helper methods for serializing Unity objects to JSON with enhanced error handling and fallback mechanisms.
    /// </summary>
    public static class SerializationHelper
    {
        // Singleton instance of the circular reference tracker
        private static readonly CircularReferenceTracker _referenceTracker = new CircularReferenceTracker();
        
        static SerializationHelper()
        {
            // Ensure serialization registry is initialized when this class is first used
            SerializationHandlerRegistry.Initialize();
        }

        /// <summary>
        /// Controls the amount of detail included in serialized objects.
        /// </summary>
        public enum SerializationDepth
        {
            /// <summary>
            /// Include only basic type information and simple properties
            /// </summary>
            Basic,
            
            /// <summary>
            /// Include normal reflection of properties and fields
            /// </summary>
            Standard,
            
            /// <summary>
            /// Attempt to serialize nested objects and special Unity properties
            /// </summary>
            Deep
        }

        private static readonly HashSet<Type> _directlySerializableTypes = new HashSet<Type>
        {
            typeof(bool), typeof(byte), typeof(sbyte), typeof(char),
            typeof(decimal), typeof(double), typeof(float), typeof(int),
            typeof(uint), typeof(long), typeof(ulong), typeof(short),
            typeof(ushort), typeof(string),
            
            // Unity built-in types
            typeof(Vector2), typeof(Vector3), typeof(Vector4),
            typeof(Rect), typeof(Quaternion), typeof(Color),
            typeof(Color32), typeof(LayerMask), typeof(AnimationCurve),
            typeof(Gradient), typeof(RectOffset), typeof(Matrix4x4)
        };

        private static readonly Dictionary<Type, Func<object, SerializationDepth, object>> _customSerializers =
            new Dictionary<Type, Func<object, SerializationDepth, object>>();

        /// <summary>
        /// Safely serializes any object to JSON, falling back to reflection-based
        /// representation when direct serialization fails.
        /// </summary>
        /// <param name="obj">The object to serialize</param>
        /// <param name="depth">The depth of serialization to perform</param>
        /// <param name="prettyPrint">Whether to format the JSON with indentation</param>
        /// <returns>A JSON string representation of the object</returns>
        public static string SafeSerializeToJson(object obj, SerializationDepth depth = SerializationDepth.Standard, bool prettyPrint = true)
        {
            if (obj == null)
            {
                return "null";
            }

            try
            {
                // Clear any previous tracking state
                _referenceTracker.Clear();
                
                // Try to create a SerializationResult object
                var result = CreateSerializationResult(obj, depth);
                
                // Convert to JSON
                return JsonUtility.ToJson(result, prettyPrint);
            }
            catch (Exception ex)
            {
                // If all else fails, create a minimal error representation
                var errorResult = new SerializationResult<object>
                {
                    WasFullySerialized = false,
                    ErrorMessage = $"Serialization failed: {ex.Message}",
                    ObjectTypeName = obj.GetType().FullName
                };
                
                if (obj is UnityObject unityObj)
                {
                    errorResult.InstanceID = unityObj.GetInstanceID();
                }

                return JsonUtility.ToJson(errorResult, prettyPrint);
            }
            finally
            {
                // Always clear the reference tracker when done
                _referenceTracker.Clear();
            }
        }

        /// <summary>
        /// Checks if an object can be directly serialized by Unity's JsonUtility.
        /// </summary>
        /// <param name="obj">The object to check</param>
        /// <returns>True if the object can be directly serialized, false otherwise</returns>
        public static bool IsDirectlySerializable(object obj)
        {
            if (obj == null)
            {
                return true;
            }

            Type type = obj.GetType();
            
            // Check primitives and simple types first
            if (_directlySerializableTypes.Contains(type))
            {
                return true;
            }
            
            // Check arrays and lists
            if (type.IsArray)
            {
                Type elementType = type.GetElementType();
                return elementType != null && IsTypeSerializable(elementType);
            }
            
            // Check if it's a List<T>
            if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>))
            {
                Type elementType = type.GetGenericArguments()[0];
                return IsTypeSerializable(elementType);
            }
            
            // Check if it's a serializable class or struct
            if (type.IsClass || type.IsValueType)
            {
                return Attribute.IsDefined(type, typeof(SerializableAttribute));
            }
            
            return false;
        }

        /// <summary>
        /// Checks if a type is serializable.
        /// </summary>
        public static bool IsTypeSerializable(Type type)
        {
            if (type == null)
            {
                return false;
            }
            
            if (_directlySerializableTypes.Contains(type))
            {
                return true;
            }
            
            // Check if it's a serializable class or struct
            if (type.IsClass || type.IsValueType)
            {
                return Attribute.IsDefined(type, typeof(SerializableAttribute));
            }
            
            return false;
        }

        /// <summary>
        /// Creates a SerializationResult for any object, handling both directly serializable objects
        /// and those that need reflection-based representation.
        /// </summary>
        public static SerializationResult<object> CreateSerializationResult(object obj, SerializationDepth depth)
        {
            if (obj == null)
            {
                // log null object
                Debug.Log($"[SERIALIZATION] obj is null");
                return new SerializationResult<object>
                {
                    WasFullySerialized = true,
                    ObjectTypeName = "null",
                    Data = null,
                    __serialization_status = "success",
                    __serialization_depth = depth.ToString()
                };
            }

            Type objType = obj.GetType();
            var result = new SerializationResult<object>
            {
                ObjectTypeName = objType.FullName,
                __serialization_depth = depth.ToString(),
                __object_id = obj is UnityEngine.Object unityObj ? unityObj.GetInstanceID().ToString() : Guid.NewGuid().ToString(),
                __assembly_qualified_name = objType.AssemblyQualifiedName,
                __base_type = objType.BaseType?.FullName,
                __implemented_interfaces = objType.GetInterfaces().Select(i => i.FullName).ToList(),
                __serialized_properties = new List<string>(),
                __failed_properties = new List<string>()
            };
            
            // Check for Unity Object type
            if (obj is UnityEngine.Object unityObject)
            {
                result.InstanceID = unityObject.GetInstanceID();
            }

            Debug.Log($"[SERIALIZATION] obj: {obj}");
            Debug.Log($"[SERIALIZATION] objType: {objType}");
            Debug.Log($"[SERIALIZATION] result: {result}");
            // Check for circular references
            string referencePath = _referenceTracker.GetReferencePath(obj);
            if (referencePath != null)
            {
                // This is a circular reference, so we'll return a reference to the original instance
                result.IsCircularReference = true;
                result.CircularReferencePath = referencePath;
                result.__serialization_status = "circular_reference";
                Debug.Log($"[SERIALIZATION] Circular reference detected for {objType.Name} at {referencePath}");
                return result;
            }
            
            // Add this object to the reference tracker
            _referenceTracker.AddReference(obj);
            try
            {
                // First, try to use a specialized handler if available
                bool handlerUsed = false;
                ISerializationHandler handler = SerializationHandlerRegistry.GetHandler(objType);
                if (handler != null)
                {
                    Debug.Log($"[SERIALIZATION] Using handler {handler.GetType().Name} for type {objType.FullName}");
                    try
                    {
                        Dictionary<string, object> handlerResult = handler.Serialize(obj, depth);
                        if (handlerResult == null)
                        {
                            Debug.LogWarning($"[SERIALIZATION] Handler {handler.GetType().Name} returned null for {objType.FullName}");
                        }
                        result.IntrospectedProperties = handlerResult;
                        result.WasFullySerialized = true;
                        handlerUsed = true;
                        result.__serialization_status = "success_with_handler";
                        
                        // Record serialized properties
                        if (handlerResult != null)
                        {
                            result.__serialized_properties.AddRange(handlerResult.Keys);
                        }
                    }
                    catch (Exception handlerEx)
                    {
                        Debug.LogWarning($"[SERIALIZATION] Serialization handler for {objType.Name} failed: {handlerEx.Message}");
                        // Fall back to standard serialization if handler fails
                        handlerUsed = false;
                        result.__serialization_error = $"Handler error: {handlerEx.Message}";
                    }
                }
                
                // If no handler or handler failed, try direct serialization for simple types
                if (!handlerUsed && IsDirectlySerializable(obj))
                {
                    Debug.Log($"[SERIALIZATION] Directly serializing {objType.FullName}");
                    result.Data = obj;
                    result.WasFullySerialized = true;
                    result.__serialization_status = "success_direct";
                    return result;
                }
                
                // If we get here and haven't used a handler, use reflection as a fallback
                if (!handlerUsed)
                {
                    Debug.Log($"[SERIALIZATION] Using fallback/reflection for {objType.FullName}");
                    // Use reflection to gather properties
                    var properties = CreateFallbackRepresentation(obj, depth);
                    result.IntrospectedProperties = properties;
                    result.WasFullySerialized = false;
                    result.__serialization_status = "fallback_reflection";
                    
                    // Record serialized properties
                    if (properties != null)
                    {
                        result.__serialized_properties.AddRange(properties.Keys);
                    }
                }

                // log result in detail
                Debug.Log($"[SERIALIZATION] result: {result}");
                // log result.IntrospectedProperties
                Debug.Log($"[SERIALIZATION] result.IntrospectedProperties: {result.IntrospectedProperties}");
                // log result.Data
                Debug.Log($"[SERIALIZATION] result.Data: {result.Data}");
                // log result.ErrorMessage
                Debug.Log($"[SERIALIZATION] result.ErrorMessage: {result.ErrorMessage}");
                // log result.WasFullySerialized
                Debug.Log($"[SERIALIZATION] result.WasFullySerialized: {result.WasFullySerialized}");
                
                
                return result;
            }
            catch (Exception ex)
            {
                // Handle any unexpected errors
                Debug.LogError($"[SERIALIZATION] Exception during serialization of {objType.FullName}: {ex}");
                result.WasFullySerialized = false;
                result.ErrorMessage = $"Serialization failed: {ex.Message}";
                result.__serialization_status = "error";
                result.__serialization_error = ex.ToString();
                return result;
            }
            finally
            {
                // We don't need to remove the reference as the CircularReferenceTracker will be cleared later
                // No RemoveReference call here
            }
        }

        /// <summary>
        /// Creates a dictionary representation of an object through reflection.
        /// Used as a fallback when direct serialization is not possible.
        /// </summary>
        /// <param name="obj">The object to create a fallback representation for</param>
        /// <param name="depth">The depth of serialization to perform</param>
        /// <param name="successList">List to track successfully serialized properties</param>
        /// <param name="failureList">List to track properties that couldn't be serialized</param>
        /// <returns>A dictionary representation of the object</returns>
        public static Dictionary<string, object> CreateFallbackRepresentation(
            object obj, 
            SerializationDepth depth,
            List<string> successList = null,
            List<string> failureList = null)
        {
            if (obj == null)
            {
                return null;
            }

            var result = new Dictionary<string, object>();
            Type objType = obj.GetType();
            
            // Special handling for Unity vector types to avoid circular references
            if (obj is Vector3 vector3)
            {
                return new Dictionary<string, object>
                {
                    ["__type"] = "UnityEngine.Vector3",
                    ["x"] = vector3.x,
                    ["y"] = vector3.y,
                    ["z"] = vector3.z
                };
            }
            else if (obj is Vector2 vector2)
            {
                return new Dictionary<string, object>
                {
                    ["__type"] = "UnityEngine.Vector2",
                    ["x"] = vector2.x,
                    ["y"] = vector2.y
                };
            }
            else if (obj is Vector4 vector4)
            {
                return new Dictionary<string, object>
                {
                    ["__type"] = "UnityEngine.Vector4",
                    ["x"] = vector4.x,
                    ["y"] = vector4.y,
                    ["z"] = vector4.z,
                    ["w"] = vector4.w
                };
            }
            else if (obj is Quaternion quaternion)
            {
                return new Dictionary<string, object>
                {
                    ["__type"] = "UnityEngine.Quaternion",
                    ["x"] = quaternion.x,
                    ["y"] = quaternion.y,
                    ["z"] = quaternion.z,
                    ["w"] = quaternion.w
                };
            }
            
            // Always add type information regardless of depth
            result["__type"] = objType.FullName;
            
            // Add Unity object instance ID if applicable
            if (obj is UnityObject unityObj)
            {
                result["__instanceId"] = unityObj.GetInstanceID();
                result["__name"] = unityObj.name;
            }

            // For Basic depth, we just return minimal info
            if (depth == SerializationDepth.Basic)
            {
                if (successList != null)
                {
                    successList.Add("__type");
                    if (obj is UnityObject)
                    {
                        successList.Add("__instanceId");
                        successList.Add("__name");
                    }
                }
                return result;
            }
            
            // Special handling for Unity GameObject
            if (obj is GameObject gameObject)
            {
                ExtractGameObjectProperties(gameObject, result, depth);
                if (successList != null)
                {
                    successList.Add("transform");
                    successList.Add("components");
                    successList.Add("children");
                    successList.Add("isActive");
                    successList.Add("tag");
                    successList.Add("layer");
                }
                return result;
            }
            
            // Special handling for Unity Component
            if (obj is Component component)
            {
                ExtractComponentProperties(component, result, depth);
                if (successList != null)
                {
                    successList.Add("gameObject");
                    successList.Add("enabled");
                }
                return result;
            }

            // Process properties using reflection
            foreach (var property in objType.GetProperties())
            {
                // Skip indexers and properties with non-public getters
                if (property.GetIndexParameters().Length > 0 || 
                    property.GetGetMethod() == null || 
                    !property.GetGetMethod().IsPublic)
                {
                    continue;
                }

                string name = property.Name;
                
                // Extract property value with error handling
                ExtractValue(obj, name, () => property.GetValue(obj), result, depth, successList, failureList);
            }

            // Process fields using reflection (for standard and deep only)
            if (depth > SerializationDepth.Basic)
            {
                foreach (var field in objType.GetFields())
                {
                    // Skip non-public fields
                    if (!field.IsPublic)
                    {
                        continue;
                    }

                    string name = field.Name;
                    
                    // Extract field value with error handling
                    ExtractValue(obj, name, () => field.GetValue(obj), result, depth, successList, failureList);
                }
            }

            // Handle collections specially
            if (obj is ICollection collection && depth > SerializationDepth.Basic)
            {
                try
                {
                    if (depth > SerializationDepth.Basic)
                    {
                        result["__count"] = collection.Count;
                        if (successList != null) successList.Add("__count");
                    }
                    
                    // For arrays and lists, try to extract items
                    if (obj is IList list)
                    {
                        var items = new List<object>();
                        for (int i = 0; i < list.Count; i++)
                        {
                            try
                            {
                                object item = list[i];
                                if (depth > SerializationDepth.Standard || IsDirectlySerializable(item))
                                {
                                    items.Add(ProcessValue(item, depth));
                                    if (successList != null) successList.Add($"items[{i}]");
                                }
                                else
                                {
                                    // For complex items in Standard depth, just add type info
                                    items.Add(new Dictionary<string, object> { 
                                        ["__type"] = item?.GetType().FullName ?? "null",
                                        ["__toString"] = item?.ToString() ?? "null" 
                                    });
                                    if (failureList != null) failureList.Add($"items[{i}]");
                                }
                            }
                            catch (Exception ex)
                            {
                                items.Add($"Error accessing item {i}: {ex.Message}");
                                if (failureList != null) failureList.Add($"items[{i}]");
                            }
                        }
                        result["__items"] = items;
                        if (successList != null) successList.Add("__items");
                    }
                }
                catch (Exception ex)
                {
                    result["__collection_error"] = ex.Message;
                    if (failureList != null) failureList.Add("__collection");
                }
            }

            // Handle dictionaries specially
            if (obj is IDictionary dictionary && depth > SerializationDepth.Basic)
            {
                try
                {
                    if (depth > SerializationDepth.Basic)
                    {
                        result["__count"] = dictionary.Count;
                        if (successList != null) successList.Add("__count");
                    }
                    
                    var entries = new Dictionary<object, object>();
                    foreach (var key in dictionary.Keys)
                    {
                        try
                        {
                            object value = dictionary[key];
                            string keyString = key?.ToString() ?? "null";
                            
                            if (depth > SerializationDepth.Standard || IsDirectlySerializable(value))
                            {
                                entries[keyString] = ProcessValue(value, depth);
                                if (successList != null) successList.Add($"entries[{keyString}]");
                            }
                            else
                            {
                                // For complex values in Standard depth, just add type info
                                entries[keyString] = new Dictionary<string, object> { 
                                    ["__type"] = value?.GetType().FullName ?? "null",
                                    ["__toString"] = value?.ToString() ?? "null" 
                                };
                                if (failureList != null) failureList.Add($"entries[{keyString}]");
                            }
                        }
                        catch (Exception ex)
                        {
                            entries[key?.ToString() ?? "null"] = $"Error accessing value: {ex.Message}";
                            if (failureList != null) failureList.Add($"entries[{key?.ToString() ?? "null"}]");
                        }
                    }
                    result["__entries"] = entries;
                    if (successList != null) successList.Add("__entries");
                }
                catch (Exception ex)
                {
                    result["__dictionary_error"] = ex.Message;
                    if (failureList != null) failureList.Add("__dictionary");
                }
            }

            // For Deep serialization, try to add additional context
            if (depth >= SerializationDepth.Deep)
            {
                try
                {
                    result["__toString"] = obj.ToString();
                    if (successList != null) successList.Add("__toString");
                    
                    // Add hash code as a consistent identifier
                    result["__hashcode"] = obj.GetHashCode();
                    if (successList != null) successList.Add("__hashcode");
                    
                    // Add type hierarchy information
                    var baseTypes = new List<string>();
                    var baseType = objType.BaseType;
                    while (baseType != null && baseType != typeof(object))
                    {
                        baseTypes.Add(baseType.FullName);
                        baseType = baseType.BaseType;
                    }
                    result["__baseTypes"] = baseTypes;
                    if (successList != null) successList.Add("__baseTypes");
                    
                    // Add interface information
                    result["__interfaces"] = objType.GetInterfaces().Select(i => i.FullName).ToArray();
                    if (successList != null) successList.Add("__interfaces");
                }
                catch (Exception ex)
                {
                    result["__deep_info_error"] = ex.Message;
                    if (failureList != null) failureList.Add("__deep_info");
                }
            }

            return result;
        }

        private static void ExtractValue(object obj, string name, Func<object> getValue, Dictionary<string, object> result, SerializationDepth depth, List<string> successList = null, List<string> failureList = null)
        {
            try
            {
                object value = getValue();
                if (value == null)
                {
                    result[name] = null;
                    if (successList != null) successList.Add(name);
                    return;
                }

                // Check for circular references
                string referencePath = _referenceTracker.GetReferencePath(value);
                if (referencePath != null)
                {
                    // This is a circular reference
                    result[name] = new Dictionary<string, object>
                    {
                        ["__circular_reference"] = true,
                        ["__reference_path"] = referencePath,
                        ["__type"] = value.GetType().FullName
                    };
                    if (successList != null) successList.Add(name);
                    return;
                }

                // Add reference for this value
                _referenceTracker.AddReference(value);
                
                try
                {
                    // Process the value based on depth
                    result[name] = ProcessValue(value, depth);
                    if (successList != null) successList.Add(name);
                }
                finally
                {
                    // We don't need to remove reference as the CircularReferenceTracker will be cleared later
                    // No RemoveReference call here
                }
            }
            catch (Exception ex)
            {
                // Record the error but don't fail the whole serialization
                result[$"__error_{name}"] = ex.Message;
                if (failureList != null) failureList.Add(name);
            }
        }
        
        /// <summary>
        /// Processes a value for serialization based on its type and the current depth.
        /// </summary>
        private static object ProcessValue(object value, SerializationDepth depth)
        {
            if (value == null)
                return null;
                
            var valueType = value.GetType();
            
            // Special handling for Unity objects
            if (value is UnityObject unityObj)
            {
                // For Unity objects, use specialized processing based on depth
                if (depth == SerializationDepth.Basic)
                {
                    // Just return minimal information for Basic depth
                    return new Dictionary<string, object>
                    {
                        ["__type"] = valueType.FullName,
                        ["__instanceId"] = unityObj.GetInstanceID(),
                        ["__name"] = unityObj.name
                    };
                }
                else if (depth == SerializationDepth.Standard)
                {
                    // Return more details but not full serialization for Standard depth
                    var objData = new Dictionary<string, object>
                    {
                        ["__type"] = valueType.FullName,
                        ["__instanceId"] = unityObj.GetInstanceID(),
                        ["__name"] = unityObj.name
                    };
                    
                    // Add extra properties for different types of Unity objects
                    if (value is GameObject go)
                    {
                        objData["isActive"] = go.activeSelf;
                        objData["tag"] = go.tag;
                        objData["layer"] = go.layer;
                        objData["componentCount"] = go.GetComponents<Component>().Length;
                    }
                    else if (value is Component comp)
                    {
                        objData["gameObjectName"] = comp.gameObject.name;
                        if (comp is Behaviour behaviour)
                        {
                            objData["enabled"] = behaviour.enabled;
                        }
                    }
                    
                    return objData;
                }
                else // Deep serialization
                {
                    // Use specialized handlers to fully serialize Unity objects
                    if (SerializationHandlerRegistry.TryGetHandler(valueType, out var handler))
                    {
                        try
                        {
                            return handler.Serialize(value, depth);
                        }
                        catch (Exception handlerEx)
                        {
                            Debug.LogWarning($"Handler for {valueType.Name} failed: {handlerEx.Message}");
                            // Fall back to default fallback representation
                            return CreateFallbackRepresentation(value, SerializationDepth.Standard);
                        }
                    }
                    
                    // If no handler, create fallback
                    return CreateFallbackRepresentation(value, SerializationDepth.Standard);
                }
            }
            
            // For directly serializable types, use them as-is
            if (IsDirectlySerializable(value))
            {
                return value;
            }
            
            // For arrays and collections with limited depth
            if ((valueType.IsArray || value is ICollection) && depth == SerializationDepth.Standard)
            {
                if (value is ICollection collection)
                {
                    return new Dictionary<string, object>
                    {
                        ["__type"] = valueType.FullName,
                        ["__count"] = collection.Count,
                        ["__toString"] = value.ToString()
                    };
                }
            }
            
            // Try to use a specialized handler first
            if (SerializationHandlerRegistry.TryGetHandler(valueType, out var typeHandler))
            {
                try
                {
                    return typeHandler.Serialize(value, depth);
                }
                catch (Exception handlerEx)
                {
                    Debug.LogWarning($"Handler for {valueType.Name} failed: {handlerEx.Message}");
                }
            }
            
            // For deeper serialization, use reflection to break down the object
            if (depth > SerializationDepth.Standard ||
                valueType.Namespace?.StartsWith("UnityEngine") == true || 
                valueType.Namespace?.StartsWith("UnityEditor") == true)
            {
                return CreateFallbackRepresentation(value, depth > SerializationDepth.Standard ? depth : SerializationDepth.Basic);
            }
            
            // For standard depth with types we don't have special handling for,
            // provide a simple string representation
            return value.ToString();
        }

        private static void ExtractGameObjectProperties(GameObject gameObject, Dictionary<string, object> result, SerializationDepth depth)
        {
            result["tag"] = gameObject.tag;
            result["layer"] = gameObject.layer;
            result["isActive"] = gameObject.activeSelf;

            if (depth == SerializationDepth.Basic)
            {
                return;
            }

            // Add transform info - manually create dictionaries to avoid Vector3 circular references
            var transform = gameObject.transform;
            
            // Position
            result["position"] = new Dictionary<string, float>
            {
                ["x"] = transform.position.x,
                ["y"] = transform.position.y,
                ["z"] = transform.position.z
            };
            
            // Rotation - store both as quaternion and euler angles
            result["rotation"] = new Dictionary<string, float>
            {
                ["x"] = transform.rotation.x,
                ["y"] = transform.rotation.y,
                ["z"] = transform.rotation.z,
                ["w"] = transform.rotation.w
            };
            
            // Euler angles
            result["eulerAngles"] = new Dictionary<string, float>
            {
                ["x"] = transform.eulerAngles.x,
                ["y"] = transform.eulerAngles.y,
                ["z"] = transform.eulerAngles.z
            };
            
            // Scale
            result["localScale"] = new Dictionary<string, float>
            {
                ["x"] = transform.localScale.x,
                ["y"] = transform.localScale.y,
                ["z"] = transform.localScale.z
            };

            // Add component information
            var components = gameObject.GetComponents<Component>();
            var componentList = new List<Dictionary<string, object>>();
            
            foreach (var component in components)
            {
                if (component != null)
                {
                    var componentData = new Dictionary<string, object>
                    {
                        ["_type"] = component.GetType().FullName,
                        ["_name"] = component.GetType().Name,
                        ["_instanceID"] = component.GetInstanceID()
                    };
                    
                    if (depth == SerializationDepth.Deep)
                    {
                        // For Deep serialization, add more component properties
                        ExtractComponentProperties(component, componentData, SerializationDepth.Standard);
                    }
                    
                    componentList.Add(componentData);
                }
            }
            
            result["components"] = componentList;
            
            // Add children
            result["childCount"] = transform.childCount;
            
            if (depth == SerializationDepth.Deep)
            {
                var children = new List<Dictionary<string, object>>();
                
                for (int i = 0; i < transform.childCount; i++)
                {
                    var childTransform = transform.GetChild(i);
                    var childData = new Dictionary<string, object>
                    {
                        ["_type"] = "UnityEngine.GameObject",
                        ["_name"] = childTransform.gameObject.name,
                        ["_instanceID"] = childTransform.gameObject.GetInstanceID()
                    };
                    
                    // To avoid deep recursion, use Standard depth for children
                    ExtractGameObjectProperties(childTransform.gameObject, childData, SerializationDepth.Standard);
                    children.Add(childData);
                }
                
                result["children"] = children;
            }
        }

        /// <summary>
        /// Extracts component properties for a Unity Component.
        /// </summary>
        private static void ExtractComponentProperties(Component component, Dictionary<string, object> result, SerializationDepth depth)
        {
            // Add reference to owner GameObject
            var gameObject = component.gameObject;
            result["gameObject"] = new Dictionary<string, object>
            {
                ["_type"] = "UnityEngine.GameObject",
                ["_name"] = gameObject.name,
                ["_instanceID"] = gameObject.GetInstanceID()
            };
            
            // Handle specific component types
            if (component is Transform transform)
            {
                result["position"] = transform.position;
                result["rotation"] = transform.rotation;
                result["localScale"] = transform.localScale;
                result["childCount"] = transform.childCount;
            }
            else if (component is Renderer renderer)
            {
                result["isVisible"] = renderer.isVisible;
                
                if (renderer.sharedMaterial != null)
                {
                    result["material"] = new Dictionary<string, object>
                    {
                        ["_type"] = "UnityEngine.Material",
                        ["_name"] = renderer.sharedMaterial.name,
                        ["_instanceID"] = renderer.sharedMaterial.GetInstanceID()
                    };
                }
            }
            else if (component is Collider collider)
            {
                result["isTrigger"] = collider.isTrigger;
                result["enabled"] = collider.enabled;
            }
            else if (component is MonoBehaviour behaviour)
            {
                result["enabled"] = behaviour.enabled;
                
                if (depth == SerializationDepth.Deep)
                {
                    // For Deep serialization, use reflection to extract properties of the script
                    var scriptProperties = CreateFallbackRepresentation(behaviour, SerializationDepth.Standard);
                    foreach (var prop in scriptProperties)
                    {
                        // Skip properties already added
                        if (prop.Key != "_type" && prop.Key != "_instanceID" && prop.Key != "_name" && 
                            prop.Key != "gameObject" && prop.Key != "enabled")
                        {
                            result[prop.Key] = prop.Value;
                        }
                    }
                }
            }
        }
        
        /// <summary>
        /// Registers a custom serializer for a specific type.
        /// </summary>
        /// <param name="type">The type to register a serializer for</param>
        /// <param name="serializer">A function that takes an object and depth and returns a serialized representation</param>
        public static void RegisterSerializer(Type type, Func<object, SerializationDepth, object> serializer)
        {
            if (type == null)
            {
                throw new ArgumentNullException(nameof(type));
            }
            
            if (serializer == null)
            {
                throw new ArgumentNullException(nameof(serializer));
            }
            
            _customSerializers[type] = serializer;
        }
        
        /// <summary>
        /// Unregisters a custom serializer for a specific type.
        /// </summary>
        /// <param name="type">The type to unregister the serializer for</param>
        /// <returns>True if the serializer was successfully removed, false otherwise</returns>
        public static bool UnregisterSerializer(Type type)
        {
            if (type == null)
            {
                throw new ArgumentNullException(nameof(type));
            }
            
            return _customSerializers.Remove(type);
        }
    }
} 