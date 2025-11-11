import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QInputDialog, QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox
from PyQt6.QtCore import Qt, QMimeData, QPoint
from PyQt6.QtGui import QDrag

STARTER_TEXT = '''
import sys

def node(func):
    """Decorator to mark a function as a workflow node."""
    func._is_workflow_node = True
    return func

@node
def example(inputs, global_state):
    message = "Hello World!"
    return {"result": message}
'''

class NodeListWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.setDragEnabled(True)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

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
            self.project_path = metadata.file_path.parent
            print(self.project_path)

        # Build the tree
        for category, nodes in category_group.items():
            category_item = QTreeWidgetItem([category])
            self.addTopLevelItem(category_item)

            for fqnn, metadata in nodes:
                function_item = QTreeWidgetItem([metadata.function_name])
                function_item.setData(0, Qt.ItemDataRole.UserRole, fqnn)
                category_item.addChild(function_item)

    def open_context_menu(self, position: QPoint):
        menu = QMenu(self)
        item = self.itemAt(position)

        if item is None:
            # --- Empty space ---
            actions = [
                ("Refresh Tree", self.handle_empty_space_action),
                ("Add New Category", self.handle_add_category),
            ]

        elif item.parent() is None:
            # --- Top-level category ---
            name = item.text(0)
            actions = [
                (f"Expand '{name}'", lambda: item.setExpanded(True)),
                (f"Collapse '{name}'", lambda: item.setExpanded(False)),
                ("Add New Node", lambda: self.handle_add_node(name)),
                (f"Delete Category '{name}'", lambda: self.handle_delete_category(name)),
            ]

        else:
            # --- Child node ---
            name = item.text(0)
            actions = [
                (f"Delete '{name}'", lambda: self.handle_delete_item(name)),
            ]

        # Add main actions to menu
        for text, func in actions:
            menu.addAction(text).triggered.connect(func)

        # Always show global settings
        menu.addSeparator()
        menu.addAction("Global Settings").triggered.connect(self.handle_global_action)

        menu.exec(self.viewport().mapToGlobal(position))


     # --- Handlers ---
    def handle_empty_space_action(self):
        self.main_window.reload_script()

    def handle_add_category(self):
        # Ask user for name of new file
        name, ok = QInputDialog.getText(self, "New file", "Enter name for new file:")
        if not ok or not name.strip():
            return
        # Build path to nodes directory
        nodes_dir = self.project_path
        nodes_dir.mkdir(parents=True, exist_ok=True)

        file_path = nodes_dir / f"{name}.py"

        if file_path.exists():
            QMessageBox.warning(self, "File Exists", f"{file_path.name} already exists.")
            return

        # Generate the python file:
        file_path.write_text(STARTER_TEXT)

        QMessageBox.information(self, "Node Created", f"Created: {file_path}")
        self.handle_empty_space_action()

    def handle_add_node(self, name):
        # Get name for function:
        func_name, ok = QInputDialog.getText(self, "New Node", "Enter name for new node:")
        if not ok or not func_name.strip():
            return

        # Build path to nodes directory
        nodes_dir = self.project_path
        nodes_dir.mkdir(parents=True, exist_ok=True)

        file_path = nodes_dir / f"{name}.py"
        print(f"The python file: {file_path}")
        if file_path.exists():
            with file_path.open("a", encoding="utf-8") as f:
                f.write("\n# Added new function\n")
                f.write("@node\n")
                f.write("def {func_name}(inputs, global_state):\n")
                f.write("    message = 'New feature added!'\n")
                f.write("    return {'result': message}\n")

        else:
            print("File not found.")

    def handle_delete_category(self, name):
        nodes_dir = self.project_path
        nodes_dir.mkdir(parents=True, exist_ok=True)

        file_path = nodes_dir / f"{name}.py"

        if file_path.exists():
            file_path.unlink()  # deletes the file
            print(f"Deleted {file_path}")
            self.handle_empty_space_action()
        else:
            print("File not found.")

    def handle_delete_item(self, item_text):
        print(f"Deleted item: {item_text}")

    def handle_global_action(self):
        print("Global action triggered")
            


