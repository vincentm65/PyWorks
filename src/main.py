import sys
import shutil
from pathlib import Path
import json

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QShortcut, QKeySequence
from PyQt6.QtWidgets import (QDockWidget, QApplication, QMainWindow, QToolBar,
                             QFileDialog, QInputDialog)

from ui.node_list import NodeListWidget
from ui.canvas import CanvasGraphicsView
from ui.editor import EditorWidget
from ui.console import ConsoleWidget
from ui.dialogs.welcome_dialog import WelcomeDialog
from ui.status_bar import StatusBarWidget
from utils.project_manager import create_project, validate_project, get_project_name, initialize_project_venv
from utils.layout_manager import LayoutManager
from core.node_registry import NodeRegistry
from core.venv_manager import VenvManager
from core.package_installer import PackageInstallThread
from core.executor import WorkflowExecutor

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
        self.node_registry = NodeRegistry()

        self.venv_manager = None
        self.install_thread = None
        self.executor = None

        # Connect canvas node double-click signal to editor
        self.canvas.scene.nodeDoubleClicked.connect(self._on_node_double_clicked)

        # Connect zoom and selection signals
        self.canvas.zoom_changed.connect(self.status_bar.update_zoom)
        self.canvas.scene.selectionChanged.connect(
            lambda: self.status_bar.update_selection(self.canvas.scene)
        )

        self.canvas.view_changed.connect(
            lambda: self.status_bar.update_coordinates(self.canvas)
        )

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

        self.reload_action = QAction("Reload Script", self)
        self.reload_action.triggered.connect(self.reload_script)
        toolbar.addAction(self.reload_action)


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

        tools_menu = self.menuBar().addMenu("Tools")
        self.install_deps_action = QAction("Install Dependencies", self)
        self.install_deps_action.triggered.connect(self.install_dependencies)
        self.install_deps_action.setEnabled(False)
        tools_menu.addAction(self.install_deps_action)

    def _create_widgets(self):
        self.canvas = CanvasGraphicsView()
        self.setCentralWidget(self.canvas)

        self.editor = EditorWidget()
        self.console = ConsoleWidget()
        self.node_list_widget = NodeListWidget() 
        

        for widget, title, area in [
            (self.node_list_widget, "Node List", Qt.DockWidgetArea.LeftDockWidgetArea),
            (self.editor, "Editor", Qt.DockWidgetArea.RightDockWidgetArea),
            (self.console, "Console", Qt.DockWidgetArea.BottomDockWidgetArea),
        ]:
            dock = QDockWidget(title, self)
            dock.setWidget(widget)
            self.addDockWidget(area, dock)

        self.status_bar = StatusBarWidget(self)
        self.setStatusBar(self.status_bar)

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
            initialize_project_venv(project_path)
            self.venv_manager = VenvManager(project_path)
            print(f"New project created at: {project_path}")
        except FileExistsError as e:
            print(str(e))

    def open_file(self):
        project_path = QFileDialog.getExistingDirectory(self, "Open Folder")

        if not project_path or not validate_project(Path(project_path)):
            print("Invalid PyWorks project folder.")
            return

        self.canvas.scene.clear()
        self.canvas.scene.connections = []
        self.set_current_project_path(project_path)

        initialize_project_venv(project_path)
        self.venv_manager = VenvManager(project_path)

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
            shutil.copytree(self.current_project_path, new_project_path)
            self.set_current_project_path(new_project_path)
            print(f"Project saved as: {new_project_path}")
        except FileExistsError as e:
            print(str(e))

    def save(self):
        if not self.current_project_path:
            print("No project open to save.")
            return

        if self.editor.save():
            self.reload_script()

        layout_path = self.current_project_path / ".layout.json"
        self.layout_manager.save_layout(
            self.canvas.scene,
            str(layout_path)
        )
        print(f"Layout saved to {layout_path}")

        self.setWindowTitle(f"PyWorks - {self.project_name}")
        self.status_bar.show_temporary_message("✓ Project saved", 2000)
        print("Project Saved")
        

    def set_current_project_path(self, project_path):
        self.current_project_path = Path(project_path)
        self.project_name = get_project_name(self.current_project_path)

        self.setWindowTitle(f"PyWorks - {self.project_name}")
        self.reload_script()

        layout_path = self.current_project_path / ".layout.json"
        if layout_path.exists():
            self.layout_manager.load_layout(self.canvas.scene, str(layout_path))
            self.run_action.setEnabled(True)
            self.pause_action.setEnabled(True)
            self.stop_action.setEnabled(True)
            self.install_deps_action.setEnabled(True)

            print(f"Loaded project from {layout_path}")

        self.status_bar.update_project(self.project_name)
        self.status_bar.update_canvas_stats(self.canvas.scene)

    def close_current_project(self):
        self.canvas.scene.clear()
        self.canvas.scene.connections = []
        self.editor.clear()

        self.current_project_path = None
        self.project_name = None
        self.venv_manager = None
        self.setWindowTitle("PyWorks")

        self.run_action.setEnabled(False)
        self.pause_action.setEnabled(False)
        self.stop_action.setEnabled(False)
        self.install_deps_action.setEnabled(False)

        self.status_bar.reset_to_defaults()
        print("Project closed")

    def install_dependencies(self):
        if not self.venv_manager:
            print("No virtual environment found.")
            return
        requirements_file = self.current_project_path / "requirements.txt"

        if not requirements_file.exists() or not requirements_file.read_text().strip():
            print("No dependencies to install.")
            return
        
        pip_path = self.venv_manager.get_pip_path()
        self.install_thread = PackageInstallThread(pip_path, str(requirements_file))

        self.install_thread.output_signal.connect(self.console.write) 
        self.install_thread.finished_signal.connect(self._on_install_finished)

        self.console.write("=== Installing dependencies ===") 
        self.install_thread.start()


    def _on_install_finished(self, success):
        if success:
            self.console.write("=== Installation complete  ===")
            self.status_bar.show_temporary_message("Dependencies installed", 3000)
        else:
            self.console.write("=== Installation failed  ===")
            self.status_bar.show_temporary_message("Installation failed", 3000)
    
    def prompt_new_project_on_launch(self):
        dialog = WelcomeDialog(self)
        dialog.exec()
        if dialog.selected_action == "new":
            self.new_file()
        elif dialog.selected_action == "open":
            self.open_file()

    def reload_script(self):
        if not self.current_project_path:
            print("No project open.")
            return

        try:
            if not self.venv_manager:
                python_path = None
            else:
                python_path = self.venv_manager.get_python_path()
            # Discover nodes from the project
            self.node_registry.discover(Path(self.current_project_path), python_path)

            # Update the Node List UI
            if self.node_list_widget:
                self.node_list_widget.clear()  # Clear existing tree
                self.node_list_widget.populate_from_registry(self.node_registry)

            print(f"✓ Reloaded {len(self.node_registry.nodes)} nodes")
        except Exception as e:
            print(f"Error reloading script: {e}")

    def _on_node_double_clicked(self, fqnn):
        """Handle node double-click by showing function in editor."""
        metadata = self.node_registry.get_metadata(fqnn)
        if metadata:
            self.editor.show_function_context(metadata)
            print(f"Showing function: {fqnn}")
        else:
            print(f"Error: Metadata not found for {fqnn}")

    def run(self):
        if not self.current_project_path:
            return
        self.run_workflow()

    def run_workflow(self):
        # Load Json
        self.layout_path = self.current_project_path / ".layout.json"
        with open(self.layout_path, 'r', encoding='utf-8') as f:
            self.layout_data = json.load(f)
        
        # Validate venv
        if self.venv_manager is None:
            return

        # Create executor
        self.executor = WorkflowExecutor(self.current_project_path, self.layout_data, self.venv_manager, self.node_registry)

        # Create signals
        self.executor.output_signal.connect(self.console.write)
        self.executor.status_signal.connect(self.status_bar.show_temporary_message)
        self.executor.finished_signal.connect(self._on_execution_finished)

        self.executor.start()

    def _on_execution_finished(self, success, message):
        self.console.write(message + "\n")
        self.executor = None
        self.status_bar.show_temporary_message(message)



    # Placeholder actions - to be implemented
    def undo(self):
        print("Undo")

    def redo(self):
        print("Redo")

    def pause(self):
        print("Pause")

    def stop(self):
        print("Stop")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
