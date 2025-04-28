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
using Newtonsoft.Json.Linq;

namespace UnityMcpBridge.Editor.Windows
{
    /// <summary>
    /// Editor window for testing serialization of Unity objects.
    /// This window provides a simple UI to serialize the current scene and display the results.
    /// </summary>
    public class SerializationTestWindow : EditorWindow
    {
        private static SerializationTestWindow _window = null;
        
        [MenuItem("Window/Unity MCP/Serialization Test")]
        public static void ShowWindow()
        {
            _window = GetWindow<SerializationTestWindow>("Serialization Test");
            _window.Show();
        }

        private bool _serializeSelectedOnly = false;
        private GameObject _selectedObject = null;
        private SerializationHelper.SerializationDepth _selectedDepth = SerializationHelper.SerializationDepth.Standard;
        private System.Type _serializablesType;
        private string _resultsJson = "";
        private Vector2 _scrollPosition = Vector2.zero;
        private Vector2 _errorScrollPosition;
        private bool _showErrors = true;
        private string _serializedOutput = "";
        private bool _prettyPrint = true;
        private List<string> _errors = new List<string>();
        private List<string> _warnings = new List<string>();
        private string _jsonResult = "";

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

            // Type-based serialization
            EditorGUILayout.BeginVertical("box");
            GUILayout.Label("Serialize All Objects of Type", EditorStyles.boldLabel);
            
            // Create a string to show the currently selected type
            string typeLabel = _serializablesType != null ? _serializablesType.Name : "Select Type...";
            
            if (GUILayout.Button(typeLabel))
            {
                // Create and show a dropdown menu with types
                var menu = new GenericMenu();
                
                // Get all types that inherit from UnityEngine.Object
                var types = System.AppDomain.CurrentDomain.GetAssemblies()
                    .SelectMany(a => a.GetTypes())
                    .Where(t => typeof(UnityEngine.Object).IsAssignableFrom(t) && !t.IsAbstract && !t.IsInterface)
                    .OrderBy(t => t.Name)
                    .ToList();
                
                // Add an option for each type
                foreach (var type in types)
                {
                    menu.AddItem(new GUIContent(type.Name), _serializablesType == type, 
                        () => { _serializablesType = type; });
                }
                
                menu.ShowAsContext();
            }
            
            if (GUILayout.Button("Serialize All Objects of Selected Type") && _serializablesType != null)
            {
                SerializeSerializables();
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

            // Add MCP Bridge integration test button
            GUILayout.Space(10);
            if (GUILayout.Button("Test MCP Bridge Integration", GUILayout.Height(30)))
            {
                TestMcpBridgeIntegration();
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
                _errors.Add("No object selected");
                _serializedOutput = "{ \"error\": \"No object selected\" }";
                return;
            }
            
            try
            {
                // Serialize the selected object using the standard helper
                string json = SerializationHelper.SafeSerializeToJson(_selectedObject, _selectedDepth, false);
                
                // Parse the JSON to ensure it's valid
                var parsedObject = Newtonsoft.Json.JsonConvert.DeserializeObject(json);
                
                // Serialize back with pretty formatting if needed
                _serializedOutput = Newtonsoft.Json.JsonConvert.SerializeObject(
                    parsedObject, 
                    _prettyPrint ? Newtonsoft.Json.Formatting.Indented : Newtonsoft.Json.Formatting.None);
                
                Debug.Log($"Serialized object '{_selectedObject.name}'");
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
                // Create a container for scene data
                var sceneData = new Dictionary<string, object>
                {
                    ["sceneName"] = scene.name,
                    ["path"] = scene.path,
                    ["rootObjectCount"] = rootObjects.Length,
                    ["serializationDepth"] = _selectedDepth.ToString()
                };
                
                // Serialize each root object using the standard serialization method
                var objectsData = new List<object>();
                
                foreach (var rootObject in rootObjects)
                {
                    try
                    {
                        // Use the exact same serialization method as the rest of the codebase
                        string objectJson = SerializationHelper.SafeSerializeToJson(rootObject, _selectedDepth, false);
                        
                        // Parse the JSON to an object so it gets included properly in the final JSON
                        var parsedObject = Newtonsoft.Json.JsonConvert.DeserializeObject(objectJson);
                        objectsData.Add(parsedObject);
                    }
                    catch (System.Exception ex)
                    {
                        _errors.Add($"Failed to serialize {rootObject.name}: {ex.Message}");
                        objectsData.Add(new { error = $"Failed to serialize {rootObject.name}: {ex.Message}" });
                    }
                }

                // Create the final JSON structure using Newtonsoft
                var finalData = new Dictionary<string, object>
                {
                    ["scene"] = new Dictionary<string, object>
                    {
                        ["sceneName"] = scene.name,
                        ["path"] = scene.path,
                        ["rootObjectCount"] = rootObjects.Length,
                        ["serializationDepth"] = _selectedDepth.ToString(),
                        ["objects"] = objectsData
                    }
                };

                // Serialize to JSON
                _serializedOutput = Newtonsoft.Json.JsonConvert.SerializeObject(finalData, 
                    _prettyPrint ? Newtonsoft.Json.Formatting.Indented : Newtonsoft.Json.Formatting.None);
                
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

        private void TestMcpBridgeIntegration()
        {
            // Log scene information for debugging
            var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
            var rootObjects = scene.GetRootGameObjects();
            Debug.Log($"Active scene: {scene.name} with {rootObjects.Length} root objects");
            
            foreach (var root in rootObjects)
            {
                Debug.Log($"Root object: {root.name}");
            }
            
            // Direct approach using FindObjectsOfType
            var allGameObjects = UnityEngine.Object.FindObjectsOfType<GameObject>(true);
            Debug.Log($"Found {allGameObjects.Length} GameObjects directly with FindObjectsOfType");
            
            // Create a list to hold serialized objects
            var gameObjectDataList = new List<object>();
            
            // Serialize each GameObject individually and add to the list
            foreach (var go in allGameObjects)
            {
                try
                {
                    // Use SafeSerializeToJson instead of CreateSerializationResult
                    string objectJson = SerializationHelper.SafeSerializeToJson(go, SerializationHelper.SerializationDepth.Standard, false);
                    var parsedObject = Newtonsoft.Json.JsonConvert.DeserializeObject(objectJson);
                    gameObjectDataList.Add(parsedObject);
                    
                    Debug.Log($"Successfully serialized GameObject: {go.name}");
                }
                catch (System.Exception ex)
                {
                    Debug.LogError($"Failed to serialize GameObject {go.name}: {ex.Message}");
                    gameObjectDataList.Add(new { error = $"Failed to serialize: {ex.Message}" });
                }
            }
            
            // Create a response with serialized objects
            var result = new Dictionary<string, object>
            {
                { "success", true },
                { "message", $"Found {allGameObjects.Length} game objects directly." },
                { "data", gameObjectDataList }
            };

            // Display the result in the text area
            _serializedOutput = Newtonsoft.Json.JsonConvert.SerializeObject(result, 
                _prettyPrint ? Newtonsoft.Json.Formatting.Indented : Newtonsoft.Json.Formatting.None);
            
            Debug.Log("MCP Bridge Integration test executed");
            Repaint();
        }

        private void SerializeSerializables()
        {
            _errors.Clear();
            _warnings.Clear();

            if (_serializablesType == null)
            {
                _errors.Add("No type selected");
                _serializedOutput = "{ \"error\": \"No type selected\" }";
                return;
            }

            try
            {
                // Find all instances of the selected type
                var instances = UnityEngine.Object.FindObjectsOfType(_serializablesType);
                if (instances.Length == 0)
                {
                    _warnings.Add($"No instances of {_serializablesType.Name} found in scene");
                    _serializedOutput = $"{{ \"warning\": \"No instances of {_serializablesType.Name} found in scene\" }}";
                    return;
                }

                // Create a dictionary to hold all the serialized objects
                var objectsData = new List<object>();
                
                foreach (var instance in instances)
                {
                    try
                    {
                        string objectJson = SerializationHelper.SafeSerializeToJson(instance, _selectedDepth, false);
                        // Parse each JSON object to ensure it's valid
                        var parsedObject = Newtonsoft.Json.JsonConvert.DeserializeObject(objectJson);
                        objectsData.Add(parsedObject);
                    }
                    catch (System.Exception ex)
                    {
                        string objectName = instance != null ? (instance as UnityEngine.Object)?.name ?? "unknown" : "null";
                        _errors.Add($"Failed to serialize {objectName}: {ex.Message}");
                        Debug.LogError($"Failed to serialize {objectName}: {ex.Message}");
                    }
                }

                // Create the final data structure
                var finalData = new Dictionary<string, object>
                {
                    { "type", _serializablesType.Name },
                    { "objects", objectsData },
                    { "count", objectsData.Count }
                };

                // Serialize the final structure
                _serializedOutput = Newtonsoft.Json.JsonConvert.SerializeObject(
                    finalData, 
                    _prettyPrint ? Newtonsoft.Json.Formatting.Indented : Newtonsoft.Json.Formatting.None);
                
                Debug.Log($"Serialized {objectsData.Count} instances of {_serializablesType.Name}");
            }
            catch (System.Exception ex)
            {
                _errors.Add($"Failed to serialize {_serializablesType.Name} instances: {ex.Message}");
                Debug.LogError($"Serialization error: {ex.Message}");
                _serializedOutput = $"{{ \"error\": \"{ex.Message}\" }}";
            }
        }
    }
} 