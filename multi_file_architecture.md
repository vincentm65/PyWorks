# Multi-File Node System Architecture

## Overview

This document describes the architecture for PyWorks' multi-file node system, which allows organizing @node functions into category-based files instead of a single monolithic workflow.py.

## Current Problem

**Current Approach (Disliked):**
```
my_project/
└── workflow.py  # One massive file with 50+ @node functions
```

- Single file becomes unwieldy with many nodes
- Hard to organize related functionality
- Difficult to navigate and maintain

## Proposed Solution

**New Approach:**
```
my_project/
└── nodes/
    ├── desktop.py      # 7 desktop-related @node functions
    ├── web.py          # 5 web-related @node functions
    └── filesystem.py   # 8 file operation @node functions
```

**Benefits:**
- Logical organization by domain/category
- Each file is a manageable size
- Easy to find and edit related functions
- Can edit full category files in external editor
- Can view individual functions in internal editor

---

## Design Decisions

### 1. Import Handling
**Decision:** Show imports at top, then function below

When viewing a single function internally:
```python
# Imports from top of file
import os
import pyautogui

# Function definition
@node
def click_mouse(inputs, global_state):
    """Click at specified coordinates."""
    x = inputs.get("x", 0)
    y = inputs.get("y", 0)
    pyautogui.click(x, y)
    return {"success": True}
```

This provides necessary context without showing the entire file.

### 2. Helper Functions
**Decision:** Allow them - only @node functions appear in Node List

Category files can contain:
- **@node decorated functions** → Appear in Node List, draggable to canvas
- **Regular functions** → Don't appear in Node List, but can be called by @node functions

Example:
```python
# desktop.py

def _get_screen_size():  # Helper - NOT in Node List
    """Helper function."""
    return (1920, 1080)

@node
def center_window(inputs, global_state):  # Shows in Node List
    """Center a window."""
    screen = _get_screen_size()  # Can use helper
    # ...
```

### 3. Migration Strategy
**Decision:** Deprecate workflow.py completely

- New projects create nodes/ structure only
- No workflow.py file created
- Clean break from old architecture
- Existing projects with workflow.py will need manual migration

### 4. Implementation Approach
**Decision:** Minimal MVP first (Phase 1-2 only)

Build core multi-file discovery and tree view first. Add advanced editing features later.

---

## Architecture Components

### Node Identification System

**Fully Qualified Node Name (FQNN):**
```
category.function_name
```

**Examples:**
- `desktop.click_mouse`
- `web.scrape_page`
- `filesystem.read_file`

**Benefits:**
- Unique identification even with duplicate function names across categories
- Easy to trace which file a node comes from
- Supports future namespacing if needed

### Project Structure

```
my_project/
├── nodes/                    # Node category files
│   ├── desktop.py           # Desktop automation nodes
│   ├── web.py               # Web scraping nodes
│   ├── filesystem.py        # File system nodes
│   └── utils.py             # Optional: shared utilities (no @node functions)
├── requirements.txt
├── .layout.json
└── .venv/
```

**Notes:**
- `nodes/` directory contains all category files
- Each .py file is a category
- Category name = filename without .py extension
- Helper/utility functions can exist in any category file

### Layout Format v2.0

**New .layout.json format:**
```json
{
  "version": "2.0",
  "nodes": {
    "desktop.click_mouse_100_200": {
      "category": "desktop",
      "function": "click_mouse",
      "x": 100,
      "y": 200
    },
    "web.scrape_page_300_200": {
      "category": "web",
      "function": "scrape_page",
      "x": 300,
      "y": 200
    }
  },
  "connections": [
    {
      "from_node": "desktop.click_mouse_100_200",
      "from_port": "output_data",
      "from_direction": "OUT",
      "from_type": "DATA",
      "to_node": "web.scrape_page_300_200",
      "to_port": "input_data",
      "to_direction": "IN",
      "to_type": "DATA"
    }
  ]
}
```

**Key Changes:**
- Node keys include category: `category.function_x_y`
- Each node stores its category and function name separately
- Enables proper reconstruction on load

---

## Phase 1-2 MVP Implementation

### Scope

**What We're Building:**
1. ✅ Multi-file node discovery using Python AST
2. ✅ Tree view Node List with categories
3. ✅ FQNN support throughout system
4. ✅ Layout v2.0 save/load
5. ✅ Read-only function viewing (imports + function)
6. ✅ "Reload Script" button

**What We're NOT Building Yet:**
- ❌ Function editing/saving in editor
- ❌ External editor integration
- ❌ Context menus (right-click features)
- ❌ AST-based function replacement

**MVP Philosophy:** Edit files externally with your own editor, then click "Reload Script" to sync changes.

### New Components

#### 1. AST Utilities Module (`src/core/ast_utils.py`)

**Purpose:** Parse Python files to find and extract @node functions

**Key Functions:**
```python
def extract_nodes_from_file(file_path: Path, category: str) -> dict:
    """
    Parse a Python file and extract all @node decorated functions.

    Returns:
        Dictionary mapping FQNN to NodeMetadata
        Example: {"desktop.click_mouse": NodeMetadata(...)}
    """

def extract_function_with_imports(file_path: Path, function_name: str) -> str:
    """
    Extract imports from top of file + a single function's code.

    Returns:
        String containing imports and function definition
    """

def has_node_decorator(func_def: ast.FunctionDef) -> bool:
    """
    Check if an AST function definition has @node decorator.

    Returns:
        True if function has @node decorator
    """
```

**Implementation Notes:**
- Uses Python's `ast` module for parsing
- Extracts decorator information, docstrings, line numbers
- Handles syntax errors gracefully

#### 2. Node Registry (`src/core/node_registry.py`)

**Purpose:** Central registry of all discovered nodes

**Structure:**
```python
@dataclass
class NodeMetadata:
    """Metadata for a discovered node."""
    fqnn: str                    # "desktop.click_mouse"
    category: str                # "desktop"
    function_name: str           # "click_mouse"
    file_path: Path              # Path to desktop.py
    docstring: str               # Function docstring
    line_start: int              # Function starts at line 42
    line_end: int                # Function ends at line 58
    signature: str               # Function signature

class NodeRegistry:
    """Central registry of all discovered nodes."""

    def __init__(self):
        self.nodes: dict[str, NodeMetadata] = {}

    def discover(self, project_path: Path):
        """Scan project nodes/ directory and populate registry."""

    def get_metadata(self, fqnn: str) -> NodeMetadata:
        """Get metadata for a node by FQNN."""

    def get_by_category(self, category: str) -> dict[str, NodeMetadata]:
        """Get all nodes in a specific category."""
```

**Discovery Process:**
1. Scan `nodes/` directory for all .py files
2. For each file, extract category name from filename
3. Parse file with AST to find @node decorated functions
4. Create NodeMetadata for each discovered node
5. Store in registry with FQNN as key

#### 3. Tree View Node List (`src/ui/node_list.py`)

**Purpose:** Display nodes organized by category

**UI Structure:**
```
Node List
├── 📁 Desktop
│   ├── click_mouse
│   ├── type_text
│   └── get_window
├── 📁 Web
│   ├── scrape_page
│   ├── download_file
│   └── parse_html
└── 📁 Filesystem
    ├── read_file
    ├── write_file
    └── list_directory
```

**Implementation:**
```python
class NodeListWidget(QTreeWidget):  # Changed from QListWidget
    """Tree view of nodes organized by category."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Nodes")
        self.setDragEnabled(True)

    def populate_from_registry(self, node_registry: NodeRegistry):
        """Populate tree from discovered nodes."""
        # Group nodes by category
        # Create top-level items for each category
        # Add function items as children

    def startDrag(self, supportedActions):
        """Drag FQNN instead of just function name."""
        # Get FQNN from selected item
        # Create mime data with FQNN
```

**Behavior:**
- Categories are expandable/collapsible
- Only function items (not categories) are draggable
- Drag data contains FQNN (e.g., "desktop.click_mouse")

### Modified Components

#### 1. MainWindow (`src/main.py`)

**Changes:**
- Add `self.node_registry = NodeRegistry()`
- Add "Reload Script" button to toolbar
- Connect reload button to discovery process
- Pass registry to Node List widget

**New Methods:**
```python
def reload_script(self):
    """Reload nodes from files and update UI."""
    # Discover nodes from project
    # Update Node List tree view
    # Show status message

def on_project_opened(self, project_path: Path):
    """Called when project is opened."""
    # Trigger initial discovery
    # Populate Node List
```

#### 2. NodeItem (`src/ui/nodes/node_item.py`)

**Changes:**
- Store FQNN instead of just title
- Add `category` and `function_name` properties
- Display shortened name in UI (just function name)
- Tooltip shows full FQNN

**New Properties:**
```python
class NodeItem(QGraphicsItem):
    def __init__(self, fqnn: str, pos: QPointF):
        self.fqnn = fqnn  # "desktop.click_mouse"
        self.category = fqnn.split('.')[0]  # "desktop"
        self.function_name = fqnn.split('.')[1]  # "click_mouse"
        self.display_name = self.function_name  # Show in UI
```

#### 3. EditorWidget (`src/ui/editor.py`)

**Changes:**
- Add method to show function with imports
- Mark as read-only for MVP
- Add banner showing context

**New Methods:**
```python
def show_function_context(self, metadata: NodeMetadata):
    """Display imports + function (read-only)."""
    code = extract_function_with_imports(
        metadata.file_path,
        metadata.function_name
    )
    self.setPlainText(code)
    self.setReadOnly(True)
    self.show_banner(f"Viewing: {metadata.fqnn} (read-only)")
```

#### 4. LayoutManager (`src/utils/layout_manager.py`)

**Changes:**
- Update save format to v2.0 with category/function fields
- Generate keys as `category.function_x_y`
- Store category and function separately in node data

**New Save Format:**
```python
def save_layout(self, scene, file_path):
    layout_data = {
        "version": "2.0",
        "nodes": {},
        "connections": []
    }

    for item in scene.items():
        if isinstance(item, NodeItem):
            key = f"{item.fqnn}_{int(item.x())}_{int(item.y())}"
            layout_data["nodes"][key] = {
                "category": item.category,
                "function": item.function_name,
                "x": item.x(),
                "y": item.y()
            }
```

#### 5. CanvasGraphicsScene (`src/ui/canvas.py`)

**Changes:**
- Update dropEvent to use FQNN from mime data
- Create NodeItem with FQNN instead of simple title

**Modified dropEvent:**
```python
def dropEvent(self, event):
    fqnn = event.mimeData().text()  # "desktop.click_mouse"
    drop_pos = event.scenePos()

    # Create node with FQNN
    node = NodeItem(fqnn, drop_pos)
    self.addItem(node)
```

#### 6. ProjectManager (`src/utils/project_manager.py`)

**Changes:**
- Create `nodes/` directory instead of `workflow.py`
- Generate `example.py` template with @node decorator

**New Project Structure:**
```python
def create_project(name: str, location: str) -> Path:
    project_path = Path(location) / name
    project_path.mkdir(parents=True)

    # Create nodes/ directory
    nodes_dir = project_path / "nodes"
    nodes_dir.mkdir()

    # Create example.py with template
    example_file = nodes_dir / "example.py"
    example_file.write_text(EXAMPLE_CATEGORY_TEMPLATE)

    # Create requirements.txt
    (project_path / "requirements.txt").write_text("")

    # Create .layout.json
    (project_path / ".layout.json").write_text('{"version": "2.0", "nodes": {}, "connections": []}')

    return project_path
```

**Example Category Template:**
```python
EXAMPLE_CATEGORY_TEMPLATE = '''"""
Example Node Category

Add your @node decorated functions here.
"""

def node(func):
    """Decorator to mark a function as a workflow node."""
    func._is_workflow_node = True
    return func


@node
def example_node(inputs, global_state):
    """
    Example node that demonstrates the basic structure.

    Args:
        inputs: Dictionary of parent node outputs
        global_state: Shared state dictionary

    Returns:
        Dictionary of outputs for child nodes
    """
    print("Example node executed")
    return {"result": "Hello from example node"}


@node
def another_example(inputs, global_state):
    """Another example node."""
    data = inputs.get("example_node", {}).get("result", "")
    print(f"Received: {data}")
    return {"processed": data.upper()}
'''
```

---

## Implementation Steps

### Step 1: AST Utilities (~3 hours)
**File:** `src/core/ast_utils.py`

**Tasks:**
- [ ] Create module structure
- [ ] Implement `has_node_decorator()` function
- [ ] Implement `extract_nodes_from_file()` function
- [ ] Implement `extract_function_with_imports()` function
- [ ] Test with example.py file
- [ ] Handle syntax errors gracefully

**Testing:**
```python
# Test discovery
nodes = extract_nodes_from_file(Path("nodes/example.py"), "example")
assert "example.example_node" in nodes

# Test extraction
code = extract_function_with_imports(Path("nodes/example.py"), "example_node")
assert "import" in code or "def example_node" in code
```

### Step 2: Node Registry (~2 hours)
**File:** `src/core/node_registry.py`

**Tasks:**
- [ ] Create NodeMetadata dataclass
- [ ] Create NodeRegistry class
- [ ] Implement `discover()` method
- [ ] Implement `get_metadata()` method
- [ ] Implement `get_by_category()` method
- [ ] Test with sample project structure

**Testing:**
```python
# Test discovery
registry = NodeRegistry()
registry.discover(Path("test_project"))
assert len(registry.nodes) > 0
assert "example.example_node" in registry.nodes
```

### Step 3: Project Structure Updates (~1 hour)
**File:** `src/utils/project_manager.py`

**Tasks:**
- [ ] Update `create_project()` to create nodes/ directory
- [ ] Remove workflow.py creation
- [ ] Create EXAMPLE_CATEGORY_TEMPLATE constant
- [ ] Write example.py with template
- [ ] Update .layout.json to v2.0 format
- [ ] Test project creation

### Step 4: Tree View Node List (~3 hours)
**File:** `src/ui/node_list.py`

**Tasks:**
- [ ] Change base class from QListWidget to QTreeWidget
- [ ] Implement `populate_from_registry()` method
- [ ] Group nodes by category (top-level items)
- [ ] Add functions as children
- [ ] Update `startDrag()` to use FQNN
- [ ] Store FQNN in item data
- [ ] Test drag-and-drop

**UI Details:**
- Categories: Bold font, not draggable
- Functions: Normal font, draggable
- Store FQNN in Qt.ItemDataRole.UserRole

### Step 5: Layout System v2 (~2 hours)
**File:** `src/utils/layout_manager.py`

**Tasks:**
- [ ] Update `save_layout()` to use v2.0 format
- [ ] Save category + function separately
- [ ] Generate FQNN-based keys
- [ ] Update `load_layout()` to read v2.0 format
- [ ] Reconstruct FQNN from category + function
- [ ] Test save/load round-trip

### Step 6: Canvas Integration (~2 hours)
**Files:** `src/ui/nodes/node_item.py`, `src/ui/canvas.py`

**Tasks:**
- [ ] Update NodeItem constructor to accept FQNN
- [ ] Add category and function_name properties
- [ ] Update display to show just function name
- [ ] Add tooltip showing full FQNN
- [ ] Update canvas dropEvent to use FQNN
- [ ] Test node creation from drag-and-drop

### Step 7: Editor Display (~2 hours)
**File:** `src/ui/editor.py`

**Tasks:**
- [ ] Add `show_function_context()` method
- [ ] Integrate with ast_utils to extract code
- [ ] Set editor to read-only mode
- [ ] Add banner widget showing context
- [ ] Handle double-click on NodeItem
- [ ] Test function viewing

### Step 8: Reload Script Button (~1 hour)
**File:** `src/main.py`

**Tasks:**
- [ ] Add "Reload Script" button to toolbar
- [ ] Implement `reload_script()` method
- [ ] Trigger node discovery
- [ ] Update Node List from registry
- [ ] Show status message
- [ ] Test reload workflow

**Total Time Estimate: ~16 hours**

---

## Success Criteria

The MVP is complete when:

- ✅ New projects create nodes/ directory (no workflow.py)
- ✅ Can add desktop.py, web.py, etc. to nodes/
- ✅ Node List shows tree view with expandable categories
- ✅ Can drag nodes from tree onto canvas
- ✅ Nodes use FQNN internally (desktop.click_mouse)
- ✅ Nodes display just function name in UI
- ✅ Double-click node shows imports + function (read-only)
- ✅ Save/load preserves FQNN in .layout.json v2.0
- ✅ "Reload Script" updates Node List from files
- ✅ Can create projects, add nodes, save, close, and reopen successfully

---

## Future Enhancements (Phase 3-4)

**Not in MVP, but planned:**

1. **Function Editing**
   - Make editor editable
   - AST-based function replacement
   - Save updates back to category file

2. **External Editor Integration**
   - Right-click category → "Edit in External Editor"
   - Opens .py file in system default editor
   - Auto-reload on file change (optional)

3. **Context Menus**
   - Right-click category → Edit, Reload, New Node
   - Right-click function → Edit, View Source, Rename

4. **Advanced Features**
   - Function renaming
   - Category management (create, rename, delete)
   - Import management UI
   - Cross-category dependency warnings

---

## Technical Challenges & Solutions

### Challenge 1: AST Parsing Errors
**Problem:** User writes invalid Python, AST fails

**Solution:**
- Wrap ast.parse() in try-except
- Show user-friendly error message
- Fall back to showing entire file
- Don't crash the application

### Challenge 2: Circular Dependencies
**Problem:** Category A imports from Category B which imports from Category A

**Solution:**
- Document best practice: avoid cross-category imports
- If needed, create shared utils.py without @node functions
- Detection and warning in future phase

### Challenge 3: Import Extraction
**Problem:** Imports can be scattered (top-level, conditional, inside functions)

**Solution:**
- Only extract top-level imports for simplicity
- Conditional imports won't show in function view
- Document limitation, recommend external editing for complex cases

### Challenge 4: FQNN Migration
**Problem:** Existing projects use simple names, not FQNN

**Solution:**
- Since we're deprecating workflow.py, no migration needed
- Fresh start with new structure
- Old projects must be manually converted (future migration tool)

---

## Testing Strategy

### Unit Tests
- AST utilities with various Python code patterns
- Node registry discovery with mock file system
- FQNN parsing and generation
- Layout v2.0 serialization/deserialization

### Integration Tests
- Create project → add nodes → discover → populate list
- Drag node → create on canvas → save → load → verify
- Reload script → verify Node List updates
- Multiple categories with same function names

### Manual Testing Checklist
- [ ] Create new project, verify nodes/ directory exists
- [ ] Add desktop.py with @node functions
- [ ] Click "Reload Script", verify nodes appear in tree
- [ ] Expand category, verify functions listed
- [ ] Drag function to canvas, verify node created
- [ ] Double-click node, verify imports + function shown
- [ ] Save project, close, reopen, verify nodes restored
- [ ] Add another category (web.py), reload, verify both categories
- [ ] Test with duplicate function names across categories

---

## Migration Guide (For Existing Projects)

**Manual Migration Steps:**

1. Create `nodes/` directory in project root
2. Move `workflow.py` → `nodes/workflow.py` (or rename to appropriate category)
3. Delete old `workflow.py`
4. Click "Reload Script"
5. Existing nodes in canvas will need to be re-added (layout won't match)

**Future:** Automated migration tool to:
- Detect workflow.py
- Prompt for category name
- Move and update .layout.json automatically

---

## Documentation Updates Needed

After implementation:

1. Update CLAUDE.md with new architecture details
2. Update phase_one.md to reflect completed multi-file system
3. Create user guide for organizing nodes into categories
4. Document @node decorator usage
5. Add examples of well-structured category files
6. Document helper function patterns

---

## Next Steps After MVP

Once Phase 1-2 MVP is complete and tested:

**Phase 3: Function Editing (~10 hours)**
- Implement AST-based function replacement
- Make editor editable
- Add save functionality
- Handle edge cases (syntax errors, renamed functions)

**Phase 4: Polish (~6 hours)**
- External editor integration
- Context menus
- Category management UI
- Import management
- Improved error messages

**Phase 5: Advanced Features (~8 hours)**
- Function renaming with dependency tracking
- Category templates
- Node documentation generation
- Cross-category dependency analysis

**Total remaining for full system: ~24 hours**

---

## Appendix: Example Category Files

### Example: desktop.py
```python
"""
Desktop Automation Nodes

Functions for controlling desktop applications and UI.
"""

import pyautogui
import time

def node(func):
    """Decorator to mark a function as a workflow node."""
    func._is_workflow_node = True
    return func


# Helper function (not a node)
def _ensure_coordinates(x, y):
    """Validate coordinates are within screen bounds."""
    screen_width, screen_height = pyautogui.size()
    x = max(0, min(x, screen_width))
    y = max(0, min(y, screen_height))
    return x, y


@node
def click_mouse(inputs, global_state):
    """
    Click the mouse at specified coordinates.

    Inputs:
        x (int): X coordinate
        y (int): Y coordinate

    Returns:
        success (bool): Whether click succeeded
    """
    x = inputs.get("x", 0)
    y = inputs.get("y", 0)
    x, y = _ensure_coordinates(x, y)

    pyautogui.click(x, y)
    return {"success": True, "x": x, "y": y}


@node
def type_text(inputs, global_state):
    """
    Type text at current cursor position.

    Inputs:
        text (str): Text to type
        interval (float): Delay between keystrokes

    Returns:
        success (bool): Whether typing succeeded
        length (int): Number of characters typed
    """
    text = inputs.get("text", "")
    interval = inputs.get("interval", 0.01)

    pyautogui.typewrite(text, interval=interval)
    return {"success": True, "length": len(text)}


@node
def screenshot(inputs, global_state):
    """
    Take a screenshot and save to file.

    Inputs:
        filepath (str): Where to save screenshot

    Returns:
        success (bool): Whether screenshot succeeded
        filepath (str): Path where screenshot was saved
    """
    filepath = inputs.get("filepath", "screenshot.png")

    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)

    return {"success": True, "filepath": filepath}
```

### Example: web.py
```python
"""
Web Scraping Nodes

Functions for fetching and parsing web content.
"""

import requests
from bs4 import BeautifulSoup

def node(func):
    """Decorator to mark a function as a workflow node."""
    func._is_workflow_node = True
    return func


@node
def fetch_url(inputs, global_state):
    """
    Fetch HTML content from a URL.

    Inputs:
        url (str): URL to fetch
        timeout (int): Request timeout in seconds

    Returns:
        success (bool): Whether request succeeded
        html (str): HTML content
        status_code (int): HTTP status code
    """
    url = inputs.get("url", "")
    timeout = inputs.get("timeout", 10)

    try:
        response = requests.get(url, timeout=timeout)
        return {
            "success": True,
            "html": response.text,
            "status_code": response.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 0
        }


@node
def parse_html(inputs, global_state):
    """
    Parse HTML and extract text content.

    Inputs:
        html (str): HTML to parse
        selector (str): CSS selector to extract

    Returns:
        success (bool): Whether parsing succeeded
        elements (list): Extracted text elements
    """
    html = inputs.get("html", "")
    selector = inputs.get("selector", "")

    soup = BeautifulSoup(html, 'html.parser')

    if selector:
        elements = [elem.get_text() for elem in soup.select(selector)]
    else:
        elements = [soup.get_text()]

    return {
        "success": True,
        "elements": elements,
        "count": len(elements)
    }
```

---

## Summary

This architecture provides:
- **Organization**: Nodes grouped by category/domain
- **Scalability**: Projects can grow to hundreds of nodes
- **Maintainability**: Small, focused files instead of monoliths
- **Flexibility**: Edit full files externally or view functions internally
- **Clean Implementation**: AST-based parsing is robust and Pythonic

The MVP focuses on core discovery and organization features, with advanced editing deferred to later phases. This gets 80% of the value with 40% of the effort.
