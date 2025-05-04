# Unity MCP Server - Docker Setup

This repository contains Docker configuration for running the Unity MCP server in a container.

## Prerequisites

- [Podman](https://podman.io/get-started) or [Docker](https://docs.docker.com/get-docker/)
- Unity Editor with the Unity MCP Bridge package installed

## Getting Started

### 1. Build the Docker Image

```bash
# From the UnityMcpServer/src directory:
docker build -t unity-mcp:latest .
```

or with Podman:

```bash
# From the UnityMcpServer/src directory:
podman build -t unity-mcp:latest .
```

The Dockerfile copies all source files (excluding test files and other unnecessary files specified in `.dockerignore`) to the container and sets up the Python environment.

### 2. Run the Container

```bash
# With Docker:
docker run -i --rm --name unity-mcp-server unity-mcp:latest --unity-host=host.docker.internal --unity-port=6400
```

With Podman:

```bash
# With Podman:
podman run -i --rm --name unity-mcp-server unity-mcp:latest --unity-host=host.containers.internal --unity-port=6400
```

### 3. Configure Your MCP Client

Configure your MCP client (Claude, Cursor, etc.) to use the dockerized server:

For Docker:
```json
{
  "mcpServers": {
    "UnityMCP": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--name",
        "unity-mcp-server",
        "unity-mcp:latest",
        "--unity-host=host.docker.internal",
        "--unity-port=6400"
      ]
    }
  }
}
```

For Podman:
```json
{
  "mcpServers": {
    "UnityMCP": {
      "command": "podman",
      "args": [
        "run",
        "-i",
        "--rm",
        "--name",
        "unity-mcp-server",
        "unity-mcp:latest",
        "--unity-host=host.containers.internal",
        "--unity-port=6400"
      ]
    }
  }
}
```

## Stopping the Container

To stop the container:

```bash
docker stop unity-mcp-server
``` 

or with Podman:

```bash
podman stop unity-mcp-server
```

## Docker Best Practices

This project follows several Docker best practices:

1. **Using a .dockerignore file** - Excludes unnecessary files from the build context to improve build times and reduce image size.
2. **Ordering commands properly** - Puts less frequently changing steps earlier in the Dockerfile.
3. **Minimizing image size** - Removes test files and uses a slim base image.
4. **Cleanup after installations** - Removes apt cache to reduce image size.
5. **Using specific base image tags** - Uses a specific Python version instead of 'latest' for reproducibility.
