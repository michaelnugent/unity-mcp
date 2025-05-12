# Unity MCP ✨

**Connect your Unity Editor to LLMs using the Model Context Protocol.**

Unity MCP acts as a bridge, allowing AI assistants (like Claude, Cursor) to interact directly with your Unity Editor via a local **MCP (Model Context Protocol) Client**. Give your LLM tools to manage assets, control scenes, edit scripts, and automate tasks within Unity.

---

## UnityMCP Workflow

## Key Features 🚀

*   **🗣️ Natural Language Control:** Instruct your LLM to perform Unity tasks.
*   **🛠️ Powerful Tools:** Manage assets, scenes, materials, scripts, and editor functions.
*   **🤖 Automation:** Automate repetitive Unity workflows.
*   **🧩 Extensible:** Designed to work with various MCP Clients.

<details>
  <summary><strong>Expand for Available Tools...</strong></summary>

  Your LLM can use functions like:

  *   `read_console`: Gets messages from or clears the console.
  *   `manage_script`: Manages C# scripts (create, read, update, delete).
  *   `manage_editor`: Controls and queries the editor's state and settings.
  *   `manage_scene`: Manages scenes (load, save, create, get hierarchy, etc.).
  *   `manage_asset`: Performs asset operations (import, create, modify, delete, etc.).
  *   `manage_gameobject`: Manages GameObjects: create, modify, delete, find, and component operations.
  *   `execute_menu_item`: Executes a menu item via its path (e.g., "File/Save Project").
  *   `manage_prefabs`: Works with Unity prefabs (create, instantiate, modify).
</details>

---

## Project Architecture 🏗️

Unity MCP consists of four main components:

1. **Unity MCP Bridge**: A Unity package that runs inside the Unity Editor
2. **Unity MCP Server**: A Python server that communicates between MCP clients and the Unity Bridge
3. **MCP Client** (external): LLM tools like Claude Desktop or Cursor that connect to the server
4. **Unity MCP Client**: A Python client library providing a programmatic API and CLI for Unity MCP

**Communication Flow:**
```
[MCP Client (Claude/Cursor)] <-> [Unity MCP Server (Python)] <-> [Unity MCP Bridge (Unity Editor)]
```

With the Unity MCP Client:
```
[Python Application] <-> [Unity MCP Client] <-> [Unity MCP Server] <-> [Unity MCP Bridge]
```

---

## How It Works 🤔

Unity MCP connects your tools using two components:

1.  **Unity MCP Bridge:** A Unity package running inside the Editor. (Installed via Package Manager).
2.  **Unity MCP Server:** A Python server that runs locally, communicating between the Unity Bridge and your MCP Client. (Installed manually).

**Flow:** `[Your LLM via MCP Client] <-> [Unity MCP Server (Python)] <-> [Unity MCP Bridge (Unity Editor)]`

---

## Installation ⚙️

> **Note:** The setup is constantly improving as we update the package. Check back if you randomly start to run into issues.

### Prerequisites

<details>
  <summary><strong>Click to view required software...</strong></summary>

  *   **Git CLI:** For cloning the server code. [Download Git](https://git-scm.com/downloads)
  *   **Python:** Version 3.12 or newer. [Download Python](https://www.python.org/downloads/)
  *   **Unity Hub & Editor:** Version 2020.3 LTS or newer. [Download Unity](https://unity.com/download)
  *   **uv (Python package manager):**
      ```bash
      pip install uv
      # Or see: https://docs.astral.sh/uv/getting-started/installation/
      ```
  *   **An MCP Client:**
      *   [Claude Desktop](https://claude.ai/download)
      *   [Cursor](https://www.cursor.com/en/downloads)
      *   *(Others may work with manual config)*
</details>

### Step 1: Install the Unity Package (Bridge)

1.  Open your Unity project.
2.  Go to `Window > Package Manager`.
3.  Click `+` -> `Add package from git URL...`.
4.  Enter:
    ```
    https://github.com/michaelnugent/unity-mcp.git?path=/UnityMcpBridge
    ```
5.  Click `Add`.
6. The MCP Server should automatically be installed onto your machine as a result of this process.

### Step 2: Configure Your MCP Client

Connect your MCP Client (Claude, Cursor, etc.) to the Python server you installed in Step 1.

**Option A: Auto-Configure (Recommended for Claude/Cursor)**

1.  In Unity, go to `Window > Unity MCP`.
2.  Click `Auto Configure Claude` or `Auto Configure Cursor`.
3.  Look for a green status indicator 🟢 and "Connected". *(This attempts to modify the MCP Client's config file automatically)*.

**Option B: Manual Configuration**

If Auto-Configure fails or you use a different client:

1.  **Find your MCP Client's configuration file.** (Check client documentation).
    *   *Claude Example (macOS):* `~/Library/Application Support/Claude/claude_desktop_config.json`
    *   *Claude Example (Windows):* `%APPDATA%\Claude\claude_desktop_config.json`
2.  **Edit the file** to add/update the `mcpServers` section, using the *exact* paths from Step 1.

<details>
<summary><strong>Click for OS-Specific JSON Configuration Snippets...</strong></summary>

**Windows:**

  ```json
  {
    "mcpServers": {
      "UnityMCP": {
        "command": "uv",
        "args": [
          "run",
          "--directory",
          "C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Programs\\UnityMCP\\UnityMcpServer\\src",
          "server.py"
        ]
      }
      // ... other servers might be here ...
    }
  }
``` 

(Remember to replace YOUR_USERNAME and use double backslashes \\)

**macOS:**

```json
{
  "mcpServers": {
    "UnityMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/usr/local/bin/UnityMCP/UnityMcpServer/src",
        "server.py"
      ]
    }
    // ... other servers might be here ...
  }
}
```
(Replace YOUR_USERNAME if using ~/bin)

**Linux:**

```json
{
  "mcpServers": {
    "UnityMCP": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/home/YOUR_USERNAME/bin/UnityMCP/UnityMcpServer/src",
        "server.py"
      ]
    }
    // ... other servers might be here ...
  }
}
```

(Replace YOUR_USERNAME)

</details>

---

## Enhanced Serialization System 🔄

Unity MCP includes a sophisticated serialization system for translating Unity objects to JSON:

- **Multi-depth Serialization Levels**:
  - `Basic`: Simple properties and type information only
  - `Standard`: Normal reflection-based serialization of properties and fields
  - `Deep`: Comprehensive serialization of nested objects and Unity-specific properties

- **Specialized Unity Type Handlers** for Transform, GameObject, Components, Rigidbody, and MeshRenderer

- **Circular Reference Detection and Resolution** to prevent infinite recursion with path-based tracking

- **Extensible Type Registry** allowing registration of custom handlers for additional types

- **Error Handling and Metadata** via SerializationResult to aid in debugging

This serialization system allows for detailed introspection of Unity objects in a format that's easily consumed by AI systems while handling the complexities of Unity's object model.

---

## Testing Requirements 🧪

When contributing to Unity MCP, please include appropriate tests:

- **Unit Tests**: Add tests for individual components in `UnityMcpServer/src/tests/`
- **Integration Tests**: Consider end-to-end tests using the Unity MCP Client
- **Test Configuration**: Follow the pytest configuration in pyproject.toml
- **Serialization Testing**: Use the SerializationTestWindow to test serialization of various Unity objects
- **Circular Reference Testing**: Include tests for serialization edge cases

The test suite uses pytest with specific configurations for proper asyncio test isolation.

---

## Usage ▶️

1. **Open your Unity Project.** The Unity MCP Bridge (package) should connect automatically. Check status via Window > Unity MCP.
    
2. **Start your MCP Client** (Claude, Cursor, etc.). It should automatically launch the Unity MCP Server (Python) using the configuration from Installation Step 3.
    
3. **Interact!** Unity tools should now be available in your MCP Client.
    
    Example Prompt: `Create a 3D player controller.`
    

---

## Contributing 🤝

Help make Unity MCP better!

1. **Fork** the main repository.
    
2. **Create a branch** (`feature/your-idea` or `bugfix/your-fix`).
    
3. **Make changes.**
    
4. **Add tests** for your new functionality:
   - Unit tests for individual components
   - Integration tests where appropriate
    
5. **Commit** (feat: Add cool new feature).
    
6. **Push** your branch.
    
7. **Open a Pull Request** against the master branch.
    

---

## Troubleshooting ❓

<details>  
<summary><strong>Click to view common issues and fixes...</strong></summary>  

- **Unity Bridge Not Running/Connecting:**
    
    - Ensure Unity Editor is open.
        
    - Check the status window: Window > Unity MCP.
        
    - Restart Unity.
        
- **MCP Client Not Connecting / Server Not Starting:**
    
    - **Verify Server Path:** Double-check the --directory path in your MCP Client's JSON config. It must exactly match the location where you cloned the UnityMCP repository in Installation Step 1 (e.g., .../Programs/UnityMCP/UnityMcpServer/src).
        
    - **Verify uv:** Make sure uv is installed and working (pip show uv).
        
    - **Run Manually:** Try running the server directly from the terminal to see errors: `# Navigate to the src directory first! cd /path/to/your/UnityMCP/UnityMcpServer/src uv run server.py`
        
    - **Permissions (macOS/Linux):** If you installed the server in a system location like /usr/local/bin, ensure the user running the MCP client has permission to execute uv and access files there. Installing in ~/bin might be easier.
        
- **Auto-Configure Failed:**
    
    - Use the Manual Configuration steps. Auto-configure might lack permissions to write to the MCP client's config file.
        

</details>  

Still stuck? [Open an Issue](https://www.google.com/url?sa=E&q=https%3A%2F%2Fgithub.com%2Fmichaelnugent%2Funity-mcp%2Fissues).

---

## License 📜

MIT License. See [LICENSE](https://www.google.com/url?sa=E&q=https%3A%2F%2Fgithub.com%2Fmichaelnugent%2Funity-mcp%2Fblob%2Fmaster%2FLICENSE) file.

---

## Acknowledgments 🙏

Thanks to the contributors, [Justin P Barnett](https://github.com/justinpbarnett), the original author of this code where I forked the project and the Unity team.
