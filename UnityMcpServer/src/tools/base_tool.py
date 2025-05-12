"""
Base class for all Unity MCP tools with shared validation logic.
"""
import asyncio
from typing import Dict, Any, Optional, Type, List, Tuple, Union
from unity_connection import get_unity_connection, ParameterValidationError
from validation_utils import (
    validate_required_param, validate_param_type,
    validate_serialized_gameobject, validate_serialized_component, 
    validate_serialized_transform, validate_serialization_status
)

# Import the new type converters
from type_converters import (
    convert_vector2, convert_vector3, convert_quaternion,
    convert_color, convert_rect, convert_bounds, euler_to_quaternion,
    is_serialized_unity_object, extract_type_info, get_unity_components,
    get_unity_children, find_component_by_type
)

# Import serialization utilities
import serialization_utils
import copy

class BaseTool:
    """Base class for all Unity MCP tools with shared validation logic."""
    
    # Class-level attributes to be overridden by subclasses
    tool_name: str = None
    required_params: Dict[str, Dict[str, Type]] = {}
    parameter_format = None  # Subclasses can set this to their ParameterFormat class
    
    # Parameter types requiring conversion
    vector2_params: List[str] = []
    vector3_params: List[str] = []
    quaternion_params: List[str] = []
    euler_params: List[str] = []  # Euler angles to be converted to quaternions
    color_params: List[str] = []
    rect_params: List[str] = []
    bounds_params: List[str] = []
    
    # Parameters expected to be serialized Unity objects of specific types
    gameobject_params: List[str] = []
    component_params: List[str] = []
    transform_params: List[str] = []
    
    def __init__(self, ctx=None):
        self.ctx = ctx
        # Only get the connection if it's not already set
        # This allows tests to inject a mock connection
        self.unity_conn = getattr(self, 'unity_conn', get_unity_connection())
    
    def validate_and_convert_params(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and convert parameters based on parameter type requirements.
        
        Args:
            action: The current action being performed
            params: Parameters to validate
            
        Returns:
            Dict[str, Any]: Converted parameters
            
        Raises:
            ParameterValidationError: If validation fails
        """
        # Make a copy of the parameters to avoid modifying the original
        converted_params = copy.deepcopy(params) if params is not None else {}
        
        # Check if action is in required_params
        if action in self.required_params:
            # Check for required parameters
            for param_name, param_type in self.required_params[action].items():
                # Skip checking parameter presence if it's an optional parameter (None)
                if param_type is None:
                    continue
                    
                # Check if required parameter is present
                if param_name not in converted_params:
                    # Support for ParameterFormat validation
                    if self.parameter_format:
                        # If using ParameterFormat, check if this is a required parameter
                        required_params = self.parameter_format.get_required_parameters(action)
                        if param_name in required_params:
                            raise ParameterValidationError(
                                f"{self.tool_name} '{action}' action requires '{param_name}' parameter"
                            )
                    else:
                        # Traditional validation
                        raise ParameterValidationError(
                            f"{self.tool_name} '{action}' action requires '{param_name}' parameter"
                        )
                
                # Validate parameter type
                if param_name in converted_params and converted_params[param_name] is not None:
                    validate_param_type(
                        converted_params[param_name], param_name, param_type, action, self.tool_name
                    )
        
        # For all parameters, apply type conversions if needed
        for param_name, param_value in list(converted_params.items()):
            if param_value is None:
                continue  # Skip None values
                
            # Vector2 conversion
            if param_name in self.vector2_params:
                converted_params[param_name] = convert_vector2(param_value, param_name)
                
            # Vector3 conversion
            elif param_name in self.vector3_params:
                converted_params[param_name] = convert_vector3(param_value, param_name)
                
            # Quaternion conversion
            elif param_name in self.quaternion_params:
                converted_params[param_name] = convert_quaternion(param_value, param_name)
                
            # Euler to Quaternion conversion
            elif param_name in self.euler_params:
                converted_params[param_name] = euler_to_quaternion(param_value)
                
            # Color conversion
            elif param_name in self.color_params:
                converted_params[param_name] = convert_color(param_value, param_name)
                
            # Rect conversion
            elif param_name in self.rect_params:
                converted_params[param_name] = convert_rect(param_value, param_name)
                
            # Bounds conversion
            elif param_name in self.bounds_params:
                converted_params[param_name] = convert_bounds(param_value, param_name)
                
            # Validate serialized Unity objects if present
            elif param_name in self.gameobject_params:
                validate_serialized_gameobject(param_value, param_name)
                
            elif param_name in self.component_params:
                validate_serialized_component(param_value, param_name)
                
            elif param_name in self.transform_params:
                validate_serialized_transform(param_value, param_name)
                
        # Call additional validation specific to each tool
        self.additional_validation(action, converted_params)
        
        return converted_params
    
    def validate_params(self, action: str, params: Dict[str, Any]) -> None:
        """Legacy method for backward compatibility.
        
        Args:
            action: The current action being performed
            params: Parameters to validate
            
        Raises:
            ParameterValidationError: If validation fails
        """
        # This method is kept for backward compatibility
        # It calls the new validate_and_convert_params method but discards the converted values
        self.validate_and_convert_params(action, params)
    
    def additional_validation(self, action: str, params: Dict[str, Any]) -> None:
        """Additional validation specific to each tool.
        
        This method should be overridden by subclasses to add tool-specific validation.
        
        Args:
            action: The current action being performed
            params: Parameters to validate
            
        Raises:
            ParameterValidationError: If validation fails
        """
        pass
    
    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Unity with parameter validation and conversion.
        
        Args:
            command_type: The type of command to send
            params: The parameters for the command
            
        Returns:
            The response from Unity
            
        Raises:
            ParameterValidationError: If parameters fail validation
        """
        # Clone params to avoid modifying the original
        params = params.copy() if params else {}
        
        # Extract action if present
        action = params.get("action", "").lower() if params.get("action") else ""
        
        # Check if this is a validation-only request
        validate_only = params.get("validateOnly", False)
        
        # Validate and convert parameters
        try:
            converted_params = self.validate_and_convert_params(action, params)
            
            # For validation-only mode, we might return here without sending to Unity
            if validate_only and not self.needs_unity_validation(action, converted_params):
                return {
                    "success": True, 
                    "message": "Parameters validated successfully", 
                    "data": {"valid": True}
                }
            
            # Use the converted parameters
            params = converted_params
            
        except Exception as e:
            if validate_only:
                return {
                    "success": False,
                    "message": str(e),
                    "data": {"valid": False, "reason": str(e)},
                    "validation_error": True
                }
            raise ParameterValidationError(str(e))
        
        # Send command using the Unity connection
        response = self.unity_conn.send_command(command_type, params)
        
        # Post-process serialized Unity objects if needed
        if isinstance(response, dict) and 'data' in response:
            response = self.post_process_response(response, action, params)
            
        return response
    
    def post_process_response(self, response: Dict[str, Any], action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process the response from Unity, especially for serialized objects.
        
        This method can be overridden by subclasses to perform tool-specific 
        post-processing of responses. The default implementation returns the response as-is.
        
        Args:
            response: The response from Unity
            action: The current action being performed
            params: The parameters that were sent
            
        Returns:
            The processed response
        """
        # By default, return the response unchanged
        return response
        
    def process_serialized_unity_object(self, obj: Any) -> Any:
        """Process a serialized Unity object for client consumption.
        
        Subclasses can override this to perform tool-specific processing of serialized objects.
        The default implementation strips internal metadata if requested by configuration.
        
        Args:
            obj: The serialized object from Unity
            
        Returns:
            The processed object
        """
        # By default, just return the object unchanged
        return obj
    
    def needs_unity_validation(self, action: str, params: Dict[str, Any]) -> bool:
        """Determine if a validate_only request needs to go to Unity for validation.
        
        Some validations can be handled entirely on the Python side, while others
        might need Unity-side validation (like checking if a GameObject exists).
        
        Args:
            action: The current action being performed
            params: Parameters to check
            
        Returns:
            True if Unity-side validation is needed, False if all validation can be done locally
        """
        # By default, assume we need Unity validation
        # Subclasses can override this to avoid unnecessary Unity communication
        return True
    
    async def send_command_async(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Unity asynchronously with parameter validation and conversion.
        
        This is an async wrapper around send_command.
        
        Args:
            command_type: The type of command to send
            params: The parameters for the command
            
        Returns:
            The response from Unity
            
        Raises:
            ParameterValidationError: If parameters fail validation
        """
        # Run the synchronous send_command
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.send_command, command_type, params
        ) 