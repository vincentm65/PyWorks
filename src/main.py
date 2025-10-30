import sys
import shutil
from PyQt6.QtWidgets import QDockWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QGraphicsView, QToolBar, QFileDialog, QInputDialog
from PyQt6.QtGui import QAction, QShortcut, QKeySequence
from pathlib import Path
from utils.project_manager import create_project, validate_project, get_project_name

from ui.node_list import NodeListWidget
from ui.canvas import CanvasGraphicsView
from ui.editor import EditorWidget
from ui.console import ConsoleWidget
from ui.welcome_dialog import WelcomeDialog

from utils.layout_manager import LayoutManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyWorks")

        self._create_menubar()
        self._create_toolbar()
        self._create_widgets()

        self.layout_manager = LayoutManager()
        self.current_file = None

        self.project_name = None
        self.current_project_path = None

        # Bind Shortcuts
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_file)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_file)

        QTimer.singleShot(100, self.prompt_new_project_on_launch)


    def _create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        self.run_action = QAction("Run", self)
        self.run_action.triggered.connect(self.run)
        toolbar.addAction(self.run_action)

        self.pause_action = QAction("Pause", self)
        self.pause_action.triggered.connect(self.pause)
        toolbar.addAction(self.pause_action)

        self.stop_action = QAction("Stop", self)
        self.stop_action.triggered.connect(self.stop)
        toolbar.addAction(self.stop_action)


    def _create_menubar(self):
        file_menu = self.menuBar().addMenu("File")
        for name, slots in [
            ("New Project", self.new_file),
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

        self.editor = EditorWidget()
        self.console = ConsoleWidget()

        # Dockable Widgets
        for widget, title, area in [
            (NodeListWidget(), "Node List", Qt.DockWidgetArea.LeftDockWidgetArea),
            (self.editor, "Editor", Qt.DockWidgetArea.RightDockWidgetArea),
            (self.console, "Console", Qt.DockWidgetArea.BottomDockWidgetArea),
        ]:
            dock = QDockWidget(title, self)
            dock.setWidget(widget)
            self.addDockWidget(area, dock)


    # Action Slots
    def new_file(self):
        name, ok = QInputDialog.getText(self, "New Project", "Enter project name:")
        if not ok or not name:
            return

        location = QFileDialog.getExistingDirectory(self, "Select Project Location")
        if not location:
            return

        try:
            project_path = create_project(name, location)
            self.set_current_project_path(project_path)
            print(f"New project created at: {project_path}")
        except FileExistsError as e:
            print(str(e))

    def open_file(self):
        # Open folder
        project_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        
        # Validate its a valid project
        if not project_path or not validate_project(Path(project_path)):
            print("Invalid PyWorks project folder.")
            return
        
        # Load project 
        self.canvas.scene.clear()
        self.canvas.scene.connections = []
        self.set_current_project_path(project_path)

        print(f"Project opened: {project_path}")

    def save_as(self):
        if not self.current_project_path:
            print("No project open to save.")
            return

        self.save()
        
        new_name, ok = QInputDialog.getText(self, "Save Project As", "Enter new project name:")
        if not ok or not new_name:
            return
        
        new_location = QFileDialog.getExistingDirectory(self, "Select New Project Location")
        if not new_location:
            return
        new_project_path = Path(new_location) / new_name
        try:
            # Copy entire folder contents
            shutil.copytree(self.current_project_path, new_project_path)
            self.set_current_project_path(new_project_path)
            print(f"Project saved as: {new_project_path}")
        except FileExistsError as e:
            print(str(e))
        
    def save(self):
        if not self.current_project_path:
            print("No project open to save.")
            return
        
        # Set editor content and save to workflow.py
        editor_content = self.editor.toPlainText()
        workflow_path = self.current_project_path / "workflow.py"
        try:
            with open(workflow_path, 'w', encoding='utf-8') as f:
                f.write(editor_content)
                print(f"Workflow code saved to {workflow_path}")
        except Exception as e:
            print(f"Error saving workflow code: {e}")
        
        # Save layout to .layout.json
        layout_path = self.current_project_path / ".layout.json"

        success = self.layout_manager.save_layout(
            self.canvas.scene,
            str(layout_path)
        )
        if success:
            print(f"Layout saved to {layout_path}")
        else:
            print("Failed to save layout")

        # Set window title
        self.setWindowTitle(f"PyWorks - {self.project_name}")
        print("Project Saved")
        
    def set_current_project_path(self, project_path):
        self.current_project_path = Path(project_path)
        self.project_name = get_project_name(self.current_project_path)

        self.setWindowTitle(f"PyWorks - {self.project_name}")

        workflow_path = self.current_project_path / "workflow.py"
        if workflow_path.exists():
            with open(workflow_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.editor.setPlainText(content)
        else:
            print(f"No workflow.py found in {self.current_project_path}")

        layout_path = self.current_project_path / ".layout.json"
        if layout_path.exists():
            success = self.layout_manager.load_layout(self.canvas.scene, str(layout_path))
            self.run_action.setEnabled(True)
            self.pause_action.setEnabled(True)
            self.stop_action.setEnabled(True)

            print(f"Loaded project from {layout_path}")
    
    def close_currnet_project(self):
        self.canvas.scene.clear()
        self.canvas.scene.connections = []
        self.editor.clear()

        self.current_project_path = None
        self.project_name = None
        self.setWindowTitle("PyWorks")
        
        self.run_action.setEnabled(False)
        self.pause_action.setEnabled(False)
        self.stop_action.setEnabled(False)

        print("Project closed")

    def prompt_new_project_on_launch(self):
        # On launch, prompt user to create or open project
        dialog = WelcomeDialog(self)
        dialog.exec()
        if dialog.selected_action == "new":
            self.new_file()
        elif dialog.selected_action == "open":
            self.open_file()

    # Place holder Action Slots
    def undo(self): print("Undo")
    def redo(self): print("Redo")
    def run(self): print("Run")
    def pause(self): print("Pause")
    def stop(self): print("Stop")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec()) 

if __name__ == "__main__":
    main()



