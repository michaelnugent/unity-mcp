"""
Base class for all Unity MCP tools with shared validation logic.
"""
import asyncio
from typing import Dict, Any, Optional, Type, List, Tuple, Union
from unity_connection import get_unity_connection, ParameterValidationError
from validation_utils import (
    validate_required_param, validate_param_type,
    validate_serialized_gameobject, validate_serialized_component, 
    validate_serialized_transform, validate_serialization_status,
    enhance_error_with_documentation
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
            # Collect all missing required parameters
            missing_params = []
            
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
                            missing_params.append(param_name)
                    else:
                        # Traditional validation
                        missing_params.append(param_name)
                
                # Validate parameter type
                elif param_name in converted_params and converted_params[param_name] is not None:
                    validate_param_type(
                        converted_params[param_name], param_name, param_type, action, self.tool_name
                    )
            
            # If there are missing parameters, raise error with all of them
            if missing_params:
                missing_params_str = "', '".join(missing_params)
                raise ParameterValidationError(
                    f"{self.tool_name} '{action}' action requires '{missing_params_str}' parameter"
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
    
    def _handle_command_params(self, command_type: str, params: Dict[str, Any] = None) -> Tuple[Dict[str, Any], bool, str]:
        """Helper method to handle parameter validation and prepare for command execution.
        
        This is an internal method that extracts common code from send_command and can be reused by
        subclasses that override send_command to implement local handling.
        
        Args:
            command_type: The type of command to send
            params: The parameters for the command
            
        Returns:
            Tuple containing:
            - Dict[str, Any]: Converted parameters
            - bool: Whether this is a validation-only request
            - str: The action being performed
            
        Raises:
            ParameterValidationError: If parameters fail validation
        """
        # Clone params to avoid modifying the original
        params = params.copy() if params else {}
        
        # Extract action if present (preserve original case for validation later)
        original_action = params.get("action", "")
        action = original_action.lower() if original_action else ""
        
        # Store original action for validation errors
        if original_action and original_action != action:
            params["original_action"] = original_action
        
        # Update action to lowercase in params
        if "action" in params:
            params["action"] = action
        
        # Check if this is a validation-only request
        validate_only = params.get("validateOnly", False)
        
        # Validate and convert parameters
        try:
            converted_params = self.validate_and_convert_params(action, params)
            
            # For validation-only mode, we might return here without sending to Unity
            if validate_only and not self.needs_unity_validation(action, converted_params):
                return converted_params, validate_only, action
            
            # Use the converted parameters
            return converted_params, validate_only, action
            
        except Exception as e:
            # Always create enhanced error response for parameter validation errors
            error_response = enhance_error_with_documentation(
                str(e),
                self.tool_name,
                action=action,
                parameter_format_class=self.parameter_format
            )
            
            if validate_only:
                # For validation-only mode, wrap the enhanced response
                raise ParameterValidationError(error_response)
            
            # For non-validation requests, use the enhanced error message
            raise ParameterValidationError(error_response)
    
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
        try:
            # Use the helper method to handle parameters
            converted_params, validate_only, action = self._handle_command_params(command_type, params)
            
            # If validation only and no Unity validation needed, return success
            if validate_only and not self.needs_unity_validation(action, converted_params):
                return {
                    "success": True, 
                    "message": "Parameters validated successfully", 
                    "data": {"valid": True}
                }
            
            # Send command using the Unity connection
            response = self.unity_conn.send_command(command_type, converted_params)
            
            # Post-process serialized Unity objects if needed
            if isinstance(response, dict) and 'data' in response:
                response = self.post_process_response(response, action, converted_params)
                
            return response
            
        except ParameterValidationError as e:
            # If this is a wrapped error response, unwrap and return it
            if hasattr(e, 'error_response') and e.error_response:
                return e.error_response
            
            # Otherwise re-raise
            raise
    
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