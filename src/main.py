import sys
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QGraphicsView, QToolBar, QFileDialog, QInputDialog
from PyQt6.QtGui import QAction 
from pathlib import Path

from ui.node_list import NodeListWidget
from ui.canvas import CanvasGraphicsView
from ui.editor import EditorWidget
from utils.layout_manager import LayoutManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyWorks")
        self.setGeometry(500, 300, 1200, 800)

        self._create_menubar()
        self._create_toolbar()
        self._create_widgets()

        self.layout_manager = LayoutManager()


    def _create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        for name, slots in [("Run", self.run), ("Pause", self.pause), ("Stop", self.stop)]:
            action = QAction(name, self)
            action.triggered.connect(slots)
            toolbar.addAction(action)

    def _create_menubar(self):
        file_menu = self.menuBar().addMenu("File")
        for name, slots in [
            ("New", self.new_file),
            ("Open", self.open_file),
            ("Save", self.save),
            ("Save As", self.save_as)
        ]:
            file_menu.addAction(name, slots)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        edit_menu = self.menuBar().addMenu("Edit")
        for name, slots in [
            ("Undo", self.undo),
            ("Redo", self.redo)
        ]:
            edit_menu.addAction(name, slots)
        
 
    def _create_widgets(self):
        # Central Widget Layout
        self.canvas = CanvasGraphicsView()
        self.setCentralWidget(self.canvas)

        # Dockable Widgets
        for widget, title, area in [
            (NodeListWidget(), "Node List", Qt.DockWidgetArea.LeftDockWidgetArea),
            (EditorWidget(), "Editor", Qt.DockWidgetArea.RightDockWidgetArea),
            (EditorWidget(), "Console", Qt.DockWidgetArea.BottomDockWidgetArea),
        ]:
            dock = QDockWidget(title, self)
            dock.setWidget(widget)
            self.addDockWidget(area, dock)


    # Action Slots
    def new_file(self): print("New file")
    def open_file(self):
        # 1. Open File Dialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Layout", "", "JSON Files (*.json)")

        # 2. Load user selected layout to the canvas
        if file_path:
            # Clear the canvas first
            self.canvas.scene.clear()
            self.canvas.scene.connections = []
            success = self.layout_manager.load_layout(self.canvas.scene, file_path)
            if success:
                print("Layout Loaded")
            else:
                print("Failed to load layout")

    def save(self):
        name, ok = QInputDialog.getText(self, "Save Layout", "Enter layout name:")
        
        if not ok or not name:
            return
        
        layouts_dir = Path("workspace/layouts")
        layouts_dir.mkdir(parents=True, exist_ok=True)
        file_path = layouts_dir / f"{name}.json"

        success = self.layout_manager.save_layout(
            self.canvas.scene,
            name,
            str(file_path)
        )

        if success:
            print("Layout Saved")
        else:
            print("Failed to save layout")
        
    def save_as(self): print("Save As")
    def undo(self): print("Undo")
    def redo(self): print("Redo")
    def run(self): print("Run")
    def pause(self): print("Pause")
    def stop(self): print("Stop")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 

if __name__ == "__main__":
    main()



