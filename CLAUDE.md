# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Claude Response Rule
- I am learning to code, I need help mostly with syntax but understand basic concepts like functions and loops. I struggle with classes.
- Never modify the code for me unless explicitly asked to.
- If I implement something myself, feel free to show me a better way of doing it so I can compare it to my own.
- If I am stuck, feel free to give me hints or lines of code entirely. I still want to write it myself.

## Effective Explanation Pattern (IMPORTANT) - Learning-Focused Blueprint Approach

When explaining code solutions, use this **blueprint-first pattern** that guides you to implement rather than hands you complete code. This approach empowers learning while providing clear direction.

### Pattern Structure:

1. **Mental Model / Analogy** (Start here!)
   - Explain what you're doing in real-world terms
   - Example: "Think of scene.items() as a box of mixed items. Your job is to pick out only the nodes."

2. **Understand the Data** (Before any code)
   - Show what data structures you're working with
   - Use concrete examples: `[NodeItem(...), PortItem(...), NodeItem(...)]`
   - Explain what each piece represents and how to access them

3. **Syntax Hints for Lesser-Known Patterns**
   - Explain specific Python/PyQt6 syntax you'll need:
     - `isinstance(item, NodeItem)` → "Checks object type, returns True/False"
     - Dictionary `.get()` method → "Safe access with default: `dict.get('key', default_value)`"
     - List comprehensions → "Compact loop: `[x * 2 for x in list]` is like `for x in list: new_list.append(x*2)`"
     - F-strings → "Insert variables: `f"{variable_name}"` becomes the actual value"
     - Lambda functions → "Quick inline function: `lambda x: x * 2` is shorthand for defining a function"
   - Clarify PyQt6 specifics like signals, item flags, and coordinate systems as needed

4. **Blueprint / Pseudo-Code** (High-level logic map)
   - Provide pseudo-code showing the algorithm structure without Python syntax:
     ```
     FUNCTION process_data(inputs):
       FOR EACH item in input_list:
         IF item matches condition THEN:
           DO something with item
           STORE result
       RETURN result
     ```
   - Show decision points and loops clearly
   - Indicate where different branches diverge

5. **Implementation Guidance**
   - Specify the function signature (what parameters, what it returns)
   - Break the task into 2-4 specific steps with guidance on each
   - Suggest which data structures to use (list vs dict, etc.)
   - Hint at library methods available (`.items()`, `.append()`, etc.) without giving full code
   - Point to similar code in the codebase to reference as patterns

6. **Syntax Hints for Implementation**
   - When you anticipate syntax challenges, provide standalone hints:
     - "Python dicts use `key in dict` to check existence, or `for key, value in dict.items()` to iterate"
     - "PyQt6 signals are connected with `.signal.connect(slot_function)`"
     - "String formatting: use f-strings for readability: `f"Node at {x}, {y}"`"
   - Don't embed these in pseudo-code; call them out separately

7. **Testing & Q&A** (After you've implemented)
   - Once you've written your code and asked for review, THEN I provide:
     - Full corrected code if your approach differs significantly
     - Side-by-side comparison explaining trade-offs
     - Why certain syntax choices are better (performance, readability, etc.)
   - Answer "Why" questions about design choices
   - Point out patterns your code uses that transfer to other problems

### When to Use This Pattern:

- User asks for help implementing a feature
- User is stuck on how to structure a solution
- Explaining complex iterations/filtering patterns
- Teaching fundamental programming concepts they struggle with (like classes, loops with conditions)
- Feature requests or bug fixes requiring code changes

### When to Break This Pattern:

- User explicitly says "just give me the code" for a task
- User says "I'm stuck" and has already tried multiple times (then provide hints + working code)
- User asks for a code review (provide corrected full code with explanations)
- Quick syntax questions (answer directly, no blueprint needed)

## Running the Application

```bash
# From project root
python src/main.py
```

The application launches with a welcome dialog prompting you to create a new project or open an existing one. Each project is a self-contained folder containing your workflow code, layout, and dependencies.

## Project Overview

**PyWorks** is a visual scripting editor for Python that allows users to build and run workflows by writing standard Python functions, where each function is represented as a node in a graph-based editor. This bridges the gap between visual programming and traditional scripting.

**Core Concept:** Users write Python functions decorated with `@node`, and the visual editor automatically discovers these functions and displays them as draggable nodes on a canvas. Users connect nodes to define execution flow and data passing.

## Current Development Status

**Phase:** Phase 1 - Core UI and Canvas (85% complete)

**What's Working:**
- ✅ PyQt6 application with main window, menubar, toolbar
- ✅ Project management system (new, open, save, save-as with validation)
- ✅ Welcome dialog on launch with project creation/selection
- ✅ Canvas with zoom (wheel), pan (drag), and custom dot matrix grid
- ✅ Three dockable panels: Node List (left), Editor (right), Console (bottom)
- ✅ Drag-and-drop node creation from Node List to Canvas
- ✅ NodeItem implementation with 4 ports (input_data, output_data, input_flow, output_flow)
- ✅ Port-based connection system with type and direction validation
- ✅ ConnectionBridge with orthogonal curved routing
- ✅ Interactive connection drawing (drag from port to port)
- ✅ Node deletion with Delete/Backspace keys
- ✅ Dual grid snapping (drag + drop operations)
- ✅ Layout save/load system (.layout.json with full graph serialization)
- ✅ Connection storage and reconstruction
- 🔨 Step 9: Manual node creation dialog (TODO)
- 🔨 Step 10: Final visual polish (minor refinements)

**Next Steps:**
- Step 9: Add UI dialog for manual node creation (alternative to drag-drop)
- Step 10: Visual polish (status bar, connection glow effects fine-tuning)
- Step 11: Remove debug prints from connection_item.py

## Architecture

### Project Structure

```
PyWorks/
├── src/
│   ├── main.py              # Application entry + MainWindow
│   ├── ui/
│   │   ├── canvas.py        # CanvasGraphicsView + CanvasGraphicsScene
│   │   ├── editor.py        # EditorWidget (code editor)
│   │   ├── node_list.py     # NodeListWidget (draggable node palette)
│   │   ├── console.py       # ConsoleTextView (output console)
│   │   ├── dialogs/
│   │   │   └── welcome_dialog.py    # Project creation/selection dialog
│   │   └── nodes/
│   │       ├── node_item.py         # NodeItem (QGraphicsItem with 4 ports)
│   │       ├── port.py              # Port class (IN/OUT, DATA/FLOW types)
│   │       └── connection_item.py   # ConnectionBridge (edges with routing)
│   └── utils/
│       ├── layout_manager.py        # Save/load .layout.json system
│       └── project_manager.py       # Project creation, validation, folder structure
├── plan.md                  # Complete technical specification
└── phase_one.md            # Phase 1 implementation guide
```

### Key Architectural Concepts

#### 1. **Node Identification System**
Each node instance gets a unique composite key combining function name with position:
```
key = f"{title}_{x}_{y}"
```
This allows multiple nodes with the same function name to coexist without collision.

#### 2. **Port Architecture**
Each node has exactly 4 ports fixed in position:
- **input_data** (IN, DATA) - Blue circle, left side, y=30, receives values
- **output_data** (OUT, DATA) - Blue triangle, right side, y=30, provides values
- **input_flow** (IN, FLOW) - Green circle, left side, y=50, receives execution signal
- **output_flow** (OUT, FLOW) - Green triangle, right side, y=50, provides execution signal

**Visual Design:**
- IN ports: Circles (◯) on left
- OUT ports: Triangles (▶) on right
- DATA ports: Blue (#4285F4)
- FLOW ports: Green (#2D7A3E)

**Connection Rules:**
- Connections always go OUT → IN (automatic normalization in ConnectionBridge)
- Only same types can connect (DATA to DATA, FLOW to FLOW)
- No self-connections allowed
- No duplicate connections between same ports

#### 3. **Connection System (ConnectionBridge)**
Implements edge visualization and interactive connection drawing:
- **Orthogonal Routing**: Paths use horizontal-vertical-horizontal pattern with curved corners
- **Smart Midpoint Calculation**: Adjusts routing based on port type and vertical positions
- **Color Coding**:
  - FLOW connections: Gray (#6E6E6E)
  - DATA connections: Purple (#8A2BE2)
- **Interactive Drawing**: Drag from one port to another; temporary dashed line shows path
- **Visual Feedback**:
  - Hover glow effects (white when normal, blue when selected)
  - Automatic path updates when nodes move
  - Connection cleanup when nodes are deleted

**Implementation Location**: `src/ui/nodes/connection_item.py`

#### 4. **Project Management System**
Each project is a self-contained folder:
```
my_project/
├── workflow.py         # Python code with @node decorated functions
├── requirements.txt    # Dependencies (one per line)
└── .layout.json        # Visual layout (positions and connections)
```

**Workflow**:
1. User selects "New Project" or "Open Project" from welcome dialog
2. ProjectManager validates folder structure and creates missing files
3. Layout loads from .layout.json and reconstructs canvas state
4. Editor displays workflow.py code
5. User edits code; changes auto-save
6. Ctrl+S saves layout changes back to .layout.json

**Validation**: Projects must contain valid workflow.py and .layout.json files.

#### 5. **Layout Save/Load System**
Serializes entire canvas state to `.layout.json`:

```json
{
  "version": "1.0",
  "nodes": {
    "GetData_100_200": {
      "title": "GetData",
      "x": 100,
      "y": 200
    }
  },
  "connections": [
    {
      "from_node": "GetData_100_200",
      "from_port": "output_data",
      "from_direction": "OUT",
      "from_type": "DATA",
      "to_node": "ProcessData_350_200",
      "to_port": "input_data",
      "to_direction": "IN",
      "to_type": "DATA"
    }
  ]
}
```

**Key Features**:
- Stores complete port metadata (type + direction) for validation on load
- Handles missing nodes gracefully (skips orphaned connections)
- Stores node uniqueness via composite keys
- Preserves exact visual layout including all connection paths

### Data Flow Model

Two key concepts drive execution:

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

## Canvas System Details

### Grid and Coordinate System
- **Scene coordinates**: -5000 to 5000 (large virtual canvas)
- **Grid size**: 20px intervals
- **Zoom limits**: 0.1x to 5.0x
- **Snap behavior**: All node positions snap to nearest 20px grid point during drag or drop

### Interactive Connection Drawing
Located in `src/ui/canvas.py` (lines 119-164):
1. User clicks and drags from an output port
2. Temporary dashed line follows mouse cursor
3. When hovering over a valid input port (matching type), port highlights
4. Release mouse to create connection (or click to cancel)
5. ConnectionBridge handles validation, path routing, and storage

### Node Movement and Updates
When a node is dragged:
1. `NodeItem.itemChange()` snaps position to grid
2. All connected ConnectionBridge items are notified
3. Each bridge recalculates its orthogonal path
4. Scene updates automatically

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
- Selection glow: #4285F4 (blue)
- DATA ports: #4285F4 (blue)
- FLOW ports: #2D7A3E (green)
- Connections: #6E6E6E (FLOW), #8A2BE2 (DATA)

**Drag and Drop:**
- Node List → Canvas uses QMimeData with text (node name)
- Canvas accepts drops and creates NodeItem at drop position (grid-snapped)
- Port hover highlights during connection drawing

## Important Implementation Details

### Port Implementation (src/ui/nodes/port.py)
Each port is a circular/triangular visual element with:
- Position relative to parent node
- Type (DATA or FLOW) and direction (IN or OUT)
- Connection list (multiple connections allowed to same port)
- Visual feedback during hover/selection
- `can_connect_to()` validation method checking type matching and direction

### Connection Updates on Node Movement
When a node moves, `itemChange()` signals all connections:
```python
# In NodeItem
def itemChange(self, change, value):
    if change == QGraphicsItem.ItemPositionHasChanged:
        # Update all connected bridges
        for connection in self.connections:
            connection.update_path()
```

### Grid Snapping Logic
Snapping happens in two places for consistency:
1. **During drag**: `NodeItem.itemChange()` rounds position to grid
2. **During drop**: `CanvasGraphicsView.dropEvent()` snaps drop position

```python
snapped_x = round(pos.x() / 20) * 20
snapped_y = round(pos.y() / 20) * 20
```

## Known Issues and TODOs

**Code Quality**:
- Debug print statements in `connection_item.py` lines 98-102 should be removed
- Two `node_item.py` files exist (`src/nodes/` and `src/ui/nodes/`) - cleanup needed, currently using `src/ui/nodes/`

**Missing Features (Phase 1 Remaining)**:
- Step 9: No manual node creation dialog (only drag-drop from palette)
- Step 10: Connection glow effects could be fine-tuned
- No undo/redo system (menu items are placeholders)
- Node List still has hardcoded placeholder nodes instead of loading from workflow.py (deferred to Phase 2)

**Future Phases**:
- Phase 2: Dynamic node loading (parse Python files for @node decorator)
- Phase 3: Virtual environment and dependency management
- Phase 4: Graph execution engine with subprocess isolation
- Phase 5: Integration, polish, real-time execution feedback

## Development Workflow

### Common Development Tasks

**Running the app:**
```bash
python src/main.py
```

**Testing a change:**
1. Edit the relevant file (e.g., `src/ui/nodes/connection_item.py`)
2. Run the app and interact with the changed feature
3. Look for debug prints in console output
4. Check that grid snapping, zoom, and pan still work

**Adding a new port to nodes:**
1. Modify port definitions in `src/ui/nodes/node_item.py` (around line 40)
2. Update `port.py` if adding new port types
3. Update connection validation in `port.py` `can_connect_to()` method
4. Test connection drawing with new port type

**Debugging layout issues:**
1. Open the `.layout.json` file in your project folder
2. Verify node keys match `{title}_{x}_{y}` format
3. Check that all `from_node` and `to_node` references exist
4. Use console output to verify layout loading in `project_manager.py`

### When Adding Visual Features
1. Work primarily in `src/ui/` (canvas, nodes, dialogs)
2. Test with PyQt6 by running `python src/main.py`
3. Make sure grid snapping still works after changes
4. Ensure connections update properly when nodes move

### When Modifying Node Architecture
1. Update `src/ui/nodes/node_item.py` for visual changes
2. Update `src/ui/nodes/port.py` for port behavior
3. Update `connection_item.py` if routing logic changes
4. Test with both new and existing projects (load from .layout.json)

### When Working with QGraphicsItems
- Override `boundingRect()` and `paint()` (required)
- Use item flags for behavior: `ItemIsMovable`, `ItemIsSelectable`, `ItemSendsGeometryChanges`
- Handle `itemChange()` for position updates that affect other items
- Use `update()` to trigger repaints when visual state changes
- Remember to call parent class methods in overrides

### When Saving/Loading Projects
- Always validate that nodes exist before restoring connections
- Use `layout_manager.py` for serialization; don't write JSON directly
- Test with projects missing nodes/connections to ensure graceful handling
- Remember that layout is separate from code; code is the source of truth

## Recent Development History

Key commits showing implementation progression:
- `94d486b` - Minor changes (latest)
- `fa91f38` - Switched to project-based saving
- `bd0f475` - Save polish
- `36c1266` - Basic save and load implemented
- `d79732a` - Polished bridges (connection system)
- Earlier - Port system, node items, canvas foundation

## Design Philosophy

**Simplicity First:**
- Manual synchronization between code and layout (explicit saves vs. auto-sync)
- Port-based connections (clearer intent than generic edges)
- Composite node keys for uniqueness without UUIDs
- Orthogonal routing for predictable, readable layouts

**User Experience:**
- Visual editor should feel responsive and predictable
- Code is the source of truth for logic
- Layout is visual metadata stored separately
- Welcome dialog guides first-time users
- Grid snapping provides satisfying, aligned layouts

**Code Organization:**
- Separate concerns: ports, connections, nodes are independent classes
- Layout manager handles all JSON serialization
- Project manager handles folder structure and validation
- Canvas manages drawing and interaction
