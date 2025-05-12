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
        
        /// <summary>
        /// Whether this object is a circular reference to another object in the object graph.
        /// </summary>
        public bool IsCircularReference;
        
        /// <summary>
        /// The path to the original instance of this object in the serialization graph.
        /// Only present if IsCircularReference is true.
        /// </summary>
        public string CircularReferencePath;
        
        /// <summary>
        /// Status of the serialization process. Helps LLMs understand what happened during serialization.
        /// </summary>
        public string __serialization_status;
        
        /// <summary>
        /// Detailed error information if serialization encountered problems.
        /// </summary>
        public string __serialization_error;
        
        /// <summary>
        /// The depth level used for this serialization.
        /// </summary>
        public string __serialization_depth;
        
        /// <summary>
        /// List of successfully serialized properties.
        /// </summary>
        public List<string> __serialized_properties;
        
        /// <summary>
        /// List of properties that could not be serialized.
        /// </summary>
        public List<string> __failed_properties;
        
        /// <summary>
        /// Object identifier that can be used to uniquely reference this object.
        /// </summary>
        public string __object_id;
        
        /// <summary>
        /// Assembly qualified name of the object type for more precise type information.
        /// </summary>
        public string __assembly_qualified_name;
        
        /// <summary>
        /// Names of interfaces implemented by this object type.
        /// </summary>
        public List<string> __implemented_interfaces;
        
        /// <summary>
        /// Base type information for class hierarchy understanding.
        /// </summary>
        public string __base_type;

        public override string ToString()
        {
            string return_value = "ObjectTypeName: " + ObjectTypeName + "\n";
            // all fields in detail
            // string return_value = $"SerializationResult<{typeof(T).Name}>: {Data}";
            // return_value += $"\nWasFullySerialized: {WasFullySerialized}";
            // return_value += $"\nErrorMessage: {ErrorMessage}";
            // return_value += $"\nObjectTypeName: {ObjectTypeName}";
            // return_value += $"\nInstanceID: {InstanceID}";
            // return_value += $"\nData: {Data}";
            // return_value += $"\nIsCircularReference: {IsCircularReference}";
            // return_value += $"\nCircularReferencePath: {CircularReferencePath}";
            // return_value += $"\n__serialization_status: {__serialization_status}";
            // return_value += $"\n__serialization_error: {__serialization_error}";
            // return_value += $"\n__serialization_depth: {__serialization_depth}";
            // return_value += $"\n__serialized_properties: {__serialized_properties}";
            // return_value += $"\n__failed_properties: {__failed_properties}";
            // return_value += $"\n__object_id: {__object_id}";
            // return_value += $"\n__assembly_qualified_name: {__assembly_qualified_name}";
            // return_value += $"\n__implemented_interfaces: {__implemented_interfaces}";
            // return_value += $"\n__base_type: {__base_type}";

            // string introspectedProperties = "";
            // foreach (var property in IntrospectedProperties)
            // {
            //     introspectedProperties += $"\n{property.Key}: {property.Value}";
            // }
            // return_value += $"\nIntrospectedProperties: {introspectedProperties}";
            return return_value;
        }
    }
} 