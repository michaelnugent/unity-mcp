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
        /// <param name="depth">The maximum depth to traverse when serializing nested objects</param>
        /// <returns>A dictionary containing the component's serialized properties</returns>
        public Dictionary<string, object> Serialize(object obj, int depth = 1)
        {
            if (obj == null)
                return null;

            if (!(obj is Component component))
                throw new ArgumentException($"Object is not a Component: {obj.GetType().Name}");

            var result = new Dictionary<string, object>
            {
                ["type"] = component.GetType().Name,
                ["enabled"] = IsComponentEnabled(component)
            };

            // Add additional properties if depth allows
            if (depth > 0)
            {
                SerializeComponentProperties(component, result, depth - 1);
            }

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
        /// <param name="depth">The remaining depth for nested serialization</param>
        private void SerializeComponentProperties(Component component, Dictionary<string, object> result, int depth)
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
                        prop.Name == "transform" || prop.Name == "enabled")
                        continue;
                    
                    var value = prop.GetValue(component);
                    
                    // Skip null values
                    if (value == null)
                        continue;
                    
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
                    // Skip other complex types to avoid circular references or excessive data
                    else
                    {
                        properties[prop.Name] = value.ToString();
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
            return new Dictionary<string, float>
            {
                ["x"] = vector.x,
                ["y"] = vector.y
            };
        }

        private Dictionary<string, float> SerializeVector3(Vector3 vector)
        {
            return new Dictionary<string, float>
            {
                ["x"] = vector.x,
                ["y"] = vector.y,
                ["z"] = vector.z
            };
        }

        private Dictionary<string, float> SerializeVector4(Vector4 vector)
        {
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