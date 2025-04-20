"""
Custom exceptions for the Unity MCP server.

This module contains all custom exceptions used throughout the Unity MCP server.
Centralizing exceptions helps maintain consistency in error handling.
"""

class ParameterValidationError(Exception):
    """Exception raised when command parameters fail validation."""
    pass

class UnityCommandError(Exception):
    """Exception raised when Unity returns an error for a command."""
    pass

class ConnectionError(Exception):
    """Exception raised when there's an issue with the Unity connection."""
    pass 