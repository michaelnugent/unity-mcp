using System;
using System.Collections;
using System.Collections.Generic;
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
                return new SerializationResult<object>
                {
                    WasFullySerialized = true,
                    ObjectTypeName = "null",
                    Data = null
                };
            }

            Type objType = obj.GetType();
            var result = new SerializationResult<object>
            {
                ObjectTypeName = objType.FullName
            };

            // Handle Unity Object specially
            if (obj is UnityObject unityObj)
            {
                result.InstanceID = unityObj.GetInstanceID();
                
                // For now, Unity objects need fallback representation
                result.WasFullySerialized = false;
                result.Data = null;
                result.IntrospectedProperties = CreateFallbackRepresentation(unityObj, depth);
                
                return result;
            }

            // Check if we have a custom serializer for this type
            if (_customSerializers.TryGetValue(objType, out var serializer))
            {
                result.Data = serializer(obj, depth);
                result.WasFullySerialized = true;
                return result;
            }

            if (IsDirectlySerializable(obj))
            {
                try
                {
                    // For directly serializable objects, we can just use the object as data
                    result.Data = obj;
                    result.WasFullySerialized = true;
                }
                catch
                {
                    // If direct serialization fails, fall back to reflection
                    result.WasFullySerialized = false;
                    result.Data = null;
                    result.IntrospectedProperties = CreateFallbackRepresentation(obj, depth);
                }
            }
            else
            {
                // Object is not directly serializable, use fallback representation
                result.WasFullySerialized = false;
                result.Data = null;
                result.IntrospectedProperties = CreateFallbackRepresentation(obj, depth);
            }

            return result;
        }

        /// <summary>
        /// Creates a dictionary representation of an object using reflection.
        /// </summary>
        public static Dictionary<string, object> CreateFallbackRepresentation(object obj, SerializationDepth depth)
        {
            if (obj == null)
            {
                return null;
            }

            var result = new Dictionary<string, object>();
            Type objType = obj.GetType();
            
            // Add type metadata
            result["_type"] = objType.FullName;

            // For Unity objects, add a minimal set of useful properties
            if (obj is UnityObject unityObj)
            {
                result["_instanceID"] = unityObj.GetInstanceID();
                result["_name"] = unityObj.name;
                
                // Try to use a specialized handler from the registry
                var handler = SerializationHandlerRegistry.GetHandler(objType);
                if (handler != null)
                {
                    // Use the specialized handler to serialize the object
                    var handlerResult = handler.Serialize(obj, (int)depth);
                    if (handlerResult != null)
                    {
                        // Add the handler results to our output
                        foreach (var kvp in handlerResult)
                        {
                            result[kvp.Key] = kvp.Value;
                        }
                        
                        // Add a flag indicating we used a specialized handler
                        result["_usedSpecializedHandler"] = true;
                        result["_handlerType"] = handler.GetType().Name;
                        
                        return result;
                    }
                }
                
                // Fallback to default handling for specific Unity types
                if (obj is GameObject gameObject)
                {
                    ExtractGameObjectProperties(gameObject, result, depth);
                }
                else if (obj is Component component)
                {
                    ExtractComponentProperties(component, result, depth);
                }
                
                return result;
            }

            // For Basic depth, just return type info
            if (depth == SerializationDepth.Basic)
            {
                return result;
            }

            // For Standard and Deep depths, extract properties using reflection
            var flags = BindingFlags.Public | BindingFlags.Instance;
            
            // Get properties
            foreach (var prop in objType.GetProperties(flags))
            {
                if (prop.CanRead && prop.GetIndexParameters().Length == 0) // Skip indexed properties
                {
                    ExtractValue(obj, prop.Name, () => prop.GetValue(obj), result, depth);
                }
            }
            
            // Get fields
            foreach (var field in objType.GetFields(flags))
            {
                ExtractValue(obj, field.Name, () => field.GetValue(obj), result, depth);
            }
            
            return result;
        }

        private static void ExtractValue(object obj, string name, Func<object> getValue, Dictionary<string, object> result, SerializationDepth depth)
        {
            try
            {
                var value = getValue();
                if (value == null)
                {
                    result[name] = null;
                    return;
                }

                // Handle primitive types directly
                Type valueType = value.GetType();
                if (_directlySerializableTypes.Contains(valueType))
                {
                    result[name] = value;
                    return;
                }

                // For Deep depth, try to serialize nested objects
                if (depth == SerializationDepth.Deep)
                {
                    // Avoid circular references - only go one level deep for objects
                    var nestedDepth = SerializationDepth.Standard;
                    
                    if (value is IList list)
                    {
                        var items = new List<object>();
                        foreach (var item in list)
                        {
                            if (item == null)
                            {
                                items.Add(null);
                            }
                            else if (_directlySerializableTypes.Contains(item.GetType()))
                            {
                                items.Add(item);
                            }
                            else
                            {
                                items.Add(CreateFallbackRepresentation(item, nestedDepth));
                            }
                        }
                        result[name] = items;
                    }
                    else if (value is IDictionary dict)
                    {
                        var entries = new Dictionary<string, object>();
                        foreach (DictionaryEntry entry in dict)
                        {
                            string key = entry.Key.ToString();
                            var entryValue = entry.Value;
                            
                            if (entryValue == null)
                            {
                                entries[key] = null;
                            }
                            else if (_directlySerializableTypes.Contains(entryValue.GetType()))
                            {
                                entries[key] = entryValue;
                            }
                            else
                            {
                                entries[key] = CreateFallbackRepresentation(entryValue, nestedDepth);
                            }
                        }
                        result[name] = entries;
                    }
                    else
                    {
                        // For other complex objects, create nested representation
                        result[name] = CreateFallbackRepresentation(value, nestedDepth);
                    }
                }
                else
                {
                    // For Standard depth, just include type info and ToString value
                    result[name] = new Dictionary<string, object>
                    {
                        ["_type"] = valueType.FullName,
                        ["_toString"] = value.ToString()
                    };

                    // If it's a Unity Object, include instance ID and name
                    if (value is UnityObject unityObj)
                    {
                        ((Dictionary<string, object>)result[name])["_instanceID"] = unityObj.GetInstanceID();
                        ((Dictionary<string, object>)result[name])["_name"] = unityObj.name;
                    }
                }
            }
            catch (Exception ex)
            {
                // In case of error accessing the property, store the error info
                result[name] = new Dictionary<string, object>
                {
                    ["_error"] = $"Error accessing property: {ex.Message}"
                };
            }
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

            // Add transform info
            var transform = gameObject.transform;
            result["position"] = transform.position;
            result["rotation"] = transform.rotation;
            result["localScale"] = transform.localScale;

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