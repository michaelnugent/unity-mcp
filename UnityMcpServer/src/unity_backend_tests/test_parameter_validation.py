"""
Tests for parameter validation and error message enhancements with a real Unity backend.

These tests validate that parameter validation and enhanced error messages work
correctly with a live Unity Editor instance rather than using mocks.
"""

import pytest
import logging
import time
import json
import re
from typing import Dict, Any, List, Optional

from tools.manage_gameobject import GameObjectTool
from tools.manage_scene import SceneTool
from tools.manage_script import ScriptTool
from tools.manage_asset import AssetTool
from exceptions import UnityCommandError, ParameterValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-parameter-validation")

class TestParameterValidation:
    """Test parameter validation and error message clarity with a real Unity Editor instance."""

    def setup_method(self):
        """Set up the test environment."""
        self.gameobject_tool = GameObjectTool()
        self.scene_tool = SceneTool()
        self.script_tool = ScriptTool()
        self.asset_tool = AssetTool()
        
    def test_clear_error_no_undefined(self, unity_conn):
        """Test that error messages do not contain 'undefined' type references.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create a GameObject with an invalid position type
        try:
            self.gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": "TestInvalidPosition",
                "position": "invalid_position"  # Invalid type for position
            })
            assert False, "Expected a validation error but none was raised"
        except ParameterValidationError as e:
            error_message = str(e)
            logger.info(f"Error message for invalid position: {error_message}")
            
            # Error should not contain the word "undefined"
            assert "undefined" not in error_message.lower()
            
            # Error should contain a clear type description
            assert any(type_name in error_message for type_name in ["array", "list", "vector", "[x, y, z]", "Vector3"])
    
    def test_script_tool_parameter_handling(self, unity_conn):
        """Test script tool correctly handles content parameter.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.script_tool.unity_conn = unity_conn
        
        # Test missing required parameters
        try:
            self.script_tool.send_command("manage_script", {
                "action": "create",
                "name": "TestScript"
                # Missing path and contents parameters
            })
            assert False, "Expected a validation error but none was raised"
        except ParameterValidationError as e:
            error_message = str(e)
            logger.info(f"Error message for missing script parameters: {error_message}")
            
            # Error should specifically mention missing path and contents
            assert "path" in error_message
            assert "contents" in error_message
            
            # Error should not mention non-required parameters
            assert "script_type" not in error_message
        
        # Now test with a valid script creation
        script_contents = """
using UnityEngine;

public class TestScript : MonoBehaviour
{
    void Start()
    {
        Debug.Log("Test script created via MCP");
    }
}
"""
        try:
            # Try creating the script
            result = self.script_tool.send_command("manage_script", {
                "action": "create",
                "name": "TestScript",
                "path": "Assets/Scripts",
                "contents": script_contents,
                "script_type": "MonoBehaviour"
            })
            
            logger.info(f"Create script response: {result}")
            
            # If script already exists, we'll get a specific error
            # Check for either success OR the specific "already exists" error
            is_success = result.get("success") is True
            is_already_exists = (result.get("success") is False and 
                                "already exists" in result.get("error", ""))
            
            assert is_success or is_already_exists, f"Expected success or 'already exists' error, got: {result}"
            
            # If script already exists, try updating it instead
            if is_already_exists:
                update_result = self.script_tool.send_command("manage_script", {
                    "action": "update",
                    "name": "TestScript",
                    "path": "Assets/Scripts",
                    "contents": script_contents,
                    "script_type": "MonoBehaviour"
                })
                
                logger.info(f"Update script response: {update_result}")
                assert update_result.get("success") is True, f"Failed to update script: {update_result}"
                
        except Exception as e:
            assert False, f"Did not expect an error with valid script creation: {str(e)}"
    
    def test_format_examples_in_errors(self, unity_conn):
        """Test that error messages include format examples for complex parameters.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Try creating a GameObject with invalid component properties format
        try:
            self.gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": "TestInvalidProperties",
                "component_properties": "not_an_object"  # Invalid type
            })
            assert False, "Expected a validation error but none was raised"
        except ParameterValidationError as e:
            error_message = str(e)
            logger.info(f"Error message for invalid component_properties: {error_message}")
            
            # Error should include the word "Example" and suggest correct format
            assert "Example" in error_message
            
            # Error should contain example format with curly braces (for objects)
            assert "{" in error_message and "}" in error_message
    
    def test_vector_format_options(self, unity_conn):
        """Test that vector parameters accept different formats.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Test array format
        try:
            array_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": "TestVectorArray",
                "position": [1, 2, 3],
                "rotation": [0, 90, 0],
                "scale": [1, 1, 1]
            })
            
            logger.info(f"Create GameObject with array format: {array_result}")
            assert array_result["success"] is True
        except Exception as e:
            assert False, f"Did not expect an error with array vector format: {str(e)}"
        
        # Test object format
        try:
            object_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": "TestVectorObject",
                "position": {"x": 4, "y": 5, "z": 6},
                "rotation": {"x": 0, "y": 180, "z": 0},
                "scale": {"x": 2, "y": 2, "z": 2}
            })
            
            logger.info(f"Create GameObject with object format: {object_result}")
            assert object_result["success"] is True
        except Exception as e:
            assert False, f"Did not expect an error with object vector format: {str(e)}"
    
    def test_consistent_action_validation(self, unity_conn):
        """Test that action validation is consistent across tools.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        self.script_tool.unity_conn = unity_conn
        self.scene_tool.unity_conn = unity_conn
        
        # Try invalid actions for each tool and verify error format is consistent
        tools_to_test = [
            (self.gameobject_tool, "manage_gameobject"),
            (self.script_tool, "manage_script"),
            (self.scene_tool, "manage_scene")
        ]
        
        for tool, command_type in tools_to_test:
            try:
                tool.send_command(command_type, {
                    "action": "invalid_action"
                })
                assert False, f"Expected a validation error for {command_type} but none was raised"
            except ParameterValidationError as e:
                error_message = str(e)
                logger.info(f"Error message for invalid action in {command_type}: {error_message}")
                
                # All error messages should mention "invalid action"
                assert "invalid" in error_message.lower() and "action" in error_message.lower()
                
                # All error messages should list valid actions
                assert "valid" in error_message.lower() and ("actions" in error_message.lower() or ":" in error_message)
    
    def test_validation_before_unity_errors(self, unity_conn):
        """Test that validation errors are caught before sending to Unity.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.asset_tool.unity_conn = unity_conn
        
        # Try an operation that would fail in Unity but should be caught by validation first
        try:
            self.asset_tool.send_command("manage_asset", {
                "action": "create_asset",
                "path": "Assets/Materials/TestMaterial.mat",
                "asset_type": 12345  # Wrong type - should be string
            })
            assert False, "Expected a validation error but none was raised"
        except ParameterValidationError as e:
            error_message = str(e)
            logger.info(f"Validation error for invalid asset_type: {error_message}")
            
            # Should be caught as a parameter validation error, not a Unity command error
            assert "asset_type" in error_message
            assert "12345" in error_message
        except UnityCommandError:
            assert False, "Expected a parameter validation error but got a Unity command error"
    
    def test_action_case_insensitivity(self, unity_conn):
        """Test that actions are case-insensitive.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Try to use an action with non-standard capitalization
        try:
            # Using CREATE (uppercase) should work the same as "create"
            result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "CREATE",
                "name": "TestCaseInsensitivity"
            })
            
            logger.info(f"Case-insensitive action response: {result}")
            assert result["success"] is True, "Expected success when using uppercase action"
            
        except ParameterValidationError as e:
            # If we get a validation error, it should not be about the action capitalization
            error_message = str(e)
            logger.info(f"Validation error: {error_message}")
            
            # The error should not be about the action being invalid
            assert "invalid action" not in error_message.lower()
            assert "action must be one of" not in error_message.lower()

# Run the tests if this script is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 