from pathlib import Path
from . import ast_utils
from dataclasses import dataclass

@dataclass
class NodeMetadata:
    fqnn: str              # "desktop.click_mouse"
    category: str          # "desktop"
    function_name: str     # "click_mouse"
    file_path: Path        # Path to desktop.py
    docstring: str         # Function docstring
    lineno: int            # Line start
    end_lineno: int        # Line end
    signature: str         # "(inputs, global_state)"

class NodeRegistry:
    def __init__(self):
        self.nodes: dict[str, NodeMetadata] = {}
    
    def discover(self, project_path: Path, python_path: str = None):
        self.nodes.clear()
        self.python_path = python_path
        for file in (project_path / "nodes").glob("*.py"):
            category = file.stem
            extracted_nodes = ast_utils.extract_nodes_from_file(file, category)
            for fqnn, node_data in extracted_nodes.items():
                metadata = NodeMetadata(
                    fqnn=node_data['fqnn'],
                    category=node_data['category'],
                    function_name=node_data['function_name'],
                    file_path=node_data['file_path'],
                    docstring=node_data['docstring'],
                    lineno=node_data['lineno'],
                    end_lineno=node_data['end_lineno'],
                    signature="(inputs, global_state)"  # You'll need to handle this
                )
                self.nodes[fqnn] = metadata


    def get_metadata(self, fqnn: str) -> NodeMetadata:
        return self.nodes.get(fqnn)

    def get_by_category(self, category: str) -> dict[str, NodeMetadata]:
        result = {}
        for fqnn, metadata in self.nodes.items():
            if metadata.category == category:
                result[fqnn] = metadata
        return result


