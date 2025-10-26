import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicItem
from PyQt6.QtCore import QRectF, QMimeData
from PyQt6.QtGui import QPainter, QColor, QDrag

class NodeItem(QGraphicItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Node properties
        self.width = 180
        self.height = 100
        self.title = "Node"
    
    # Define the bounding rect
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
    
    # Paint the node
    def paint(self, painter, option, widget):
        radius = 10

        painter.setBrush(QColor("#444"))
        painter.setPen(QColor("#222"))
        painter.drawRoundedRect(0, 0, self.width, self.height)
        painter.setPen(QColor("#fff"))
        painter.drawText(10, 20, self.title)

    def status(self):
        colors = {
            "idle": "#444",
            "running": "#4a4",
            "error": "#a44"
        }
        return colors.get(self.status, "#444")

        