"""
Shared validation utilities for Unity MCP tools.

This module provides validation functions that can be used across different tool modules
to ensure consistent parameter validation and error reporting.

It also includes functions for validating serialized Unity objects with the enhanced
serialization format, including validation of GameObject, Component, and Transform
representations.
"""

from typing import Any, Dict, List, Tuple, Union, Optional, Type
from unity_connection import ParameterValidationError
from type_converters import (
    is_serialized_unity_object, extract_type_info, is_circular_reference,
    get_unity_components, get_unity_children, find_component_by_type,
    SERIALIZATION_TYPE_KEY, SERIALIZATION_UNITY_TYPE_KEY, SERIALIZATION_STATUS_KEY,
    SERIALIZATION_PATH_KEY, SERIALIZATION_ID_KEY
)

class ParameterFormat:
    """Base class for parameter format definitions.
    
    This class provides a structure for tools to define and document their
    parameter formats in a consistent way. Tools can subclass this and define
    their specific parameters, making validation and documentation more maintainable.
    """
    
    # Define common parameter types that can be reused across tools
    POSITION_TYPE = Union[List[float], Dict[str, float]]
    ROTATION_TYPE = Union[List[float], Dict[str, float]]
    SCALE_TYPE = Union[List[float], Dict[str, float]]
    COLOR_TYPE = Union[List[float], str]
    GAMEOBJECT_REF_TYPE = str
    ASSET_PATH_TYPE = str
    
    # Common parameter definitions with examples and validation rules
    COMMON_PARAMETERS = {
        "position": {
            "type": POSITION_TYPE,
            "description": "3D position in world space",
            "examples": [
                [0, 1, 0],
                {"x": 0, "y": 1, "z": 0}
            ],
            "validation_rules": [
                "Must be a list/array with exactly 3 numbers or an object with x, y, z properties",
                "All components must be numeric values"
            ]
        },
        "rotation": {
            "type": ROTATION_TYPE,
            "description": "Rotation as euler angles or quaternion",
            "examples": [
                [0, 90, 0],  # Euler angles (degrees)
                [0, 0, 0, 1],  # Quaternion (x, y, z, w)
                {"x": 0, "y": 0, "z": 0},  # Euler angles
                {"x": 0, "y": 0, "z": 0, "w": 1}  # Quaternion
            ],
            "validation_rules": [
                "Euler angles: Must be a list/array with exactly 3 numbers or an object with x, y, z properties",
                "Quaternion: Must be a list/array with exactly 4 numbers or an object with x, y, z, w properties",
                "All components must be numeric values"
            ]
        },
        "scale": {
            "type": SCALE_TYPE,
            "description": "3D scale factors for each axis",
            "examples": [
                [1, 1, 1],
                {"x": 1, "y": 1, "z": 1}
            ],
            "validation_rules": [
                "Must be a list/array with exactly 3 numbers or an object with x, y, z properties",
                "All components must be numeric values"
            ]
        }
    }
    
    @classmethod
    def get_parameter_definition(cls, param_name: str) -> Optional[Dict[str, Any]]:
        """Get parameter definition by name.
        
        Args:
            param_name: Name of the parameter
            
        Returns:
            Parameter definition dictionary or None if not found
        """
        # First check tool-specific parameters
        if hasattr(cls, 'PARAMETERS') and param_name in cls.PARAMETERS:
            return cls.PARAMETERS[param_name]
        
        # Then check common parameters
        return cls.COMMON_PARAMETERS.get(param_name)
    
    @classmethod
    def get_parameter_type(cls, param_name: str) -> Optional[Type]:
        """Get parameter type by name.
        
        Args:
            param_name: Name of the parameter
            
        Returns:
            Parameter type or None if not found
        """
        param_def = cls.get_parameter_definition(param_name)
        return param_def.get('type') if param_def else None
    
    @classmethod
    def get_parameter_examples(cls, param_name: str) -> List[Any]:
        """Get examples for a parameter.
        
        Args:
            param_name: Name of the parameter
            
        Returns:
            List of examples for the parameter or empty list if not found
        """
        param_def = cls.get_parameter_definition(param_name)
        return param_def.get('examples', []) if param_def else []
    
    @classmethod
    def get_parameter_description(cls, param_name: str) -> str:
        """Get description for a parameter.
        
        Args:
            param_name: Name of the parameter
            
        Returns:
            Description of the parameter or empty string if not found
        """
        param_def = cls.get_parameter_definition(param_name)
        return param_def.get('description', '') if param_def else ''
    
    @classmethod
    def get_parameter_validation_rules(cls, param_name: str) -> List[str]:
        """Get validation rules for a parameter.
        
        Args:
            param_name: Name of the parameter
            
        Returns:
            List of validation rules or empty list if not found
        """
        param_def = cls.get_parameter_definition(param_name)
        return param_def.get('validation_rules', []) if param_def else []
    
    @classmethod
    def get_required_parameters(cls, action: str) -> List[str]:
        """Get required parameters for an action.
        
        Args:
            action: The action to get required parameters for
            
        Returns:
            List of required parameter names or empty list if not found
        """
        if hasattr(cls, 'REQUIRED_PARAMETERS') and action in cls.REQUIRED_PARAMETERS:
            return cls.REQUIRED_PARAMETERS[action]
        return []
    
    @classmethod
    def get_valid_actions(cls) -> List[str]:
        """Get list of valid actions for this tool.
        
        Returns:
            List of valid action names
        """
        if hasattr(cls, 'VALID_ACTIONS'):
            return cls.VALID_ACTIONS
        if hasattr(cls, 'REQUIRED_PARAMETERS'):
            return list(cls.REQUIRED_PARAMETERS.keys())
        return []

def get_type_description_with_example(expected_type: Union[type, Tuple[type, ...]]) -> Tuple[str, str]:
    """Generate a human-readable type description with an example.
    
    Args:
        expected_type: The expected type or tuple of allowed types
        
    Returns:
        Tuple containing (type_description, example_str)
    """
    # For simple types, just use the type name
    if expected_type == str:
        return "str", '"example_string"'
    elif expected_type == int:
        return "int", "42"
    elif expected_type == float:
        return "float", "3.14"
    elif expected_type == bool:
        return "bool", "true or false"
        
    # For complex types, provide more helpful descriptions and examples
    elif expected_type == list:
        return "list", "[item1, item2, item3]"
    elif expected_type == dict:
        return "dict", '{"key1": value1, "key2": value2}'
        
    # For Vector2 (common in Unity)
    elif expected_type == tuple and list in expected_type:
        return "array or list", "[1, 2]"
        
    # For Vector3 (common in Unity)
    elif expected_type == list or (isinstance(expected_type, tuple) and list in expected_type):
        return "array or list", "[x, y, z] or {\"x\": 0, \"y\": 0, \"z\": 0}"
        
    # For color parameters
    elif expected_type == list or (isinstance(expected_type, tuple) and list in expected_type):
        return "array, list or string", "[r, g, b, a] or \"#RRGGBBAA\" or \"red\""
        
    # Handle tuples of allowed types
    elif isinstance(expected_type, tuple):
        type_names = [t.__name__ for t in expected_type]
        return " or ".join(type_names), "(multiple formats allowed)"
        
    # Default case
    else:
        return expected_type.__name__, f"(a valid {expected_type.__name__})"

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
                f"{error_prefix}: Vector3 must have exactly 3 components, got {len(value)}. " 
                f"Example format: [x, y, z] with numeric values."
            )
        
        # Check if all elements are numbers
        for i, component in enumerate(value):
            if not isinstance(component, (int, float)):
                raise ParameterValidationError(
                    f"{error_prefix}: Component {i} must be a number, got {type(component).__name__} ({component}). "
                    f"Example format: [0, 1, 0] with all numeric values."
                )
                
    # Check if value is a dictionary with x,y,z keys
    elif isinstance(value, dict):
        required_keys = {"x", "y", "z"}
        missing_keys = required_keys - set(value.keys())
        if missing_keys:
            raise ParameterValidationError(
                f"{error_prefix}: Missing Vector3 components: {', '.join(missing_keys)}. "
                f"Example format: {{\"x\": 0, \"y\": 1, \"z\": 0}} with all components."
            )
            
        # Check if values are numbers
        for key in required_keys:
            if not isinstance(value[key], (int, float)):
                raise ParameterValidationError(
                    f"{error_prefix}: Component {key} must be a number, got {type(value[key]).__name__} ({value[key]}). "
                    f"Example format: {{\"x\": 0, \"y\": 1, \"z\": 0}} with numeric values."
                )
    else:
        raise ParameterValidationError(
            f"{error_prefix}: Expected list, tuple or dict, got {type(value).__name__} ({value}). "
            f"Example formats: [0, 1, 0] or {{\"x\": 0, \"y\": 1, \"z\": 0}}"
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
        # Get the readable type description and example
        type_desc, type_example = get_type_description_with_example(expected_type)
        
        # Create a readable description of the actual value
        actual_type_str = type(param).__name__
        value_str = str(param)
        if len(value_str) > 50:  # Truncate long values
            value_str = value_str[:47] + "..."
        
        # Build an enhanced error message with example format
        error_msg = (
            f"{tool_name} '{action}' parameter '{param_name}' must be of type {type_desc}, "
            f"got {actual_type_str}: {value_str}. "
            f"Example format: {type_example}"
        )
        
        raise ParameterValidationError(error_msg)

def validate_dict_structure(
    param: Any, 
    param_name: str, 
    expected_keys: Dict[str, Union[type, Tuple[type, ...]]],
    required_keys: Optional[List[str]] = None,
    action: str = "",
    tool_name: str = ""
) -> None:
    """Validate that a dictionary parameter has the expected structure.
    
    Args:
        param: Dictionary parameter to validate
        param_name: Name of the parameter for error reporting
        expected_keys: Dictionary mapping key names to their expected types
        required_keys: List of keys that must be present (if None, all keys in expected_keys are required)
        action: Current action being performed (for error context)
        tool_name: Name of the tool (for error context)
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Validate basic type
    if not isinstance(param, dict):
        type_desc, type_example = "dict", "{'key1': value1, 'key2': value2}"
        raise ParameterValidationError(
            f"Parameter '{param_name}' must be a dictionary, got {type(param).__name__}: {param}. "
            f"Example: {type_example}"
        )
    
    # Determine which keys are required
    if required_keys is None:
        required_keys = list(expected_keys.keys())
    
    # Check for missing required keys
    missing_keys = [key for key in required_keys if key not in param]
    if missing_keys:
        # Create an example with the missing keys
        example = {k: "value" for k in required_keys}
        raise ParameterValidationError(
            f"Parameter '{param_name}' is missing required keys: {', '.join(missing_keys)}. "
            f"Required keys are: {', '.join(required_keys)}. "
            f"Example: {example}"
        )
    
    # Validate types of provided values
    for key, value in param.items():
        if key in expected_keys:
            expected_type = expected_keys[key]
            if not isinstance(value, expected_type):
                type_desc, type_example = get_type_description_with_example(expected_type)
                raise ParameterValidationError(
                    f"In parameter '{param_name}', key '{key}' must be of type {type_desc}, "
                    f"got {type(value).__name__}: {value}. "
                    f"Example: {type_example}"
                )

def validate_nested_structure(
    value: Any, 
    schema: Dict[str, Any], 
    path: str = "root", 
    param_name: str = "",
    action: str = "",
    tool_name: str = ""
) -> None:
    """Validate complex nested structures against a schema.
    
    This allows validation of deeply nested structures like:
    {
        "transform": {
            "position": [1, 2, 3],
            "rotation": [0, 0, 0, 1]
        },
        "components": [
            {"type": "Collider", "properties": {...}},
            {"type": "Renderer", "properties": {...}}
        ]
    }
    
    The schema defines expected types and structures at each level.
    
    Args:
        value: The value to validate
        schema: Schema definition that describes expected structure
        path: Current path in the structure for error reporting
        param_name: Name of the parameter for error reporting
        action: Current action being performed
        tool_name: Name of the tool for error reporting
        
    Raises:
        ParameterValidationError: If validation fails
    """
    # Schema can be:
    # 1. A type or tuple of types - validate directly
    # 2. A dictionary with keys that describes structure
    # 3. A list with one element that describes array element type
    # 4. A callable validator function
    
    # Handle None case for optional values
    if value is None:
        if schema.get('required', False):
            raise ParameterValidationError(
                f"Required value at '{path}' is missing. "
                f"Expected: {schema.get('description', str(schema['type']) if 'type' in schema else 'value')}"
            )
        return
    
    # Handle different schema types
    if isinstance(schema, dict):
        # Schema is a dictionary describing structure
        if 'type' in schema:
            # Simple type validation with possible constraints
            expected_type = schema['type']
            
            # Validate basic type
            if not isinstance(value, expected_type):
                type_desc, example = get_type_description_with_example(expected_type)
                if 'example' in schema:
                    example = schema['example']
                
                raise ParameterValidationError(
                    f"Invalid value at '{path}' in parameter '{param_name}'. "
                    f"Expected {schema.get('description', type_desc)}, got {type(value).__name__}: {value}. "
                    f"Example: {example}"
                )
                
            # Check constraints if defined
            if 'constraints' in schema:
                constraints = schema['constraints']
                
                # Numeric constraints
                if 'min' in constraints and value < constraints['min']:
                    raise ParameterValidationError(
                        f"Value at '{path}' must be at least {constraints['min']}, got {value}"
                    )
                if 'max' in constraints and value > constraints['max']:
                    raise ParameterValidationError(
                        f"Value at '{path}' must be at most {constraints['max']}, got {value}"
                    )
                    
                # String constraints
                if 'pattern' in constraints and isinstance(value, str):
                    import re
                    if not re.match(constraints['pattern'], value):
                        raise ParameterValidationError(
                            f"String at '{path}' must match pattern {constraints['pattern']}, got '{value}'"
                        )
                
                # Length constraints for strings, lists, dicts
                if 'min_length' in constraints:
                    if len(value) < constraints['min_length']:
                        raise ParameterValidationError(
                            f"Value at '{path}' must have at least {constraints['min_length']} items, got {len(value)}"
                        )
                if 'max_length' in constraints:
                    if len(value) > constraints['max_length']:
                        raise ParameterValidationError(
                            f"Value at '{path}' must have at most {constraints['max_length']} items, got {len(value)}"
                        )
                
                # Enum constraints
                if 'enum' in constraints and value not in constraints['enum']:
                    raise ParameterValidationError(
                        f"Value at '{path}' must be one of {constraints['enum']}, got {value}"
                    )
                
        elif 'properties' in schema:
            # Object validation with defined properties
            if not isinstance(value, dict):
                raise ParameterValidationError(
                    f"Value at '{path}' must be an object, got {type(value).__name__}: {value}"
                )
                
            properties = schema['properties']
            required = schema.get('required', [])
            
            # Check required properties are present
            for prop in required:
                if prop not in value:
                    raise ParameterValidationError(
                        f"Required property '{prop}' is missing at '{path}'"
                    )
                    
            # Validate each property in the value
            for prop, prop_value in value.items():
                if prop in properties:
                    validate_nested_structure(
                        prop_value, 
                        properties[prop], 
                        f"{path}.{prop}", 
                        param_name,
                        action,
                        tool_name
                    )
                elif not schema.get('additional_properties', False):
                    raise ParameterValidationError(
                        f"Unknown property '{prop}' at '{path}'. "
                        f"Allowed properties: {list(properties.keys())}"
                    )
    
    elif isinstance(schema, list) and len(schema) == 1:
        # Array validation with elements matching the schema
        if not isinstance(value, (list, tuple)):
            raise ParameterValidationError(
                f"Value at '{path}' must be an array, got {type(value).__name__}: {value}"
            )
            
        # Validate each array element
        for i, item in enumerate(value):
            validate_nested_structure(
                item, 
                schema[0], 
                f"{path}[{i}]", 
                param_name,
                action,
                tool_name
            )
    
    elif isinstance(schema, type) or (isinstance(schema, tuple) and all(isinstance(t, type) for t in schema)):
        # Direct type validation
        if not isinstance(value, schema):
            type_desc, example = get_type_description_with_example(schema)
            raise ParameterValidationError(
                f"Value at '{path}' must be of type {type_desc}, got {type(value).__name__}: {value}. "
                f"Example: {example}"
            )
    
    elif callable(schema):
        # Custom validator function
        try:
            schema(value, f"{path}")
        except Exception as e:
            # Convert any exception to ParameterValidationError
            raise ParameterValidationError(f"Validation failed at '{path}': {str(e)}")

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
            f"{error_prefix}: Expected GameObject object, got {type(value).__name__} ({value})"
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
            f"{error_prefix}: Expected Component object, got {type(value).__name__} ({value})"
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
        ParameterValidationError: If the serialization status is not successful
    """
    if value is None:
        return  # Optional parameter
        
    if not isinstance(value, dict):
        raise ParameterValidationError(
            f"Invalid {param_name} value: Expected serialized object, got {type(value).__name__}"
        )
        
    if SERIALIZATION_STATUS_KEY not in value:
        raise ParameterValidationError(
            f"Invalid {param_name} value: Missing serialization status"
        )
        
    status = value.get(SERIALIZATION_STATUS_KEY)
    if status != "success":
        error_message = value.get("message", "Unknown serialization error")
        raise ParameterValidationError(
            f"Invalid {param_name} value: Serialization failed - {error_message}"
        )

def generate_parameter_help_response(
    tool_name: str, 
    param_name: Optional[str] = None, 
    action: Optional[str] = None,
    parameter_format_class: Optional[Type] = None
) -> Dict[str, Any]:
    """Generate a formatted help response with parameter documentation.
    
    This function creates a structured response containing parameter documentation
    to help users understand the expected formats and requirements. It can be used
    both as a standalone help feature and to enhance error messages.
    
    Args:
        tool_name: Name of the tool
        param_name: Optional name of the specific parameter to document
        action: Optional action context for the parameter
        parameter_format_class: Optional ParameterFormat class to use for documentation
        
    Returns:
        Dict containing formatted documentation
    """
    result = {
        "tool": tool_name,
        "action": action,
        "documentation": {}
    }
    
    # If no parameter format class was provided, just return basic info
    if not parameter_format_class:
        return result
    
    # If a specific parameter was requested
    if param_name:
        param_def = parameter_format_class.get_parameter_definition(param_name)
        if param_def:
            result["documentation"] = {
                "parameter": param_name,
                "description": param_def.get("description", ""),
                "type": str(param_def.get("type", "unknown")),
                "examples": param_def.get("examples", []),
                "validation_rules": param_def.get("validation_rules", [])
            }
            
            # Add information about whether this parameter is required for the given action
            if action:
                required_params = parameter_format_class.get_required_parameters(action)
                result["documentation"]["required_for_action"] = param_name in required_params
        else:
            result["documentation"] = {
                "parameter": param_name,
                "error": f"No documentation found for parameter '{param_name}'"
            }
    
    # If documentation for an action was requested
    elif action:
        # Get required parameters for the action
        required_params = parameter_format_class.get_required_parameters(action)
        
        # Get valid actions to check if the requested action is valid
        valid_actions = parameter_format_class.get_valid_actions()
        action_valid = action in valid_actions
        
        result["documentation"] = {
            "action": action,
            "valid_action": action_valid,
            "required_parameters": [],
            "optional_parameters": []
        }
        
        # If the action is valid, document its parameters
        if action_valid:
            # Add documentation for each required parameter
            for req_param in required_params:
                param_def = parameter_format_class.get_parameter_definition(req_param)
                if param_def:
                    result["documentation"]["required_parameters"].append({
                        "name": req_param,
                        "description": param_def.get("description", ""),
                        "type": str(param_def.get("type", "unknown")),
                        "examples": param_def.get("examples", [])
                    })
    
    # If no specific parameter or action was requested, list all valid actions
    else:
        valid_actions = parameter_format_class.get_valid_actions()
        result["documentation"] = {
            "valid_actions": valid_actions,
            "common_parameters": list(parameter_format_class.COMMON_PARAMETERS.keys())
        }
        
        # If there's a tool-specific PARAMETERS dict, include those parameters
        if hasattr(parameter_format_class, 'PARAMETERS'):
            result["documentation"]["tool_parameters"] = list(parameter_format_class.PARAMETERS.keys())
    
    return result

def enhance_error_with_documentation(
    error_message: str,
    tool_name: str,
    param_name: Optional[str] = None,
    action: Optional[str] = None,
    parameter_format_class: Optional[Type] = None
) -> Dict[str, Any]:
    """Enhance an error message with parameter documentation.
    
    This function takes an error message and enriches it with parameter documentation
    to help users understand how to fix the issue.
    
    Args:
        error_message: The original error message
        tool_name: Name of the tool
        param_name: Optional name of the parameter that caused the error
        action: Optional action context for the error
        parameter_format_class: Optional ParameterFormat class to use for documentation
        
    Returns:
        Dict containing the enhanced error response
    """
    response = {
        "success": False,
        "message": error_message,
        "validation_error": True,
    }
    
    # If we have a parameter format class, add documentation
    if parameter_format_class:
        # Generate parameter help
        help_info = generate_parameter_help_response(
            tool_name, param_name, action, parameter_format_class
        )
        
        # Add documentation to the error response
        response["help"] = help_info
        
        # If we have a specific parameter with examples, add a suggestions section
        if param_name and "documentation" in help_info and "examples" in help_info["documentation"]:
            examples = help_info["documentation"]["examples"]
            if examples:
                response["suggestions"] = {
                    "example_format": examples[0] if examples else None,
                    "valid_format": help_info["documentation"].get("validation_rules", [])
                }
    
    return response 