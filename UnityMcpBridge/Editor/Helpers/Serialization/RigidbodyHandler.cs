using System;
using System.Collections.Generic;
using UnityEngine;

namespace UnityMcpBridge.Editor.Helpers.Serialization
{
    /// <summary>
    /// Handler for serializing Unity Rigidbody components.
    /// </summary>
    public class RigidbodyHandler : ISerializationHandler
    {
        /// <summary>
        /// Gets the type handled by this serialization handler.
        /// </summary>
        public Type HandledType => typeof(Rigidbody);

        /// <summary>
        /// Serializes a Rigidbody component into a dictionary representation.
        /// </summary>
        /// <param name="obj">The Rigidbody to serialize</param>
        /// <param name="depth">The maximum depth to traverse (not used for this handler)</param>
        /// <returns>A dictionary containing the Rigidbody's serialized properties</returns>
        public Dictionary<string, object> Serialize(object obj, int depth = 1)
        {
            if (obj == null)
                return null;

            if (!(obj is Rigidbody rigidbody))
                throw new ArgumentException($"Object is not a Rigidbody: {obj.GetType().Name}");

            var result = new Dictionary<string, object>
            {
                // Basic physics properties
                ["mass"] = rigidbody.mass,
                ["drag"] = rigidbody.linearDamping,
                ["angularDrag"] = rigidbody.angularDamping,
                ["useGravity"] = rigidbody.useGravity,
                ["isKinematic"] = rigidbody.isKinematic,
                ["freezeRotation"] = rigidbody.freezeRotation,
                
                // Interpolation and collision detection settings
                ["interpolation"] = rigidbody.interpolation.ToString(),
                ["collisionDetectionMode"] = rigidbody.collisionDetectionMode.ToString(),
                
                // Dynamic state (if rigidbody is active)
                ["velocity"] = SerializeVector3(rigidbody.linearVelocity),
                ["angularVelocity"] = SerializeVector3(rigidbody.angularVelocity),
                ["position"] = SerializeVector3(rigidbody.position),
                ["rotation"] = SerializeQuaternion(rigidbody.rotation),
                
                // Constraints
                ["constraints"] = SerializeConstraints(rigidbody.constraints),
                
                // Center of mass (if not using auto-calculation)
                ["centerOfMass"] = SerializeVector3(rigidbody.centerOfMass),
                ["inertiaTensor"] = SerializeVector3(rigidbody.inertiaTensor),
                ["maxAngularVelocity"] = rigidbody.maxAngularVelocity,
                ["maxDepenetrationVelocity"] = rigidbody.maxDepenetrationVelocity,
                
                // Sleep thresholds
                ["sleepThreshold"] = rigidbody.sleepThreshold,
                ["solverIterations"] = rigidbody.solverIterations,
                ["solverVelocityIterations"] = rigidbody.solverVelocityIterations,
                
                // Detection state
                ["detectCollisions"] = rigidbody.detectCollisions,
                
                // Additional state info
                ["IsSleeping"] = rigidbody.IsSleeping(),
                ["worldCenterOfMass"] = SerializeVector3(rigidbody.worldCenterOfMass)
            };

            return result;
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

        private Dictionary<string, bool> SerializeConstraints(RigidbodyConstraints constraints)
        {
            return new Dictionary<string, bool>
            {
                ["FreezePositionX"] = (constraints & RigidbodyConstraints.FreezePositionX) != 0,
                ["FreezePositionY"] = (constraints & RigidbodyConstraints.FreezePositionY) != 0,
                ["FreezePositionZ"] = (constraints & RigidbodyConstraints.FreezePositionZ) != 0,
                ["FreezeRotationX"] = (constraints & RigidbodyConstraints.FreezeRotationX) != 0,
                ["FreezeRotationY"] = (constraints & RigidbodyConstraints.FreezeRotationY) != 0,
                ["FreezeRotationZ"] = (constraints & RigidbodyConstraints.FreezeRotationZ) != 0,
                ["FreezeAll"] = constraints == RigidbodyConstraints.FreezeAll,
                ["FreezePosition"] = (constraints & RigidbodyConstraints.FreezePosition) == RigidbodyConstraints.FreezePosition,
                ["FreezeRotation"] = (constraints & RigidbodyConstraints.FreezeRotation) == RigidbodyConstraints.FreezeRotation
            };
        }

        #endregion
    }
} 