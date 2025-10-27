from PyQt6.QtWidgets import QGraphicsPathItem  # Changed import
from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPen, QColor, QPainterPath

from ui.nodes.port import PortItem
from ui.nodes.node_item import NodeItem

class ConnectionBridge(QGraphicsPathItem):
    def __init__(self, source_port, target_port, parent = None):
        super().__init__(parent)
        self.source_port = source_port
        self.target_port = target_port
        
        pen = QPen(QColor("#888"), 2)
        self.setPen(pen)

        self.update_path()

    def update_path(self,):
        path = self.create_orthoganal_path()
        self.setPath(path)
    
    def create_orthoganal_path(self):
        start = self.source_port.get_center_pos()
        end = self.target_port.get_center_pos()

        mid_x = (start.x() + end.x()) / 2

        path = QPainterPath(start)
        path.lineTo(mid_x, start.y())
        path.lineTo(mid_x, end.y())
        path.lineTo(end.x(), end.y())

        return path
