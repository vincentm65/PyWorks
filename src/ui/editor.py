import sys
from core import ast_utils
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit


class EditorWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Start typing your code here...")

        # File tracking
        self.current_file_path = None
        self.current_metadata = None
        self.is_dirty = False

        # Connected to text change signal
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        if self.current_file_path and not self.is_dirty:
            self.is_dirty = True

    def show_function_context(self, metadata):
        try:
            # Temp disconnect to avoid false dirty trigger
            self.textChanged.disconnect(self._on_text_changed)

            code = ast_utils.extract_function_with_imports(metadata.file_path, metadata.function_name)
            self.setPlainText(code)

            # Now begin tracking
            self.current_file_path = metadata.file_path
            self.current_metadata = metadata
            self.setReadOnly(False)

            # Reconenct the signal
            self.textChanged.connect(self._on_text_changed)

        except Exception as e:
            self.setPlainText(f"Error loading function: {e}")
            self.current_file_path = None
            self.current_metadata = None

    def save(self):
        if not self.current_file_path:
            print("No file loaded in editor")
            return False

        if not self.is_dirty:
            print("No changes to save")
            return False

        try:
            success = ast_utils.replace_function_in_file(
              self.current_file_path,
              self.current_metadata.function_name,
              self.toPlainText()
            )

            if success:
                self.is_dirty = False
                print(f"✓ Saved changes to {self.current_file_path.name}")
                return True
            else:
                print("Failed to save function")
                return False
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def clear(self):
        self.setPlainText("")
        self.current_file_path = None
        self.current_metadata = None
        self.is_dirty = False
        self.setReadOnly(False)

    

