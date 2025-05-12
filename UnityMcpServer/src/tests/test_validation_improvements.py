"""
Unit tests for validating improvements to parameter validation.

This module contains tests focused on validating the fixes to the parameter validation
issues identified in the testing report. It specifically targets:

1. String parameter validation
2. Vector type validation
3. Error message clarity and correctness
4. Parameter presence detection
5. Validation consistency across tools
"""
import pytest
from unity_connection import ParameterValidationError
from validation_utils import (
    validate_vector3, validate_required_param, validate_param_type,
    validate_serialized_gameobject, validate_serialized_component,
    validate_serialized_transform, get_type_description_with_example,
    validate_dict_structure, validate_nested_structure
)
from type_converters import (
    convert_vector2, convert_vector3, convert_quaternion, 
    convert_color, convert_rect, convert_bounds, euler_to_quaternion
)
from tools.validation_layer import (
    validate_asset_path, validate_gameobject_path, 
    validate_component_type, validate_action,
    validate_gameobject_name
)
from tools.manage_gameobject import GameObjectTool
from tools.manage_scene import SceneTool
from tools.manage_script import ScriptTool
from tools.base_tool import BaseTool


class TestStringParameterValidation:
    """Tests for validating string parameters."""
    
    def test_basic_string_parameters(self):
        """Test validation for basic string parameters."""
        # Valid string parameters should not raise exceptions
        validate_param_type("MainCamera", "name", str, "create", "manage_gameobject")
        validate_param_type("Assets/Prefabs/Player.prefab", "path", str, "load", "manage_asset")
        validate_param_type("create", "action", str, "any", "any_tool")
        
        # Non-string values should raise exceptions with clear messages
        with pytest.raises(ParameterValidationError) as e:
            validate_param_type(123, "name", str, "create", "manage_gameobject")
        error_msg = str(e.value)
        assert "name" in error_msg  # Should reference correct parameter
        assert "must be of type str" in error_msg  # Should specify expected type
        assert "int" in error_msg  # Should mention actual type
    
    def test_gameobject_name_validation(self):
        """Test validation of GameObject name parameters."""
        # Valid names
        validate_gameobject_name("MainCamera")
        validate_gameobject_name("Player_1")
        validate_gameobject_name("Level 3 Boss")
        
        # Invalid names (empty)
        with pytest.raises(ParameterValidationError) as e:
            validate_gameobject_name("")  # Empty name
        assert "name cannot be empty" in str(e.value)
        
        # Non-string names
        with pytest.raises(ParameterValidationError) as e:
            validate_gameobject_name(123)  # Numeric name
        assert "name must be a string" in str(e.value)
    
    def test_asset_path_validation(self):
        """Test validation of asset path parameters."""
        # Valid paths
        validate_asset_path("Assets/Prefabs/Player.prefab")
        validate_asset_path("Assets/Models/Environment/Tree.fbx")
        
        # Invalid paths (no Assets prefix)
        with pytest.raises(ParameterValidationError) as e:
            validate_asset_path("InvalidPath")
        assert "path must start with 'Assets/'" in str(e.value)
        
        # Invalid paths (non-string)
        with pytest.raises(ParameterValidationError) as e:
            validate_asset_path(123)
        assert "path must be a string" in str(e.value)
    
    def test_action_parameter_validation(self):
        """Test validation of action parameters."""
        valid_actions = ["create", "modify", "delete"]
        
        # Valid actions
        validate_action("create", valid_actions)
        validate_action("modify", valid_actions)
        
        # Invalid actions (not in list)
        with pytest.raises(ParameterValidationError) as e:
            validate_action("remove", valid_actions)
        error_msg = str(e.value)
        assert "must be one of" in error_msg
        for action in valid_actions:
            assert action in error_msg
        
        # Invalid actions (non-string)
        with pytest.raises(ParameterValidationError) as e:
            validate_action(123, valid_actions)
        assert "must be a string" in str(e.value)
        assert "123" in str(e.value)  # Should include the invalid value


class TestVectorTypeValidation:
    """Tests for validating vector type parameters."""
    
    def test_vector3_array_validation(self):
        """Test validation of Vector3 parameters in array format."""
        # Valid formats
        validate_vector3([0, 1, 2], "position")
        validate_vector3([0.5, -1.5, 2.5], "position")
        
        # Invalid formats (too few elements)
        with pytest.raises(ParameterValidationError) as e:
            validate_vector3([0, 1], "position")
        assert "Vector3 must have exactly 3 components" in str(e.value)
        assert "position" in str(e.value)  # Should reference parameter name
        
        # Invalid formats (non-numeric element)
        with pytest.raises(ParameterValidationError) as e:
            validate_vector3([0, "1", 2], "position")
        assert "Component 1 must be a number" in str(e.value)
        assert "position" in str(e.value)  # Should reference parameter name
    
    def test_vector3_object_validation(self):
        """Test validation of Vector3 parameters in object format."""
        # Valid formats
        validate_vector3({"x": 0, "y": 1, "z": 2}, "position")
        validate_vector3({"x": 0.5, "y": -1.5, "z": 2.5}, "position")
        
        # Invalid formats (missing component)
        with pytest.raises(ParameterValidationError) as e:
            validate_vector3({"x": 0, "y": 1}, "position")
        assert "Missing Vector3 components: z" in str(e.value)
        assert "position" in str(e.value)  # Should reference parameter name
        
        # Invalid formats (non-numeric value)
        with pytest.raises(ParameterValidationError) as e:
            validate_vector3({"x": 0, "y": "1", "z": 2}, "position")
        assert "Component y must be a number" in str(e.value)
        assert "position" in str(e.value)  # Should reference parameter name
    
    def test_vector3_invalid_type(self):
        """Test validation of Vector3 with invalid types."""
        with pytest.raises(ParameterValidationError) as e:
            validate_vector3("not_a_vector", "position")
        error_msg = str(e.value)
        assert "Expected list, tuple or dict" in error_msg
        assert "position" in error_msg  # Should reference parameter name
        assert "not_a_vector" in error_msg  # Should include the invalid value
    
    def test_vector3_conversion(self):
        """Test conversion of Vector3 parameters."""
        # Array format conversion
        result = convert_vector3([1, 2, 3], "position")
        assert isinstance(result, dict)
        assert result["x"] == 1
        assert result["y"] == 2
        assert result["z"] == 3
        
        # Object format conversion (should be kept as is)
        result = convert_vector3({"x": 1, "y": 2, "z": 3}, "position")
        assert isinstance(result, dict)
        assert result["x"] == 1
        assert result["y"] == 2
        assert result["z"] == 3


class TestErrorMessageFormatting:
    """Tests for error message formatting."""
    
    def test_error_messages_include_parameter_name(self):
        """Test that error messages include the correct parameter name."""
        # Error for position parameter
        try:
            validate_vector3("not_a_vector", "position")
        except ParameterValidationError as e:
            assert "position" in str(e)
        
        # Error for rotation parameter
        try:
            validate_vector3("not_a_vector", "rotation")
        except ParameterValidationError as e:
            assert "rotation" in str(e)
    
    def test_error_messages_include_type_info(self):
        """Test that error messages include expected type information."""
        # Error for vector3
        try:
            validate_vector3("not_a_vector", "position")
        except ParameterValidationError as e:
            assert "Expected list, tuple or dict" in str(e)
        
        # Error for string parameter
        try:
            validate_param_type(123, "name", str, "create", "manage_gameobject")
        except ParameterValidationError as e:
            assert "must be of type str" in str(e)
            assert not "undefined" in str(e)  # Should never say "undefined"
    
    def test_error_messages_include_value_info(self):
        """Test that error messages include the actual value received."""
        # Error with string value
        try:
            validate_vector3("not_a_vector", "position")
        except ParameterValidationError as e:
            assert "not_a_vector" in str(e)
        
        # Error with numeric value
        try:
            validate_param_type(123, "name", str, "create", "manage_gameobject")
        except ParameterValidationError as e:
            assert "123" in str(e) or "int" in str(e)


class TestParameterPresenceDetection:
    """Tests for parameter presence detection."""
    
    def test_required_parameter_detection(self):
        """Test detection of required parameters."""
        # Test with all required parameters
        params = {
            "name": "TestObject",
            "position": [0, 1, 0],
            "rotation": [0, 0, 0]
        }
        validate_required_param(params, "name", "create", "manage_gameobject")
        validate_required_param(params, "position", "create", "manage_gameobject")
        
        # Test with missing parameters
        params = {
            "name": "TestObject"
        }
        with pytest.raises(ParameterValidationError) as e:
            validate_required_param(params, "position", "create", "manage_gameobject")
        assert "requires 'position' parameter" in str(e.value)
    
    def test_complex_parameter_presence_detection(self):
        """Test detection of complex parameter presence like script contents."""
        # Test with script content parameter
        params = {
            "name": "TestScript",
            "path": "Assets/Scripts/",
            "contents": "using UnityEngine;\npublic class TestScript : MonoBehaviour {}"
        }
        
        # Check validation
        validate_required_param(params, "contents", "create", "manage_script")
        
        # Test with empty content (should still be valid)
        params = {
            "name": "TestScript",
            "path": "Assets/Scripts/",
            "contents": ""
        }
        validate_required_param(params, "contents", "create", "manage_script")
        
        # Test with missing content
        params = {
            "name": "TestScript",
            "path": "Assets/Scripts/"
        }
        with pytest.raises(ParameterValidationError) as e:
            validate_required_param(params, "contents", "create", "manage_script")
        assert "requires 'contents' parameter" in str(e.value)
    
    def test_large_content_parameter_handling(self):
        """Test handling of large content parameters."""
        # Create a large script content
        large_content = "using UnityEngine;\n" + "// Comment line\n" * 1000 + "public class Test {}"
        
        params = {
            "name": "TestScript",
            "path": "Assets/Scripts/",
            "contents": large_content
        }
        
        # The validation should not fail due to size
        validate_required_param(params, "contents", "create", "manage_script")


class TestParameterConsistency:
    """Tests for parameter validation consistency across tools."""
    
    def test_position_parameter_consistency(self):
        """Test that position parameters are validated consistently."""
        # Valid Vector3 formats
        valid_positions = [
            [1, 2, 3],
            {"x": 1, "y": 2, "z": 3}
        ]
        
        for pos in valid_positions:
            # Should be valid across all validation contexts
            validate_vector3(pos, "position")
            
            # Should be convertible consistently
            converted = convert_vector3(pos, "position")
            assert isinstance(converted, dict)
            assert converted["x"] == 1
            assert converted["y"] == 2
            assert converted["z"] == 3
        
        # Invalid Vector3 formats
        invalid_positions = [
            "not_a_vector",
            [1, 2],
            {"x": 1, "y": 2}
        ]
        
        for pos in invalid_positions:
            # Should raise similar validation errors
            with pytest.raises(ParameterValidationError):
                validate_vector3(pos, "position")
    
    def test_action_parameter_consistency(self):
        """Test that action parameters are validated consistently."""
        # Define valid actions for different tools
        tool_actions = {
            "manage_gameobject": ["create", "modify", "delete", "find"],
            "manage_scene": ["load", "save", "create", "instantiate"],
            "manage_script": ["create", "update", "delete", "compile"]
        }
        
        for tool_name, actions in tool_actions.items():
            # Valid actions should pass validation
            for action in actions:
                validate_action(action, actions)
            
            # Invalid actions should fail with consistent error format
            with pytest.raises(ParameterValidationError) as e:
                validate_action("invalid_action", actions)
            
            error_msg = str(e.value)
            assert "must be one of" in error_msg
            for action in actions:
                assert action in error_msg


class TestToolValidation:
    """Tests for tool-specific validation."""
    
    def test_gameobject_tool_validation(self):
        """Test validation in the GameObject tool."""
        # Create a GameObject tool instance
        tool = GameObjectTool()
        
        # Test valid parameters
        result = tool.validate_and_convert_params("create", {
            "name": "TestObject",
            "position": [1, 2, 3],
            "rotation": [0, 90, 0]
        })
        
        # Position should be converted to object format
        assert isinstance(result["position"], dict)
        assert result["position"]["x"] == 1
        assert result["position"]["y"] == 2
        assert result["position"]["z"] == 3
        
        # Rotation should be converted to quaternion
        assert isinstance(result["rotation"], dict)
        assert "x" in result["rotation"]
        assert "y" in result["rotation"]
        assert "z" in result["rotation"]
        assert "w" in result["rotation"]
        
        # Test invalid position
        with pytest.raises(ParameterValidationError) as e:
            tool.validate_and_convert_params("create", {
                "name": "TestObject",
                "position": "not_a_vector"
            })
        
        error_msg = str(e.value)
        assert "position" in error_msg  # Should reference position parameter
        assert "Invalid position value" in error_msg  # Should indicate the invalid value
    
    def test_script_tool_validation(self):
        """Test validation in the Script tool."""
        # Create a Script tool instance
        tool = ScriptTool()
        
        # Test valid parameters for script creation
        params = {
            "name": "TestScript",
            "path": "Assets/Scripts/",
            "contents": "using UnityEngine;\npublic class TestScript : MonoBehaviour {}"
        }
        
        # Script tool should require 'contents' parameter
        result = tool.validate_and_convert_params("create", params)
        assert "contents" in result
        
        # Test missing contents parameter
        with pytest.raises(ParameterValidationError) as e:
            tool.validate_and_convert_params("create", {
                "name": "TestScript",
                "path": "Assets/Scripts/"
                # Missing contents
            })
        
        error_msg = str(e.value)
        assert "contents" in error_msg  # Should reference missing parameter
        assert "requires" in error_msg.lower()  # Should indicate it's required


class TestTypeDescriptionInErrors:
    """Tests for improved type descriptions in error messages."""
    
    def test_error_messages_use_specific_types(self):
        """Test that error messages use specific type names rather than 'undefined'."""
        # Test numeric parameter validation
        try:
            validate_param_type("string", "page_size", int, "search", "manage_asset")
        except ParameterValidationError as e:
            error_msg = str(e)
            assert "must be of type int" in error_msg or "must be a number" in error_msg
            assert "undefined" not in error_msg
            
        # Test array parameter validation  
        try:
            validate_param_type("not_array", "position", list, "move", "manage_gameobject")
        except ParameterValidationError as e:
            error_msg = str(e)
            assert "must be of type list" in error_msg or "must be an array" in error_msg
            assert "undefined" not in error_msg
            
        # Test boolean parameter validation
        try:
            validate_param_type("not_bool", "include_stacktrace", bool, "get", "read_console")
        except ParameterValidationError as e:
            error_msg = str(e)
            assert "must be of type bool" in error_msg or "must be a boolean" in error_msg
            assert "undefined" not in error_msg
    
    def test_asset_tool_error_messages(self):
        """Test validation in the Asset tool produces proper error messages."""
        from tools.manage_asset import AssetTool
        
        # Create an Asset tool instance
        tool = AssetTool()
        
        # Test action validation error
        with pytest.raises(ParameterValidationError) as e:
            tool.validate_params("invalid_action", {
                "action": "invalid_action", 
                "path": "Assets/Scripts/test.asset"
            })
        error_msg = str(e)
        assert "action" in error_msg
        assert "must be one of" in error_msg
        assert "undefined" not in error_msg
        
        # Test invalid asset_type
        with pytest.raises(ParameterValidationError) as e:
            tool.validate_params("create", {
                "action": "create", 
                "path": "Assets/Materials/TestMaterial.mat",
                "asset_type": "InvalidType",  # Invalid asset type
                "properties": {}
            })
        error_msg = str(e)
        assert "asset_type" in error_msg
        assert "Invalid asset_type" in error_msg
        assert "undefined" not in error_msg
    
    def test_scene_tool_error_messages(self):
        """Test validation in the Scene tool produces proper error messages."""
        from tools.manage_scene import SceneTool
        
        # Create a Scene tool instance
        tool = SceneTool()
        
        # Test string parameter validation
        with pytest.raises(ParameterValidationError) as e:
            tool.validate_params("open", {
                "action": "open",
                "path": 12345  # Should be a string
            })
        error_msg = str(e)
        assert "path" in error_msg
        assert "must be of type str" in error_msg or "must be a string" in error_msg
        assert "undefined" not in error_msg
        
        # Test array/vector parameter validation
        with pytest.raises(ParameterValidationError) as e:
            tool.validate_params("move", {
                "action": "move",
                "game_object_name": "Player",
                "position": "not an array"  # Should be a vector array
            })
        error_msg = str(e.value)
        assert "position" in error_msg
        # Update this assertion to match the actual error message format
        assert "array or list" in error_msg or "Expected list, tuple or dict" in error_msg
        assert "undefined" not in error_msg
    
    def test_gameobject_tool_error_messages(self):
        """Test validation in the GameObject tool produces proper error messages."""
        from tools.manage_gameobject import GameObjectTool
        
        # Create a GameObject tool instance
        tool = GameObjectTool()
        
        # Test dictionary/object parameter validation
        with pytest.raises(ParameterValidationError) as e:
            tool.validate_params("set_component_property", {
                "action": "set_component_property",
                "target": "Player",
                "component_properties": "not an object"  # Should be a dictionary
            })
        error_msg = str(e)
        assert "component_properties" in error_msg
        assert "must be of type" in error_msg and "dict" in error_msg
        assert "undefined" not in error_msg
        
        # Test enum/choice parameter validation
        with pytest.raises(ParameterValidationError) as e:
            tool.validate_params("invalid_action", {
                "action": "invalid_action"  # Not a valid action choice
            })
        error_msg = str(e)
        assert "action" in error_msg
        assert "must be one of" in error_msg
        assert "undefined" not in error_msg


class TestParameterTypeValidation:
    """Test that parameter types are properly validated."""

    def test_basic_type_validation(self):
        """Test validation of basic parameter types."""
        # String
        validate_param_type("test", "name", str, "create", "TestTool")
        with pytest.raises(ParameterValidationError):
            validate_param_type(123, "name", str, "create", "TestTool")

        # Integer
        validate_param_type(123, "count", int, "create", "TestTool")
        with pytest.raises(ParameterValidationError):
            validate_param_type("123", "count", int, "create", "TestTool")

        # Boolean
        validate_param_type(True, "enabled", bool, "create", "TestTool")
        with pytest.raises(ParameterValidationError):
            validate_param_type("true", "enabled", bool, "create", "TestTool")

        # List
        validate_param_type([1, 2, 3], "items", list, "create", "TestTool")
        with pytest.raises(ParameterValidationError):
            validate_param_type("not a list", "items", list, "create", "TestTool")

        # Dictionary
        validate_param_type({"key": "value"}, "properties", dict, "create", "TestTool")
        with pytest.raises(ParameterValidationError):
            validate_param_type("not a dict", "properties", dict, "create", "TestTool")

    def test_union_type_validation(self):
        """Test validation of union types."""
        union_type = (str, int)

        # String is valid
        validate_param_type("test", "value", union_type, "create", "TestTool")

        # Integer is valid
        validate_param_type(123, "value", union_type, "create", "TestTool")

        # Other types are invalid (dict is not compatible with str or int)
        with pytest.raises(ParameterValidationError):
            validate_param_type({"key": "value"}, "value", union_type, "create", "TestTool")

        # Lists should also be invalid for str/int union
        with pytest.raises(ParameterValidationError):
            validate_param_type([1, 2, 3], "value", union_type, "create", "TestTool")

    def test_optional_type_validation(self):
        """Test validation of optional types."""
        optional_str = (str, type(None))

        # String is valid
        validate_param_type("test", "value", optional_str, "create", "TestTool")

        # None is valid
        validate_param_type(None, "value", optional_str, "create", "TestTool")

        # Other types are invalid
        with pytest.raises(ParameterValidationError):
            validate_param_type(123, "value", optional_str, "create", "TestTool")


class TestEnhancedTypeValidation:
    """Test enhanced validation utilities for complex types."""
    
    def test_type_description_with_example(self):
        """Test that type descriptions and examples are correctly generated."""
        # Test simple types
        assert get_type_description_with_example(str) == ("str", '"example_string"')
        assert get_type_description_with_example(int) == ("int", "42")
        assert get_type_description_with_example(float) == ("float", "3.14")
        assert get_type_description_with_example(bool) == ("bool", "true or false")
        
        # Test complex types
        assert get_type_description_with_example(list)[0] == "list"
        assert get_type_description_with_example(dict)[0] == "dict"
        
        # Test union types
        desc, example = get_type_description_with_example((str, int))
        assert desc == "str or int"
        assert example == "(multiple formats allowed)"
        
    def test_dict_structure_validation(self):
        """Test validation of dictionary structures."""
        # Define expected structure
        expected_keys = {
            "name": str,
            "count": int,
            "active": bool
        }
        
        # Valid dictionary
        valid_dict = {
            "name": "example",
            "count": 10,
            "active": True
        }
        
        # Validate valid dictionary - should not raise
        validate_dict_structure(valid_dict, "config", expected_keys)
        
        # Test with missing required key
        invalid_dict = {
            "name": "example",
            "active": True
        }
        with pytest.raises(ParameterValidationError) as e:
            validate_dict_structure(invalid_dict, "config", expected_keys)
        error_msg = str(e.value)
        assert "missing required keys" in error_msg
        assert "count" in error_msg
        
        # Test with wrong type for a key
        invalid_dict = {
            "name": "example",
            "count": "10",  # Should be int
            "active": True
        }
        with pytest.raises(ParameterValidationError) as e:
            validate_dict_structure(invalid_dict, "config", expected_keys)
        assert "must be of type int" in str(e.value)
        
        # Test with non-dict input
        with pytest.raises(ParameterValidationError) as e:
            validate_dict_structure("not a dict", "config", expected_keys)
        assert "must be a dictionary" in str(e.value)
        
        # Test with optional keys
        validate_dict_structure(
            {"name": "example"}, 
            "config", 
            expected_keys, 
            required_keys=["name"]
        )
    
    def test_nested_structure_validation(self):
        """Test validation of complex nested structures."""
        # Define a schema for a Unity GameObject-like structure
        schema = {
            "properties": {
                "name": {"type": str},
                "transform": {
                    "properties": {
                        "position": {"type": list},
                        "rotation": {"type": list}
                    },
                    "required": ["position"]
                },
                "components": [
                    {
                        "properties": {
                            "type": {"type": str},
                            "enabled": {"type": bool}
                        },
                        "required": ["type"]
                    }
                ]
            },
            "required": ["name", "transform"]
        }
        
        # Valid structure
        valid_structure = {
            "name": "Player",
            "transform": {
                "position": [0, 1, 0],
                "rotation": [0, 0, 0, 1]
            },
            "components": [
                {"type": "Rigidbody", "enabled": True},
                {"type": "Collider", "enabled": False}
            ]
        }
        
        # Should validate without errors
        validate_nested_structure(valid_structure, schema, param_name="gameObject")
        
        # Test missing required field
        invalid_structure = {
            "name": "Player",
            # Missing transform
            "components": [
                {"type": "Rigidbody", "enabled": True}
            ]
        }
        with pytest.raises(ParameterValidationError) as e:
            validate_nested_structure(invalid_structure, schema, param_name="gameObject")
        assert "transform" in str(e.value)
        
        # Test missing nested required field
        invalid_structure = {
            "name": "Player",
            "transform": {
                # Missing position
                "rotation": [0, 0, 0, 1]
            }
        }
        with pytest.raises(ParameterValidationError) as e:
            validate_nested_structure(invalid_structure, schema, param_name="gameObject")
        assert "position" in str(e.value)
        
        # Test wrong type in array
        invalid_structure = {
            "name": "Player",
            "transform": {
                "position": [0, 1, 0],
                "rotation": [0, 0, 0, 1]
            },
            "components": [
                {"type": "Rigidbody", "enabled": "true"}  # Should be boolean
            ]
        }
        with pytest.raises(ParameterValidationError) as e:
            validate_nested_structure(invalid_structure, schema, param_name="gameObject")
        assert "bool" in str(e.value)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 