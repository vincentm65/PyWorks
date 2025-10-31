from PyQt6.QtWidgets import QGraphicsPathItem, QStyle
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPen, QColor, QPainterPath

from ui.nodes.port import PortItem
from ui.nodes.node_item import NodeItem

class ConnectionBridge(QGraphicsPathItem):
    def __init__(self, source_port, target_port, parent = None):
        super().__init__(parent)

        # Normalize ports
        if source_port.port_direction == "IN":
          source_port, target_port = target_port, source_port

        self.source_port = source_port
        self.target_port = target_port
        self.setAcceptHoverEvents(True)
        self.is_hovered = False
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable, True)
        
        if source_port.port_type == "FLOW":
            pen = QPen(QColor(110, 110, 110), 2)
        elif source_port.port_type == "DATA":
            pen = QPen(QColor(138, 43, 226), 2)
       
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

        self.setZValue(-1)

        self.update_path()

    def paint(self, painter, option, widget):
        is_selected = option.state & QStyle.StateFlag.State_Selected
        if self.is_hovered or is_selected:
            if self.source_port.port_type == "FLOW":
                glow_color = QColor(150, 150, 150, 100)
            else:
                glow_color = QColor(180, 100, 255, 120)
            if is_selected:
                glow_color = QColor(255, 255, 255, 60)

            glow_pen = QPen(glow_color, 6)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            glow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

            painter.setPen(glow_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.path())
            
        option.state &= ~QStyle.StateFlag.State_Selected

        super().paint(painter, option, widget)

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

        radius = 10
        base_mid_x = (start.x() + end.x()) / 2
        # Otherwise, use curved orthogonal routing, based on node position and port type
        if self.source_port.port_type == "FLOW":
            if self.source_port.scenePos().y() < self.target_port.scenePos().y():
                mid_x = base_mid_x - 10
            else:
                mid_x = base_mid_x + 10
        elif self.source_port.port_type == "DATA":
            if self.source_port.scenePos().y() < self.target_port.scenePos().y():
                mid_x = base_mid_x + 10
            else:
                mid_x = base_mid_x - 10

        going_right = end.x() > start.x()
        going_down = end.y() > start.y()

        h_radius = radius if going_right else -radius
        v_radius = radius if going_down else -radius

        path.lineTo(mid_x - h_radius, start.y())
        path.quadTo(QPointF(mid_x, start.y()), QPointF(mid_x, start.y() + v_radius))
        path.lineTo(mid_x, end.y() - v_radius)
        path.quadTo(QPointF(mid_x, end.y()), QPointF(mid_x + h_radius, end.y()))
        path.lineTo(end)

        print(f"Port type: {self.source_port.port_type}")
        print(f"Source Y: {self.source_port.scenePos().y()}, Target Y: {self.target_port.scenePos().y()}")
        print(f"Going down? {self.source_port.scenePos().y() < self.target_port.scenePos().y()}")
        print(f"Calculated mid_x: {mid_x}")
        print("---")

        return path
    
    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)