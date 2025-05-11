"""
Unity serialization utilities for working with enhanced serialized Unity objects.

This module provides helper functions for working with the enhanced serialization 
format used by the Unity MCP Bridge. These utilities help extract data, traverse
object hierarchies, and work with the various metadata included in serialized objects.
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Set, Iterator, TypeVar
import copy
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

# Type alias for serialized objects
SerializedObject = Dict[str, Any]
T = TypeVar('T')

def get_serialization_info(obj: SerializedObject) -> Dict[str, Any]:
    """Get all serialization metadata from a serialized object.
    
    Args:
        obj: The serialized object
        
    Returns:
        Dictionary with all serialization metadata
    """
    if not is_serialized_unity_object(obj):
        return {}
    
    metadata = {}
    metadata_keys = [
        SERIALIZATION_STATUS_KEY,
        SERIALIZATION_ERROR_KEY,
        SERIALIZATION_TYPE_KEY,
        SERIALIZATION_UNITY_TYPE_KEY,
        SERIALIZATION_PATH_KEY,
        SERIALIZATION_ID_KEY,
        SERIALIZATION_DEPTH_KEY,
        SERIALIZATION_FALLBACK_KEY
    ]
    
    for key in metadata_keys:
        if key in obj:
            metadata[key] = obj[key]
            
    return metadata

def is_successful_serialization(obj: SerializedObject) -> bool:
    """Check if an object was successfully serialized.
    
    Args:
        obj: The serialized object
        
    Returns:
        True if serialization was successful, False otherwise
    """
    if not is_serialized_unity_object(obj):
        return False
        
    status = obj.get(SERIALIZATION_STATUS_KEY, '').lower()
    return status == 'success'

def get_serialization_error(obj: SerializedObject) -> Optional[str]:
    """Get the serialization error message if present.
    
    Args:
        obj: The serialized object
        
    Returns:
        Error message string, or None if no error
    """
    if not is_serialized_unity_object(obj):
        return None
        
    status = obj.get(SERIALIZATION_STATUS_KEY, '').lower()
    if status != 'success':
        return obj.get(SERIALIZATION_ERROR_KEY)
        
    return None

def get_gameobject_components_by_type(gameobject: SerializedObject, component_type: str) -> List[SerializedObject]:
    """Get all components of a specific type from a GameObject.
    
    Args:
        gameobject: The serialized GameObject
        component_type: The type of components to find
        
    Returns:
        List of matching component objects
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Looking for components of type '{component_type}' in gameobject")
    
    if not is_serialized_unity_object(gameobject):
        logger.info("Object is not a serialized Unity object")
        return []
        
    components = get_unity_components(gameobject)
    logger.info(f"Found {len(components)} components in the gameobject")
    
    # Normalize component_type by removing namespace if present
    if '.' in component_type:
        short_type = component_type.split('.')[-1]
    else:
        short_type = component_type
    
    logger.info(f"Normalized type: short_type='{short_type}', full_type='{component_type}'")
    
    matching_components = []
    
    for i, component in enumerate(components):
        # Get the component type directly from __unity_type or __type
        unity_type = component.get(SERIALIZATION_UNITY_TYPE_KEY, '')
        type_name = component.get(SERIALIZATION_TYPE_KEY, '')
        
        logger.info(f"Examining component {i}: unity_type='{unity_type}', type='{type_name}'")
        
        # Extract short name from unity_type if it has a namespace
        if '.' in unity_type:
            unity_short_type = unity_type.split('.')[-1]
        else:
            unity_short_type = unity_type
            
        logger.info(f"Component {i} short type: '{unity_short_type}'")
        
        # Match by checking all possible forms of the type name
        if (unity_type == component_type or                 # Exact full type match
            unity_short_type == short_type or               # Short name match
            type_name == short_type or                      # Type name match
            unity_type.endswith(f".{short_type}")           # Namespace ending match
           ):
            logger.info(f"Component {i} MATCHED the search criteria")
            matching_components.append(component)
        else:
            logger.info(f"Component {i} did NOT match the search criteria")
            
    logger.info(f"Found {len(matching_components)} matching components")
    return matching_components

def find_gameobject_in_hierarchy(root: SerializedObject, name: str) -> Optional[SerializedObject]:
    """Find a GameObject by name in a hierarchy.
    
    Args:
        root: The root GameObject to search from
        name: The name of the GameObject to find
        
    Returns:
        The matching GameObject or None if not found
    """
    if not is_serialized_unity_object(root):
        return None
        
    # Check if this is the GameObject we're looking for
    root_name = root.get('name', '')
    if root_name == name:
        return root
        
    # Check all children recursively
    children = get_unity_children(root)
    for child in children:
        result = find_gameobject_in_hierarchy(child, name)
        if result:
            return result
            
    return None

def get_all_gameobjects_in_hierarchy(root: SerializedObject) -> List[SerializedObject]:
    """Get all GameObjects in a hierarchy including the root.
    
    Args:
        root: The root GameObject
        
    Returns:
        List of all GameObjects in the hierarchy
    """
    if not is_serialized_unity_object(root):
        return []
        
    result = [root]
    
    children = get_unity_children(root)
    for child in children:
        result.extend(get_all_gameobjects_in_hierarchy(child))
        
    return result

def extract_properties_from_serialized_object(obj: SerializedObject, 
                                             property_names: List[str]) -> Dict[str, Any]:
    """Extract specific properties from a serialized object.
    
    Args:
        obj: The serialized object
        property_names: List of property names to extract
        
    Returns:
        Dictionary mapping property names to their values
    """
    if not is_serialized_unity_object(obj):
        return {}
        
    result = {}
    
    for prop in property_names:
        value = get_serialized_value(obj, prop)
        if value is not None:
            result[prop] = value
            
    return result

def strip_serialization_metadata(obj: Any) -> Any:
    """Remove serialization metadata from an object recursively.
    
    This creates a clean version of the object without the serialization
    metadata, useful for presenting to users or for comparing objects.
    
    Args:
        obj: The object to clean
        
    Returns:
        A copy of the object with serialization metadata removed
    """
    if isinstance(obj, dict):
        result = {}
        
        # Skip serialization metadata keys
        metadata_keys = {
            SERIALIZATION_STATUS_KEY,
            SERIALIZATION_ERROR_KEY,
            SERIALIZATION_TYPE_KEY,
            SERIALIZATION_UNITY_TYPE_KEY,
            SERIALIZATION_PATH_KEY,
            SERIALIZATION_ID_KEY,
            SERIALIZATION_DEPTH_KEY,
            SERIALIZATION_FALLBACK_KEY,
            SERIALIZATION_CIRCULAR_REF_KEY,
            SERIALIZATION_REF_PATH_KEY
        }
        
        for key, value in obj.items():
            if key.startswith('__'):
                continue  # Skip all keys starting with __
                
            if key in metadata_keys:
                continue  # Skip known metadata keys
                
            # Recursively process value
            result[key] = strip_serialization_metadata(value)
            
        return result
    elif isinstance(obj, list):
        return [strip_serialization_metadata(item) for item in obj]
    else:
        return obj

def get_gameobject_path(gameobject: SerializedObject) -> str:
    """Get the full path of a GameObject in the hierarchy.
    
    Args:
        gameobject: The serialized GameObject
        
    Returns:
        The full path string (e.g., "Parent/Child/GrandChild")
    """
    if not is_serialized_unity_object(gameobject):
        return ""
        
    # Check if the path is already provided in the serialization
    if SERIALIZATION_PATH_KEY in gameobject:
        return gameobject[SERIALIZATION_PATH_KEY]
        
    # Otherwise try to construct it from the name
    return gameobject.get('name', '')

def resolve_circular_reference(obj: SerializedObject, 
                              root_object: Optional[SerializedObject] = None) -> Optional[SerializedObject]:
    """Resolve a circular reference object to its actual target object.
    
    Args:
        obj: The circular reference object
        root_object: The root object to search from (optional)
        
    Returns:
        The resolved object, or None if it cannot be resolved
    """
    if not is_circular_reference(obj) or not root_object:
        return None
        
    reference_path = get_reference_path(obj)
    if not reference_path:
        return None
        
    # Split the path and navigate through the hierarchy
    path_parts = reference_path.split('/')
    current = root_object
    
    # If the path has a single part and it matches the name of the root object,
    # we're directly referring to the root object itself
    if len(path_parts) == 1 and path_parts[0] == root_object.get('name'):
        return root_object
    
    for part in path_parts:
        if not part:
            continue
            
        # If this is a GameObject, look in its children
        if part in current:
            current = current[part]
        else:
            # Try to find among children by name
            children = get_unity_children(current)
            found = False
            for child in children:
                if child.get('name', '') == part:
                    current = child
                    found = True
                    break
                    
            if not found:
                return None  # Path cannot be resolved
                
    return current 