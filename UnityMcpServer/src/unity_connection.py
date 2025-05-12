import socket
import json
import logging
import sys
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple, Union
from config import config
from exceptions import ParameterValidationError, UnityCommandError, ConnectionError

# Configure logging using settings from config
# Explicitly use stderr for logging since stdout is used for protocol communication
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format=config.log_format,
    stream=sys.stderr  # Force all logs to stderr
)
logger = logging.getLogger("unity-mcp-server")

# Maximum number of retries for sending commands
MAX_RETRIES = config.max_retries
# Time to wait between retries
RETRY_WAIT = config.retry_delay

@dataclass
class UnityConnection:
    """Manages the socket connection to the Unity Editor."""
    host: str = config.unity_host
    port: int = config.unity_port
    sock: socket.socket = None  # Socket for Unity communication

    def __init__(self, host='localhost', port=6400, sock=None):
        """Initialize a connection to the Unity Editor.
        
        Args:
            host: The hostname or IP address where Unity is running
            port: The port number Unity is listening on
            sock: An optional existing socket to use
        """
        self.host = host
        self.port = port
        self.sock = sock or self._connect()
        logger.info(f"Connected to Unity at {host}:{port}")

    def _connect(self):
        """Create a new socket connection to Unity."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            return sock
        except socket.error as e:
            raise ConnectionError(f"Failed to connect to Unity at {self.host}:{self.port}: {str(e)}")

    def connect(self) -> bool:
        """Establish a connection to the Unity Editor."""
        if self.sock:
            return True
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Unity at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to on {self.host}:{self.port}")
            logger.error(f"Failed to connect to Unity: {str(e)}")
            self.sock = None
            return False

    def disconnect(self):
        """Close the connection to the Unity Editor."""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Unity: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=config.buffer_size) -> bytes:
        """Receive a complete response from Unity, handling chunked data."""
        chunks = []
        sock.settimeout(config.connection_timeout)  # Use timeout from config
        try:
            while True:
                chunk = sock.recv(buffer_size)
                if not chunk:
                    if not chunks:
                        raise ConnectionError("Connection closed before receiving data")
                    break
                chunks.append(chunk)
                
                # Process the data received so far
                data = b''.join(chunks)
                decoded_data = data.decode('utf-8')
                
                # Check if we've received a complete response
                try:
                    # Special case for ping-pong
                    if decoded_data.strip().startswith('{"status":"success","result":{"message":"pong"'):
                        logger.debug("Received ping response")
                        return data
                    
                    # Handle escaped quotes in the content
                    if '"content":' in decoded_data:
                        # Find the content field and its value
                        content_start = decoded_data.find('"content":') + 9
                        content_end = decoded_data.rfind('"', content_start)
                        if content_end > content_start:
                            # Replace escaped quotes in content with regular quotes
                            content = decoded_data[content_start:content_end]
                            content = content.replace('\\"', '"')
                            decoded_data = decoded_data[:content_start] + content + decoded_data[content_end:]
                    
                    # Validate JSON format
                    json.loads(decoded_data)
                    
                    # If we get here, we have valid JSON
                    logger.info(f"Received complete response ({len(data)} bytes)")
                    return data
                except json.JSONDecodeError:
                    # We haven't received a complete valid JSON response yet
                    continue
                except Exception as e:
                    logger.warning(f"Error processing response chunk: {str(e)}")
                    # Continue reading more chunks as this might not be the complete response
                    continue
        except socket.timeout:
            logger.warning("Socket timeout during receive")
            raise ConnectionError("Timeout receiving Unity response")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Unity and return its response.
        
        This method includes retry logic with exponential backoff to handle
        temporary connection issues with Unity.
        
        Args:
            command_type: The type of command to send
            params: The parameters for the command
            
        Returns:
            The response from Unity
            
        Raises:
            ConnectionError: If unable to connect to Unity after retries
            UnityCommandError: If Unity returns an error
        """
        # Make sure params is at least an empty dict
        params = params or {}
        
        retry_count = 0
        last_exception = None
        retry_delay = RETRY_WAIT
        
        while retry_count <= MAX_RETRIES:
            try:
                # Make sure we're connected
                if not self.sock and not self.connect():
                    raise ConnectionError("Not connected to Unity")
                
                # Special handling for ping command
                if command_type == "ping":
                    logger.debug("Sending ping to verify connection")
                    self.sock.sendall(b"ping")
                    response_data = self.receive_full_response(self.sock)
                    response = json.loads(response_data.decode('utf-8'))
                    
                    if response.get("status") != "success":
                        logger.warning("Ping response was not successful")
                        self.sock = None
                        raise ConnectionError("Connection verification failed")
                        
                    return {"message": "pong"}
                
                # Normal command handling
                command = {"type": command_type, "params": params}
                
                # Check for very large content that might cause JSON issues
                command_size = len(json.dumps(command))
                
                if command_size > config.buffer_size / 2:
                    logger.warning(f"Large command detected ({command_size} bytes). This might cause issues.")
                    
                logger.info(f"Sending command: {command_type} with params size: {command_size} bytes")
                
                # Ensure we have a valid JSON string before sending
                command_json = json.dumps(command, ensure_ascii=False)
                self.sock.sendall(command_json.encode('utf-8'))
                
                response_data = self.receive_full_response(self.sock)
                try:
                    response = json.loads(response_data.decode('utf-8'))
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decode error: {str(je)}")
                    # Log partial response for debugging
                    partial_response = response_data.decode('utf-8')[:500] + "..." if len(response_data) > 500 else response_data.decode('utf-8')
                    logger.error(f"Partial response: {partial_response}")
                    raise UnityCommandError(f"Invalid JSON response from Unity: {str(je)}")
                
                if response.get("status") == "error":
                    error_message = response.get("error") or response.get("message", "Unknown Unity error")
                    logger.error(f"Unity error: {error_message}")
                    raise UnityCommandError(error_message)
                
                # Success! Return the result
                return response.get("result", {})
            
            except UnityCommandError:
                # Don't retry for command errors (these are expected to fail consistently)
                raise
                
            except (ConnectionError, socket.error) as e:
                last_exception = e
                self.sock = None
                
                if retry_count < MAX_RETRIES:
                    retry_count += 1
                    logger.warning(f"Connection to Unity failed. Retry {retry_count}/{MAX_RETRIES} in {retry_delay:.2f}s: {str(e)}")
                    
                    # Sleep with exponential backoff
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    
                    # Try to reconnect before next retry
                    try:
                        logger.info("Attempting to reconnect to Unity...")
                        self.reconnect()
                    except Exception as reconnect_error:
                        logger.warning(f"Reconnection attempt failed: {str(reconnect_error)}")
                else:
                    # We've reached max retries
                    logger.error(f"Failed to communicate with Unity after {MAX_RETRIES} retries: {str(e)}")
                    raise ConnectionError(f"Failed to communicate with Unity after {MAX_RETRIES} retries: {str(last_exception)}")
                    
            except Exception as e:
                last_exception = e
                self.sock = None
                
                if retry_count < MAX_RETRIES:
                    retry_count += 1
                    logger.warning(f"Communication error with Unity. Retry {retry_count}/{MAX_RETRIES} in {retry_delay:.2f}s: {str(e)}")
                    
                    # Sleep with exponential backoff
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    
                    # Try to reconnect before next retry
                    try:
                        logger.info("Attempting to reconnect to Unity...")
                        self.reconnect()
                    except Exception as reconnect_error:
                        logger.warning(f"Reconnection attempt failed: {str(reconnect_error)}")
                else:
                    # We've reached max retries
                    logger.error(f"Communication error with Unity after {MAX_RETRIES} retries: {str(e)}")
                    raise ConnectionError(f"Failed to communicate with Unity after {MAX_RETRIES} retries: {str(last_exception)}")
        
        # This should never be reached due to the raises above, but just in case
        raise ConnectionError(f"Failed to communicate with Unity: Maximum retries exceeded")

    def reconnect(self):
        """Reestablish the connection to Unity if it was lost.
        
        This method will attempt to create a new socket connection, and update
        the internal socket reference if successful.
        
        Returns:
            bool: True if reconnection was successful, False otherwise
            
        Raises:
            ConnectionError: If unable to reconnect to Unity
        """
        # Close the existing socket if it exists
        if self.sock:
            try:
                self.sock.close()
            except:
                pass  # Ignore errors closing the socket
                
        # Create a new connection
        self.sock = self._connect()
        logger.info(f"Reconnected to Unity at {self.host}:{self.port}")
        return True

# Global Unity connection
_unity_connection = None

def get_unity_connection() -> UnityConnection:
    """Retrieve or establish a persistent Unity connection.
    
    This function will try to reconnect to Unity with exponential backoff
    if the initial connection fails. It will make up to config.max_retries attempts
    before giving up.
    
    Args:
        None: This function takes no parameters
        
    Returns:
        UnityConnection: A connected UnityConnection instance ready for use
        
    Raises:
        ConnectionError: If unable to connect to Unity after retries
    """
    global _unity_connection
    
    # Try to use existing connection
    if _unity_connection is not None:
        try:
            # Try to ping with a short timeout to verify connection
            result = _unity_connection.send_command("ping")
            # If we get here, the connection is still valid
            logger.debug("Reusing existing Unity connection")
            return _unity_connection
        except Exception as e:
            logger.warning(f"Existing connection failed: {str(e)}")
            try:
                _unity_connection.disconnect()
            except:
                pass
            _unity_connection = None
    
    # Create a new connection with retries
    retry_count = 0
    last_exception = None
    retry_delay = config.retry_delay
    
    while retry_count <= config.max_retries:
        try:
            logger.info(f"Creating new Unity connection (attempt {retry_count + 1}/{config.max_retries + 1})")
            _unity_connection = UnityConnection(host=config.unity_host, port=config.unity_port)
            
            if not _unity_connection.connect():
                raise ConnectionError(f"Failed to connect to Unity at {config.unity_host}:{config.unity_port}")
            
            # Verify the new connection works
            _unity_connection.send_command("ping")
            logger.info("Successfully established new Unity connection")
            return _unity_connection
            
        except Exception as e:
            last_exception = e
            
            # Clean up any failed connection
            if _unity_connection:
                try:
                    _unity_connection.disconnect()
                except:
                    pass
                _unity_connection = None
            
            if retry_count < config.max_retries:
                retry_count += 1
                logger.warning(f"Connection to Unity failed. Retry {retry_count}/{config.max_retries} in {retry_delay:.2f}s: {str(e)}")
                
                # Sleep with exponential backoff
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                # We've reached max retries
                logger.error(f"Could not establish Unity connection after {config.max_retries} retries: {str(e)}")
                raise ConnectionError(f"Could not establish valid Unity connection after {config.max_retries} retries: {str(last_exception)}")
    
    # This should never be reached due to the raises above, but just in case
    raise ConnectionError("Could not establish Unity connection: Maximum retries exceeded")
