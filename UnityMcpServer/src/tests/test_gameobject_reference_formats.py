"""
Unit tests for GameObject reference format standardization.

This module contains tests focused on validating that GameObject references
accept various formats (name, path, ID) consistently across all tools.
"""
import pytest
from typing import Dict, Any, List
from unity_connection import ParameterValidationError
from tools.manage_gameobject import GameObjectTool
from tools.manage_scene import SceneTool
from tools.base_tool import BaseTool
from tools.manage_gameobject import validate_gameobject_path

class TestGameObjectReferenceFormats:
    """Tests for GameObject reference format validation."""
    
    def setup_method(self):
        """Set up tools for testing."""
        self.gameobject_tool = GameObjectTool()
        self.scene_tool = SceneTool()
    
    def test_string_reference_validation(self):
        """Test that string references to GameObjects are accepted."""
        # Simple name reference
        validate_gameobject_path("MainCamera")
        
        # Hierarchical path reference
        validate_gameobject_path("Parent/Child")
        
        # Test with non-string references
        with pytest.raises(ParameterValidationError) as e:
            validate_gameobject_path(123)
        error_msg = str(e.value)
        assert "must be a string" in error_msg
        assert "undefined" not in error_msg
        
    def test_consistent_reference_formats(self):
        """Test that GameObject reference formats are consistently accepted across tools."""
        # Test with GameObject tool
        gameobject_tool = GameObjectTool()
        
        # These parameters should pass validation for target
        try:
            gameobject_tool.validate_and_convert_params("get_components", {
                "target": "MainCamera"
            })
        except ParameterValidationError as e:
            assert False, f"GameObject tool rejected valid string reference: {str(e)}"
        
        # Test with Scene tool that also deals with GameObjects
        scene_tool = SceneTool()
        
        # These parameters should pass validation for game_object_name
        try:
            scene_tool.validate_and_convert_params("find", {
                "query": "MainCamera"
            })
        except ParameterValidationError as e:
            assert False, f"Scene tool rejected valid string reference: {str(e)}"

    def test_hierarchical_path_references(self):
        """Test that hierarchical path references are accepted."""
        # Test simple hierarchical path
        try:
            validate_gameobject_path("Parent/Child")
        except ParameterValidationError as e:
            assert False, f"Rejected valid hierarchical path: {str(e)}"
        
        # Test deeper hierarchical path
        try:
            validate_gameobject_path("Parent/Child/Grandchild")
        except ParameterValidationError as e:
            assert False, f"Rejected valid deep hierarchical path: {str(e)}"
        
        # Test with leading slash (should be accepted but normalized)
        try:
            validate_gameobject_path("/Parent/Child")
        except ParameterValidationError as e:
            assert False, f"Rejected path with leading slash: {str(e)}"
        
    def test_path_validation_with_invalid_chars(self):
        """Test that paths with invalid characters are rejected."""
        invalid_chars = ['\\', '"', '*', '<', '>', '|', ':', '?']
        for char in invalid_chars:
            path = f"Parent{char}Child"
            with pytest.raises(ParameterValidationError) as e:
                validate_gameobject_path(path)
            error_msg = str(e.value)
            assert char in error_msg
            assert "invalid character" in error_msg.lower()
    
    def test_empty_path_validation(self):
        """Test that empty paths are rejected."""
        with pytest.raises(ParameterValidationError) as e:
            validate_gameobject_path("")
        error_msg = str(e.value)
        assert "empty" in error_msg.lower()
        
        with pytest.raises(ParameterValidationError) as e:
            validate_gameobject_path(None)
        error_msg = str(e.value)
        assert "must be a string" in error_msg.lower() or "none" in error_msg.lower()
    
    def test_gameobject_find_by_path(self):
        """Test finding GameObjects by hierarchical path."""
        # Mock validation for finding by path
        try:
            self.gameobject_tool.validate_and_convert_params("find", {
                "search_term": "Parent/Child",
                "search_method": "by_path"
            })
        except ParameterValidationError as e:
            assert False, f"Rejected valid path for finding: {str(e)}"
    
    def test_gameobject_target_param_validation(self):
        """Test validation of target parameter in various actions."""
        # Actions that only require a target parameter
        actions = ["modify", "delete", "get_components"]
        
        for action in actions:
            # Test with valid string reference
            try:
                self.gameobject_tool.validate_and_convert_params(action, {
                    "target": "Parent/Child"
                })
            except ParameterValidationError as e:
                assert False, f"Rejected valid target string in {action}: {str(e)}"

        # Actions that require additional parameters besides target
        extra_param_actions = {
            "add_component": {"components_to_add": ["UnityEngine.BoxCollider"]},
            "remove_component": {"components_to_remove": ["UnityEngine.BoxCollider"]},
            "set_component_property": {"component_properties": {"Transform": {"position": [0, 0, 0]}}}
        }
        
        for action, extra_params in extra_param_actions.items():
            # Create params with target and required extra params
            params = {"target": "Parent/Child"}
            params.update(extra_params)
            
            try:
                self.gameobject_tool.validate_and_convert_params(action, params)
            except ParameterValidationError as e:
                error_msg = str(e)
                # Make sure it's not rejecting the target parameter format
                assert not ("target" in error_msg and ("must be a string" in error_msg or "invalid" in error_msg)), \
                    f"Rejected valid target string in {action}: {error_msg}" 