import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag

class NodeListWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            fqnn = item.data(0, Qt.ItemDataRole.UserRole)

            if not fqnn:
                return
                
            drag = QDrag(self)
            mimeData = QMimeData()
            mimeData.setText(fqnn)
            drag.setMimeData(mimeData)
            drag.exec(supportedActions)

    def populate_from_registry(self, node_registry):
        category_group = {}
        for fqnn, metadata in node_registry.nodes.items():
            cat = metadata.category
            if cat not in category_group:
                category_group[cat] = []
            category_group[cat].append((fqnn, metadata))

        # Build the tree
        for category, nodes in category_group.items():
            category_item = QTreeWidgetItem([category])
            self.addTopLevelItem(category_item)

            for fqnn, metadata in nodes:
                function_item = QTreeWidgetItem([metadata.function_name])
                function_item.setData(0, Qt.ItemDataRole.UserRole, fqnn)
                category_item.addChild(function_item)

    
            


