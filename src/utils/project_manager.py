import json
from pathlib import Path
from typing import Optional
from core.venv_manager import VenvManager


# Default template with example nodes
EXAMPLE_CATEGORY_TEMPLATE = '''"""
Example Node Category

Add your @node decorated functions here.
"""
import sys

def node(func):
    """Decorator to mark a function as a workflow node."""
    func._is_workflow_node = True
    return func


@node
def send_example(inputs, global_state):
    """
    Example node that demonstrates the basic structure.

    Args:
        inputs: Dictionary of parent node outputs
        global_state: Shared state dictionary

    Returns:
        Dictionary of outputs for child nodes
    """
    message = "Hello World!"
    return {"result": message}


@node
def receive_example(inputs, global_state):
    print(f"All inputs {inputs}") # This is the dict structure that is passed in

    data = inputs.get("example.send_example", {}).get("result", "")
    print(f"Received: {data} from parent node")
    return {"processed": data.upper()}
'''


def create_project(name: str, location: str) -> Path:
    # Create project folder path
    project_path = Path(location) / name
    nodes_dir = project_path / "nodes"

    # Check if project already exists
    if project_path.exists():
        raise FileExistsError(f"Project already exists at: {project_path}")

    # Create project directory and example.py
    project_path.mkdir(parents=True, exist_ok=False)
    nodes_dir.mkdir(parents=True, exist_ok=False)
    workflow_file = nodes_dir / "example.py"
    workflow_file.write_text(EXAMPLE_CATEGORY_TEMPLATE, encoding='utf-8')

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
    
    print(f"Creating virtual environment for {name}...")
    venv_manager = VenvManager(str(project_path))
    if venv_manager.create_venv():
        print("Virtual environment created successfully")
    else:
        print("Failed to create virtual environment")
        

    print(f"Created new project: {project_path}")
    return project_path


def validate_project(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False

    nodes_path = path / "nodes"
    if not nodes_path.exists() or not nodes_path.is_dir():
        return False

    layout_path = path / ".layout.json"
    if not layout_path.exists() or not layout_path.is_file():
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

def initialize_project_venv(project_path: Path) -> VenvManager:
    venv_manager = VenvManager(str(project_path))

    if not venv_manager.venv_exists():
        print(f"Virtual environment not found. Creating one...")
        if venv_manager.create_venv():
            print("Virtual environment created successfully")
        else:
            print("Failed to create virtual environment")
    else:
        # Validate existing venv
        if venv_manager.validate_venv():
            print("Virtual environment is ready")
        else:
            print("Virtual environment exists but may be corrupted")
    return venv_manager



def get_project_name(path: Path) -> str:
    return path.name
