"""
Tests for the serialization utilities module.

These tests verify that the serialization utilities properly handle serialized
Unity objects with the enhanced serialization format.
"""

import pytest
import json
from typing import Dict, Any, List

import sys
import os

# Add the parent directory to sys.path to allow importing modules from there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import serialization_utils
from type_converters import (
    is_serialized_unity_object, extract_type_info, get_unity_components,
    get_unity_children, find_component_by_type, is_circular_reference, 
    get_reference_path, get_serialization_depth, get_serialized_value,
    SERIALIZATION_STATUS_KEY, SERIALIZATION_ERROR_KEY, SERIALIZATION_TYPE_KEY,
    SERIALIZATION_UNITY_TYPE_KEY, SERIALIZATION_PATH_KEY, SERIALIZATION_ID_KEY,
    SERIALIZATION_CIRCULAR_REF_KEY, SERIALIZATION_REF_PATH_KEY,
    SERIALIZATION_DEPTH_KEY, SERIALIZATION_PROPERTIES_KEY, SERIALIZATION_FALLBACK_KEY,
    SERIALIZATION_CHILDREN_KEY, SERIALIZATION_COMPONENTS_KEY,
    SERIALIZATION_DEPTH_BASIC, SERIALIZATION_DEPTH_STANDARD, SERIALIZATION_DEPTH_DEEP
)


# Sample serialized GameObject with the enhanced format
@pytest.fixture
def sample_gameobject():
    return {
        "__serialization_status": "Success",
        "__type": "GameObject",
        "__unity_type": "UnityEngine.GameObject",
        "__id": "12345",
        "__path": "Parent/Child",
        "name": "Child",
        "tag": "Player",
        "layer": 0,
        "activeSelf": True,
        "__components": [
            {
                "__type": "Component",
                "__unity_type": "UnityEngine.Transform",
                "__id": "12346",
                "position": {"x": 1.0, "y": 2.0, "z": 3.0},
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                "localScale": {"x": 1.0, "y": 1.0, "z": 1.0}
            },
            {
                "__type": "Component",
                "__unity_type": "UnityEngine.MeshRenderer",
                "__id": "12347",
                "enabled": True,
                "material": {
                    "__type": "Material",
                    "__unity_type": "UnityEngine.Material",
                    "__id": "12348",
                    "name": "Default Material"
                }
            }
        ],
        "__children": [
            {
                "__type": "GameObject",
                "__unity_type": "UnityEngine.GameObject",
                "__id": "12349",
                "__path": "Parent/Child/GrandChild",
                "name": "GrandChild",
                "tag": "Untagged",
                "layer": 0,
                "activeSelf": True,
                "__components": [
                    {
                        "__type": "Component",
                        "__unity_type": "UnityEngine.Transform",
                        "__id": "12350",
                        "position": {"x": 0.0, "y": 1.0, "z": 0.0},
                        "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0},
                        "localScale": {"x": 1.0, "y": 1.0, "z": 1.0}
                    }
                ],
                "__children": []
            }
        ]
    }

# Sample serialized GameObject with circular reference
@pytest.fixture
def circular_reference_gameobject():
    return {
        "__serialization_status": "Success",
        "__type": "GameObject",
        "__unity_type": "UnityEngine.GameObject",
        "__id": "12345",
        "name": "Parent",
        "tag": "Untagged",
        "layer": 0,
        "__components": [
            {
                "__type": "Component",
                "__unity_type": "UnityEngine.Transform",
                "__id": "12346",
                "position": {"x": 0.0, "y": 0.0, "z": 0.0}
            }
        ],
        "__children": [
            {
                "__type": "GameObject",
                "__unity_type": "UnityEngine.GameObject",
                "__id": "12347",
                "name": "Child",
                "__components": [
                    {
                        "__type": "Component",
                        "__unity_type": "UnityEngine.Transform",
                        "__id": "12348",
                        "position": {"x": 1.0, "y": 0.0, "z": 0.0},
                        "parent": {
                            "__circular_reference": True,
                            "__reference_path": "Parent",
                            "__type": "GameObject",
                            "__unity_type": "UnityEngine.GameObject",
                            "__id": "12345"
                        }
                    }
                ]
            }
        ]
    }

# Tests for type_converters functions
def test_is_serialized_unity_object(sample_gameobject):
    assert is_serialized_unity_object(sample_gameobject) == True
    assert is_serialized_unity_object({"name": "Not a Unity object"}) == False
    assert is_serialized_unity_object(None) == False
    assert is_serialized_unity_object(42) == False

def test_extract_type_info(sample_gameobject):
    type_info = extract_type_info(sample_gameobject)
    assert type_info is not None
    assert type_info["type"] == "GameObject"
    assert type_info["unity_type"] == "UnityEngine.GameObject"
    assert type_info["id"] == "12345"
    assert type_info["path"] == "Parent/Child"

def test_get_unity_components(sample_gameobject):
    components = get_unity_components(sample_gameobject)
    assert len(components) == 2
    assert components[0]["__unity_type"] == "UnityEngine.Transform"
    assert components[1]["__unity_type"] == "UnityEngine.MeshRenderer"

def test_get_unity_children(sample_gameobject):
    children = get_unity_children(sample_gameobject)
    assert len(children) == 1
    assert children[0]["name"] == "GrandChild"
    assert children[0]["__path"] == "Parent/Child/GrandChild"

def test_find_component_by_type(sample_gameobject):
    transform = find_component_by_type(sample_gameobject, "Transform")
    assert transform is not None
    assert transform["__unity_type"] == "UnityEngine.Transform"
    
    mesh_renderer = find_component_by_type(sample_gameobject, "MeshRenderer")
    assert mesh_renderer is not None
    assert mesh_renderer["__unity_type"] == "UnityEngine.MeshRenderer"
    
    # Test with full type name including namespace
    transform_full = find_component_by_type(sample_gameobject, "UnityEngine.Transform")
    assert transform_full is not None
    assert transform_full["__unity_type"] == "UnityEngine.Transform"
    
    # Test non-existent component
    none_component = find_component_by_type(sample_gameobject, "NonExistentComponent")
    assert none_component is None

def test_is_circular_reference(circular_reference_gameobject):
    # Get the parent reference from the child's transform
    parent_ref = circular_reference_gameobject["__children"][0]["__components"][0]["parent"]
    
    assert is_circular_reference(parent_ref) == True
    assert is_circular_reference(circular_reference_gameobject) == False
    assert is_circular_reference({"name": "Regular object"}) == False

def test_get_reference_path(circular_reference_gameobject):
    # Get the parent reference from the child's transform
    parent_ref = circular_reference_gameobject["__children"][0]["__components"][0]["parent"]
    
    assert get_reference_path(parent_ref) == "Parent"
    assert get_reference_path(circular_reference_gameobject) is None
    assert get_reference_path({"name": "Regular object"}) is None

# Tests for serialization_utils functions
def test_get_serialization_info(sample_gameobject):
    info = serialization_utils.get_serialization_info(sample_gameobject)
    assert info[SERIALIZATION_STATUS_KEY] == "Success"
    assert info[SERIALIZATION_TYPE_KEY] == "GameObject"
    assert info[SERIALIZATION_UNITY_TYPE_KEY] == "UnityEngine.GameObject"
    assert info[SERIALIZATION_ID_KEY] == "12345"
    assert info[SERIALIZATION_PATH_KEY] == "Parent/Child"

def test_is_successful_serialization(sample_gameobject):
    assert serialization_utils.is_successful_serialization(sample_gameobject) == True
    
    # Test with failed serialization
    failed_obj = {
        "__serialization_status": "Failed",
        "__serialization_error": "Test error",
        "__type": "GameObject"
    }
    assert serialization_utils.is_successful_serialization(failed_obj) == False

def test_get_serialization_error():
    # Test with failed serialization
    failed_obj = {
        "__serialization_status": "Failed",
        "__serialization_error": "Test error",
        "__type": "GameObject"
    }
    assert serialization_utils.get_serialization_error(failed_obj) == "Test error"
    
    # Test with successful serialization
    success_obj = {
        "__serialization_status": "Success",
        "__type": "GameObject"
    }
    assert serialization_utils.get_serialization_error(success_obj) is None

def test_get_gameobject_components_by_type(sample_gameobject):
    transforms = serialization_utils.get_gameobject_components_by_type(sample_gameobject, "Transform")
    assert len(transforms) == 1
    assert transforms[0]["__unity_type"] == "UnityEngine.Transform"
    
    renderers = serialization_utils.get_gameobject_components_by_type(sample_gameobject, "MeshRenderer")
    assert len(renderers) == 1
    assert renderers[0]["__unity_type"] == "UnityEngine.MeshRenderer"
    
    # Test with namespace
    transforms_ns = serialization_utils.get_gameobject_components_by_type(sample_gameobject, "UnityEngine.Transform")
    assert len(transforms_ns) == 1
    
    # Test non-existent component
    none_components = serialization_utils.get_gameobject_components_by_type(sample_gameobject, "NonExistentComponent")
    assert len(none_components) == 0

def test_find_gameobject_in_hierarchy(sample_gameobject):
    # Find the root object
    child = serialization_utils.find_gameobject_in_hierarchy(sample_gameobject, "Child")
    assert child is not None
    assert child["name"] == "Child"
    
    # Find a child object
    grandchild = serialization_utils.find_gameobject_in_hierarchy(sample_gameobject, "GrandChild")
    assert grandchild is not None
    assert grandchild["name"] == "GrandChild"
    
    # Test non-existent object
    none_obj = serialization_utils.find_gameobject_in_hierarchy(sample_gameobject, "NonExistentObject")
    assert none_obj is None

def test_get_all_gameobjects_in_hierarchy(sample_gameobject):
    all_objs = serialization_utils.get_all_gameobjects_in_hierarchy(sample_gameobject)
    assert len(all_objs) == 2  # Child and GrandChild
    
    # Check the names
    names = [obj["name"] for obj in all_objs]
    assert "Child" in names
    assert "GrandChild" in names

def test_extract_properties_from_serialized_object(sample_gameobject):
    # Extract top-level properties
    props = serialization_utils.extract_properties_from_serialized_object(
        sample_gameobject, ["name", "tag", "layer"]
    )
    assert props["name"] == "Child"
    assert props["tag"] == "Player"
    assert props["layer"] == 0
    
    # Test with non-existent property
    props_with_missing = serialization_utils.extract_properties_from_serialized_object(
        sample_gameobject, ["name", "nonExistentProp"]
    )
    assert "name" in props_with_missing
    assert "nonExistentProp" not in props_with_missing

def test_strip_serialization_metadata(sample_gameobject):
    cleaned = serialization_utils.strip_serialization_metadata(sample_gameobject)
    
    # Check that metadata is removed
    assert "__serialization_status" not in cleaned
    assert "__type" not in cleaned
    assert "__unity_type" not in cleaned
    assert "__id" not in cleaned
    assert "__path" not in cleaned
    
    # Check that regular properties remain
    assert "name" in cleaned
    assert "tag" in cleaned
    assert "layer" in cleaned
    
    # Check that children and components are preserved but also cleaned
    assert "__children" not in cleaned
    assert "__components" not in cleaned
    
    # The children and components should be available without the metadata prefix
    if "children" in cleaned:
        child = cleaned["children"][0]
        assert "__type" not in child
    
    if "components" in cleaned:
        component = cleaned["components"][0]
        assert "__type" not in component

def test_get_gameobject_path(sample_gameobject):
    path = serialization_utils.get_gameobject_path(sample_gameobject)
    assert path == "Parent/Child"
    
    # Test with object that doesn't have __path
    no_path_obj = {
        "__type": "GameObject",
        "name": "NoPathObject"
    }
    path2 = serialization_utils.get_gameobject_path(no_path_obj)
    assert path2 == "NoPathObject"

def test_resolve_circular_reference(circular_reference_gameobject):
    # Get the parent reference from the child's transform
    parent_ref = circular_reference_gameobject["__children"][0]["__components"][0]["parent"]
    
    # Resolve it back to the original object
    resolved = serialization_utils.resolve_circular_reference(
        parent_ref, circular_reference_gameobject
    )
    
    assert resolved is not None
    assert resolved["__id"] == "12345"
    assert resolved["name"] == "Parent"
    
    # Test with non-circular reference
    non_circ = {"name": "Regular object"}
    assert serialization_utils.resolve_circular_reference(non_circ, circular_reference_gameobject) is None
    
    # Test with invalid path
    invalid_ref = {
        "__circular_reference": True,
        "__reference_path": "InvalidPath",
    }
    assert serialization_utils.resolve_circular_reference(invalid_ref, circular_reference_gameobject) is None 