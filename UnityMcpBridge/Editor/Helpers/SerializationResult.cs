using System;
using System.Collections.Generic;

namespace UnityMcpBridge.Editor.Helpers
{
    /// <summary>
    /// Contains the result of a serialization operation, including metadata about the serialization process.
    /// </summary>
    /// <typeparam name="T">The type of data being serialized</typeparam>
    [Serializable]
    public class SerializationResult<T>
    {
        /// <summary>
        /// Whether the object was fully serialized or required fallback representation.
        /// </summary>
        public bool WasFullySerialized;
        
        /// <summary>
        /// Error message if serialization encountered issues.
        /// </summary>
        public string ErrorMessage;
        
        /// <summary>
        /// The full type name of the object being serialized.
        /// </summary>
        public string ObjectTypeName;
        
        /// <summary>
        /// The instance ID of the Unity object, if applicable.
        /// </summary>
        public int? InstanceID;
        
        /// <summary>
        /// The serialized data if directly serializable.
        /// </summary>
        public T Data;
        
        /// <summary>
        /// Additional properties gathered through reflection when direct serialization is not possible.
        /// </summary>
        public Dictionary<string, object> IntrospectedProperties;
    }
} 