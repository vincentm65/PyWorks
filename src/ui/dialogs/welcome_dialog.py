 
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to PyWorks")
        self.setModal(True)  # Block interaction with main window
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)

        self.selected_action = None  # Will be "new" or "open" or None

        self._create_ui()
        self._center_ui()

    def _center_ui(self):
        screen = self.screen().geometry()

        dialog_size = self.geometry()
        x = (screen.width() - dialog_size.width()) // 2
        y = (screen.height() - dialog_size.height()) // 2
        self.move(x, y)

    def _create_ui(self):
        # Build the dialog UI
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Welcome title
        title = QLabel("Welcome to PyWorks")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Visual Python Workflow Editor")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)

        # Add some spacing
        layout.addSpacing(20)

        # Instructions
        instructions = QLabel("Get started by creating a new project or opening an existing one:")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        layout.addSpacing(10)

        # Buttons container
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        # New Project Button
        self.new_btn = QPushButton("Create New Project")
        self.new_btn.setMinimumHeight(60)
        self.new_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid #4285F4;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #5294ff;
            }
            QPushButton:pressed {
                background-color: #3275e4;
            }
        """)
        self.new_btn.clicked.connect(self._on_new_project)
        button_layout.addWidget(self.new_btn)

        # Open Project Button
        self.open_btn = QPushButton("Open Existing Project")
        self.open_btn.setMinimumHeight(60)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: 2px solid #34A853;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #44b863;
            }
            QPushButton:pressed {
                background-color: #2a9843;
            }
        """)
        self.open_btn.clicked.connect(self._on_open_project)
        button_layout.addWidget(self.open_btn)

        layout.addLayout(button_layout)

        # Add stretch to push everything to the top
        layout.addStretch()

        # Cancel button (smaller, at bottom)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMaximumWidth(100)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        cancel_layout = QHBoxLayout()
        cancel_layout.addStretch()
        cancel_layout.addWidget(cancel_btn)
        layout.addLayout(cancel_layout)

        self.setLayout(layout)

    def _on_new_project(self):
        self.selected_action = "new"
        self.accept()

    def _on_open_project(self):
        self.selected_action = "open"
        self.accept()