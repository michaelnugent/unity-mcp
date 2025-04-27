using System.Collections.Generic;
using UnityEngine;
using UnityObject = UnityEngine.Object;

namespace UnityMcpBridge.Editor.Helpers
{
    /// <summary>
    /// Extension methods for serialization operations.
    /// </summary>
    public static class SerializationExtensions
    {
        /// <summary>
        /// Safely serializes an object to JSON with fallback representation when needed.
        /// </summary>
        /// <param name="obj">The object to serialize</param>
        /// <param name="depth">The depth of serialization to perform</param>
        /// <param name="prettyPrint">Whether to format the JSON with indentation</param>
        /// <returns>A JSON string representation of the object</returns>
        public static string ToSafeJson(this object obj, 
            SerializationHelper.SerializationDepth depth = SerializationHelper.SerializationDepth.Standard, 
            bool prettyPrint = true)
        {
            return SerializationHelper.SafeSerializeToJson(obj, depth, prettyPrint);
        }

        /// <summary>
        /// Converts a regular Dictionary to a SerializableDictionary.
        /// </summary>
        /// <typeparam name="TKey">The key type</typeparam>
        /// <typeparam name="TValue">The value type</typeparam>
        /// <param name="dict">The dictionary to convert</param>
        /// <returns>A new SerializableDictionary containing the same key-value pairs</returns>
        public static SerializableDictionary<TKey, TValue> ToSerializable<TKey, TValue>(
            this Dictionary<TKey, TValue> dict)
        {
            var serializableDict = new SerializableDictionary<TKey, TValue>();
            
            if (dict != null)
            {
                foreach (var kvp in dict)
                {
                    serializableDict.Add(kvp.Key, kvp.Value);
                }
            }
            
            return serializableDict;
        }

        /// <summary>
        /// Gets a fallback representation of a Unity object with key properties.
        /// </summary>
        /// <param name="unityObject">The Unity object to get a representation for</param>
        /// <param name="depth">The depth of serialization to perform</param>
        /// <returns>A dictionary containing key properties of the object</returns>
        public static Dictionary<string, object> GetFallbackRepresentation(
            this UnityObject unityObject,
            SerializationHelper.SerializationDepth depth = SerializationHelper.SerializationDepth.Standard)
        {
            return SerializationHelper.CreateFallbackRepresentation(unityObject, depth);
        }

        /// <summary>
        /// Checks if an object can be directly serialized by Unity's JsonUtility.
        /// </summary>
        /// <param name="obj">The object to check</param>
        /// <returns>True if the object can be directly serialized, false otherwise</returns>
        public static bool IsDirectlySerializable(this object obj)
        {
            return SerializationHelper.IsDirectlySerializable(obj);
        }
    }
} 