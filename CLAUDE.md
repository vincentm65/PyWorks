# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude Reponse Rule
- I am learning to code, I need help mostly with syntax but understand basic concepts like functions and loops. I struggle with classes.
- Never modify the code for me unless explicity asked to.
- If I implement something my self, feel free to show me a better way of doing it so I can compare it to my own.
- If I am stuck, feel free to give me hints or lines of code entirely. I still want to write it myself.

## Project Overview

**PyWorks** is a visual scripting editor for Python that allows users to build and run workflows by writing standard Python functions, where each function is represented as a node in a graph-based editor. This bridges the gap between visual programming and traditional scripting.

**Core Concept:** Users write Python functions decorated with `@node`, and the visual editor automatically discovers these functions and displays them as draggable nodes on a canvas. Users connect nodes to define execution flow and data passing.

## Current Development Status

**Phase:** Phase 1 - Core UI and Canvas (54% complete)

**What's Working:**
- ✅ PyQt6 application with main window, menubar, toolbar
- ✅ Canvas with zoom (wheel), pan (drag), and custom dot matrix grid
- ✅ Three dockable panels: Node List (left), Editor (right), Console (bottom)
- ✅ Drag-and-drop node creation from Node List to Canvas
- ✅ NodeItem implementation with selection highlighting and grid snapping
- ✅ Node deletion with Delete/Backspace keys
- ✅ Dual grid snapping (drag + drop operations)

**Next Steps (from phase_one.md):**
- Step 6: Create ConnectionItem for visual connections between nodes 🔨 NEXT
- Step 7: Implement interactive connection drawing (drag from node to node)
- Step 8: Layout save/load system (.layout.json)
- Step 9: Manual node creation dialog
- Step 10: Visual polish (hover effects, status bar)

## Running the Application

```bash
# From project root
python src/main.py
```

**Note:** This project uses PyQt6, which should be installed in your environment. There is no requirements.txt yet, but PyQt6>=6.6.0 is required.

## Architecture

### Data Flow Model (Planned)

The execution model revolves around two key concepts:

**1. `global_state` Dictionary:**
- Shared across all nodes in a workflow
- Initialized once at workflow start
- Allows persistent state throughout execution

**2. `inputs` Dictionary:**
- Passed to each node containing return values from parent nodes
- Namespaced by parent function name
- Example: `inputs['get_data']['raw_data']`

**Node Signature:**
```python
from pyworks import node

@node
def process_data(inputs, global_state):
    """Process data from parent nodes."""
    data = inputs.get("get_data", {}).get("raw_data", [])
    result = [x * 2 for x in data]
    return {"processed_data": result}
```

### Project Structure

```
PyWorks/
├── src/
│   ├── main.py              # Application entry + MainWindow
│   ├── ui/
│   │   ├── canvas.py        # CanvasGraphicsView + CanvasGraphicsScene
│   │   ├── editor.py        # EditorWidget (code editor)
│   │   ├── node_list.py     # NodeListWidget (draggable node palette)
│   │   └── console.py       # ConsoleTextView (output console)
│   ├── nodes/
│   │   ├── node_item.py     # NodeItem (QGraphicsItem for visual nodes)
│   │   └── connection_item.py  # [TODO] ConnectionItem for edges
│   └── utils/               # [TODO] Layout manager, execution engine
├── plan.md                  # Complete technical specification
└── phase_one.md            # Phase 1 implementation guide
```

### Key Files

**src/main.py:1-86**
- `MainWindow`: Main application window with PyQt6
- Creates toolbar (Run, Pause, Stop), menubar (File, Edit)
- Sets up three dock widgets for Node List, Editor, Console
- Canvas as central widget

**src/ui/canvas.py:9-112**
- `CanvasGraphicsView`: Graphics view with zoom/pan
- `CanvasGraphicsScene`: Scene with dot matrix grid background, drag-drop support
- Handles node deletion (Delete/Backspace keys)
- Grid snapping (20px intervals)

**src/nodes/node_item.py:6-58**
- `NodeItem`: Visual representation of a workflow node
- Draggable, selectable, with grid snapping
- Shows function name as title
- Selection highlights with blue border (#4285F4)

**src/ui/node_list.py:6-21**
- Drag-enabled list widget with placeholder nodes (Node1, Node2, Node3)
- Nodes can be dragged onto canvas to create instances

## Layout System (Planned)

The `.layout.json` file stores visual layout separately from code:

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

**Synchronization Strategy:**
- **Python code (`workflow.py`)**: Source of truth for what nodes exist
- **`.layout.json`**: Source of truth for positions and connections
- **Manual sync**: User clicks "Reload Script" button to sync code → canvas
- **Auto-save**: Canvas changes (positions, connections) auto-save to `.layout.json`

## Execution Model (Future Phases)

**Graph Execution:**
- DAG (Directed Acyclic Graph) only - cycles are forbidden
- Topological sort determines execution order
- Each workflow runs in isolated subprocess using project-specific venv
- Node discovery via `importlib` + `inspect` (checks for `_is_workflow_node` attribute)

**Error Handling:**
- Failed nodes stop downstream dependencies
- Independent branches continue execution
- Visual states: pending, running, completed, error, blocked

**Isolation:**
- Each project has its own `.venv/` directory
- User code runs in separate process (subprocess module)
- Communication via stdout/stderr pipes

## PyQt6 Conventions Used

**Graphics Framework:**
- Scene coordinates: -5000 to 5000 (large canvas)
- Grid size: 20px (for snapping)
- Zoom limits: 0.1x to 5.0x
- Antialiasing enabled for smooth rendering

**Color Scheme:**
- Background: #222 (dark)
- Grid dots: rgb(100, 100, 100)
- Node background: #444
- Node border: #444 (normal), #4285F4 (selected)
- Text: #fff (white)

**Drag and Drop:**
- Node List → Canvas uses QMimeData with text (node name)
- Canvas accepts drops and creates NodeItem at drop position (grid-snapped)

## Important Implementation Details

### Grid Snapping
All node positions snap to 20px grid intervals. This happens in two places:
1. `NodeItem.itemChange()` - during manual dragging
2. `CanvasGraphicsView.dropEvent()` - when dropping from node list

### Canvas Navigation
- **Zoom**: Ctrl+Wheel (not implemented yet, but zoom works with just wheel)
- **Pan**: Click and drag (ScrollHandDrag mode)
- **Delete**: Select nodes and press Delete or Backspace

### Node Visual States (Planned)
- Pending: #E0E0E0 (light gray)
- Running: #64B5F6 (light blue)
- Completed: #81C784 (light green)
- Error: #E57373 (light red)
- Blocked: #FFB74D (light orange)

## Known Issues

**src/ui/console.py:11**
- Bug: `self.console.write()` should be `self.append()` - console widget is not yet functional

**Missing Features (Phase 1):**
- No connection drawing between nodes yet
- No save/load for layouts
- No connection anchors on nodes
- No hover effects or visual feedback
- Node List has hardcoded placeholder nodes instead of loading from workflow.py

## Development Workflow

1. **Adding Visual Features**: Work primarily in `src/ui/` and `src/nodes/`
2. **Testing Changes**: Run `python src/main.py` and interact with the GUI
3. **Next Milestone**: Complete Phase 1 by implementing ConnectionItem and interactive connection drawing
4. **Reference Documentation**: See `plan.md` for full technical spec, `phase_one.md` for step-by-step guide

## Future Phases (Not Yet Implemented)

- **Phase 2**: Basic workflow execution with hardcoded workflows
- **Phase 3**: Dynamic node loading (parse Python files for @node decorator)
- **Phase 4**: Virtual environment and dependency management
- **Phase 5**: Integration, polish, real-time execution feedback

## Design Philosophy

**Simplicity First:**
- Manual synchronization (explicit "Reload Script" button) over automatic syncing
- DAG-only execution (no cycles) to avoid complexity
- Decorator-based node discovery (Pythonic and familiar)
- Process isolation for safety without complex sandboxing

**User Experience:**
- Visual editor should feel responsive and predictable
- Code is the source of truth for logic
- Layout is visual metadata stored separately
- No custom config languages - just Python

## When Adding New Node Types

1. Ensure `@node` decorator is applied to function
2. Function signature must be `def func_name(inputs, global_state):`
3. Return a dictionary of output values
4. Node will auto-appear in canvas after "Reload Script" (future feature)

## When Modifying the Canvas

- Always maintain scene coordinate system (-5000 to 5000)
- Preserve grid snapping behavior (20px intervals)
- Use `QPointF` for positions, convert to grid via `round(value / 20) * 20`
- Update connections when nodes move (future: via `itemChange()` callback)

## When Working with QGraphicsItems

- Override `boundingRect()` and `paint()` (required)
- Use item flags for behavior: `ItemIsMovable`, `ItemIsSelectable`, `ItemSendsGeometryChanges`
- Handle `itemChange()` for position updates that affect other items
- Use `update()` to trigger repaints when visual state changes
