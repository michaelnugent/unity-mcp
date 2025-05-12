using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace UnityMcpBridge.Editor.Helpers.Serialization
{
    /// <summary>
    /// Handler for serializing Unity GameObject objects.
    /// </summary>
    public class GameObjectHandler : ISerializationHandler
    {
        /// <summary>
        /// Gets the type handled by this serialization handler.
        /// </summary>
        public Type HandledType => typeof(GameObject);

        /// <summary>
        /// Serializes a GameObject object into a dictionary representation.
        /// </summary>
        /// <param name="obj">The GameObject to serialize</param>
        /// <param name="depth">The serialization depth to use</param>
        /// <returns>A dictionary containing the GameObject's serialized properties</returns>
        public Dictionary<string, object> Serialize(object obj, SerializationHelper.SerializationDepth depth = SerializationHelper.SerializationDepth.Standard)
        {
            if (obj == null)
                return null;

            if (!(obj is GameObject gameObject))
                throw new ArgumentException($"Object is not a GameObject: {obj.GetType().Name}");

            var result = new Dictionary<string, object>
            {
                ["name"] = gameObject.name,
                ["active"] = gameObject.activeSelf,
                ["tag"] = gameObject.tag,
                ["layer"] = gameObject.layer,
                ["layerName"] = LayerMask.LayerToName(gameObject.layer),
                ["instanceID"] = gameObject.GetInstanceID(),
                ["isStatic"] = gameObject.isStatic,
                ["__type"] = typeof(GameObject).FullName,
                ["__unity_type"] = typeof(GameObject).FullName,
                ["__object_id"] = gameObject.GetInstanceID().ToString(),
                ["hierarchyPath"] = GetHierarchyPath(gameObject)
            };

            // Add transform data (position, rotation, scale) for all depth levels
            result["transform"] = SerializeTransform(gameObject.transform);

            // For Basic depth, we're done here
            if (depth == SerializationHelper.SerializationDepth.Basic)
            {
                return result;
            }

            // Add component data for Standard and Deep depths
            SerializeComponents(gameObject, result, depth);

            // Add children data for Standard and Deep depths
            // For Standard depth, we include minimal child info
            // For Deep depth, we recursively serialize all children
            SerializeChildren(gameObject, result, depth);

            return result;
        }

        /// <summary>
        /// Gets the full hierarchy path for a GameObject.
        /// </summary>
        public string GetHierarchyPath(GameObject gameObject)
        {
            var transform = gameObject.transform;
            string path = gameObject.name;
            
            while (transform.parent != null)
            {
                transform = transform.parent;
                path = transform.name + "/" + path;
            }
            
            return path;
        }

        /// <summary>
        /// Serializes a Transform component into a dictionary.
        /// </summary>
        /// <param name="transform">The transform to serialize</param>
        /// <returns>A dictionary containing transform data</returns>
        private Dictionary<string, object> SerializeTransform(Transform transform)
        {
            var result = new Dictionary<string, object>();

            // Local position/rotation/scale
            result["localPosition"] = SerializeVector3(transform.localPosition);
            result["localRotation"] = SerializeQuaternion(transform.localRotation);
            result["localEulerAngles"] = SerializeVector3(transform.localEulerAngles);
            result["localScale"] = SerializeVector3(transform.localScale);

            // World position/rotation
            result["position"] = SerializeVector3(transform.position);
            result["rotation"] = SerializeQuaternion(transform.rotation);
            result["eulerAngles"] = SerializeVector3(transform.eulerAngles);

            // Other transform properties
            result["childCount"] = transform.childCount;
            
            // Parent name (if any)
            if (transform.parent != null)
            {
                result["parentName"] = transform.parent.name;
                result["parentID"] = transform.parent.gameObject.GetInstanceID();
            }

            return result;
        }

        /// <summary>
        /// Serializes the components of a GameObject.
        /// </summary>
        /// <param name="gameObject">The GameObject containing the components</param>
        /// <param name="result">The dictionary to add component data to</param>
        /// <param name="depth">The serialization depth to use</param>
        private void SerializeComponents(GameObject gameObject, Dictionary<string, object> result, SerializationHelper.SerializationDepth depth)
        {
            var components = gameObject.GetComponents<Component>();
            var componentData = new List<Dictionary<string, object>>();

            var componentHandler = new ComponentHandler();

            foreach (var component in components)
            {
                // Skip null components (can happen if scripts are missing)
                if (component == null)
                    continue;

                // Skip Transform as it's already handled separately
                if (component is Transform)
                    continue;

                try
                {
                    // For Standard depth, use reduced depth for components
                    var componentDepth = depth == SerializationHelper.SerializationDepth.Deep 
                        ? depth 
                        : SerializationHelper.SerializationDepth.Basic;
                    
                    var serializedComponent = componentHandler.Serialize(component, componentDepth);
                    if (serializedComponent != null)
                    {
                        componentData.Add(serializedComponent);
                    }
                }
                catch (Exception)
                {
                    // Skip components that can't be serialized
                    continue;
                }
            }

            result["components"] = componentData;
        }

        /// <summary>
        /// Serializes the children of a GameObject.
        /// </summary>
        /// <param name="gameObject">The GameObject containing the children</param>
        /// <param name="result">The dictionary to add children data to</param>
        /// <param name="depth">The serialization depth to use</param>
        private void SerializeChildren(GameObject gameObject, Dictionary<string, object> result, SerializationHelper.SerializationDepth depth)
        {
            var transform = gameObject.transform;
            
            if (transform.childCount == 0)
                return;

            var childrenData = new List<Dictionary<string, object>>();

            for (int i = 0; i < transform.childCount; i++)
            {
                var childTransform = transform.GetChild(i);
                var childGameObject = childTransform.gameObject;

                Dictionary<string, object> childData;
                
                if (depth == SerializationHelper.SerializationDepth.Deep)
                {
                    // For Deep depth, fully serialize child
                    childData = Serialize(childGameObject, SerializationHelper.SerializationDepth.Standard);
                }
                else
                {
                    // For Standard depth, create minimal data
                    childData = new Dictionary<string, object>
                    {
                        ["name"] = childGameObject.name,
                        ["active"] = childGameObject.activeSelf,
                        ["tag"] = childGameObject.tag,
                        ["instanceID"] = childGameObject.GetInstanceID(),
                        ["__type"] = typeof(GameObject).FullName,
                        ["childCount"] = childTransform.childCount
                    };
                }

                childrenData.Add(childData);
            }

            result["children"] = childrenData;
        }

        #region Type Serialization Helpers

        private Dictionary<string, float> SerializeVector3(Vector3 vector)
        {
            return new Dictionary<string, float>
            {
                ["x"] = vector.x,
                ["y"] = vector.y,
                ["z"] = vector.z
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

        #endregion
    }
} 