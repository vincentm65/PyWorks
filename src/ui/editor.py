import sys
from core import ast_utils
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt6.QtGui import QFont, QTextDocument, QTextCursor, QPainter, QPen, QColor, QFontMetrics
from PyQt6.QtCore import Qt, QRect, QPoint

import pygments
import pygments.formatters.html
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter
from pygments import highlight
import re


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

    def _highlight_code(self, code: str) -> str:
        """
        Highlight Python code using Pygments.
        Returns a string with syntax highlighting (plain text with color tokens).
        """
        try:
            # Use Python lexer
            highlighted = highlight(
                code,
                PythonLexer(),
                pygments.formatters.HtmlFormatter(
                    style="monokai",       # use a dark style
                    noclasses=True,        # inline styles instead of CSS classes
                    linenums=False,
                    full=False,
                    prestyles=(
                        "background: transparent; "
                        "color: #f8f8f2; "
                        "font-family: Consolas, 'Fira Code', 'JetBrains Mono', monospace; "
                        "font-size: 14pt;"
                    )
                )
            )
            return highlighted  # This will render as HTML

        except Exception as e:
            print(f"Error highlighting code: {e}")
            return code  # fallback

    def _apply_highlighting(self, code: str):
        # Create a QTextDocument and set HTML content
        doc = QTextDocument()
        doc.setHtml(code)
        self.setDocument(doc)

    def show_function_context(self, metadata):
        try:
            # Temp disconnect to avoid false dirty trigger
            self.textChanged.disconnect(self._on_text_changed)

            code = ast_utils.extract_function_with_imports(metadata.file_path, metadata.function_name)

            # Highlight the code using Pygments HTML formatter
            highlighted_html = self._highlight_code(code)

            # Apply the highlighted HTML to the editor
            self._apply_highlighting(highlighted_html)

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
