using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEngine;
using UnityMcpBridge.Editor.Helpers;
using UnityMcpBridge.Editor.Tools.ManageGameObjectImpl.Models;

namespace UnityMcpBridge.Editor.Tools.ManageGameObjectImpl
{
    /// <summary>
    /// Handles deletion of GameObjects in the scene.
    /// Part of the ManageGameObject tool's internal implementation.
    /// </summary>
    internal static class GameObjectDeleter
    {
        /// <summary>
        /// Deletes a GameObject based on the provided parameters
        /// </summary>
        public static object DeleteGameObject(JObject @params)
        {
            GameObjectParams goParams = GameObjectParams.FromJObject(@params);
            JToken targetToken = goParams.TargetToken;
            
            if (targetToken == null)
            {
                return Response.Error("'target' parameter is required for delete action.");
            }

            // Get delete children option
            bool deleteChildren = @params["delete_children"]?.ToObject<bool>() ?? true;
            
            // Try to handle special case for multiple targets
            if (targetToken.Type == JTokenType.Array)
            {
                return DeleteMultipleGameObjects(targetToken as JArray, deleteChildren);
            }

            // Handle single target
            GameObject targetObj = GameObjectFinder.FindSingleObject(targetToken, "by_id_or_name_or_path");
            if (targetObj == null)
            {
                return Response.Error($"Target GameObject '{targetToken}' not found.");
            }

            // Handle special exclusions
            if (targetObj.CompareTag("EditorOnly") || targetObj.name == "MCP_Editor_Only")
            {
                return Response.Error($"GameObject '{targetObj.name}' is marked as Editor Only and cannot be deleted.");
            }

            // Store data before deletion for the response
            string targetName = targetObj.name;
            string targetPath = GameObjectSerializer.GetFullPath(targetObj.transform);
            GameObject parentObj = targetObj.transform.parent != null ? targetObj.transform.parent.gameObject : null;

            // Register for Undo
            if (!deleteChildren)
            {
                // Move children to parent
                List<Transform> children = new List<Transform>();
                foreach (Transform child in targetObj.transform)
                {
                    children.Add(child);
                }

                foreach (Transform child in children)
                {
                    Undo.SetTransformParent(child, targetObj.transform.parent, $"Reparent {child.name} before delete");
                }
            }

            Undo.DestroyObjectImmediate(targetObj);

            if (parentObj != null)
            {
                Selection.activeGameObject = parentObj;
            }

            return Response.Success(
                deleteChildren
                    ? $"GameObject '{targetName}' and its children deleted."
                    : $"GameObject '{targetName}' deleted, its children reparented to '{(parentObj != null ? parentObj.name : "Scene Root")}'.",
                new JObject
                {
                    ["deleted_object"] = new JObject
                    {
                        ["name"] = targetName,
                        ["path"] = targetPath,
                        ["parent"] = parentObj != null ? (JToken)GameObjectSerializer.GetGameObjectData(parentObj) : null
                    }
                }
            );
        }

        /// <summary>
        /// Deletes multiple GameObjects based on an array of targets
        /// </summary>
        private static object DeleteMultipleGameObjects(JArray targetArray, bool deleteChildren)
        {
            if (targetArray == null || targetArray.Count == 0)
            {
                return Response.Error("No valid targets specified for deletion.");
            }

            int successCount = 0;
            int failureCount = 0;
            List<string> errors = new List<string>();
            List<JObject> deletedObjects = new List<JObject>();
            HashSet<GameObject> parentObjects = new HashSet<GameObject>(); // To keep track of parents for selection

            foreach (JToken target in targetArray)
            {
                GameObject targetObj = GameObjectFinder.FindSingleObject(target, "by_id_or_name_or_path");
                if (targetObj == null)
                {
                    failureCount++;
                    errors.Add($"Target '{target}' not found.");
                    continue;
                }

                // Handle special exclusions
                if (targetObj.CompareTag("EditorOnly") || targetObj.name == "MCP_Editor_Only")
                {
                    failureCount++;
                    errors.Add($"GameObject '{targetObj.name}' is marked as Editor Only and cannot be deleted.");
                    continue;
                }

                // Store data before deletion for the response
                string targetName = targetObj.name;
                string targetPath = GameObjectSerializer.GetFullPath(targetObj.transform);
                GameObject parentObj = targetObj.transform.parent != null ? targetObj.transform.parent.gameObject : null;

                // Add parent to tracking set (if not null) 
                if (parentObj != null)
                {
                    parentObjects.Add(parentObj);
                }

                // Register for Undo
                if (!deleteChildren)
                {
                    // Move children to parent
                    List<Transform> children = new List<Transform>();
                    foreach (Transform child in targetObj.transform)
                    {
                        children.Add(child);
                    }

                    foreach (Transform child in children)
                    {
                        Undo.SetTransformParent(child, targetObj.transform.parent, $"Reparent {child.name} before delete");
                    }
                }

                try
                {
                    Undo.DestroyObjectImmediate(targetObj);
                    successCount++;
                    deletedObjects.Add(new JObject
                    {
                        ["name"] = targetName,
                        ["path"] = targetPath,
                        ["parent"] = parentObj != null ? (JToken)GameObjectSerializer.GetGameObjectData(parentObj) : null
                    });
                }
                catch (Exception ex)
                {
                    failureCount++;
                    errors.Add($"Failed to delete '{targetName}': {ex.Message}");
                }
            }

            // Try to select a common parent if available
            if (parentObjects.Count > 0)
            {
                Selection.activeGameObject = parentObjects.First();
            }

            // Prepare response
            JObject resultData = new JObject
            {
                ["deleted_count"] = successCount,
                ["failed_count"] = failureCount,
                ["errors"] = new JArray(errors.Cast<object>().Select(e => (JToken)e).ToArray()),
                ["deleted_objects"] = new JArray(deletedObjects.Cast<object>().Select(o => (JToken)o).ToArray())
            };

            if (failureCount == 0)
            {
                return Response.Success(
                    deleteChildren
                        ? $"{successCount} GameObjects and their children deleted."
                        : $"{successCount} GameObjects deleted, their children reparented to their parents.",
                    resultData
                );
            }
            else if (successCount == 0)
            {
                return Response.Error($"Failed to delete any GameObjects. Errors: {string.Join(", ", errors)}");
            }
            else
            {
                return Response.Warning(
                    $"{successCount} GameObjects deleted, {failureCount} failed. See errors for details.",
                    resultData
                );
            }
        }
    }
} 