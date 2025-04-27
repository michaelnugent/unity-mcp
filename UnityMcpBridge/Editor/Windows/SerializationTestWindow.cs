using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Newtonsoft.Json;
using UnityEditor;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityMcpBridge.Editor.Helpers;
using UnityMcpBridge.Editor.Helpers.Serialization;

namespace UnityMcpBridge.Editor.Windows
{
    /// <summary>
    /// Editor window for testing serialization of Unity objects.
    /// This window provides a simple UI to serialize the current scene and display the results.
    /// </summary>
    public class SerializationTestWindow : EditorWindow
    {
        private SerializationHelper.SerializationDepth _selectedDepth = SerializationHelper.SerializationDepth.Standard;
        private Vector2 _scrollPosition;
        private string _serializedOutput = "";
        private bool _prettyPrint = true;
        private List<string> _errors = new List<string>();
        private List<string> _warnings = new List<string>();
        private bool _showErrors = true;
        private Vector2 _errorScrollPosition;
        private GameObject _selectedObject;
        private bool _serializeSelectedOnly = false;

        [MenuItem("MCP/Serialization Test Window")]
        public static void ShowWindow()
        {
            GetWindow<SerializationTestWindow>("Serialization Test");
        }

        private void OnGUI()
        {
            GUILayout.Label("Unity Serialization Test", EditorStyles.boldLabel);

            EditorGUILayout.Space();
            
            // Ensure serialization registry is initialized
            SerializationHandlerRegistry.Initialize();
            
            // Display registered handlers
            EditorGUILayout.BeginVertical("box");
            GUILayout.Label("Registered Handlers", EditorStyles.boldLabel);
            
            var handlers = SerializationHandlerRegistry.GetAllHandlers().ToList();
            EditorGUILayout.LabelField($"Total Handlers: {handlers.Count}");
            
            foreach (var handler in handlers)
            {
                EditorGUILayout.LabelField($"• {handler.GetType().Name} - Handles {handler.HandledType.Name}");
            }
            
            EditorGUILayout.EndVertical();
            
            EditorGUILayout.Space();
            
            // Serialization options
            EditorGUILayout.BeginVertical("box");
            GUILayout.Label("Options", EditorStyles.boldLabel);
            
            _selectedDepth = (SerializationHelper.SerializationDepth)EditorGUILayout.EnumPopup("Serialization Depth:", _selectedDepth);
            _prettyPrint = EditorGUILayout.Toggle("Pretty Print:", _prettyPrint);
            
            EditorGUILayout.Space();
            
            _serializeSelectedOnly = EditorGUILayout.Toggle("Serialize Selected Only:", _serializeSelectedOnly);
            if (_serializeSelectedOnly)
            {
                _selectedObject = EditorGUILayout.ObjectField("GameObject:", _selectedObject, typeof(GameObject), true) as GameObject;
            }
            
            EditorGUILayout.EndVertical();

            EditorGUILayout.Space();

            // Action buttons
            if (GUILayout.Button(_serializeSelectedOnly ? "Serialize Selected Object" : "Serialize Current Scene"))
            {
                if (_serializeSelectedOnly && _selectedObject != null)
                {
                    SerializeSelectedObject();
                }
                else
                {
                    SerializeCurrentScene();
                }
            }

            EditorGUILayout.Space();

            // Results display
            EditorGUILayout.BeginVertical("box");
            GUILayout.Label("Serialized Output:", EditorStyles.boldLabel);
            
            _scrollPosition = EditorGUILayout.BeginScrollView(_scrollPosition, GUILayout.Height(300));
            EditorGUILayout.TextArea(_serializedOutput, GUILayout.ExpandHeight(true));
            EditorGUILayout.EndScrollView();
            
            EditorGUILayout.EndVertical();

            // Error display
            _showErrors = EditorGUILayout.Foldout(_showErrors, $"Errors & Warnings ({_errors.Count + _warnings.Count})");
            
            if (_showErrors)
            {
                EditorGUILayout.BeginVertical("box");
                
                _errorScrollPosition = EditorGUILayout.BeginScrollView(_errorScrollPosition, GUILayout.Height(100));
                
                foreach (var error in _errors)
                {
                    EditorGUILayout.HelpBox(error, MessageType.Error);
                }
                
                foreach (var warning in _warnings)
                {
                    EditorGUILayout.HelpBox(warning, MessageType.Warning);
                }
                
                EditorGUILayout.EndScrollView();
                
                EditorGUILayout.EndVertical();
            }

            EditorGUILayout.Space();

            // Export button
            if (GUILayout.Button("Export JSON to File") && !string.IsNullOrEmpty(_serializedOutput))
            {
                ExportToFile();
            }
        }

        private void SerializeSelectedObject()
        {
            _errors.Clear();
            _warnings.Clear();
            
            if (_selectedObject == null)
            {
                _errors.Add("No GameObject selected for serialization.");
                _serializedOutput = "{ \"error\": \"No GameObject selected\" }";
                return;
            }
            
            try
            {
                // Use our new serialization system
                _serializedOutput = _selectedObject.ToSafeJson(_selectedDepth, _prettyPrint);
                Debug.Log($"Serialized GameObject '{_selectedObject.name}'.");
            }
            catch (System.Exception ex)
            {
                _errors.Add($"Failed to serialize {_selectedObject.name}: {ex.Message}");
                Debug.LogError($"Serialization error: {ex.Message}");
                _serializedOutput = $"{{ \"error\": \"{ex.Message}\" }}";
            }
        }

        private void SerializeCurrentScene()
        {
            _errors.Clear();
            _warnings.Clear();
            
            var scene = SceneManager.GetActiveScene();
            var rootObjects = scene.GetRootGameObjects();
            
            try
            {
                // Create a container object to hold scene information
                var sceneContainer = new SceneContainer
                {
                    SceneName = scene.name,
                    Path = scene.path,
                    RootObjectCount = rootObjects.Length,
                    SerializationDepth = _selectedDepth.ToString()
                };
                
                // Serialize each root object and store results as Dictionary<string, object> to preserve the full structure
                var objectsData = new List<Dictionary<string, object>>();
                
                foreach (var rootObject in rootObjects)
                {
                    try
                    {
                        // Parse the JSON to extract the full object data, including IntrospectedProperties
                        string objectJson = rootObject.ToSafeJson(_selectedDepth, false);
                        
                        // Debug logging to see the raw JSON
                        Debug.Log($"Raw JSON for {rootObject.name}: {objectJson.Substring(0, Mathf.Min(100, objectJson.Length))}...");
                        
                        // Create a dictionary to hold the deserialized data
                        Dictionary<string, object> objData = new Dictionary<string, object>();
                        
                        // Extract whether it was fully serialized
                        objData["WasFullySerialized"] = false;
                        objData["ErrorMessage"] = "";
                        objData["ObjectTypeName"] = rootObject.GetType().FullName;
                        
                        // Get the fallback representation directly
                        var introspectedProps = SerializationHelper.CreateFallbackRepresentation(rootObject, _selectedDepth);
                        if (introspectedProps != null && introspectedProps.Count > 0)
                        {
                            objData["IntrospectedProperties"] = introspectedProps;
                            objData["Handler"] = introspectedProps.ContainsKey("_handlerType") ? 
                                                 introspectedProps["_handlerType"] : "None";
                        }
                        
                        objectsData.Add(objData);
                    }
                    catch (System.Exception ex)
                    {
                        _errors.Add($"Failed to serialize {rootObject.name}: {ex.Message}");
                        Dictionary<string, object> errorObj = new Dictionary<string, object>
                        {
                            ["WasFullySerialized"] = false,
                            ["ErrorMessage"] = $"Failed to serialize {rootObject.name}: {ex.Message}",
                            ["ObjectTypeName"] = rootObject.GetType().FullName
                        };
                        objectsData.Add(errorObj);
                    }
                }
                
                // Convert the dictionaries to JSON
                var settings = new JsonSerializerSettings
                { 
                    Formatting = _prettyPrint ? Formatting.Indented : Formatting.None
                };
                
                // Create the scene container JSON
                var sceneJson = new Dictionary<string, object>
                {
                    ["scene"] = new Dictionary<string, object>
                    {
                        ["sceneName"] = sceneContainer.SceneName,
                        ["path"] = sceneContainer.Path,
                        ["rootObjectCount"] = sceneContainer.RootObjectCount,
                        ["serializationDepth"] = sceneContainer.SerializationDepth,
                        ["objects"] = objectsData
                    }
                };
                
                // Use Newtonsoft.Json to serialize the entire structure
                _serializedOutput = JsonConvert.SerializeObject(sceneJson, settings);
                
                Debug.Log($"Serialized scene '{scene.name}' with {rootObjects.Length} root objects.");
            }
            catch (System.Exception ex)
            {
                _errors.Add($"Failed to serialize scene: {ex.Message}");
                Debug.LogError($"Serialization error: {ex.Message}");
                _serializedOutput = $"{{ \"error\": \"{ex.Message}\" }}";
            }
        }

        private void ExportToFile()
        {
            string path = EditorUtility.SaveFilePanel(
                "Save JSON File",
                "",
                $"Scene_{SceneManager.GetActiveScene().name}_Serialized.json",
                "json");

            if (!string.IsNullOrEmpty(path))
            {
                File.WriteAllText(path, _serializedOutput);
                Debug.Log($"Serialized data saved to {path}");
            }
        }

        // Simple container for scene information
        private class SceneContainer
        {
            public string SceneName { get; set; }
            public string Path { get; set; }
            public int RootObjectCount { get; set; }
            public string SerializationDepth { get; set; }
        }
    }
} 