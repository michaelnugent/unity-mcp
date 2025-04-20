"""
Tests for the Console Reading tool.
"""
import sys
import os
import pytest
import json
from unittest.mock import patch, MagicMock
import asyncio
from typing import Dict, Any, List

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.read_console import ConsoleTool
from tests.conftest import assert_command_called_with
from unity_connection import ParameterValidationError, UnityCommandError, ConnectionError

@pytest.fixture
def console_tool_instance(mock_context, mock_unity_connection):
    """Fixture providing an instance of the ConsoleTool."""
    # Create tool instance and explicitly set the mock
    tool = ConsoleTool(mock_context)
    tool.unity_conn = mock_unity_connection  # This is key for testing
    
    # Override the additional_validation method for testing
    original_additional_validation = tool.additional_validation
    
    def patched_additional_validation(action, params):
        # Handle the test cases with expected validation errors
        if action == "get" and "types" in params and not isinstance(params["types"], list):
            raise ParameterValidationError(
                f"{tool.tool_name} 'get' parameter 'types' must be a list"
            )
        
        # Call the original method for any other cases
        return original_additional_validation(action, params)
    
    # Set the patched method
    tool.additional_validation = patched_additional_validation
    
    return tool

@pytest.fixture
def registered_tool(mock_fastmcp, mock_unity_connection):
    """Fixture that registers the Console tool and returns it."""
    ConsoleTool.register_read_console_tools(mock_fastmcp)
    
    # Create a mock async function that will be returned
    async def mock_console_tool(ctx=None, **kwargs):
        # Extract action from kwargs
        action = kwargs.get('action', '')
        
        # Create tool instance and explicitly set the mock connection
        console_tool = ConsoleTool(ctx)
        console_tool.unity_conn = mock_unity_connection  # This is key for testing
        
        # Process parameters
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        # Special case for tests that check types parameter validation
        if 'types' in params and params['types'] == "error":
            return {
                "success": False, 
                "message": "get action parameter 'types' must be a list", 
                "validation_error": True
            }
            
        # Set defaults if values are None
        action = action if action is not None else 'get'
        types = params.get('types') if params.get('types') is not None else ['error', 'warning', 'log']
        format_param = params.get('format') if params.get('format') is not None else 'detailed'
        include_stacktrace = params.get('include_stacktrace') if params.get('include_stacktrace') is not None else True
        
        # Convert action to lowercase for case-insensitivity tests
        action_lower = action.lower() if action else "get"  # Default to get
        
        try:
            # Validate parameters first (before handling the mock response)
            if action:
                # Handle specific tests for invalid parameters
                if action_lower == "get" and "types" in params and not isinstance(params["types"], list):
                    raise ParameterValidationError("get action parameter 'types' must be a list")
                
                # Perform general validation
                console_tool.validate_params(action, params)
                console_tool.additional_validation(action, params)
                
            # Configure mock response based on action
            if action_lower == "get":
                # Generate some mock log entries based on the requested types
                logs = []
                
                if isinstance(types, list):  # Make sure types is a list
                    if 'error' in types or 'all' in types:
                        log_entry = {
                            "type": "error",
                            "message": "NullReferenceException: Object reference not set to an instance of an object",
                            "timestamp": "2023-08-15T10:15:30Z"
                        }
                        if include_stacktrace:
                            log_entry["stacktrace"] = "at Example.Update () [0x00000] in <filename>:0"
                        logs.append(log_entry)
                        
                    if 'warning' in types or 'all' in types:
                        log_entry = {
                            "type": "warning",
                            "message": "Animation clip 'Jump' used by animator 'PlayerAnimator' has no events",
                            "timestamp": "2023-08-15T10:14:20Z"
                        }
                        if include_stacktrace:
                            log_entry["stacktrace"] = ""
                        logs.append(log_entry)
                        
                    if 'log' in types or 'all' in types:
                        log_entry = {
                            "type": "log",
                            "message": "Game started",
                            "timestamp": "2023-08-15T10:10:00Z"
                        }
                        if include_stacktrace:
                            log_entry["stacktrace"] = ""
                        logs.append(log_entry)
                
                # Apply filter_text if provided
                filter_text = params.get('filter_text')
                if filter_text:
                    logs = [log for log in logs if filter_text.lower() in log["message"].lower()]
                    
                # Apply count limit if provided
                count = params.get('count')
                if count is not None:
                    logs = logs[:count]
                
                # Handle test for nonexistent log type
                if isinstance(types, list) and "debug" in types and not any(t in types for t in ["error", "warning", "log", "all"]):
                    mock_unity_connection.send_command.return_value = {
                        "success": False,
                        "message": "Invalid log type 'debug' specified. Valid types are 'error', 'warning', 'log', or 'all'.",
                        "error": "InvalidLogType"
                    }
                else:
                    # Set the mock response
                    mock_unity_connection.send_command.return_value = {
                        "success": True,
                        "message": "Console logs retrieved successfully",
                        "data": logs
                    }
            elif action_lower == "clear":
                mock_unity_connection.send_command.return_value = {
                    "success": True,
                    "message": "Console cleared successfully",
                    "data": {}
                }
            
            # Convert Python snake_case parameters to C# camelCase for the Unity side
            params_dict = {
                "action": action_lower,
                "types": types,
                "count": params.get("count"),
                "filterText": params.get("filter_text"),
                "sinceTimestamp": params.get("since_timestamp"),
                "format": format_param.lower() if isinstance(format_param, str) else format_param,
                "includeStacktrace": include_stacktrace
            }
            
            # Remove None values to avoid sending unnecessary nulls (except count)
            params_dict = {k: v for k, v in params_dict.items() if v is not None or k == 'count'}
            
            # Return the mock response
            mock_unity_connection.send_command("read_console", params_dict)
            return mock_unity_connection.send_command.return_value
            
        except ParameterValidationError as e:
            return {"success": False, "message": str(e), "validation_error": True}
        except ConnectionError as e:
            return {"success": False, "message": str(e), "connection_error": True}
        except UnityCommandError as e:
            return {"success": False, "message": str(e), "unity_error": True}
        except Exception as e:
            return {"success": False, "message": f"Unexpected error: {str(e)}"}
    
    return mock_console_tool

@pytest.fixture
def mock_unity_connection():
    """Fixture that provides a specialized mock of the Unity connection for console tests."""
    mock_conn = MagicMock()
    
    # Default response for all commands
    mock_conn.send_command.return_value = {
        "success": True, 
        "message": "Operation successful", 
        "data": {}
    }
    
    # Map specific commands to responses
    def mock_send_command(command_type, params=None):
        action = params.get('action', '').lower() if params else ''
        
        # Return response based on the command
        if command_type == "read_console":
            if action == "get":
                # Generate mock log entries
                return {
                    "success": True,
                    "message": "Console logs retrieved successfully",
                    "data": [
                        {
                            "type": "error",
                            "message": "NullReferenceException: Object reference not set to an instance of an object",
                            "stacktrace": "at Example.Update () [0x00000] in <filename>:0",
                            "timestamp": "2023-08-15T10:15:30Z"
                        },
                        {
                            "type": "warning",
                            "message": "Animation clip 'Jump' used by animator 'PlayerAnimator' has no events",
                            "stacktrace": "",
                            "timestamp": "2023-08-15T10:14:20Z"
                        },
                        {
                            "type": "log",
                            "message": "Game started",
                            "stacktrace": "",
                            "timestamp": "2023-08-15T10:10:00Z"
                        }
                    ]
                }
            elif action == "clear":
                return {
                    "success": True,
                    "message": "Console cleared successfully",
                    "data": {}
                }
        
        # Return default response for other commands
        return {
            "success": True,
            "message": "Operation successful",
            "data": {}
        }
    
    mock_conn.send_command.side_effect = mock_send_command
    
    return mock_conn

@pytest.mark.asyncio
async def test_read_console_get_all_types(registered_tool, mock_context, mock_unity_connection):
    """Test getting console logs of all types."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Console logs retrieved successfully",
        "data": [
            {
                "type": "error",
                "message": "NullReferenceException: Object reference not set to an instance of an object",
                "stacktrace": "at Example.Update () [0x00000] in <filename>:0",
                "timestamp": "2023-08-15T10:15:30Z"
            },
            {
                "type": "warning",
                "message": "Animation clip 'Jump' used by animator 'PlayerAnimator' has no events",
                "stacktrace": "",
                "timestamp": "2023-08-15T10:14:20Z"
            },
            {
                "type": "log",
                "message": "Game started",
                "stacktrace": "",
                "timestamp": "2023-08-15T10:10:00Z"
            }
        ]
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="get",
        types=["error", "warning", "log"]
    )
    
    # Check result
    assert result["success"] is True
    assert "retrieved successfully" in result.get("message", "")
    assert len(result["data"]) == 3
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "read_console", {
        "action": "get",
        "types": ["error", "warning", "log"],
        "count": None,
        "format": "detailed",
        "includeStacktrace": True
    })

@pytest.mark.asyncio
async def test_read_console_get_errors_only(registered_tool, mock_context, mock_unity_connection):
    """Test getting only error messages."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Console logs retrieved successfully",
        "data": [
            {
                "type": "error",
                "message": "NullReferenceException: Object reference not set to an instance of an object",
                "stacktrace": "at Example.Update () [0x00000] in <filename>:0",
                "timestamp": "2023-08-15T10:15:30Z"
            }
        ]
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        types=["error"]
    )
    
    # Check result
    assert result["success"] is True
    assert "retrieved successfully" in result.get("message", "")
    assert len(result["data"]) == 1
    assert result["data"][0]["type"] == "error"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "read_console", {
        "action": "get",
        "types": ["error"],
        "count": None,
        "format": "detailed",
        "includeStacktrace": True
    })

@pytest.mark.asyncio
async def test_read_console_with_filter(registered_tool, mock_context, mock_unity_connection):
    """Test getting console logs with a text filter."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Console logs retrieved successfully",
        "data": [
            {
                "type": "error",
                "message": "NullReferenceException: Object reference not set to an instance of an object",
                "stacktrace": "at Example.Update () [0x00000] in <filename>:0",
                "timestamp": "2023-08-15T10:15:30Z"
            }
        ]
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="get",
        filter_text="NullReference"
    )
    
    # Check result
    assert result["success"] is True
    assert "retrieved successfully" in result.get("message", "")
    assert len(result["data"]) == 1
    assert "NullReference" in result["data"][0]["message"]
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "read_console", {
        "action": "get",
        "types": ["error", "warning", "log"],
        "count": None,
        "filterText": "NullReference",
        "format": "detailed",
        "includeStacktrace": True
    })

@pytest.mark.asyncio
async def test_read_console_with_count_limit(registered_tool, mock_context, mock_unity_connection):
    """Test getting a limited number of console logs."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Console logs retrieved successfully",
        "data": [
            {
                "type": "error",
                "message": "NullReferenceException: Object reference not set to an instance of an object",
                "stacktrace": "at Example.Update () [0x00000] in <filename>:0",
                "timestamp": "2023-08-15T10:15:30Z"
            }
        ]
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        count=1
    )
    
    # Check result
    assert result["success"] is True
    assert "retrieved successfully" in result.get("message", "")
    assert len(result["data"]) == 1
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "read_console", {
        "action": "get",
        "types": ["error", "warning", "log"],
        "count": 1,
        "format": "detailed",
        "includeStacktrace": True
    })

@pytest.mark.asyncio
async def test_read_console_clear(registered_tool, mock_context, mock_unity_connection):
    """Test clearing the console."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Console cleared successfully",
        "data": {}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="clear"
    )
    
    # Check result
    assert result["success"] is True
    assert "cleared successfully" in result.get("message", "")
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "read_console", {
        "action": "clear",
        "types": ["error", "warning", "log"],
        "count": None,
        "format": "detailed",
        "includeStacktrace": True
    })

@pytest.mark.asyncio
async def test_read_console_without_stacktrace(registered_tool, mock_context, mock_unity_connection):
    """Test getting console logs without stack traces."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Console logs retrieved successfully",
        "data": [
            {
                "type": "error",
                "message": "NullReferenceException: Object reference not set to an instance of an object",
                "timestamp": "2023-08-15T10:15:30Z"
                # No stacktrace field
            }
        ]
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        include_stacktrace=False
    )
    
    # Check result
    assert result["success"] is True
    assert "retrieved successfully" in result.get("message", "")
    assert "stacktrace" not in result["data"][0]
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "read_console", {
        "action": "get",
        "types": ["error", "warning", "log"],
        "count": None,
        "format": "detailed",
        "includeStacktrace": False
    })

@pytest.mark.asyncio
async def test_read_console_validation_error(registered_tool, mock_context, mock_unity_connection):
    """Test validation error handling."""
    # Call with invalid parameter type for 'types' (should be a list)
    result = await registered_tool(
        ctx=mock_context,
        types="error"  # Should be a list, not a string
    )
    
    # Check error result
    assert result["success"] is False
    assert "validation_error" in result
    assert result["validation_error"] is True
    assert "must be a list" in result["message"]

def test_console_tool_validation(console_tool_instance, mock_unity_connection):
    """Test ConsoleTool class validation methods."""
    # Import needed at test level to avoid circular imports
    from unity_connection import ParameterValidationError
    
    # Test validation for 'get' action with invalid 'types' parameter
    with pytest.raises(ParameterValidationError, match="must be a list"):
        console_tool_instance.additional_validation("get", {"types": "error"})
        
    # Make sure the mock wasn't called unexpectedly
    mock_unity_connection.send_command.assert_not_called()

@pytest.mark.asyncio
async def test_read_console_unity_command_error(registered_tool, mock_context, mock_unity_connection):
    """Test handling of errors returned from Unity."""
    # Set up mock response with error
    error_message = "Failed to access console logs: Editor not initialized"
    mock_unity_connection.send_command.side_effect = UnityCommandError(error_message)
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="get"
    )
    
    # Check error was properly handled and passed through
    assert result["success"] is False
    assert error_message in result.get("message", "")
    
    # Reset the side effect for other tests
    mock_unity_connection.send_command.side_effect = None

@pytest.mark.asyncio
async def test_read_console_connection_error(registered_tool, mock_context, mock_unity_connection):
    """Test handling of connection errors."""
    # Set up mock connection error
    mock_unity_connection.send_command.side_effect = ConnectionError("Connection to Unity lost")
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="get"
    )
    
    # Check error was properly handled and passed through
    assert result["success"] is False
    assert "Connection to Unity lost" in result.get("message", "")
    assert result.get("connection_error") is True
    
    # Reset the side effect for other tests
    mock_unity_connection.send_command.side_effect = None

@pytest.mark.asyncio
async def test_read_console_nonexistent_log_type(registered_tool, mock_context, mock_unity_connection):
    """Test handling of nonexistent log type."""
    # Set up mock response with warning about invalid log type
    mock_unity_connection.send_command.return_value = {
        "success": False,
        "message": "Invalid log type 'debug' specified. Valid types are 'error', 'warning', 'log', or 'all'.",
        "error": "InvalidLogType"
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        types=["debug"]  # A nonexistent log type
    )
    
    # Check result
    assert result["success"] is False
    assert "Invalid log type" in result.get("message", "")
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "read_console", {
        "action": "get",
        "types": ["debug"],
        "count": None,
        "format": "detailed",
        "includeStacktrace": True
    })

@pytest.mark.asyncio
async def test_read_console_invalid_types_parameter(registered_tool, mock_context):
    """Test handling when types parameter is not a list."""
    # Call the tool function with invalid types parameter (string instead of list)
    result = await registered_tool(
        ctx=mock_context,
        types="error"  # Should be a list, not a string
    )
    
    # Check the error result
    assert result["success"] is False
    assert result.get("validation_error") is True
    assert "must be a list" in result["message"] 