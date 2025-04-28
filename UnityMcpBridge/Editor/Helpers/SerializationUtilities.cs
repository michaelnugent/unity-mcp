using System;
using System.Collections.Generic;
using UnityEngine;
using UnityMcpBridge.Editor.Models;
using UnityObject = UnityEngine.Object;

namespace UnityMcpBridge.Editor.Helpers
{
    /// <summary>
    /// Bridge-specific serialization utilities optimized for the Unity MCP Bridge.
    /// Provides helper methods for common serialization tasks in the context of the bridge tools.
    /// </summary>
    public static class SerializationUtilities
    {
        // Cache the config instance reference for faster access
        private static McpConfig _configCache;
        
        /// <summary>
        /// Gets the configured serialization depth for a specific command.
        /// </summary>
        /// <param name="commandName">The command name to get the depth for.</param>
        /// <returns>The configured serialization depth.</returns>
        public static SerializationHelper.SerializationDepth GetSerializationDepthForCommand(string commandName)
        {
            // Get or initialize the config cache
            if (_configCache == null)
            {
                // Create a default config if we can't access the actual one
                _configCache = new McpConfig();
            }
            
            // If serialization config is null, initialize with defaults
            if (_configCache.serialization == null)
            {
                _configCache.serialization = new SerializationConfig();
            }
            
            // Get the depth from the command overrides or default
            return _configCache.serialization.commandOverrides.GetDepthForCommand(commandName);
        }
        
        /// <summary>
        /// Serializes a response for a specific command, using the configured serialization depth.
        /// </summary>
        /// <param name="commandName">The command name for which to create the response.</param>
        /// <param name="message">A success message.</param>
        /// <param name="data">The data to include in the response.</param>
        /// <returns>A standardized success response.</returns>
        public static object SerializeResponse(string commandName, string message, object data = null)
        {
            var depth = GetSerializationDepthForCommand(commandName);
            return Response.Success(message, data, depth);
        }
        
        /// <summary>
        /// Serializes an error response for a specific command, using the configured serialization depth.
        /// </summary>
        /// <param name="commandName">The command name for which to create the error response.</param>
        /// <param name="errorMessage">An error message.</param>
        /// <param name="data">Optional error data to include.</param>
        /// <returns>A standardized error response.</returns>
        public static object SerializeErrorResponse(string commandName, string errorMessage, object data = null)
        {
            var depth = GetSerializationDepthForCommand(commandName);
            return Response.Error(errorMessage, data, depth);
        }
        
        /// <summary>
        /// Creates a serialized representation of a GameObject with the appropriate depth.
        /// </summary>
        /// <param name="gameObject">The GameObject to serialize.</param>
        /// <param name="commandName">The command context for determining serialization depth.</param>
        /// <returns>A serialized representation of the GameObject.</returns>
        public static object SerializeGameObject(GameObject gameObject, string commandName)
        {
            if (gameObject == null)
                return null;
                
            var depth = GetSerializationDepthForCommand(commandName);
            return SerializationHelper.CreateSerializationResult(gameObject, depth).Data;
        }
        
        /// <summary>
        /// Creates a serialized representation of a Component with the appropriate depth.
        /// </summary>
        /// <param name="component">The Component to serialize.</param>
        /// <param name="commandName">The command context for determining serialization depth.</param>
        /// <returns>A serialized representation of the Component.</returns>
        public static object SerializeComponent(Component component, string commandName)
        {
            if (component == null)
                return null;
                
            var depth = GetSerializationDepthForCommand(commandName);
            return SerializationHelper.CreateSerializationResult(component, depth).Data;
        }
        
        /// <summary>
        /// Creates a serialized representation of a collection of Unity objects with the appropriate depth.
        /// </summary>
        /// <param name="objects">The objects to serialize.</param>
        /// <param name="commandName">The command context for determining serialization depth.</param>
        /// <returns>A list of serialized representations of the objects.</returns>
        public static List<object> SerializeUnityObjects(IEnumerable<UnityObject> objects, string commandName)
        {
            if (objects == null)
                return new List<object>();
                
            var result = new List<object>();
            var depth = GetSerializationDepthForCommand(commandName);
            
            foreach (var obj in objects)
            {
                if (obj == null)
                    continue;
                    
                result.Add(SerializationHelper.CreateSerializationResult(obj, depth).Data);
            }
            
            return result;
        }
    }
} 