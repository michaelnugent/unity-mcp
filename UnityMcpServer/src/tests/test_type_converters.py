import pytest
import math
from type_converters import (
    convert_vector2, convert_vector3, convert_quaternion,
    convert_color, convert_rect, convert_bounds, euler_to_quaternion
)
from exceptions import ParameterValidationError

class TestTypeConverters:
    """Tests for the Unity type converters."""

    def test_vector2_conversion(self):
        """Test Vector2 conversion with various input formats."""
        # Test list input
        result = convert_vector2([1, 2], "test_vec2")
        assert result == {"x": 1.0, "y": 2.0}
        
        # Test tuple input
        result = convert_vector2((3.5, 4.5), "test_vec2")
        assert result == {"x": 3.5, "y": 4.5}
        
        # Test dict input
        result = convert_vector2({"x": 5, "y": 6}, "test_vec2")
        assert result == {"x": 5.0, "y": 6.0}
        
        # Test invalid inputs
        with pytest.raises(ParameterValidationError):
            convert_vector2([1], "test_vec2")  # Too few components
            
        with pytest.raises(ParameterValidationError):
            convert_vector2([1, 2, 3], "test_vec2")  # Too many components
            
        with pytest.raises(ParameterValidationError):
            convert_vector2({"x": 1}, "test_vec2")  # Missing y component
            
        with pytest.raises(ParameterValidationError):
            convert_vector2("not_a_vector", "test_vec2")  # Wrong type

    def test_vector3_conversion(self):
        """Test Vector3 conversion with various input formats."""
        # Test list input
        result = convert_vector3([1, 2, 3], "test_vec3")
        assert result == {"x": 1.0, "y": 2.0, "z": 3.0}
        
        # Test tuple input
        result = convert_vector3((3.5, 4.5, 5.5), "test_vec3")
        assert result == {"x": 3.5, "y": 4.5, "z": 5.5}
        
        # Test dict input
        result = convert_vector3({"x": 5, "y": 6, "z": 7}, "test_vec3")
        assert result == {"x": 5.0, "y": 6.0, "z": 7.0}
        
        # Test invalid inputs
        with pytest.raises(ParameterValidationError):
            convert_vector3([1, 2], "test_vec3")  # Too few components
            
        with pytest.raises(ParameterValidationError):
            convert_vector3([1, 2, 3, 4], "test_vec3")  # Too many components
            
        with pytest.raises(ParameterValidationError):
            convert_vector3({"x": 1, "y": 2}, "test_vec3")  # Missing z component
            
        with pytest.raises(ParameterValidationError):
            convert_vector3("not_a_vector", "test_vec3")  # Wrong type

    def test_quaternion_conversion(self):
        """Test Quaternion conversion with various input formats."""
        # Test list input
        result = convert_quaternion([1, 2, 3, 4], "test_quat")
        assert result == {"x": 1.0, "y": 2.0, "z": 3.0, "w": 4.0}
        
        # Test tuple input
        result = convert_quaternion((0.5, 0.5, 0.5, 0.5), "test_quat")
        assert result == {"x": 0.5, "y": 0.5, "z": 0.5, "w": 0.5}
        
        # Test dict input
        result = convert_quaternion({"x": 0, "y": 0, "z": 0, "w": 1}, "test_quat")
        assert result == {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
        
        # Test invalid inputs
        with pytest.raises(ParameterValidationError):
            convert_quaternion([1, 2, 3], "test_quat")  # Too few components
            
        with pytest.raises(ParameterValidationError):
            convert_quaternion([1, 2, 3, 4, 5], "test_quat")  # Too many components
            
        with pytest.raises(ParameterValidationError):
            convert_quaternion({"x": 1, "y": 2, "z": 3}, "test_quat")  # Missing w component
            
        with pytest.raises(ParameterValidationError):
            convert_quaternion("not_a_quaternion", "test_quat")  # Wrong type

    def test_euler_to_quaternion(self):
        """Test Euler angles to Quaternion conversion."""
        # Test identity rotation (0,0,0)
        result = euler_to_quaternion([0, 0, 0])
        assert math.isclose(result["x"], 0.0, abs_tol=1e-6)
        assert math.isclose(result["y"], 0.0, abs_tol=1e-6)
        assert math.isclose(result["z"], 0.0, abs_tol=1e-6)
        assert math.isclose(result["w"], 1.0, abs_tol=1e-6)
        
        # Test 90 degrees around Y
        result = euler_to_quaternion([0, 90, 0])
        assert math.isclose(result["x"], 0.0, abs_tol=1e-6)
        assert math.isclose(result["y"], 0.7071068, abs_tol=1e-6)  # sin(45)
        assert math.isclose(result["z"], 0.0, abs_tol=1e-6)
        assert math.isclose(result["w"], 0.7071068, abs_tol=1e-6)  # cos(45)
        
        # Test with dict input
        result = euler_to_quaternion({"x": 90, "y": 0, "z": 0})
        assert math.isclose(result["x"], 0.7071068, abs_tol=1e-6)
        assert math.isclose(result["y"], 0.0, abs_tol=1e-6)
        assert math.isclose(result["z"], 0.0, abs_tol=1e-6)
        assert math.isclose(result["w"], 0.7071068, abs_tol=1e-6)

    def test_color_conversion(self):
        """Test Color conversion with various input formats."""
        # Test RGB list input
        result = convert_color([0.1, 0.2, 0.3], "test_color")
        assert result == {"r": 0.1, "g": 0.2, "b": 0.3, "a": 1.0}
        
        # Test RGBA list input
        result = convert_color([0.1, 0.2, 0.3, 0.4], "test_color")
        assert result == {"r": 0.1, "g": 0.2, "b": 0.3, "a": 0.4}
        
        # Test dict input with RGB
        result = convert_color({"r": 0.5, "g": 0.6, "b": 0.7}, "test_color")
        assert result == {"r": 0.5, "g": 0.6, "b": 0.7, "a": 1.0}
        
        # Test dict input with RGBA
        result = convert_color({"r": 0.5, "g": 0.6, "b": 0.7, "a": 0.8}, "test_color")
        assert result == {"r": 0.5, "g": 0.6, "b": 0.7, "a": 0.8}
        
        # Test value range validation
        with pytest.raises(ParameterValidationError):
            convert_color([1.1, 0.5, 0.5], "test_color")  # r > 1.0
            
        with pytest.raises(ParameterValidationError):
            convert_color([0.5, -0.1, 0.5], "test_color")  # g < 0.0

    def test_rect_conversion(self):
        """Test Rect conversion with various input formats."""
        # Test list input
        result = convert_rect([10, 20, 30, 40], "test_rect")
        assert result == {"x": 10.0, "y": 20.0, "width": 30.0, "height": 40.0}
        
        # Test dict input
        result = convert_rect({"x": 50, "y": 60, "width": 70, "height": 80}, "test_rect")
        assert result == {"x": 50.0, "y": 60.0, "width": 70.0, "height": 80.0}
        
        # Test invalid inputs
        with pytest.raises(ParameterValidationError):
            convert_rect([10, 20, 30], "test_rect")  # Too few components
            
        with pytest.raises(ParameterValidationError):
            convert_rect({"x": 10, "y": 20, "width": 30}, "test_rect")  # Missing height
            
        with pytest.raises(ParameterValidationError):
            convert_rect("not_a_rect", "test_rect")  # Wrong type

    def test_bounds_conversion(self):
        """Test Bounds conversion with various input formats."""
        # Test dict with nested vectors
        result = convert_bounds({
            "center": [1, 2, 3],
            "size": [4, 5, 6]
        }, "test_bounds")
        assert result == {
            "center": {"x": 1.0, "y": 2.0, "z": 3.0},
            "size": {"x": 4.0, "y": 5.0, "z": 6.0}
        }
        
        # Test dict with nested dicts
        result = convert_bounds({
            "center": {"x": 10, "y": 20, "z": 30},
            "size": {"x": 40, "y": 50, "z": 60}
        }, "test_bounds")
        assert result == {
            "center": {"x": 10.0, "y": 20.0, "z": 30.0},
            "size": {"x": 40.0, "y": 50.0, "z": 60.0}
        }
        
        # Test invalid inputs
        with pytest.raises(ParameterValidationError):
            convert_bounds({"center": [1, 2, 3]}, "test_bounds")  # Missing size
            
        with pytest.raises(ParameterValidationError):
            convert_bounds("not_bounds", "test_bounds")  # Wrong type 