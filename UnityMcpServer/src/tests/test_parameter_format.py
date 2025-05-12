"""
Unit tests for the ParameterFormat base class.

This module contains tests for the ParameterFormat base class in validation_utils.py,
which provides a foundation for standardizing parameter formats across tools.
"""
import pytest
from typing import Dict, List, Any, Union
from validation_utils import ParameterFormat


class TestParameterFormatBase:
    """Tests for the ParameterFormat base class functionality."""
    
    def test_common_parameters(self):
        """Test that common parameters are correctly defined in the base class."""
        # Check a few common parameters
        assert "position" in ParameterFormat.COMMON_PARAMETERS
        assert "rotation" in ParameterFormat.COMMON_PARAMETERS
        assert "scale" in ParameterFormat.COMMON_PARAMETERS
        
        # Verify position parameter has the expected structure
        position_param = ParameterFormat.COMMON_PARAMETERS["position"]
        assert "type" in position_param
        assert "description" in position_param
        assert "examples" in position_param
        assert "validation_rules" in position_param
        
        # Verify examples are properly defined
        assert isinstance(position_param["examples"], list)
        assert len(position_param["examples"]) > 0
    
    def test_get_parameter_definition(self):
        """Test the get_parameter_definition method."""
        # Test getting a common parameter
        position_def = ParameterFormat.get_parameter_definition("position")
        assert position_def is not None
        assert position_def["description"] == "3D position in world space"
        
        # Test getting a non-existent parameter
        assert ParameterFormat.get_parameter_definition("non_existent") is None
    
    def test_get_parameter_type(self):
        """Test the get_parameter_type method."""
        # Test getting the type of a common parameter
        position_type = ParameterFormat.get_parameter_type("position")
        assert position_type == ParameterFormat.POSITION_TYPE
        
        # Test getting the type of a non-existent parameter
        assert ParameterFormat.get_parameter_type("non_existent") is None
    
    def test_get_parameter_examples(self):
        """Test the get_parameter_examples method."""
        # Test getting examples for a common parameter
        position_examples = ParameterFormat.get_parameter_examples("position")
        assert isinstance(position_examples, list)
        assert len(position_examples) > 0
        
        # Test getting examples for a non-existent parameter
        assert ParameterFormat.get_parameter_examples("non_existent") == []
    
    def test_get_parameter_description(self):
        """Test the get_parameter_description method."""
        # Test getting description for a common parameter
        position_desc = ParameterFormat.get_parameter_description("position")
        assert position_desc == "3D position in world space"
        
        # Test getting description for a non-existent parameter
        assert ParameterFormat.get_parameter_description("non_existent") == ""
    
    def test_get_parameter_validation_rules(self):
        """Test the get_parameter_validation_rules method."""
        # Test getting validation rules for a common parameter
        position_rules = ParameterFormat.get_parameter_validation_rules("position")
        assert isinstance(position_rules, list)
        assert len(position_rules) > 0
        
        # Test getting validation rules for a non-existent parameter
        assert ParameterFormat.get_parameter_validation_rules("non_existent") == []
    
    def test_get_required_parameters(self):
        """Test the get_required_parameters method."""
        # Base class doesn't define required parameters
        assert ParameterFormat.get_required_parameters("create") == []
    
    def test_get_valid_actions(self):
        """Test the get_valid_actions method."""
        # Base class doesn't define valid actions
        assert ParameterFormat.get_valid_actions() == []


class GameObjectToolFormat(ParameterFormat):
    """Sample tool-specific parameter format for testing."""
    
    # Tool-specific parameters
    PARAMETERS = {
        "target": {
            "type": str,
            "description": "Reference to a GameObject to operate on",
            "examples": ["Player", "Player/Child"],
            "validation_rules": ["Must be a valid GameObject name or path"]
        },
        "components_to_add": {
            "type": List[str],
            "description": "List of component types to add to the GameObject",
            "examples": [["Rigidbody", "BoxCollider"]],
            "validation_rules": ["Must be a list of valid component type names"]
        }
    }
    
    # Required parameters by action
    REQUIRED_PARAMETERS = {
        "create": ["name"],
        "delete": ["target"],
        "add_component": ["target", "components_to_add"]
    }
    
    # Valid actions
    VALID_ACTIONS = ["create", "delete", "modify", "add_component"]


class TestToolSpecificParameterFormat:
    """Tests for tool-specific parameter format implementations."""
    
    def test_tool_specific_parameters(self):
        """Test that tool-specific parameters are correctly defined."""
        # Check tool-specific parameters
        assert "target" in GameObjectToolFormat.PARAMETERS
        assert "components_to_add" in GameObjectToolFormat.PARAMETERS
        
        # Verify parameter structure
        target_param = GameObjectToolFormat.PARAMETERS["target"]
        assert "type" in target_param
        assert "description" in target_param
        assert "examples" in target_param
        assert "validation_rules" in target_param
    
    def test_get_parameter_definition_inheritance(self):
        """Test that parameter definitions are correctly inherited."""
        # Tool-specific parameter
        target_def = GameObjectToolFormat.get_parameter_definition("target")
        assert target_def is not None
        assert target_def["description"] == "Reference to a GameObject to operate on"
        
        # Common parameter (inherited from base class)
        position_def = GameObjectToolFormat.get_parameter_definition("position")
        assert position_def is not None
        assert position_def["description"] == "3D position in world space"
        
        # Non-existent parameter
        assert GameObjectToolFormat.get_parameter_definition("non_existent") is None
    
    def test_get_required_parameters(self):
        """Test that required parameters are correctly defined for actions."""
        # Test getting required parameters for different actions
        assert GameObjectToolFormat.get_required_parameters("create") == ["name"]
        assert GameObjectToolFormat.get_required_parameters("delete") == ["target"]
        assert GameObjectToolFormat.get_required_parameters("add_component") == ["target", "components_to_add"]
        
        # Non-existent action
        assert GameObjectToolFormat.get_required_parameters("non_existent") == []
    
    def test_get_valid_actions(self):
        """Test that valid actions are correctly defined."""
        assert set(GameObjectToolFormat.get_valid_actions()) == {"create", "delete", "modify", "add_component"}


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 