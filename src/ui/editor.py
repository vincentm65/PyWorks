import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit


class EditorWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Start typing your code here...")