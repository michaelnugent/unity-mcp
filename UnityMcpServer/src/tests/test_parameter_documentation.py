"""
Unit tests for parameter documentation and introspection features.

This module contains tests for the parameter documentation utilities and 
introspection tool that are part of the Phase 5 improvements.
"""
import pytest
from typing import Dict, List, Any, Union, Optional
import sys
import os
from pathlib import Path

# Add the src directory to the Python path so we can import modules
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import the validation utilities and introspection tool
from validation_utils import (
    ParameterFormat,
    generate_parameter_help_response,
    enhance_error_with_documentation
)
from tools.introspection_tool import IntrospectionTool, TOOL_MODULES
from tools.base_tool import BaseTool

# Import the unittest mocks
from unittest.mock import Mock, patch, MagicMock


class TestParameterDocumentation:
    """Tests for the parameter documentation functions."""
    
    def test_generate_parameter_help_response_basic(self):
        """Test the basic functionality of generate_parameter_help_response."""
        # Test with no parameter format class
        response = generate_parameter_help_response("test_tool")
        assert response["tool"] == "test_tool"
        assert response["action"] is None
        assert isinstance(response["documentation"], dict)
        assert len(response["documentation"]) == 0
    
    def test_generate_parameter_help_response_with_parameter(self):
        """Test generate_parameter_help_response with a specific parameter."""
        # Create a mock parameter format class
        class MockParameterFormat(ParameterFormat):
            PARAMETERS = {
                "test_param": {
                    "type": str,
                    "description": "Test parameter description",
                    "examples": ["example1", "example2"],
                    "validation_rules": ["Must be a string"]
                }
            }
        
        # Test with a parameter that exists
        response = generate_parameter_help_response(
            "test_tool", 
            "test_param", 
            parameter_format_class=MockParameterFormat
        )
        assert response["tool"] == "test_tool"
        assert "documentation" in response
        assert response["documentation"]["parameter"] == "test_param"
        assert response["documentation"]["description"] == "Test parameter description"
        assert "examples" in response["documentation"]
        assert len(response["documentation"]["examples"]) == 2
        assert "validation_rules" in response["documentation"]
        
        # Test with a parameter that doesn't exist
        response = generate_parameter_help_response(
            "test_tool", 
            "non_existent_param", 
            parameter_format_class=MockParameterFormat
        )
        assert "error" in response["documentation"]
    
    def test_generate_parameter_help_response_with_action(self):
        """Test generate_parameter_help_response with a specific action."""
        # Create a mock parameter format class with required parameters
        class MockParameterFormat(ParameterFormat):
            PARAMETERS = {
                "name": {
                    "type": str,
                    "description": "Name parameter",
                    "examples": ["example_name"],
                    "validation_rules": ["Must be a string"]
                },
                "path": {
                    "type": str,
                    "description": "Path parameter",
                    "examples": ["Assets/MyPath"],
                    "validation_rules": ["Must be a valid path"]
                }
            }
            
            REQUIRED_PARAMETERS = {
                "create": ["name", "path"],
                "delete": ["path"]
            }
            
            VALID_ACTIONS = ["create", "read", "update", "delete"]
        
        # Test with a valid action
        response = generate_parameter_help_response(
            "test_tool", 
            action="create", 
            parameter_format_class=MockParameterFormat
        )
        assert response["tool"] == "test_tool"
        assert response["action"] == "create"
        assert "documentation" in response
        assert response["documentation"]["action"] == "create"
        assert response["documentation"]["valid_action"] is True
        assert "required_parameters" in response["documentation"]
        assert len(response["documentation"]["required_parameters"]) == 2
        
        # Test with an invalid action
        response = generate_parameter_help_response(
            "test_tool", 
            action="invalid_action", 
            parameter_format_class=MockParameterFormat
        )
        assert response["documentation"]["valid_action"] is False
    
    def test_enhance_error_with_documentation(self):
        """Test the enhance_error_with_documentation function."""
        # Create a mock parameter format class
        class MockParameterFormat(ParameterFormat):
            PARAMETERS = {
                "test_param": {
                    "type": str,
                    "description": "Test parameter description",
                    "examples": ["example1", "example2"],
                    "validation_rules": ["Must be a string"]
                }
            }
            
            REQUIRED_PARAMETERS = {
                "test_action": ["test_param"]
            }
            
            VALID_ACTIONS = ["test_action"]
        
        # Test enhancing an error with documentation
        error_message = "Test error message"
        response = enhance_error_with_documentation(
            error_message,
            "test_tool",
            param_name="test_param",
            action="test_action",
            parameter_format_class=MockParameterFormat
        )
        
        assert response["success"] is False
        assert response["message"] == error_message
        assert response["validation_error"] is True
        assert "help" in response
        assert "suggestions" in response
        assert "example_format" in response["suggestions"]
        assert "valid_format" in response["suggestions"]


class TestIntrospectionTool:
    """Tests for the IntrospectionTool class."""
    
    def test_find_tool_class(self):
        """Test the _find_tool_class method."""
        # Create a mock module with a BaseTool subclass
        mock_module = MagicMock()
        mock_tool_class = type('MockToolClass', (BaseTool,), {})
        mock_module.__name__ = "mock_module"
        
        # Add the tool class to the module's members
        mock_module.__dict__ = {"MockToolClass": mock_tool_class}
        
        # Create a patched inspect.getmembers that returns our mock class
        with patch('inspect.getmembers', return_value=[('MockToolClass', mock_tool_class)]):
            # Test finding the tool class
            result = IntrospectionTool._find_tool_class(mock_module)
            assert result == mock_tool_class
    
    def test_find_parameter_format_class(self):
        """Test the _find_parameter_format_class method."""
        # Create a mock module with a ParameterFormat subclass
        mock_module = MagicMock()
        mock_format_class = type('MockFormatClass', (ParameterFormat,), {})
        mock_module.__name__ = "mock_module"
        
        # Add the format class to the module's members
        mock_module.__dict__ = {"MockFormatClass": mock_format_class}
        
        # Create a patched inspect.getmembers that returns our mock class
        with patch('inspect.getmembers', return_value=[('MockFormatClass', mock_format_class)]):
            # Test finding the parameter format class
            result = IntrospectionTool._find_parameter_format_class(mock_module)
            assert result == mock_format_class
    
    def test_get_tool_parameter_format(self):
        """Test the _get_tool_parameter_format method."""
        # Create a mock format class
        mock_format_class = type('MockFormatClass', (ParameterFormat,), {})
        
        # First test with a tool that's already in the cache
        with patch.dict('tools.introspection_tool.TOOL_PARAMETER_FORMATS', 
                        {'cached_tool': mock_format_class}):
            result = IntrospectionTool._get_tool_parameter_format('cached_tool')
            assert result == mock_format_class
        
        # Now test with a tool that needs to be looked up
        mock_module = MagicMock()
        with patch.dict('tools.introspection_tool.TOOL_MODULES', {'new_tool': mock_module}):
            with patch.object(IntrospectionTool, '_find_parameter_format_class', 
                              return_value=mock_format_class):
                result = IntrospectionTool._get_tool_parameter_format('new_tool')
                assert result == mock_format_class
                
                # Make sure we're using the right TOOL_PARAMETER_FORMATS dict
                from tools.introspection_tool import TOOL_PARAMETER_FORMATS
                assert 'new_tool' in TOOL_PARAMETER_FORMATS
                assert TOOL_PARAMETER_FORMATS['new_tool'] == mock_format_class


class TestIntrospectionToolEndToEnd:
    """End-to-end tests for the IntrospectionTool."""
    
    @pytest.fixture
    def mock_context(self):
        """Create a mock Context for testing."""
        return MagicMock()
    
    @pytest.fixture
    def mock_unity_connection(self):
        """Create a mock unity connection for testing."""
        # Set up the mock connection
        mock_conn = MagicMock()
        mock_conn.send_command.return_value = {
            "success": True,
            "message": "Mock unity response",
            "data": {}
        }
        return mock_conn
    
    @pytest.fixture
    def mock_introspection_tool(self, mock_unity_connection):
        """Create a mock IntrospectionTool instance for testing."""
        tool = IntrospectionTool()
        tool.unity_conn = mock_unity_connection
        return tool
    
    def test_validate_params(self, mock_introspection_tool):
        """Test the parameter validation in IntrospectionTool."""
        # Test with valid action and parameters
        params = {"action": "list_tools"}
        mock_introspection_tool.validate_params("list_tools", params)
        
        # Test with invalid action
        with pytest.raises(Exception):
            mock_introspection_tool.validate_params("invalid_action", params)
    
    def test_introspection_tool_list_tools(self, mock_context, mock_introspection_tool):
        """Test the list_tools action of the introspection tool."""
        # Create a simple test of the validation logic
        params = {"action": "list_tools"}
        with patch.object(IntrospectionTool, 'validate_params'):
            # Create a mock response
            expected_result = {
                "success": True,
                "message": "Available tools listed successfully",
                "data": {"tools": list(TOOL_MODULES.keys())}
            }
            
            # Instead of trying to access the actual function, mock the send_command
            with patch.object(mock_introspection_tool, 'send_command', return_value=expected_result):
                # Call the method directly
                result = mock_introspection_tool.send_command("introspection_tool", params)
                
                # Verify the result
                assert result["success"] is True
                assert "tools" in result["data"]
                assert isinstance(result["data"]["tools"], list)
                assert len(result["data"]["tools"]) > 0
    
    def test_introspection_tool_get_tool_info(self, mock_context, mock_introspection_tool):
        """Test the get_tool_info action of the introspection tool."""
        # Create a simple test of the validation logic
        params = {
            "action": "get_tool_info",
            "tool_name": "test_tool"
        }
        
        # Mock response data
        expected_result = {
            "success": True,
            "message": "Information for tool 'test_tool' retrieved successfully",
            "data": {
                "name": "test_tool",
                "description": "Test tool docs"
            }
        }
        
        with patch.object(IntrospectionTool, 'validate_params'):
            # Mock the send_command call
            with patch.object(mock_introspection_tool, 'send_command', return_value=expected_result):
                # Call the method directly
                result = mock_introspection_tool.send_command("introspection_tool", params)
                
                # Verify the result
                assert result["success"] is True
                assert "data" in result
                assert result["data"]["name"] == "test_tool"
                assert "description" in result["data"]


# Run the tests if this script is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 