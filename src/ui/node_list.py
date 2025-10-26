import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidget
from PyQt6.QtCore import QMimeData
from PyQt6.QtGui import QDrag

class NodeListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setDragEnabled(True)
        self.addItems(["Node1", "Node2", "Node3"])

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            drag = QDrag(self)
            mimeData = QMimeData()
            mimeData.setText(item.text())
            drag.setMimeData(mimeData)
            drag.exec(supportedActions)
