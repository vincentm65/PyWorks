### Project Overview

This project, "PyWorks," is a visual workflow editor built with Python and PyQt6. It allows users to create, connect, and execute Python functions as nodes in a graph-based workflow. Each project has its own virtual environment, and dependencies can be managed via a `requirements.txt` file. The UI consists of a canvas for arranging nodes, a code editor for modifying node logic, a console for viewing output, and a list of available nodes.

The core components are:

*   **`main.py`**: The application's entry point, which sets up the main window, menus, and docks.
*   **`ui/canvas.py`**: Implements the main graph view where users can add, connect, and arrange nodes.
*   **`core/executor.py`**: Responsible for executing the workflow by generating and running a Python script based on the node graph.
*   **`core/graph_builder.py`**: Constructs the execution graph from the layout data.
*   **`core/node_registry.py`**: Discovers and registers available nodes from the project's `nodes` directory.
*   **`utils/project_manager.py`**: Handles project creation, validation, and virtual environment management.
*   **`utils/layout_manager.py`**: Saves and loads the node layout to/from a `.layout.json` file.

### Building and Running

To run the project, execute the `main.py` script:

```bash
python src/main.py
```

The application will launch, and you can create a new project or open an existing one.

### Development Conventions

*   **Nodes**: Custom nodes are created by decorating Python functions with `@node` in files within the `nodes` directory.
*   **Virtual Environments**: Each project has its own virtual environment located in a `.venv` directory within the project folder.
*   **Dependencies**: Project dependencies are managed using a `requirements.txt` file.
*   **Layout**: The visual layout of the nodes and connections is stored in a `.layout.json` file.
*   **Execution**: The workflow is executed by generating a single Python script that imports and runs the node functions in the correct order.
