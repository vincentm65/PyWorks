from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen, QTransform

from ui.nodes.node_item import NodeItem
from ui.nodes.port import PortItem
from ui.nodes.connection_item import ConnectionBridge


class CanvasGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAcceptDrops(True)

        # Attach the custom scene
        self.scene = CanvasGraphicsScene(self)
        self.scene.setSceneRect(QRectF(-5000, -5000, 10000, 10000))
        self.setScene(self.scene)
        

        # Initial zoom level
        self.zoom_factor = 1.25
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.current_scale = 1.0

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            zoom = self.zoom_factor
        else:
            zoom = 1 / self.zoom_factor

        new_scale = self.current_scale * zoom

        if self.min_zoom <= new_scale <= self.max_zoom:
            self.scale(zoom, zoom)
            self.current_scale = new_scale

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.viewport().rect()
        border_width = 2
        adjusted_rect = rect.adjusted(border_width // 2, border_width // 2, -border_width // 2, -border_width // 2)

        border_pen = QPen(QColor("#555"), border_width)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(adjusted_rect, 10, 10)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        event.acceptProposedAction()
    
    def dropEvent(self, event):
        node_name = event.mimeData().text()
        scene_pos = self.mapToScene(event.position().toPoint())

        scene_pos_x = round(scene_pos.x() / 20) * 20
        scene_pos_y = round(scene_pos.y() / 20) * 20

        node = NodeItem(node_name, scene_pos_x, scene_pos_y)
        self.scene.addItem(node)
        event.acceptProposedAction()

class CanvasGraphicsScene(QGraphicsScene):
    # Signal emitted when a node is double-clicked
    nodeDoubleClicked = pyqtSignal(str)  # Emits FQNN

    def __init__(self, parent=None, grid_size=20, radius=10):
        super().__init__(parent)
        self.setBackgroundBrush(QColor("#222"))
        self.gridSize = grid_size
        self.radius = radius
        self.temp_connection = None
        self.connection_start_port = None
        self.is_drawing_connection = False
        self.connections = []

    def addItem(self, item):
        """Override addItem to connect NodeItem signals."""
        super().addItem(item)
        # Connect nodeDoubleClicked signal from NodeItem to scene signal
        if isinstance(item, NodeItem):
            item.nodeDoubleClicked.connect(self.nodeDoubleClicked.emit)

    def drawBackground(self, painter, rect):
        path = QPainterPath()
        path.addRoundedRect(rect, self.radius, self.radius)
        painter.setClipPath(path)

        painter.fillRect(rect, self.backgroundBrush())

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(100, 100, 100))

        left  = int(rect.left()) - (int(rect.left()) % self.gridSize)
        top   = int(rect.top())  - (int(rect.top())  % self.gridSize)

        for x in range(left, int(rect.right()), self.gridSize):
            for y in range(top, int(rect.bottom()), self.gridSize):
                painter.drawEllipse(x, y, 2, 2)

    def dropEvent(self, event):
        event.setDropAction(Qt.DropAction.CopyAction)
        event.accept()

    def keyPressEvent(self, event):
        # Backspace or delete for removing nodes
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            for item in self.selectedItems():
                self.removeItem(item)
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), QTransform())

        if isinstance(item, PortItem):
            self.is_drawing_connection = True
            self.connection_start_port = item


        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing_connection:
            if self.temp_connection is None:
                self.temp_connection = QGraphicsLineItem()
                self.temp_connection.setPen(QPen(QColor("#FFF"), 2, Qt.PenStyle.DashLine))
                self.addItem(self.temp_connection)

            start_pos = self.connection_start_port.get_center_pos()
            end_pos = event.scenePos()

            self.temp_connection.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_drawing_connection:
            target_port = None
            for item in self.items(event.scenePos()):
                if isinstance(item, PortItem):
                    target_port = item
                    break

            if target_port:
                can_connect = self.connection_start_port.can_connect_to(target_port)

                if can_connect:
                    connection = ConnectionBridge(self.connection_start_port, target_port)
                    self.addItem(connection)
                    self.connections.append(connection)

            if self.temp_connection:
                self.removeItem(self.temp_connection)
                self.temp_connection = None

            self.is_drawing_connection = False
            self.connection_start_port = None

        return super().mouseReleaseEvent(event)