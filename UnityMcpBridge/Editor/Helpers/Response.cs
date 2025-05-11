using System;
using System.Collections.Generic;
using UnityEngine;

namespace UnityMcpBridge.Editor.Helpers
{
    /// <summary>
    /// Provides static methods for creating standardized success and error response objects.
    /// Ensures consistent JSON structure for communication back to the Python server.
    /// </summary>
    public static class Response
    {
        /// <summary>
        /// Creates a standardized success response object.
        /// </summary>
        /// <param name="message">A message describing the successful operation.</param>
        /// <param name="data">Optional additional data to include in the response.</param>
        /// <param name="serializationDepth">The depth level for serialization of complex objects.</param>
        /// <returns>An object representing the success response.</returns>
        public static object Success(string message, object data = null, SerializationHelper.SerializationDepth serializationDepth = SerializationHelper.SerializationDepth.Standard)
        {
            if (data != null)
            {
                // Create a result object with serialized data
                var serializedData = SerializeResponseData(data, serializationDepth);
                
                return new
                {
                    success = true,
                    message = message,
                    data = serializedData,
                };
            }
            else
            {
                return new { success = true, message = message };
            }
        }

        /// <summary>
        /// Creates a standardized warning response object for partially successful operations.
        /// </summary>
        /// <param name="warningMessage">A message describing the warning or partial success.</param>
        /// <param name="data">Optional additional data to include in the response.</param>
        /// <param name="serializationDepth">The depth level for serialization of complex objects.</param>
        /// <returns>An object representing the warning response.</returns>
        public static object Warning(string warningMessage, object data = null, SerializationHelper.SerializationDepth serializationDepth = SerializationHelper.SerializationDepth.Standard)
        {
            if (data != null)
            {
                // Create a result object with serialized data
                var serializedData = SerializeResponseData(data, serializationDepth);
                
                return new
                {
                    success = true,
                    warning = warningMessage,
                    data = serializedData,
                };
            }
            else
            {
                return new { success = true, warning = warningMessage };
            }
        }

        /// <summary>
        /// Creates a standardized error response object.
        /// </summary>
        /// <param name="errorMessage">A message describing the error.</param>
        /// <param name="data">Optional additional data (e.g., error details) to include.</param>
        /// <param name="serializationDepth">The depth level for serialization of complex objects.</param>
        /// <returns>An object representing the error response.</returns>
        public static object Error(string errorMessage, object data = null, SerializationHelper.SerializationDepth serializationDepth = SerializationHelper.SerializationDepth.Standard)
        {
            if (data != null)
            {
                // Create a result object with serialized data
                var serializedData = SerializeResponseData(data, serializationDepth);
                
                // Note: The key is "error" for error messages, not "message"
                return new
                {
                    success = false,
                    error = errorMessage,
                    data = serializedData,
                };
            }
            else
            {
                return new { success = false, error = errorMessage };
            }
        }
        
        /// <summary>
        /// Serializes response data using the enhanced serialization system.
        /// </summary>
        /// <param name="data">The data to serialize.</param>
        /// <param name="depth">The serialization depth to use.</param>
        /// <returns>The serialized data object.</returns>
        private static object SerializeResponseData(object data, SerializationHelper.SerializationDepth depth)
        {
            if (data == null)
                return null;
                
            try
            {
                // For primitive types and strings, return as is
                if (data is string || data is bool || data.GetType().IsPrimitive)
                    return data;
                    
                // For collections that contain serializable objects, we'll let
                // the JSON serializer handle them directly for now
                
                // For complex types, use our enhanced serialization
                return SerializationHelper.CreateSerializationResult(data, depth);
            }
            catch (Exception ex)
            {
                Debug.LogWarning($"Error serializing response data: {ex.Message}");
                return new { 
                    __serialization_error = true, 
                    __error_message = ex.Message,
                    __original_type = data.GetType().FullName
                };
            }
        }
    }
}

