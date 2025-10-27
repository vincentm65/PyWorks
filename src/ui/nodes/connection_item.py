from PyQt6.QtWidgets import QGraphicsPathItem  # Changed import
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPen, QColor, QPainterPath

from ui.nodes.port import PortItem
from ui.nodes.node_item import NodeItem

class ConnectionBridge(QGraphicsPathItem):
    def __init__(self, source_port, target_port, parent = None):
        super().__init__(parent)
        self.source_port = source_port
        self.target_port = target_port
        
        if source_port.port_type == "FLOW":
            pen = QPen(QColor(110, 110, 110), 2)
        elif source_port.port_type == "DATA":
            pen = QPen(QColor(138, 43, 226), 2)
       
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

        self.setZValue(-1)

        self.update_path()

    def update_path(self,):
        path = self.create_orthoganal_path()
        self.setPath(path)
    
    def create_orthoganal_path(self):
        start = self.source_port.get_center_pos()
        end = self.target_port.get_center_pos()

        path = QPainterPath(start)

        # If perfectly horizontal or vertical, draw straight line
        if start.y() == end.y() or start.x() == end.x():
            path.lineTo(end)
            return path

        # Otherwise, use curved orthogonal routing
        mid_x = (start.x() + end.x()) / 2
        radius = 10

        going_right = end.x() > start.x()
        going_down = end.y() > start.y()

        h_radius = radius if going_right else -radius
        v_radius = radius if going_down else -radius

        path.lineTo(mid_x - h_radius, start.y())
        path.quadTo(QPointF(mid_x, start.y()), QPointF(mid_x, start.y() + v_radius))
        path.lineTo(mid_x, end.y() - v_radius)
        path.quadTo(QPointF(mid_x, end.y()), QPointF(mid_x + h_radius, end.y()))
        path.lineTo(end)

        return path