# Phase 4: Execution Engine - Comprehensive Implementation Guide

## Overview

This document provides a detailed, step-by-step breakdown of how to implement PyWorks' execution engine. The engine will take visual node graphs and execute them in the correct order, passing data between nodes, handling errors gracefully, and supporting advanced features like conditional branching and real-time debugging.

**Key Principle:** The execution engine is the "heart" of PyWorks. Everything built in Phases 1-3 (UI, node discovery, venv management) exists to support this engine.

---

## Core Architecture Philosophy

### Design Principles

1. **Separation of Concerns**
   - Graph building (topology) is separate from execution (runtime)
   - Allows testing graph structure without running code
   - Makes debugging easier: know if problem is in graph or node code

2. **Subprocess Isolation**
   - User code runs in completely separate Python process
   - Main PyQt application stays responsive
   - Crashes in user code don't crash the editor
   - Full control over imports and environment

3. **Explicit Control Flow**
   - FLOW connections (grey lines) define execution order
   - DATA connections (purple lines) define data routing
   - Two systems can be analyzed independently
   - Supports parallel execution in future phases

4. **Graceful Degradation**
   - Failed nodes don't stop entire graph (by design)
   - Independent branches continue executing
   - Errors are captured and reported without crashing
   - Makes complex graphs more robust

5. **Future-Proof Architecture**
   - Core systems built to support conditionals, loops, parallel execution
   - Each phase adds features without breaking existing code
   - No "rip and replace" needed as complexity grows

---

## Execution Model: How It Works

### Phase 1: Prepare (GUI Thread)
1. User clicks "Run Workflow" button
2. Application loads `.layout.json` to get graph structure
3. Creates `WorkflowExecutor` thread (doesn't run yet)
4. Connects signals for feedback

### Phase 2: Analyze (Executor Thread)
1. Build FLOW graph from connections (defines execution order)
2. Build DATA graph from connections (defines data dependencies)
3. Detect cycles (abort if found - prevents infinite loops)
4. Compute topological sort (execution order respecting dependencies)
5. Validate all nodes are defined in node_registry

### Phase 3: Execute (Subprocess)
1. Create temporary Python script with:
   - All imports needed by node functions
   - Global state initialization
   - Node execution code in topological order
2. Spawn subprocess with venv Python
3. Run script, streaming output back to main process
4. Capture return values and errors

### Phase 4: Report (GUI Thread)
1. Receive execution status/output from subprocess
2. Update console in real-time
3. Highlight active nodes on canvas
4. Show final success/failure status

---

## Data Flow Model

### The Three Data Containers

#### 1. **global_state** (Dictionary)
- **Shared across all nodes**
- **Persistent throughout execution**
- **Example use:** Database connection, session ID, counters

```python
# In first node:
global_state['db_connection'] = sqlite3.connect(':memory:')
global_state['counter'] = 0

# In later nodes:
db = global_state.get('db_connection')  # Same connection!
counter = global_state.get('counter', 0)
```

#### 2. **inputs** (Dictionary)
- **Unique to each node**
- **Built from DATA connections**
- **Namespaced by parent node name**

```python
# If node "DataProcessor" has inputs from:
# - "LoadData" node (output_data port)
# - "Config" node (output_data port)

# Then DataProcessor's inputs dict looks like:
inputs = {
    "LoadData": {
        "raw_data": [1, 2, 3],
        "timestamp": "2024-11-06"
    },
    "Config": {
        "format": "json",
        "compress": True
    }
}

# Node accesses via:
def process_data(inputs, global_state):
    data = inputs['LoadData']['raw_data']  # [1, 2, 3]
    config = inputs['Config']              # Full dict
```

#### 3. **node_outputs** (Dictionary)
- **Internal to executor**
- **Stores return values from each node**
- **Used to build inputs for downstream nodes**

```python
node_outputs = {
    "LoadData_100_200": {
        "raw_data": [1, 2, 3],
        "timestamp": "2024-11-06"
    },
    "Config_300_200": {
        "format": "json",
        "compress": True
    }
}
```

---

## Error Handling Strategy: Continue Independent Branches

### The Challenge
What happens when a node fails?

**Bad approach:** Stop entire graph
- Users can't debug partial failures
- Wastes execution of independent branches
- Frustrating for complex workflows

**Good approach:** Continue independent branches
- Only nodes that depend on the failed node are skipped
- Independent branches execute normally
- User sees full picture of what worked/failed

### Implementation Strategy

```python
# Pseudo-code showing how execution handles errors

node_outputs = {}
node_errors = {}  # Track which nodes failed

for node_key in topological_order:
    # Check if this node depends on any failed nodes
    depends_on_failed = False
    for parent_key, parent_port in data_graph.get(node_key, []):
        if parent_key in node_errors:
            depends_on_failed = True
            break

    if depends_on_failed:
        # Mark as skipped, don't execute
        node_errors[node_key] = "Skipped: parent node failed"
        continue

    # Try to execute
    try:
        inputs = build_inputs(node_key, data_graph, node_outputs)
        result = execute_node(node_key, inputs, global_state)
        node_outputs[node_key] = result
    except Exception as e:
        # Capture error, mark node as failed
        node_errors[node_key] = str(e)
        console.write(f"[ERROR] {node_key}: {e}")
        # DON'T break - continue with next node
```

### User Experience
1. Console shows which nodes executed successfully
2. Console shows which nodes failed with error messages
3. Console shows which nodes were skipped
4. Status bar shows: "X complete, Y failed, Z skipped"
5. Failed nodes are highlighted red on canvas

### Debugging Failed Workflows
```
=== EXECUTION REPORT ===
✓ LoadData_100_200: Loaded 1000 records
✓ Config_300_200: Config loaded
✗ ProcessData_200_300: ValueError in line 15 - "Invalid format"
⊘ SaveData_400_300: Skipped (parent ProcessData failed)
⊘ SendNotification_500_300: Skipped (parent SaveData skipped)

Summary: 2 succeeded, 1 failed, 2 skipped
```

---

## Conditional Branching: Any Node Can Return Boolean

### Design Decision
Unlike traditional flow diagrams with dedicated "If" nodes, PyWorks allows **any node** to influence execution by returning boolean values in its data output.

### How It Works

#### Step 1: Node Returns Decision
```python
@node
def check_credentials(inputs, global_state):
    username = inputs.get("UserInput", {}).get("username")
    password = inputs.get("UserInput", {}).get("password")

    is_valid = authenticate(username, password)

    return {
        "is_valid": is_valid,           # Boolean that controls flow
        "message": "Auth successful" if is_valid else "Invalid creds",
        "user_id": 123 if is_valid else None
    }
```

#### Step 2: Next Node Checks Boolean
```python
@node
def process_request(inputs, global_state):
    auth_result = inputs.get("CheckCredentials", {})

    if not auth_result.get("is_valid", False):
        # Skip processing, return early
        return {
            "status": "rejected",
            "reason": auth_result.get("message")
        }

    # Continue with normal processing
    user_id = auth_result.get("user_id")
    request = inputs.get("Request", {})

    return {
        "status": "processed",
        "user_id": user_id,
        "result": process(user_id, request)
    }
```

#### Step 3: Visually on Canvas
```
┌──────────────────────────────────────┐
│  [UserInput] ──data──> [CheckCreds]  │
│                              ↓       │
│                         ┌─data─┐     │
│                         │      │     │
│  [Request] ──data──> [ProcessReq]   │
│                         ↓           │
│                      [SaveResult]    │
└──────────────────────────────────────┘
```

User visually sees data flowing, but they understand that ProcessReq checks the `is_valid` flag from CheckCreds to decide what to do.

### Key Points
- **No special nodes needed**
- **Leverages existing data connection system**
- **Node authors control logic (flexible)**
- **More code in nodes, less visual clutter**
- **Future enhancement:** Could add visual indicators (e.g., red outline) to show a port "controls flow"

### Limitations
- Doesn't prevent execution of nodes (they always run if no parent failed)
- Next node must explicitly check boolean
- Less "failsafe" than dedicated If nodes
- Makes graph slightly less readable

### Future Enhancement: Conditional Ports
If this becomes unwieldy, Phase 5 could add:
- Special `condition` port type
- Conditional data connections that skip execution
- Visual distinction for "decision" outputs

---

## Debugging Features: Four Levels

### Level 1: Visual Highlighting of Active Node

```python
# In WorkflowExecutor.run():
for node_key in topological_order:
    # Before execution
    self.active_node_signal.emit(node_key, "running")

    # Execute
    result = execute_node(...)

    # After execution
    self.active_node_signal.emit(node_key, "complete" if success else "failed")

# In MainWindow:
def _on_active_node_changed(self, node_key, status):
    # Find NodeItem on canvas with this key
    for item in self.canvas.scene.items():
        if isinstance(item, NodeItem) and item.key == node_key:
            if status == "running":
                item.highlight(color="gold")  # Currently executing
            elif status == "complete":
                item.highlight(color="green")  # Finished successfully
            elif status == "failed":
                item.highlight(color="red")    # Execution failed
```

**User sees:**
- Gold highlight: "this node is running right now"
- Green highlight: "this node completed successfully"
- Red highlight: "this node failed"

### Level 2: Pause/Resume/Step Controls

```python
# In WorkflowExecutor:
class WorkflowExecutor(QThread):
    def __init__(self, ...):
        self.paused = False
        self.step_requested = False

    def run(self):
        for node_key in topological_order:
            # Check pause state before each node
            while self.paused and not self.step_requested:
                time.sleep(0.1)  # Yield CPU until resumed

            if self.step_requested:
                self.step_requested = False

            # Execute node
            ...

# In MainWindow:
def pause_execution(self):
    self.executor.paused = True
    self.status_bar.showMessage("Execution paused")

def resume_execution(self):
    self.executor.paused = False
    self.status_bar.showMessage("Execution running")

def step_execution(self):
    self.executor.step_requested = True  # Execute one node, pause again
```

**Toolbar buttons:**
- ⏸ Pause: Halts before next node
- ▶ Resume: Continues execution
- ⏭ Step: Executes one node, pauses

### Level 3: Breakpoint Support

```python
# In MainWindow:
def _on_node_item_right_click(self, node_item):
    """Toggle breakpoint on right-click"""
    if node_item.key in self.breakpoints:
        self.breakpoints.remove(node_item.key)
        node_item.show_breakpoint(False)
    else:
        self.breakpoints.add(node_item.key)
        node_item.show_breakpoint(True)  # Show red dot on node

# In WorkflowExecutor:
def run(self):
    for node_key in topological_order:
        # Check if this node has a breakpoint
        if node_key in self.breakpoints:
            self.paused = True
            self.breakpoint_hit_signal.emit(node_key)
            # Will stay paused until user clicks Resume
            while self.paused:
                time.sleep(0.1)

        # Execute node
        ...

# In MainWindow:
def _on_breakpoint_hit(self, node_key):
    # Flash the node
    self.canvas.scene.scroll_to_item(node_key)
    self.status_bar.showMessage(f"Breakpoint hit: {node_key}")
```

**User interaction:**
1. Right-click node → red dot appears (breakpoint set)
2. Click "Run Workflow"
3. Execution hits breakpoint, pauses automatically
4. User can click "Step" to execute one node at a time
5. Or click "Resume" to continue

### Level 4: Variable Inspection

```python
# In WorkflowExecutor - capture state at each step:
class DebugFrame:
    def __init__(self, node_key, inputs, global_state, result):
        self.node_key = node_key
        self.inputs = inputs              # Data inputs to this node
        self.global_state = global_state  # Current global_state
        self.result = result              # What node returned
        self.timestamp = time.time()

# Collect frames during execution:
def run(self):
    debug_frames = []

    for node_key in topological_order:
        inputs = build_inputs(...)
        result = execute_node(...)

        # Capture state snapshot
        frame = DebugFrame(
            node_key,
            inputs,
            copy.deepcopy(global_state),  # Deep copy to preserve snapshot
            result
        )
        debug_frames.append(frame)
        self.debug_frames_signal.emit(debug_frames)

# In MainWindow - show in debug panel:
class DebugPanel(QWidget):
    def show_frame(self, frame: DebugFrame):
        # Show three sections:
        # 1. Inputs (what this node received)
        # 2. Global State (shared dictionary at this point)
        # 3. Output (what this node returned)

        inputs_text = json.dumps(frame.inputs, indent=2)
        global_state_text = json.dumps(frame.global_state, indent=2)
        output_text = json.dumps(frame.result, indent=2)
```

**UI Example:**
```
DEBUG INSPECTOR
═══════════════════════════════════════

Currently Paused At: LoadData_100_200

INPUTS (what this node received)
─────────────────────────────────
{}  (no upstream nodes)

GLOBAL STATE (shared data)
─────────────────────────────────
{
  "db_connection": <sqlite3.Connection>,
  "counter": 0
}

OUTPUT (what this node returned)
─────────────────────────────────
{
  "records": [1, 2, 3, ...],
  "timestamp": "2024-11-06T10:30:00",
  "count": 1000
}
```

Users can click through execution history to see how data changed at each step.

---

## Component Implementation Details

### 4.1 GraphBuilder (`src/core/graph_builder.py`)

**Purpose:** Convert visual layout into executable graphs

**Key Concepts:**
- FLOW graph: Nodes execute in dependency order
- DATA graph: Tracks which node outputs feed which node inputs
- Both graphs are DAGs (Directed Acyclic Graphs)

```python
class GraphBuilder:
    def __init__(self, layout_data: dict, node_registry: NodeRegistry):
        self.layout_data = layout_data
        self.node_registry = node_registry
        self.flow_graph = {}   # Execution graph
        self.data_graph = {}   # Data flow graph
        self.all_nodes = set() # All unique node keys

    def build(self):
        """Build both graphs from layout"""
        self._extract_nodes()
        self._build_flow_graph()
        self._build_data_graph()
        self._validate()
        return self

    def _extract_nodes(self):
        """Get all node keys from layout"""
        self.all_nodes = set(self.layout_data.get('nodes', {}).keys())

    def _build_flow_graph(self):
        """Build from FLOW connections only"""
        self.flow_graph = {node: [] for node in self.all_nodes}

        for conn in self.layout_data.get('connections', []):
            # Only process FLOW connections
            if conn.get('from_type') != 'FLOW':
                continue

            from_node = conn['from_node']
            to_node = conn['to_node']

            if to_node in self.all_nodes:
                self.flow_graph[from_node].append(to_node)

    def _build_data_graph(self):
        """Build from DATA connections only"""
        self.data_graph = {node: [] for node in self.all_nodes}

        for conn in self.layout_data.get('connections', []):
            # Only process DATA connections
            if conn.get('from_type') != 'DATA':
                continue

            from_node = conn['from_node']
            to_node = conn['to_node']
            from_port = conn['from_port']

            if to_node in self.all_nodes:
                self.data_graph[to_node].append((from_node, from_port))

    def _validate(self):
        """Check all nodes exist in registry"""
        for node_key in self.all_nodes:
            title = node_key.split('_')[0]  # Extract from "Title_X_Y"
            if not self.node_registry.get_metadata(title):
                raise ValueError(f"Node '{title}' not found in registry")

    def has_cycle(self) -> bool:
        """Detect cycles in FLOW graph"""
        visited = set()
        rec_stack = set()

        def has_cycle_dfs(node):
            visited.add(node)
            rec_stack.add(node)

            for child in self.flow_graph.get(node, []):
                if child not in visited:
                    if has_cycle_dfs(child):
                        return True
                elif child in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in self.all_nodes:
            if node not in visited:
                if has_cycle_dfs(node):
                    return True

        return False

    def get_entry_nodes(self) -> list:
        """Return nodes with no incoming FLOW connections"""
        in_degree = {node: 0 for node in self.all_nodes}

        for node in self.all_nodes:
            for child in self.flow_graph.get(node, []):
                in_degree[child] += 1

        return [node for node in self.all_nodes if in_degree[node] == 0]
```

### 4.2 Topological Sort (`src/core/topological.py`)

**Purpose:** Determine execution order respecting FLOW dependencies

**Algorithm:** Kahn's algorithm (queue-based, simpler than DFS)

```python
def topological_sort(flow_graph: dict, all_nodes: set) -> list:
    """
    Kahn's algorithm for topological sorting.

    Args:
        flow_graph: {node_key: [child_keys]}
        all_nodes: Set of all node keys

    Returns:
        List of nodes in execution order

    Raises:
        ValueError: If cycle detected
    """
    # Calculate in-degree for each node
    in_degree = {node: 0 for node in all_nodes}

    for node in all_nodes:
        for child in flow_graph.get(node, []):
            in_degree[child] += 1

    # Start with nodes that have no dependencies
    queue = [node for node in all_nodes if in_degree[node] == 0]
    sorted_order = []

    while queue:
        # Pop node with no incoming edges
        node = queue.pop(0)
        sorted_order.append(node)

        # For each child, decrement in-degree
        for child in flow_graph.get(node, []):
            in_degree[child] -= 1

            # If child now has no dependencies, add to queue
            if in_degree[child] == 0:
                queue.append(child)

    # If not all nodes are sorted, cycle exists
    if len(sorted_order) != len(all_nodes):
        raise ValueError("Cycle detected in FLOW graph")

    return sorted_order
```

### 4.3 WorkflowExecutor (`src/core/executor.py`)

**Purpose:** Execute workflow in isolated subprocess

**Key Responsibilities:**
1. Build execution script dynamically
2. Spawn subprocess with venv Python
3. Stream output and status to main thread
4. Handle errors gracefully
5. Support pause/resume/step debugging

```python
from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import json
import tempfile
from pathlib import Path

class WorkflowExecutor(QThread):
    # Signals emitted to main thread
    output_signal = pyqtSignal(str)           # Raw output from script
    status_signal = pyqtSignal(str)           # Status updates
    node_active_signal = pyqtSignal(str, str) # (node_key, status)
    debug_frames_signal = pyqtSignal(list)    # Debug snapshots
    finished_signal = pyqtSignal(bool, str)   # (success, message)

    def __init__(self, project_path: Path, layout_data: dict,
                 venv_manager, node_registry):
        super().__init__()
        self.project_path = Path(project_path)
        self.layout_data = layout_data
        self.venv_manager = venv_manager
        self.node_registry = node_registry

        # Debugging state
        self.paused = False
        self.step_requested = False
        self.breakpoints = set()

    def run(self):
        """Execute workflow in subprocess"""
        try:
            # Step 1: Build graphs
            graph_builder = GraphBuilder(self.layout_data, self.node_registry)
            graph_builder.build()

            # Check for cycles
            if graph_builder.has_cycle():
                self.finished_signal.emit(False, "Cycle detected in FLOW graph")
                return

            # Step 2: Get execution order
            sorted_nodes = topological_sort(
                graph_builder.flow_graph,
                graph_builder.all_nodes
            )

            self.status_signal.emit(f"Executing {len(sorted_nodes)} nodes...")

            # Step 3: Create execution script
            script = self._generate_execution_script(
                sorted_nodes,
                graph_builder.data_graph,
                graph_builder.flow_graph
            )

            # Step 4: Run in subprocess
            success, output = self._run_subprocess(script)

            if success:
                self.status_signal.emit("✓ Execution completed")
                self.finished_signal.emit(True, "Workflow completed successfully")
            else:
                self.status_signal.emit("✗ Execution failed")
                self.finished_signal.emit(False, output)

        except Exception as e:
            self.status_signal.emit(f"✗ Error: {str(e)}")
            self.finished_signal.emit(False, str(e))

    def _generate_execution_script(self, sorted_nodes: list,
                                   data_graph: dict, flow_graph: dict) -> str:
        """Generate Python script that will be executed in subprocess"""

        # Build imports
        imports = self._build_imports()

        # Build node execution code
        node_code = []
        for node_key in sorted_nodes:
            node_code.append(f"""
# Execute: {node_key}
try:
    # Build inputs from DATA connections
    inputs = {{}}
    for parent_key, parent_port in {data_graph.get(node_key, [])}:
        parent_title = parent_key.split('_')[0]
        parent_output = node_outputs.get(parent_key, {{}})
        inputs[parent_title] = parent_output

    # Execute node function
    result = {node_key}(inputs, global_state)
    node_outputs['{node_key}'] = result

    print(f"[OK] {node_key}: {{result}}")
except Exception as e:
    node_errors['{node_key}'] = str(e)
    print(f"[ERROR] {node_key}: {{e}}")
""")

        # Combine into final script
        script = f"""
import json
import sys
sys.path.insert(0, '{self.project_path}')

{imports}

# Initialize execution state
global_state = {{}}
node_outputs = {{}}
node_errors = {{}}

# Execute nodes in topological order
{''.join(node_code)}

# Report results
print(f"[SUMMARY] Nodes: {len(sorted_nodes)}, Succeeded: {len(node_outputs)}, Failed: {len(node_errors)}")
sys.exit(0 if len(node_errors) == 0 else 1)
"""
        return script

    def _build_imports(self) -> str:
        """Generate import statements for all nodes"""
        imports = []

        # Import all node functions
        for fqnn, metadata in self.node_registry.nodes.items():
            file_path = metadata.file_path
            module_name = file_path.stem
            func_name = metadata.function_name

            imports.append(f"from {module_name} import {func_name} as {fqnn.replace('.', '_')}")

        return '\n'.join(imports)

    def _run_subprocess(self, script: str) -> tuple[bool, str]:
        """Execute script in subprocess and return (success, output)"""

        python_path = self.venv_manager.get_python_path()

        try:
            process = subprocess.Popen(
                [python_path, '-c', script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self.project_path)
            )

            output_lines = []
            for line in process.stdout:
                output_lines.append(line.rstrip())
                self.output_signal.emit(line)

            process.wait()

            return (
                process.returncode == 0,
                '\n'.join(output_lines)
            )

        except Exception as e:
            return False, f"Failed to run subprocess: {str(e)}"
```

### 4.4 UI Integration (`src/main.py`)

```python
# Add to MainWindow class:

def run_workflow(self):
    """Execute the current workflow"""
    if not self.current_project_path:
        QMessageBox.warning(self, "No Project", "Open a project first.")
        return

    # Validate venv
    if not self.venv_manager.venv_exists():
        QMessageBox.warning(self, "No Venv",
            "Virtual environment not found. Create dependencies first.")
        return

    # Load layout
    layout_path = self.current_project_path / ".layout.json"
    layout_data = self.layout_manager.load_layout_data(str(layout_path))

    # Create executor
    self.executor = WorkflowExecutor(
        self.current_project_path,
        layout_data,
        self.venv_manager,
        self.node_registry
    )

    # Connect signals
    self.executor.output_signal.connect(self.console.write)
    self.executor.status_signal.connect(self.status_bar.show_temporary_message)
    self.executor.node_active_signal.connect(self._on_node_active)
    self.executor.debug_frames_signal.connect(self._on_debug_frames)
    self.executor.finished_signal.connect(self._on_execution_finished)

    # Clear console and start
    self.console.clear()
    self.console.write("=== Starting workflow execution ===\n")
    self.executor.start()

    # Disable run button, enable pause/resume
    self.run_action.setEnabled(False)
    self.pause_action.setEnabled(True)
    self.resume_action.setEnabled(False)

def pause_execution(self):
    """Pause the currently running workflow"""
    if self.executor:
        self.executor.paused = True
        self.pause_action.setEnabled(False)
        self.resume_action.setEnabled(True)
        self.status_bar.show_temporary_message("Execution paused", 0)

def resume_execution(self):
    """Resume the paused workflow"""
    if self.executor:
        self.executor.paused = False
        self.pause_action.setEnabled(True)
        self.resume_action.setEnabled(False)
        self.status_bar.show_temporary_message("Execution resumed", 0)

def step_execution(self):
    """Step through execution one node at a time"""
    if self.executor:
        self.executor.step_requested = True

def _on_node_active(self, node_key: str, status: str):
    """Update canvas when node becomes active"""
    # Find node on canvas and highlight
    for item in self.canvas.scene.items():
        if isinstance(item, NodeItem) and item.key == node_key:
            if status == "running":
                item.set_highlight_color("#FFD700")  # Gold
            elif status == "complete":
                item.set_highlight_color("#00AA00")  # Green
            elif status == "failed":
                item.set_highlight_color("#FF0000")  # Red
            item.update()
            break

def _on_execution_finished(self, success: bool, message: str):
    """Handle execution completion"""
    self.run_action.setEnabled(True)
    self.pause_action.setEnabled(False)
    self.resume_action.setEnabled(False)

    if success:
        self.console.write("\n=== ✓ Execution completed successfully ===\n")
        self.status_bar.show_temporary_message("✓ Workflow completed", 3000)
    else:
        self.console.write(f"\n=== ✗ Execution failed: {message} ===\n")
        QMessageBox.critical(self, "Execution Failed", message)
```

---

## Testing Strategy

### Unit Tests (Before Integration)

**Test GraphBuilder:**
```python
def test_simple_linear_graph():
    """A -> B -> C"""
    layout = {
        'nodes': {'A_0_0': {}, 'B_100_0': {}, 'C_200_0': {}},
        'connections': [
            {'from_node': 'A_0_0', 'to_node': 'B_100_0', 'from_type': 'FLOW'},
            {'from_node': 'B_100_0', 'to_node': 'C_200_0', 'from_type': 'FLOW'}
        ]
    }

    builder = GraphBuilder(layout, registry)
    builder.build()

    assert builder.flow_graph == {
        'A_0_0': ['B_100_0'],
        'B_100_0': ['C_200_0'],
        'C_200_0': []
    }
    assert not builder.has_cycle()

def test_cycle_detection():
    """A -> B -> C -> A (cycle!)"""
    # Should raise or return True for has_cycle()
```

**Test Topological Sort:**
```python
def test_execution_order():
    """Verify topological order respects dependencies"""
    graph = {
        'A': ['B', 'C'],      # A runs first
        'B': ['D'],           # B runs before D
        'C': ['D'],           # C also runs before D
        'D': []
    }

    order = topological_sort(graph, set(graph.keys()))

    # A must come before B and C
    assert order.index('A') < order.index('B')
    assert order.index('A') < order.index('C')

    # B and C must come before D
    assert order.index('B') < order.index('D')
    assert order.index('C') < order.index('D')
```

### Integration Tests (With Real Nodes)

**Test Case 1: Basic Sequential Execution**
```python
def test_sequential_nodes():
    """Create simple nodes: Increment -> Increment -> Increment"""
    # Arrange: Create test workflow with 3 nodes
    # Act: Run executor
    # Assert: global_state['counter'] == 3
```

**Test Case 2: Data Passing**
```python
def test_data_connections():
    """LoadData -> ProcessData -> SaveData"""
    # Arrange: Create nodes with data connections
    # Act: Run executor
    # Assert: SaveData received correct processed data
```

**Test Case 3: Error Isolation**
```python
def test_continue_on_error():
    """
    A (success)
    A -> B (fails)
    A -> C (success)

    Should execute: A, B (fail), C
    """
    # Arrange: Create branching graph with error in B
    # Act: Run executor
    # Assert: C still executes, C has access to A's output
```

**Test Case 4: Conditional Branching**
```python
def test_boolean_branching():
    """CheckAuth returns is_valid=True, next node processes normally"""
    # Arrange: CheckAuth -> ProcessRequest
    # Act: Run with valid credentials
    # Assert: ProcessRequest executes and completes

    # Then: Run with invalid credentials
    # Arrange: CheckAuth returns is_valid=False
    # Act: Run again
    # Assert: ProcessRequest still executes but returns early
```

### Manual Testing Checklist

- [ ] Create new project with 2-3 simple nodes
- [ ] Create FLOW connections (A -> B -> C)
- [ ] Click Run, watch nodes highlight in sequence
- [ ] Verify output in console shows node execution
- [ ] Test Pause/Resume buttons
- [ ] Test Step button (one node at a time)
- [ ] Set breakpoint on middle node
- [ ] Run, should pause at breakpoint
- [ ] Check debug panel shows inputs/global_state
- [ ] Click Resume to continue
- [ ] Create workflow with data connections
- [ ] Verify data flows correctly between nodes
- [ ] Create conditional workflow
- [ ] Run with valid condition (verify behavior)
- [ ] Run with invalid condition (verify behavior)
- [ ] Intentionally cause error in one node
- [ ] Verify other branches continue
- [ ] Check console shows error message

---

## Implementation Phases

### Phase 4.1: GraphBuilder & Topological Sort (Days 1-2)
- Implement GraphBuilder
- Implement Topological sort
- Unit tests for both
- No UI changes yet

### Phase 4.2: Basic Executor (Days 3-4)
- Implement WorkflowExecutor (without debugging)
- Generate execution scripts
- Subprocess execution
- Basic signal connections

### Phase 4.3: UI Integration & Debugging (Days 5-7)
- Add Run button to toolbar
- Implement pause/resume/step
- Add node highlighting
- Implement breakpoints
- Add debug inspector panel
- Connect all signals to UI

### Phase 4.4: Testing & Polish (Days 8-9)
- Unit tests
- Integration tests
- Manual testing with real workflows
- Error messages refinement
- Performance optimization

---

## Future Enhancements (Phase 5+)

### Loop Support
- ForEach nodes with iteration count
- While nodes with condition port
- Loop variables in global_state

### Parallel Execution
- Nodes with no dependencies execute concurrently
- Thread pool in executor
- Visual indication of parallel branches

### Advanced Debugging
- Record full execution history
- "Undo" to earlier execution point
- Time travel debugging

### Visual Enhancements
- Connection highlight when hovering node (shows data flow)
- Execution timeline view
- Performance metrics (node execution time)

---

## Common Pitfalls & Solutions

### Pitfall 1: Circular Data Dependencies
**Problem:** Node A depends on B's output, B depends on A's output

**Solution:** Already handled by topological sort - would fail at graph validation

### Pitfall 2: Infinite Global State Mutation
**Problem:** Node modifies global_state in ways that cause infinite loops

**Solution:** Not preventable (users are writing code), but debug inspector shows state changes

### Pitfall 3: Slow Subprocess Startup
**Problem:** Creating new process for every workflow run is slow

**Solution (Future):** Implement long-lived executor process that receives code to run

### Pitfall 4: Import Errors from Dependencies
**Problem:** workflow.py imports packages that aren't installed in venv

**Solution:** Installation step (Phase 3) must complete before execution; error message guides user

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│              PyWorks GUI (Qt Main Thread)            │
│  ┌───────────────────────────────────────────────┐  │
│  │ MainWindow                                     │  │
│  │ - Run button clicked                          │  │
│  │ - Create WorkflowExecutor(thread)             │  │
│  │ - Connect signals                             │  │
│  │ - Start thread                                │  │
│  └──────────────┬──────────────────────────────┘  │
│                 │ (spawns)                        │
├─────────────────┼────────────────────────────────┤
│                 ↓                                 │
│  ┌───────────────────────────────────────────┐   │
│  │ WorkflowExecutor (Qt Thread)              │   │
│  │ 1. Build graphs (GraphBuilder)            │   │
│  │ 2. Topological sort                       │   │
│  │ 3. Generate Python script                 │   │
│  │ 4. Spawn subprocess                       │   │
│  │ 5. Stream output to main thread           │   │
│  │ 6. Emit signals (node_active, finished)   │   │
│  └───────────────┬───────────────────────────┘   │
│                  │ (spawns)                      │
├──────────────────┼──────────────────────────────┤
│                  ↓                               │
│       ┌──────────────────────────┐              │
│       │  Subprocess (Isolated)    │              │
│       │  - Venv Python            │              │
│       │ - Execute nodes in order  │              │
│       │ - Print results           │              │
│       │ - Return exit code        │              │
│       └──────────────────────────┘              │
└─────────────────────────────────────────────────┘

Signal Flow:
WorkflowExecutor → (signals) → MainWindow → update GUI
```

---

## Summary

This Phase 4 implementation:

✅ **Is robust** - Continues on errors, prevents infinite loops, validates graphs
✅ **Is debuggable** - Four levels of debugging support
✅ **Is flexible** - Supports boolean branching without special nodes
✅ **Is isolated** - User code crashes don't crash editor
✅ **Is future-proof** - Architecture ready for loops, parallel execution, advanced features
✅ **Is tested** - Unit tests, integration tests, manual testing plan included

The execution engine transforms PyWorks from a visual node editor into a fully functional workflow execution system. It's the culmination of Phases 1-3 and the foundation for all future features.
