using System;
using System.Collections.Generic;
using UnityEngine;

namespace UnityMcpBridge.Editor.Helpers
{
    /// <summary>
    /// A serializable dictionary implementation that can be used in Unity.
    /// Unity cannot serialize standard dictionaries, so this class provides a workaround.
    /// </summary>
    /// <typeparam name="TKey">The key type</typeparam>
    /// <typeparam name="TValue">The value type</typeparam>
    [Serializable]
    public class SerializableDictionary<TKey, TValue> : ISerializationCallbackReceiver
    {
        /// <summary>
        /// The internal dictionary that is not directly serialized.
        /// </summary>
        [NonSerialized]
        public Dictionary<TKey, TValue> Dictionary = new Dictionary<TKey, TValue>();
        
        /// <summary>
        /// Serializable list of keys.
        /// </summary>
        [SerializeField]
        private List<TKey> _keys = new List<TKey>();
        
        /// <summary>
        /// Serializable list of values.
        /// </summary>
        [SerializeField]
        private List<TValue> _values = new List<TValue>();
        
        /// <summary>
        /// Converts the dictionary to a serializable format before serialization occurs.
        /// </summary>
        public void OnBeforeSerialize()
        {
            _keys.Clear();
            _values.Clear();
            
            foreach (var kvp in Dictionary)
            {
                _keys.Add(kvp.Key);
                _values.Add(kvp.Value);
            }
        }
        
        /// <summary>
        /// Restores the dictionary from serialized data after deserialization.
        /// </summary>
        public void OnAfterDeserialize()
        {
            Dictionary.Clear();
            
            for (int i = 0; i < Math.Min(_keys.Count, _values.Count); i++)
            {
                // Handle the case where a key already exists (should not happen, but just to be safe)
                if (!Dictionary.ContainsKey(_keys[i]))
                {
                    Dictionary.Add(_keys[i], _values[i]);
                }
            }
        }
        
        /// <summary>
        /// Adds a key-value pair to the dictionary.
        /// </summary>
        /// <param name="key">The key to add</param>
        /// <param name="value">The value to add</param>
        public void Add(TKey key, TValue value)
        {
            Dictionary.Add(key, value);
        }
        
        /// <summary>
        /// Removes a key-value pair from the dictionary.
        /// </summary>
        /// <param name="key">The key to remove</param>
        /// <returns>True if the key was removed, false otherwise</returns>
        public bool Remove(TKey key)
        {
            return Dictionary.Remove(key);
        }
        
        /// <summary>
        /// Clears all key-value pairs from the dictionary.
        /// </summary>
        public void Clear()
        {
            Dictionary.Clear();
        }
        
        /// <summary>
        /// Gets the value associated with the specified key.
        /// </summary>
        /// <param name="key">The key to get the value for</param>
        /// <param name="value">The value associated with the key, if found</param>
        /// <returns>True if the key was found, false otherwise</returns>
        public bool TryGetValue(TKey key, out TValue value)
        {
            return Dictionary.TryGetValue(key, out value);
        }
        
        /// <summary>
        /// Checks if the dictionary contains the specified key.
        /// </summary>
        /// <param name="key">The key to check for</param>
        /// <returns>True if the key was found, false otherwise</returns>
        public bool ContainsKey(TKey key)
        {
            return Dictionary.ContainsKey(key);
        }
        
        /// <summary>
        /// Gets the number of key-value pairs in the dictionary.
        /// </summary>
        public int Count => Dictionary.Count;
        
        /// <summary>
        /// Gets or sets the value associated with the specified key.
        /// </summary>
        /// <param name="key">The key to get or set the value for</param>
        /// <returns>The value associated with the key</returns>
        public TValue this[TKey key]
        {
            get { return Dictionary[key]; }
            set { Dictionary[key] = value; }
        }
    }
} 