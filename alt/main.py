import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from sudoku_window import SudokuWindow


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    window = SudokuWindow()
    window.show()
    sys.exit((app.exec()))


if __name__ == "__main__":
    main()


