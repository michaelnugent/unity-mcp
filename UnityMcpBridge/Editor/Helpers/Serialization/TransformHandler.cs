using System;
using System.Collections.Generic;
using UnityEngine;

namespace UnityMcpBridge.Editor.Helpers.Serialization
{
    /// <summary>
    /// Handler for serializing Unity Transform objects.
    /// </summary>
    public class TransformHandler : ISerializationHandler
    {
        /// <summary>
        /// Gets the type handled by this serialization handler.
        /// </summary>
        public Type HandledType => typeof(Transform);

        /// <summary>
        /// Serializes a Transform object into a dictionary representation.
        /// </summary>
        /// <param name="obj">The Transform to serialize</param>
        /// <param name="depth">The maximum depth to traverse when serializing nested objects</param>
        /// <returns>A dictionary containing the Transform's serialized properties</returns>
        public Dictionary<string, object> Serialize(object obj, int depth = 1)
        {
            if (obj == null)
                return null;

            if (!(obj is Transform transform))
                throw new ArgumentException($"Object is not a Transform: {obj.GetType().Name}");

            var result = new Dictionary<string, object>();

            // Local position, rotation, and scale
            result["localPosition"] = SerializeVector3(transform.localPosition);
            result["localRotation"] = SerializeQuaternion(transform.localRotation);
            result["localEulerAngles"] = SerializeVector3(transform.localEulerAngles);
            result["localScale"] = SerializeVector3(transform.localScale);

            // World position, rotation
            result["position"] = SerializeVector3(transform.position);
            result["rotation"] = SerializeQuaternion(transform.rotation);
            result["eulerAngles"] = SerializeVector3(transform.eulerAngles);

            // Parent information
            if (transform.parent != null)
            {
                result["hasParent"] = true;
                result["parentName"] = transform.parent.name;
                
                if (depth > 0)
                {
                    try
                    {
                        result["parent"] = new Dictionary<string, object>
                        {
                            ["name"] = transform.parent.name,
                            ["instanceID"] = transform.parent.gameObject.GetInstanceID()
                        };
                    }
                    catch
                    {
                        // Ignore any exceptions when trying to get parent data
                    }
                }
            }
            else
            {
                result["hasParent"] = false;
            }

            // Child count
            result["childCount"] = transform.childCount;

            // Serialize children if depth allows
            if (depth > 0 && transform.childCount > 0)
            {
                var children = new List<Dictionary<string, object>>();
                
                for (int i = 0; i < transform.childCount; i++)
                {
                    var child = transform.GetChild(i);
                    
                    // For each child, add minimal info at this level
                    var childData = new Dictionary<string, object>
                    {
                        ["name"] = child.name,
                        ["index"] = i,
                        ["instanceID"] = child.gameObject.GetInstanceID()
                    };
                    
                    // Only go deeper if we have more depth available
                    if (depth > 1)
                    {
                        childData = Serialize(child, depth - 1);
                    }
                    
                    children.Add(childData);
                }
                
                result["children"] = children;
            }

            // Add hierarchy path
            result["hierarchyPath"] = GetTransformPath(transform);
            
            // Add sibling index
            result["siblingIndex"] = transform.GetSiblingIndex();

            // Add lossyScale (global scale)
            result["lossyScale"] = SerializeVector3(transform.lossyScale);

            return result;
        }

        /// <summary>
        /// Gets the full hierarchy path of the transform
        /// </summary>
        /// <param name="transform">The transform to get the path for</param>
        /// <returns>The full path string</returns>
        private string GetTransformPath(Transform transform)
        {
            if (transform.parent == null)
                return transform.name;
                
            return GetTransformPath(transform.parent) + "/" + transform.name;
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