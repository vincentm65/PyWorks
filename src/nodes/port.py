import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsItem, QStyle
from PyQt6.QtCore import QRectF, QMimeData, QPointF
from PyQt6.QtGui import QPainter, QColor, QDrag, QPen, QBrush

class PortItem(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.port_type = "DATA"
        self.port_direction = "IN"
        self.port_color = QPen("#111")
        self.parent_node = None
        self.position = QPointF

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
    
    def boundingRect(self):
        radius = 4
        return QRectF(-radius, -radius, radius*2, radius*2)
    
    def paint(self, painter, option, widget):
        radius = 4
        painter.drawEllipse()
        
        if self.port_type == "DATA":
            self.port_color = QPen("#555")
        elif self.port_type == "FLOW":
            self.port_color = QPen("#555")

    def get_center_pos():
        # dont know what goes here
        pass

    def can_connect_to():
        pass


    
    