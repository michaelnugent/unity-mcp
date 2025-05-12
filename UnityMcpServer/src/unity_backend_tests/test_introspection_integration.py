"""
Tests for the Introspection Tool with a real Unity Editor instance.

These tests validate that the introspection tool works correctly with a live
Unity Editor instance rather than using mocks.
"""

import pytest
import logging
import time
import json
from typing import Dict, Any, List, Optional

from tools.introspection_tool import IntrospectionTool
from tools.manage_gameobject import GameObjectTool
from tools.manage_scene import SceneTool
from exceptions import UnityCommandError, ParameterValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-introspection-integration")

class TestIntrospectionToolIntegration:
    """Test Introspection Tool with a real Unity Editor instance."""

    def setup_method(self):
        """Set up the test environment."""
        self.introspection_tool = IntrospectionTool()
        
    def test_list_tools(self, unity_conn):
        """Test listing all available tools with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture (used for other tools)
        """
        # Use the real Unity connection
        self.introspection_tool.unity_conn = unity_conn
        
        # List all available tools
        result = self.introspection_tool.send_command("introspection_tool", {
            "action": "list_tools"
        })
        
        # Log the result
        logger.info(f"List tools response: {result}")
        
        # Verify the response structure
        assert result["success"] is True
        assert "message" in result
        assert "data" in result
        assert "tools" in result["data"]
        
        # Check that the result contains the expected tools
        tools = result["data"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check for essential tools
        essential_tools = ["manage_script", "manage_scene", "manage_gameobject", "manage_editor"]
        for tool in essential_tools:
            assert tool in tools
    
    def test_get_tool_info(self, unity_conn):
        """Test getting information about a specific tool with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture (used for other tools)
        """
        # Use the real Unity connection
        self.introspection_tool.unity_conn = unity_conn
        
        # Get information about the GameObject tool
        tool_name = "manage_gameobject"
        result = self.introspection_tool.send_command("introspection_tool", {
            "action": "get_tool_info",
            "tool_name": tool_name
        })
        
        # Log the result
        logger.info(f"Get tool info response for {tool_name}: {result}")
        
        # Verify the response structure
        assert result["success"] is True
        assert "message" in result
        assert "data" in result
        assert "name" in result["data"]
        assert result["data"]["name"] == tool_name
        assert "description" in result["data"]
        
        # Should have parameter documentation
        assert "parameter_documentation" in result["data"]
    
    def test_get_parameter_info(self, unity_conn):
        """Test getting information about a specific parameter with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture (used for other tools)
        """
        # Use the real Unity connection
        self.introspection_tool.unity_conn = unity_conn
        
        # Get information about the 'position' parameter of the GameObject tool
        tool_name = "manage_gameobject"
        param_name = "position"
        result = self.introspection_tool.send_command("introspection_tool", {
            "action": "get_parameter_info",
            "tool_name": tool_name,
            "parameter_name": param_name
        })
        
        # Log the result
        logger.info(f"Get parameter info response for {tool_name}.{param_name}: {result}")
        
        # Verify the response structure
        assert result["success"] is True
        assert "message" in result
        assert "data" in result
        assert "documentation" in result["data"]
        assert "parameter" in result["data"]["documentation"]
        assert result["data"]["documentation"]["parameter"] == param_name
        
        # Should have description, examples, and validation rules
        param_doc = result["data"]["documentation"]
        assert "description" in param_doc
        assert "examples" in param_doc
        assert "validation_rules" in param_doc
        
        # Position should allow vector3 formats
        examples = param_doc["examples"]
        assert len(examples) > 0
        
        # Test a vector example
        vector_example = None
        for example in examples:
            if isinstance(example, list) and len(example) == 3:
                vector_example = example
                break
        
        # If we found a vector example, test it with the GameObject tool
        if vector_example:
            gameobject_tool = GameObjectTool()
            gameobject_tool.unity_conn = unity_conn
            
            # Create a GameObject using the example position
            create_result = gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": "TestIntrospectionPosition",
                "position": vector_example
            })
            
            # Log the result
            logger.info(f"Create GameObject with example position: {create_result}")
            
            # Verify the result
            assert create_result["success"] is True
    
    def test_get_action_info(self, unity_conn):
        """Test getting information about a specific action with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture (used for other tools)
        """
        # Use the real Unity connection
        self.introspection_tool.unity_conn = unity_conn
        
        # Get information about the 'create' action of the GameObject tool
        tool_name = "manage_gameobject"
        action_name = "create"
        result = self.introspection_tool.send_command("introspection_tool", {
            "action": "get_action_info",
            "tool_name": tool_name,
            "action_name": action_name
        })
        
        # Log the result
        logger.info(f"Get action info response for {tool_name}.{action_name}: {result}")

        # Verify the response structure
        assert result["success"] is True
        assert "message" in result
        assert "data" in result
        assert "documentation" in result["data"]
        assert "action" in result["data"]["documentation"]
        assert result["data"]["documentation"]["action"] == action_name
        assert result["data"]["documentation"]["valid_action"] is True
        
        # Should have required parameters
        assert "required_parameters" in result["data"]["documentation"]
        required_params = result["data"]["documentation"]["required_parameters"]
        assert len(required_params) > 0
        
        # Required parameters for create should include 'name'
        has_name_param = False
        for param in required_params:
            if param.get("name") == "name":
                has_name_param = True
                break
        assert has_name_param, "The 'name' parameter should be required for the 'create' action"
    
    def test_list_actions(self, unity_conn):
        """Test listing all available actions for a tool with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture (used for other tools)
        """
        # Use the real Unity connection
        self.introspection_tool.unity_conn = unity_conn
        
        # List all available actions for the Scene tool
        tool_name = "manage_scene"
        result = self.introspection_tool.send_command("introspection_tool", {
            "action": "list_actions",
            "tool_name": tool_name
        })
        
        # Log the result
        logger.info(f"List actions response for {tool_name}: {result}")
        
        # Verify the response structure
        assert result["success"] is True
        assert "message" in result
        assert "data" in result
        assert "actions" in result["data"]
        
        # Check that the result contains expected actions
        actions = result["data"]["actions"]
        assert isinstance(actions, list)
        assert len(actions) > 0
        
        # Check for essential actions
        essential_actions = ["open", "create", "save", "get_scene_info"]
        for action in essential_actions:
            assert action in actions
    
    def test_error_response_enhancement(self, unity_conn):
        """Test that error responses include enhanced documentation with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture (used for other tools)
        """
        # Use the real Unity connection
        scene_tool = SceneTool()
        scene_tool.unity_conn = unity_conn
        
        # Try to send an invalid action
        invalid_action = "invalid_action"
        try:
            result = scene_tool.send_command("manage_scene", {
                "action": invalid_action
            })
            
            # Log the result
            logger.info(f"Invalid action response: {result}")
            
            # If we get a successful response (which is unexpected),
            # manually verify that it contains an error about the invalid action
            assert result["success"] is False
            assert invalid_action in result["error"].lower()
            
            # Check if the error contains a list of valid actions
            error_message = result["error"].lower()
            assert "valid actions" in error_message or "available actions" in error_message
            
            # Should list at least some of the valid actions
            common_actions = ["open", "create", "save"]
            assert any(action in error_message for action in common_actions)
            
        except (ParameterValidationError, UnityCommandError) as e:
            # This is the expected path - server should catch the invalid action
            error_message = str(e).lower()
            logger.info(f"Validation error (expected): {error_message}")
            
            # Error message should mention the invalid action
            assert invalid_action in error_message
            
            # Check if the error message includes enhanced documentation
            documentation_terms = ["valid actions", "available actions", "list of actions"]
            has_enhanced_docs = any(term in error_message for term in documentation_terms)
            
            # Fail the test if documentation enhancement is not present
            assert has_enhanced_docs, "Error response must include enhanced documentation with suggested actions"
            
            # Should list at least some of the valid actions
            common_actions = ["open", "create", "save"]
            assert any(action in error_message for action in common_actions)
    
    def test_parameter_validation_with_example(self, unity_conn):
        """Test that parameter validation includes examples in error responses"""
        # Use a real Unity connection
        game_object_tool = GameObjectTool()
        game_object_tool.unity_conn = unity_conn
        
        # Attempt to create a GameObject with an invalid position (should be a Vector3)
        try:
            result = game_object_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": "TestObject",
                "position": "not_a_valid_position"  # This should trigger a validation error
            })
            
            # If we get a response (which means it didn't throw an exception),
            # check that it contains a validation error
            assert result["success"] is False, "Command should have failed validation"
            
            # Check if the error message mentions the position parameter
            error_msg = result["error"].lower()
            logger.info(f"Position validation error: {error_msg}")
            
            # Verify essential elements in the error message
            assert "position" in error_msg, "Error should mention 'position' parameter"
            assert "valid" in error_msg, "Error should indicate validity issue"
            
            # Check for any helpful guidance in the error
            helpful_terms = ["array", "vector", "list", "coordinate", "number", "format"]
            assert any(term in error_msg for term in helpful_terms), "Error should include helpful guidance"
            
        except ParameterValidationError as e:
            # This is an acceptable path - validation error caught before sending
            error_msg = str(e).lower()
            logger.info(f"Validation error (expected): {error_msg}")
            
            # Verify essential elements in the error message
            assert "position" in error_msg, "Error should mention 'position' parameter"
            assert "valid" in error_msg, "Error should indicate validity issue"
            
            # Check for any helpful guidance in the error
            helpful_terms = ["array", "vector", "list", "coordinate", "number", "format"]
            assert any(term in error_msg for term in helpful_terms), "Error should include helpful guidance"

# Run the tests if this script is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 