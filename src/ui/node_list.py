import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QListWidget

class NodeListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setDragEnabled(True)
        self.addItems(["Node1", "Node2", "Node3"])