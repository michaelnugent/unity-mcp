using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

namespace UnityMcpBridge.Editor.Helpers.Serialization
{
    /// <summary>
    /// Handler for serializing Unity Component objects.
    /// </summary>
    public class ComponentHandler : ISerializationHandler
    {
        /// <summary>
        /// Gets the type handled by this serialization handler.
        /// </summary>
        public Type HandledType => typeof(Component);

        /// <summary>
        /// Serializes a Component object into a dictionary representation.
        /// </summary>
        /// <param name="obj">The Component to serialize</param>
        /// <param name="depth">The serialization depth to use</param>
        /// <returns>A dictionary containing the component's serialized properties</returns>
        public Dictionary<string, object> Serialize(object obj, SerializationHelper.SerializationDepth depth = SerializationHelper.SerializationDepth.Standard)
        {
            if (obj == null)
                return null;

            if (!(obj is Component component))
                throw new ArgumentException($"Object is not a Component: {obj.GetType().Name}");

            var result = new Dictionary<string, object>
            {
                ["type"] = component.GetType().Name,
                ["enabled"] = IsComponentEnabled(component),
                ["__type"] = component.GetType().FullName,
                ["__object_id"] = component.GetInstanceID().ToString()
            };

            // For Basic depth, we're done
            if (depth == SerializationHelper.SerializationDepth.Basic)
            {
                return result;
            }

            // Add reference to GameObject
            result["gameObject"] = new Dictionary<string, object>
            {
                ["name"] = component.gameObject.name,
                ["instanceID"] = component.gameObject.GetInstanceID(),
                ["__type"] = typeof(GameObject).FullName
            };

            // Add component-specific properties
            SerializeComponentProperties(component, result, depth);

            return result;
        }

        /// <summary>
        /// Checks if a component is enabled.
        /// </summary>
        /// <param name="component">The component to check</param>
        /// <returns>True if enabled, false otherwise</returns>
        private bool IsComponentEnabled(Component component)
        {
            // Handle common enableable components
            if (component is Behaviour behaviour)
                return behaviour.enabled;
            if (component is Renderer renderer)
                return renderer.enabled;
            if (component is Collider collider)
                return collider.enabled;

            // Default case, the component doesn't have an enabled property
            return true;
        }

        /// <summary>
        /// Serializes the public properties of a component.
        /// </summary>
        /// <param name="component">The component to serialize</param>
        /// <param name="result">The dictionary to add properties to</param>
        /// <param name="depth">The serialization depth to use</param>
        private void SerializeComponentProperties(Component component, Dictionary<string, object> result, SerializationHelper.SerializationDepth depth)
        {
            var properties = new Dictionary<string, object>();
            var type = component.GetType();
            
            // Get public properties
            var publicProps = type.GetProperties(BindingFlags.Public | BindingFlags.Instance);
            
            foreach (var prop in publicProps)
            {
                try
                {
                    // Skip non-readable properties or special Unity properties that might cause issues
                    if (!prop.CanRead || prop.Name == "tag" || prop.Name == "name" || 
                        prop.Name == "hideFlags" || prop.Name == "gameObject" ||
                        prop.Name == "transform" || prop.Name == "enabled" ||
                        prop.Name == "normalized") // Skip normalized to avoid circular references
                        continue;
                    
                    var value = prop.GetValue(component);
                    
                    // Skip null values
                    if (value == null)
                        continue;

                    // For Standard depth, only include simple properties
                    if (depth == SerializationHelper.SerializationDepth.Standard)
                    {
                        // Handle common Unity types
                        if (value is Vector2 vector2)
                            properties[prop.Name] = SerializeVector2(vector2);
                        else if (value is Vector3 vector3)
                            properties[prop.Name] = SerializeVector3(vector3);
                        else if (value is Vector4 vector4)
                            properties[prop.Name] = SerializeVector4(vector4);
                        else if (value is Quaternion quaternion)
                            properties[prop.Name] = SerializeQuaternion(quaternion);
                        else if (value is Color color)
                            properties[prop.Name] = SerializeColor(color);
                        else if (value is Bounds bounds)
                            properties[prop.Name] = SerializeBounds(bounds);
                        else if (value is Rect rect)
                            properties[prop.Name] = SerializeRect(rect);
                        // Add simple value types directly
                        else if (value is string || value is bool || value is int || value is float || 
                                value is double || value is long || value is byte || value is sbyte || 
                                value is short || value is ushort || value is uint || value is ulong || 
                                value is decimal || value.GetType().IsEnum)
                        {
                            properties[prop.Name] = value;
                        }
                        // For non-primitive types, just add type info
                        else
                        {
                            properties[prop.Name] = new Dictionary<string, object>
                            {
                                ["__type"] = value.GetType().FullName,
                                ["__toString"] = value.ToString()
                            };
                        }
                    }
                    // For Deep depth, include more complex properties
                    else if (depth == SerializationHelper.SerializationDepth.Deep)
                    {
                        // For Unity Objects, add reference
                        if (value is UnityEngine.Object unityObj)
                        {
                            properties[prop.Name] = new Dictionary<string, object>
                            {
                                ["__type"] = unityObj.GetType().FullName,
                                ["__name"] = unityObj.name,
                                ["__instanceId"] = unityObj.GetInstanceID()
                            };
                        }
                        // Handle common Unity types
                        else if (value is Vector2 vector2)
                            properties[prop.Name] = SerializeVector2(vector2);
                        else if (value is Vector3 vector3)
                            properties[prop.Name] = SerializeVector3(vector3);
                        else if (value is Vector4 vector4)
                            properties[prop.Name] = SerializeVector4(vector4);
                        else if (value is Quaternion quaternion)
                            properties[prop.Name] = SerializeQuaternion(quaternion);
                        else if (value is Color color)
                            properties[prop.Name] = SerializeColor(color);
                        else if (value is Bounds bounds)
                            properties[prop.Name] = SerializeBounds(bounds);
                        else if (value is Rect rect)
                            properties[prop.Name] = SerializeRect(rect);
                        // Add simple value types directly
                        else if (value is string || value is bool || value is int || value is float || 
                                value is double || value is long || value is byte || value is sbyte || 
                                value is short || value is ushort || value is uint || value is ulong || 
                                value is decimal || value.GetType().IsEnum)
                        {
                            properties[prop.Name] = value;
                        }
                        // Try to introspect other types
                        else
                        {
                            try
                            {
                                // Create a representation with property values for complex types
                                var propData = new Dictionary<string, object>
                                {
                                    ["__type"] = value.GetType().FullName,
                                    ["__toString"] = value.ToString()
                                };

                                // Try to add a few public properties
                                foreach (var nestedProp in value.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
                                {
                                    if (nestedProp.CanRead && nestedProp.GetIndexParameters().Length == 0 &&
                                        nestedProp.Name != "normalized") // Skip normalized to avoid circular references
                                    {
                                        try
                                        {
                                            var nestedValue = nestedProp.GetValue(value);
                                            if (nestedValue == null)
                                                continue;
                                                
                                            if (nestedValue is string || nestedValue is bool || nestedValue is int || 
                                                nestedValue is float || nestedValue is double || nestedValue is long || 
                                                nestedValue is decimal || nestedValue.GetType().IsEnum)
                                            {
                                                propData[nestedProp.Name] = nestedValue;
                                            }
                                        }
                                        catch
                                        {
                                            // Skip properties that can't be accessed
                                        }
                                    }
                                }
                                
                                properties[prop.Name] = propData;
                            }
                            catch
                            {
                                // Fallback to just string representation
                                properties[prop.Name] = value.ToString();
                            }
                        }
                    }
                }
                catch (Exception)
                {
                    // Skip properties that throw exceptions when accessed
                    continue;
                }
            }
            
            if (properties.Count > 0)
            {
                result["properties"] = properties;
            }
        }

        #region Type Serialization Helpers

        private Dictionary<string, float> SerializeVector2(Vector2 vector)
        {
            // Only serialize the basic components to avoid self-referencing loops
            return new Dictionary<string, float>
            {
                ["x"] = vector.x,
                ["y"] = vector.y
            };
        }

        private Dictionary<string, float> SerializeVector3(Vector3 vector)
        {
            // Only serialize the basic components to avoid self-referencing loops
            return new Dictionary<string, float>
            {
                ["x"] = vector.x,
                ["y"] = vector.y,
                ["z"] = vector.z
            };
        }

        private Dictionary<string, float> SerializeVector4(Vector4 vector)
        {
            // Only serialize the basic components to avoid self-referencing loops
            return new Dictionary<string, float>
            {
                ["x"] = vector.x,
                ["y"] = vector.y,
                ["z"] = vector.z,
                ["w"] = vector.w
            };
        }

        private Dictionary<string, float> SerializeQuaternion(Quaternion quaternion)
        {
            // Only serialize the basic components to avoid self-referencing loops
            return new Dictionary<string, float>
            {
                ["x"] = quaternion.x,
                ["y"] = quaternion.y,
                ["z"] = quaternion.z,
                ["w"] = quaternion.w
            };
        }

        private Dictionary<string, float> SerializeColor(Color color)
        {
            // Only serialize the basic components to avoid self-referencing loops
            return new Dictionary<string, float>
            {
                ["r"] = color.r,
                ["g"] = color.g,
                ["b"] = color.b,
                ["a"] = color.a
            };
        }

        private Dictionary<string, object> SerializeBounds(Bounds bounds)
        {
            return new Dictionary<string, object>
            {
                ["center"] = SerializeVector3(bounds.center),
                ["size"] = SerializeVector3(bounds.size)
            };
        }

        private Dictionary<string, float> SerializeRect(Rect rect)
        {
            return new Dictionary<string, float>
            {
                ["x"] = rect.x,
                ["y"] = rect.y,
                ["width"] = rect.width,
                ["height"] = rect.height
            };
        }

        #endregion
    }
} 