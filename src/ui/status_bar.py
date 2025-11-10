from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import Qt

class StatusBarWidget(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
            # Create labels
            self.status_label = QLabel("🟢 Ready")
            self.project_label = QLabel("No project")
            self.canvas_stats_label = QLabel("0 nodes, 0 connections")
            self.zoom_label = QLabel("Zoom: 100%")
            self.coords_label = QLabel("Pos: (0, 0)")
            self.selection_label = QLabel("")
            
            # Add to bar (left-aligned)
            self.addWidget(self.status_label)
            self.addWidget(self.project_label)
            self.addWidget(self.canvas_stats_label)

            # Add to bar (right-aligned)
            self.addPermanentWidget(self.zoom_label)
            self.addPermanentWidget(self.coords_label)
            self.addPermanentWidget(self.selection_label)

            # Style all labels
            self._apply_style()

    def _apply_style(self):
        style = "color: #ccc; padding: 2px 5px;"
        for label in [self.status_label, self.project_label,
                        self.canvas_stats_label, self.zoom_label, self.coords_label,
                        self.selection_label]:
            label.setStyleSheet(style)

    def update_project(self, project_name):
          if project_name:
              self.project_label.setText(f"📁 {project_name}")
          else:
              self.project_label.setText("No project")

    def update_canvas_stats(self, scene):
        from ui.nodes.node_item import NodeItem
        # Count only NodeItem instances (ignore ports, connections, etc)
        node_count = sum(1 for item in scene.items()
                        if isinstance(item, NodeItem))
        connection_count = len(scene.connections)

        text = f"{node_count} nodes, {connection_count} connections"
        self.canvas_stats_label.setText(text)

    def update_zoom(self, scale):
        if scale <= 0:  # Prevent division errors
            return

        percentage = round(scale * 100)
        self.zoom_label.setText(f"Zoom: {percentage}%")

    def update_coordinates(self, canvas_view):
        point = canvas_view.viewport().rect().center()
        
        x = round(canvas_view.mapToScene(point).x(), 2)
        y = round(canvas_view.mapToScene(point).y(), 2)

        self.coords_label.setText(f"Pos: ({x}, {y})")


    def update_selection(self, scene):
        from ui.nodes.node_item import NodeItem

        selected = sum(1 for item in scene.selectedItems()
                        if isinstance(item, NodeItem))

        if selected > 0:
            plural = "node" if selected == 1 else "nodes"
            self.selection_label.setText(f"Selected: {selected} {plural}")
        else:
            self.selection_label.setText("")

    def show_temporary_message(self, text, timeout_ms=2000):
        self.showMessage(text, timeout_ms)

    def set_status(self, text):
        self.status_label.setText(text)

    def reset_to_defaults(self):
        self.status_label.setText("🟢 Ready")
        self.project_label.setText("No project")
        self.canvas_stats_label.setText("0 nodes, 0 connections")
        self.zoom_label.setText("Zoom: 100%")
        self.selection_label.setText("")