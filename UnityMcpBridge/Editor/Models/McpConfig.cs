using System;
using Newtonsoft.Json;
using UnityMcpBridge.Editor.Helpers;

namespace UnityMcpBridge.Editor.Models
{
    [Serializable]
    public class McpConfig
    {
        [JsonProperty("mcpServers")]
        public McpConfigServers mcpServers;
        
        [JsonProperty("serialization")]
        public SerializationConfig serialization;
        
        public McpConfig()
        {
            // Set default values
            serialization = new SerializationConfig();
        }
    }
    
    [Serializable]
    public class SerializationConfig
    {
        [JsonProperty("defaultDepth")]
        public string defaultDepth = "Standard";
        
        [JsonProperty("commandOverrides")]
        public CommandSerializationOverrides commandOverrides = new CommandSerializationOverrides();
        
        public SerializationHelper.SerializationDepth GetDefaultDepth()
        {
            // Parse the string value to the enum, default to Standard if parsing fails
            if (Enum.TryParse<SerializationHelper.SerializationDepth>(defaultDepth, true, out var result))
            {
                return result;
            }
            return SerializationHelper.SerializationDepth.Standard;
        }
    }
    
    [Serializable]
    public class CommandSerializationOverrides
    {
        // Define overrides for specific commands that need different serialization depths
        [JsonProperty("manage_scene")]
        public string manageScene = "Deep";
        
        [JsonProperty("manage_gameobject")]
        public string manageGameObject = "Deep";
        
        [JsonProperty("manage_prefabs")]
        public string managePrefabs = "Deep";
        
        [JsonProperty("manage_asset")]
        public string manageAsset = "Standard";
        
        // Helper method to get serialization depth for a command
        public SerializationHelper.SerializationDepth GetDepthForCommand(string commandName)
        {
            // This could be implemented with reflection to be more dynamic
            // but for simplicity, we'll use a switch statement
            switch (commandName.ToLower())
            {
                case "manage_scene":
                case "handlemanagescene":
                    return ParseDepth(manageScene);
                    
                case "manage_gameobject":
                case "handlemanagegameobject":
                    return ParseDepth(manageGameObject);
                    
                case "manage_prefabs":
                case "handlemanageprefabs":
                    return ParseDepth(managePrefabs);
                    
                case "manage_asset":
                case "handlemanageasset":
                    return ParseDepth(manageAsset);
                    
                default:
                    return SerializationHelper.SerializationDepth.Standard;
            }
        }
        
        private SerializationHelper.SerializationDepth ParseDepth(string depthString)
        {
            if (Enum.TryParse<SerializationHelper.SerializationDepth>(depthString, true, out var result))
            {
                return result;
            }
            return SerializationHelper.SerializationDepth.Standard;
        }
    }
}
