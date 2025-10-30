# Python Visual Scripting Editor - Technical Plan

## 1. Project Vision

Create a desktop application that allows users to build and run complex workflows by writing standard Python functions. Each function is represented as a node in a visual, graph-based editor. This approach bridges the gap between visual programming and traditional scripting, enabling users to focus solely on Python code without needing to learn a separate configuration language.

---

## 2. Core Features

### Visual Node Editor
A canvas where Python functions from a user's script are represented as draggable nodes.

### Code Editor
An integrated text editor for writing and modifying the Python source code for the workflow.

### Manual Synchronization
A **"Reload Script"** button that parses the Python file and updates the node canvas, making the sync process explicit and predictable.

### Node Connectivity
Users can visually connect nodes to define the flow of execution and data.

### Isolated Dependency Management
Each workflow project will have its own dedicated Python virtual environment (venv).

### Explicit Data Flow

**Global State (`global_state`):**
- A dictionary shared across all nodes in a workflow
- Allows for persistent state throughout execution
- Initialized once at workflow start

**Node Inputs (`inputs`):**
- A dictionary passed to each node
- Contains the return values of all parent nodes
- Namespaced by the parent function's name
- Example: `inputs['get_data']['raw_data']`

---

## 3. Architecture

The application is divided into three main components: **Frontend UI**, **Workflow Execution Backend**, and **Project Management**.

### 3.1. Frontend (UI)

#### Main Window
- `QMainWindow` serves as the main application container

#### Toolbar
- **"Reload Script"** button - Triggers canvas synchronization
- **"Run"** button - Executes the workflow

#### Dock Widgets

**Canvas:**
- `QGraphicsView` containing a `QGraphicsScene`
- **Nodes:** Custom `QGraphicsItem` subclasses representing Python functions
- **Connections:** Custom `QGraphicsItem` paths connecting nodes
- **Visual Feedback:** Nodes display states (pending, running, completed, error)

**Code Editor:**
- `QScintilla` (preferred) or `QPlainTextEdit` with custom `QSyntaxHighlighter`
- Syntax highlighting for Python
- Line numbers and basic editing features

**Project Explorer:**
- `QTreeView` to manage workflow projects
- Shows project structure (workflow.py, requirements.txt, etc.)

**Data Inspector:**
- View execution results from each node
- Inspect data structures produced by nodes
- Shows execution time and status

**Output Console:**
- Display logs, execution status, and error messages
- Real-time output during workflow execution

#### UI-Backend Communication
Uses Qt signals/slots and `QThread` workers to asynchronously communicate with the backend for:
- Reloading scripts
- Running workflows
- Installing packages

---

### 3.2. Backend (Workflow Execution)

#### Node Discovery

Uses a decorator-based discovery mechanism:

```python
from pyworks import node

@node
def get_data(inputs, global_state):
    """This node gets initial data."""
    # 'inputs' is empty for a root node
    return {"raw_data": [1, 2, 3]}

@node
def process_data(inputs, global_state):
    """
    This node processes data from 'get_data'.
    'inputs' will be: {'get_data': {'raw_data': [1, 2, 3]}}
    """
    data = inputs.get("get_data", {}).get("raw_data", [])
    result = [x * 2 for x in data]
    return {"processed_data": result}
```

#### Workflow Runner

A core module responsible for executing a workflow:

**Node Loading:**
- Uses `importlib` and `inspect` in the project's venv subprocess
- Imports the user's `workflow.py` module
- Identifies functions decorated with `@node` (checks for `_is_workflow_node` attribute)

**Execution Graph:**
- Builds a directed acyclic graph (DAG) from connections in `.layout.json`
- Performs topological sort to determine execution order

**Cycle Handling:**
- Cycles are **forbidden** (DAG only)
- If topological sort fails, a "Cycle detected" error is reported
- Execution is aborted
- *Rationale: Massively simplifies the execution engine*

**Execution Strategy:**
- Execute nodes according to the sorted graph order
- Single-threaded execution within the subprocess (parallel execution is a future enhancement)

**Error Handling:**
- Continue executing independent branches when a node fails
- Only halt execution for nodes that depend on failed predecessors
- Failed nodes are marked with error state
- Dependent nodes are marked as "blocked"

**Result Tracking:**
- Store each node's output dictionary
- Track execution time per node
- Record status (pending, running, completed, error, blocked)

**Context Management:**
- `global_state`: Initialized once at workflow start, passed to all nodes
- `inputs`: For each node, a new `inputs` dictionary is constructed containing the full return value of every parent node, keyed by that parent's function name

**Process Isolation:**
- All user code (discovery and execution) runs in a separate process
- Uses the Python interpreter from the workflow's specific venv
- Managed via the `subprocess` module
- Communication via stdout/stderr pipes

---

### 3.3. Project & Environment Management

#### Project Structure

Each workflow is a directory containing:

```
my_workflow/
├── workflow.py          # User's node functions
├── requirements.txt     # Dependencies
├── .layout.json         # Visual layout (version controlled)
├── .venv/               # Virtual environment
└── .pyworks/            # App metadata, logs, etc.
    ├── config.json      # Project settings
    └── execution.log    # Last run logs
```

#### .layout.json Structure

```json
{
  "version": "1.0",
  "nodes": {
    "get_data": {"x": 100, "y": 200},
    "process_data": {"x": 350, "y": 200}
  },
  "connections": [
    {"from": "get_data", "to": "process_data"}
  ]
}
```

**Note:** Simplified structure without ports. Connections are simple node-to-node links.

#### Venv Manager

A utility module responsible for:
- Creating new virtual environments (`python -m venv .venv`)
- Running `pip install -r requirements.txt` using subprocess
- Validating venv exists before execution

---

### 3.4. Manual Synchronization System

The synchronization between code and canvas is **explicit and user-driven**.

#### Source of Truth
- **Python code (`workflow.py`):** Primary source of truth for what nodes exist
- **`.layout.json`:** Source of truth for node positions and connections

#### Code-to-Canvas Sync (Manual)

**Trigger:** User clicks the "Reload Script" button

**Process:**
1. Save the current content of the code editor to `workflow.py`
2. Launch a `QThread` worker to run the Node Discovery process (using `importlib` in the venv subprocess)
3. The worker returns a list of all `@node`-decorated function names
4. The main UI thread receives this list and performs a diff against the current canvas:
   - **Added functions:** Create new nodes on the canvas (at default positions or from `.layout.json` if they existed previously)
   - **Removed functions:** Remove corresponding nodes and their connections from the canvas
   - **Unchanged functions:** Ensure the node is present and retains its position
5. Update canvas display

**Benefits:**
- Simple, fast, and predictable
- Avoids complexity of AST parsing and signature matching
- User controls when sync happens

#### Canvas-to-Data Sync

**Trigger:** Node drag, connection creation/deletion

**Process:**
1. Update the in-memory graph structure
2. Mark layout as modified (dirty flag)
3. On manual save (Ctrl+S) or auto-save interval, write the node positions and connection list to `.layout.json`

**Validation:**
- Warn if connections create cycles (when user attempts to create them)
- Visual feedback during connection dragging (valid/invalid)

---

### 3.5. Asynchronous Operations Strategy

All blocking operations run in `QThread` workers to keep the UI responsive.

#### WorkflowExecutionThread
- Manages the subprocess for running the workflow
- **Signals:**
  - `node_update(node_name: str, status: str)` - For real-time node status updates
  - `finished(results: dict)` - Final results and execution summary
  - `error(error_msg: str)` - Critical errors
  - `log(message: str)` - Log messages for output console

#### PackageInstallThread
- Manages the `pip install` subprocess
- **Signals:**
  - `log_output(line: str)` - Real-time log output
  - `finished(success: bool)` - Installation complete
  - `progress(percentage: int)` - Installation progress (if parseable)

#### ScriptReloadThread
- Manages the `importlib` discovery subprocess
- **Signals:**
  - `finished(node_names: list)` - List of discovered node function names
  - `error(error_msg: str)` - Import or syntax errors

**Thread Safety:**
- All UI updates happen on the main thread via signals
- Workers only communicate via signals, never directly manipulate UI
- Subprocess stdout/stderr parsed in worker thread

---

### 3.6. Data Type System (Future Enhancement)

To enable port validation and visual clarity, a future enhancement could use decorator metadata:

```python
@node(outputs=["filtered: np.ndarray", "stats: dict"])
def filter_image(inputs, global_state):
    image = inputs['parent_node']['image_data']
    # ... processing
    return {"filtered": result, "stats": {"mean": 0.5}}
```

**Benefits:**
- Visual port coloring by type
- Connection validation (type compatibility)
- Auto-generated port labels
- Runtime type checking (optional)

**Implementation:**
- Phase 1-3: No type system, all connections allowed
- Phase 4+: Add optional type hints and visual enhancements
- The core execution logic remains the same (dict-based return values)

---

## 4. Technology Stack

- **Language:** Python 3.10+
- **UI Framework:** PySide6 (officially supported Qt bindings)
- **Canvas:** `QGraphicsView` / `QGraphicsScene`
- **Code Editor:** `QScintilla` (preferred) or `QPlainTextEdit` with syntax highlighting
- **Subprocess Management:** `subprocess.Popen()`
- **Threading:** `QThread` from PySide6

---

## 5. Development Phases

### Phase 1: Core UI and Canvas

**Goal:** Build the basic application shell and visual components.

**Tasks:**
1. Set up a `QMainWindow` with dockable `QPlainTextEdit` and `QGraphicsView`
2. Create a custom `QGraphicsItem` for a draggable node with:
   - Function name label
   - Visual state indicator (color/border)
   - Connection points (anchors)
3. Implement manual connection drawing between nodes:
   - Click and drag from one node to another
   - Visual feedback during dragging
   - Store connections in memory
4. Add basic toolbar with placeholder buttons
5. Implement save/load of `.layout.json` for node positions

**Deliverable:** A visual editor where you can manually create nodes and connect them.

---

### Phase 1.5: Project Foundation

**Goal:** Establish project-based workspace management to enable workflow execution.

**Rationale:** Phase 2 requires knowing "what code to run" and "where dependencies are." This phase implements the minimum viable project system to provide that context.

**Tasks:**

1. **Project Structure Module** (`src/utils/project_manager.py`):
   - `create_project(name, location)`: Creates project folder with:
     - `workflow.py` (template with two example `@node` functions showing data passing)
     - `requirements.txt` (empty)
     - `.layout.json` (empty structure)
   - `validate_project(path)`: Validates project folder structure

2. **MainWindow Project State Tracking**:
   - Add `current_project_path` attribute to track open project
   - `set_current_project(path)`: Opens project, loads files, updates UI
   - `close_current_project()`: Closes project, clears workspace
   - Update window title to show project name

3. **File Menu Restructure**:
   - **New Project** (Ctrl+N): Dialog for name + location, creates project
   - **Open Project** (Ctrl+O): Folder picker, validates and opens project
   - **Close Project**: Closes current project
   - **Save** (Ctrl+S): Saves `.layout.json` and `workflow.py` to project folder
   - Remove: Standalone layout file operations

4. **Editor Integration**:
   - Load `workflow.py` into editor when project opens
   - Save editor content to `workflow.py` on Ctrl+S
   - Disable editor when no project open

5. **Layout Manager Updates**:
   - Modify `save_layout()` to save to project's `.layout.json`
   - Modify `load_layout()` to load from project's `.layout.json`

6. **First Launch Experience**:
   - Show "New Project" dialog automatically on startup if no project open
   - Welcome message and easy project creation

7. **Toolbar State Management**:
   - Disable Run/Pause/Stop buttons when no project open
   - Add tooltips explaining why disabled

8. **Cleanup**:
   - Remove deprecated `workspace/layouts/` code

**Deliverable:** A project-based workspace system where users create self-contained project folders with `workflow.py`, `.layout.json`, and `requirements.txt`. Ready for Phase 2 execution.

---

### Phase 2: Basic Workflow Execution

**Goal:** Create a proof-of-concept for running a hardcoded workflow.

**Tasks:**
1. Write a simple hardcoded `workflow.py` with 2-3 functions
2. Implement the `@node` decorator (sets `_is_workflow_node = True` attribute)
3. Develop the `(inputs, global_state)` data-passing mechanism:
   - Initialize `global_state` as empty dict
   - Build `inputs` dict from parent node return values
4. Implement a basic graph executor:
   - Load connections from `.layout.json`
   - Build adjacency list
   - Perform topological sort (use standard algorithm)
   - Execute nodes in sorted order
   - Pass `inputs` and `global_state` to each function
   - Collect return values
5. Handle cycle detection (topological sort failure)
6. Print execution results to console

**Deliverable:** A command-line script that can execute a workflow graph.

---

### Phase 3: Dynamic Node Loading

**Goal:** Automatically populate the canvas based on a Python script.

**Tasks:**
1. Implement the `ScriptReloadThread`:
   - Run in subprocess using venv Python
   - Use `importlib.import_module()` to load `workflow.py`
   - Use `inspect.getmembers()` to find all functions
   - Filter to only those with `_is_workflow_node` attribute
   - Return list of function names
2. Implement the "Reload Script" button:
   - Save editor content to `workflow.py`
   - Launch `ScriptReloadThread`
   - On completion, diff with current canvas
   - Add/remove nodes as needed
3. Handle errors gracefully (syntax errors, import errors)
4. Implement node positioning:
   - Check `.layout.json` for existing positions
   - Use default staggered layout for new nodes
5. Save connections to `.layout.json` on file save

**Deliverable:** A fully integrated editor where code changes automatically sync to the canvas.

---

### Phase 4: Venv and Dependency Management

**Goal:** Isolate workflow execution environments.

**Tasks:**
1. Implement venv creation:
   - Detect if `.venv/` exists
   - Offer to create if missing
   - Use `subprocess` to run `python -m venv .venv`
2. Implement `PackageInstallThread`:
   - Run `pip install -r requirements.txt` in venv
   - Stream output to UI console
   - Handle errors (missing packages, network issues)
3. Modify `ScriptReloadThread` to use venv Python interpreter
4. Modify `WorkflowExecutionThread` to use venv Python interpreter
5. Build a simple requirements.txt editor:
   - Text area in a dialog or dock widget
   - "Install Dependencies" button
   - Progress indicator during installation

**Deliverable:** Each workflow runs in its own isolated environment.

---

### Phase 5: Integration and Polish

**Goal:** Connect all systems and refine the user experience.

**Tasks:**
1. Implement the "Run" button:
   - Validate workflow (no cycles, all nodes connected)
   - Launch `WorkflowExecutionThread`
   - Update node visual states in real-time
2. Implement real-time node status highlighting:
   - Pending: Default color (gray)
   - Running: Blue pulse/animation
   - Completed: Green
   - Error: Red
   - Blocked: Yellow/orange
3. Build the Data Inspector:
   - Tree view of execution results
   - Shows each node's return value
   - Displays execution time
   - Shows error messages/tracebacks
4. Add robust error handling and logging:
   - Catch all exceptions in threads
   - Log to `.pyworks/execution.log`
   - Display user-friendly error messages
5. Add keyboard shortcuts (F5 for run, Ctrl+S for save, Ctrl+R for reload)
6. Implement undo/redo for canvas operations (optional)

**Deliverable:** A fully functional visual scripting editor.

---

## 6. Architectural Decisions & Resolutions

### 6.1. State Management ✓

**Decision:** Use `.layout.json` for visual state storage.

**Rationale:**
- Clean separation of code (logic) vs. presentation (layout)
- Version controllable
- Easy to parse and modify programmatically

---

### 6.2. Bidirectional Synchronization ✓

**Decision:** Manual, user-driven sync.

**Strategy:**
- **Code → Canvas:** User clicks "Reload Script". App re-imports the `workflow.py` module in a subprocess and diffs the node list with the canvas.
- **Canvas → Layout:** Connection/position changes are saved to `.layout.json`.
- **Conflict Resolution:** Simple add/remove. If a user renames a function, it's treated as a "delete" and an "add."

**Rationale:**
- Simplicity and predictability
- No need for complex AST diffing or signature matching
- User controls when sync happens, avoiding surprises
- Fast and reliable

---

### 6.3. Asynchronous Operations ✓

**Decision:** Use Qt's `QThread` for all blocking operations (install, run, reload).

**Implementation:**
- Worker threads manage `subprocess.Popen()` calls
- Communicate with UI via signals
- UI remains responsive during long operations

---

### 6.4. Node Discovery Mechanism ✓

**Decision:** Decorator-based using `@node`.

**Rationale:**
- Explicit and Pythonic
- Familiar pattern for Python developers
- Allows future metadata (inputs, outputs, types)

**Implementation:**
- Detected at runtime using `importlib` and `inspect` on the user's module
- Not by parsing the AST (simpler and more reliable)

---

### 6.5. Execution Graph Cycles ✓

**Decision:** Not supported (DAG Only).

**Rationale:**
- Massively simplifies the execution engine
- Most workflows are naturally acyclic
- Iterative workflows are a future enhancement

**Implementation:**
- Standard topological sort is used
- If the sort fails, a "Cycle detected" error is shown
- Execution is stopped

---

### 6.6. Error Handling Strategy ✓

**Decision:** Continue executing independent branches on errors.

**Behavior:**
- Failed nodes stop their downstream dependencies
- Parallel branches continue execution
- UI will visually flag failed and blocked nodes
- Detailed error logs in Data Inspector and Output Console

---

### 6.7. Security Considerations

**Decision:** Market as a development tool for trusted users and trusted code.

**Safety Features:**

1. **Environment Isolation:**
   - Each project's venv prevents dependency conflicts
   - No access to the main app environment

2. **Process Isolation:**
   - All user code runs in a separate subprocess
   - App cannot be compromised by user code

3. **Code Review Warnings (Future):**
   - Flag potentially dangerous imports (`os.system`, `eval`, etc.)
   - Show diff before running modified workflows

**Out of Scope:**
- Full sandboxing (too complex for initial versions)
- Network isolation
- Filesystem access restrictions

---

## 7. Implementation Priorities

### Must Have (Phase 1-3)
- [x] Decorator-based node discovery (via `importlib`/`inspect`)
- [x] Manual "Reload Script" code-to-canvas sync
- [x] Execution graph (DAG only) with topological sort
- [x] `QThread`-based async execution in a subprocess
- [x] `.layout.json` storage and loading
- [x] Explicit `(inputs, global_state)` data passing

### Should Have (Phase 4-5)
- [ ] Venv management UI (create venv, run pip install)
- [ ] Data inspector for execution results
- [ ] Node-level visual error reporting
- [ ] Output console with real-time logs
- [ ] Keyboard shortcuts

### Nice to Have (Post-Launch)
- [ ] Cycle/loop support for iterative workflows
- [ ] Port-based type system with visual validation
- [ ] Parallel execution of independent branches
- [ ] Advanced debugging (breakpoints, step-through)
- [ ] Workflow templates and examples
- [ ] Export/import workflows as bundles

---

## 8. Open Questions & Considerations

### Question 1: Node Placement Strategy
When new nodes are added during "Reload Script", where should they be placed?

**Options:**
- **Staggered grid:** Place new nodes in a grid with configurable spacing
- **Centered:** Place all new nodes at canvas center (user drags to position)
- **Smart layout:** Use a graph layout algorithm (e.g., hierarchical layout)

**Recommendation:** Start with staggered grid, add smart layout in Phase 5.

---

### Question 2: Connection Validation
Should the UI prevent invalid connections in real-time?

**Considerations:**
- Prevent cycles (use a temporary graph check during drag)
- Prevent self-connections (node connecting to itself)
- Future: Prevent type mismatches (when type system is added)

**Recommendation:** Implement basic validation (cycles, self-connections) in Phase 3.

---

### Question 3: Multiple Outputs Handling
How should nodes with multiple output keys be connected?

**Current approach:** All return values are passed to child nodes via `inputs['parent_name']`.

**Future enhancement:** Port-based connections where user can specify which output goes to which input.

**Recommendation:** Keep simple dict-based approach initially. Add ports in type system enhancement.

---

### Question 4: Execution Feedback
How much detail should be shown during execution?

**Options:**
- **Minimal:** Just show running/completed/error states
- **Moderate:** Show execution time, return value summary
- **Detailed:** Show full return values, intermediate state, variable inspection

**Recommendation:** Start with moderate (Phase 5), add detailed inspection as optional feature.

---

### Question 5: Auto-save vs Manual Save
Should `.layout.json` be auto-saved or require manual save?

**Considerations:**
- **Auto-save:** Convenient, no lost work
- **Manual save:** More control, avoids cluttering git history

**Recommendation:** Auto-save on interval (30s) + manual save (Ctrl+S). Add dirty indicator in title bar.

---

## 9. Success Criteria

The project will be considered successful when:

1. **Users can create workflows without writing JSON/YAML**
   - Only Python code is needed
   - Visual editor is intuitive and responsive

2. **Workflows execute reliably**
   - Correct execution order (topological sort)
   - Proper data passing between nodes
   - Clear error messages when failures occur

3. **Environment isolation works**
   - Each workflow has its own venv
   - Dependencies don't conflict
   - Easy to install packages

4. **Sync is predictable**
   - "Reload Script" button always works
   - Users understand what will happen
   - No surprising behavior

5. **Development is maintainable**
   - Clean architecture with separation of concerns
   - Well-documented code
   - Testable components

---

## 10. Future Enhancements

Ideas for post-launch development:

- **Subgraphs/Modules:** Allow nodes to be collapsed into reusable subgraphs
- **Conditional Execution:** Support if/else logic in the graph
- **Loop Nodes:** Special nodes that execute children multiple times
- **Remote Execution:** Run workflows on remote machines or clusters
- **Collaboration:** Multi-user editing with conflict resolution
- **Version History:** Built-in git integration for workflow versioning
- **Marketplace:** Share and discover workflow templates
- **Plugin System:** Allow third-party node types and integrations
