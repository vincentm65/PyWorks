import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QWidget, QGraphicsView

from ui.node_list import NodeListWidget
from ui.canvas import CanvasGraphicsView
from ui.editor import EditorWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyWorks")
        self.setGeometry(500, 300, 1200, 800)

        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QHBoxLayout()

        # Add custom widgets
        self.node_list = NodeListWidget()
        layout.addWidget(self.node_list)

        self.canvas = CanvasGraphicsView()
        layout.addWidget(self.canvas)

        self.editor = EditorWidget()
        layout.addWidget(self.editor)

        central_widget.setLayout(layout)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 

if __name__ == "__main__":
    main()



