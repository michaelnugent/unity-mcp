"""
Validation layer for Unity MCP tools.

This module provides a set of standardized validation functions that ensure
consistent parameter validation across all tools, with clear and helpful error messages.
"""
from typing import List, Dict, Any, Union, Optional
from unity_connection import ParameterValidationError
import os
import re

def validate_gameobject_name(name: Any) -> None:
    """Validate a GameObject name parameter.
    
    Args:
        name: The name value to validate
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(name, str):
        raise ParameterValidationError(f"GameObject name must be a string, got {type(name).__name__}: {name}")
    
    # Check for empty name
    if not name:
        raise ParameterValidationError("GameObject name cannot be empty")

def validate_asset_path(path: Any, must_exist: bool = False, extension: Optional[str] = None) -> None:
    """Validate an asset path parameter.
    
    Args:
        path: The path value to validate
        must_exist: Whether the asset must exist (cannot be validated client-side, only format check)
        extension: Optional file extension the path must have (e.g., ".prefab")
    
    Returns:
        None: This function doesn't return anything but raises exceptions on validation failure
    
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(path, str):
        raise ParameterValidationError(f"Asset path must be a string, got {type(path).__name__}: {path}")
    
    # Check for empty path
    if not path:
        raise ParameterValidationError("Asset path cannot be empty")
    
    # Check for Assets prefix
    if not path.startswith("Assets/"):
        raise ParameterValidationError(f"Asset path must start with 'Assets/', got: {path}")
    
    # Check file extension if specified
    if extension and not path.endswith(extension):
        raise ParameterValidationError(f"Asset path must end with '{extension}', got: {path}")

def validate_gameobject_path(path: Any, must_exist: bool = False) -> None:
    """Validate a GameObject path parameter.
    
    Args:
        path: The path value to validate
        must_exist: Whether the GameObject must exist (cannot be validated client-side, only format check)
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(path, str):
        raise ParameterValidationError(f"GameObject path must be a string, got {type(path).__name__}: {path}")
    
    # Check for empty path
    if not path:
        raise ParameterValidationError("GameObject path cannot be empty")

def validate_component_type(component_type: Any) -> None:
    """Validate a component type parameter.
    
    Args:
        component_type: The component type to validate
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(component_type, str):
        raise ParameterValidationError(f"Component type must be a string, got {type(component_type).__name__}: {component_type}")
    
    # Check for empty type
    if not component_type:
        raise ParameterValidationError("Component type cannot be empty")

def validate_menu_path(menu_path: Any) -> None:
    """Validate a menu path parameter.
    
    Args:
        menu_path: The menu path to validate
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(menu_path, str):
        raise ParameterValidationError(f"Menu path must be a string, got {type(menu_path).__name__}: {menu_path}")
    
    # Check for empty path
    if not menu_path:
        raise ParameterValidationError("Menu path cannot be empty")
    
    # Check for menu separator
    if "/" not in menu_path:
        raise ParameterValidationError(f"Menu path must contain at least one '/' separator, got: {menu_path}")

def validate_script_code(code: Any) -> None:
    """Validate a script code parameter.
    
    Args:
        code: The script code to validate
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(code, str):
        raise ParameterValidationError(f"Script code must be a string, got {type(code).__name__}")
    
    # Not checking content - empty scripts are valid

def validate_screenshot_path(path: Any) -> None:
    """Validate a screenshot save path parameter.
    
    Args:
        path: The path to validate
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(path, str):
        raise ParameterValidationError(f"Screenshot path must be a string, got {type(path).__name__}: {path}")
    
    # Check for empty path
    if not path:
        raise ParameterValidationError("Screenshot path cannot be empty")
    
    # Check file extension
    valid_extensions = [".png", ".jpg", ".jpeg"]
    if not any(path.lower().endswith(ext) for ext in valid_extensions):
        raise ParameterValidationError(f"Screenshot path must end with {', '.join(valid_extensions)}, got: {path}")

def validate_action(action: Any, valid_actions: List[str]) -> None:
    """Validate an action parameter against a list of valid actions.
    
    Args:
        action: The action to validate
        valid_actions: List of valid action values
    
    Returns:
        None: This function doesn't return anything but raises exceptions on validation failure
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Check type
    if not isinstance(action, str):
        raise ParameterValidationError(f"Action must be a string, got {type(action).__name__}: {action}")
    
    # Check if action is in valid_actions list
    if action not in valid_actions:
        raise ParameterValidationError(f"Action must be one of: {', '.join(valid_actions)}, got: {action}")

def validate_parameters_by_action(action: str, params: Dict[str, Any], action_param_map: Dict[str, List[str]]) -> None:
    """Validate that all required parameters for an action are present.
    
    Args:
        action: The current action
        params: Parameter dictionary to validate
        action_param_map: Mapping of actions to required parameter lists
    
    Returns:
        None: This function doesn't return anything but raises exceptions on validation failure
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Get required params for this action
    if action not in action_param_map:
        return  # No validation needed for this action
    
    required_params = action_param_map[action]
    
    # Check for missing parameters
    for param in required_params:
        if param not in params:
            raise ParameterValidationError(f"Action '{action}' requires '{param}' parameter")

def create_action_validator(valid_actions: List[str]) -> callable:
    """Create an action validator function for a specific set of valid actions.
    
    Args:
        valid_actions: List of valid action values
        
    Returns:
        callable: A validator function that checks if an action is valid against the provided list
    """
    def validator(action: Any) -> None:
        validate_action(action, valid_actions)
    
    return validator 