"""
Shared validation utilities for Unity MCP tools.

This module provides validation functions that can be used across different tool modules
to ensure consistent parameter validation and error reporting.

It also includes functions for validating serialized Unity objects with the enhanced
serialization format, including validation of GameObject, Component, and Transform
representations.
"""

from typing import Any, Dict, List, Tuple, Union, Optional
from unity_connection import ParameterValidationError
from type_converters import (
    is_serialized_unity_object, extract_type_info, is_circular_reference,
    get_unity_components, get_unity_children, find_component_by_type,
    SERIALIZATION_TYPE_KEY, SERIALIZATION_UNITY_TYPE_KEY, SERIALIZATION_STATUS_KEY,
    SERIALIZATION_PATH_KEY, SERIALIZATION_ID_KEY
)

def validate_vector3(value: Any, param_name: str) -> None:
    """Validate a Vector3 parameter (position, rotation, scale).
    
    Args:
        value: The value to validate (list, tuple or dict)
        param_name: Name of the parameter for error reporting
        
    Raises:
        ParameterValidationError: If validation fails
    """
    if value is None:
        return  # Optional parameter
        
    error_prefix = f"Invalid {param_name} value"
    
    # Check if value is a list or array-like
    if isinstance(value, (list, tuple)):
        if len(value) != 3:
            raise ParameterValidationError(
                f"{error_prefix}: Vector3 must have exactly 3 components, got {len(value)}"
            )
        
        # Check if all elements are numbers
        for i, component in enumerate(value):
            if not isinstance(component, (int, float)):
                raise ParameterValidationError(
                    f"{error_prefix}: Component {i} must be a number, got {type(component).__name__}"
                )
                
    # Check if value is a dictionary with x,y,z keys
    elif isinstance(value, dict):
        required_keys = {"x", "y", "z"}
        missing_keys = required_keys - set(value.keys())
        if missing_keys:
            raise ParameterValidationError(
                f"{error_prefix}: Missing Vector3 components: {', '.join(missing_keys)}"
            )
            
        # Check if values are numbers
        for key in required_keys:
            if not isinstance(value[key], (int, float)):
                raise ParameterValidationError(
                    f"{error_prefix}: Component {key} must be a number, got {type(value[key]).__name__}"
                )
    else:
        raise ParameterValidationError(
            f"{error_prefix}: Expected list, tuple or dict, got {type(value).__name__}"
        )

def validate_required_param(params: Dict[str, Any], param_name: str, action: str, tool_name: str) -> None:
    """Validate that a required parameter is present.
    
    Args:
        params: Dictionary of parameters to check
        param_name: Name of the required parameter
        action: Current action being performed
        tool_name: Name of the tool for error reporting
        
    Raises:
        ParameterValidationError: If the required parameter is missing
    """
    if param_name not in params:
        raise ParameterValidationError(
            f"{tool_name} '{action}' action requires '{param_name}' parameter"
        )

def validate_param_type(param: Any, param_name: str, expected_type: Union[type, Tuple[type, ...]], 
                       action: str, tool_name: str) -> None:
    """Validate that a parameter is of the expected type.
    
    Args:
        param: Parameter value to check
        param_name: Name of the parameter for error reporting
        expected_type: Expected type or tuple of allowed types
        action: Current action being performed
        tool_name: Name of the tool for error reporting
        
    Raises:
        ParameterValidationError: If the parameter is not of the expected type
    """
    if param is not None and not isinstance(param, expected_type):
        type_names = [t.__name__ for t in expected_type] if isinstance(expected_type, tuple) else [expected_type.__name__]
        expected_type_str = ", ".join(type_names)
        
        raise ParameterValidationError(
            f"{tool_name} '{action}' parameter '{param_name}' must be of type {expected_type_str}, "
            f"got {type(param).__name__}"
        )

def validate_serialized_gameobject(value: Any, param_name: str) -> None:
    """Validate that a value is a serialized GameObject.
    
    Args:
        value: The value to validate
        param_name: Name of the parameter for error reporting
        
    Raises:
        ParameterValidationError: If validation fails
    """
    if value is None:
        return  # Optional parameter
        
    error_prefix = f"Invalid {param_name} value"
    
    if not isinstance(value, dict):
        raise ParameterValidationError(
            f"{error_prefix}: Expected GameObject object, got {type(value).__name__}"
        )
        
    if not is_serialized_unity_object(value):
        raise ParameterValidationError(
            f"{error_prefix}: Value is not a serialized Unity object"
        )
    
    # Check for expected GameObject properties
    type_info = extract_type_info(value)
    if not type_info:
        raise ParameterValidationError(
            f"{error_prefix}: Missing type information for GameObject"
        )
        
    # Check if it's a circular reference (which is valid)
    if is_circular_reference(value):
        return
    
    # For non-circular references, validate essential properties
    unity_type = type_info.get('unity_type', '')
    if not unity_type or not (
        unity_type.endswith('GameObject') or 
        unity_type == 'GameObject' or
        'GameObject' in unity_type
    ):
        raise ParameterValidationError(
            f"{error_prefix}: Object is not a GameObject, got {unity_type}"
        )

def validate_serialized_component(value: Any, param_name: str, required_type: Optional[str] = None) -> None:
    """Validate that a value is a serialized Component of a specific type.
    
    Args:
        value: The value to validate
        param_name: Name of the parameter for error reporting
        required_type: If specified, validate that the component is of this type
        
    Raises:
        ParameterValidationError: If validation fails
    """
    if value is None:
        return  # Optional parameter
        
    error_prefix = f"Invalid {param_name} value"
    
    if not isinstance(value, dict):
        raise ParameterValidationError(
            f"{error_prefix}: Expected Component object, got {type(value).__name__}"
        )
        
    if not is_serialized_unity_object(value):
        raise ParameterValidationError(
            f"{error_prefix}: Value is not a serialized Unity object"
        )
    
    # Check for expected Component properties
    type_info = extract_type_info(value)
    if not type_info:
        raise ParameterValidationError(
            f"{error_prefix}: Missing type information for Component"
        )
        
    # Check if it's a circular reference (which is valid)
    if is_circular_reference(value):
        return
    
    # For non-circular references, validate essential properties
    unity_type = type_info.get('unity_type', '')
    if not unity_type:
        raise ParameterValidationError(
            f"{error_prefix}: Missing component type information"
        )
        
    # Validate against required_type if specified
    if required_type and not (
        unity_type.endswith(required_type) or 
        unity_type == required_type or
        required_type in unity_type
    ):
        raise ParameterValidationError(
            f"{error_prefix}: Expected component of type {required_type}, got {unity_type}"
        )

def validate_serialized_transform(value: Any, param_name: str) -> None:
    """Validate that a value is a serialized Transform component.
    
    Args:
        value: The value to validate
        param_name: Name of the parameter for error reporting
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Use the component validation with the Transform type
    validate_serialized_component(value, param_name, "Transform")
    
    # For non-circular references, validate essential transform properties
    if value is not None and not is_circular_reference(value):
        # Check for position, rotation, and scale properties
        # These might be directly on the transform or under a "localPosition", etc. property
        required_property_found = False
        position_properties = ["position", "localPosition"]
        rotation_properties = ["rotation", "localRotation", "eulerAngles", "localEulerAngles"]
        scale_properties = ["localScale"]
        
        # Check if at least one position, rotation, or scale property exists
        for prop in position_properties + rotation_properties + scale_properties:
            if prop in value:
                required_property_found = True
                break
                
        if not required_property_found:
            raise ParameterValidationError(
                f"Invalid {param_name} value: Missing required Transform properties"
            )

def validate_serialization_status(value: Any, param_name: str) -> None:
    """Validate that a serialized object has a successful serialization status.
    
    Args:
        value: The value to validate
        param_name: Name of the parameter for error reporting
        
    Raises:
        ParameterValidationError: If validation fails or serialization was not successful
    """
    if value is None:
        return  # Optional parameter
        
    error_prefix = f"Invalid {param_name} value"
    
    if not isinstance(value, dict):
        raise ParameterValidationError(
            f"{error_prefix}: Expected serialized object, got {type(value).__name__}"
        )
        
    if not is_serialized_unity_object(value):
        raise ParameterValidationError(
            f"{error_prefix}: Value is not a serialized Unity object"
        )
    
    # Check for serialization status
    if SERIALIZATION_STATUS_KEY in value:
        status = value[SERIALIZATION_STATUS_KEY]
        if status.lower() != "success":
            error_message = value.get("__serialization_error", "Unknown serialization error")
            raise ParameterValidationError(
                f"{error_prefix}: Serialization failed with status '{status}': {error_message}"
            ) 