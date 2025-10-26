# Drag-and-Drop Node Implementation Plan

## Current Status

### What You've Completed ✅

1. **NodeListWidget** (`src/ui/node_list.py`):
   - ✅ Drag enabled
   - ✅ `startDrag()` method implemented with QMimeData
   - ⚠️ Missing imports for `QDrag` and `QMimeData`

2. **NodeItem** (`src/nodes/node_item.py`):
   - ✅ Basic class structure with width/height
   - ✅ `boundingRect()` implemented
   - ✅ `paint()` method started
   - ⚠️ Several issues to fix (see below)

3. **Canvas** (`src/ui/canvas.py`):
   - ✅ Scene and view setup complete
   - ❌ No drop event handling yet

---

## Issues to Fix & Features to Add 🔨

### Critical Fixes in `node_item.py`:
1. **Typo**: Line 2 - `QGraphicItem` → `QGraphicsItem`
2. **Missing imports**: Need to import `QRectF`, `QColor`, `QPen`, `QBrush`
3. **Missing constructor parameter**: Needs `function_name` parameter
4. **Missing flags**: Not movable or selectable
5. **Status method bug**: Line 26-32 has circular logic (method calls itself)
6. **Unused radius**: Line 18 defines `radius` but doesn't use it in `drawRoundedRect()`

---

## Implementation Steps

### Phase 1: Fix NodeItem class (`src/nodes/node_item.py`)
- [ ] Fix typo: `QGraphicItem` → `QGraphicsItem`
- [ ] Add missing imports: `QRectF`, `QColor`, `QPen`, `QBrush` from `PyQt6.QtGui`
- [ ] Update `__init__` to accept `function_name`, `x`, `y` parameters
- [ ] Set flags: `ItemIsMovable`, `ItemIsSelectable`, `ItemSendsGeometryChanges`
- [ ] Fix status coloring logic:
  - Remove circular method (method calling itself)
  - Use instance variable `self.status` instead
  - Apply color in `paint()` method based on status
- [ ] Use `radius` parameter in `drawRoundedRect()` call
- [ ] Set initial position with `setPos(x, y)`

### Phase 2: Complete drag setup (`src/ui/node_list.py`)
- [ ] Add missing imports: `QDrag`, `QMimeData` from `PyQt6.QtCore`

### Phase 3: Implement drop handling (`src/ui/canvas.py`)

**Option A: Handle drops in CanvasGraphicsView (Recommended)**
- [ ] Override `dragEnterEvent(event)` in `CanvasGraphicsView`
  - Call `event.acceptProposedAction()`
- [ ] Override `dragMoveEvent(event)` in `CanvasGraphicsView`
  - Call `event.acceptProposedAction()`
- [ ] Override `dropEvent(event)` in `CanvasGraphicsView`
  - Extract node name: `event.mimeData().text()`
  - Get scene position: `self.mapToScene(event.pos())`
  - Create NodeItem at position
  - Add to scene: `self.scene.addItem(node)`
  - Accept event: `event.acceptProposedAction()`

**Option B: Handle drops in CanvasGraphicsScene (Alternative)**
- Override same events in scene instead of view
- Note: May conflict with `ScrollHandDrag` mode in view

### Phase 4: Create nodes package init (`src/nodes/__init__.py`)
- [ ] Create `src/nodes/__init__.py`
- [ ] Optionally export NodeItem: `from .node_item import NodeItem`

---

## Key Concepts

### Qt Drag-and-Drop System
This uses a three-part collaboration:
1. **Source** (NodeList) creates QMimeData containing the node type
2. **Transfer** happens through Qt's event system with visual feedback
3. **Target** (Scene/View) receives the data and creates the visual node

### Drag Mode Conflict
The canvas uses `ScrollHandDrag` for panning, which can interfere with drop events. We handle drops at the **view level** (not scene) to avoid conflicts. The view receives drop events first and can accept them before the drag mode intercepts.

### QGraphicsItem Flags
- `ItemIsMovable`: Allows dragging the item with mouse
- `ItemIsSelectable`: Allows selecting with mouse click
- `ItemSendsGeometryChanges`: Notifies when position/transform changes (useful for updating connections later)

---

## Testing Checklist

After implementation:
- [ ] Can drag items from node list
- [ ] Drag shows visual feedback
- [ ] Can drop on canvas at specific location
- [ ] Node appears as a box at drop location
- [ ] Node is draggable after creation
- [ ] Node is selectable (click shows selection)
- [ ] Multiple nodes can be created
- [ ] Node displays correct function name

---

## Expected Result

You'll be able to:
1. Click and drag an item from the Node List panel
2. See a drag cursor/indicator
3. Drop onto the canvas at any position
4. See a box-shaped node appear with the function name
5. Drag the created node around the canvas
6. Select nodes by clicking them
