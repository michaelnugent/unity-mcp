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