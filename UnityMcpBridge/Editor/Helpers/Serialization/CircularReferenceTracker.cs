using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityObject = UnityEngine.Object;

namespace UnityMcpBridge.Editor.Helpers.Serialization
{
    /// <summary>
    /// Tracks object references during serialization to detect circular references.
    /// </summary>
    public class CircularReferenceTracker
    {
        // Dictionary of object references to their serialization paths
        private readonly Dictionary<object, string> _objectPaths = new Dictionary<object, string>(new ReferenceEqualityComparer());
        
        // Dictionary to store detected circular references (object -> reference path)
        private readonly Dictionary<object, string> _circularReferences = new Dictionary<object, string>(new ReferenceEqualityComparer());
        
        // Track the current path during serialization
        private readonly Stack<string> _currentPath = new Stack<string>();
        
        /// <summary>
        /// Clears all tracked references, resetting the tracker state.
        /// </summary>
        public void Clear()
        {
            _objectPaths.Clear();
            _circularReferences.Clear();
            _currentPath.Clear();
        }
        
        /// <summary>
        /// Enters a new object context during serialization.
        /// </summary>
        /// <param name="pathSegment">The property name or array index being serialized</param>
        /// <returns>The full current path</returns>
        public string EnterContext(string pathSegment)
        {
            _currentPath.Push(pathSegment);
            return GetCurrentPath();
        }
        
        /// <summary>
        /// Exits the current object context during serialization.
        /// </summary>
        public void ExitContext()
        {
            if (_currentPath.Count > 0)
            {
                _currentPath.Pop();
            }
        }
        
        /// <summary>
        /// Gets the current serialization path.
        /// </summary>
        /// <returns>A string representing the current path (e.g., "root.gameObject.transform")</returns>
        public string GetCurrentPath()
        {
            if (_currentPath.Count == 0)
            {
                return "root";
            }
            
            var path = string.Join(".", _currentPath.Reverse());
            return path;
        }
        
        /// <summary>
        /// Adds an object to be tracked for circular references.
        /// </summary>
        /// <param name="obj">The object to track</param>
        /// <returns>True if the object is being referenced for the first time, false if it's a circular reference</returns>
        public bool AddReference(object obj)
        {
            // Don't track null or value types (they can't create cycles)
            if (obj == null || (obj.GetType().IsValueType && !(obj is UnityObject)))
            {
                return true;
            }
            
            string currentPath = GetCurrentPath();
            
            // If we've seen this object before, we have a circular reference
            if (_objectPaths.TryGetValue(obj, out string existingPath))
            {
                _circularReferences[obj] = existingPath;
                return false;
            }
            
            // First time seeing this object, record its path
            _objectPaths[obj] = currentPath;
            return true;
        }
        
        /// <summary>
        /// Checks if an object creates a circular reference.
        /// </summary>
        /// <param name="obj">The object to check</param>
        /// <returns>True if the object creates a circular reference, false otherwise</returns>
        public bool IsCircularReference(object obj)
        {
            // Null and value types can't create cycles
            if (obj == null || (obj.GetType().IsValueType && !(obj is UnityObject)))
            {
                return false;
            }
            
            return _circularReferences.ContainsKey(obj);
        }
        
        /// <summary>
        /// Gets the reference path for a circular reference.
        /// </summary>
        /// <param name="obj">The object to get the reference path for</param>
        /// <returns>The path to the first occurrence of the object in the serialization graph, or null if not a circular reference</returns>
        public string GetReferencePath(object obj)
        {
            // Return null for null objects
            if (obj == null)
            {
                return null;
            }
            
            // Check if this is a known circular reference
            if (_circularReferences.TryGetValue(obj, out string path))
            {
                return path;
            }
            
            return null;
        }
    }
    
    /// <summary>
    /// Custom equality comparer for reference-based equality rather than value-based equality.
    /// </summary>
    internal class ReferenceEqualityComparer : IEqualityComparer<object>
    {
        public new bool Equals(object x, object y)
        {
            return ReferenceEquals(x, y);
        }
        
        public int GetHashCode(object obj)
        {
            if (obj == null) return 0;
            
            // For Unity Objects, use instance ID for more reliable hashing
            if (obj is UnityObject unityObj)
            {
                return unityObj.GetInstanceID();
            }
            
            return System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(obj);
        }
    }
} 