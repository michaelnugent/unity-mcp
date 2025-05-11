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

class BaseTool:
    """Base class for all Unity MCP tools with shared validation logic."""
    
    # Class-level attributes to be overridden by subclasses
    tool_name: str = None
    required_params: Dict[str, Dict[str, Type]] = {}
    
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
        """Validate and convert parameters before sending to Unity.
        
        Args:
            action: The current action being performed
            params: Parameters to validate and convert
            
        Returns:
            Dict with validated and converted parameters
            
        Raises:
            ParameterValidationError: If validation fails
        """
        # Make a copy of params to avoid modifying the original
        converted_params = params.copy() if params else {}
        
        # Check required parameters based on action
        action_required = self.required_params.get(action, {})
        for param_name, param_type in action_required.items():
            try:
                if param_name not in params:
                    raise ParameterValidationError(f"{self.tool_name} '{action}' action requires '{param_name}' parameter")
                if params[param_name] is not None:  # Allow None values for optional params
                    validate_param_type(params[param_name], param_name, param_type, action, self.tool_name)
            except ParameterValidationError as e:
                # Re-raise with the original error message to preserve parameter information
                raise ParameterValidationError(str(e))
        
        # Convert Vector2 parameters
        for param_name in self.vector2_params:
            if param_name in params and params[param_name] is not None:
                try:
                    converted_params[param_name] = convert_vector2(params[param_name], param_name)
                except Exception as e:
                    # Provide a clear error message that references the specific parameter
                    raise ParameterValidationError(f"Failed to convert {param_name} to Vector2: {str(e)}")
        
        # Convert Vector3 parameters
        for param_name in self.vector3_params:
            if param_name in params and params[param_name] is not None:
                try:
                    converted_params[param_name] = convert_vector3(params[param_name], param_name)
                except Exception as e:
                    # Provide a clear error message that references the specific parameter
                    raise ParameterValidationError(f"Failed to convert {param_name} to Vector3: {str(e)}")
        
        # Convert Quaternion parameters
        for param_name in self.quaternion_params:
            if param_name in params and params[param_name] is not None:
                try:
                    converted_params[param_name] = convert_quaternion(params[param_name], param_name)
                except Exception as e:
                    # Provide a clear error message that references the specific parameter
                    raise ParameterValidationError(f"Failed to convert {param_name} to Quaternion: {str(e)}")
        
        # Convert Euler angles to Quaternion
        for param_name in self.euler_params:
            if param_name in params and params[param_name] is not None:
                try:
                    converted_params[param_name] = euler_to_quaternion(params[param_name])
                except Exception as e:
                    # Provide a clear error message that references the specific parameter
                    raise ParameterValidationError(f"Failed to convert {param_name} Euler angles to Quaternion: {str(e)}")
        
        # Convert Color parameters
        for param_name in self.color_params:
            if param_name in params and params[param_name] is not None:
                try:
                    converted_params[param_name] = convert_color(params[param_name], param_name)
                except Exception as e:
                    # Provide a clear error message that references the specific parameter
                    raise ParameterValidationError(f"Failed to convert {param_name} to Color: {str(e)}")
        
        # Convert Rect parameters
        for param_name in self.rect_params:
            if param_name in params and params[param_name] is not None:
                try:
                    converted_params[param_name] = convert_rect(params[param_name], param_name)
                except Exception as e:
                    # Provide a clear error message that references the specific parameter
                    raise ParameterValidationError(f"Failed to convert {param_name} to Rect: {str(e)}")
        
        # Convert Bounds parameters
        for param_name in self.bounds_params:
            if param_name in params and params[param_name] is not None:
                try:
                    converted_params[param_name] = convert_bounds(params[param_name], param_name)
                except Exception as e:
                    # Provide a clear error message that references the specific parameter
                    raise ParameterValidationError(f"Failed to convert {param_name} to Bounds: {str(e)}")
        
        # Validate GameObject parameters
        for param_name in self.gameobject_params:
            if param_name in params and params[param_name] is not None:
                try:
                    validate_serialized_gameobject(params[param_name], param_name)
                except Exception as e:
                    # Provide a clear error message that references the specific parameter
                    raise ParameterValidationError(f"Invalid {param_name} GameObject: {str(e)}")
        
        # Validate Component parameters
        for param_name in self.component_params:
            if param_name in params and params[param_name] is not None:
                try:
                    validate_serialized_component(params[param_name], param_name)
                except Exception as e:
                    # Provide a clear error message that references the specific parameter
                    raise ParameterValidationError(f"Invalid {param_name} Component: {str(e)}")
        
        # Validate Transform parameters
        for param_name in self.transform_params:
            if param_name in params and params[param_name] is not None:
                try:
                    validate_serialized_transform(params[param_name], param_name)
                except Exception as e:
                    # Provide a clear error message that references the specific parameter
                    raise ParameterValidationError(f"Invalid {param_name} Transform: {str(e)}")
        
        # Allow subclasses to add more specific validation and conversion
        try:
            self.additional_validation(action, converted_params)
        except ParameterValidationError as e:
            # Pass through validation errors from additional_validation
            raise ParameterValidationError(str(e))
        except Exception as e:
            # Wrap other exceptions in ParameterValidationError
            raise ParameterValidationError(f"Validation error in additional_validation: {str(e)}")
        
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