using UnityEngine;
using UnityMcpBridge.Editor.Helpers;
using UnityMcpBridge.Editor.Helpers.Serialization;

namespace UnityMcpBridge.Editor.Tools.ManageGameObjectImpl
{
    /// <summary>
    /// Provides a simplified interface to the GameObject and Component serialization system.
    /// Part of the ManageGameObject tool's internal implementation.
    /// </summary>
    internal static class GameObjectSerializer
    {
        private static readonly GameObjectHandler _gameObjectHandler = new GameObjectHandler();
        private static readonly ComponentHandler _componentHandler = new ComponentHandler();

        /// <summary>
        /// Creates a serializable representation of a GameObject.
        /// </summary>
        public static object GetGameObjectData(GameObject go)
        {
            if (go == null)
                return null;
                
            // Use the serialization handler to consistently serialize GameObjects
            return _gameObjectHandler.Serialize(go, SerializationHelper.SerializationDepth.Standard);
        }

        /// <summary>
        /// Creates a serializable representation of a Component.
        /// </summary>
        public static object GetComponentData(Component c)
        {
            if (c == null)
                return null;
                
            // Use the serialization handler to consistently serialize Components
            return _componentHandler.Serialize(c, SerializationHelper.SerializationDepth.Standard);
        }

        /// <summary>
        /// Gets the full hierarchical path of a Transform.
        /// </summary>
        /// <remarks>
        /// This method now delegates to the GameObjectHandler's GetHierarchyPath method
        /// </remarks>
        public static string GetFullPath(Transform transform)
        {
            if (transform == null)
                return string.Empty;
                
            var gameObject = transform.gameObject;
            return _gameObjectHandler.GetHierarchyPath(gameObject);
        }
    }
} 