import json
from pathlib import Path
from typing import Optional


# Default workflow.py template with example nodes
WORKFLOW_TEMPLATE = '''"""
PyWorks Workflow

Define your nodes here using the @node decorator.
Each node receives inputs from parent nodes and can pass data to children.
"""

def node(func):
    """Decorator to mark a function as a workflow node."""
    func._is_workflow_node = True
    return func


@node
def get_data(inputs, global_state):
    """
    Example node that produces initial data.

    Args:
        inputs: Dictionary of parent node outputs (empty for root nodes)
        global_state: Shared state dictionary across all nodes

    Returns:
        Dictionary of outputs that will be passed to child nodes
    """
    # This is a root node with no parents, so inputs will be empty
    numbers = [1, 2, 3, 4, 5]
    print(f"Generated data: {numbers}")
    return {"numbers": numbers}


@node
def process_data(inputs, global_state):
    """
    Example node that processes data from the get_data node.

    Args:
        inputs: Contains outputs from parent nodes
                Example: {"get_data": {"numbers": [1,2,3,4,5]}}
        global_state: Shared state dictionary

    Returns:
        Dictionary of processed outputs
    """
    # Access data from the parent 'get_data' node
    data = inputs.get("get_data", {}).get("numbers", [])

    # Process the data (multiply each number by 2)
    result = [x * 2 for x in data]

    print(f"Processed {len(data)} numbers")
    print(f"Result: {result}")

    return {"processed": result}
'''


def create_project(name: str, location: str) -> Path:
    # Create project folder path
    project_path = Path(location) / name

    # Check if project already exists
    if project_path.exists():
        raise FileExistsError(f"Project already exists at: {project_path}")

    # Create project directory and workflow.py
    project_path.mkdir(parents=True, exist_ok=False)
    workflow_file = project_path / "workflow.py"
    workflow_file.write_text(WORKFLOW_TEMPLATE, encoding='utf-8')

    # Create empty requirements.txt
    requirements_file = project_path / "requirements.txt"
    requirements_file.write_text("# Add your project dependencies here\n# Example:\n# numpy>=1.21.0\n# pandas>=1.3.0\n", encoding='utf-8')

    # Create empty .layout.json
    layout_file = project_path / ".layout.json"
    empty_layout = {
        "version": "1.0",
        "nodes": {},
        "connections": []
    }
    layout_file.write_text(json.dumps(empty_layout, indent=2), encoding='utf-8')

    print(f"Created new project: {project_path}")
    return project_path


def validate_project(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False

    # Check for required files
    required_files = ["workflow.py", ".layout.json"]

    for file_name in required_files:
        file_path = path / file_name
        if not file_path.exists() or not file_path.is_file():
            return False

    # Validate .layout.json structure
    try:
        layout_file = path / ".layout.json"
        with open(layout_file, 'r', encoding='utf-8') as f:
            layout_data = json.load(f)

        # Check for required keys
        if "nodes" not in layout_data or "connections" not in layout_data:
            return False

    except (json.JSONDecodeError, OSError):
        return False

    return True


def get_project_name(path: Path) -> str:
    return path.name
