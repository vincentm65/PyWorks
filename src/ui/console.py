import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt6.QtGui import QPainter


class ConsoleTextView(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("background-color: #111; color: #0f0; font-family: monospace;")
        self.console.write("Application started...")

    def write(self, message):
        self.append(message)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())