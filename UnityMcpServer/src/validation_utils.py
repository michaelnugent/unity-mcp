"""
Shared validation utilities for Unity MCP tools.

This module provides validation functions that can be used across different tool modules
to ensure consistent parameter validation and error reporting.
"""

from typing import Any, Dict, List, Tuple, Union
from unity_connection import ParameterValidationError

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