
from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtCore import QRectF, QPointF
from PyQt6.QtGui import QColor, QPen, QBrush, QPolygonF

class PortItem(QGraphicsItem):
    def __init__(self, port_type, port_direction, parent_node, parent=None):
        super().__init__(parent)
        self.port_type = port_type
        self.port_direction = port_direction
        self.parent_node = parent_node

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
    
    def boundingRect(self):
        radius = 5
        return QRectF(-radius, -radius, radius*2, radius*2)
    
    def paint(self, painter, option, widget):
        radius = 5
        
        if self.port_type == "DATA":
            self.port_color = QPen(QColor("#2196F3"))
            painter.setPen(self.port_color)
            painter.setBrush(QBrush(self.port_color.color()))
            
        elif self.port_type == "FLOW":
            self.port_color = QPen(QColor("#4CAF50"))
            painter.setPen(self.port_color)
            painter.setBrush(QBrush(self.port_color.color()))

        if self.port_direction == "OUT":
            triangle = QPolygonF([
                QPointF(radius, 0),
                QPointF(-radius, -radius), 
                QPointF(-radius, radius)
            ])

            painter.drawPolygon(triangle)
        elif self.port_direction == "IN":
            painter.drawEllipse(self.boundingRect())

        

    def get_center_pos(self):
        radius = 5
        self.center_pos = self.scenePos()
        return self.center_pos

    def can_connect_to(self, other_port):
        # Prevent connecting to self
        if self is other_port:
            return False
        
        # Must have opposite directions
        if self.port_direction == other_port.port_direction:
            return False

        # Must have same type
        if self.port_type != other_port.port_type:
            return False

        return True


    
    