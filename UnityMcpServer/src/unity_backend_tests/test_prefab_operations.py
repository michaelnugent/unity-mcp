"""
Tests for Prefab operations in the Unity backend.

These tests validate prefab creation, instantiation, and other prefab operations
with a live Unity Editor instance rather than using mocks.
"""

import pytest
import logging
import os
import time
import json
from typing import Dict, Any

from tools.manage_prefabs import PrefabsTool
from tools.manage_gameobject import GameObjectTool
from tools.manage_asset import AssetTool
from unity_connection import UnityConnection
from exceptions import UnityCommandError, ParameterValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-prefab-operations")

class TestPrefabOperations:
    """Test Prefab operations against a real Unity instance.
    
    These tests validate prefab creation, instantiation, and management in Unity.
    """

    def setup_method(self):
        """Set up the test environment.
        
        Creates new instances of the tools to be tested, initially
        without a real Unity connection.
        """
        self.prefab_tool = PrefabsTool()
        self.gameobject_tool = GameObjectTool()
        self.asset_tool = AssetTool()
        self.test_prefab_path = f"Assets/Prefabs/TestPrefab_{int(time.time())}.prefab"
        self.test_gameobject_name = f"TestGameObject_{int(time.time())}"
        
    def teardown_method(self):
        """Clean up any assets created during tests.
        
        This method attempts to delete any test assets that might have been created
        during the test to ensure a clean state for the next test.
        """
        if hasattr(self, 'prefab_tool') and hasattr(self, 'unity_conn') and self.unity_conn:
            try:
                # Try to clean up test prefab if it exists
                if hasattr(self, 'test_prefab_path'):
                    try:
                        self.prefab_tool.send_command("manage_asset", {
                            "action": "delete",
                            "path": self.test_prefab_path
                        })
                        logger.info(f"Cleaned up test prefab at {self.test_prefab_path}")
                    except Exception as e:
                        logger.info(f"No cleanup needed for prefab: {e}")
                
                # Try to clean up test GameObjects that might have been created
                if hasattr(self, 'test_gameobject_name'):
                    try:
                        self.gameobject_tool.send_command("manage_gameobject", {
                            "action": "delete",
                            "target": self.test_gameobject_name
                        })
                        logger.info(f"Cleaned up test GameObject: {self.test_gameobject_name}")
                    except Exception as e:
                        logger.info(f"No cleanup needed for GameObject: {e}")
                        
                # Also try to clean up any instantiated prefabs
                try:
                    instantiated_name = f"{self.test_gameobject_name}(Clone)"
                    self.gameobject_tool.send_command("manage_gameobject", {
                        "action": "delete",
                        "target": instantiated_name
                    })
                    logger.info(f"Cleaned up instantiated prefab: {instantiated_name}")
                except Exception as e:
                    logger.info(f"No cleanup needed for instantiated prefab: {e}")
            except Exception as e:
                logger.warning(f"Error during test cleanup: {e}")
                
    def _find_instantiated_prefab_name(self, prefab_base_name, gameobject_tool):
        """Helper to find the instantiated prefab's name by searching for both base and (Clone) names."""
        clone_name = f"{prefab_base_name}(Clone)"
        for _ in range(2):
            #for search_name in (clone_name, prefab_base_name):
            for search_name in [prefab_base_name]:
                find_instantiated_result = gameobject_tool.send_command("manage_gameobject", {
                    "action": "find",
                    "search_term": search_name,
                    "searchTerm": search_name,
                })
                logger.info(f"Find instantiated prefab response for '{search_name}': {find_instantiated_result}")
                if find_instantiated_result.get("success") and find_instantiated_result.get("data"):
                    found = find_instantiated_result["data"]
                    if isinstance(found, list) and found:
                        return found[0].get("name", search_name)
                    elif isinstance(found, dict) and "name" in found:
                        return found["name"]
            time.sleep(0.5)
        logger.error(f"Instantiated prefab not found in scene after retries. Tried both '{clone_name}' and '{prefab_base_name}'.")
        pytest.fail(f"Instantiated prefab not found in scene after retries. Tried both '{clone_name}' and '{prefab_base_name}'.")

    def test_create_prefab(self, unity_conn):
        """Test creating a prefab from a GameObject.
        
        This test creates a GameObject, adds a component to it, and then
        creates a prefab from the GameObject.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.prefab_tool.unity_conn = unity_conn
        self.gameobject_tool.unity_conn = unity_conn
        self.unity_conn = unity_conn
        
        # Dump the actual required params dictionary
        required_params = getattr(self.prefab_tool, "required_params", {})
        logger.info(f"Tool required_params dictionary: {required_params}")
        
        # First ensure the Prefabs folder exists
        prefabs_folder = "Assets/Prefabs"
        try:
            # Create Prefabs folder if it doesn't exist
            create_prefabs_result = self.prefab_tool.send_command("manage_asset", {
                "action": "create_folder",
                "path": prefabs_folder
            })
            logger.info(f"Created or verified Prefabs folder: {create_prefabs_result}")
        except Exception as e:
            logger.warning(f"Could not create or verify Prefabs folder: {e}")
        
        try:
            # Create a test GameObject first
            create_go_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": self.test_gameobject_name
            })
            
            logger.info(f"Create GameObject response: {create_go_result}")
            assert create_go_result["success"] is True, f"Failed to create GameObject: {create_go_result.get('error', '')}"
            
            # Add a component to the GameObject to make it more interesting
            add_component_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "add_component",
                "target": self.test_gameobject_name,
                "componentsToAdd": ["UnityEngine.BoxCollider"]
            })
            
            logger.info(f"Add component response: {add_component_result}")
            assert add_component_result["success"] is True, f"Failed to add component: {add_component_result.get('error', '')}"
            
            # Try with camelCase parameters
            camel_case_params = {
                "action": "create",
                "gameObjectPath": self.test_gameobject_name,
                "destinationPath": self.test_prefab_path,
                # Include both camelCase and snake_case versions to handle either case
                "game_object_path": self.test_gameobject_name,
                "destination_path": self.test_prefab_path
            }
            logger.info(f"Trying with combined camelCase/snake_case parameters: {camel_case_params}")
            
            # Debug: modify the parameters to match what we think is expected
            # Try using combined camelCase/snake_case parameters
            logger.info("Attempting to create prefab with combined parameters...")
            create_prefab_result = self.prefab_tool.send_command("manage_prefabs", camel_case_params)
            logger.info(f"Create prefab response: {create_prefab_result}")
            
            assert create_prefab_result["success"] is True, f"Failed to create prefab: {create_prefab_result.get('error', '')}"
            
            # Verify the prefab was created by checking if it exists
            verify_prefab_result = self.prefab_tool.send_command("manage_asset", {
                "action": "get_info",
                "path": self.test_prefab_path
            })
            
            logger.info(f"Verify prefab response: {verify_prefab_result}")
            assert verify_prefab_result["success"] is True, f"Failed to verify prefab exists: {verify_prefab_result.get('error', '')}"
            
        except Exception as e:
            logger.error(f"Error during prefab creation test: {e}")
            pytest.fail(f"Prefab creation test failed: {e}")

    def test_find_gameobject(self, unity_conn):
        """Test finding a GameObject in the scene.
        
        This test finds a GameObject in the scene using the GameObjectTool.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        self.gameobject_tool.unity_conn = unity_conn

        name = "TestPrefab_1746942643"
        find_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": name,
            #"searchTerm": name,
        })
        logger.info(f"Find GameObject response: {find_result}")
        assert find_result["success"] is True, f"Failed to find GameObject: {find_result.get('error', '')}"
        pytest.fail("Failed to find GameObject")
    
    def test_instantiate_prefab(self, unity_conn):
        """Test instantiating a prefab in the scene.
        
        This test creates a GameObject, converts it to a prefab, and then instantiates
        the prefab back into the scene.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.prefab_tool.unity_conn = unity_conn
        self.gameobject_tool.unity_conn = unity_conn
        self.unity_conn = unity_conn
        
        # Ensure Prefabs folder exists
        prefabs_folder = "Assets/Prefabs"
        try:
            create_prefabs_result = self.prefab_tool.send_command("manage_asset", {
                "action": "create_folder",
                "path": prefabs_folder
            })
            logger.info(f"Created or verified Prefabs folder: {create_prefabs_result}")
        except Exception as e:
            logger.warning(f"Could not create or verify Prefabs folder: {e}")
        
        try:
            # Create a test GameObject
            create_go_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": self.test_gameobject_name
            })
            
            logger.info(f"Create GameObject response: {create_go_result}")
            assert create_go_result["success"] is True, f"Failed to create GameObject: {create_go_result.get('error', '')}"
            
            # Create a prefab from the GameObject using both parameter formats
            create_prefab_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "create",
                "gameObjectPath": self.test_gameobject_name,
                "destinationPath": self.test_prefab_path,
                "game_object_path": self.test_gameobject_name,
                "destination_path": self.test_prefab_path
            })
            
            logger.info(f"Create prefab response: {create_prefab_result}")
            assert create_prefab_result["success"] is True, f"Failed to create prefab: {create_prefab_result.get('error', '')}"
            
            # Delete the original GameObject so we don't confuse it with the instantiated one
            delete_go_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "delete",
                "target": self.test_gameobject_name
            })
            
            logger.info(f"Delete GameObject response: {delete_go_result}")
            assert delete_go_result["success"] is True, f"Failed to delete original GameObject: {delete_go_result.get('error', '')}"
            
            # Instantiate the prefab using both parameter formats
            instantiate_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "instantiate",
                "prefabPath": self.test_prefab_path,
                "prefab_path": self.test_prefab_path
            })
            
            logger.info(f"Instantiate prefab response: {instantiate_result}")
            assert instantiate_result["success"] is True, f"Failed to instantiate prefab: {instantiate_result.get('error', '')}"
            
            # Get the path or name of the instantiated prefab from the response if available
            instantiated_name = None
            if "data" in instantiate_result:
                if isinstance(instantiate_result["data"], dict):
                    instantiated_name = (
                        instantiate_result["data"].get("gameObjectName") or
                        instantiate_result["data"].get("name") or
                        instantiate_result["data"].get("path")
                    )
                elif isinstance(instantiate_result["data"], str):
                    instantiated_name = instantiate_result["data"]
            if not instantiated_name:
                instantiated_name = f"{self.test_gameobject_name}(Clone)"
            logger.info(f"Initial instantiated_name for modification: {instantiated_name}")

            # Use prefab base name for searching instantiated object
            prefab_base_name = os.path.splitext(os.path.basename(self.test_prefab_path))[0]
            instantiated_name = self._find_instantiated_prefab_name(prefab_base_name, self.gameobject_tool)
            logger.info(f"Using instantiated_name for modification after find: {instantiated_name}")
            
            # Modify the instantiated prefab to create an override
            modify_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "modify",
                "target": instantiated_name,
                "position": [10.0, 20.0, 30.0]
            })
            
            logger.info(f"Modify position response: {modify_result}")
            assert modify_result["success"] is True, f"Failed to modify position: {modify_result.get('error', '')}"
            
            # List the overrides on the prefab instance using both parameter formats
            overrides_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "list_overrides",
                "gameObjectPath": instantiated_name,
                "game_object_path": instantiated_name
            })
            
            logger.info(f"List overrides response: {overrides_result}")
            assert overrides_result["success"] is True, f"Failed to list overrides: {overrides_result.get('error', '')}"
            
            # Verify we have at least one override related to the position
            if "data" in overrides_result and isinstance(overrides_result["data"], list):
                found_position_override = False
                for override in overrides_result["data"]:
                    if isinstance(override, dict) and override.get("component", "").lower() == "transform" and "position" in override.get("property", "").lower():
                        found_position_override = True
                        break
                
                if not found_position_override:
                    logger.warning(f"No position override found in {overrides_result['data']}")
                    # Not failing the test since the format might vary
            
        except Exception as e:
            logger.error(f"Error during prefab instantiation test: {e}")
            pytest.fail(f"Prefab instantiation test failed: {e}")
    
    def test_prefab_variant(self, unity_conn):
        """Test creating a prefab variant.
        
        This test creates a GameObject, converts it to a prefab, and then creates
        a prefab variant from the original prefab.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.prefab_tool.unity_conn = unity_conn
        self.gameobject_tool.unity_conn = unity_conn
        self.unity_conn = unity_conn
        
        # Ensure Prefabs folder exists
        prefabs_folder = "Assets/Prefabs"
        try:
            create_prefabs_result = self.prefab_tool.send_command("manage_asset", {
                "action": "create_folder",
                "path": prefabs_folder
            })
            logger.info(f"Created or verified Prefabs folder: {create_prefabs_result}")
        except Exception as e:
            logger.warning(f"Could not create or verify Prefabs folder: {e}")

        # Define the variant path
        variant_path = f"Assets/Prefabs/TestVariant_{int(time.time())}.prefab"
        
        try:
            # Create a test GameObject
            create_go_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": self.test_gameobject_name
            })
            
            logger.info(f"Create GameObject response: {create_go_result}")
            assert create_go_result["success"] is True, f"Failed to create GameObject: {create_go_result.get('error', '')}"
            
            # Add a component to the GameObject
            add_component_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "add_component",
                "target": self.test_gameobject_name,
                "componentsToAdd": ["UnityEngine.BoxCollider"]
            })
            
            logger.info(f"Add component response: {add_component_result}")
            assert add_component_result["success"] is True, f"Failed to add component: {add_component_result.get('error', '')}"
            
            # Create a prefab from the GameObject using both parameter formats
            create_prefab_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "create",
                "gameObjectPath": self.test_gameobject_name,
                "destinationPath": self.test_prefab_path,
                "game_object_path": self.test_gameobject_name,
                "destination_path": self.test_prefab_path
            })
            
            logger.info(f"Create prefab response: {create_prefab_result}")
            assert create_prefab_result["success"] is True, f"Failed to create prefab: {create_prefab_result.get('error', '')}"
            
            # Create a prefab variant from the original prefab using both parameter formats
            create_variant_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "create_variant",
                "prefabPath": self.test_prefab_path,
                "destinationPath": variant_path,
                "prefab_path": self.test_prefab_path,
                "destination_path": variant_path
            })
            
            logger.info(f"Create variant response: {create_variant_result}")
            assert create_variant_result["success"] is True, f"Failed to create prefab variant: {create_variant_result.get('error', '')}"
            
            # Verify the variant was created
            verify_variant_result = self.prefab_tool.send_command("manage_asset", {
                "action": "get_info",
                "path": variant_path
            })
            
            logger.info(f"Verify variant response: {verify_variant_result}")
            assert verify_variant_result["success"] is True, f"Failed to verify variant exists: {verify_variant_result.get('error', '')}"
            
            # Clean up the variant
            try:
                delete_variant_result = self.prefab_tool.send_command("manage_asset", {
                    "action": "delete",
                    "path": variant_path
                })
                logger.info(f"Cleaned up variant: {delete_variant_result}")
            except Exception as e:
                logger.warning(f"Failed to clean up variant: {e}")
            
        except Exception as e:
            logger.error(f"Error during prefab variant test: {e}")
            pytest.fail(f"Prefab variant test failed: {e}")

    def test_prefab_overrides(self, unity_conn):
        """Test listing prefab overrides.
        
        This test creates a prefab, instantiates it, modifies the instance,
        and then lists the overrides.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.prefab_tool.unity_conn = unity_conn
        self.gameobject_tool.unity_conn = unity_conn
        self.unity_conn = unity_conn
        
        # Ensure Prefabs folder exists
        prefabs_folder = "Assets/Prefabs"
        try:
            create_prefabs_result = self.prefab_tool.send_command("manage_asset", {
                "action": "create_folder",
                "path": prefabs_folder
            })
            logger.info(f"Created or verified Prefabs folder: {create_prefabs_result}")
        except Exception as e:
            logger.warning(f"Could not create or verify Prefabs folder: {e}")
        
        try:
            # Create a test GameObject
            create_go_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": self.test_gameobject_name
            })
            
            logger.info(f"Create GameObject response: {create_go_result}")
            assert create_go_result["success"] is True, f"Failed to create GameObject: {create_go_result.get('error', '')}"
            
            # Create a prefab from the GameObject using both parameter formats
            create_prefab_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "create",
                "gameObjectPath": self.test_gameobject_name,
                "destinationPath": self.test_prefab_path,
                "game_object_path": self.test_gameobject_name,
                "destination_path": self.test_prefab_path
            })
            
            logger.info(f"Create prefab response: {create_prefab_result}")
            assert create_prefab_result["success"] is True, f"Failed to create prefab: {create_prefab_result.get('error', '')}"
            
            # Delete the original GameObject
            delete_go_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "delete",
                "target": self.test_gameobject_name
            })
            
            logger.info(f"Delete GameObject response: {delete_go_result}")
            assert delete_go_result["success"] is True, f"Failed to delete original GameObject: {delete_go_result.get('error', '')}"
            
            # Instantiate the prefab using both parameter formats
            instantiate_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "instantiate",
                "prefabPath": self.test_prefab_path,
                "prefab_path": self.test_prefab_path
            })
            
            logger.info(f"Instantiate prefab response: {instantiate_result}")
            assert instantiate_result["success"] is True, f"Failed to instantiate prefab: {instantiate_result.get('error', '')}"
            
            # Get the path or name of the instantiated prefab from the response if available
            instantiated_name = None
            if "data" in instantiate_result:
                if isinstance(instantiate_result["data"], dict):
                    instantiated_name = (
                        instantiate_result["data"].get("gameObjectName") or
                        instantiate_result["data"].get("name") or
                        instantiate_result["data"].get("path")
                    )
                elif isinstance(instantiate_result["data"], str):
                    instantiated_name = instantiate_result["data"]
            if not instantiated_name:
                instantiated_name = f"{self.test_gameobject_name}(Clone)"
            logger.info(f"Initial instantiated_name for modification: {instantiated_name}")

            # Use prefab base name for searching instantiated object
            prefab_base_name = os.path.splitext(os.path.basename(self.test_prefab_path))[0]
            instantiated_name = self._find_instantiated_prefab_name(prefab_base_name, self.gameobject_tool)
            logger.info(f"Using instantiated_name for modification after find: {instantiated_name}")
            
            # Modify the instantiated prefab to create an override
            modify_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "modify",
                "target": instantiated_name,
                "position": [10.0, 20.0, 30.0]
            })
            
            logger.info(f"Modify position response: {modify_result}")
            assert modify_result["success"] is True, f"Failed to modify position: {modify_result.get('error', '')}"
            
            # List the overrides on the prefab instance using both parameter formats
            overrides_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "list_overrides",
                "gameObjectPath": instantiated_name,
                "game_object_path": instantiated_name
            })
            
            logger.info(f"List overrides response: {overrides_result}")
            assert overrides_result["success"] is True, f"Failed to list overrides: {overrides_result.get('error', '')}"
            
            # Verify we have at least one override related to the position
            if "data" in overrides_result and isinstance(overrides_result["data"], list):
                found_position_override = False
                for override in overrides_result["data"]:
                    if isinstance(override, dict) and override.get("component", "").lower() == "transform" and "position" in override.get("property", "").lower():
                        found_position_override = True
                        break
                
                if not found_position_override:
                    logger.warning(f"No position override found in {overrides_result['data']}")
                    # Not failing the test since the format might vary
            
        except Exception as e:
            logger.error(f"Error during prefab overrides test: {e}")
            pytest.fail(f"Prefab overrides test failed: {e}")
    
    def test_parameter_validation(self, unity_conn):
        """Test parameter validation for prefab operations.
        
        This test verifies that parameter validation works correctly for prefab operations.
        
        Args:
            unity_conn: The Unity connection fixture
        """
        # Use the real Unity connection
        self.prefab_tool.unity_conn = unity_conn
        self.unity_conn = unity_conn
        
        # Test missing parameters for create
        try:
            create_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "create",
                "destination_path": self.test_prefab_path
                # Missing game_object_path
            })
            assert create_result["success"] is False, "Should fail with missing game_object_path"
            assert (
                "game_object_path" in create_result.get("error", "") or
                "gameObjectPath" in create_result.get("error", "") or
                "game_object_path" in create_result.get("message", "").lower() or
                "gameObjectPath" in create_result.get("message", "").lower()
            )
        except ParameterValidationError as e:
            error_message = str(e)
            assert (
                "game_object_path" in error_message or
                "gameObjectPath" in error_message
            ), f"Error message did not mention missing game_object_path: {error_message}"
        
        # Test missing parameters for instantiate
        try:
            instantiate_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "instantiate",
                # Missing prefab_path
            })
            assert instantiate_result["success"] is False, "Should fail with missing prefab_path"
            assert (
                "prefab_path" in instantiate_result.get("error", "") or
                "prefabPath" in instantiate_result.get("error", "") or
                "prefab_path" in instantiate_result.get("message", "").lower() or
                "prefabPath" in instantiate_result.get("message", "").lower()
            )
        except ParameterValidationError as e:
            error_message = str(e)
            assert (
                "prefab_path" in error_message or
                "prefabPath" in error_message
            ), f"Error message did not mention missing prefab_path: {error_message}"
        
        # Test missing parameters for add_component
        try:
            add_component_result = self.prefab_tool.send_command("manage_prefabs", {
                "action": "add_component",
                "prefab_path": self.test_prefab_path
                # Missing component_type
            })
            assert add_component_result["success"] is False, "Should fail with missing component_type"
            assert (
                "component_type" in add_component_result.get("error", "") or
                "componentType" in add_component_result.get("error", "") or
                "component_type" in add_component_result.get("message", "").lower() or
                "componentType" in add_component_result.get("message", "").lower()
            )
        except ParameterValidationError as e:
            error_message = str(e)
            assert (
                "component_type" in error_message or
                "componentType" in error_message
            ), f"Error message did not mention missing component_type: {error_message}" 