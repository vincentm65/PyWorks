import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsItem, QStyle
from PyQt6.QtCore import QRectF, QMimeData, QPointF
from PyQt6.QtGui import QPainter, QColor, QDrag, QPen, QBrush

class NodeItem(QGraphicsItem):
    def __init__(self, function_name, x, y, parent=None):
        super().__init__(parent)
        # Node properties
        self.width = 180
        self.height = 100
        self.title = function_name

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
            border_pen = QPen(QColor("#4285F4"), 2)
        else: 
            border_pen= QPen(QColor("#444"))

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
            return QPointF(scene_pos_x, scene_pos_y)
        return super().itemChange(change, value)

        