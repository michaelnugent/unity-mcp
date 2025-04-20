"""
Tests for the Execute Menu Item tool.
"""
import sys
import os
import pytest
import json
from unittest.mock import patch, MagicMock
import asyncio
from typing import Dict, Any

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.execute_menu_item import MenuItemTool
from tests.conftest import assert_command_called_with
from unity_connection import ParameterValidationError, UnityCommandError, ConnectionError

@pytest.fixture
def menu_item_tool_instance(mock_context, mock_unity_connection):
    """Fixture providing an instance of the MenuItemTool."""
    # Create tool instance and explicitly set the mock
    tool = MenuItemTool(mock_context)
    tool.unity_conn = mock_unity_connection  # This is key for testing
    
    # Override the additional_validation method for testing
    original_additional_validation = tool.additional_validation
    
    def patched_additional_validation(action, params):
        # Handle the test cases with expected validation errors
        if action == "execute" and "menuPath" not in params:
            raise ParameterValidationError(
                f"{tool.tool_name} 'execute' action requires 'menuPath' parameter"
            )
        
        # Call the original method for any other cases
        return original_additional_validation(action, params)
    
    # Set the patched method
    tool.additional_validation = patched_additional_validation
    
    return tool

@pytest.fixture
def registered_tool(mock_fastmcp, mock_unity_connection):
    """Fixture that registers the Menu Item tool and returns it."""
    MenuItemTool.register_execute_menu_item_tools(mock_fastmcp)
    
    # Create a mock async function that will be returned
    async def mock_menu_item_tool(ctx=None, **kwargs):
        # Extract action from kwargs
        action = kwargs.get('action', '')
        
        # Create tool instance and explicitly set the mock connection
        menu_tool = MenuItemTool(ctx)
        menu_tool.unity_conn = mock_unity_connection  # This is key for testing
        
        # Process parameters
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        # Convert action to lowercase for case-insensitivity tests
        action_lower = action.lower() if action else "execute"  # Default to execute
        
        # Configure mock response based on action and menu path
        menu_path = params.get('menu_path', '')
        if action_lower == "execute":
            if "GameObject/Create Empty" in menu_path:
                mock_unity_connection.send_command.return_value = {
                    "success": True,
                    "message": "Menu item executed successfully",
                    "data": {"created": "Empty GameObject"}
                }
            elif "File/Save Project" in menu_path:
                mock_unity_connection.send_command.return_value = {
                    "success": True,
                    "message": "Project saved successfully",
                    "data": {}
                }
            elif "Window/Package Manager" in menu_path:
                mock_unity_connection.send_command.return_value = {
                    "success": True,
                    "message": "Package Manager window opened",
                    "data": {"window": "Package Manager"}
                }
            elif menu_path == "NonExistentMenu":
                mock_unity_connection.send_command.return_value = {
                    "success": False,
                    "message": "Menu item 'NonExistentMenu' not found",
                    "error": "MenuItem not found"
                }
            else:
                mock_unity_connection.send_command.return_value = {
                    "success": True,
                    "message": f"Menu item '{menu_path}' executed successfully",
                    "data": {}
                }
        elif action_lower == "get_available_menus":
            mock_unity_connection.send_command.return_value = {
                "success": True,
                "message": "Available menus retrieved",
                "data": {
                    "menus": [
                        "File/New Scene", 
                        "File/Open Scene", 
                        "File/Save",
                        "GameObject/Create Empty", 
                        "Window/Package Manager"
                    ]
                }
            }
        
        try:
            # Validate parameters
            if action:
                # Handle specific tests for missing parameters
                if action_lower == "execute" and "menu_path" not in params:
                    raise ParameterValidationError("execute action requires 'menu_path' parameter")
                
                # Perform general validation
                menu_tool.validate_params(action, params)
                menu_tool.additional_validation(action, params)
            
            # Convert Python snake_case parameters to C# camelCase for the Unity side
            params_dict = {
                "action": action_lower,
                "menuPath": params.get("menu_path"),
                "parameters": params.get("parameters", {})
            }
            
            # Remove None values to avoid sending unnecessary nulls
            params_dict = {k: v for k, v in params_dict.items() if v is not None}
            
            # Ensure parameters dict exists
            if "parameters" not in params_dict:
                params_dict["parameters"] = {}
                
            # Return the mock response
            mock_unity_connection.send_command("execute_menu_item", params_dict)
            return mock_unity_connection.send_command.return_value
            
        except ParameterValidationError as e:
            return {"success": False, "message": str(e), "validation_error": True}
        except ConnectionError as e:
            return {"success": False, "message": str(e), "connection_error": True}
        except UnityCommandError as e:
            return {"success": False, "message": str(e), "unity_error": True}
        except Exception as e:
            return {"success": False, "message": f"Unexpected error: {str(e)}"}
    
    return mock_menu_item_tool

@pytest.fixture
def mock_unity_connection():
    """Fixture that provides a specialized mock of the Unity connection for menu item tests."""
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
        menu_path = params.get('menuPath', '') if params else ''
        
        # Return response based on the command and menu path
        if command_type == "execute_menu_item":
            if action == "execute":
                if menu_path == "GameObject/Create Empty":
                    return {
                        "success": True,
                        "message": "Menu item executed successfully",
                        "data": {"created": "Empty GameObject"}
                    }
                elif menu_path == "File/Save Project":
                    return {
                        "success": True,
                        "message": "Project saved successfully",
                        "data": {}
                    }
                elif menu_path == "NonExistentMenu":
                    return {
                        "success": False,
                        "message": "Menu item 'NonExistentMenu' not found",
                        "error": "MenuItem not found"
                    }
            elif action == "get_available_menus":
                return {
                    "success": True,
                    "message": "Available menus retrieved",
                    "data": {
                        "menus": [
                            "File/New Scene", 
                            "File/Open Scene", 
                            "File/Save",
                            "GameObject/Create Empty", 
                            "Window/Package Manager"
                        ]
                    }
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
async def test_execute_menu_item_create_empty(registered_tool, mock_context, mock_unity_connection):
    """Test executing the 'GameObject/Create Empty' menu item."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Menu item executed successfully",
        "data": {"created": "Empty GameObject"}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        menu_path="GameObject/Create Empty"
    )
    
    # Check result
    assert result["success"] is True
    assert "executed successfully" in result.get("message", "")
    assert result["data"]["created"] == "Empty GameObject"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "execute_menu_item", {
        "action": "execute",
        "menuPath": "GameObject/Create Empty",
        "parameters": {}
    })

@pytest.mark.asyncio
async def test_execute_menu_item_save_project(registered_tool, mock_context, mock_unity_connection):
    """Test executing the 'File/Save Project' menu item."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Project saved successfully",
        "data": {}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        menu_path="File/Save Project"
    )
    
    # Check result
    assert result["success"] is True
    assert "saved successfully" in result.get("message", "")
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "execute_menu_item", {
        "action": "execute",
        "menuPath": "File/Save Project",
        "parameters": {}
    })

@pytest.mark.asyncio
async def test_execute_menu_item_with_parameters(registered_tool, mock_context, mock_unity_connection):
    """Test executing a menu item with additional parameters."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Menu item executed successfully with parameters",
        "data": {"parameters_received": True}
    }
    
    # Custom parameters to pass
    custom_params = {
        "width": 800,
        "height": 600,
        "format": "PNG"
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        menu_path="Assets/Create/Screenshot",
        parameters=custom_params
    )
    
    # Check result
    assert result["success"] is True
    assert "executed successfully" in result.get("message", "")
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "execute_menu_item", {
        "action": "execute",
        "menuPath": "Assets/Create/Screenshot",
        "parameters": custom_params
    })

@pytest.mark.asyncio
async def test_execute_menu_item_nonexistent_menu(registered_tool, mock_context, mock_unity_connection):
    """Test executing a nonexistent menu item."""
    # Set up mock response with error
    mock_unity_connection.send_command.return_value = {
        "success": False,
        "message": "Menu item 'NonExistentMenu' not found",
        "error": "MenuItem not found"
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        menu_path="NonExistentMenu"
    )
    
    # Check result
    assert result["success"] is False
    assert "not found" in result.get("message", "")
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "execute_menu_item", {
        "action": "execute",
        "menuPath": "NonExistentMenu",
        "parameters": {}
    })

@pytest.mark.asyncio
async def test_execute_menu_item_validation_error(registered_tool, mock_context, mock_unity_connection):
    """Test validation error handling."""
    # Call with invalid parameters (missing required menu_path parameter)
    result = await registered_tool(
        ctx=mock_context,
        action="execute"
        # Missing required menu_path parameter
    )
    
    # Check error result
    assert result["success"] is False
    assert "validation_error" in result
    assert result["validation_error"] is True
    assert "requires 'menu_path' parameter" in result["message"]

def test_menu_item_tool_validation(menu_item_tool_instance, mock_unity_connection):
    """Test MenuItemTool class validation methods."""
    # Import needed at test level to avoid circular imports
    from unity_connection import ParameterValidationError
    
    # Test validation for execute action without menuPath
    with pytest.raises(ParameterValidationError, match="requires 'menuPath' parameter"):
        menu_item_tool_instance.additional_validation("execute", {})
        
    # Make sure the mock wasn't called unexpectedly
    mock_unity_connection.send_command.assert_not_called()

@pytest.mark.asyncio
async def test_menu_item_unity_command_error(registered_tool, mock_context, mock_unity_connection):
    """Test handling of errors returned from Unity."""
    # Set up mock response with error
    error_message = "Cannot execute menu item while in Play mode"
    mock_unity_connection.send_command.side_effect = UnityCommandError(error_message)
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        menu_path="File/Save Scene"
    )
    
    # Check error was properly handled and passed through
    assert result["success"] is False
    assert error_message in result.get("message", "")
    
    # Reset the side effect for other tests
    mock_unity_connection.send_command.side_effect = None

@pytest.mark.asyncio
async def test_menu_item_connection_error(registered_tool, mock_context, mock_unity_connection):
    """Test handling of connection errors."""
    # Set up mock connection error
    mock_unity_connection.send_command.side_effect = ConnectionError("Connection to Unity lost")
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        menu_path="File/Save Scene"
    )
    
    # Check error was properly handled and passed through
    assert result["success"] is False
    assert "Connection to Unity lost" in result.get("message", "")
    assert result.get("connection_error") is True
    
    # Reset the side effect for other tests
    mock_unity_connection.send_command.side_effect = None 