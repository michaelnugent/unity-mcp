using System;
using System.Collections.Generic;
using UnityEngine;

namespace UnityMcpBridge.Editor.Helpers.Serialization
{
    /// <summary>
    /// Handler for serializing Unity MeshRenderer components.
    /// </summary>
    public class MeshRendererHandler : ISerializationHandler
    {
        /// <summary>
        /// Gets the type handled by this serialization handler.
        /// </summary>
        public Type HandledType => typeof(MeshRenderer);

        /// <summary>
        /// Serializes a MeshRenderer component into a dictionary representation.
        /// </summary>
        /// <param name="obj">The MeshRenderer to serialize</param>
        /// <param name="depth">The maximum depth to traverse (not used for this handler)</param>
        /// <returns>A dictionary containing the MeshRenderer's serialized properties</returns>
        public Dictionary<string, object> Serialize(object obj, int depth = 1)
        {
            if (obj == null)
                return null;

            if (!(obj is MeshRenderer renderer))
                throw new ArgumentException($"Object is not a MeshRenderer: {obj.GetType().Name}");

            var result = new Dictionary<string, object>
            {
                // Renderer base properties
                ["enabled"] = renderer.enabled,
                ["shadowCastingMode"] = renderer.shadowCastingMode.ToString(),
                ["receiveShadows"] = renderer.receiveShadows,
                ["lightProbeUsage"] = renderer.lightProbeUsage.ToString(),
                ["reflectionProbeUsage"] = renderer.reflectionProbeUsage.ToString(),
                ["rendererPriority"] = renderer.rendererPriority,
                ["renderingLayerMask"] = renderer.renderingLayerMask,
                ["sortingLayerID"] = renderer.sortingLayerID,
                ["sortingLayerName"] = renderer.sortingLayerName,
                ["sortingOrder"] = renderer.sortingOrder,
                ["allowOcclusionWhenDynamic"] = renderer.allowOcclusionWhenDynamic,
                
                // Material properties
                ["materials"] = SerializeMaterials(renderer.materials),
                ["sharedMaterials"] = SerializeMaterials(renderer.sharedMaterials),
                
                // MeshRenderer specific properties
                ["additionalVertexStreams"] = renderer.additionalVertexStreams != null ? 
                    renderer.additionalVertexStreams.name : null,
                ["subMeshStartIndex"] = renderer.subMeshStartIndex,
                
                // Material properties block exists check
                ["hasMaterialPropertyBlock"] = renderer.HasPropertyBlock(),
                
                // Bounds information
                ["bounds"] = SerializeBounds(renderer.bounds),
                ["localBounds"] = SerializeBounds(renderer.localBounds)
            };

            return result;
        }

        #region Type Serialization Helpers

        private List<Dictionary<string, object>> SerializeMaterials(Material[] materials)
        {
            if (materials == null || materials.Length == 0)
                return null;
                
            var materialsList = new List<Dictionary<string, object>>();
            
            foreach (var material in materials)
            {
                if (material == null)
                {
                    materialsList.Add(null);
                    continue;
                }
                
                materialsList.Add(new Dictionary<string, object>
                {
                    ["name"] = material.name,
                    ["shader"] = material.shader != null ? material.shader.name : null,
                    ["color"] = material.HasProperty("_Color") ? SerializeColor(material.color) : null,
                    ["mainTexture"] = material.mainTexture != null ? material.mainTexture.name : null,
                    ["renderQueue"] = material.renderQueue,
                    ["enableInstancing"] = material.enableInstancing,
                    ["doubleSidedGI"] = material.doubleSidedGI,
                    ["globalIlluminationFlags"] = material.globalIlluminationFlags.ToString()
                });
            }
            
            return materialsList;
        }
        
        private Dictionary<string, float> SerializeColor(Color color)
        {
            return new Dictionary<string, float>
            {
                ["r"] = color.r,
                ["g"] = color.g,
                ["b"] = color.b,
                ["a"] = color.a
            };
        }
        
        private Dictionary<string, object> SerializeBounds(Bounds bounds)
        {
            return new Dictionary<string, object>
            {
                ["center"] = SerializeVector3(bounds.center),
                ["size"] = SerializeVector3(bounds.size),
                ["min"] = SerializeVector3(bounds.min),
                ["max"] = SerializeVector3(bounds.max)
            };
        }
        
        private Dictionary<string, float> SerializeVector3(Vector3 vector)
        {
            return new Dictionary<string, float>
            {
                ["x"] = vector.x,
                ["y"] = vector.y,
                ["z"] = vector.z
            };
        }

        #endregion
    }
} 