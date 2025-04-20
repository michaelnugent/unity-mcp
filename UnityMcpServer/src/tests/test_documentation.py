import pytest
import inspect
import importlib
import sys
import os
from pathlib import Path
import re

# Add the src directory to the Python path so we can import modules
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import all tools modules
from tools import (
    manage_script,
    manage_scene,
    manage_editor,
    manage_gameobject,
    manage_asset,
    read_console,
    execute_menu_item,
    manage_prefabs,
)

# List of all modules to check
MODULES = [
    manage_script,
    manage_scene,
    manage_editor,
    manage_gameobject,
    manage_asset,
    read_console,
    execute_menu_item,
    manage_prefabs,
]

def get_tool_functions(module):
    """Extract functions that are decorated with @mcp.tool()"""
    # Simple heuristic: Look for functions in the module that have docstrings
    # and are not helper functions (don't start with _)
    return [
        func for name, func in inspect.getmembers(module, inspect.isfunction)
        if not name.startswith('_') and func.__doc__ and 
        (name != 'register_all_tools' and 
         not name.startswith('register_') and 
         not name.endswith('_tools') and
         name != 'TypedDict')  # Exclude TypedDict which is a type hint, not a tool
    ]

def test_all_tools_have_docstrings():
    """Test that all tool functions have docstrings."""
    for module in MODULES:
        tools = get_tool_functions(module)
        for tool in tools:
            assert tool.__doc__, f"Tool {tool.__name__} in {module.__name__} is missing a docstring"

def test_docstring_has_required_sections():
    """Test that all tool docstrings have the required sections."""
    required_sections = ["Args:", "Returns:"]
    recommended_sections = ["Examples:"]
    
    for module in MODULES:
        tools = get_tool_functions(module)
        for tool in tools:
            docstring = tool.__doc__
            
            # Check for required sections
            for section in required_sections:
                assert section in docstring, f"Tool {tool.__name__} in {module.__name__} is missing required section '{section}'"
            
            # Print warning for recommended sections
            for section in recommended_sections:
                if section not in docstring:
                    print(f"Warning: Tool {tool.__name__} in {module.__name__} is missing recommended section '{section}'")

def test_args_match_parameters():
    """Test that all parameters in the function signature are documented in the Args section."""
    for module in MODULES:
        tools = get_tool_functions(module)
        for tool in tools:
            # Get function parameters
            signature = inspect.signature(tool)
            parameters = list(signature.parameters.keys())
            
            # Skip 'ctx' parameter as it's a common MCP context parameter
            if 'ctx' in parameters:
                parameters.remove('ctx')
            
            # Extract Args section from docstring
            docstring = tool.__doc__
            args_section_match = re.search(r'Args:(.*?)(?:Returns:|Examples:|$)', docstring, re.DOTALL)
            
            if args_section_match:
                args_section = args_section_match.group(1)
                
                # Check if each parameter is documented
                for param in parameters:
                    param_pattern = fr'^\s*{param}:'
                    assert re.search(param_pattern, args_section, re.MULTILINE), \
                        f"Parameter '{param}' for tool {tool.__name__} in {module.__name__} is not documented in Args section"
            else:
                assert False, f"Could not find Args section in {tool.__name__} in {module.__name__}"

def test_return_section_content():
    """Test that the Returns section has meaningful content."""
    for module in MODULES:
        tools = get_tool_functions(module)
        for tool in tools:
            docstring = tool.__doc__
            
            # Extract Returns section
            returns_match = re.search(r'Returns:(.*?)(?:Examples:|$)', docstring, re.DOTALL)
            assert returns_match, f"Could not find Returns section in {tool.__name__} in {module.__name__}"
            
            # Check that Returns section has meaningful content (more than 10 characters)
            returns_content = returns_match.group(1).strip()
            assert len(returns_content) > 10, \
                f"Returns section for {tool.__name__} in {module.__name__} is too short or empty"

if __name__ == "__main__":
    # This allows the file to be run directly for quick testing
    pytest.main(["-xvs", __file__]) 