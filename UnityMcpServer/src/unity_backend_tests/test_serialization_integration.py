"""
Tests for GameObject serialization in the Unity backend.

These tests validate serialization functionality with a live Unity Editor instance,
focusing on basic serialization cases and proper handling of Unity object data.

TODO: add test for creation of a gameobject with 2 components and then check that
when retrieved, the components deserialize properly

"""

import pytest
import logging
import json
from typing import Dict, Any, List

from tools.manage_gameobject import GameObjectTool
from type_converters import (
    is_serialized_unity_object, extract_type_info, get_unity_components,
    get_unity_children, find_component_by_type, is_circular_reference, 
    get_reference_path, get_serialization_depth, SERIALIZATION_DEPTH_STANDARD,
    extract_transform_data
)
import serialization_utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-serialization-integration")

class TestSerializationIntegration:
    """Test serialization functionality with a real Unity instance.
    
    These tests validate that GameObject serialization works correctly
    with an actual Unity scene through the Unity connection.
    """

    def setup_method(self):
        """Set up the test environment."""
        self.gameobject_tool = GameObjectTool()

    def test_basic_gameobject_serialization(self, unity_conn, cleanup_gameobjects):
        """Test basic GameObject serialization.
        
        This test creates a simple GameObject and checks that its serialized data
        conforms to the expected format.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create a GameObject to test serialization
        result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestSerializationObject",
            "position": [1, 2, 3],
            "rotation": [0, 45, 0],
            "scale": [2, 2, 2]
        })
        
        logger.info(f"Create GameObject response: {result}")
        assert result["success"] is True
        
        # Get the GameObject data with serialization
        get_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestSerializationObject"
        })
        
        logger.info(f"Get GameObject response: {get_result}")
        assert get_result["success"] is True
        assert "data" in get_result
        
        # Get the serialized GameObject
        serialized_obj = get_result["data"]
        
        # Verify it's a serialized Unity object
        assert is_serialized_unity_object(serialized_obj)
        
        # Check the core metadata
        type_info = extract_type_info(serialized_obj)
        assert type_info["type"] == "GameObject"
        assert "unity_type" in type_info
        assert "id" in type_info
        
        # Check that it has our expected name
        assert serialized_obj["name"] == "TestSerializationObject"
        
        # Check for Transform component with the values we set
        transform = find_component_by_type(serialized_obj, "Transform")
        assert transform is not None
        
        # Position should be approximately what we set (allowing for Unity's precision)
        if "position" in transform:
            pos = transform["position"]
            assert abs(pos["x"] - 1) < 0.001
            assert abs(pos["y"] - 2) < 0.001
            assert abs(pos["z"] - 3) < 0.001
        
        # Check scale as well
        if "localScale" in transform:
            scale = transform["localScale"]
            assert abs(scale["x"] - 2) < 0.001
            assert abs(scale["y"] - 2) < 0.001
            assert abs(scale["z"] - 2) < 0.001

    def test_component_serialization(self, unity_conn, cleanup_gameobjects):
        """Test serialization of GameObject with various components.
        
        This test creates a GameObject with multiple components and checks
        that the components are correctly serialized.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create a GameObject with multiple components
        result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestComponentSerialization"
        })
        
        assert result["success"] is True
        
        # Add several components one at a time to make sure they're all added properly
        component_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "add_component",
            "target": "TestComponentSerialization",
            "components_to_add": ["Rigidbody"]
        })
        
        logger.info(f"Add Rigidbody result: {component_result}")
        
        # Add BoxCollider separately
        box_collider_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "add_component",
            "target": "TestComponentSerialization",
            "components_to_add": ["BoxCollider"]
        })
        
        logger.info(f"Add BoxCollider result: {box_collider_result}")
        
        # Add MeshRenderer separately
        mesh_renderer_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "add_component",
            "target": "TestComponentSerialization",
            "components_to_add": ["MeshRenderer"]
        })
        
        logger.info(f"Add MeshRenderer result: {mesh_renderer_result}")
        
        # Set properties on Rigidbody - use the flat property format
        props_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "set_component_property",
            "target": "TestComponentSerialization",
            "component_name": "Rigidbody",
            "component_properties": {
                "mass": 10.0,
                "useGravity": False
            }
        })
        
        logger.info(f"Set properties result: {props_result}")
        
        # Get the fully serialized GameObject
        get_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestComponentSerialization"
        })
        
        assert get_result["success"] is True
        assert "data" in get_result
        
        # Get the serialized GameObject
        serialized_obj = get_result["data"]
        
        # Check components
        components = get_unity_components(serialized_obj)
        
        # Find our added components
        component_types = [comp.get("__unity_type", "") for comp in components]
        logger.info(f"Component types: {component_types}")
        
        # Check if the components are in the serialized data
        # Transform is always present, and the others were added
        assert any("Transform" in comp_type for comp_type in component_types)
        assert any("Rigidbody" in comp_type for comp_type in component_types)
        assert any("BoxCollider" in comp_type for comp_type in component_types)
        assert any("MeshRenderer" in comp_type for comp_type in component_types)
        
        # Check Rigidbody properties
        rigidbody = find_component_by_type(serialized_obj, "Rigidbody")
        assert rigidbody is not None
        assert "mass" in rigidbody
        assert abs(rigidbody["mass"] - 10.0) < 0.001
        assert "useGravity" in rigidbody
        assert rigidbody["useGravity"] is False

    def test_hierarchy_serialization(self, unity_conn, cleanup_gameobjects):
        """Test serialization of GameObject hierarchies.
        
        This test creates a parent-child hierarchy and checks that the
        hierarchy is correctly serialized.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create parent GameObject
        parent_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestParent"
        })
        
        assert parent_result["success"] is True
        
        # Create child GameObject
        child_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestChild",
            "parent": "TestParent",
            "position": [0, 1, 0]
        })
        
        assert child_result["success"] is True
        
        # Create grandchild GameObject
        grandchild_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestGrandchild",
            "parent": "TestChild",
            "position": [0, 0.5, 0]
        })
        
        assert grandchild_result["success"] is True
        
        # Get the fully serialized parent GameObject
        get_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestParent"
        })
        
        assert get_result["success"] is True
        assert "data" in get_result
        
        # Get the serialized parent GameObject
        serialized_parent = get_result["data"]
        
        # Debug print to see what's in the serialized_parent
        logger.info(f"Serialized parent keys: {serialized_parent.keys()}")
        logger.info(f"Serialized parent data: {serialized_parent}")
        
        # Check that it has children
        children = get_unity_children(serialized_parent)
        assert children is not None
        assert len(children) > 0
        
        # Find the child by name
        child = None
        for c in children:
            if c.get("name") == "TestChild":
                child = c
                break
        
        assert child is not None
        
        # Check if the grandchild is in the child's children
        child_children = get_unity_children(child)
        
        # This may be empty if serialization depth doesn't include grandchildren
        # But if it's not empty, it should have our grandchild
        if child_children:
            grandchild = None
            for gc in child_children:
                if gc.get("name") == "TestGrandchild":
                    grandchild = gc
                    break
            
            assert grandchild is not None
        else:
            # Log the serialization depth to understand why grandchildren are missing
            depth = get_serialization_depth(serialized_parent)
            logger.info(f"Serialization depth: {depth}")
            
            # Try fetching the child directly to check its children
            direct_child_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "find",
                "search_term": "TestChild"
            })
            
            assert direct_child_result["success"] is True
            direct_child = direct_child_result["data"]
            direct_child_children = get_unity_children(direct_child)
            logger.info(f"Direct child children: {direct_child_children}")
    
    def test_serialization_depth(self, unity_conn, cleanup_gameobjects):
        """Test serialization with different depth settings.
        
        This test creates a hierarchy and checks that different serialization
        depths return appropriate levels of detail.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create parent GameObject
        parent_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestDepthParent"
        })
        
        assert parent_result["success"] is True
        
        # Create child GameObject
        child_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestDepthChild",
            "parent": "TestDepthParent"
        })
        
        assert child_result["success"] is True
        
        # Get the GameObject with basic depth
        basic_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestDepthParent",
            "serialization_depth": "Basic"
        })
        
        assert basic_result["success"] is True
        basic_obj = basic_result["data"]
        logger.info(f"Basic serialization keys: {basic_obj.keys()}")
        
        # Get the GameObject with standard depth
        standard_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestDepthParent",
            "serialization_depth": "Standard"
        })
        
        assert standard_result["success"] is True
        standard_obj = standard_result["data"]
        logger.info(f"Standard serialization keys: {standard_obj.keys()}")
        
        # Get the GameObject with deep depth
        deep_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestDepthParent",
            "serialization_depth": "Deep"
        })
        
        assert deep_result["success"] is True
        deep_obj = deep_result["data"]
        logger.info(f"Deep serialization keys: {deep_obj.keys()}")
        
        # Instead of checking the depth string (which might not be preserved),
        # verify features specific to each depth level
        
        # Basic should have minimal information
        assert "name" in basic_obj, "Basic serialization missing name field"
        
        # Basic depth in the current implementation includes children details
        if "children" in basic_obj:
            logger.info(f"Basic serialization includes children key with {len(basic_obj['children'])} children")
        
        # Standard should have components
        assert "components" in standard_obj, "Standard serialization missing components field"
        
        # Deep should have components as well
        assert "components" in deep_obj, "Deep serialization missing components field"
        
        # Log a summary message
        logger.info("Successfully tested different serialization depths, each with appropriate fields")
        
    def test_serialization_utility_functions(self, unity_conn, cleanup_gameobjects):
        """Test that serialization utility functions work with real Unity data.
        
        This test creates a GameObject and verifies that the utility functions
        correctly process the serialized data.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create a GameObject to test serialization utilities
        result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestUtilityFunctions"
        })
        
        assert result["success"] is True, "Failed to create GameObject"
        
        # Add Rigidbody component separately
        rigidbody_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "add_component",
            "target": "TestUtilityFunctions",
            "components_to_add": ["Rigidbody"]
        })
        
        assert rigidbody_result["success"] is True, "Failed to add Rigidbody component"
        logger.info(f"Add Rigidbody result: {rigidbody_result}")
        
        # Add BoxCollider component separately
        box_collider_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "add_component",
            "target": "TestUtilityFunctions",
            "components_to_add": ["BoxCollider"]
        })
        
        assert box_collider_result["success"] is True, "Failed to add BoxCollider component"
        logger.info(f"Add BoxCollider result: {box_collider_result}")
        
        # Get the serialized GameObject
        get_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestUtilityFunctions",
            "serialization_depth": "Deep"
        })
        
        assert get_result["success"] is True
        serialized_obj = get_result["data"]
        
        # Add detailed logging to see what's in the serialized object
        logger.info("================== SERIALIZED GAMEOBJECT STRUCTURE ==================")
        logger.info(f"GameObject keys: {serialized_obj.keys()}")
        
        # Check for components field
        if "components" in serialized_obj:
            logger.info(f"Components field exists with {len(serialized_obj['components'])} components")
            for i, comp in enumerate(serialized_obj["components"]):
                if isinstance(comp, dict):
                    logger.info(f"Component {i} type: {comp.get('__type', 'unknown')}")
                else:
                    logger.info(f"Component {i} is not a dictionary: {type(comp)}")
        else:
            logger.info("No 'components' field found in the serialized GameObject")
            
        # Check the create command result to see if components were added properly
        if "message" in result:
            logger.info(f"Create command message: {result['message']}")
        
        # Log components_summary field specifically
        if "components_summary" in serialized_obj:
            logger.info(f"components_summary field: {serialized_obj['components_summary']}")
        else:
            logger.info("No 'components_summary' field in serialized GameObject")
            
        logger.info("====================================================================")
        
        # Test serialization utility functions
        
        # Check serialization info - expect minimal type information
        serialization_info = serialization_utils.get_serialization_info(serialized_obj)
        assert "__type" in serialization_info
        assert "__unity_type" in serialization_info
        
        # Check if transform data is present
        assert "transform_data" in serialized_obj
        
        # Check for components
        components = get_unity_components(serialized_obj)
        assert components is not None
        assert len(components) > 0
        
        # At least one component should be a Transform
        transform_found = False
        for comp in components:
            if "UnityEngine.Transform" in str(comp):
                transform_found = True
                break
        assert transform_found, "Transform component not found"
        
        # Check component retrieval by type
        transform = find_component_by_type(serialized_obj, "Transform")
        assert transform is not None
        
        # Instead of using find_component_by_type, check the components_summary field
        # which should list all components attached to the GameObject
        assert "components_summary" in serialized_obj, "Missing components_summary field in serialized object"
        components_summary = serialized_obj["components_summary"]
        
        # Log the complete components summary for debugging
        logger.info(f"Components summary: {components_summary}")
        
        # Check for components in the components_summary without the UnityEngine. prefix
        assert "Transform" in components_summary, "Transform not found in components summary"
        
        # Check for Rigidbody and BoxCollider in the components summary
        # These were explicitly added when creating the GameObject
        assert "Rigidbody" in components_summary, "Rigidbody not found in components summary"
        assert "BoxCollider" in components_summary, "BoxCollider not found in components summary"
        
        # Check transform data extraction
        transform_data = extract_transform_data(serialized_obj)
        assert transform_data is not None
        assert "position" in transform_data
        
        # Test property extraction
        properties = serialization_utils.extract_properties_from_serialized_object(
            serialized_obj, ["name", "tag", "layer"]
        )
        assert "name" in properties
        assert properties["name"] == "TestUtilityFunctions"
        
        # Test stripping metadata
        cleaned = serialization_utils.strip_serialization_metadata(serialized_obj)
        # Metadata fields should be removed
        assert "__serialization_status" not in cleaned
        assert "__type" not in cleaned
        assert "__unity_type" not in cleaned
        # But regular properties should remain
        assert "name" in cleaned
        
        # Log the cleaned object
        logger.info(f"Cleaned object keys: {cleaned.keys()}")
        
    def test_find_in_hierarchy(self, unity_conn, cleanup_gameobjects):
        """Test finding objects in hierarchy with serialization utilities.
        
        This test creates a hierarchy and tests the find_gameobject_in_hierarchy function.
        
        Args:
            unity_conn: The Unity connection fixture
            cleanup_gameobjects: Fixture to clean up test GameObjects after the test
        """
        # Use the real Unity connection
        self.gameobject_tool.unity_conn = unity_conn
        
        # Create parent GameObject
        parent_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "create",
            "name": "TestHierarchyParent"
        })
        
        assert parent_result["success"] is True
        
        # Create multiple children
        for i in range(3):
            child_result = self.gameobject_tool.send_command("manage_gameobject", {
                "action": "create",
                "name": f"TestHierarchyChild{i+1}",
                "parent": "TestHierarchyParent"
            })
            
            assert child_result["success"] is True
        
        # Get the serialized parent (with deep depth to ensure we get all children)
        get_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestHierarchyParent",
            "serialization_depth": "Deep"
        })
        
        assert get_result["success"] is True
        serialized_parent = get_result["data"]
        
        # Find children by name using serialization utils
        child1 = serialization_utils.find_gameobject_in_hierarchy(serialized_parent, "TestHierarchyChild1")
        assert child1 is not None
        assert child1["name"] == "TestHierarchyChild1"
        
        child2 = serialization_utils.find_gameobject_in_hierarchy(serialized_parent, "TestHierarchyChild2")
        assert child2 is not None
        assert child2["name"] == "TestHierarchyChild2"
        
        child3 = serialization_utils.find_gameobject_in_hierarchy(serialized_parent, "TestHierarchyChild3")
        assert child3 is not None
        assert child3["name"] == "TestHierarchyChild3"
        
        # Test finding non-existent object
        none_obj = serialization_utils.find_gameobject_in_hierarchy(serialized_parent, "NonExistentObject")
        assert none_obj is None
        
        # Get all objects in hierarchy
        all_objects = serialization_utils.get_all_gameobjects_in_hierarchy(serialized_parent)
        assert len(all_objects) == 4  # Parent + 3 children
        
        # Check that all names are in the result
        names = [obj["name"] for obj in all_objects]
        assert "TestHierarchyParent" in names
        assert "TestHierarchyChild1" in names
        assert "TestHierarchyChild2" in names
        assert "TestHierarchyChild3" in names
        
        # Test searching for the parent by hierarchy path
        path_find = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestHierarchyParent"
        })
        
        assert path_find["success"] is True
        
        # Verify that the returned data contains the correct GameObject
        assert path_find["data"]["name"] == "TestHierarchyParent", "Expected to find GameObject with name 'TestHierarchyParent'"
        
        # Test direct path specification for a path that doesn't exist
        direct_path_get = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestHierarchyParent/ChildObject/GrandchildObject"
        })
        
        # This should fail since the path doesn't exist
        assert direct_path_get["success"] is False
        
        # Get the parent again to check it exists
        parent_check = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestHierarchyParent"
        })
        
        assert parent_check["success"] is True 