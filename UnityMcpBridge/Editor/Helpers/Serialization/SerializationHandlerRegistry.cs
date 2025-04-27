using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace UnityMcpBridge.Editor.Helpers.Serialization
{
    /// <summary>
    /// Registry for type-specific serialization handlers.
    /// </summary>
    public static class SerializationHandlerRegistry
    {
        private static readonly Dictionary<Type, ISerializationHandler> _handlers = new Dictionary<Type, ISerializationHandler>();
        private static bool _initialized = false;

        /// <summary>
        /// Initializes the registry with default handlers.
        /// </summary>
        public static void Initialize()
        {
            if (_initialized)
                return;

            // Register built-in handlers
            RegisterHandler(new GameObjectHandler());
            RegisterHandler(new ComponentHandler());
            RegisterHandler(new TransformHandler());
            RegisterHandler(new RigidbodyHandler());
            RegisterHandler(new MeshRendererHandler());
            // Additional handlers will be registered here as they're implemented
            
            _initialized = true;
            Debug.Log("SerializationHandlerRegistry initialized with " + _handlers.Count + " handlers");
        }

        /// <summary>
        /// Registers a serialization handler.
        /// </summary>
        /// <param name="handler">The handler to register</param>
        public static void RegisterHandler(ISerializationHandler handler)
        {
            if (handler == null)
                throw new ArgumentNullException(nameof(handler));

            _handlers[handler.HandledType] = handler;
        }

        /// <summary>
        /// Gets the handler for a specific type.
        /// </summary>
        /// <param name="type">The type to get a handler for</param>
        /// <returns>A serialization handler if one exists, otherwise null</returns>
        public static ISerializationHandler GetHandler(Type type)
        {
            if (type == null)
                throw new ArgumentNullException(nameof(type));

            // Try to get an exact match first
            if (_handlers.TryGetValue(type, out var exactHandler))
                return exactHandler;

            // If no exact match, look for handlers that can handle base types or interfaces
            foreach (var handler in _handlers)
            {
                if (handler.Key.IsAssignableFrom(type))
                    return handler.Value;
            }

            return null;
        }

        /// <summary>
        /// Returns all registered handlers.
        /// </summary>
        /// <returns>A collection of all registered handlers</returns>
        public static IEnumerable<ISerializationHandler> GetAllHandlers()
        {
            return _handlers.Values;
        }

        /// <summary>
        /// Clears all registered handlers.
        /// </summary>
        public static void Clear()
        {
            _handlers.Clear();
            _initialized = false;
        }
    }
} 