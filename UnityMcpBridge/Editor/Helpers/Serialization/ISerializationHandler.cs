using System;
using System.Collections.Generic;

namespace UnityMcpBridge.Editor.Helpers.Serialization
{
    /// <summary>
    /// Interface for type-specific serialization handlers that convert objects to dictionary representations.
    /// </summary>
    public interface ISerializationHandler
    {
        /// <summary>
        /// The type this handler is responsible for serializing.
        /// </summary>
        Type HandledType { get; }

        /// <summary>
        /// Serializes an object to a dictionary representation.
        /// </summary>
        /// <param name="obj">The object to serialize</param>
        /// <param name="depth">The maximum depth to traverse when serializing nested objects</param>
        /// <returns>A dictionary representation of the object</returns>
        Dictionary<string, object> Serialize(object obj, int depth = 1);
    }
} 