from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import Terminal256Formatter
from pygments.formatters import HtmlFormatter
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
from pygments.styles import get_style_by_name
import os

class PygmentsSyntaxHighlighter(QTextEdit):
    def __init__(self, language="python", parent=None):
        super().__init__(parent)
        self.language = language
        self.setPlaceholderText("Start typing your code here...")
        self._setup_highlighter()

    def _setup_highlighter(self):
        # Set font to Fira Code (like VS Code)
        #self.setFont(QFont("Fira Code", 14))
        self.setReadOnly(False)

    def highlight_text(self, text):
        """Apply Pygments syntax highlighting to text"""
        try:
            # Determine lexer based on language
            lexer = get_lexer_by_name(self.language)

            # Use HTML formatter to render styled HTML
            formatter = HtmlFormatter(style="monokai", linenums=False)

            # Highlight the text and return HTML
            html = highlight(text, lexer, formatter)
            self.setHtml(html)
        except Exception as e:
            print(f"Error highlighting: {e}")
            self.setHtml(f"<p style='color:red;'>Error highlighting: {e}</p>")
