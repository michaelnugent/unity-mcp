"""
Unit tests for GameObjectTool parameter validation.

This module contains tests focused on validating the improvements to the GameObject tool's
parameter validation, error handling, and response formatting.
"""
import pytest
from typing import Dict, Any, List
from unity_connection import ParameterValidationError
from tools.manage_gameobject import GameObjectTool
import json

class TestGameObjectToolValidation:
    """Tests for the GameObjectTool validation."""
    
    def setup_method(self):
        """Set up a GameObject tool instance for testing."""
        self.tool = GameObjectTool()
    
    def test_create_gameobject_validation(self):
        """Test validation for creating a GameObject."""
        # Valid parameters
        params = {
            "name": "TestObject",
            "position": [1, 2, 3],
            "rotation": [0, 90, 0],
            "scale": [1, 1, 1]
        }
        
        # Should validate without errors
        result = self.tool.validate_and_convert_params("create", params)
        
        # Check parameter conversion
        assert isinstance(result["position"], dict)
        assert result["position"]["x"] == 1
        assert result["position"]["y"] == 2
        assert result["position"]["z"] == 3
        
        # Test invalid parameters - missing name
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("create", {
                "position": [1, 2, 3]
            })
        assert "name" in str(e.value)
        assert "requires" in str(e.value).lower()
        
        # Test invalid parameters - invalid position
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("create", {
                "name": "TestObject",
                "position": "not_a_vector"
            })
        assert "position" in str(e.value)
        assert "Invalid" in str(e.value)
        
        # Test invalid parameters - position with wrong number of components
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("create", {
                "name": "TestObject",
                "position": [1, 2]
            })
        assert "position" in str(e.value)
        assert "exactly 3 components" in str(e.value)
        
        # Test invalid parameters - position with non-numeric components
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("create", {
                "name": "TestObject",
                "position": [1, "two", 3]
            })
        assert "position" in str(e.value)
        assert "components must be convertible to float" in str(e.value)
    
    def test_modify_gameobject_validation(self):
        """Test validation for modifying a GameObject."""
        # Valid parameters
        params = {
            "target": "Main Camera",
            "position": [1, 2, 3],
            "rotation": [0, 90, 0],
            "scale": [1, 1, 1]
        }
        
        # Should validate without errors
        result = self.tool.validate_and_convert_params("modify", params)
        
        # Test invalid parameters - missing target
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("modify", {
                "position": [1, 2, 3]
            })
        assert "target" in str(e.value)
        assert "requires" in str(e.value).lower()
    
    def test_add_component_validation(self):
        """Test validation for adding components to a GameObject."""
        # Valid parameters
        params = {
            "target": "Main Camera",
            "componentsToAdd": ["UnityEngine.BoxCollider", "UnityEngine.Rigidbody"]
        }
        
        # Should validate without errors
        result = self.tool.validate_and_convert_params("add_component", params)
        
        # Test invalid parameters - missing target
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("add_component", {
                "componentsToAdd": ["UnityEngine.BoxCollider"]
            })
        assert "target" in str(e.value)
        
        # Test invalid parameters - missing componentsToAdd
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("add_component", {
                "target": "Main Camera"
            })
        assert "componentsToAdd" in str(e.value) or "components" in str(e.value)
    
    def test_component_properties_validation(self):
        """Test validation for setting component properties."""
        # Valid parameters
        params = {
            "target": "Main Camera",
            "componentProperties": {
                "Transform": {
                    "position": [1, 2, 3],
                    "rotation": [0, 90, 0]
                },
                "Camera": {
                    "fieldOfView": 60,
                    "nearClipPlane": 0.1
                }
            }
        }
        
        # Should validate without errors
        result = self.tool.validate_and_convert_params("set_component_property", params)
        
        # Test invalid parameters - componentProperties not a dict
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("set_component_property", {
                "target": "Main Camera",
                "componentProperties": "not_a_dict"
            })
        assert "componentProperties" in str(e.value)
        assert "dict" in str(e.value).lower()
        
        # Test invalid parameters - component properties not a dict
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("set_component_property", {
                "target": "Main Camera",
                "componentProperties": {
                    "Transform": "not_a_dict"
                }
            })
        error_msg = str(e.value)
        assert "Transform" in error_msg or "component" in error_msg.lower()
        assert "must be a dictionary" in error_msg.lower() or "dict" in error_msg.lower()
    
    def test_find_gameobject_validation(self):
        """Test validation for finding GameObjects."""
        # Valid parameters with correct parameter names
        params = {
            "search_term": "Camera",  # Using snake_case as required by required_params
            "searchMethod": "by_name",
            "findAll": True
        }
        
        # Should validate without errors
        result = self.tool.validate_and_convert_params("find", params)
        
        # Test invalid parameters - missing search_term
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("find", {
                "searchMethod": "by_name"
            })
        assert "search_term" in str(e.value)
        
        # Test invalid parameters - invalid searchMethod
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("find", {
                "search_term": "Camera",
                "searchMethod": "invalid_method"
            })
        assert "searchMethod" in str(e.value) or "search_method" in str(e.value)
        assert "invalid_method" in str(e.value)
        assert "Valid methods" in str(e.value)
    
    def test_instantiate_validation(self):
        """Test validation for instantiating prefabs."""
        # Valid parameters
        params = {
            "prefabPath": "Assets/Prefabs/TestPrefab.prefab",
            "position": [1, 2, 3],
            "rotation": [0, 90, 0]
        }
        
        # Should validate without errors
        result = self.tool.validate_and_convert_params("instantiate", params)
        
        # Test invalid parameters - missing prefabPath
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("instantiate", {
                "position": [1, 2, 3]
            })
        assert "prefabPath" in str(e.value)
        
        # Test invalid parameters - invalid prefab path
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("instantiate", {
                "prefabPath": "InvalidPath/TestPrefab.prefab"
            })
        assert "prefabPath" in str(e.value) or "prefab path" in str(e.value)
        assert "Asset" in str(e.value)
    
    def test_primitive_type_validation(self):
        """Test validation for primitive type creation."""
        # Valid parameters
        params = {
            "name": "TestCube",
            "primitiveType": "Cube",
            "position": [1, 2, 3]
        }
        
        # Should validate without errors
        result = self.tool.validate_and_convert_params("create", params)
        
        # Test invalid parameters - invalid primitiveType
        with pytest.raises(ParameterValidationError) as e:
            self.tool.validate_and_convert_params("create", {
                "name": "TestShape",
                "primitiveType": "InvalidShape"
            })
        assert "primitiveType" in str(e.value) or "primitive" in str(e.value).lower()
        assert "InvalidShape" in str(e.value)
        assert "Valid types" in str(e.value)
    
    def test_post_process_response(self):
        """Test post-processing of responses."""
        # Mock a find response
        response = {
            "success": True,
            "data": []
        }
        params = {
            "action": "find",
            "searchTerm": "Camera",
            "searchMethod": "by_name"
        }
        
        # Process the response
        result = self.tool.post_process_response(response, "find", params)
        
        # Should add a helpful message
        assert "message" in result
        assert "No GameObjects found" in result["message"]
        assert "Camera" in result["message"]
        
        # Mock a find response with results
        response = {
            "success": True,
            "data": [{"name": "Main Camera"}, {"name": "UI Camera"}]
        }
        
        # Process the response
        result = self.tool.post_process_response(response, "find", params)
        
        # Should add a helpful message with count
        assert "message" in result
        assert "Found 2 GameObjects" in result["message"]
        assert "Camera" in result["message"]
        
        # Mock a get_children response
        response = {
            "success": True,
            "data": [{"name": "Child1"}, {"name": "Child2"}, {"name": "Child3"}]
        }
        params = {
            "action": "get_children",
            "target": "Parent"
        }
        
        # Process the response
        result = self.tool.post_process_response(response, "get_children", params)
        
        # Should add a helpful message with count
        assert "message" in result
        assert "has 3 children" in result["message"]
        assert "Parent" in result["message"]

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 