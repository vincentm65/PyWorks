
from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtCore import QRectF, QPointF
from PyQt6.QtGui import QColor, QPen, QBrush, QPolygonF

class PortItem(QGraphicsItem):
    def __init__(self, port_type, port_direction, parent_node, parent=None):
        super().__init__(parent)
        self.port_type = port_type
        self.port_direction = port_direction
        self.parent_node = parent_node
        self._node_key = None  # Will store the parent node's key

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
    
    def boundingRect(self):
        radius = 6
        return QRectF(-radius, -radius, radius*2, radius*2)
    
    def paint(self, painter, option, widget):
        radius = 6
        
        if self.port_type == "DATA":
            self.port_color = QPen(QColor("#2196F3"))
            border_color = QColor("#1565C0")
        elif self.port_type == "FLOW":
            self.port_color = QPen(QColor("#4CAF50"))
            border_color = QColor("#2E7D32")
            
        painter.setPen(QPen(border_color, 1.5))
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
        """Get the center position of the port in scene coordinates"""
        self.center_pos = self.scenePos()
        return self.center_pos
        
    def get_node_key(self):
        """Get the key of the parent node"""
        if self._node_key is None and hasattr(self.parent_node, 'id'):
            self._node_key = self.parent_node.id
        return self._node_key
        
    def can_connect_to(self, other_port):
        """Check if this port can connect to another port"""
        # Must have opposite directions
        if self.port_direction == other_port.port_direction:
            return False

        # Must have same type
        if self.port_type != other_port.port_type:
            return False

        # Must be connecting to a different node
        if self.get_node_key() == other_port.get_node_key():
            return False
            
        return True


    
    