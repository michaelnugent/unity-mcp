"""
Tests for the BaseTool class, which handles common validation logic.
"""
import pytest
from unittest.mock import MagicMock, patch
from tools.base_tool import BaseTool
from unity_connection import ParameterValidationError

class MockTool(BaseTool):
    """Test implementation of BaseTool with validation rules."""
    
    tool_name = "test_tool"
    
    required_params = {
        "create": {"name": str, "type": str},
        "modify": {"id": str}
    }
    
    vector3_params = ["position", "rotation", "scale"]
    
    def additional_validation(self, action, params):
        if action == "special" and "special_param" not in params:
            raise ParameterValidationError("special_param required for special action")

@pytest.fixture
def test_tool(mock_context, mock_unity_connection):
    """Fixture providing an instance of the test tool."""
    tool = MockTool(mock_context)
    tool.unity_conn = mock_unity_connection  # Explicitly set the mock
    return tool

def test_validate_params_required(test_tool):
    """Test validation of required parameters."""
    # Valid parameters
    test_tool.validate_params("create", {"name": "TestObject", "type": "Cube"})
    
    # Missing required parameter
    with pytest.raises(ParameterValidationError, match="'name' parameter"):
        test_tool.validate_params("create", {"type": "Cube"})
    
    # Wrong type
    with pytest.raises(ParameterValidationError, match="type"):
        test_tool.validate_params("create", {"name": "TestObject", "type": 123})

def test_validate_params_vector3(test_tool):
    """Test validation of Vector3 parameters."""
    # Valid vector3 parameters
    test_tool.validate_params("create", {
        "name": "TestObject", 
        "type": "Cube",
        "position": [0, 1, 0]
    })
    
    # Invalid vector3 - wrong number of elements
    with pytest.raises(ParameterValidationError, match="Vector3 must have exactly 3 components"):
        test_tool.validate_params("create", {
            "name": "TestObject", 
            "type": "Cube",
            "position": [0, 1]
        })
    
    # Invalid vector3 - wrong type
    with pytest.raises(ParameterValidationError, match="Expected list, tuple or dict"):
        test_tool.validate_params("create", {
            "name": "TestObject", 
            "type": "Cube",
            "position": "0,1,0"
        })

def test_additional_validation(test_tool):
    """Test additional validation logic specific to a tool."""
    # Valid parameters for special action
    test_tool.validate_params("special", {"special_param": "value"})
    
    # Invalid parameters for special action
    with pytest.raises(ParameterValidationError, match="special_param required"):
        test_tool.validate_params("special", {})

@pytest.mark.asyncio
async def test_send_command_async(test_tool, mock_unity_connection):
    """Test async version of send_command."""
    # Set up mock response for the async test
    expected_response = {"success": True, "message": "Operation successful", "data": {"id": "123"}}
    
    # Explicitly mock the 'create' action response
    mock_unity_connection.mock_action("create", expected_response)
    
    # Call send_command_async with valid parameters
    result = await test_tool.send_command_async("test_tool", {
        "action": "create",
        "name": "TestObject",
        "type": "Cube"
    })
    
    # Check result
    assert result == expected_response
    
    # Check mock was called with correct arguments
    mock_unity_connection.send_command.assert_called_with("test_tool", {
        "action": "create",
        "name": "TestObject",
        "type": "Cube"
    }) 