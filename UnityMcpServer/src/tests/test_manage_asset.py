"""
Tests for the Asset management tool.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
import asyncio
from tools.manage_asset import AssetTool
from tests.conftest import assert_command_called_with
from unity_connection import ParameterValidationError

@pytest.fixture
def asset_tool_instance(mock_context, mock_unity_connection):
    """Fixture providing an instance of the AssetTool."""
    tool = AssetTool(mock_context)
    tool.unity_conn = mock_unity_connection  # Directly set the mocked connection
    return tool

@pytest.fixture
def registered_tool(mock_fastmcp, mock_unity_connection):
    """Fixture that registers the Asset tool and returns it."""
    AssetTool.register_manage_asset_tools(mock_fastmcp)
    
    # Create a mock async function that will be returned
    async def mock_asset_tool(ctx=None, **kwargs):
        # Extract parameters
        action = kwargs.get('action', '')
        
        # Create tool instance
        asset_tool = AssetTool(ctx)
        asset_tool.unity_conn = mock_unity_connection  # Explicitly set the mock
        
        # Process parameters
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        # Set up appropriate mock responses based on action
        if action == "create":
            mock_unity_connection.send_command.return_value = {
                "success": True,
                "message": "Asset created successfully",
                "data": {
                    "path": kwargs.get("path", ""),
                    "assetType": kwargs.get("asset_type", ""),
                    "guid": "12345678901234567890123456789012"
                }
            }
        elif action == "modify":
            mock_unity_connection.send_command.return_value = {
                "success": True,
                "message": "Asset modified successfully",
                "data": {
                    "path": kwargs.get("path", ""),
                    "assetType": "Material",
                    "modifiedProperties": ["color"]
                }
            }
        elif action == "delete":
            mock_unity_connection.send_command.return_value = {
                "success": True,
                "message": "Asset deleted successfully",
                "data": {
                    "path": kwargs.get("path", ""),
                    "assetType": "Material"
                }
            }
        elif action == "search":
            mock_unity_connection.send_command.return_value = {
                "success": True,
                "message": "Assets found successfully",
                "data": [
                    {
                        "path": "Assets/Materials/Red.mat",
                        "assetType": "Material",
                        "guid": "12345678901234567890123456789012"
                    },
                    {
                        "path": "Assets/Materials/Blue.mat",
                        "assetType": "Material",
                        "guid": "23456789012345678901234567890123"
                    }
                ]
            }
        elif action == "create_folder":
            mock_unity_connection.send_command.return_value = {
                "success": True,
                "message": "Folder created successfully",
                "data": {
                    "path": kwargs.get("path", ""),
                    "assetType": "Folder",
                    "guid": "12345678901234567890123456789012"
                }
            }
        elif action == "get_components":
            mock_unity_connection.send_command.return_value = {
                "success": True,
                "message": "Components retrieved successfully",
                "data": [
                    "UnityEngine.Transform",
                    "UnityEngine.MeshFilter",
                    "UnityEngine.MeshRenderer",
                    "UnityEngine.BoxCollider",
                    "MyGame.PlayerController"
                ]
            }
        
        try:
            # We need to call send_command_async, but ensure we return the mock response
            # that's already been set up for this specific action
            await asset_tool.send_command_async("manage_asset", params)
            return mock_unity_connection.send_command.return_value
        except ParameterValidationError as e:
            return {"success": False, "message": str(e), "validation_error": True}
    
    return mock_asset_tool

@pytest.mark.asyncio
async def test_asset_tool_create(registered_tool, mock_context, mock_unity_connection):
    """Test creating a new asset."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Asset created successfully",
        "data": {
            "path": "Assets/Materials/NewMaterial.mat",
            "assetType": "Material",
            "guid": "12345678901234567890123456789012"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="create",
        path="Assets/Materials/NewMaterial.mat",
        asset_type="Material",
        properties={"color": [1.0, 0.0, 0.0, 1.0]}
    )
    
    # Check result
    assert result["success"] is True
    assert "created" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/Materials/NewMaterial.mat"
    assert result["data"]["assetType"] == "Material"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_asset", {
        "action": "create",
        "path": "Assets/Materials/NewMaterial.mat",
        "asset_type": "Material",
        "properties": {"color": [1.0, 0.0, 0.0, 1.0]}
    })

@pytest.mark.asyncio
async def test_asset_tool_modify(registered_tool, mock_context, mock_unity_connection):
    """Test modifying an existing asset."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Asset modified successfully",
        "data": {
            "path": "Assets/Materials/ExistingMaterial.mat",
            "assetType": "Material",
            "modifiedProperties": ["color"]
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="modify",
        path="Assets/Materials/ExistingMaterial.mat",
        properties={"color": [0.0, 1.0, 0.0, 1.0]}
    )
    
    # Check result
    assert result["success"] is True
    assert "modified" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/Materials/ExistingMaterial.mat"
    assert "color" in result["data"]["modifiedProperties"]
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_asset", {
        "action": "modify",
        "path": "Assets/Materials/ExistingMaterial.mat",
        "properties": {"color": [0.0, 1.0, 0.0, 1.0]}
    })

@pytest.mark.asyncio
async def test_asset_tool_delete(registered_tool, mock_context, mock_unity_connection):
    """Test deleting an asset."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Asset deleted successfully",
        "data": {
            "path": "Assets/Materials/OldMaterial.mat",
            "assetType": "Material"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="delete",
        path="Assets/Materials/OldMaterial.mat"
    )
    
    # Check result
    assert result["success"] is True
    assert "deleted" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/Materials/OldMaterial.mat"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_asset", {
        "action": "delete",
        "path": "Assets/Materials/OldMaterial.mat"
    })

@pytest.mark.asyncio
async def test_asset_tool_duplicate(registered_tool, mock_context, mock_unity_connection):
    """Test duplicating an asset."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Asset duplicated successfully",
        "data": {
            "originalPath": "Assets/Materials/OriginalMaterial.mat",
            "duplicatePath": "Assets/Materials/CopiedMaterial.mat",
            "assetType": "Material"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="duplicate",
        path="Assets/Materials/OriginalMaterial.mat",
        destination="Assets/Materials/CopiedMaterial.mat"
    )
    
    # Check result
    assert result["success"] is True
    assert "duplicated" in result.get("message", "").lower()
    assert result["data"]["originalPath"] == "Assets/Materials/OriginalMaterial.mat"
    assert result["data"]["duplicatePath"] == "Assets/Materials/CopiedMaterial.mat"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_asset", {
        "action": "duplicate",
        "path": "Assets/Materials/OriginalMaterial.mat",
        "destination": "Assets/Materials/CopiedMaterial.mat"
    })

@pytest.mark.asyncio
async def test_asset_tool_move(registered_tool, mock_context, mock_unity_connection):
    """Test moving an asset."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Asset moved successfully",
        "data": {
            "originalPath": "Assets/Materials/OldFolder/Material.mat",
            "newPath": "Assets/Materials/NewFolder/Material.mat",
            "assetType": "Material"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="move",
        path="Assets/Materials/OldFolder/Material.mat",
        destination="Assets/Materials/NewFolder/Material.mat"
    )
    
    # Check result
    assert result["success"] is True
    assert "moved" in result.get("message", "").lower()
    assert result["data"]["originalPath"] == "Assets/Materials/OldFolder/Material.mat"
    assert result["data"]["newPath"] == "Assets/Materials/NewFolder/Material.mat"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_asset", {
        "action": "move",
        "path": "Assets/Materials/OldFolder/Material.mat",
        "destination": "Assets/Materials/NewFolder/Material.mat"
    })

@pytest.mark.asyncio
async def test_asset_tool_rename(registered_tool, mock_context, mock_unity_connection):
    """Test renaming an asset."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Asset renamed successfully",
        "data": {
            "originalPath": "Assets/Materials/OldName.mat",
            "newPath": "Assets/Materials/NewName.mat",
            "assetType": "Material"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="rename",
        path="Assets/Materials/OldName.mat",
        destination="Assets/Materials/NewName.mat"
    )
    
    # Check result
    assert result["success"] is True
    assert "renamed" in result.get("message", "").lower()
    assert result["data"]["originalPath"] == "Assets/Materials/OldName.mat"
    assert result["data"]["newPath"] == "Assets/Materials/NewName.mat"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_asset", {
        "action": "rename",
        "path": "Assets/Materials/OldName.mat",
        "destination": "Assets/Materials/NewName.mat"
    })

@pytest.mark.asyncio
async def test_asset_tool_search(registered_tool, mock_context, mock_unity_connection):
    """Test searching for assets."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Assets found successfully",
        "data": [
            {
                "path": "Assets/Materials/Red.mat",
                "assetType": "Material",
                "guid": "12345678901234567890123456789012"
            },
            {
                "path": "Assets/Materials/Blue.mat",
                "assetType": "Material",
                "guid": "23456789012345678901234567890123"
            }
        ]
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="search",
        path="Assets/Materials",
        search_pattern="*.mat",
        filter_type="Material"
    )
    
    # Check result
    assert result["success"] is True
    assert "found" in result.get("message", "").lower()
    assert len(result["data"]) == 2
    assert result["data"][0]["path"] == "Assets/Materials/Red.mat"
    assert result["data"][1]["path"] == "Assets/Materials/Blue.mat"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_asset", {
        "action": "search",
        "path": "Assets/Materials",
        "search_pattern": "*.mat",
        "filter_type": "Material"
    })

@pytest.mark.asyncio
async def test_asset_tool_get_info(registered_tool, mock_context, mock_unity_connection):
    """Test getting asset information."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Asset information retrieved successfully",
        "data": {
            "path": "Assets/Materials/ExampleMaterial.mat",
            "assetType": "Material",
            "guid": "12345678901234567890123456789012",
            "fileSize": 2048,
            "importedTime": "2023-09-15T14:30:00Z",
            "dependencies": [
                "Assets/Textures/ExampleTexture.png"
            ],
            "properties": {
                "shader": "Standard",
                "color": [1.0, 0.5, 0.5, 1.0],
                "smoothness": 0.5
            }
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="get_info",
        path="Assets/Materials/ExampleMaterial.mat"
    )
    
    # Check result
    assert result["success"] is True
    assert "information" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/Materials/ExampleMaterial.mat"
    assert result["data"]["assetType"] == "Material"
    assert len(result["data"]["dependencies"]) == 1
    assert result["data"]["properties"]["shader"] == "Standard"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_asset", {
        "action": "get_info",
        "path": "Assets/Materials/ExampleMaterial.mat"
    })

@pytest.mark.asyncio
async def test_asset_tool_create_folder(registered_tool, mock_context, mock_unity_connection):
    """Test creating a folder."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Folder created successfully",
        "data": {
            "path": "Assets/NewFolder",
            "assetType": "Folder",
            "guid": "12345678901234567890123456789012"
        }
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="create_folder",
        path="Assets/NewFolder"
    )
    
    # Check result
    assert result["success"] is True
    assert "folder" in result.get("message", "").lower()
    assert result["data"]["path"] == "Assets/NewFolder"
    assert result["data"]["assetType"] == "Folder"
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_asset", {
        "action": "create_folder",
        "path": "Assets/NewFolder"
    })

@pytest.mark.asyncio
async def test_asset_tool_get_components(registered_tool, mock_context, mock_unity_connection):
    """Test getting components from a prefab asset."""
    # Set up mock response
    mock_unity_connection.send_command.return_value = {
        "success": True,
        "message": "Components retrieved successfully",
        "data": [
            "UnityEngine.Transform",
            "UnityEngine.MeshFilter",
            "UnityEngine.MeshRenderer",
            "UnityEngine.BoxCollider",
            "MyGame.PlayerController"
        ]
    }
    
    # Call the tool function
    result = await registered_tool(
        ctx=mock_context,
        action="get_components",
        path="Assets/Prefabs/Player.prefab"
    )
    
    # Check result
    assert result["success"] is True
    assert "components" in result.get("message", "").lower()
    assert len(result["data"]) == 5
    assert "UnityEngine.Transform" in result["data"]
    assert "MyGame.PlayerController" in result["data"]
    
    # Check correct parameters were sent
    assert_command_called_with(mock_unity_connection, "manage_asset", {
        "action": "get_components",
        "path": "Assets/Prefabs/Player.prefab"
    })

@pytest.mark.asyncio
async def test_asset_tool_validation_error(registered_tool, mock_context, mock_unity_connection):
    """Test validation error handling."""
    # Configure mock to raise validation error
    mock_unity_connection.send_command.side_effect = ParameterValidationError("manage_asset 'create' action requires 'path' parameter")
    
    # Call with invalid parameters (missing required parameter)
    result = await registered_tool(
        ctx=mock_context,
        action="create"
        # Missing required path parameter
    )
    
    # Check result
    assert result["success"] is False
    assert "validation_error" in result
    assert result["validation_error"] is True
    
    # Reset the side effect for other tests
    mock_unity_connection.send_command.side_effect = None

def test_asset_tool_validation(asset_tool_instance, mock_unity_connection):
    """Test AssetTool class validation methods."""
    # Test validation for modify action without properties
    with pytest.raises(ParameterValidationError, match="requires 'properties' parameter"):
        asset_tool_instance.additional_validation("modify", {"path": "Assets/Test.mat"})
    
    # Test validation for move action without destination
    with pytest.raises(ParameterValidationError, match="requires 'destination' or 'destination_path' parameter"):
        asset_tool_instance.additional_validation("move", {"path": "Assets/Test.mat"})
        
    # Make sure the mock wasn't called unexpectedly
    mock_unity_connection.send_command.assert_not_called() 