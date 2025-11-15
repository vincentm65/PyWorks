from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
from pathlib import Path

class WorkflowExecutor(QThread):
    output_signal = pyqtSignal(str)
    active_node_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
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

            self.status_signal.emit(f"Executing {len(sorted_nodes)} nodes...")
            
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
        imports = []

        for fqnn, metadata in self.node_registry.nodes.items():
            parts = fqnn.split(".")
            module_name = parts[0]
            func_name = parts[1]

            safe_name = fqnn.replace(".", "_")

            statement = f"from nodes.{module_name} import {func_name} as {safe_name}"
            imports.append(statement)

        return '\n'.join(imports)

    def _generate_execution_script(self, sorted_nodes: list, data_graph: dict, flow_graph: dict) -> str:
        imports = self._build_imports()
        nodes_dict = self.layout_data.get('nodes', {})

        node_code = []

        for node_key in sorted_nodes:
            node_data = nodes_dict.get(node_key, {})
            fqnn = node_data.get('fqnn')
            if not fqnn:
                continue

            code = f"print(f'__PYWORKS_EXEC_NODE__:{node_key}', flush=True)\n"
            code += "try:\n"
            code += "    inputs = {}\n"
            for parent_key, port in data_graph.get(node_key, []):
                parent_node_data = nodes_dict.get(parent_key, {})
                parent_fqnn = parent_node_data.get('fqnn')
                if not parent_fqnn:
                    continue
                code += f"    inputs['{parent_fqnn}'] = node_outputs.get('{parent_fqnn}', {{}})\n"

            safe_name = fqnn.replace('.', '_')

            code += f"    result = {safe_name}(inputs, global_state)\n"
            code += f"    node_outputs['{fqnn}'] = result\n"
            code += "except Exception as e:\n"
            code += "    import traceback\n"
            code += f"    tb = traceback.format_exc()\n"
            code += f"    print(f'🔴 Error in {fqnn}:', tb)\n"
            code += f"    node_errors['{fqnn}'] = str(e)\n"

            node_code.append(code)

        script = f"""
import sys
sys.path.insert(0, "{self.project_path.as_posix()}")

{imports}

global_state = {{}}
node_outputs = {{}}
node_errors = {{}}

{''.join(node_code)}

print(f"[SUMMARY] Done")
sys.exit(0 if len(node_errors) == 0 else 1)
"""

        return script

    def _run_subprocess(self, script: str) -> tuple[bool, str]:
        self.python = self.venv_manager.get_python_path()

        process = subprocess.Popen([self.python, '-u', '-c', script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=str(self.project_path)
        ) 

        output_lines = []

        

        for line in process.stdout:
            if line.startswith("__PYWORKS_EXEC_NODE__"):
                node_id = line.strip().split(":")[1]
                self.active_node_signal.emit(node_id)
            else:
                self.output_signal.emit(line.rstrip())
            output_lines.append(line.rstrip())

        process.wait()

        success = (process.returncode == 0)
        all_output = '\n'.join(output_lines)

        return (success, all_output)

