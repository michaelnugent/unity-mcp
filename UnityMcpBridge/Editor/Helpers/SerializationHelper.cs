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

            // Check for circular references
            if (_referenceTracker.IsCircularReference(obj))
            {
                // This is a circular reference, create a reference placeholder
                result.IsCircularReference = true;
                result.CircularReferencePath = _referenceTracker.GetReferencePath(obj);
                result.WasFullySerialized = false;
                
                // For Unity objects, still include the instance ID
                if (obj is UnityObject unityObject)
                {
                    result.InstanceID = unityObject.GetInstanceID();
                }
                
                return result;
            }
            
            // Add this object to the reference tracker
            _referenceTracker.AddReference(obj);

            // Handle Unity Object specially
            if (obj is UnityObject unityObj)
            {
                result.InstanceID = unityObj.GetInstanceID();
                
                // For now, Unity objects need fallback representation
                result.WasFullySerialized = false;
                result.Data = null;
                
                // Enter context for nested serialization
                _referenceTracker.EnterContext(objType.Name);
                result.IntrospectedProperties = CreateFallbackRepresentation(unityObj, depth);
                _referenceTracker.ExitContext();
                
                return result;
            }

            // Check if we have a custom serializer for this type
            if (_customSerializers.TryGetValue(objType, out var serializer))
            {
                // Enter context for nested serialization
                _referenceTracker.EnterContext(objType.Name);
                result.Data = serializer(obj, depth);
                _referenceTracker.ExitContext();
                
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
                    
                    // Enter context for nested serialization
                    _referenceTracker.EnterContext(objType.Name);
                    result.IntrospectedProperties = CreateFallbackRepresentation(obj, depth);
                    _referenceTracker.ExitContext();
                }
            }
            else
            {
                // Object is not directly serializable, use fallback representation
                result.WasFullySerialized = false;
                result.Data = null;
                
                // Enter context for nested serialization
                _referenceTracker.EnterContext(objType.Name);
                result.IntrospectedProperties = CreateFallbackRepresentation(obj, depth);
                _referenceTracker.ExitContext();
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

            // Check if there's a specialized handler for this type
            if (SerializationHandlerRegistry.TryGetHandler(objType, out var handler))
            {
                try
                {
                    int depthValue = (int)depth;
                    return handler.Serialize(obj, depthValue);
                }
                catch (Exception ex)
                {
                    // If handler fails, fall back to general reflection approach
                    result["__handler_error"] = $"Handler failed: {ex.Message}";
                }
            }

            // Add specialized handling for common types
            if (obj is GameObject gameObject)
            {
                // Special handling for GameObjects to extract key information
                ExtractGameObjectProperties(gameObject, result, depth);
                return result;
            }
            
            if (obj is Component component)
            {
                // Special handling for Components to extract key information
                ExtractComponentProperties(component, result, depth);
                return result;
            }

            // Add type information
            result["__type"] = objType.FullName;
            
            // For arrays, extract simple array representation
            if (objType.IsArray)
            {
                var array = obj as Array;
                result["__array_length"] = array.Length;
                result["__array_type"] = objType.GetElementType().FullName;
                
                // Only extract elements if we have remaining depth
                if (depth > SerializationDepth.Basic)
                {
                    var elements = new List<object>();
                    for (int i = 0; i < array.Length; i++)
                    {
                        var element = array.GetValue(i);
                        
                        // Check for circular references in array elements
                        _referenceTracker.EnterContext($"[{i}]");
                        if (_referenceTracker.IsCircularReference(element))
                        {
                            elements.Add(new Dictionary<string, object>
                            {
                                ["__circular_reference"] = true,
                                ["__reference_path"] = _referenceTracker.GetReferencePath(element)
                            });
                        }
                        else if (_referenceTracker.AddReference(element))
                        {
                            if (depth > SerializationDepth.Standard || IsDirectlySerializable(element))
                            {
                                elements.Add(ProcessValue(element, depth));
                            }
                            else
                            {
                                elements.Add($"{element?.GetType()?.Name ?? "null"}: {element}");
                            }
                        }
                        _referenceTracker.ExitContext();
                    }
                    result["elements"] = elements;
                }
                
                return result;
            }
            
            // For collections, extract elements
            if (obj is ICollection collection && depth > SerializationDepth.Basic)
            {
                result["__collection_count"] = collection.Count;
                
                // Extract elements if we're deep enough
                if (depth > SerializationDepth.Basic)
                {
                    var elements = new List<object>();
                    int index = 0;
                    foreach (var item in collection)
                    {
                        // Check for circular references in collection elements
                        _referenceTracker.EnterContext($"[{index}]");
                        if (_referenceTracker.IsCircularReference(item))
                        {
                            elements.Add(new Dictionary<string, object>
                            {
                                ["__circular_reference"] = true,
                                ["__reference_path"] = _referenceTracker.GetReferencePath(item)
                            });
                        }
                        else if (_referenceTracker.AddReference(item))
                        {
                            if (depth > SerializationDepth.Standard || IsDirectlySerializable(item))
                            {
                                elements.Add(ProcessValue(item, depth));
                            }
                            else
                            {
                                elements.Add($"{item?.GetType()?.Name ?? "null"}: {item}");
                            }
                        }
                        _referenceTracker.ExitContext();
                        index++;
                    }
                    result["elements"] = elements;
                }
            }
            
            // For dictionaries, extract keys and values
            if (obj is IDictionary dictionary && depth > SerializationDepth.Basic)
            {
                result["__dictionary_count"] = dictionary.Count;
                
                if (depth > SerializationDepth.Basic)
                {
                    var entries = new List<Dictionary<string, object>>();
                    
                    foreach (DictionaryEntry entry in dictionary)
                    {
                        var entryData = new Dictionary<string, object>();
                        
                        // Process the key
                        _referenceTracker.EnterContext($"key_{entry.Key}");
                        if (_referenceTracker.IsCircularReference(entry.Key))
                        {
                            entryData["key"] = new Dictionary<string, object>
                            {
                                ["__circular_reference"] = true,
                                ["__reference_path"] = _referenceTracker.GetReferencePath(entry.Key)
                            };
                        }
                        else if (_referenceTracker.AddReference(entry.Key))
                        {
                            entryData["key"] = ProcessValue(entry.Key, depth);
                        }
                        _referenceTracker.ExitContext();
                        
                        // Process the value
                        _referenceTracker.EnterContext($"value_{entry.Key}");
                        if (_referenceTracker.IsCircularReference(entry.Value))
                        {
                            entryData["value"] = new Dictionary<string, object>
                            {
                                ["__circular_reference"] = true,
                                ["__reference_path"] = _referenceTracker.GetReferencePath(entry.Value)
                            };
                        }
                        else if (_referenceTracker.AddReference(entry.Value))
                        {
                            entryData["value"] = ProcessValue(entry.Value, depth);
                        }
                        _referenceTracker.ExitContext();
                        
                        entries.Add(entryData);
                    }
                    
                    result["entries"] = entries;
                }
            }

            // Use reflection to get properties
            if (depth >= SerializationDepth.Basic)
            {
                // Get all public properties with getters
                foreach (var prop in objType.GetProperties(BindingFlags.Public | BindingFlags.Instance))
                {
                    try
                    {
                        if (prop.CanRead && prop.GetIndexParameters().Length == 0)
                        {
                            ExtractValue(obj, prop.Name, () => prop.GetValue(obj, null), result, depth);
                        }
                    }
                    catch (Exception ex)
                    {
                        // Skip problematic properties but record the error
                        result[$"__error_{prop.Name}"] = $"Property access failed: {ex.Message}";
                    }
                }
                
                // Get all public fields
                foreach (var field in objType.GetFields(BindingFlags.Public | BindingFlags.Instance))
                {
                    try
                    {
                        ExtractValue(obj, field.Name, () => field.GetValue(obj), result, depth);
                    }
                    catch (Exception ex)
                    {
                        // Skip problematic fields but record the error
                        result[$"__error_{field.Name}"] = $"Field access failed: {ex.Message}";
                    }
                }
            }
            
            return result;
        }

        private static void ExtractValue(object obj, string name, Func<object> getValue, Dictionary<string, object> result, SerializationDepth depth)
        {
            try
            {
                var value = getValue();
                
                // Enter context for the property/field
                _referenceTracker.EnterContext(name);
                
                // Check for circular references
                if (_referenceTracker.IsCircularReference(value))
                {
                    result[name] = new Dictionary<string, object>
                    {
                        ["__circular_reference"] = true,
                        ["__reference_path"] = _referenceTracker.GetReferencePath(value)
                    };
                }
                else if (_referenceTracker.AddReference(value))
                {
                    result[name] = ProcessValue(value, depth);
                }
                
                // Exit context
                _referenceTracker.ExitContext();
            }
            catch (Exception ex)
            {
                // Record the error but don't fail the entire serialization
                result[$"__error_{name}"] = $"Value extraction failed: {ex.Message}";
            }
        }
        
        /// <summary>
        /// Processes a value for serialization based on its type and the serialization depth.
        /// </summary>
        private static object ProcessValue(object value, SerializationDepth depth)
        {
            if (value == null)
            {
                return null;
            }
            
            Type valueType = value.GetType();
            
            // Handle directly serializable types
            if (IsDirectlySerializable(value))
            {
                return value;
            }
            
            // Handle Unity Objects
            if (value is UnityObject unityObj)
            {
                return new Dictionary<string, object>
                {
                    ["__unity_object"] = true,
                    ["__type"] = valueType.FullName,
                    ["instanceID"] = unityObj.GetInstanceID(),
                    ["name"] = unityObj.name
                };
            }
            
            // Handle collections at deeper depths
            if (depth > SerializationDepth.Standard && 
                (value is ICollection || valueType.IsArray || value is IDictionary))
            {
                return CreateFallbackRepresentation(value, depth);
            }
            
            // For other objects at deeper depths, recurse
            if (depth > SerializationDepth.Standard &&
                (valueType.IsClass || valueType.IsValueType))
            {
                return CreateFallbackRepresentation(value, SerializationDepth.Basic);
            }
            
            // For simple representation, just use ToString
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