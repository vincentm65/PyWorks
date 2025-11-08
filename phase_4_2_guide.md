# Phase 4.2: Basic Executor - Step-by-Step Implementation Guide

## Overview
This guide walks you through implementing the **WorkflowExecutor** - the component that takes your visual node graph and executes it in an isolated subprocess. By the end of this phase, you'll be able to click a "Run" button and watch your workflow execute!

**Current Status:**
- ✅ Phase 4.1 Complete: GraphBuilder and topological sort are working
- 🎯 Phase 4.2 Goal: Implement basic executor (without debugging features)

---

## Architecture Recap

### How Execution Works (Big Picture)

```
User clicks "Run" button
    ↓
MainWindow creates WorkflowExecutor thread
    ↓
WorkflowExecutor builds graphs (uses GraphBuilder from Phase 4.1)
    ↓
WorkflowExecutor generates Python script
    ↓
WorkflowExecutor spawns subprocess with venv Python
    ↓
Subprocess executes nodes in order
    ↓
Output streams back to MainWindow console
    ↓
Execution completes (success or failure)
```

### Key Concepts

**1. QThread (Background Thread)**
- WorkflowExecutor runs in a separate thread so the GUI stays responsive
- Uses Qt signals to communicate with the main thread
- Think of it like: "GUI says 'go!', executor does work, then reports back"

**2. Subprocess Isolation**
- User's Python code runs in a completely separate process
- If their code crashes, the editor stays alive
- Uses the virtual environment's Python interpreter

**3. Dynamic Script Generation**
- We build a Python script as a string
- Script contains all the imports and execution logic
- Pass it to subprocess with `python -c "script"`

---

## Step-by-Step Implementation

### Step 1: Understand the Executor Class Structure

The `WorkflowExecutor` class needs these parts:

```python
from PyQt6.QtCore import QThread, pyqtSignal
import subprocess
import tempfile
from pathlib import Path

class WorkflowExecutor(QThread):
    # Signals - ways to talk back to the main thread
    output_signal = pyqtSignal(str)        # Send console output
    status_signal = pyqtSignal(str)        # Send status updates
    finished_signal = pyqtSignal(bool, str) # Send completion (success?, message)

    def __init__(self, project_path, layout_data, venv_manager, node_registry):
        super().__init__()
        # Store what we need to execute
        self.project_path = Path(project_path)
        self.layout_data = layout_data
        self.venv_manager = venv_manager
        self.node_registry = node_registry

    def run(self):
        # This method runs in the background thread
        # It's called automatically when you do: executor.start()
        pass
```

**Key Points:**
- `QThread` = runs in background so GUI doesn't freeze
- `pyqtSignal` = safe way to send data from background thread to main thread
- `run()` = automatically called when thread starts

---

### Step 2: Implement the `run()` Method Flow

The `run()` method is the heart of the executor. Here's the step-by-step logic:

```python
def run(self):
    """Execute workflow in subprocess"""
    try:
        # STEP 1: Build the graph structure
        # STEP 2: Get execution order
        # STEP 3: Generate Python script
        # STEP 4: Run script in subprocess
        # STEP 5: Report success
    except Exception as e:
        # STEP 6: Report failure
        pass
```

Let's implement each step:

#### Step 2.1: Build Graphs and Get Execution Order

```python
def run(self):
    try:
        # STEP 1: Build graphs using GraphBuilder from Phase 4.1
        from .graph_builder import GraphBuilder
        from .topological import topological_sort

        self.status_signal.emit("Building execution graph...")

        graph_builder = GraphBuilder(self.layout_data, self.node_registry)
        graph_builder.build()

        # STEP 1.5: Check for cycles (infinite loops)
        if graph_builder.has_cycle():
            self.finished_signal.emit(False, "Cycle detected in FLOW graph - execution would loop forever!")
            return

        # STEP 2: Get execution order (which node runs first, second, etc.)
        sorted_nodes = topological_sort(
            graph_builder.flow_graph,
            graph_builder.all_nodes
        )

        self.status_signal.emit(f"Executing {len(sorted_nodes)} nodes...")
```

**What's happening:**
- `GraphBuilder` analyzes your connections to figure out dependencies
- `has_cycle()` prevents infinite loops
- `topological_sort()` gives us the correct order to run nodes
- We emit status signals so the GUI can show progress

---

#### Step 2.2: Generate the Execution Script

This is where we create the Python code that will run in the subprocess.

```python
        # STEP 3: Generate Python script
        script = self._generate_execution_script(
            sorted_nodes,
            graph_builder.data_graph,
            graph_builder.flow_graph
        )
```

Now we need to implement `_generate_execution_script()`:

```python
def _generate_execution_script(self, sorted_nodes: list,
                                data_graph: dict,
                                flow_graph: dict) -> str:
    """
    Generate Python script that will execute in subprocess.

    Args:
        sorted_nodes: List of node keys in execution order
        data_graph: {node_key: [(parent_node, parent_port), ...]}
        flow_graph: {node_key: [child_keys]}

    Returns:
        Python script as a string
    """

    # Build imports for all node functions
    imports = self._build_imports()

    # Build execution code for each node
    node_execution_code = []

    for node_key in sorted_nodes:
        # Extract the function name from the node key
        # node_key format: "module.function_100_200"
        fqnn = node_key.rsplit('_', 2)[0]  # Get "module.function"

        # Build code for this node
        node_code = f"""
# ===== Execute: {node_key} =====
try:
    # Build inputs dictionary from parent nodes
    inputs = {{}}
    data_parents = {data_graph.get(node_key, [])}

    for parent_key, parent_port in data_parents:
        parent_fqnn = parent_key.rsplit('_', 2)[0]
        parent_output = node_outputs.get(parent_key, {{}})
        inputs[parent_fqnn] = parent_output

    # Call the node function
    result = {fqnn.replace('.', '_')}(inputs, global_state)

    # Store result for downstream nodes
    node_outputs['{node_key}'] = result if result else {{}}

    print(f"[OK] {node_key}")
    if result:
        print(f"     Output: {{result}}")

except Exception as e:
    node_errors['{node_key}'] = str(e)
    print(f"[ERROR] {node_key}: {{e}}")
    import traceback
    traceback.print_exc()
"""
        node_execution_code.append(node_code)

    # Combine everything into final script
    script = f"""
import sys
import os

# Add project path so we can import user's modules
sys.path.insert(0, r'{self.project_path}')

{imports}

# Initialize execution state
global_state = {{}}       # Shared across all nodes
node_outputs = {{}}       # Store results: {{node_key: output_dict}}
node_errors = {{}}        # Track failures: {{node_key: error_message}}

print("=" * 60)
print("WORKFLOW EXECUTION STARTED")
print("=" * 60)

# Execute nodes in topological order
{''.join(node_execution_code)}

# Print summary
print()
print("=" * 60)
print("EXECUTION SUMMARY")
print("=" * 60)
succeeded = len(sorted_nodes) - len(node_errors)
print(f"Total nodes: {len(sorted_nodes)}")
print(f"Succeeded: {{succeeded}}")
print(f"Failed: {{len(node_errors)}}")

if node_errors:
    print()
    print("Failed nodes:")
    for node_key, error in node_errors.items():
        print(f"  - {{node_key}}: {{error}}")

# Exit with failure code if any errors occurred
sys.exit(0 if len(node_errors) == 0 else 1)
"""

    return script
```

**What's happening:**
- We loop through nodes in execution order
- For each node, we generate Python code that:
  1. Builds the `inputs` dictionary from parent nodes
  2. Calls the node function
  3. Stores the result
  4. Handles errors gracefully
- All this code gets wrapped in a complete Python script

---

#### Step 2.3: Build Import Statements

We need to import all the node functions from the user's code:

```python
def _build_imports(self) -> str:
    """Generate import statements for all registered nodes"""
    imports = []

    for fqnn, metadata in self.node_registry.nodes.items():
        # fqnn = "workflow.get_data"
        # We need to import it as "workflow_get_data" (replace . with _)

        parts = fqnn.split('.')
        module_name = parts[0]      # "workflow"
        func_name = parts[1]        # "get_data"
        safe_name = fqnn.replace('.', '_')  # "workflow_get_data"

        imports.append(f"from {module_name} import {func_name} as {safe_name}")

    return '\n'.join(imports)
```

**Why do we rename with underscores?**
- Node keys use format: `workflow.get_data_100_200`
- We can't use dots in Python variable names
- So we convert to: `workflow_get_data_100_200`

---

#### Step 2.4: Run the Script in Subprocess

Now that we have our script, we need to execute it:

```python
        # STEP 4: Run script in subprocess
        success, output = self._run_subprocess(script)

        # STEP 5: Report results
        if success:
            self.status_signal.emit("✓ Execution completed successfully")
            self.finished_signal.emit(True, "Workflow completed successfully")
        else:
            self.status_signal.emit("✗ Execution failed")
            self.finished_signal.emit(False, "Workflow failed - check console for errors")

    except Exception as e:
        # STEP 6: Handle any exceptions
        self.status_signal.emit(f"✗ Error: {str(e)}")
        self.finished_signal.emit(False, str(e))
```

Now implement `_run_subprocess()`:

```python
def _run_subprocess(self, script: str) -> tuple[bool, str]:
    """
    Execute script in subprocess and stream output.

    Args:
        script: Python script to execute

    Returns:
        (success, output) tuple
    """

    # Get the venv Python path (from Phase 3)
    python_path = self.venv_manager.get_python_path()

    try:
        # Spawn subprocess
        # -u flag = unbuffered output (we see output immediately)
        process = subprocess.Popen(
            [str(python_path), '-u', '-c', script],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,                 # Get strings, not bytes
            cwd=str(self.project_path) # Run from project directory
        )

        # Stream output line by line
        output_lines = []
        for line in process.stdout:
            line = line.rstrip()  # Remove trailing newline
            output_lines.append(line)
            self.output_signal.emit(line + '\n')  # Send to console

        # Wait for process to finish
        process.wait()

        # Check exit code (0 = success, non-zero = failure)
        return (
            process.returncode == 0,
            '\n'.join(output_lines)
        )

    except Exception as e:
        error_msg = f"Failed to run subprocess: {str(e)}"
        self.output_signal.emit(error_msg + '\n')
        return False, error_msg
```

**What's happening:**
- `subprocess.Popen` starts a new Python process
- We use `-c` flag to pass script as string (instead of file)
- `stdout=subprocess.PIPE` lets us read output
- We loop through output line-by-line and emit to GUI
- Return code 0 means success, anything else is failure

---

### Step 3: Connect Executor to Main Window

Now we need to wire up the executor in `main.py`. Let me check the current main window structure:

```python
# In MainWindow class (src/main.py)

def _setup_toolbar_actions(self):
    """Add this to your existing toolbar setup"""

    # ... existing actions (New, Open, Save) ...

    # Add separator
    self.toolbar.addSeparator()

    # Add Run button
    self.run_action = QAction("▶ Run Workflow", self)
    self.run_action.setShortcut("F5")
    self.run_action.setToolTip("Execute the workflow (F5)")
    self.run_action.triggered.connect(self.run_workflow)
    self.toolbar.addAction(self.run_action)

def run_workflow(self):
    """Execute the current workflow"""

    # Validation checks
    if not self.current_project_path:
        QMessageBox.warning(self, "No Project",
            "Please open a project before running.")
        return

    if not self.venv_manager.venv_exists():
        QMessageBox.warning(self, "No Virtual Environment",
            "Virtual environment not found. Please install dependencies first.")
        return

    # Load layout data
    layout_path = self.current_project_path / ".layout.json"
    if not layout_path.exists():
        QMessageBox.warning(self, "No Layout",
            "Layout file not found. Please save your workflow first.")
        return

    layout_data = self.layout_manager.load_layout_data(str(layout_path))

    # Check if there are any nodes to execute
    if not layout_data.get('nodes'):
        QMessageBox.information(self, "Empty Workflow",
            "Add some nodes to the canvas before running.")
        return

    # Create executor thread
    from src.core.executor import WorkflowExecutor

    self.executor = WorkflowExecutor(
        self.current_project_path,
        layout_data,
        self.venv_manager,
        self.node_registry
    )

    # Connect signals
    self.executor.output_signal.connect(self.console.write)
    self.executor.status_signal.connect(self._on_executor_status)
    self.executor.finished_signal.connect(self._on_execution_finished)

    # Clear console and start
    self.console.clear()
    self.console.write("Starting workflow execution...\n")

    # Disable run button while executing
    self.run_action.setEnabled(False)

    # Start executor thread
    self.executor.start()

def _on_executor_status(self, message: str):
    """Handle status updates from executor"""
    self.statusBar().showMessage(message, 3000)  # Show for 3 seconds

def _on_execution_finished(self, success: bool, message: str):
    """Handle execution completion"""

    # Re-enable run button
    self.run_action.setEnabled(True)

    if success:
        self.console.write("\n✓ Execution completed successfully!\n")
        self.statusBar().showMessage("✓ Workflow completed", 5000)
    else:
        self.console.write(f"\n✗ Execution failed: {message}\n")
        QMessageBox.warning(self, "Execution Failed", message)
```

---

### Step 4: Create a Test Workflow

To test if everything works, create a simple test workflow:

**File: `test_project/workflow.py`**
```python
from pyworks import node

@node
def start_node(inputs, global_state):
    """Initialize the workflow"""
    print("Starting workflow...")
    global_state['counter'] = 0
    return {
        "message": "Workflow started",
        "timestamp": "2024-11-07"
    }

@node
def increment_counter(inputs, global_state):
    """Increment the counter"""
    global_state['counter'] += 1
    count = global_state['counter']
    print(f"Counter incremented to: {count}")
    return {
        "current_count": count
    }

@node
def finish_node(inputs, global_state):
    """Finish the workflow"""
    start_data = inputs.get('workflow.start_node', {})
    increment_data = inputs.get('workflow.increment_counter', {})

    print(f"Workflow finished!")
    print(f"Start message: {start_data.get('message')}")
    print(f"Final count: {increment_data.get('current_count')}")

    return {
        "status": "complete"
    }
```

**Visual Layout:**
```
[start_node] --FLOW--> [increment_counter] --FLOW--> [finish_node]
      |                                                     ↑
      +------------------DATA----------------------------+
                              |
      +------------------DATA----------------------------+
```

---

## Testing Checklist

Once implemented, test in this order:

### Test 1: Single Node
- [ ] Create workflow with 1 node
- [ ] Click Run
- [ ] Verify output appears in console
- [ ] Verify success message

### Test 2: Sequential Nodes (FLOW connections)
- [ ] Create workflow: A --FLOW--> B --FLOW--> C
- [ ] Click Run
- [ ] Verify nodes execute in order (A, then B, then C)
- [ ] Verify console shows all three

### Test 3: Data Passing (DATA connections)
- [ ] Create workflow: A --DATA--> B
- [ ] Node A returns `{"value": 42}`
- [ ] Node B prints `inputs['A']['value']`
- [ ] Click Run
- [ ] Verify B receives 42

### Test 4: Error Handling
- [ ] Create node that raises exception
- [ ] Click Run
- [ ] Verify error appears in console
- [ ] Verify workflow continues if error is in independent branch

### Test 5: Global State
- [ ] Create two nodes that both modify `global_state['counter']`
- [ ] Click Run
- [ ] Verify changes persist across nodes

---

## Common Issues & Solutions

### Issue 1: "No module named 'pyworks'"
**Problem:** Import fails in subprocess
**Solution:** Make sure pyworks is installed in venv: `pip install -e .`

### Issue 2: "Cycle detected in FLOW graph"
**Problem:** Nodes connected in a loop
**Solution:** Check your connections - you can't have A->B->C->A

### Issue 3: No output in console
**Problem:** Signals not connected
**Solution:** Verify `output_signal.connect(self.console.write)` is called

### Issue 4: GUI freezes during execution
**Problem:** Running in main thread instead of QThread
**Solution:** Make sure you're calling `executor.start()`, not `executor.run()`

### Issue 5: "KeyError" when accessing inputs
**Problem:** Trying to access parent that doesn't exist
**Solution:** Always use `.get()`: `inputs.get('parent_name', {})`

---

## Success Criteria

You've successfully completed Phase 4.2 when:

✅ You can click "Run" and see output in console
✅ Multiple nodes execute in correct order
✅ Data passes between nodes via DATA connections
✅ Errors are caught and displayed (don't crash editor)
✅ GUI stays responsive during execution
✅ Success/failure is reported clearly

---

## What's Next?

**Phase 4.3** will add:
- Node highlighting during execution (see which node is running)
- Pause/Resume/Step controls
- Breakpoint support
- Debug inspector panel

But for now, focus on getting basic execution working! Once you can run workflows and see output, you've built the core of the execution engine.

---

## Quick Reference: Key Files

```
src/core/executor.py          # WorkflowExecutor class (what you're building)
src/core/graph_builder.py     # GraphBuilder (already done in 4.1)
src/core/topological.py       # Topological sort (already done in 4.1)
src/main.py                   # MainWindow with run_workflow() method
```

## Quick Reference: Important Methods

```python
# In executor.py:
WorkflowExecutor.run()                           # Main execution flow
WorkflowExecutor._generate_execution_script()    # Generate Python script
WorkflowExecutor._build_imports()                # Build import statements
WorkflowExecutor._run_subprocess()               # Execute in subprocess

# In main.py:
MainWindow.run_workflow()                        # User clicks Run button
MainWindow._on_execution_finished()              # Execution completes
```

---

Good luck! Take it step by step, test each part as you go, and remember: the executor is just building a Python script and running it in a subprocess. Everything else is just making that process smooth and reliable.
