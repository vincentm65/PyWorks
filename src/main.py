import sys
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QGraphicsView, QToolBar
from PyQt6.QtGui import QAction 

from ui.node_list import NodeListWidget
from ui.canvas import CanvasGraphicsView
from ui.editor import EditorWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyWorks")
        self.setGeometry(500, 300, 1200, 800)

        # Create a menubar
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction("New", self.new_file)
        file_menu.addAction("Open", self.open_file)
        file_menu.addAction("Save", self.save)
        file_menu.addAction("Save As", self.save_as)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction("Undo", self.undo)
        edit_menu.addAction("Redo", self.redo)
        
        # Create a toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        for name, slots in [("Run", self.run), ("Pause", self.pause), ("Stop", self.stop)]:
            action = QAction(name, self)
            action.triggered.connect(slots)
            toolbar.addAction(action)

        # Central Widget Layout
        self.canvas = CanvasGraphicsView()
        self.setCentralWidget(self.canvas)

        # Add custom docked widgets
        self.node_list = NodeListWidget()
        node_dock = QDockWidget("Node List", self)
        node_dock.setWidget(self.node_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, node_dock)

        self.editor = EditorWidget()
        editor_dock = QDockWidget("Editor", self)
        editor_dock.setWidget(self.editor)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, editor_dock)

        self.console = EditorWidget()
        console_dock = QDockWidget("Console", self)
        console_dock.setWidget(self.console)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, console_dock)
        
 
    def new_file(self): 
        print("New file")
    def open_file(self): 
        print("Open file")
    def save(self):
        print("Save")
    def save_as(self): 
        print("Save As")
    def undo(self): 
        print("Undo")
    def redo(self): 
        print("Redo")

    def run(self): 
        print("Run")
    def pause(self): 
        print("Pause")
    def stop(self): 
        print("Stop")

    

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 

if __name__ == "__main__":
    main()



