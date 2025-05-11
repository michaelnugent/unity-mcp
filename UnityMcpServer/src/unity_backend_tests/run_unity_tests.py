#!/usr/bin/env python3
"""
Unity Backend Tests Runner

This script runs the Unity backend tests that connect to a real Unity Editor instance.
These tests are separate from the unit tests and require a running Unity Editor with
the Unity MCP Bridge plugin.

Usage:
    python run_unity_tests.py [test_file_pattern]

Examples:
    # Run all Unity backend tests
    python run_unity_tests.py
    
    # Run just the editor tests
    python run_unity_tests.py test_editor_operations.py
    
    # Run tests matching a pattern
    python run_unity_tests.py test_*_operations.py
"""

import os
import sys
import subprocess
import argparse
import socket
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("unity-test-runner")

def is_unity_running(host="localhost", port=6400, timeout=1):
    """Check if Unity is running and available on the given port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except:
        return False

def run_tests(test_pattern=None):
    """Run the Unity backend tests.
    
    Args:
        test_pattern: Optional file pattern to filter tests
    
    Returns:
        int: The exit code from pytest
    """
    # Check if Unity is running
    if not is_unity_running():
        logger.error("Unity Editor is not running. Please start Unity with the MCP Bridge plugin.")
        return 1
    
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build the pytest command
    cmd = ["python", "-m", "pytest", "-v"]
    
    # Add the test pattern if provided
    if test_pattern:
        cmd.append(os.path.join(current_dir, test_pattern))
    else:
        cmd.append(current_dir)
    
    # Add additional pytest arguments
    cmd.extend([
        "--log-cli-level=INFO",
        "--no-header",
        "-xvs"  # Exit on first failure, verbose, don't capture output
    ])
    
    logger.info(f"Running Unity backend tests with command: {' '.join(cmd)}")
    
    # Run the tests
    try:
        result = subprocess.run(cmd, cwd=os.path.dirname(current_dir))
        return result.returncode
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Unity backend tests")
    parser.add_argument("test_pattern", nargs="?", help="Optional pattern to filter test files", default=None)
    args = parser.parse_args()
    
    sys.exit(run_tests(args.test_pattern)) 