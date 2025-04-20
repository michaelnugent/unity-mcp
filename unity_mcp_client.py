#!/usr/bin/env python3
import json
import subprocess
import sys
import time
import select
import argparse
import uuid
import socket
import asyncio
import logging
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import JSONRPCMessage, JSONRPCRequest
from fastmcp import FastMCP, Client
from fastmcp.client.transports import PythonStdioTransport, SSETransport
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Change to DEBUG for more detailed logs
logger = logging.getLogger(__name__)

def check_unity_connection(host="localhost", port=6400, timeout=2):
    """Check if Unity Editor is running and listening on the specified port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return True, "Unity Editor is running and accessible"
        else:
            return False, f"Unity Editor is not accessible on {host}:{port} (error code: {result})"
    except Exception as e:
        return False, f"Error checking Unity connection: {str(e)}"

def create_json_rpc_request(method, params=None, request_id=None):
    """Create a properly formatted JSON-RPC request."""
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": {} if params is None else params
    }

async def run_mcp_client(args):
    """Run MCP client using the official MCP SDK"""
    # Direct process parameters
    server_path = "UnityMcpServer/src/server.py"
    python_path = "/home/mike/code/unity/unity-mcp/venv/bin/python"
    
    logger.info(f"Starting server directly")
    
    # Directly start the server process to have more control
    server_cmd = [
        python_path,
        server_path,
        "--unity-host", args.unity_host,
        "--unity-port", str(args.unity_port),
        "--log-level", "DEBUG"
    ]
    
    logger.debug(f"Command: {' '.join(server_cmd)}")
    
    process = await asyncio.create_subprocess_exec(
        *server_cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    logger.info(f"Server process started with PID: {process.pid}")
    
    # Give the server a moment to start up
    await asyncio.sleep(1)
    
    try:
        # Create the initialization request
        init_params = {
            "clientInfo": {
                "name": "unity-mcp-test-client",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {
                    "listChanged": True
                }
            }
        }
        
        init_request = create_json_rpc_request("initialize", init_params)
        init_json = json.dumps(init_request)
        
        logger.info(f"Sending initialization request: {init_json}")
        process.stdin.write((init_json + "\n").encode())
        await process.stdin.drain()
        
        # Read initialization response
        init_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=args.timeout)
        init_response_str = init_response_line.decode().strip()
        logger.info(f"Received initialization response: {init_response_str}")
        
        try:
            init_response = json.loads(init_response_str)
            logger.info(f"Initialization successful: {init_response}")
            
            # Only continue if not just initializing
            if args.method != "initialize":
                # Parse user parameters if provided
                params = {}
                if args.params:
                    try:
                        params = json.loads(args.params)
                    except json.JSONDecodeError:
                        logger.warning(f"Parameters not valid JSON: {args.params}")
                        logger.warning("Using empty parameters instead")
                
                # Create the method request
                request = create_json_rpc_request(args.method, params)
                request_json = json.dumps(request)
                
                logger.info(f"Sending {args.method} request: {request_json}")
                process.stdin.write((request_json + "\n").encode())
                await process.stdin.drain()
                
                # Read method response
                method_response_line = await asyncio.wait_for(process.stdout.readline(), timeout=args.timeout)
                method_response_str = method_response_line.decode().strip()
                logger.info(f"Received method response: {method_response_str}")
                
                try:
                    method_response = json.loads(method_response_str)
                    
                    # Print formatted response
                    print("\nResponse result:")
                    print(json.dumps(method_response.get("result", {}), indent=2))
                    
                    # Special formatting for tools/list
                    if args.method == "tools/list" and "tools" in method_response.get("result", {}):
                        print("\nAvailable Unity MCP Tools:")
                        for tool in method_response["result"]["tools"]:
                            print(f"\n  {tool.get('name', 'Unknown')}")
                            print(f"  Description: {tool.get('description', 'No description')}")
                            if "parameters" in tool:
                                print(f"  Parameters:")
                                print(json.dumps(tool["parameters"], indent=4))
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse method response: {e}")
                    print(f"Received non-JSON response: {method_response_str}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse initialization response: {e}")
            print(f"Received non-JSON response: {init_response_str}")
    
    except asyncio.TimeoutError:
        logger.error(f"Timeout: No response received after {args.timeout} seconds")
    
    except Exception as e:
        logger.error(f"Error communicating with MCP server: {e}")
        
        # Check if there's any stderr output that might explain the issue
        stderr_data = await process.stderr.read(10000)
        if stderr_data:
            logger.error(f"Server stderr output: {stderr_data.decode()}")
    
    finally:
        # Read any remaining stderr for debugging
        stderr_data = await process.stderr.read(10000)
        if stderr_data:
            logger.debug(f"Final server stderr output: {stderr_data.decode()}")
            
        # Make sure to terminate the process
        if process.returncode is None:
            logger.info("Terminating server process")
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except asyncio.TimeoutError:
                logger.warning("Server didn't terminate gracefully, killing it")
                process.kill()
                await process.wait()
        else:
            logger.info(f"Server already terminated with exit code: {process.returncode}")

def run_fastmcp_proxy(args):
    """Run FastMCP proxy for the Unity MCP server"""
    logger.info("Starting FastMCP proxy for Unity MCP server")
    
    # Set necessary environment variables for the server script
    os.environ["UNITY_HOST"] = args.unity_host
    os.environ["UNITY_PORT"] = str(args.unity_port)
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Create a client connection to the original server
    unity_client = Client(
        transport=PythonStdioTransport(
            'UnityMcpServer/src/server.py',
            python_cmd="/home/mike/code/unity/unity-mcp/venv/bin/python"
        )
    )

    # Create a proxy server that exposes the same capabilities
    proxy = FastMCP.from_client(unity_client, name="Unity MCP Proxy")
    
    # Run the proxy server with SSE transport
    print(f"Starting FastMCP proxy server for Unity MCP on http://127.0.0.1:{args.sse_port}")
    print(f"Unity connection: {args.unity_host}:{args.unity_port}")
    print(f"You can now connect to this proxy server using an MCP client.")
    
    # Use the simple transport name with no extra parameters
    proxy.run('sse')

async def run_fastmcp_client(args):
    """Connect directly to the Unity MCP server using FastMCP client"""
    logger.info("Connecting to Unity MCP server using FastMCP client...")
    
    # Create a client that connects directly to the Unity MCP server
    async with Client(
        transport=PythonStdioTransport(
            'UnityMcpServer/src/server.py',
            python_cmd="/home/mike/code/unity/unity-mcp/venv/bin/python",
            env={
                "UNITY_HOST": args.unity_host,
                "UNITY_PORT": str(args.unity_port),
                "LOG_LEVEL": "DEBUG"
            }
        )
    ) as client:
        # Client is already initialized by the context manager
        logger.info("Client connected successfully")
        
        if args.method == "tools/list":
            # List available tools using the FastMCP client's list_tools method
            tools = await client.list_tools()
            
            print("\n\033[1;36mAvailable Unity MCP Tools:\033[0m")
            for tool in tools:
                print(f"\n  \033[1;32m{tool.name}\033[0m")
                print(f"  \033[1;33mDescription:\033[0m {tool.description}")
                if hasattr(tool, "parameters") and hasattr(tool.parameters, "properties"):
                    print(f"  \033[1;33mParameters:\033[0m")
                    # Print each parameter with its type and description
                    for param_name, param_info in tool.parameters.properties.items():
                        param_type = param_info.get("type", "unknown")
                        param_desc = param_info.get("description", "No description")
                        print(f"    - \033[1;34m{param_name}\033[0m (\033[1;35m{param_type}\033[0m): {param_desc}")
            
            # Show a quick example after listing tools
            print("\n\033[1;36mQuick Examples:\033[0m")
            print("\033[1;33mGet editor state:\033[0m")
            print("  python unity_mcp_client.py --as-client --method tools/call --tool-name manage_editor --params '{\"action\":\"get_state\"}'")
            
            print("\n\033[1;33mGet active tool:\033[0m")
            print("  python unity_mcp_client.py --as-client --method tools/call --tool-name manage_editor --params '{\"action\":\"get_active_tool\"}'")
            
            print("\n\033[1;33mGet current selection:\033[0m")
            print("  python unity_mcp_client.py --as-client --method tools/call --tool-name manage_editor --params '{\"action\":\"get_selection\"}'")
            
            print("\n\033[1;33mCreate a new script:\033[0m")
            print("""  python unity_mcp_client.py --as-client --method tools/call --tool-name manage_script --params '{
  "action": "create", 
  "name": "NewScript", 
  "path": "Assets/Scripts", 
  "contents": "using UnityEngine;\\n\\npublic class NewScript : MonoBehaviour {\\n    void Start() {\\n        Debug.Log(\\"Hello from NewScript!\\");\\n    }\\n}",
  "script_type": "MonoBehaviour",
  "namespace": ""
}'""")
        
        elif args.method == "tools/call":
            if not args.tool_name:
                print("Error: --tool-name is required for tools/call method")
                return
            
            # Parse params for the tool call
            tool_params = {}
            if args.params:
                try:
                    tool_params = json.loads(args.params)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in tool parameters: {args.params}")
                    return
            
            # Call the specified tool
            print(f"\n\033[1;36mCalling tool:\033[0m \033[1;32m{args.tool_name}\033[0m")
            print(f"\033[1;33mParameters:\033[0m")
            print(json.dumps(tool_params, indent=2))
            
            result = await client.call_tool(args.tool_name, tool_params)
            
            print("\n\033[1;36mTool call result:\033[0m")
            
            # Process the result based on its type
            if isinstance(result, dict):
                # Dictionary result
                success = result.get("success", False)
                if success:
                    print(f"\033[1;32mSuccess:\033[0m {result.get('message', 'Operation completed successfully')}")
                else:
                    print(f"\033[1;31mError:\033[0m {result.get('error', 'Unknown error')}")
                
                if "data" in result:
                    print("\n\033[1;33mData:\033[0m")
                    try:
                        print(json.dumps(result["data"], indent=2))
                    except TypeError:
                        print(str(result["data"]))
            elif isinstance(result, list):
                # List result
                try:
                    # Try to serialize the list to JSON
                    print(json.dumps(result, indent=2))
                except TypeError:
                    # If that fails, print each item separately
                    for item in result:
                        print(f"- {str(item)}")
            else:
                # Other result types
                print(f"Result: {str(result)}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Unity MCP Client")
    parser.add_argument("--method", choices=["tools/list", "tools/call", "initialize", "capabilities"], 
                      default="tools/list", help="MCP method to call")
    parser.add_argument("--params", default=None, 
                      help="JSON parameters for the method call")
    parser.add_argument("--timeout", type=int, default=5, 
                      help="Timeout in seconds for server response")
    parser.add_argument("--unity-host", default="localhost",
                      help="Unity Editor host (default: localhost)")
    parser.add_argument("--unity-port", type=int, default=6400,
                      help="Unity Editor port (default: 6400)")
    parser.add_argument("--use-sdk", action="store_true",
                      help="Use the MCP SDK client instead of subprocess")
    parser.add_argument("--use-fastmcp", action="store_true",
                      help="Use FastMCP to create a proxy server")
    parser.add_argument("--as-client", action="store_true",
                      help="Use FastMCP as client instead of starting a proxy server")
    parser.add_argument("--sse-port", type=int, default=8000,
                      help="Port for the SSE server when using FastMCP (default: 8000)")
    parser.add_argument("--debug", action="store_true",
                      help="Enable debug logging")
    parser.add_argument("--tool-name", default=None,
                      help="Tool name to call (required for tools/call method)")
    args = parser.parse_args()
    
    # Set logging level based on args
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if Unity Editor is accessible
    is_unity_running, unity_message = check_unity_connection(args.unity_host, args.unity_port)
    print(f"Unity status: {unity_message}")
    
    if not is_unity_running:
        print("\n⚠️  WARNING: Unity Editor is not accessible!")
        print("The MCP server requires a running Unity Editor with the MCP Bridge plugin installed.")
        print("The server will start but might not be able to process tool requests.")
        print("Make sure to:")
        print("1. Open Unity Editor")
        print("2. Install the Unity MCP Bridge plugin")
        print("3. Ensure the MCP Bridge is running in Unity on port 6400")
        print("\nWould you like to continue anyway? (y/n)")
        response = input().strip().lower()
        if response != 'y' and response != 'yes':
            print("Exiting...")
            return

    # Choose which implementation to use
    if args.use_fastmcp:
        run_fastmcp_proxy(args)
    elif args.as_client:
        # Use FastMCP as a client
        asyncio.run(run_fastmcp_client(args))
    else:
        # Use the async implementation
        asyncio.run(run_mcp_client(args))
    return

if __name__ == "__main__":
    main() 