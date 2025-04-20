using Newtonsoft.Json.Linq;
using UnityEngine;
using System.Collections.Generic;

namespace UnityMcpBridge.Editor.Helpers
{
    /// <summary>
    /// Helper class for converting JSON parameters to Unity types
    /// </summary>
    public static class UnityTypeHelper
    {
        /// <summary>
        /// Parses a JObject or JArray into a Vector2
        /// </summary>
        /// <param name="value">JSON value representing a Vector2</param>
        /// <returns>A Vector2 with the parsed values</returns>
        /// <exception cref="System.Exception">Thrown when value has invalid format</exception>
        public static Vector2 ParseVector2(JToken value)
        {
            if (value == null)
                throw new System.Exception("Vector2 value cannot be null.");

            // Handle array format [x, y]
            if (value is JArray array)
            {
                if (array.Count != 2)
                    throw new System.Exception("Vector2 array must have exactly 2 elements [x, y].");
                
                return new Vector2(
                    (float)array[0],
                    (float)array[1]
                );
            }
            
            // Handle object format {"x": float, "y": float}
            if (value is JObject obj)
            {
                if (!obj.ContainsKey("x") || !obj.ContainsKey("y"))
                    throw new System.Exception("Vector2 object must contain 'x' and 'y' properties.");
                
                return new Vector2(
                    (float)obj["x"],
                    (float)obj["y"]
                );
            }
            
            throw new System.Exception("Vector2 must be provided as an array [x, y] or object {\"x\": float, \"y\": float}.");
        }

        /// <summary>
        /// Parses a JObject or JArray into a Vector3
        /// </summary>
        /// <param name="value">JSON value representing a Vector3</param>
        /// <returns>A Vector3 with the parsed values</returns>
        /// <exception cref="System.Exception">Thrown when value has invalid format</exception>
        public static Vector3 ParseVector3(JToken value)
        {
            if (value == null)
                throw new System.Exception("Vector3 value cannot be null.");

            // Handle array format [x, y, z]
            if (value is JArray array)
            {
                if (array.Count != 3)
                    throw new System.Exception("Vector3 array must have exactly 3 elements [x, y, z].");
                
                return new Vector3(
                    (float)array[0],
                    (float)array[1],
                    (float)array[2]
                );
            }
            
            // Handle object format {"x": float, "y": float, "z": float}
            if (value is JObject obj)
            {
                if (!obj.ContainsKey("x") || !obj.ContainsKey("y") || !obj.ContainsKey("z"))
                    throw new System.Exception("Vector3 object must contain 'x', 'y', and 'z' properties.");
                
                return new Vector3(
                    (float)obj["x"],
                    (float)obj["y"],
                    (float)obj["z"]
                );
            }
            
            throw new System.Exception("Vector3 must be provided as an array [x, y, z] or object {\"x\": float, \"y\": float, \"z\": float}.");
        }

        /// <summary>
        /// Parses a JObject or JArray into a Vector4
        /// </summary>
        /// <param name="value">JSON value representing a Vector4</param>
        /// <returns>A Vector4 with the parsed values</returns>
        /// <exception cref="System.Exception">Thrown when value has invalid format</exception>
        public static Vector4 ParseVector4(JToken value)
        {
            if (value == null)
                throw new System.Exception("Vector4 value cannot be null.");

            // Handle array format [x, y, z, w]
            if (value is JArray array)
            {
                if (array.Count != 4)
                    throw new System.Exception("Vector4 array must have exactly 4 elements [x, y, z, w].");
                
                return new Vector4(
                    (float)array[0],
                    (float)array[1],
                    (float)array[2],
                    (float)array[3]
                );
            }
            
            // Handle object format {"x": float, "y": float, "z": float, "w": float}
            if (value is JObject obj)
            {
                if (!obj.ContainsKey("x") || !obj.ContainsKey("y") || 
                    !obj.ContainsKey("z") || !obj.ContainsKey("w"))
                    throw new System.Exception("Vector4 object must contain 'x', 'y', 'z', and 'w' properties.");
                
                return new Vector4(
                    (float)obj["x"],
                    (float)obj["y"],
                    (float)obj["z"],
                    (float)obj["w"]
                );
            }
            
            throw new System.Exception("Vector4 must be provided as an array [x, y, z, w] or object {\"x\": float, \"y\": float, \"z\": float, \"w\": float}.");
        }

        /// <summary>
        /// Parses a JObject or JArray into a Quaternion
        /// </summary>
        /// <param name="value">JSON value representing a Quaternion</param>
        /// <returns>A Quaternion with the parsed values</returns>
        /// <exception cref="System.Exception">Thrown when value has invalid format</exception>
        public static Quaternion ParseQuaternion(JToken value)
        {
            if (value == null)
                throw new System.Exception("Quaternion value cannot be null.");

            // Handle array format [x, y, z, w]
            if (value is JArray array)
            {
                if (array.Count != 4)
                    throw new System.Exception("Quaternion array must have exactly 4 elements [x, y, z, w].");
                
                return new Quaternion(
                    (float)array[0],
                    (float)array[1],
                    (float)array[2],
                    (float)array[3]
                );
            }
            
            // Handle object format {"x": float, "y": float, "z": float, "w": float}
            if (value is JObject obj)
            {
                if (!obj.ContainsKey("x") || !obj.ContainsKey("y") || 
                    !obj.ContainsKey("z") || !obj.ContainsKey("w"))
                    throw new System.Exception("Quaternion object must contain 'x', 'y', 'z', and 'w' properties.");
                
                return new Quaternion(
                    (float)obj["x"],
                    (float)obj["y"],
                    (float)obj["z"],
                    (float)obj["w"]
                );
            }
            
            throw new System.Exception("Quaternion must be provided as an array [x, y, z, w] or object {\"x\": float, \"y\": float, \"z\": float, \"w\": float}.");
        }

        /// <summary>
        /// Parses a JObject or JArray into a Color
        /// </summary>
        /// <param name="value">JSON value representing a Color</param>
        /// <returns>A Color with the parsed values</returns>
        /// <exception cref="System.Exception">Thrown when value has invalid format</exception>
        public static Color ParseColor(JToken value)
        {
            if (value == null)
                throw new System.Exception("Color value cannot be null.");

            // Handle array format [r, g, b] or [r, g, b, a]
            if (value is JArray array)
            {
                if (array.Count < 3 || array.Count > 4)
                    throw new System.Exception("Color array must have 3 or 4 elements [r, g, b] or [r, g, b, a].");
                
                float r = (float)array[0];
                float g = (float)array[1];
                float b = (float)array[2];
                float a = array.Count > 3 ? (float)array[3] : 1.0f;
                
                return new Color(r, g, b, a);
            }
            
            // Handle object format {"r": float, "g": float, "b": float, "a": float}
            if (value is JObject obj)
            {
                if (!obj.ContainsKey("r") || !obj.ContainsKey("g") || !obj.ContainsKey("b"))
                    throw new System.Exception("Color object must contain 'r', 'g', and 'b' properties.");
                
                float r = (float)obj["r"];
                float g = (float)obj["g"];
                float b = (float)obj["b"];
                float a = obj.ContainsKey("a") ? (float)obj["a"] : 1.0f;
                
                return new Color(r, g, b, a);
            }
            
            throw new System.Exception("Color must be provided as an array [r, g, b] or [r, g, b, a] or object {\"r\": float, \"g\": float, \"b\": float, \"a\": float}.");
        }

        /// <summary>
        /// Parses a JObject or JArray into a Rect
        /// </summary>
        /// <param name="value">JSON value representing a Rect</param>
        /// <returns>A Rect with the parsed values</returns>
        /// <exception cref="System.Exception">Thrown when value has invalid format</exception>
        public static Rect ParseRect(JToken value)
        {
            if (value == null)
                throw new System.Exception("Rect value cannot be null.");

            // Handle array format [x, y, width, height]
            if (value is JArray array)
            {
                if (array.Count != 4)
                    throw new System.Exception("Rect array must have exactly 4 elements [x, y, width, height].");
                
                return new Rect(
                    (float)array[0],
                    (float)array[1],
                    (float)array[2],
                    (float)array[3]
                );
            }
            
            // Handle object format {"x": float, "y": float, "width": float, "height": float}
            if (value is JObject obj)
            {
                if (!obj.ContainsKey("x") || !obj.ContainsKey("y") || 
                    !obj.ContainsKey("width") || !obj.ContainsKey("height"))
                    throw new System.Exception("Rect object must contain 'x', 'y', 'width', and 'height' properties.");
                
                return new Rect(
                    (float)obj["x"],
                    (float)obj["y"],
                    (float)obj["width"],
                    (float)obj["height"]
                );
            }
            
            throw new System.Exception("Rect must be provided as an array [x, y, width, height] or object {\"x\": float, \"y\": float, \"width\": float, \"height\": float}.");
        }

        /// <summary>
        /// Parses a JObject into Bounds
        /// </summary>
        /// <param name="value">JSON value representing Bounds</param>
        /// <returns>Bounds with the parsed values</returns>
        /// <exception cref="System.Exception">Thrown when value has invalid format</exception>
        public static Bounds ParseBounds(JToken value)
        {
            if (value == null)
                throw new System.Exception("Bounds value cannot be null.");
            
            if (!(value is JObject obj))
                throw new System.Exception("Bounds must be provided as an object with 'center' and 'size' properties.");
            
            if (!obj.ContainsKey("center") || !obj.ContainsKey("size"))
                throw new System.Exception("Bounds object must contain 'center' and 'size' properties.");
            
            Vector3 center = ParseVector3(obj["center"]);
            Vector3 size = ParseVector3(obj["size"]);
            
            return new Bounds(center, size);
        }

        /// <summary>
        /// Converts a Unity Vector2 to a JObject
        /// </summary>
        /// <param name="vector2">The Vector2 to convert</param>
        /// <returns>JObject representing the Vector2</returns>
        public static JObject ToJObject(Vector2 vector2)
        {
            return new JObject
            {
                ["x"] = vector2.x,
                ["y"] = vector2.y
            };
        }

        /// <summary>
        /// Converts a Unity Vector3 to a JObject
        /// </summary>
        /// <param name="vector3">The Vector3 to convert</param>
        /// <returns>JObject representing the Vector3</returns>
        public static JObject ToJObject(Vector3 vector3)
        {
            return new JObject
            {
                ["x"] = vector3.x,
                ["y"] = vector3.y,
                ["z"] = vector3.z
            };
        }

        /// <summary>
        /// Converts a Unity Vector4 to a JObject
        /// </summary>
        /// <param name="vector4">The Vector4 to convert</param>
        /// <returns>JObject representing the Vector4</returns>
        public static JObject ToJObject(Vector4 vector4)
        {
            return new JObject
            {
                ["x"] = vector4.x,
                ["y"] = vector4.y,
                ["z"] = vector4.z,
                ["w"] = vector4.w
            };
        }

        /// <summary>
        /// Converts a Unity Quaternion to a JObject
        /// </summary>
        /// <param name="quaternion">The Quaternion to convert</param>
        /// <returns>JObject representing the Quaternion</returns>
        public static JObject ToJObject(Quaternion quaternion)
        {
            return new JObject
            {
                ["x"] = quaternion.x,
                ["y"] = quaternion.y,
                ["z"] = quaternion.z,
                ["w"] = quaternion.w
            };
        }

        /// <summary>
        /// Converts a Unity Color to a JObject
        /// </summary>
        /// <param name="color">The Color to convert</param>
        /// <returns>JObject representing the Color</returns>
        public static JObject ToJObject(Color color)
        {
            return new JObject
            {
                ["r"] = color.r,
                ["g"] = color.g,
                ["b"] = color.b,
                ["a"] = color.a
            };
        }

        /// <summary>
        /// Converts a Unity Rect to a JObject
        /// </summary>
        /// <param name="rect">The Rect to convert</param>
        /// <returns>JObject representing the Rect</returns>
        public static JObject ToJObject(Rect rect)
        {
            return new JObject
            {
                ["x"] = rect.x,
                ["y"] = rect.y,
                ["width"] = rect.width,
                ["height"] = rect.height
            };
        }

        /// <summary>
        /// Converts Unity Bounds to a JObject
        /// </summary>
        /// <param name="bounds">The Bounds to convert</param>
        /// <returns>JObject representing the Bounds</returns>
        public static JObject ToJObject(Bounds bounds)
        {
            return new JObject
            {
                ["center"] = ToJObject(bounds.center),
                ["size"] = ToJObject(bounds.size)
            };
        }
    }
} 