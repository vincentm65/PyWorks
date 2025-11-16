from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLineEdit, QApplication
from PyQt6.QtCore import pyqtSignal, Qt

class ConsoleWidget(QWidget):
    input_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setStyleSheet("background-color: #111; color: #fff; font-family: monospace;")
        
        self.input_widget = QLineEdit()
        self.input_widget.setPlaceholderText("Enter input and press Enter...")
        self.input_widget.hide()
        self.input_widget.returnPressed.connect(self.on_input_submitted)

        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.addWidget(self.output_view)
        layout.addWidget(self.input_widget)
        self.setLayout(layout)

        self.write("Application started...")

    def write(self, message):
        self.output_view.append(message)
        QApplication.processEvents()
        self.output_view.verticalScrollBar().setValue(self.output_view.verticalScrollBar().maximum())

    def on_input_submitted(self):
        text = self.input_widget.text()
        self.input_submitted.emit(text + '\n')
        self.write(f"> {text}")
        self.input_widget.clear()
        self.input_widget.hide()

    def request_input(self, prompt):
        self.write(prompt)
        self.input_widget.show()
        self.input_widget.setFocus()