from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
from pathlib import Path

class WorkflowExecutor(QThread):
    output_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, project_path, layout_data, venv_manager, node_registry):
        super().__init__()
        self.project_path = project_path
        self.layout_data = layout_data
        self.venv_manager = venv_manager
        self.node_registry = node_registry

    def run(self):
        try:
            from .graph_builder import GraphBuilder
            from .topological import topological_sort

            self.status_signal.emit("Building execution graph...")

            graph_builder = GraphBuilder(self.layout_data, self.node_registry)
            graph_builder.build()

            if graph_builder.has_cycle():
                self.finished_signal.emit(False, "Cycle detected in FLOW graph - execution canceled!")
                return
            
            sorted_nodes = topological_sort(
                graph_builder.flow_graph,
                graph_builder.all_nodes
            )

            self.signal_status.emit(f"Executing {len(sorted_nodes)} nodes...")
            
            script = self._generate_execution_script(
                sorted_nodes,
                graph_builder.data_graph,
                graph_builder.all_nodes
            )

            success, output = self._run_subprocess(script)

            if success:
                self.status_signal.emit("Execution completed successfully")
                self.finished_signal.emit(True, "Workflow completed successfully")
            else:
                self.status_signal.emit("Execution failed")
                self.finished_signal.emit(False, "Workflow failed - check console for errors")

        except Exception as e:
            self.status_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False, str(e))

    def _build_imports(self)-> str:
        imports = {}

        for node_key in self.all_nodes:
            fqnn = node_key.rsplit('_', 2)[0]

            meta_data = self.node_registry.get_metadata(fqnn)

        for node_key in self.node_registry.nodes.items():
            fqnn = node_key.rsplit('_', 2)[0]

        
