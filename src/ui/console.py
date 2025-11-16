from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QApplication
from PyQt6.QtCore import pyqtSignal


class ConsoleWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("background-color: #111; color: #fff; font-family: monospace;")
        self.write("Application started...")

    def write(self, message):
        self.append(message)
        QApplication.processEvents()
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())