"""
Tests for Scene operations in the Unity backend.

These tests validate scene creation, loading, saving, and other operations with
a live Unity Editor instance rather than using mocks.

IMPORTANT: These tests have been modified to avoid triggering popup windows in Unity.
We focus only on parameter validation and safe read operations that don't modify
the scene or create new ones.
"""

import pytest
import logging
import os
from typing import Dict, Any

from tools.manage_scene import SceneTool
from exceptions import UnityCommandError, ParameterValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-scene-operations")

class TestSceneOperations:
    """Test Scene operations against a real Unity instance.
    
    These tests validate that we can get information about scenes and properly
    validate parameters without modifying scenes (which can cause popups).
    """

    def setup_method(self):
        """Set up the test environment.
        
        Creates a new instance of the tool to be tested, initially
        without a real Unity connection.
        """
        self.scene_tool = SceneTool()

    def test_scene_operations_read_only(self, unity_conn):
        """Test read-only scene operations to ensure they work properly.
    
        This test only performs operations that don't modify scenes to
        avoid popup windows in Unity.
    
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.scene_tool.unity_conn = unity_conn
    
        # Get scene info - this should work without causing popups
        scene_info_result = self.scene_tool.send_command("manage_scene", {
            "action": "get_scene_info"
        })
    
        # Log the scene info result
        logger.info(f"Get scene info response: {scene_info_result}")
    
        # Verify we get a valid response
        assert scene_info_result["success"] is True
        assert "message" in scene_info_result
        
        # Test getting open scenes - should also work without popups
        open_scenes_result = self.scene_tool.send_command("manage_scene", {
            "action": "get_open_scenes"
        })
        
        logger.info(f"Get open scenes response: {open_scenes_result}")
        assert open_scenes_result["success"] is True
        assert "message" in open_scenes_result

    def test_parameter_validation_errors(self, unity_conn):
        """Test that parameter validation errors are correctly raised and formatted.
        
        This test verifies that when parameters are missing or invalid, the validation
        layer correctly identifies and reports the issues with clear error messages.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.scene_tool.unity_conn = unity_conn
        
        # Test missing required parameter (path) for open action
        try:
            self.scene_tool.send_command("manage_scene", {
                "action": "open"
                # Missing required "path" parameter
            })
            pytest.fail("Expected ParameterValidationError for missing path")
        except ParameterValidationError as e:
            # Validate the error message
            error_message = str(e)
            
            # Error should mention the missing parameter
            assert "path" in error_message
            
            # Error should be clear about what's wrong
            assert "requires" in error_message.lower() or "missing" in error_message.lower()
            
            # Log the error message for debugging
            logger.info(f"Validation error message: {error_message}")
        except UnityCommandError as e:
            # This is also acceptable - the Unity backend might reject it directly
            error_message = str(e)
            assert "path" in error_message.lower()
            logger.info(f"Unity command error: {error_message}")
        
        # Test missing required parameter (prefab_path) for instantiate action
        try:
            self.scene_tool.send_command("manage_scene", {
                "action": "instantiate",
                "name": "TestObject"
                # Missing required "prefab_path" parameter
            })
            pytest.fail("Expected ParameterValidationError for missing prefab_path")
        except ParameterValidationError as e:
            # Validate the error message
            error_message = str(e)
            
            # Error should mention the missing parameter
            assert "prefab_path" in error_message
            
            # Error should be clear about what's wrong
            assert "requires" in error_message.lower() or "missing" in error_message.lower()
            
            # Log the error message for debugging
            logger.info(f"Validation error message: {error_message}")
        except UnityCommandError as e:
            # This is also acceptable - the Unity backend might reject it directly
            error_message = str(e)
            assert "prefab" in error_message.lower() or "path" in error_message.lower()
            logger.info(f"Unity command error: {error_message}")

    def test_vector_parameter_handling(self, unity_conn):
        """Test handling of vector parameters in scene operations.
        
        This test verifies that vector parameters (position, rotation, scale)
        can be correctly provided in different formats.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.scene_tool.unity_conn = unity_conn
        
        # Test parameter validation for move operation with array format
        try:
            # We don't expect this to succeed since the GameObject doesn't exist,
            # but the parameter validation should work
            result = self.scene_tool.send_command("manage_scene", {
                "action": "move",
                "game_object_name": "NonExistentObject",
                "position": [1, 2, 3]  # Array format
            })
            
            # Log the response
            logger.info(f"Move operation with array format response: {result}")
            
            # If we got a response (not an exception), the parameter validation passed
            # The operation might still fail due to the non-existent GameObject
            assert "success" in result
            if not result.get("success", False):
                error_msg = result.get("error", "")
                # The error should not be about parameter validation
                assert "parameter" not in error_msg.lower()
                assert "validation" not in error_msg.lower()
                logger.info(f"Move operation failed as expected (missing GameObject): {error_msg}")
                
        except ParameterValidationError as e:
            # Parameter validation can also happen via exceptions
            error_message = str(e)
            
            # If it's about validation, it should not be about the vector format
            assert "position" not in error_message.lower()
            assert "vector" not in error_message.lower()
            assert "format" not in error_message.lower()
            
            logger.info(f"Parameter validation error (not related to vector format): {error_message}")
        
        # Test parameter validation for rotate operation with object format
        try:
            # Again, we don't expect the operation to succeed
            result = self.scene_tool.send_command("manage_scene", {
                "action": "rotate",
                "game_object_name": "NonExistentObject",
                "rotation": {"x": 90, "y": 0, "z": 0}  # Object format
            })
            
            # Log the response
            logger.info(f"Rotate operation with object format response: {result}")
            
            # Check that parameter validation succeeded
            assert "success" in result
            if not result.get("success", False):
                error_msg = result.get("error", "")
                # The error should not be about parameter validation
                assert "parameter" not in error_msg.lower()
                assert "validation" not in error_msg.lower()
                logger.info(f"Rotate operation failed as expected (missing GameObject): {error_msg}")
                
        except ParameterValidationError as e:
            # Parameter validation can also happen via exceptions
            error_message = str(e)
            
            # If it's about validation, it should not be about the vector format
            assert "rotation" not in error_message.lower()
            assert "vector" not in error_message.lower()
            assert "format" not in error_message.lower()
            
            logger.info(f"Parameter validation error (not related to vector format): {error_message}")
            
    def test_get_scene_info(self, unity_conn):
        """Test getting scene information.
        
        This test verifies that we can get information about the current scene,
        which should work regardless of the scene state.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.scene_tool.unity_conn = unity_conn
        
        # Get scene info
        result = self.scene_tool.send_command("manage_scene", {
            "action": "get_scene_info"
        })
        
        # Log the complete response
        logger.info(f"Get scene info response: {result}")
        
        # This operation should always succeed
        assert result["success"] is True
        assert "message" in result
        
        # The response should mention the scene
        assert "scene" in result["message"].lower()
        
        # If data is included, it should have expected fields
        if "data" in result:
            if isinstance(result["data"], dict):
                # Some of these fields should be present
                expected_fields = ["name", "path", "build_index", "is_dirty"]
                
                # At least one of the expected fields should be present
                found_fields = [field for field in expected_fields if field in result["data"]]
                assert len(found_fields) > 0, f"None of the expected fields {expected_fields} were found in {result['data']}"

    def test_get_open_scenes(self, unity_conn):
        """Test retrieving open scenes from a real Unity instance.
    
        This test validates that we can successfully get a list of all open
        scenes from the Unity Editor.
    
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.scene_tool.unity_conn = unity_conn
    
        # Get list of open scenes
        result = self.scene_tool.send_command("manage_scene", {
            "action": "get_open_scenes"
        })
    
        # Log the complete response
        logger.info(f"Get open scenes response: {result}")
    
        # Validate the response
        assert result["success"] is True
        assert "message" in result
        
        # The response should mention scenes
        assert "scene" in result["message"].lower()
        
        # If response includes data, it should be structured as expected
        if "data" in result:
            assert isinstance(result["data"], list) or isinstance(result["data"], dict) 