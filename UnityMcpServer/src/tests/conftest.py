"""
Configuration file for pytest with Unity MCP server tool test fixtures.
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from mcp.server.fastmcp import FastMCP, Context
import sys
import os
import logging

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s [%(name)s]: %(message)s',
    stream=sys.stderr
)

# Our test logger
test_logger = logging.getLogger('mcp_tests')
test_logger.setLevel(logging.DEBUG)

# Reduce noise from other loggers
for logger_name in ['unity-mcp-server', 'unity_connection']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# Add src directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope="session", autouse=True)
def patch_unity_connection():
    """Global patch for unity_connection to ensure no real connections are attempted."""
    # Create a mock that will be returned by get_unity_connection
    mock_conn = MagicMock()
    mock_conn.send_command.return_value = {"success": True, "message": "Default mock response", "data": {}}
    
    # Patch both the direct import and the one used by BaseTool
    with patch('unity_connection.get_unity_connection', return_value=mock_conn) as mock:
        with patch('tools.base_tool.get_unity_connection', return_value=mock_conn):
            with patch('unity_connection.UnityConnection.connect', return_value=True):
                with patch('unity_connection._unity_connection', None):
                    yield mock  # Return the mock for backward compatibility

@pytest.fixture(scope="function")
def mock_unity_connection(patch_unity_connection):
    """Fixture that provides a mocked Unity connection."""
    # Get the mock created by the session-wide patch
    mock_conn = patch_unity_connection
    
    # Reset the mock for clean test
    mock_conn.reset_mock()
    
    # Create a simple way to capture mock settings
    responses_by_action = {}
    
    # Replace side_effect with a direct function
    def mock_send_command(command_type, params=None):
        params = params or {}
        action = params.get('action', '') or ''
        action = action.lower()
        
        test_logger.debug(f"mock_send_command: command={command_type}, action={action}, params={params}")
        
        if action in responses_by_action:
            test_logger.debug(f"Using action-specific response for '{action}'")
            return responses_by_action[action]
        
        test_logger.debug(f"No action-specific response for '{action}', using default")
        return {"success": True, "message": "Operation successful", "data": {}}
    
    # Set up mock behavior
    mock_conn.send_command.side_effect = mock_send_command
    
    # Add a simpler method to mock specific actions
    def mock_action(action, response):
        """Set up a mock response for a specific action"""
        action = action.lower()
        test_logger.debug(f"Mocking response for action '{action}': {response}")
        responses_by_action[action] = response
    
    # Attach the helper method
    mock_conn.mock_action = mock_action
    
    return mock_conn

@pytest.fixture
def mock_context():
    """Fixture that provides a mocked MCP context."""
    mock_ctx = MagicMock(spec=Context)
    mock_ctx.lifespan_context = {"bridge": MagicMock()}
    return mock_ctx

@pytest.fixture
def mock_fastmcp():
    """Fixture that provides a mocked FastMCP instance."""
    mock_mcp = MagicMock(spec=FastMCP)
    
    # Create a tool decorator that captures the decorated function
    def tool_decorator(*args, **kwargs):
        def wrapper(func):
            # Store the function in an attribute of the mock
            wrapper.decorated_func = func
            return wrapper  # Return wrapper instead of func
        return wrapper
    
    # Make tool() method return our decorator
    mock_mcp.tool = tool_decorator
    return mock_mcp

def assert_command_called_with(mock_connection, command_type, expected_params):
    """Helper to assert that send_command was called with expected parameters."""
    mock_connection.send_command.assert_called()
    
    # Get the actual params
    args, kwargs = mock_connection.send_command.call_args
    
    # Check command_type
    assert args[0] == command_type, f"Expected command_type '{command_type}', got '{args[0]}'"
    
    # Check params
    actual_params = args[1] if len(args) > 1 else kwargs.get('params', {})
    
    # Check each expected param is in actual params
    for key, value in expected_params.items():
        assert key in actual_params, f"Expected parameter '{key}' not found in actual parameters"
        assert actual_params[key] == value, f"For parameter '{key}', expected '{value}', got '{actual_params[key]}'" 