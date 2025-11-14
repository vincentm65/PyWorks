# PyWorks Development Plan

## Overview

PyWorks is a visual scripting editor for Python that bridges visual programming and traditional scripting. Users write Python functions decorated with `@node`, and the editor displays them as draggable nodes on a canvas with port-based connections.

---

## Phase Status

### ✅ Phase 1: Core UI and Canvas (95% Complete)
- Main window, menubar, toolbar
- Project management system (new/open/save)
- Canvas with zoom, pan, grid snapping
- Node drag-and-drop from palette
- Port-based connection system (4 ports per node)
- ConnectionBridge with orthogonal routing
- Layout save/load system (.layout.json)
- Status bar

**Remaining:**
- Manual node creation dialog (minor)
- Remove debug prints

### ✅ Phase 2: Dynamic Node Loading (100% Complete)
- AST parsing (`src/core/ast_utils.py`)
- `@node` decorator discovery
- Node registry system (`src/core/node_registry.py`)
- "Reload Script" button functionality
- Automatic Node List population

### 🔨 Phase 3: Virtual Environment Management (0% Complete - NEXT)
**Goal:** Isolate project dependencies using virtual environments

### 🔨 Phase 4: Execution Engine (0% Complete - AFTER PHASE 3)
**Goal:** Execute node graphs with data flow

---

## Phase 3: Virtual Environment Management

### Architecture Decisions
- Each project gets its own `.venv` folder
- Use venv Python for script reloading and execution
- Async package installation (QThread to avoid blocking UI)
- Install from `requirements.txt` in project folder

### Implementation Tasks

#### 3.1 Create VenvManager Module
**File:** `src/core/venv_manager.py`

**Responsibilities:**
```python
class VenvManager:
    def __init__(self, project_path):
        """Initialize with project directory path."""

    def venv_exists(self) -> bool:
        """Check if .venv folder exists and is valid."""

    def create_venv(self) -> bool:
        """Create virtual environment using python -m venv .venv"""

    def get_python_path(self) -> str:
        """Return path to venv Python executable."""

    def get_pip_path(self) -> str:
        """Return path to venv pip executable."""

    def validate_venv(self) -> bool:
        """Check if venv is healthy and usable."""
```

**Implementation Details:**
- Venv location: `{project_path}/.venv/`
- Windows Python path: `.venv/Scripts/python.exe`
- Unix Python path: `.venv/bin/python`
- Use `subprocess.run()` to create venv
- Validate by checking Python executable exists and runs

#### 3.2 Add Package Installation System
**File:** `src/core/package_installer.py`

**Create QThread for async installation:**
```python
class PackageInstallThread(QThread):
    output_signal = pyqtSignal(str)      # Emit installation output
    progress_signal = pyqtSignal(int)    # Emit progress percentage
    finished_signal = pyqtSignal(bool)   # Emit success/failure

    def __init__(self, pip_path, requirements_file):
        """Initialize with pip path and requirements.txt path."""

    def run(self):
        """Execute pip install -r requirements.txt in subprocess."""
```

**Implementation Details:**
- Read `requirements.txt` line by line to count packages
- Run `pip install -r requirements.txt` using venv pip
- Stream stdout/stderr to console using `output_signal`
- Calculate progress based on package count
- Handle errors gracefully (missing requirements.txt, failed installs)

#### 3.3 Wire Up to Project System

**Modify `src/utils/project_manager.py`:**
- Add `venv_manager` attribute to project
- On project open/create:
  1. Check if venv exists
  2. If not, create venv automatically
  3. Initialize venv_manager

**Modify `src/main.py`:**
- Import `VenvManager` and `PackageInstallThread`
- Add "Install Dependencies" menu item to Tools menu
- Add venv status indicator to status bar:
  - "Venv: Ready" (green) when venv exists and valid
  - "Venv: Missing" (red) when venv doesn't exist
  - "Venv: Installing..." (yellow) during package installation

**Install Dependencies Workflow:**
1. User clicks "Tools > Install Dependencies"
2. Validate venv exists (create if missing)
3. Launch `PackageInstallThread`
4. Stream output to console widget
5. Show progress in status bar
6. On completion, show success/error message

#### 3.4 Modify Script Reload to Use Venv

**Update `src/main.py` `reload_script()` method:**
- Change from using system Python to venv Python
- Use `venv_manager.get_python_path()` for imports
- Ensure node discovery works with venv packages

**Current (system Python):**
```python
def reload_script(self):
    discovered = node_registry.discover(self.current_project)
    self.node_list_widget.populate_from_registry(discovered)
```

**Updated (venv Python):**
```python
def reload_script(self):
    # Get venv Python path
    python_path = self.venv_manager.get_python_path()

    # Discover nodes using venv interpreter
    discovered = node_registry.discover(self.current_project, python_path)
    self.node_list_widget.populate_from_registry(discovered)
```

---

## Phase 4: Execution Engine

### Architecture Decisions
- **FLOW connections (grey lines) determine execution order**
  - Explicit control flow (A→B→C means "run in this order")
- **DATA connections (purple lines) determine data routing**
  - Can skip nodes (A→C means "C receives A's output, even if B runs in between")
- **Subprocess isolation from day 1**
  - Use venv Python executable
  - Prevents main process crashes from user code
- **Data passing model:**
  - `global_state`: Dictionary shared across all nodes
  - `inputs`: Dictionary containing parent node outputs, namespaced by node key

### Implementation Tasks

#### 4.1 Build Graph/DAG System
**File:** `src/core/graph_builder.py`

**Responsibilities:**
```python
class GraphBuilder:
    def __init__(self, layout_data, node_registry):
        """Initialize with .layout.json data and discovered nodes."""

    def build_execution_graph(self) -> dict:
        """Build adjacency list from FLOW connections only."""
        # Returns: {"NodeA_100_200": ["NodeB_300_200"], ...}

    def build_data_graph(self) -> dict:
        """Build data dependency map from DATA connections."""
        # Returns: {"NodeC_500_200": [("NodeA_100_200", "output_data")], ...}

    def detect_cycles(self) -> bool:
        """Check if execution graph has cycles."""

    def get_entry_nodes(self) -> list:
        """Return nodes with no incoming FLOW connections."""
```

**Implementation Details:**
- Parse `connections` from `.layout.json`
- Filter FLOW connections (type == "FLOW")
- Build adjacency list: `node_key -> [child_node_keys]`
- Use DFS to detect cycles
- Entry nodes are nodes with in-degree 0 in FLOW graph

#### 4.2 Implement Topological Sort
**File:** `src/core/topological.py`

**Implementation:**
```python
def topological_sort(adjacency_list: dict) -> list:
    """
    Kahn's algorithm for topological ordering.

    Args:
        adjacency_list: {node_key: [child_keys]}

    Returns:
        Ordered list of node_keys, or raises CycleError
    """
```

**Algorithm (Kahn's):**
1. Calculate in-degree for each node
2. Add all nodes with in-degree 0 to queue
3. While queue not empty:
   - Pop node, add to result
   - For each child, decrement in-degree
   - If child in-degree becomes 0, add to queue
4. If result length != total nodes, cycle detected

#### 4.3 Create Executor
**File:** `src/core/executor.py`

**Main Class:**
```python
class WorkflowExecutor(QThread):
    output_signal = pyqtSignal(str)       # Stream execution output
    status_signal = pyqtSignal(str)       # Execution status updates
    finished_signal = pyqtSignal(bool, str)  # Success/failure + message

    def __init__(self, project_path, layout_data, venv_manager, node_registry):
        """Initialize with project context."""

    def run(self):
        """Execute workflow in subprocess."""
```

**Execution Flow:**
1. Build execution graph (FLOW connections)
2. Build data graph (DATA connections)
3. Detect cycles (abort if found)
4. Compute topological sort
5. Initialize `global_state = {}`
6. Initialize `node_outputs = {}` (stores return values by node key)
7. For each node in execution order:
   a. Build `inputs` dict from data graph
   b. Import node function using metadata from `node_registry`
   c. Call `result = node_func(inputs, global_state)`
   d. Store result in `node_outputs[node_key] = result`
   e. Stream output to console
8. Report final success/failure

**Building `inputs` Dictionary:**
```python
def build_inputs(node_key, data_graph, node_outputs):
    """
    Build inputs dict for a node based on DATA connections.

    Args:
        node_key: Current node being executed
        data_graph: {node_key: [(parent_key, parent_port), ...]}
        node_outputs: {node_key: returned_dict, ...}

    Returns:
        inputs dict: {parent_title: parent_output_dict, ...}
    """
    inputs = {}

    for parent_key, parent_port in data_graph.get(node_key, []):
        parent_title = parent_key.split('_')[0]  # Extract title from "GetData_100_200"
        parent_output = node_outputs.get(parent_key, {})
        inputs[parent_title] = parent_output

    return inputs
```

**Subprocess Execution:**
```python
# Create Python script dynamically
script = f"""
import sys
sys.path.insert(0, '{project_path}')

# Import all node functions
# ... (build imports from node_registry)

# Execute in topological order
global_state = {{}}
node_outputs = {{}}

# For each node:
inputs = {inputs_dict}
result = node_function(inputs, global_state)
node_outputs['{node_key}'] = result
print(f"[{node_key}] Completed: {{result}}")
"""

# Run in subprocess
process = subprocess.Popen(
    [venv_python, '-c', script],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Stream output
for line in process.stdout:
    self.output_signal.emit(line)
```

#### 4.4 Wire Up UI

**Add to `src/main.py`:**

**Toolbar Button:**
- Add "Run Workflow" button with play icon
- Keyboard shortcut: Ctrl+R (or Cmd+R on Mac)

**Menu Item:**
- Add "Workflow > Run" menu item

**Run Workflow Handler:**
```python
def run_workflow(self):
    """Execute current workflow."""
    # Validate project loaded
    if not self.current_project:
        QMessageBox.warning(self, "No Project", "Open a project first.")
        return

    # Validate venv exists
    if not self.venv_manager.venv_exists():
        reply = QMessageBox.question(
            self,
            "Venv Missing",
            "Virtual environment not found. Create now?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.venv_manager.create_venv()
        else:
            return

    # Load layout
    layout_data = self.layout_manager.load_layout(self.current_project)

    # Create executor thread
    self.executor = WorkflowExecutor(
        self.current_project,
        layout_data,
        self.venv_manager,
        node_registry
    )

    # Connect signals
    self.executor.output_signal.connect(self.console_widget.append_output)
    self.executor.status_signal.connect(self.update_status)
    self.executor.finished_signal.connect(self.execution_finished)

    # Start execution
    self.console_widget.clear()
    self.console_widget.append_output("[WORKFLOW] Starting execution...\n")
    self.executor.start()

def execution_finished(self, success, message):
    """Handle execution completion."""
    if success:
        self.console_widget.append_output(f"[WORKFLOW] ✓ Completed successfully\n")
        self.statusBar().showMessage("Execution complete", 3000)
    else:
        self.console_widget.append_output(f"[WORKFLOW] ✗ Error: {message}\n")
        QMessageBox.critical(self, "Execution Failed", message)
```

**Update Status Bar:**
- Show "Running..." during execution
- Show "Complete" or "Failed" after execution
- Clear after 3 seconds

#### 4.5 Testing Plan

**Test with vincent Project:**

Current graph structure:
- 4 nodes across 2 categories
- Both FLOW and DATA connections present

**Test Cases:**

1. **Basic Sequential Execution:**
   - Create simple A→B→C FLOW chain
   - Verify execution order in console output
   - Verify each node completes before next starts

2. **Data Flow Skipping Nodes:**
   - Create FLOW: A→B→C
   - Create DATA: A→C (skipping B)
   - Verify C receives A's output
   - Verify B still executes in sequence

3. **Cycle Detection:**
   - Create FLOW: A→B→C→A (cycle)
   - Verify error message before execution
   - Console shows "Cycle detected" error

4. **Error Handling:**
   - Create node that raises exception
   - Verify execution stops
   - Error message displayed in console
   - Stack trace captured

5. **Global State Persistence:**
   - Create node A that sets `global_state['counter'] = 0`
   - Create node B that increments `global_state['counter'] += 1`
   - Create node C that reads and prints counter
   - Verify state persists across nodes

---

## Future Phases (Post-Execution)

### Phase 5: Visual Execution Feedback
- Node visual states (pending/running/complete/error)
- Progress bar for multi-node workflows
- Real-time node highlighting during execution
- Animated data flow along connections

### Phase 6: Data Inspector
- Show `global_state` contents during/after execution
- Show each node's output (`node_outputs`)
- Interactive data viewer (tables, charts, JSON trees)

### Phase 7: Advanced Features
- Breakpoints for debugging
- Step-through execution mode
- Node execution time metrics
- Workflow optimization suggestions

---