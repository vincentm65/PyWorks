# PyWorks

PyWorks is a visual workflow editor for Python. It allows you to create, connect, and execute Python functions as nodes in a graph-based workflow.

## Features

- **Node-based workflow:** Create and connect nodes to build complex workflows.
- **Code editor:** Inspect and modify the underlying code of your nodes.
- **Virtual environment management:** Each project has its own virtual environment.
- **Package management:** Install project dependencies from a `requirements.txt` file.
- **Save and load layouts:** Save your workflow layout and reload it later.
- **Customizable nodes:** Create your own nodes by decorating Python functions with `@node`.

## Getting Started

1. **Create a new project:**
   - Launch PyWorks. (PyWorks>Dist>main.exe)
   - Click "Create New Project" in the welcome dialog.
   - Enter a project name and select a location.
   - A new project will be created with an example workflow.

2. **Open an existing project:**
   - Launch PyWorks.
   - Click "Open Existing Project" in the welcome dialog.
   - Select the project folder.

3. **Add nodes to the canvas:**
   - Drag and drop nodes from the "Node List" on the left to the canvas.

4. **Connect nodes:**
   - Click and drag from a port on one node to a port on another node to create a connection.
   - There are two types of connections:
     - **FLOW:** Determines the execution order of the nodes.
     - **DATA:** Passes data from one node to another.

5. **Edit node code:**
   - Double-click a node to open its code in the editor.
   - You can modify the code and save it.

6. **Run the workflow:**
   - Click the "Run" button in the toolbar to execute the workflow.
   - The output of the workflow will be displayed in the console.

## Creating Custom Nodes

To create a custom node, you need to create a Python function and decorate it with `@node`. The function must take two arguments: `inputs` and `global_state`.

- `inputs`: A dictionary containing the outputs of the parent nodes.
- `global_state`: A dictionary that is shared across all nodes in the workflow.

The function should return a dictionary of outputs that can be passed to child nodes.

Here is an example of a custom node:

```python
from nodes import node

@node
def my_custom_node(inputs, global_state):
    """
    This is a custom node.
    """
    # Get data from parent nodes
    data = inputs.get("parent_node_name", {}).get("output_name", "")

    # Do some processing
    result = data.upper()

    # Return the output
    return {"result": result}
```

## Project Structure

A PyWorks project has the following structure:

```
my_project/
├── nodes/
│   ├── example.py
│   └── ...
├── .venv/
│   └── ...
├── .layout.json
└── requirements.txt
```

- `nodes/`: Contains the Python files with your custom nodes.
- `.venv/`: The virtual environment for the project.
- `.layout.json`: Stores the layout of the nodes on the canvas.
- `requirements.txt`: The project dependencies.
