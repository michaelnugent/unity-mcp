"""
Unity Type Converters for MCP parameter validation and conversion.

This module provides conversion functions for common Unity types to ensure
proper serialization and deserialization between Python and Unity C#.
Each converter handles validation and standardizes the format for the Unity bridge.
"""

from typing import Any, Dict, List, Tuple, Union, Optional
import math
from exceptions import ParameterValidationError

# Type aliases for clarity
Vector2Type = Union[Dict[str, float], List[float], Tuple[float, float]]
Vector3Type = Union[Dict[str, float], List[float], Tuple[float, float, float]]
Vector4Type = Union[Dict[str, float], List[float], Tuple[float, float, float, float]]
QuaternionType = Union[Dict[str, float], List[float], Tuple[float, float, float, float]]
ColorType = Union[Dict[str, float], List[float], Tuple[float, float, float, float]]
RectType = Union[Dict[str, float], List[float], Tuple[float, float, float, float]]
BoundsType = Union[Dict[str, Vector3Type], Dict[str, Any]]


def convert_vector2(value: Vector2Type, param_name: str = "Vector2") -> Dict[str, float]:
    """Convert and validate a Vector2 parameter.
    
    Args:
        value: The Vector2 value as dict, list, or tuple
        param_name: Name of the parameter for error reporting
        
    Returns:
        Standardized dictionary format: {"x": float, "y": float}
        
    Raises:
        ParameterValidationError: If validation fails
    """
    if value is None:
        raise ParameterValidationError(f"{param_name} cannot be None")
        
    error_prefix = f"Invalid {param_name} value"
    
    # Convert list/tuple to dict
    if isinstance(value, (list, tuple)):
        if len(value) != 2:
            raise ParameterValidationError(
                f"{error_prefix}: Vector2 must have exactly 2 components, got {len(value)}"
            )
        
        try:
            return {"x": float(value[0]), "y": float(value[1])}
        except (ValueError, TypeError):
            raise ParameterValidationError(
                f"{error_prefix}: Vector2 components must be convertible to float"
            )
                
    # Validate and standardize dict format
    elif isinstance(value, dict):
        required_keys = {"x", "y"}
        missing_keys = required_keys - set(value.keys())
        if missing_keys:
            raise ParameterValidationError(
                f"{error_prefix}: Missing Vector2 components: {', '.join(missing_keys)}"
            )
            
        try:
            return {"x": float(value["x"]), "y": float(value["y"])}
        except (ValueError, TypeError):
            raise ParameterValidationError(
                f"{error_prefix}: Vector2 components must be convertible to float"
            )
    else:
        raise ParameterValidationError(
            f"{error_prefix}: Expected list, tuple or dict, got {type(value).__name__}"
        )


def convert_vector3(value: Vector3Type, param_name: str = "Vector3") -> Dict[str, float]:
    """Convert and validate a Vector3 parameter.
    
    Args:
        value: The Vector3 value as dict, list, or tuple
        param_name: Name of the parameter for error reporting
        
    Returns:
        Standardized dictionary format: {"x": float, "y": float, "z": float}
        
    Raises:
        ParameterValidationError: If validation fails
    """
    if value is None:
        raise ParameterValidationError(f"{param_name} cannot be None")
        
    error_prefix = f"Invalid {param_name} value"
    
    # Convert list/tuple to dict
    if isinstance(value, (list, tuple)):
        if len(value) != 3:
            raise ParameterValidationError(
                f"{error_prefix}: Vector3 must have exactly 3 components, got {len(value)}"
            )
        
        try:
            return {"x": float(value[0]), "y": float(value[1]), "z": float(value[2])}
        except (ValueError, TypeError):
            raise ParameterValidationError(
                f"{error_prefix}: Vector3 components must be convertible to float"
            )
                
    # Validate and standardize dict format
    elif isinstance(value, dict):
        required_keys = {"x", "y", "z"}
        missing_keys = required_keys - set(value.keys())
        if missing_keys:
            raise ParameterValidationError(
                f"{error_prefix}: Missing Vector3 components: {', '.join(missing_keys)}"
            )
            
        try:
            return {"x": float(value["x"]), "y": float(value["y"]), "z": float(value["z"])}
        except (ValueError, TypeError):
            raise ParameterValidationError(
                f"{error_prefix}: Vector3 components must be convertible to float"
            )
    else:
        raise ParameterValidationError(
            f"{error_prefix}: Expected list, tuple or dict, got {type(value).__name__}"
        )


def convert_quaternion(value: QuaternionType, param_name: str = "Quaternion") -> Dict[str, float]:
    """Convert and validate a Quaternion parameter.
    
    Args:
        value: The Quaternion value as dict, list, or tuple
        param_name: Name of the parameter for error reporting
        
    Returns:
        Standardized dictionary format: {"x": float, "y": float, "z": float, "w": float}
        
    Raises:
        ParameterValidationError: If validation fails
    """
    if value is None:
        raise ParameterValidationError(f"{param_name} cannot be None")
        
    error_prefix = f"Invalid {param_name} value"
    
    # Convert list/tuple to dict
    if isinstance(value, (list, tuple)):
        if len(value) != 4:
            raise ParameterValidationError(
                f"{error_prefix}: Quaternion must have exactly 4 components, got {len(value)}"
            )
        
        try:
            return {"x": float(value[0]), "y": float(value[1]), 
                    "z": float(value[2]), "w": float(value[3])}
        except (ValueError, TypeError):
            raise ParameterValidationError(
                f"{error_prefix}: Quaternion components must be convertible to float"
            )
                
    # Validate and standardize dict format
    elif isinstance(value, dict):
        required_keys = {"x", "y", "z", "w"}
        missing_keys = required_keys - set(value.keys())
        if missing_keys:
            raise ParameterValidationError(
                f"{error_prefix}: Missing Quaternion components: {', '.join(missing_keys)}"
            )
            
        try:
            return {"x": float(value["x"]), "y": float(value["y"]), 
                    "z": float(value["z"]), "w": float(value["w"])}
        except (ValueError, TypeError):
            raise ParameterValidationError(
                f"{error_prefix}: Quaternion components must be convertible to float"
            )
    else:
        raise ParameterValidationError(
            f"{error_prefix}: Expected list, tuple or dict, got {type(value).__name__}"
        )


def euler_to_quaternion(euler: Vector3Type) -> Dict[str, float]:
    """Convert Euler angles (in degrees) to a Quaternion.
    
    Args:
        euler: Euler angles in degrees as Vector3
        
    Returns:
        Quaternion as {"x", "y", "z", "w"}
    """
    # First convert the euler input to a standard format
    euler_dict = convert_vector3(euler, "EulerAngles")
    
    # Convert degrees to radians
    x = math.radians(euler_dict["x"])
    y = math.radians(euler_dict["y"])
    z = math.radians(euler_dict["z"])
    
    # Calculate quaternion components
    c1 = math.cos(x / 2)
    s1 = math.sin(x / 2)
    c2 = math.cos(y / 2)
    s2 = math.sin(y / 2)
    c3 = math.cos(z / 2)
    s3 = math.sin(z / 2)
    
    # Multiply the matrices
    qx = s1 * c2 * c3 + c1 * s2 * s3
    qy = c1 * s2 * c3 - s1 * c2 * s3
    qz = c1 * c2 * s3 + s1 * s2 * c3
    qw = c1 * c2 * c3 - s1 * s2 * s3
    
    return {"x": qx, "y": qy, "z": qz, "w": qw}


def convert_color(value: ColorType, param_name: str = "Color") -> Dict[str, float]:
    """Convert and validate a Color parameter.
    
    Args:
        value: The Color value as dict, list, or tuple (RGBA format)
        param_name: Name of the parameter for error reporting
        
    Returns:
        Standardized dictionary format: {"r": float, "g": float, "b": float, "a": float}
        
    Raises:
        ParameterValidationError: If validation fails
    """
    if value is None:
        raise ParameterValidationError(f"{param_name} cannot be None")
        
    error_prefix = f"Invalid {param_name} value"
    
    # Convert list/tuple to dict
    if isinstance(value, (list, tuple)):
        # Allow RGB (3 components) or RGBA (4 components)
        if len(value) < 3 or len(value) > 4:
            raise ParameterValidationError(
                f"{error_prefix}: Color must have 3 or 4 components, got {len(value)}"
            )
        
        try:
            result = {
                "r": float(value[0]), 
                "g": float(value[1]), 
                "b": float(value[2]),
                "a": float(value[3]) if len(value) > 3 else 1.0
            }
            # Validate ranges (0-1)
            for component, val in result.items():
                if val < 0 or val > 1:
                    raise ParameterValidationError(
                        f"{error_prefix}: Color {component} component must be between 0 and 1"
                    )
            return result
        except (ValueError, TypeError):
            raise ParameterValidationError(
                f"{error_prefix}: Color components must be convertible to float"
            )
                
    # Validate and standardize dict format
    elif isinstance(value, dict):
        # Check if using color formats
        if set(value.keys()) == {"r", "g", "b"} or set(value.keys()) == {"r", "g", "b", "a"}:
            # RGBA format
            try:
                result = {
                    "r": float(value["r"]),
                    "g": float(value["g"]),
                    "b": float(value["b"]),
                    "a": float(value["a"]) if "a" in value else 1.0
                }
                # Validate ranges (0-1)
                for component, val in result.items():
                    if val < 0 or val > 1:
                        raise ParameterValidationError(
                            f"{error_prefix}: Color {component} component must be between 0 and 1"
                        )
                return result
            except (ValueError, TypeError):
                raise ParameterValidationError(
                    f"{error_prefix}: Color components must be convertible to float"
                )
        else:
            raise ParameterValidationError(
                f"{error_prefix}: Color dict must have keys 'r', 'g', 'b', optional 'a'"
            )
    else:
        raise ParameterValidationError(
            f"{error_prefix}: Expected list, tuple or dict, got {type(value).__name__}"
        )


def convert_rect(value: RectType, param_name: str = "Rect") -> Dict[str, float]:
    """Convert and validate a Rect parameter.
    
    Args:
        value: The Rect value as dict, list, or tuple
        param_name: Name of the parameter for error reporting
        
    Returns:
        Standardized dictionary format: {"x": float, "y": float, "width": float, "height": float}
        
    Raises:
        ParameterValidationError: If validation fails
    """
    if value is None:
        raise ParameterValidationError(f"{param_name} cannot be None")
        
    error_prefix = f"Invalid {param_name} value"
    
    # Convert list/tuple to dict
    if isinstance(value, (list, tuple)):
        if len(value) != 4:
            raise ParameterValidationError(
                f"{error_prefix}: Rect must have exactly 4 components, got {len(value)}"
            )
        
        try:
            return {"x": float(value[0]), "y": float(value[1]), 
                    "width": float(value[2]), "height": float(value[3])}
        except (ValueError, TypeError):
            raise ParameterValidationError(
                f"{error_prefix}: Rect components must be convertible to float"
            )
                
    # Validate and standardize dict format
    elif isinstance(value, dict):
        required_keys = {"x", "y", "width", "height"}
        missing_keys = required_keys - set(value.keys())
        if missing_keys:
            raise ParameterValidationError(
                f"{error_prefix}: Missing Rect components: {', '.join(missing_keys)}"
            )
            
        try:
            return {"x": float(value["x"]), "y": float(value["y"]), 
                    "width": float(value["width"]), "height": float(value["height"])}
        except (ValueError, TypeError):
            raise ParameterValidationError(
                f"{error_prefix}: Rect components must be convertible to float"
            )
    else:
        raise ParameterValidationError(
            f"{error_prefix}: Expected list, tuple or dict, got {type(value).__name__}"
        )


def convert_bounds(value: BoundsType, param_name: str = "Bounds") -> Dict[str, Dict[str, float]]:
    """Convert and validate a Bounds parameter.
    
    Args:
        value: The Bounds value as dict with center and size
        param_name: Name of the parameter for error reporting
        
    Returns:
        Standardized dictionary format: {"center": Vector3Dict, "size": Vector3Dict}
        
    Raises:
        ParameterValidationError: If validation fails
    """
    if value is None:
        raise ParameterValidationError(f"{param_name} cannot be None")
        
    error_prefix = f"Invalid {param_name} value"
    
    if not isinstance(value, dict):
        raise ParameterValidationError(
            f"{error_prefix}: Expected dict, got {type(value).__name__}"
        )
    
    required_keys = {"center", "size"}
    missing_keys = required_keys - set(value.keys())
    if missing_keys:
        raise ParameterValidationError(
            f"{error_prefix}: Missing Bounds components: {', '.join(missing_keys)}"
        )
    
    # Convert and validate the center and size as Vector3
    try:
        center = convert_vector3(value["center"], f"{param_name}.center")
        size = convert_vector3(value["size"], f"{param_name}.size")
        return {"center": center, "size": size}
    except ParameterValidationError as e:
        raise e
    except Exception as e:
        raise ParameterValidationError(
            f"{error_prefix}: {str(e)}"
        )

# Enhanced serialization support
def get_serialized_value(obj, property_path=None):
    """
    Extract a value from a serialized Unity object by property path.
    
    Args:
        obj: The serialized Unity object (dictionary) containing serialization metadata
        property_path: Property path in dot notation (e.g., "transform.position.x")
        
    Returns:
        The value at the given property path, or the object itself if no path is specified
    
    Raises:
        KeyError: If the property path doesn't exist in the object
    """
    if obj is None:
        return None
        
    # If no property path is specified, return the original object data
    if not property_path:
        # Return the data property if this is a SerializationResult
        return obj.get('Data', obj)
        
    # Handle property path navigation
    parts = property_path.split('.')
    current = obj
    
    # If this is a serialization result, start with Data property
    if isinstance(current, dict) and 'Data' in current:
        current = current['Data']
        
    # Navigate through the property path
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise KeyError(f"Property '{part}' not found in path '{property_path}'")
            
    return current

def is_serialized_unity_object(obj):
    """
    Check if an object is a serialized Unity object with enhanced serialization metadata.
    
    Args:
        obj: The object to check
        
    Returns:
        True if the object is a serialized Unity object, False otherwise
    """
    if not isinstance(obj, dict):
        return False
        
    # Check for serialization metadata properties
    serialization_props = ['__serialization_status', '__serialization_depth', 'ObjectTypeName']
    
    # Either a direct object with metadata or a SerializationResult
    if any(prop in obj for prop in serialization_props):
        return True
        
    # Check if it's a serialization result (Data property with metadata inside)
    if 'Data' in obj and isinstance(obj['Data'], dict):
        return any(prop in obj['Data'] for prop in serialization_props)
        
    return False

def extract_type_info(obj):
    """
    Extract type information from a serialized Unity object.
    
    Args:
        obj: The serialized Unity object
        
    Returns:
        A tuple of (type_name, instance_id) where type_name is the full name of the object's type
        and instance_id is the Unity instance ID if available, or None
    """
    if not is_serialized_unity_object(obj):
        return (None, None)
        
    # Handle both direct objects and SerializationResult objects
    data = obj.get('Data', obj)
    
    type_name = data.get('ObjectTypeName')
    instance_id = data.get('InstanceID')
    
    return (type_name, instance_id)

def get_unity_components(serialized_gameobject):
    """
    Extract components from a serialized GameObject.
    
    Args:
        serialized_gameobject: A serialized GameObject
        
    Returns:
        A list of serialized component dictionaries, or an empty list if no components are found
    """
    if not is_serialized_unity_object(serialized_gameobject):
        return []
        
    # Handle both direct objects and SerializationResult objects
    data = serialized_gameobject.get('Data', serialized_gameobject)
    
    # Try to get components list
    components = data.get('components', [])
    
    # If components is a list, return it
    if isinstance(components, list):
        return components
        
    return []
    
def get_unity_children(serialized_gameobject):
    """
    Extract children from a serialized GameObject.
    
    Args:
        serialized_gameobject: A serialized GameObject
        
    Returns:
        A list of serialized GameObject dictionaries representing the children, 
        or an empty list if no children are found
    """
    if not is_serialized_unity_object(serialized_gameobject):
        return []
        
    # Handle both direct objects and SerializationResult objects
    data = serialized_gameobject.get('Data', serialized_gameobject)
    
    # Try to get children list
    children = data.get('children', [])
    
    # If children is a list, return it
    if isinstance(children, list):
        return children
        
    return []

def find_component_by_type(serialized_gameobject, component_type):
    """
    Find a component by type in a serialized GameObject.
    
    Args:
        serialized_gameobject: A serialized GameObject
        component_type: The name of the component type to find
        
    Returns:
        The serialized component dictionary if found, or None if not found
    """
    components = get_unity_components(serialized_gameobject)
    
    for component in components:
        component_data = component.get('Data', component)
        type_name = component_data.get('ObjectTypeName', '')
        
        # Check if the component type matches (case-insensitive)
        if type_name.lower() == component_type.lower():
            return component
        
        # Also check for short names without namespace
        short_name = type_name.split('.')[-1] if '.' in type_name else type_name
        if short_name.lower() == component_type.lower():
            return component
            
    return None

def is_circular_reference(obj):
    """
    Check if an object is a circular reference.
    
    Args:
        obj: The object to check
        
    Returns:
        True if the object is a circular reference, False otherwise
    """
    if not isinstance(obj, dict):
        return False
        
    # Check for circular reference flag
    circular_ref = obj.get('__circular_reference', False)
    return bool(circular_ref)

def get_reference_path(obj):
    """
    Get the reference path for a circular reference.
    
    Args:
        obj: The circular reference object
        
    Returns:
        The reference path if the object is a circular reference, None otherwise
    """
    if not is_circular_reference(obj):
        return None
        
    return obj.get('__reference_path') 