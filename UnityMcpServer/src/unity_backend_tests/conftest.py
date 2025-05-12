"""
Fixtures for Unity backend testing

This module provides pytest fixtures for the Unity backend tests that connect to an actual
Unity Editor instance instead of using mocks.
"""
import pytest
import logging
import time
import socket
from typing import Dict, Any, List, Tuple, Union

from unity_connection import UnityConnection, get_unity_connection, ConnectionError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("unity-backend-tests")

def is_unity_running(host: str = "localhost", port: int = 6400, timeout: int = 1) -> bool:
    """Check if Unity is running and available on the given port.
    
    Args:
        host: The host where Unity is running
        port: The port Unity is listening on
        timeout: Socket timeout in seconds
        
    Returns:
        bool: True if Unity is available, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except:
        return False

@pytest.fixture(scope="session")
def unity_conn():
    """Provide a real connection to the Unity Editor.
    
    This fixture will try to connect to a real Unity Editor instance.
    The tests will be skipped if the Unity Editor is not running.
    
    Returns:
        UnityConnection: A connection to the Unity Editor
    """
    # Verify that Unity is running before trying to connect
    if not is_unity_running():
        pytest.skip("Unity Editor is not running. Start Unity with the MCP Bridge plugin to run these tests.")
    
    # Get a real connection to Unity
    try:
        connection = get_unity_connection()
        
        # Verify connection with a ping
        connection.send_command("ping")
        logger.info("Successfully connected to Unity Editor")
        
        yield connection
        
        # Close the connection when done
        connection.disconnect()
        logger.info("Disconnected from Unity Editor")
    except ConnectionError as e:
        pytest.skip(f"Could not connect to Unity Editor: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error connecting to Unity: {str(e)}")
        pytest.skip(f"Error connecting to Unity: {str(e)}")

@pytest.fixture
def cleanup_gameobjects(unity_conn):
    """Clean up test GameObjects after each test.
    
    This fixture will yield control to the test and then delete any GameObjects
    with names that start with "Test" to clean up after tests.
    
    Args:
        unity_conn: The Unity connection from the unity_conn fixture
    """
    # Let the test run
    yield
    
    # Clean up test GameObjects
    try:
        # Find all GameObjects in the scene without using wildcards
        result = unity_conn.send_command("manage_gameobject", {
            "action": "find",
            "find_all": True,
            "search_inactive": True
        })
        
        # Check if we got a valid response
        if isinstance(result, dict) and "data" in result:
            gameobjects = result.get("data", [])
            test_objects_to_delete = []
            
            # Make sure gameObjects is a list
            if isinstance(gameobjects, list):
                # First, identify all test objects (those starting with "Test")
                for go in gameobjects:
                    if isinstance(go, dict) and "name" in go:
                        go_name = go.get("name", "")
                        # Check if the name starts with "Test"
                        if go_name and go_name.startswith("Test"):
                            test_objects_to_delete.append(go_name)
                
                # Then delete them one by one
                for test_obj_name in test_objects_to_delete:
                    try:
                        unity_conn.send_command("manage_gameobject", {
                            "action": "delete",
                            "target": test_obj_name
                        })
                        logger.info(f"Cleaned up GameObject: {test_obj_name}")
                    except Exception as e:
                        logger.warning(f"Error deleting GameObject {test_obj_name}: {str(e)}")
                
                if test_objects_to_delete:
                    logger.info(f"Cleaned up {len(test_objects_to_delete)} test GameObjects")
                else:
                    logger.info("No test GameObjects found for cleanup")
            else:
                logger.warning(f"Unexpected response format for GameObjects: {gameobjects}")
        else:
            logger.warning(f"Unable to find GameObjects for cleanup: {result}")
    except Exception as e:
        logger.warning(f"Error during cleanup: {str(e)}")

@pytest.fixture
def reset_scene(unity_conn):
    """Reset the scene to a clean state.
    
    This fixture will store the original scene information and restore it after the test.
    Note: We avoid creating a new scene to prevent dialog popups.
    
    Args:
        unity_conn: The Unity connection from the unity_conn fixture
    """
    # Store original scene information
    original_scene_info = unity_conn.send_command("manage_editor", {
        "action": "get_state"
    })
    original_scene = original_scene_info.get("activeScene", "")
    logger.info(f"Stored original scene: {original_scene}")
    
    # Let the test run - we don't create a new scene to avoid popups
    yield
    
    # Restore original scene if needed
    try:
        if original_scene:
            # Only attempt to restore if we have a valid original scene path
            unity_conn.send_command("manage_scene", {
                "action": "load",
                "path": original_scene
            })
            logger.info(f"Restored original scene: {original_scene}")
    except Exception as e:
        logger.warning(f"Error restoring original scene: {str(e)}") 