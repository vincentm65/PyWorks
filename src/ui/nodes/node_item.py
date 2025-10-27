import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsItem, QStyle
from PyQt6.QtCore import QRectF, QMimeData, QPointF
from PyQt6.QtGui import QPainter, QColor, QDrag, QPen, QBrush

from ui.nodes.port import PortItem

class NodeItem(QGraphicsItem):
    def __init__(self, function_name, x, y, parent=None):
        super().__init__(parent)
        # Node properties
        self.width = 140
        self.height = 80
        self.title = function_name
        self.add_ports()

        # Center the node at the given position
        self.setPos(x - self.width / 2, y - self.height / 2)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
    
    # Define the bounding rect
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
    
    # Paint the node
    def paint(self, painter, option, widget):
        radius = 10

        if option.state & QStyle.StateFlag.State_Selected:
            border_pen = QPen(QColor("#4285F4"), 1.5)
        else: 
            border_pen= QPen(QColor("#888"), 1.5)

        painter.setBrush(QColor("#444"))
        painter.setPen(border_pen)
        painter.drawRoundedRect(0, 0, self.width, self.height, radius, radius)
        painter.setPen(QColor("#fff"))
        painter.drawText(10, 20, self.title)
        
    def get_status_color(self):
        colors = {
            "idle": "#444",
            "running": "#4a4",
            "error": "#a44"
        }
        return colors.get(getattr(self, '_status', 'idle'), "#444")
    
    # Check if position changed to re-snap to grid
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            scene_pos_x = round(value.x() / 20) * 20
            scene_pos_y = round(value.y() / 20) * 20
            new_pos = QPointF(scene_pos_x, scene_pos_y)

            if self.scene() and hasattr(self.scene(), 'connections'):
                for connections in self.scene().connections:
                    if connections.source_port in self.ports or connections.target_port in self.ports:
                        connections.update_path()

            return new_pos

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
