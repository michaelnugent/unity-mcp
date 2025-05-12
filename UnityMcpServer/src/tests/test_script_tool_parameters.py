import pytest
from tools.manage_script import ScriptTool
from exceptions import ParameterValidationError
import base64

class TestScriptToolParameterHandling:
    """Tests for script tool parameter handling, especially content parameter."""
    
    def setup_method(self):
        """Set up a ScriptTool instance for each test."""
        self.script_tool = ScriptTool()
    
    def test_content_parameter_detection(self):
        """Test that the content parameter is properly detected when provided."""
        
        # Valid parameters with content
        params = {
            "action": "create",
            "name": "TestScript",
            "path": "Assets/Scripts",
            "script_type": "MonoBehaviour",
            "namespace": "",
            "contents": "using UnityEngine;\n\npublic class TestScript : MonoBehaviour {}"
        }
        
        # This should not raise an exception about missing content parameter
        try:
            self.script_tool.validate_and_convert_params("create", params)
        except ParameterValidationError as e:
            assert False, f"Unexpectedly raised error: {str(e)}"
    
    def test_encoded_content_parameter(self):
        """Test handling of base64 encoded content parameters."""
        
        # Script content
        content = "using UnityEngine;\n\npublic class TestScript : MonoBehaviour {}"
        
        # Encode content
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        # Parameters with encoded contents
        params = {
            "action": "create",
            "name": "TestScript",
            "path": "Assets/Scripts",
            "script_type": "MonoBehaviour",
            "namespace": "",
            "contents": encoded_content,
            "contents_encoded": True
        }
        
        # This should not raise an exception about missing content parameter
        try:
            self.script_tool.validate_and_convert_params("create", params)
        except ParameterValidationError as e:
            assert False, f"Unexpectedly raised error: {str(e)}"
    
    def test_large_content_parameter(self):
        """Test handling of large script content parameters."""
        
        # Create a large content string
        large_content = "using UnityEngine;\n\n" + ("// Comment line\n" * 1000) + "public class TestScript : MonoBehaviour {}"
        
        params = {
            "action": "create",
            "name": "TestScript",
            "path": "Assets/Scripts",
            "script_type": "MonoBehaviour",
            "namespace": "",
            "contents": large_content
        }
        
        # This should not raise an exception about missing content parameter
        try:
            self.script_tool.validate_and_convert_params("create", params)
        except ParameterValidationError as e:
            assert False, f"Unexpectedly raised error: {str(e)}"
    
    def test_missing_content_parameter(self):
        """Test that a proper error is raised when content parameter is missing."""
        
        # Parameters without content
        params = {
            "action": "create",
            "name": "TestScript",
            "path": "Assets/Scripts",
            "script_type": "MonoBehaviour",
            "namespace": ""
            # Missing contents
        }
        
        # Should raise an exception that correctly mentions missing contents parameter
        with pytest.raises(ParameterValidationError) as e:
            self.script_tool.validate_and_convert_params("create", params)
        
        error_msg = str(e.value)
        assert "contents" in error_msg, f"Error message doesn't mention missing contents parameter: {error_msg}"
        assert "requires" in error_msg.lower(), f"Error message doesn't indicate contents is required: {error_msg}"
        assert "undefined" not in error_msg, f"Error message uses 'undefined' type: {error_msg}" 