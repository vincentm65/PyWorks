import sys
from core import ast_utils
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit


class EditorWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Start typing your code here...")

    def show_function_context(self, metadata):
        try:
            code = ast_utils.extract_function_with_imports(metadata.file_path, metadata.function_name)
            self.setPlainText(code)
            self.setReadOnly(True)
        except Exception as e:
            self.setPlainText(f"Error loading function: {e}")
    
    def clear(self):
        self.setPlainText("")
        self.setReadOnly(False)

    

