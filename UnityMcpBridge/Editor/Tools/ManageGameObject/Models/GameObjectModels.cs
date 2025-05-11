using Newtonsoft.Json.Linq;
using UnityEngine;

namespace UnityMcpBridge.Editor.Tools.ManageGameObject.Models
{
    /// <summary>
    /// Contains common model classes and structs for GameObject management operations.
    /// Part of the ManageGameObject tool's internal implementation.
    /// </summary>
    internal struct GameObjectQueryParams
    {
        public JToken TargetToken { get; set; }
        public string SearchMethod { get; set; }
        public bool FindAll { get; set; }
        public bool SearchInactive { get; set; }
        public bool SearchInChildren { get; set; }
        public string SearchTerm { get; set; }
        
        public static GameObjectQueryParams FromJObject(JObject @params)
        {
            return new GameObjectQueryParams
            {
                TargetToken = @params["target"],
                SearchMethod = @params["search_method"]?.ToString()?.ToLower(),
                FindAll = @params["find_all"]?.ToObject<bool>() ?? false,
                SearchInactive = @params["search_inactive"]?.ToObject<bool>() ?? false,
                SearchInChildren = @params["search_in_children"]?.ToObject<bool>() ?? false,
                SearchTerm = @params["search_term"]?.ToString()
            };
        }
    }

    /// <summary>
    /// Common parameters used for GameObject operations
    /// </summary>
    internal struct GameObjectParams
    {
        public string Name { get; set; }
        public string Tag { get; set; }
        public string Layer { get; set; }
        public JToken ParentToken { get; set; }
        public JArray Position { get; set; }
        public JArray Rotation { get; set; }
        public JArray Scale { get; set; }
        
        public static GameObjectParams FromJObject(JObject @params)
        {
            return new GameObjectParams
            {
                Name = @params["name"]?.ToString(),
                Tag = @params["tag"]?.ToString(),
                Layer = @params["layer"]?.ToString(),
                ParentToken = @params["parent"],
                Position = @params["position"] as JArray,
                Rotation = @params["rotation"] as JArray,
                Scale = @params["scale"] as JArray
            };
        }
    }

    /// <summary>
    /// Parameters for component operations
    /// </summary>
    internal struct ComponentParams
    {
        public string ComponentName { get; set; }
        public JObject Properties { get; set; }
        public JArray ComponentsToAdd { get; set; }
        public JArray ComponentsToRemove { get; set; }
        public JObject ComponentProperties { get; set; }
        
        public static ComponentParams FromJObject(JObject @params)
        {
            return new ComponentParams
            {
                ComponentName = @params["component_name"]?.ToString(),
                ComponentsToAdd = @params["components_to_add"] as JArray,
                ComponentsToRemove = @params["components_to_remove"] as JArray,
                ComponentProperties = @params["component_properties"] as JObject
            };
        }
    }
} 