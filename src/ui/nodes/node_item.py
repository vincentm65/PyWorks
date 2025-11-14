import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsItem, QGraphicsObject, QStyle
from PyQt6.QtCore import QRectF, QMimeData, QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QDrag, QPen, QBrush

from ui.nodes.port import PortItem

class NodeItem(QGraphicsObject):
    # Signal emitted when node is double-clicked
    nodeDoubleClicked = pyqtSignal(str)  # Emits FQNN

    def __init__(self, fqnn, x, y, parent=None):
        super().__init__(parent)
        # Node properties
        self.width = 140
        self.height = 80
        self.fqnn = fqnn
        self.category = fqnn.split('.')[0]
        self.function_name = fqnn.split('.')[1]
        self.add_ports()
        self.setAcceptHoverEvents(True)
        self.is_hovered = False
        self.is_executing = False
        self.setToolTip(fqnn)

        # Center the node at the given position
        self.setPos(x - self.width / 2, y - self.height / 2)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
    
    def set_executing(self, executing: bool):
        self.is_executing = executing
        self.update()

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter, option, widget):
        radius = 10

        is_selected = option.state & QStyle.StateFlag.State_Selected

        if self.is_executing:
            glow_color = QColor(0, 255, 0, 150) # Green glow
            glow_size = 5
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow_color)
            painter.drawRoundedRect(
                        -glow_size, -glow_size,
                        self.width + glow_size * 2,
                        self.height + glow_size * 2,
                        radius + glow_size,
                        radius + glow_size
                    )
        elif self.is_hovered:
            # Determine glow color
            if is_selected:
                glow_color = QColor(66, 133, 244, 80)
            else:
                glow_color = QColor(255, 255, 255, 40)

            glow_size = 4
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow_color)
            painter.drawRoundedRect(
                        -glow_size, -glow_size,
                        self.width + glow_size * 2,
                        self.height + glow_size * 2,
                        radius + glow_size,
                        radius + glow_size
                    )
            
        if is_selected:
            border_pen = QPen(QColor("#4285F4"), 1.5)
        else: 
            border_pen= QPen(QColor("#888"), 1.5)

        painter.setBrush(QColor("#444"))
        painter.setPen(border_pen)
        painter.drawRoundedRect(0, 0, self.width, self.height, radius, radius)
        painter.setPen(QColor("#fff"))
        painter.drawText(10, 20, self.function_name)
    
    def get_status_color(self):
        colors = {
            "idle": "#444",
            "running": "#4a4",
            "error": "#a44"
        }
        return colors.get(getattr(self, '_status', 'idle'), "#444")
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene_pos_x = round(value.x() / 20) * 20
            scene_pos_y = round(value.y() / 20) * 20
            new_pos = QPointF(scene_pos_x, scene_pos_y)

            if self.scene() and hasattr(self.scene(), 'connections'):
                for connection in self.scene().connections:
                    if connection.source_port in self.ports or connection.target_port in self.ports:
                        connection.update_path()
            return new_pos
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneChange:
            if value is None and self.scene():
                connections_to_remove = []
                for connection in self.scene().connections:
                    if connection.source_port in self.ports or connection.target_port in self.ports:
                        connections_to_remove.append(connection)

                for connection in connections_to_remove:
                    self.scene().removeItem(connection)
                    self.scene().connections.remove(connection)
        return super().itemChange(change, value)

    def add_ports(self):
        self.input_data = PortItem("DATA", "IN", self, self)
        self.input_data.setPos(0, 30)
        
        self.output_data = PortItem("DATA", "OUT", self, self)
        self.output_data.setPos(self.width, 30)

        self.input_flow = PortItem("FLOW", "IN", self, self)
        self.input_flow.setPos(0, 50)

        self.output_flow = PortItem("FLOW", "OUT", self, self)
        self.output_flow.setPos(self.width, 50)

        self.ports = [self.input_data, self.output_data, self.input_flow, self.output_flow]

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Emit signal when node is double-clicked."""
        self.nodeDoubleClicked.emit(self.fqnn)