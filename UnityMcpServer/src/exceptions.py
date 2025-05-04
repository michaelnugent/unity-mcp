"""
Custom exceptions for the Unity MCP server.

This module contains all custom exceptions used throughout the Unity MCP server.
Centralizing exceptions helps maintain consistency in error handling and maps to standard
JSON-RPC error codes as well as MCP protocol-specific error codes.
"""

# Standard JSON-RPC error codes
RPC_PARSE_ERROR = -32700
RPC_INVALID_REQUEST = -32600
RPC_METHOD_NOT_FOUND = -32601
RPC_INVALID_PARAMS = -32602
RPC_INTERNAL_ERROR = -32603
RPC_SERVER_ERROR_START = -32000
RPC_SERVER_ERROR_END = -32099

# MCP specific error codes (aligned with McpStatus)
MCP_ERROR_INCORRECT_PATH = 1000
MCP_ERROR_COMMUNICATION = 1001
MCP_ERROR_NO_RESPONSE = 1002
MCP_ERROR_MISSING_CONFIG = 1003
MCP_ERROR_UNSUPPORTED_OS = 1004
MCP_ERROR_GENERAL = 1099

# Unity MCP Server specific error codes (1100-1199)
MCP_PARAMETER_VALIDATION_ERROR = 1100
MCP_UNITY_COMMAND_ERROR = 1101
MCP_CONNECTION_ERROR = 1102
MCP_RESOURCE_NOT_FOUND = 1103
MCP_TYPE_CONVERSION_ERROR = 1104
MCP_FILE_ACCESS_ERROR = 1105
MCP_TOOL_EXECUTION_ERROR = 1106

class McpException(Exception):
    """Base exception class for all MCP-related errors.
    
    Provides common structure for error code, message, and data.
    """
    def __init__(self, message, code=RPC_INTERNAL_ERROR, data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

    def to_json_rpc_error(self):
        """Convert to a JSON-RPC error object."""
        error = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            error["data"] = self.data
        return error

# JSON-RPC standard errors
class JsonRpcParseError(McpException):
    """Invalid JSON was received."""
    def __init__(self, message="Parse error", data=None):
        super().__init__(message, RPC_PARSE_ERROR, data)

class JsonRpcInvalidRequestError(McpException):
    """The JSON sent is not a valid Request object."""
    def __init__(self, message="Invalid Request", data=None):
        super().__init__(message, RPC_INVALID_REQUEST, data)

class JsonRpcMethodNotFoundError(McpException):
    """The method does not exist / is not available."""
    def __init__(self, message="Method not found", data=None):
        super().__init__(message, RPC_METHOD_NOT_FOUND, data)

class JsonRpcInvalidParamsError(McpException):
    """Invalid method parameter(s)."""
    def __init__(self, message="Invalid params", data=None):
        super().__init__(message, RPC_INVALID_PARAMS, data)

class JsonRpcInternalError(McpException):
    """Internal JSON-RPC error."""
    def __init__(self, message="Internal error", data=None):
        super().__init__(message, RPC_INTERNAL_ERROR, data)

# Unity MCP Status errors (mapping to McpStatus enum)
class McpIncorrectPathError(McpException):
    """Configuration has incorrect paths."""
    def __init__(self, message="Configuration has incorrect paths", data=None):
        super().__init__(message, MCP_ERROR_INCORRECT_PATH, data)

class McpCommunicationError(McpException):
    """Connected but having communication issues."""
    def __init__(self, message="Communication error with Unity", data=None):
        super().__init__(message, MCP_ERROR_COMMUNICATION, data)

class McpNoResponseError(McpException):
    """Connected but not responding."""
    def __init__(self, message="No response from Unity", data=None):
        super().__init__(message, MCP_ERROR_NO_RESPONSE, data)

class McpMissingConfigError(McpException):
    """Config file exists but missing required elements."""
    def __init__(self, message="Missing configuration elements", data=None):
        super().__init__(message, MCP_ERROR_MISSING_CONFIG, data)

class McpUnsupportedOsError(McpException):
    """OS is not supported."""
    def __init__(self, message="Operating system is not supported", data=None):
        super().__init__(message, MCP_ERROR_UNSUPPORTED_OS, data)

class McpGeneralError(McpException):
    """General error state."""
    def __init__(self, message="General MCP error", data=None):
        super().__init__(message, MCP_ERROR_GENERAL, data)

# Unity MCP Server-specific errors
class ParameterValidationError(McpException):
    """Exception raised when command parameters fail validation."""
    def __init__(self, message="Parameter validation failed", data=None):
        super().__init__(message, MCP_PARAMETER_VALIDATION_ERROR, data)

class UnityCommandError(McpException):
    """Exception raised when Unity returns an error for a command."""
    def __init__(self, message="Unity command execution failed", data=None):
        super().__init__(message, MCP_UNITY_COMMAND_ERROR, data)

class ConnectionError(McpException):
    """Exception raised when there's an issue with the Unity connection."""
    def __init__(self, message="Failed to connect to Unity", data=None):
        super().__init__(message, MCP_CONNECTION_ERROR, data)

class ResourceNotFoundError(McpException):
    """Exception raised when a requested resource is not found."""
    def __init__(self, message="Resource not found", data=None):
        super().__init__(message, MCP_RESOURCE_NOT_FOUND, data)

class TypeConversionError(McpException):
    """Exception raised when a type conversion fails."""
    def __init__(self, message="Failed to convert parameter type", data=None):
        super().__init__(message, MCP_TYPE_CONVERSION_ERROR, data)

class FileAccessError(McpException):
    """Exception raised when file access fails."""
    def __init__(self, message="Failed to access file", data=None):
        super().__init__(message, MCP_FILE_ACCESS_ERROR, data)

class ToolExecutionError(McpException):
    """Exception raised when tool execution fails."""
    def __init__(self, message="Tool execution failed", data=None):
        super().__init__(message, MCP_TOOL_EXECUTION_ERROR, data) 