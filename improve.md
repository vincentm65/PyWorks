# PyWorks Codebase Improvements

This document lists improvements organized by **Severity** (Critical → Low) and **Difficulty** (Easy → Hard) to help prioritize fixes.

---

## 🔴 CRITICAL SEVERITY

### 1. Memory Leak - Connection Animation Timers
**Difficulty:** 🟢 Easy
**Location:** `src/ui/nodes/connection_item.py:14-16`

**Issue:** Each ConnectionBridge creates a QTimer that runs forever. When connections are deleted, timers never stop, causing memory leaks.

```python
# Current code (PROBLEM):
self.timer = QTimer()
self.timer.timeout.connect(self.update_animation)
self.timer.start(30)  # Runs forever!
```

**Impact:** With many connections created/deleted, timers accumulate in memory. Performance degrades over time.

**Fix:** Add cleanup when connection is removed:
```python
def __del__(self):
    if hasattr(self, 'timer'):
        self.timer.stop()
        self.timer.deleteLater()
```

---

### 2. Thread Safety - WorkflowExecutor Lifecycle
**Difficulty:** 🟡 Medium
**Location:** `src/main.py:334-341`

**Issue:** WorkflowExecutor thread starts but never properly stops. The thread continues running even after executor is set to None.

```python
# Current code (PROBLEM):
self.executor = WorkflowExecutor(...)
self.executor.start()
# Later:
self.executor = None  # Thread still running!
```

**Impact:** Background threads can crash or access deleted objects after main window closes.

**Fix:** Implement proper thread termination:
```python
def stop(self):
    if self.executor and self.executor.isRunning():
        self.executor.terminate()
        self.executor.wait()
        self.executor = None
```

---

### 3. PackageInstallThread Never Cleaned Up
**Difficulty:** 🟢 Easy
**Location:** `src/main.py:263-269`

**Issue:** PackageInstallThread starts but never stops or joins, creating zombie threads.

```python
# Current code (PROBLEM):
self.install_thread = PackageInstallThread(pip_path, str(requirements_file))
self.install_thread.start()
# No cleanup!
```

**Impact:** Multiple install operations leave running threads consuming resources.

**Fix:** Wait for thread completion:
```python
def _on_install_finished(self, success):
    if self.install_thread:
        self.install_thread.wait()
        self.install_thread = None
    # ... rest of handler
```

---

## 🟠 HIGH SEVERITY

### 4. Bug - Node Deletion Deletes Wrong File
**Difficulty:** 🟢 Easy
**Location:** `src/ui/node_list.py:173-174`

**Issue:** Variable overwrite causes wrong file path for deletion.

```python
# Current code (PROBLEM):
def handle_delete_item(self, category, name):
    # ...
    file_path = nodes_dir / f"{name}.py"      # Line 173
    file_path = nodes_dir / f"{category}.py"  # Line 174 - OVERWRITES LINE 173!
```

**Impact:** Deleting a function will delete the entire category file instead.

**Fix:** Remove line 173:
```python
def handle_delete_item(self, category, name):
    nodes_dir = self.project_path
    file_path = nodes_dir / f"{category}.py"
    # ... rest of code
```

---

### 5. Unsafe Exception Handling
**Difficulty:** 🟡 Medium
**Locations:**
- `src/main.py:58-59` - Runtime error catch
- `src/ui/editor.py:89-92` - Generic exception on function load
- `src/ui/editor.py:169-170` - Generic exception in paint event

**Issue:** Bare `except Exception` blocks swallow all errors, making debugging impossible.

```python
# Current code (PROBLEM):
try:
    some_operation()
except Exception:
    pass  # Silent failure!
```

**Impact:** Silent failures, no error messages, hard-to-diagnose bugs.

**Fix:** Catch specific exceptions and log:
```python
except (RuntimeError, AttributeError) as e:
    print(f"Signal connection error: {e}")
    # Handle gracefully
```

---

### 6. Windows-Only Path Assumptions
**Difficulty:** 🟡 Medium
**Location:** `src/core/venv_manager.py:24, 31`

**Issue:** Hardcoded Windows paths won't work on Linux/macOS.

```python
# Current code (PROBLEM):
python_path = os.path.join(self.project_path, ".venv", "Scripts", "python.exe")
pip_path = os.path.join(self.project_path, ".venv", "Scripts", "pip.exe")
```

**Impact:** Application fails on Linux/macOS (uses "bin" not "Scripts", no ".exe").

**Fix:** Use platform detection:
```python
import sys
script_dir = "Scripts" if sys.platform == "win32" else "bin"
python_name = "python.exe" if sys.platform == "win32" else "python"
python_path = os.path.join(self.project_path, ".venv", script_dir, python_name)
```

---

### 7. No Connection Cleanup on Scene Clear
**Difficulty:** 🟢 Easy
**Location:** `src/main.py:164-166, 235-237`

**Issue:** Scene cleared but connection timers not stopped first.

```python
# Current code (PROBLEM):
self.canvas.scene.clear()
self.canvas.scene.connections = []
```

**Impact:** Memory leaks from orphaned timers (compounds issue #1).

**Fix:** Stop timers before clearing:
```python
for connection in self.canvas.scene.connections:
    if hasattr(connection, 'timer'):
        connection.timer.stop()
self.canvas.scene.clear()
self.canvas.scene.connections = []
```

---

### 8. Race Condition in Save Operation
**Difficulty:** 🟡 Medium
**Location:** `src/main.py:195-212`

**Issue:** Layout saves before editor save completes. If editor fails, layout still updates.

```python
# Current code (PROBLEM):
if self.editor.save():
    self.reload_script()  # Async operation

layout_path = self.current_project_path / ".layout.json"
self.layout_manager.save_layout(...)  # May happen before reload completes!
```

**Impact:** Inconsistent state between code and layout files.

**Fix:** Wait for reload completion or make save atomic.

---

## 🟡 MEDIUM SEVERITY

### 9. Unused Imports Throughout
**Difficulty:** 🟢 Easy
**Locations:**
- `src/main.py:3` - `import time`
- `src/utils/layout_manager.py:1` - `import sys`
- `src/utils/layout_manager.py:3` - `QApplication, QMainWindow`
- `src/ui/editor.py:3` - `QApplication, QMainWindow`
- `src/ui/node_list.py:1` - `import sys`
- `src/ui/console.py:3` - `QPainter`
- `src/ui/syntax_highlight.py:8` - `import os`

**Impact:** Code clutter, confusion about dependencies.

**Fix:** Remove all unused imports (run `autoflake` or remove manually).

---

### 10. Excessive Debug Print Statements
**Difficulty:** 🟢 Easy
**Location:** Throughout codebase (72+ occurrences)

**Issue:** Debug prints scattered everywhere:
- `src/ui/node_list.py:56` - `print(self.project_path)`
- `src/ui/node_list.py:144` - `print(f'The python file: {file_path}')`
- Console spam during normal operations

**Impact:** Cluttered console, debugging difficulty, unprofessional appearance.

**Fix:** Replace with logging framework:
```python
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Project path: {self.project_path}")
```

---

### 11. Magic Numbers Throughout
**Difficulty:** 🟢 Easy
**Locations:**
- `src/ui/canvas.py:82-83` - Grid size hardcoded as `20`
- `src/ui/nodes/node_item.py:15-16` - Node dimensions hardcoded
- `src/ui/nodes/port.py:18-19` - Port radius hardcoded as `6`
- `src/ui/nodes/connection_item.py:93` - Curve radius hardcoded as `10`

**Impact:** Hard to maintain, unclear meaning.

**Fix:** Extract to named constants at top of files:
```python
GRID_SIZE = 20
NODE_WIDTH = 140
NODE_HEIGHT = 80
PORT_RADIUS = 6
CURVE_RADIUS = 10
```

---

### 12. Duplicate File - syntax_highlight.py
**Difficulty:** 🟢 Easy
**Location:** `src/ui/syntax_highlight.py`

**Issue:** File appears unused. EditorWidget already has syntax highlighting via Pygments. This class is never imported.

**Impact:** Code confusion, maintenance burden.

**Fix:** Delete file if confirmed unused, or integrate if it's intended as replacement.

---

### 13. Inconsistent Error Handling in AST Operations
**Difficulty:** 🟡 Medium
**Location:** `src/core/ast_utils.py`

**Issue:** Some functions return empty strings on error (`extract_function_with_imports`), others return `False` (`replace_function_in_file`, `delete_function_from_file`).

**Impact:** Caller code must handle different error patterns.

**Fix:** Standardize on exceptions or consistent return values:
```python
# Option 1: Use exceptions
def extract_function(file_path, function_name):
    if not found:
        raise ValueError(f"Function '{function_name}' not found")
    return code

# Option 2: Use Optional type
def extract_function(file_path, function_name) -> Optional[str]:
    if not found:
        return None
    return code
```

---

### 14. No Validation on User Input
**Difficulty:** 🟡 Medium
**Locations:**
- `src/main.py:140-142` - Project name not validated
- `src/ui/node_list.py:114` - Category name not validated
- `src/ui/node_list.py:135` - Function name not validated

**Issue:** User can enter invalid Python identifiers, paths with special characters.

```python
# Current code (PROBLEM):
name, ok = QInputDialog.getText(self, "New Project", "Enter project name:")
if not ok or not name:
    return
# No validation!
```

**Impact:** Creates invalid file paths, invalid Python identifiers, runtime errors.

**Fix:** Add validation:
```python
if not name.isidentifier():
    QMessageBox.warning(self, "Invalid Name", "Must be valid Python identifier")
    return
if name in keyword.kwlist:
    QMessageBox.warning(self, "Invalid Name", "Cannot use Python keyword")
    return
```

---

### 15. Hardcoded Project Structure Assumption
**Difficulty:** 🔴 Hard
**Location:** `src/core/node_registry.py:23`

**Issue:** Assumes "nodes" directory exists. No fallback or error handling.

```python
# Current code (PROBLEM):
for file in (project_path / "nodes").glob("*.py"):
    # Silently fails if directory doesn't exist
```

**Impact:** Fails silently if directory missing or renamed.

**Fix:** Check directory existence:
```python
nodes_dir = project_path / "nodes"
if not nodes_dir.exists():
    print(f"Warning: nodes directory not found at {nodes_dir}")
    return []

for file in nodes_dir.glob("*.py"):
    # ...
```

---

### 16. Node Position Encoding in Key
**Difficulty:** 🔴 Hard
**Location:** `src/utils/layout_manager.py:27`, `src/ui/nodes/node_item.py:26`

**Issue:** Node uniqueness depends on position in key format `fqnn_x_y`. Moving a node creates a "new" node.

```python
# Current code (PROBLEM):
node_key = f"{item.fqnn}_{int(node_x)}_{int(node_y)}"
```

**Impact:** Moving nodes breaks connections in saved layouts (connections reference old keys).

**Fix:** Use UUID for node instances or maintain stable node IDs separate from position:
```python
import uuid

# In NodeItem.__init__():
self.node_id = str(uuid.uuid4())

# In layout save:
node_key = item.node_id  # Stable across moves
```

---

## 🔵 LOW SEVERITY

### 17. Typo in Method Name
**Difficulty:** 🟢 Easy
**Location:** `src/ui/nodes/connection_item.py:71, 121`

**Issue:** Method name misspelled.

```python
def create_orthoganal_path(self):  # Should be "orthogonal"
```

**Fix:** Rename to `create_orthogonal_path()` throughout file.

---

### 18. Unused Variables
**Difficulty:** 🟢 Easy
**Locations:**
- `src/utils/layout_manager.py:97` - `source_port = None` (never used)
- `src/core/package_installer.py:41` - `installed_count = 0` (never incremented)
- `src/ui/nodes/port.py:46` - `radius = 5` (declared but unused)

**Fix:** Remove unused variable declarations.

---

### 19. Inefficient Port Lookup
**Difficulty:** 🟡 Medium
**Location:** `src/utils/layout_manager.py:114-123`

**Issue:** Linear search through ports for each connection.

```python
# Current code (INEFFICIENT):
for port in source_node.ports:
    if port.port_type == ... and port.port_direction == ...:
        source_port = port
        break
```

**Fix:** Create port lookup dictionary in NodeItem:
```python
# In NodeItem.__init__():
self.port_map = {
    ('DATA', 'IN'): self.input_data,
    ('DATA', 'OUT'): self.output_data,
    ('FLOW', 'IN'): self.input_flow,
    ('FLOW', 'OUT'): self.output_flow,
}

# In layout_manager.py:
source_port = source_node.port_map.get((port_type, port_direction))
```

---

### 20. Placeholder Menu Actions
**Difficulty:** 🟡 Medium
**Location:** `src/main.py:350-360`

**Issue:** Menu items do nothing but print.

```python
def undo(self):
    print("Undo")

def redo(self):
    print("Redo")
```

**Impact:** User expects functionality but gets no-op.

**Fix:** Either implement or disable menu items:
```python
# Option 1: Disable until ready
undo_action.setEnabled(False)

# Option 2: Show not implemented message
def undo(self):
    QMessageBox.information(self, "Not Implemented", "Undo feature coming soon!")
```

---

### 21. No Docstrings
**Difficulty:** 🟢 Easy
**Location:** Most classes and methods

**Impact:** Reduced maintainability, unclear API contracts.

**Fix:** Add docstrings to all public classes and methods:
```python
class NodeItem(QGraphicsItem):
    """Visual representation of a node in the canvas.

    Each node has 4 ports for connections and can be dragged/selected.
    Positions snap to a grid for aligned layouts.
    """

    def __init__(self, fqnn: str, title: str):
        """Initialize a node item.

        Args:
            fqnn: Fully qualified node name
            title: Display name shown in the node
        """
```

---

### 22. No Type Hints
**Difficulty:** 🟡 Medium
**Location:** Most functions

**Fix:** Add type hints for IDE support and type checking:
```python
from typing import Optional, List, Dict
from PyQt6.QtWidgets import QGraphicsScene

def save_layout(self, scene: QGraphicsScene, file_path: str) -> bool:
    """Save the current layout to JSON file.

    Args:
        scene: The graphics scene to save
        file_path: Path to save the layout file

    Returns:
        True if save succeeded, False otherwise
    """
```

---

### 23. Hardcoded Style Strings
**Difficulty:** 🟡 Medium
**Locations:**
- `src/ui/dialogs/welcome_dialog.py:69-85, 92-108`
- `src/ui/status_bar.py:32`
- `src/ui/console.py:10`

**Issue:** Inline stylesheets scattered throughout code.

**Fix:** Extract to QSS files or stylesheet constants:
```python
# styles.py
BUTTON_STYLE = """
    QPushButton {
        background-color: #4285F4;
        color: white;
        border-radius: 4px;
        padding: 8px 16px;
    }
"""

# In your widget:
from .styles import BUTTON_STYLE
button.setStyleSheet(BUTTON_STYLE)
```

---

### 24. Inconsistent String Quotes
**Difficulty:** 🟢 Easy
**Location:** Throughout codebase

**Issue:** Mix of single and double quotes without clear convention.

**Fix:** Run Black formatter to standardize:
```bash
pip install black
black src/
```

---

### 25. Missing __init__.py Files
**Difficulty:** 🟢 Easy
**Location:** Package directories

**Fix:** Ensure all package directories have `__init__.py`:
```bash
touch src/ui/nodes/__init__.py
touch src/ui/dialogs/__init__.py
touch src/core/__init__.py
touch src/utils/__init__.py
```

---

### 26. No .gitignore for Python Files
**Difficulty:** 🟢 Easy
**Location:** Root directory

**Fix:** Add `.gitignore`:
```
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Virtual environment
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project
*.layout.json
```

---

### 27. Trailing Blank Lines
**Difficulty:** 🟢 Easy
**Locations:**
- `src/ui/nodes/port.py:67-68`
- `src/core/package_installer.py:53-54`

**Fix:** Remove trailing whitespace (Black formatter handles this).

---

### 28. Inconsistent Naming - FQNN vs fqnn
**Difficulty:** 🟢 Easy
**Location:** Throughout codebase

**Issue:** Sometimes "FQNN" (uppercase), sometimes "fqnn" (lowercase).

**Fix:** Standardize:
- Variables/attributes: `fqnn` (lowercase)
- Documentation/comments: FQNN (uppercase)
- Type hints: `FQNN` as type alias

```python
from typing import NewType
FQNN = NewType('FQNN', str)

def get_node_by_fqnn(self, fqnn: FQNN) -> Optional[NodeItem]:
    """Get node by its FQNN."""
```

---

## 🏗️ ARCHITECTURAL CONCERNS

### A1. N Connections × 30ms Timer = Performance Drain
**Difficulty:** 🟡 Medium
**Severity:** High

**Issue:** Each connection has its own 30ms timer. With 100 connections = 100 timers firing 33x/sec = 3,300 events/sec.

**Fix:** Use single scene-level animation timer:
```python
# In CanvasGraphicsScene:
def __init__(self):
    super().__init__()
    self.animation_timer = QTimer()
    self.animation_timer.timeout.connect(self.update_all_connections)
    self.animation_timer.start(30)

def update_all_connections(self):
    for connection in self.connections:
        connection.update_animation()
```

---

### A2. Global Scene State
**Difficulty:** 🔴 Hard
**Severity:** Medium

**Issue:** `connections` list stored as scene attribute rather than Qt parent-child relationships.

**Fix:** Use QGraphicsScene's built-in item management or implement proper observer pattern.

---

### A3. Circular Import Potential
**Difficulty:** 🟡 Medium
**Severity:** Medium

**Issue:** Several files have circular import patterns:
- `layout_manager.py` imports `node_item.py` and `connection_item.py`
- `connection_item.py` imports `node_item.py`

**Fix:** Use TYPE_CHECKING for type hints:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .node_item import NodeItem

def process_node(node: 'NodeItem'):  # String annotation
    pass
```

---

### A4. MainWindow God Class
**Difficulty:** 🔴 Hard
**Severity:** Medium

**Issue:** MainWindow has too many responsibilities:
- Project management
- File operations
- Workflow execution
- Thread management
- UI updates

**Fix:** Split into separate controllers:
- `ProjectController` - Project operations
- `WorkflowController` - Execution management
- `CanvasController` - Canvas operations

---

### A5. No Undo/Redo Architecture
**Difficulty:** 🔴 Hard
**Severity:** Low

**Issue:** Menu items exist but no command pattern or undo stack implemented.

**Fix:** Implement Qt's QUndoStack:
```python
from PyQt6.QtGui import QUndoStack, QUndoCommand

class AddNodeCommand(QUndoCommand):
    def __init__(self, scene, node):
        super().__init__("Add Node")
        self.scene = scene
        self.node = node

    def redo(self):
        self.scene.addItem(self.node)

    def undo(self):
        self.scene.removeItem(self.node)

# In MainWindow:
self.undo_stack = QUndoStack(self)
```

---

## 📊 RECOMMENDED ACTION PLAN

### Phase 1: Critical Fixes (Do First!)
**Estimated Time:** 2-4 hours

1. ✅ Add timer cleanup to ConnectionBridge (#1)
2. ✅ Implement thread termination in stop/pause (#2)
3. ✅ Clean up PackageInstallThread lifecycle (#3)
4. ✅ Fix node deletion bug (#4)

### Phase 2: High Priority
**Estimated Time:** 4-6 hours

5. ✅ Add platform detection for venv paths (#6)
6. ✅ Improve exception handling (#5)
7. ✅ Add connection cleanup on scene clear (#7)
8. ✅ Fix save race condition (#8)

### Phase 3: Code Quality
**Estimated Time:** 3-5 hours

9. ✅ Remove unused imports (#9)
10. ✅ Replace print() with logging (#10)
11. ✅ Extract magic numbers to constants (#11)
12. ✅ Add input validation (#14)
13. ✅ Remove syntax_highlight.py if unused (#12)

### Phase 4: Architecture
**Estimated Time:** 8-12 hours

14. ✅ Implement single animation timer (A1)
15. ✅ Add stable node IDs (not position-based) (#16)
16. ✅ Refactor MainWindow responsibilities (A4)
17. ✅ Add type hints throughout (#22)

### Phase 5: Polish
**Estimated Time:** 2-4 hours

18. ✅ Add comprehensive docstrings (#21)
19. ✅ Run Black formatter (#24)
20. ✅ Add .gitignore (#26)
21. ✅ Fix typos and naming (#17, #28)

---

## 🎯 QUICK WINS (Easy + High Impact)

These give maximum benefit for minimal effort:

1. **Fix node deletion bug** (#4) - 5 minutes, prevents data loss
2. **Add timer cleanup** (#1) - 10 minutes, prevents memory leaks
3. **Stop timers on scene clear** (#7) - 5 minutes, prevents memory leaks
4. **Remove unused imports** (#9) - 10 minutes, cleaner code
5. **Extract magic numbers** (#11) - 20 minutes, easier maintenance
6. **Add input validation** (#14) - 30 minutes, prevents crashes

**Total Quick Win Time:** ~1.5 hours for major improvements!

---

## 📝 NOTES

- Run `pylint src/` to catch additional issues
- Consider adding pre-commit hooks for formatting/linting
- Test each fix on both Windows and Linux if possible
- Keep CLAUDE.md updated with architecture changes
