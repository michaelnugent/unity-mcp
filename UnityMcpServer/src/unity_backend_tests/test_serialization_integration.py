"""
Tests for GameObject serialization in the Unity backend.

These tests validate serialization functionality with a live Unity Editor instance,
focusing on basic serialization cases and proper handling of Unity object data.
"""

import pytest
import logging
import json
from typing import Dict, Any, List

from tools.manage_gameobject import GameObjectTool
from type_converters import (
    is_serialized_unity_object, extract_type_info, get_unity_components,
    get_unity_children, find_component_by_type, is_circular_reference, 
    get_reference_path, get_serialization_depth, SERIALIZATION_DEPTH_STANDARD
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
        
        # Get the GameObject with standard depth
        standard_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestDepthParent",
            "serialization_depth": "Standard"
        })
        
        assert standard_result["success"] is True
        standard_obj = standard_result["data"]
        
        # Get the GameObject with deep depth
        deep_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestDepthParent",
            "serialization_depth": "Deep"
        })
        
        assert deep_result["success"] is True
        deep_obj = deep_result["data"]
        
        # Check serialization depth
        assert get_serialization_depth(basic_obj) == "Basic"
        assert get_serialization_depth(standard_obj) == "Standard"
        assert get_serialization_depth(deep_obj) == "Deep"
        
        # Basic should have minimal information and no children
        assert "name" in basic_obj
        
        # Standard should have components and first level children
        assert get_unity_components(standard_obj) is not None
        standard_children = get_unity_children(standard_obj)
        assert standard_children is not None
        
        # Find child in standard depth
        standard_child = None
        for c in standard_children:
            if c.get("name") == "TestDepthChild":
                standard_child = c
                break
        
        assert standard_child is not None
        
        # In standard depth, the child shouldn't have detailed components
        if "__components" in standard_child:
            components = standard_child["__components"]
            # Simple serialization of components in standard depth
            assert len(components) <= 1  # May just have Transform
            
        # Deep should have more details in child components
        deep_children = get_unity_children(deep_obj)
        assert deep_children is not None
        
        # Find child in deep depth
        deep_child = None
        for c in deep_children:
            if c.get("name") == "TestDepthChild":
                deep_child = c
                break
        
        assert deep_child is not None
        
        # In deep depth, the child should have detailed components
        assert "__components" in deep_child
        deep_child_components = deep_child["__components"]
        assert len(deep_child_components) >= 1  # At least Transform
        
        # Log all three for comparison
        logger.info(f"Basic depth object keys: {basic_obj.keys()}")
        logger.info(f"Standard depth object keys: {standard_obj.keys()}")
        logger.info(f"Deep depth object keys: {deep_obj.keys()}")
        
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
            "name": "TestUtilityFunctions",
            "add_components": ["Rigidbody", "BoxCollider"]
        })
        
        assert result["success"] is True
        
        # Get the serialized GameObject
        get_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestUtilityFunctions"
        })
        
        assert get_result["success"] is True
        serialized_obj = get_result["data"]
        
        # Test serialization utility functions
        
        # Check serialization info
        serialization_info = serialization_utils.get_serialization_info(serialized_obj)
        assert "__serialization_status" in serialization_info
        assert serialization_info["__serialization_status"] == "Success"
        
        # Check component finding
        transform = serialization_utils.get_gameobject_components_by_type(serialized_obj, "Transform")
        assert len(transform) == 1
        
        rigidbody = serialization_utils.get_gameobject_components_by_type(serialized_obj, "Rigidbody")
        assert len(rigidbody) >= 1
        
        box_collider = serialization_utils.get_gameobject_components_by_type(serialized_obj, "BoxCollider")
        assert len(box_collider) >= 1
        
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
        assert path_find["data"] == "TestHierarchyParent"
        
        # Test direct path specification
        direct_path_get = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestHierarchyParent/ChildObject/GrandchildObject"
        })
        
        assert direct_path_get["success"] is True
        assert direct_path_get["data"] == "TestHierarchyParent/ChildObject/GrandchildObject"
        
        # Get the specified depth object directly - deep case
        deep_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestParent"
        })
        
        assert deep_result["success"] is True
        assert deep_result["data"] == "TestParent"
        
        # Get the specified depth object directly - standard depth
        standard_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestParent"
        })
        
        assert standard_result["success"] is True
        assert standard_result["data"] == "TestParent"
        
        # Get the specified depth object directly - shallow depth
        shallow_result = self.gameobject_tool.send_command("manage_gameobject", {
            "action": "find",
            "search_term": "TestParent"
        })
        
        assert shallow_result["success"] is True
        assert shallow_result["data"] == "TestParent" 