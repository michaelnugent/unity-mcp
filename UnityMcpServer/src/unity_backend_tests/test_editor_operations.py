"""
Tests for Editor operations with a real Unity instance.

These tests validate that the Editor tool works correctly with a real Unity Editor.
They focus on basic editor state operations like getting the current scene.
"""

import pytest
import logging
from typing import Dict, Any

from tools.manage_editor import EditorTool
from exceptions import UnityCommandError, ParameterValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-editor-operations")

class TestEditorOperations:
    """Test editor operations with a real Unity Editor."""
    
    def setup_method(self):
        """Set up the EditorTool for testing."""
        self.editor_tool = EditorTool()
    
    def test_get_editor_state(self, unity_conn):
        """Test getting the editor state from a real Unity instance.
        
        This test validates that the EditorTool can successfully get the state
        from a real Unity Editor, which is a good first test to ensure the connection
        is working properly.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.editor_tool.unity_conn = unity_conn
        
        # Get the editor state using send_command
        result = self.editor_tool.send_command("manage_editor", {
            "action": "get_state"
        })
        
        # Log the entire response for debugging
        logger.info(f"Complete editor state response: {result}")
        
        # Validate the response (simplified for initial test)
        assert result["success"] is True
        assert "message" in result
        
        # The response should at least include a message about the state
        assert "state" in result["message"].lower()
        
        # Try to get the active tool which should be a more detailed operation
        active_tool_result = self.editor_tool.send_command("manage_editor", {
            "action": "get_active_tool"
        })
        
        logger.info(f"Active tool response: {active_tool_result}")
        
        # This should also succeed
        assert active_tool_result["success"] is True
    
    def test_string_parameter_acceptance(self, unity_conn):
        """Test that string parameters are accepted correctly.
        
        This test validates that string parameters are properly accepted
        and don't cause validation errors, while handling the parameter naming 
        inconsistency between Python (tool_name) and Unity (toolName).
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.editor_tool.unity_conn = unity_conn
        
        # Try to set the active tool using a string parameter
        tool_name = "Move"  # Use a simple Unity tool name
        
        # Include both parameter names to work around inconsistency
        # Python validation expects tool_name but Unity might expect toolName
        result = self.editor_tool.send_command("manage_editor", {
            "action": "set_active_tool",
            "tool_name": tool_name,  # For Python validation
            "toolName": tool_name    # For Unity backend
        })
        
        # Log the complete response
        logger.info(f"Set active tool response: {result}")
        
        # For this test, we'll accept either success or a specific Unity error
        # since we're testing parameter validation, not tool functionality
        if not result.get("success", False):
            error_msg = result.get("error", "")
            # If it fails, it should not be because of missing parameters
            assert "required" not in error_msg
            assert "parameter" not in error_msg
            logger.info(f"Tool rejected with error, but not due to parameter validation: {error_msg}")
        
        # Get the active tool to verify connection still works
        state_result = self.editor_tool.send_command("manage_editor", {
            "action": "get_active_tool"
        })
        
        # Log the current active tool
        logger.info(f"Active tool response after setting: {state_result}")
        assert state_result["success"] is True
    
    def test_parameter_validation_error(self, unity_conn):
        """Test that parameter validation errors are correctly raised and formatted.
        
        This test verifies that when a parameter is missing or invalid, the validation
        layer correctly identifies and reports the issue with a clear error message.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.editor_tool.unity_conn = unity_conn
        
        # Try to call set_active_tool without the required tool_name parameter
        try:
            self.editor_tool.send_command("manage_editor", {
                "action": "set_active_tool"
                # Missing tool_name parameter
            })
            pytest.fail("Expected ParameterValidationError for missing tool_name")
        except ParameterValidationError as e:
            # Validate the error message
            error_message = str(e)
            
            # Error should mention the missing parameter
            assert "tool_name" in error_message
            
            # Error should be clear about what's missing
            assert "requires" in error_message.lower() or "missing" in error_message.lower()
            
            # Log the error message for debugging
            logger.info(f"Validation error message: {error_message}")
        except UnityCommandError as e:
            # This is also acceptable - the Unity backend might reject it directly
            error_message = str(e)
            assert "tool" in error_message.lower() and "name" in error_message.lower()
            logger.info(f"Unity command error: {error_message}")

    def test_vector_parameter_formats(self, unity_conn):
        """Test that vector parameters accept different formats.
        
        This test verifies that vector parameters can be provided in both array
        format [x, y, z] and object format {"x": x, "y": y, "z": z}.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.editor_tool.unity_conn = unity_conn
        
        # This test uses GameObject operations since Editor doesn't have vector params
        from tools.manage_gameobject import GameObjectTool
        gameobject_tool = GameObjectTool()
        gameobject_tool.unity_conn = unity_conn
        
        # Test array format
        array_result = gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestVectorArray",
            "position": [1, 2, 3],
            "rotation": [0, 90, 0],
            "scale": [1, 1, 1]
        })
        assert array_result["success"] is True
        
        # Test object format
        object_result = gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestVectorObject",
            "position": {"x": 4, "y": 5, "z": 6},
            "rotation": {"x": 0, "y": 180, "z": 0},
            "scale": {"x": 2, "y": 2, "z": 2}
        })
        assert object_result["success"] is True
        
        # Log the results for debugging
        logger.info(f"Created GameObject with array format: {array_result}")
        logger.info(f"Created GameObject with object format: {object_result}") 