"""
Unit tests for cross-tool parameter validation consistency.

This module contains tests focused on ensuring that similar parameters
are validated consistently across different tools.
"""
import unittest
from unittest.mock import MagicMock, patch
from tools.base_tool import BaseTool
from tools.manage_gameobject import GameObjectTool
from tools.manage_script import ScriptTool
from tools.manage_scene import SceneTool
from tools.manage_asset import AssetTool
from tools.read_console import ConsoleTool
from unity_connection import ParameterValidationError
from validation_utils import validate_param_type

class TestParameterValidationConsistency(unittest.TestCase):
    """Test suite for ensuring consistent parameter validation across different tools."""

    def setUp(self):
        """Set up test environment with mock context and initialize tools."""
        mock_ctx = MagicMock()
        mock_unity_conn = MagicMock()
        
        # Create instances of each tool
        self.gameobject_tool = GameObjectTool(mock_ctx)
        self.gameobject_tool.unity_conn = mock_unity_conn
        
        self.script_tool = ScriptTool(mock_ctx)
        self.script_tool.unity_conn = mock_unity_conn
        
        self.scene_tool = SceneTool(mock_ctx)
        self.scene_tool.unity_conn = mock_unity_conn
        
        self.asset_tool = AssetTool(mock_ctx)
        self.asset_tool.unity_conn = mock_unity_conn
        
        self.console_tool = ConsoleTool(mock_ctx)
        self.console_tool.unity_conn = mock_unity_conn

    def test_action_parameter_consistency(self):
        """Test that action parameters are consistently validated across tools."""
        # Test valid actions in GameObject tool
        try:
            self.gameobject_tool.validate_and_convert_params("get_components", {
                "target": "MainCamera"
            })
        except ParameterValidationError as e:
            assert "action" not in str(e), f"GameObject tool rejected valid action: {str(e)}"
    
        # Test valid actions in Script tool
        try:
            self.script_tool.validate_and_convert_params("read", {
                "name": "TestScript",
                "path": "Assets/Scripts"
            })
        except ParameterValidationError as e:
            assert "action" not in str(e), f"Script tool rejected valid action: {str(e)}"
    
        # Test valid actions in Console tool
        try:
            self.console_tool.validate_and_convert_params("get", {
                "types": ["error"],
                "count": 10
            })
        except ParameterValidationError as e:
            assert "action" not in str(e), f"Console tool rejected valid action: {str(e)}"
    
        # Test invalid action gets rejected with clear message for GameObject tool
        try:
            self.gameobject_tool.validate_and_convert_params("invalid_action", {})
            self.fail("GameObject tool accepted invalid action")
        except ParameterValidationError as e:
            error_msg = str(e)
            assert "invalid_action" in error_msg, "Error didn't mention invalid action name"
            assert "undefined" not in error_msg, "Error used 'undefined' type"
    
        # Test invalid action in Script tool - now should behave consistently with GameObject tool
        try:
            self.script_tool.validate_and_convert_params("invalid_action", {})
            self.fail("Script tool accepted invalid action")
        except ParameterValidationError as e:
            error_msg = str(e)
            assert "invalid_action" in error_msg, "Error didn't mention invalid action name"
            assert "undefined" not in error_msg, "Error used 'undefined' type"
    
        # Test invalid action in Console tool 
        try:
            self.console_tool.validate_and_convert_params("invalid_action", {})
            self.fail("Console tool accepted invalid action")
        except ParameterValidationError:
            # Expected - we just want to make sure it rejects the invalid action
            pass

    def test_path_parameter_consistency(self):
        """Test that path parameters are consistently validated as strings across tools."""
        # Test GameObject tool target path
        try:
            self.gameobject_tool.validate_and_convert_params("delete", {
                "target": 123  # Invalid type (number instead of string)
            })
            self.fail("GameObject tool accepted non-string target path")
        except ParameterValidationError as e:
            assert "target" in str(e), "Error didn't mention parameter name"
            assert "str" in str(e), "Error didn't mention string type requirement"
        
        # Test Script tool path
        try:
            self.script_tool.validate_and_convert_params("read", {
                "name": "TestScript",
                "path": 123  # Invalid type
            })
            self.fail("Script tool accepted non-string path")
        except ParameterValidationError as e:
            assert "path" in str(e), "Error didn't mention parameter name"
            assert "str" in str(e), "Error didn't mention string type requirement"
        
        # Test Asset tool path
        try:
            self.asset_tool.validate_and_convert_params("get_info", {
                "path": 123  # Invalid type
            })
            self.fail("Asset tool accepted non-string path")
        except ParameterValidationError as e:
            assert "path" in str(e), "Error didn't mention parameter name"
            assert "str" in str(e), "Error didn't mention string type requirement"

    def test_vector_parameter_consistency(self):
        """Test that vector parameters are consistently validated across tools."""
        # Test GameObject tool position parameter
        try:
            self.gameobject_tool.validate_and_convert_params("set_position", {
                "target": "Player",
                "position": "invalid"  # Should be a list/array
            })
            self.fail("GameObject tool accepted invalid position")
        except ParameterValidationError as e:
            assert "position" in str(e), "Error didn't mention parameter name"
        
        # Test Scene tool position parameter
        try:
            self.scene_tool.validate_and_convert_params("move", {
                "game_object_name": "Player",
                "position": "invalid"  # Should be a list/array
            })
            self.fail("Scene tool accepted invalid position")
        except ParameterValidationError as e:
            assert "position" in str(e), "Error didn't mention parameter name"

    def test_consistent_error_messages(self):
        """Test that error messages are consistent across tools for similar parameter types."""
        try:
            validate_param_type(123, "test_string", str, "test_action", "test_tool")
            self.fail("validate_param_type accepted incorrect type")
        except ParameterValidationError as e:
            error_msg = str(e)
            assert "test_string" in error_msg, "Error didn't mention parameter name"
            assert "test_action" in error_msg, "Error didn't mention action name"
            assert "test_tool" in error_msg, "Error didn't mention tool name"
            assert "str" in error_msg, "Error didn't mention expected type"
            assert "int" in error_msg, "Error didn't mention actual type" 