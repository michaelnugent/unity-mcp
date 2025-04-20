"""
Tests for the Script management tool.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
import asyncio
from tools.manage_script import ScriptTool
from tools.base_tool import BaseTool
from tests.conftest import assert_command_called_with
from unity_connection import ParameterValidationError

# Patch BaseTool's get_unity_connection at module level to ensure all instances use our mock
@pytest.fixture(autouse=True)
def patch_base_tool(mock_unity_connection):
    with patch('tools.base_tool.get_unity_connection', return_value=mock_unity_connection):
        yield

@pytest.fixture
def script_tool_instance(mock_context, mock_unity_connection):
    """Fixture providing an instance of the ScriptTool."""
    tool = ScriptTool(mock_context)
    tool.unity_conn = mock_unity_connection  # Directly set the mocked connection
    return tool

@pytest.fixture
def registered_tool(mock_fastmcp, mock_unity_connection):
    """Fixture that registers the Script tool and returns it."""
    ScriptTool.register_manage_script_tools(mock_fastmcp)
    
    # Create a mock async function that will be returned
    async def mock_script_tool(ctx=None, **kwargs):
        # Extract parameters
        action = kwargs.get('action', '')
        
        # Create tool instance
        script_tool = ScriptTool(ctx)
        script_tool.unity_conn = mock_unity_connection  # Explicitly set the mock
        
        # Process parameters
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        try:
            # We need to call send_command_async, but ensure we return the mock response
            # that's already been set up for this specific action
            await script_tool.send_command_async("manage_script", params)
            return mock_unity_connection.send_command.return_value
        except ParameterValidationError as e:
            return {"success": False, "message": str(e), "validation_error": True}
    
    return mock_script_tool

@pytest.mark.asyncio
async def test_script_tool_create(registered_tool, mock_context, mock_unity_connection):
    """Test creating a new script."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Script created successfully",
        "data": {
            "path": "Assets/Scripts/PlayerController.cs",
            "name": "PlayerController"
        }
    }
    
    # Sample script content
    script_content = """
using UnityEngine;

public class PlayerController : MonoBehaviour
{
    public float speed = 5f;
    
    void Update()
    {
        float horizontal = Input.GetAxis("Horizontal");
        float vertical = Input.GetAxis("Vertical");
        
        Vector3 movement = new Vector3(horizontal, 0f, vertical) * speed * Time.deltaTime;
        transform.Translate(movement);
    }
}
"""
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="create",
        name="PlayerController",
        path="Assets/Scripts",
        contents=script_content,
        script_type="MonoBehaviour",
        namespace=""
    )
    
    # Check result
    assert result["success"] is True
    assert "created" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/Scripts/PlayerController.cs"
    assert result["data"]["name"] == "PlayerController"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_script", {
        "action": "create",
        "name": "PlayerController",
        "path": "Assets/Scripts",
        "contents": script_content,
        "script_type": "MonoBehaviour",
        "namespace": ""
    })

@pytest.mark.asyncio
async def test_script_tool_read(registered_tool, mock_context, mock_unity_connection):
    """Test reading a script."""
    # Script content to return
    script_content = """
using UnityEngine;

public class EnemyController : MonoBehaviour
{
    public float health = 100f;
    public float speed = 3f;
    
    void Start()
    {
        Debug.Log("Enemy initialized");
    }
    
    void Update()
    {
        // Enemy logic here
    }
}
"""
    
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Script read successfully",
        "data": {
            "path": "Assets/Scripts/EnemyController.cs",
            "name": "EnemyController",
            "contents": script_content
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="read",
        name="EnemyController",
        path="Assets/Scripts"
    )
    
    # Check result
    assert result["success"] is True
    assert "read" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/Scripts/EnemyController.cs"
    assert result["data"]["name"] == "EnemyController"
    assert result["data"]["contents"] == script_content
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_script", {
        "action": "read",
        "name": "EnemyController",
        "path": "Assets/Scripts"
    })

@pytest.mark.asyncio
async def test_script_tool_update(registered_tool, mock_context, mock_unity_connection):
    """Test updating a script."""
    # Updated script content
    updated_script_content = """
using UnityEngine;

public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }
    
    public int score = 0;
    public int lives = 3;
    
    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }
    
    public void AddScore(int points)
    {
        score += points;
    }
    
    public void LoseLife()
    {
        lives--;
        if (lives <= 0)
        {
            GameOver();
        }
    }
    
    private void GameOver()
    {
        Debug.Log("Game Over!");
    }
}
"""
    
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Script updated successfully",
        "data": {
            "path": "Assets/Scripts/GameManager.cs",
            "name": "GameManager"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="update",
        name="GameManager",
        path="Assets/Scripts",
        contents=updated_script_content,
        script_type="MonoBehaviour",
        namespace=""
    )
    
    # Check result
    assert result["success"] is True
    assert "updated" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/Scripts/GameManager.cs"
    assert result["data"]["name"] == "GameManager"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_script", {
        "action": "update",
        "name": "GameManager",
        "path": "Assets/Scripts",
        "contents": updated_script_content,
        "script_type": "MonoBehaviour",
        "namespace": ""
    })

@pytest.mark.asyncio
async def test_script_tool_delete(registered_tool, mock_context, mock_unity_connection):
    """Test deleting a script."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Script deleted successfully",
        "data": {
            "path": "Assets/Scripts/OldScript.cs",
            "name": "OldScript"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="delete",
        name="OldScript",
        path="Assets/Scripts"
    )
    
    # Check result
    assert result["success"] is True
    assert "deleted" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/Scripts/OldScript.cs"
    assert result["data"]["name"] == "OldScript"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_script", {
        "action": "delete",
        "name": "OldScript",
        "path": "Assets/Scripts"
    })

@pytest.mark.asyncio
async def test_script_tool_create_with_namespace(registered_tool, mock_context, mock_unity_connection):
    """Test creating a script with a namespace."""
    # Sample script content with namespace
    script_content = """
using UnityEngine;

namespace MyGame.Utilities
{
    public class TimeManager : MonoBehaviour
    {
        public float timeScale = 1f;
        
        void Start()
        {
            Time.timeScale = timeScale;
        }
        
        public void SetTimeScale(float scale)
        {
            timeScale = scale;
            Time.timeScale = scale;
        }
    }
}
"""
    
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Script created successfully",
        "data": {
            "path": "Assets/Scripts/Utilities/TimeManager.cs",
            "name": "TimeManager",
            "namespace": "MyGame.Utilities"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="create",
        name="TimeManager",
        path="Assets/Scripts/Utilities",
        contents=script_content,
        script_type="MonoBehaviour",
        namespace="MyGame.Utilities"
    )
    
    # Check result
    assert result["success"] is True
    assert "created" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/Scripts/Utilities/TimeManager.cs"
    assert result["data"]["name"] == "TimeManager"
    assert result["data"]["namespace"] == "MyGame.Utilities"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_script", {
        "action": "create",
        "name": "TimeManager",
        "path": "Assets/Scripts/Utilities",
        "contents": script_content,
        "script_type": "MonoBehaviour",
        "namespace": "MyGame.Utilities"
    })

@pytest.mark.asyncio
async def test_script_tool_create_scriptable_object(registered_tool, mock_context, mock_unity_connection):
    """Test creating a ScriptableObject script."""
    # Sample ScriptableObject script content
    script_content = """
using UnityEngine;

[CreateAssetMenu(fileName = "New Item Data", menuName = "Inventory/Item Data")]
public class ItemData : ScriptableObject
{
    public string itemName;
    public string description;
    public Sprite icon;
    public int value;
    public float weight;
    
    public bool isStackable;
    public int maxStackSize = 99;
}
"""
    
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Script created successfully",
        "data": {
            "path": "Assets/Scripts/ItemData.cs",
            "name": "ItemData",
            "script_type": "ScriptableObject"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="create",
        name="ItemData",
        path="Assets/Scripts",
        contents=script_content,
        script_type="ScriptableObject",
        namespace=""
    )
    
    # Check result
    assert result["success"] is True
    assert "created" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/Scripts/ItemData.cs"
    assert result["data"]["name"] == "ItemData"
    assert result["data"]["script_type"] == "ScriptableObject"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_script", {
        "action": "create",
        "name": "ItemData",
        "path": "Assets/Scripts",
        "contents": script_content,
        "script_type": "ScriptableObject",
        "namespace": ""
    })

@pytest.mark.asyncio
async def test_script_tool_validation_error(registered_tool, mock_context, mock_unity_connection):
    """Test validation error handling."""
    # Call with missing required parameters
    result = await registered_tool(
        ctx=mock_context,
        action="create",
        name="IncompleteScript"
        # Missing required parameters: path, contents, script_type
    )
    
    # Check result
    assert result["success"] is False
    assert "validation_error" in result
    assert result["validation_error"] is True

def test_script_tool_validation(script_tool_instance, mock_unity_connection):
    """Test ScriptTool class validation methods."""
    # Test validation for create action without contents
    with pytest.raises(ParameterValidationError, match="requires 'contents' parameter"):
        script_tool_instance.additional_validation("create", {
            "name": "Test",
            "path": "Assets/Scripts"
            # Missing contents parameter
        })
    
    # Test validation for update action without contents
    with pytest.raises(ParameterValidationError, match="requires 'contents' parameter"):
        script_tool_instance.additional_validation("update", {
            "name": "Test",
            "path": "Assets/Scripts"
            # Missing contents parameter
        })
        
    # Make sure the mock wasn't called unexpectedly
    mock_unity_connection.send_command.assert_not_called() 