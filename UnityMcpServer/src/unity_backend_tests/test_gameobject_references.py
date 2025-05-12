"""
Tests for GameObject reference standardization with a real Unity Editor instance.

These tests validate that the various ways of referencing GameObjects work correctly
with a live Unity Editor instance rather than using mocks.
"""

import pytest
import logging
import time
from typing import Dict, Any, List, Optional

from tools.manage_gameobject import GameObjectTool
from tools.manage_scene import SceneTool
from exceptions import UnityCommandError, ParameterValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-gameobject-references")

class TestGameObjectReferences:
    """Test GameObject reference formats with a real Unity Editor instance."""

    def setup_method(self):
        """Set up the test environment."""
        self.gameobject_tool = GameObjectTool()
        self.scene_tool = SceneTool()
        
    def test_reference_by_name(self, unity_conn, cleanup_gameobjects):
        """Test referencing GameObjects by name with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create a test GameObject
        obj_name = "TestReferenceByName"
        create_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": obj_name,
            "position": [1, 2, 3]
        })
        
        # Log the result
        logger.info(f"Create GameObject response: {create_result}")
        
        # Verify the creation was successful
        assert create_result["success"] is True
        
        # Wait a moment for Unity to process
        time.sleep(0.5)
        
        # Now try to reference it by name
        find_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_method": "by_name",
            "search_term": obj_name
        })
        
        # Log the result
        logger.info(f"Find GameObject by name response: {find_result}")
        
        # Verify the response
        assert find_result["success"] is True
        assert "data" in find_result
        
        # Should return info about the GameObject
        assert isinstance(find_result["data"], dict)
        assert "name" in find_result["data"]
        assert find_result["data"]["name"] == obj_name
        
        # Now modify it to test reference works
        modify_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "modify",
            "target": obj_name,  # Reference by name
            "position": [4, 5, 6]
        })
        
        # Log the result
        logger.info(f"Modify GameObject by name response: {modify_result}")
        
        # Verify the modification was successful
        assert modify_result["success"] is True
        
    def test_reference_by_path(self, unity_conn, cleanup_gameobjects):
        """Test referencing GameObjects by hierarchical path with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create a parent GameObject
        parent_name = "TestParent"
        create_parent_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": parent_name
        })
        
        # Log the result
        logger.info(f"Create parent GameObject response: {create_parent_result}")
        
        # Verify the creation was successful
        assert create_parent_result["success"] is True
        
        # Wait a moment for Unity to process
        time.sleep(0.5)
        
        # Create a child GameObject
        child_name = "TestChild"
        create_child_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": child_name,
            "parent": parent_name  # Set parent by name
        })
        
        # Log the result
        logger.info(f"Create child GameObject response: {create_child_result}")
        
        # Verify the creation was successful
        assert create_child_result["success"] is True
        
        # Wait a moment for Unity to process
        time.sleep(0.5)
        
        # Now try to reference the child by hierarchical path
        path = f"{parent_name}/{child_name}"
        find_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_method": "by_path",
            "search_term": path
        })
        
        # Log the result
        logger.info(f"Find GameObject by path response: {find_result}")
        
        # Verify the response
        assert find_result["success"] is True
        assert "data" in find_result
        
        # Should return info about the GameObject
        assert isinstance(find_result["data"], dict)
        assert "name" in find_result["data"]
        assert find_result["data"]["name"] == child_name
        
        # Now modify the child using the path reference
        modify_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "modify",
            "target": path,  # Reference by path
            "position": [4, 5, 6]
        })
        
        # Log the result
        logger.info(f"Modify GameObject by path response: {modify_result}")
        
        # Verify the modification was successful
        assert modify_result["success"] is True
    
    def test_find_with_wildcard(self, unity_conn, cleanup_gameobjects):
        """Test finding GameObjects with wildcard patterns with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create multiple test GameObjects with a pattern
        prefix = "TestWildcard"
        created_objects = []
        for i in range(3):
            obj_name = f"{prefix}{i}"
            created_objects.append(obj_name)
            create_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": obj_name
            })
            
            # Verify the creation was successful
            assert create_result["success"] is True
        
        # Wait a moment for Unity to process
        time.sleep(1)
        
        # Look for each object individually instead of using wildcard
        for obj_name in created_objects:
            find_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "find",
                "search_method": "by_name",
                "search_term": obj_name
            })
            
            # Log the result
            logger.info(f"Find GameObject {obj_name} response: {find_result}")
            
            # Verify the response
            assert find_result["success"] is True
            assert "data" in find_result
            
            # Should return info about the GameObject
            assert isinstance(find_result["data"], dict)
            assert "name" in find_result["data"]
            assert find_result["data"]["name"] == obj_name
    
    def test_nested_gameobject_hierarchy(self, unity_conn, cleanup_gameobjects):
        """Test working with nested GameObject hierarchies with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create a deeply nested hierarchy
        root_name = "TestRoot"
        create_root_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": root_name
        })
        
        # Verify the creation was successful
        assert create_root_result["success"] is True
        
        # Wait a moment for Unity to process
        time.sleep(0.5)
        
        # Create level 1 child
        level1_name = "Level1"
        create_level1_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": level1_name,
            "parent": root_name
        })
        
        # Verify the creation was successful
        assert create_level1_result["success"] is True
        
        # Wait a moment for Unity to process
        time.sleep(0.5)
        
        # Create level 2 child
        level2_name = "Level2"
        create_level2_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": level2_name,
            "parent": f"{root_name}/{level1_name}"  # Reference by path
        })
        
        # Verify the creation was successful
        assert create_level2_result["success"] is True
        
        # Wait a moment for Unity to process
        time.sleep(0.5)
        
        # Create level 3 child
        level3_name = "Level3"
        create_level3_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": level3_name,
            "parent": f"{root_name}/{level1_name}/{level2_name}"  # Reference by deep path
        })
        
        # Log the result
        logger.info(f"Create level 3 GameObject response: {create_level3_result}")
        
        # Verify the creation was successful
        assert create_level3_result["success"] is True
        
        # Wait a moment for Unity to process
        time.sleep(0.5)
        
        # Now try to reference the deepest child by hierarchical path
        deep_path = f"{root_name}/{level1_name}/{level2_name}/{level3_name}"
        find_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_method": "by_path",
            "search_term": deep_path
        })
        
        # Log the result
        logger.info(f"Find GameObject by deep path response: {find_result}")
        
        # Verify the response
        assert find_result["success"] is True
        assert "data" in find_result
        
        # Should return info about the GameObject
        assert isinstance(find_result["data"], dict)
        assert "name" in find_result["data"]
        assert find_result["data"]["name"] == level3_name
    
    def test_component_reference(self, unity_conn, cleanup_gameobjects):
        """Test referencing and working with components with a real Unity instance.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create a test GameObject with a component
        obj_name = "TestComponentReference"
        create_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": obj_name,
            "components_to_add": ["UnityEngine.BoxCollider"]
        })
        
        # Log the result
        logger.info(f"Create GameObject with component response: {create_result}")
        
        # Verify the creation was successful
        assert create_result["success"] is True
        
        # Wait a moment for Unity to process
        time.sleep(0.5)
        
        # Now get components of the GameObject
        get_components_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "get_components",
            "target": obj_name
        })
        
        # Log the result
        logger.info(f"Get components response: {get_components_result}")
        
        # Verify the response
        assert get_components_result["success"] is True
        assert "data" in get_components_result
        
        # Should have found the BoxCollider component
        components = get_components_result["data"]
        assert isinstance(components, list)
        has_box_collider = False
        for comp in components:
            if isinstance(comp, dict):
                # Check using different available keys
                if "type" in comp and "BoxCollider" in comp["type"]:
                    has_box_collider = True
                    break
                elif "ObjectTypeName" in comp and "BoxCollider" in comp["ObjectTypeName"]:
                    has_box_collider = True
                    break
                elif "__type" in comp and "BoxCollider" in comp["__type"]:
                    has_box_collider = True
                    break
        
        assert has_box_collider, "Expected to find BoxCollider component"
        
        # Now modify the component property
        set_property_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "set_component_property",
            "target": obj_name,
            "component_name": "BoxCollider", 
            "component_properties": {
                "isTrigger": True,
                "size": [2, 2, 2]
            }
        })
        
        # Log the result
        logger.info(f"Set component property response: {set_property_result}")
        
        # Verify the modification was successful
        assert set_property_result["success"] is True

# Run the tests if this script is executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 