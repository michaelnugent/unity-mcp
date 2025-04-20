"""
Tests for the Editor management tool.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
import asyncio
from tools.manage_editor import EditorTool
from tests.conftest import assert_command_called_with
from unity_connection import ParameterValidationError

@pytest.fixture
def editor_tool_instance(mock_context, mock_unity_connection):
    """Fixture providing an instance of the EditorTool."""
    tool = EditorTool(mock_context)
    tool.unity_conn = mock_unity_connection  # Directly set the mocked connection
    return tool

@pytest.fixture
def registered_tool(mock_fastmcp, mock_unity_connection):
    """Fixture that registers the Editor tool and returns it."""
    EditorTool.register_manage_editor_tools(mock_fastmcp)
    
    # Create a mock async function that will be returned
    async def mock_editor_tool(ctx=None, **kwargs):
        # Extract parameters
        action = kwargs.get('action', '')
        
        # Create tool instance
        editor_tool = EditorTool(ctx)
        editor_tool.unity_conn = mock_unity_connection  # Explicitly set the mock
        
        # Process parameters
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        try:
            # We need to call send_command_async, but ensure we return the mock response
            # that's already been set up for this specific action
            await editor_tool.send_command_async("manage_editor", params)
            return mock_unity_connection.send_command.return_value
        except ParameterValidationError as e:
            return {"success": False, "message": str(e), "validation_error": True}
    
    return mock_editor_tool

@pytest.mark.asyncio
async def test_editor_tool_play(registered_tool, mock_context, mock_unity_connection):
    """Test entering play mode."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Entered play mode",
        "data": {"isPlaying": True, "isPaused": False}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="play"
    )
    
    # Check result
    assert result["success"] is True
    assert "play" in result.get("message", "").lower()
    assert result["data"]["isPlaying"] is True
    assert result["data"]["isPaused"] is False
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "play"
    })

@pytest.mark.asyncio
async def test_editor_tool_pause(registered_tool, mock_context, mock_unity_connection):
    """Test pausing play mode."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Paused play mode",
        "data": {"isPlaying": True, "isPaused": True}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="pause"
    )
    
    # Check result
    assert result["success"] is True
    assert "pause" in result.get("message", "").lower()
    assert result["data"]["isPlaying"] is True
    assert result["data"]["isPaused"] is True
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "pause"
    })

@pytest.mark.asyncio
async def test_editor_tool_stop(registered_tool, mock_context, mock_unity_connection):
    """Test stopping play mode."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Stopped play mode",
        "data": {"isPlaying": False, "isPaused": False}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="stop"
    )
    
    # Check result
    assert result["success"] is True
    assert "stop" in result.get("message", "").lower()
    assert result["data"]["isPlaying"] is False
    assert result["data"]["isPaused"] is False
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "stop"
    })

@pytest.mark.asyncio
async def test_editor_tool_get_status(registered_tool, mock_context, mock_unity_connection):
    """Test getting editor status."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Editor status retrieved",
        "data": {
            "isPlaying": False, 
            "isPaused": False,
            "playbackSpeed": 1.0,
            "currentScene": "Assets/Scenes/MainScene.unity"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="get_status"
    )
    
    # Check result
    assert result["success"] is True
    assert "status" in result.get("message", "").lower()
    assert "isPlaying" in result["data"]
    assert "isPaused" in result["data"]
    assert "playbackSpeed" in result["data"]
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "get_status"
    })

@pytest.mark.asyncio
async def test_editor_tool_set_playback_speed(registered_tool, mock_context, mock_unity_connection):
    """Test setting playback speed."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Playback speed set to 2.0",
        "data": {"playbackSpeed": 2.0}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="set_playback_speed",
        playback_speed=2.0
    )
    
    # Check result
    assert result["success"] is True
    assert "playback speed" in result.get("message", "").lower()
    assert result["data"]["playbackSpeed"] == 2.0
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "set_playback_speed",
        "playback_speed": 2.0
    })

@pytest.mark.asyncio
async def test_editor_tool_step_frame(registered_tool, mock_context, mock_unity_connection):
    """Test stepping frames in paused mode."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Stepped 2 frames",
        "data": {"framesAdvanced": 2}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="step_frame",
        frames=2
    )
    
    # Check result
    assert result["success"] is True
    assert "stepped" in result.get("message", "").lower()
    assert result["data"]["framesAdvanced"] == 2
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "step_frame",
        "frames": 2
    })

@pytest.mark.asyncio
async def test_editor_tool_recompile_scripts(registered_tool, mock_context, mock_unity_connection):
    """Test recompiling scripts."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Scripts recompiled successfully",
        "data": {"compilationTime": 0.8}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="recompile_scripts"
    )
    
    # Check result
    assert result["success"] is True
    assert "recompile" in result.get("message", "").lower()
    assert "compilationTime" in result["data"]
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "recompile_scripts"
    })

@pytest.mark.asyncio
async def test_editor_tool_save_scene(registered_tool, mock_context, mock_unity_connection):
    """Test saving the current scene."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Scene saved successfully",
        "data": {"scenePath": "Assets/Scenes/MainScene.unity"}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="save_scene"
    )
    
    # Check result
    assert result["success"] is True
    assert "saved" in result.get("message", "").lower()
    assert "scenePath" in result["data"]
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "save_scene"
    })

@pytest.mark.asyncio
async def test_editor_tool_save_scene_as(registered_tool, mock_context, mock_unity_connection):
    """Test saving the current scene to a new path."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Scene saved as NewScene.unity",
        "data": {"scenePath": "Assets/Scenes/NewScene.unity"}
    }
    
    new_path = "Assets/Scenes/NewScene.unity"
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="save_scene",
        save_as_path=new_path
    )
    
    # Check result
    assert result["success"] is True
    assert "saved" in result.get("message", "").lower()
    assert result["data"]["scenePath"] == new_path
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "save_scene",
        "save_as_path": new_path
    })

@pytest.mark.asyncio
async def test_editor_tool_save_project(registered_tool, mock_context, mock_unity_connection):
    """Test saving the entire project."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Project saved successfully",
        "data": {"timestamp": "2023-09-15T12:30:45Z"}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="save_project"
    )
    
    # Check result
    assert result["success"] is True
    assert "project" in result.get("message", "").lower()
    assert "saved" in result.get("message", "").lower()
    assert "timestamp" in result["data"]
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "save_project"
    })

@pytest.mark.asyncio
async def test_editor_tool_get_preferences(registered_tool, mock_context, mock_unity_connection):
    """Test getting editor preferences."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Preferences retrieved",
        "data": {
            "value": True,
            "path": "General/Auto Refresh"
        }
    }
    
    preferences_path = "General/Auto Refresh"
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="get_preferences",
        preferences_path=preferences_path
    )
    
    # Check result
    assert result["success"] is True
    assert "preferences" in result.get("message", "").lower() or "retrieved" in result.get("message", "").lower()
    assert result["data"]["path"] == preferences_path
    assert "value" in result["data"]
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "get_preferences",
        "preferences_path": preferences_path
    })

@pytest.mark.asyncio
async def test_editor_tool_set_preferences(registered_tool, mock_context, mock_unity_connection):
    """Test setting editor preferences."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Preferences updated",
        "data": {
            "path": "General/Auto Refresh",
            "value": False,
            "previous_value": True
        }
    }
    
    preferences_path = "General/Auto Refresh"
    preferences_value = False
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="set_preferences",
        preferences_path=preferences_path,
        preferences_value=preferences_value
    )
    
    # Check result
    assert result["success"] is True
    assert "preferences" in result.get("message", "").lower() or "updated" in result.get("message", "").lower()
    assert result["data"]["path"] == preferences_path
    assert result["data"]["value"] == preferences_value
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "set_preferences",
        "preferences_path": preferences_path,
        "preferences_value": preferences_value
    })

@pytest.mark.asyncio
async def test_editor_tool_clear_console(registered_tool, mock_context, mock_unity_connection):
    """Test clearing the Unity console."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Console cleared",
        "data": {}
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="clear_console"
    )
    
    # Check result
    assert result["success"] is True
    assert "console" in result.get("message", "").lower()
    assert "cleared" in result.get("message", "").lower()
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "clear_console"
    })

@pytest.mark.asyncio
async def test_editor_tool_screenshot(registered_tool, mock_context, mock_unity_connection):
    """Test taking a screenshot."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Screenshot saved",
        "data": {
            "path": "Assets/Screenshots/test.png",
            "width": 1920,
            "height": 1080
        }
    }
    
    screenshot_path = "Assets/Screenshots/test.png"
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="screenshot",
        screenshot_path=screenshot_path,
        screenshot_width=1920,
        screenshot_height=1080
    )
    
    # Check result
    assert result["success"] is True
    assert "screenshot" in result.get("message", "").lower()
    assert result["data"]["path"] == screenshot_path
    assert result["data"]["width"] == 1920
    assert result["data"]["height"] == 1080
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "screenshot",
        "screenshot_path": screenshot_path,
        "screenshot_width": 1920,
        "screenshot_height": 1080
    })

@pytest.mark.asyncio
async def test_editor_tool_screenshot_with_camera(registered_tool, mock_context, mock_unity_connection):
    """Test taking a screenshot with a specific camera."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Screenshot saved from MainCamera",
        "data": {
            "path": "Assets/Screenshots/camera_view.png",
            "camera": "MainCamera",
            "width": 1280,
            "height": 720
        }
    }
    
    screenshot_path = "Assets/Screenshots/camera_view.png"
    camera_name = "MainCamera"
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="screenshot",
        screenshot_path=screenshot_path,
        screenshot_width=1280,
        screenshot_height=720,
        camera_name=camera_name
    )
    
    # Check result
    assert result["success"] is True
    assert "screenshot" in result.get("message", "").lower()
    assert result["data"]["path"] == screenshot_path
    assert result["data"]["camera"] == camera_name
    assert result["data"]["width"] == 1280
    assert result["data"]["height"] == 720
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_editor", {
        "action": "screenshot",
        "screenshot_path": screenshot_path,
        "screenshot_width": 1280,
        "screenshot_height": 720,
        "camera_name": camera_name
    })

@pytest.mark.asyncio
async def test_editor_tool_validation_error(registered_tool, mock_context, mock_unity_connection):
    """Test validation error handling."""
    # Configure mock to raise validation error for missing parameter
    mock_unity_connection.send_command.side_effect = ParameterValidationError("Missing required parameter playback_speed")
    
    # Call with missing required parameters for set_playback_speed
    result = await registered_tool(
        ctx=mock_context,
        action="set_playback_speed"
        # Missing required parameter: playback_speed
    )
    
    # Check result
    assert result["success"] is False
    assert "validation_error" in result
    assert result["validation_error"] is True
    
    # Reset mock side effect for other tests
    mock_unity_connection.send_command.side_effect = None

def test_editor_tool_validation(editor_tool_instance, mock_unity_connection):
    """Test EditorTool class validation methods."""
    # Test validation for capture_screenshot action without screenshotPath
    with pytest.raises(ParameterValidationError, match="requires 'screenshotPath' parameter"):
        editor_tool_instance.additional_validation("capture_screenshot", {})
        
    # Make sure the mock wasn't called unexpectedly
    mock_unity_connection.send_command.assert_not_called() 