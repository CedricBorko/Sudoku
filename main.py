import sys

from PySide6.QtCore import QRect, QPoint, QSize, Qt
from PySide6.QtGui import QPaintEvent, QPainter, QPen, QColor, QResizeEvent, QMouseEvent, QKeyEvent, QFont
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QSizePolicy
from sudoku import Sudoku


class SudokuWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.hovered_cell = None
        self.selected_cell = None
        self.seen_cells = None

        self.sudoku = Sudoku.from_string(
            "200080300060070084030500209000105408000000000402706000301007040720040060004010003"
        )

        self.sudoku.do_logic_step()
        self.update()

    def bounding_rect(self) -> QRect:
        width, height = self.size().toTuple()
        margin = 10
        bounding_rect_size = min(width, height) - margin * 2
        bounding_rect_size = 9 * round(bounding_rect_size / 9)
        return QRect(margin, margin, bounding_rect_size, bounding_rect_size)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.setFixedWidth(self.height())
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHints(QPainter.TextAntialiasing | QPainter.Antialiasing)

        painter.fillRect(self.rect(), "#f2f2f2")
        painter.setPen(QPen(QColor("#000"), 4.0))

        bounding_rect = self.bounding_rect()
        cell_size = bounding_rect.height() / 9

        painter.fillRect(
            bounding_rect,
            QColor("#FFF")
        )

        if self.hovered_cell is not None and self.selected_cell is None:
            painter.fillRect(
                QRect(
                    QPoint(10 + self.hovered_cell.x() * cell_size, 10 + self.hovered_cell.y() * cell_size),
                    QSize(cell_size, cell_size)
                ),
                QColor("#88ffcd3c")
            )

        if self.selected_cell is not None:
            painter.fillRect(
                QRect(
                    QPoint(10 + self.selected_cell.x() * cell_size, 10 + self.selected_cell.y() * cell_size),
                    QSize(cell_size, cell_size)
                ),
                QColor("#88ffcd3c")
            )

            for cell_index in self.seen_cells:
                row, column = cell_index // 9, cell_index % 9
                painter.fillRect(
                    QRect(
                        QPoint(
                            10 + column * cell_size,
                            10 + row * cell_size
                        ),
                        QSize(cell_size, cell_size)
                    ),
                    QColor("#884394ff")
                )

        painter.setPen(QPen(QColor("#000"), 4.0))
        painter.drawRect(bounding_rect)

        for i in range(1, 9):
            if i % 3 == 0: painter.setPen(QPen(QColor("#000"), 4.0))
            else: painter.setPen(QPen(QColor("#000"), 1.0))
            painter.drawLine(
                bounding_rect.x(),
                bounding_rect.y() + i * cell_size,
                bounding_rect.right(),
                bounding_rect.y() + i * cell_size,
            )

            painter.drawLine(
                bounding_rect.x() + i * cell_size,
                bounding_rect.y(),
                bounding_rect.x() + i * cell_size,
                bounding_rect.bottom(),
            )

        for index, value in self.sudoku:
            row, column = index // 9, index % 9

            if value == 0:
                painter.setFont(QFont("Expressway", 14))
                painter.setPen(QColor("#000000"))
                rect = QRect(
                    QPoint(
                        10 + column * cell_size, 10 + row * cell_size
                    ),
                    QSize(cell_size, cell_size)
                )
                painter.drawText(rect, Qt.AlignCenter, ''.join(map(str, sorted(self.sudoku.get_options(index)))))
                continue

            painter.setFont(QFont("Expressway", 36))
            painter.setPen(QColor("#000000") if self.sudoku.get_initial(index) != 0 else QColor("#0000ff"))
            rect = QRect(
                QPoint(
                    10 + column * cell_size, 10 + row * cell_size
                ),
                QSize(cell_size, cell_size)
            )
            painter.drawText(rect, Qt.AlignCenter, str(value))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        bounding_rect = self.bounding_rect()
        cell_size = bounding_rect.height() / 9

        x, y = event.position().toTuple()
        x, y = (x - bounding_rect.x()) // cell_size, (y - bounding_rect.y()) // cell_size
        if 0 <= x <= 8 and 0 <= y <= 8 and self.selected_cell is None:
            self.hovered_cell = QPoint(x, y)
            self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.RightButton:
            self.selected_cell = None
            self.seen_cells = None
            self.update()
            return

        bounding_rect = self.bounding_rect()
        cell_size = bounding_rect.height() / 9

        x, y = event.position().toTuple()
        x, y = (x - bounding_rect.x()) // cell_size, (y - bounding_rect.y()) // cell_size
        if 0 <= x <= 8 and 0 <= y <= 8:
            self.selected_cell = QPoint(x, y)
            self.seen_cells = self.sudoku.seen_indices(self.selected_cell.y() * 9 + self.selected_cell.x())
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        match event.key():
            case Qt.Key_1: self.place_number(1)
            case Qt.Key_2: self.place_number(2)
            case Qt.Key_3: self.place_number(3)
            case Qt.Key_4: self.place_number(4)
            case Qt.Key_5: self.place_number(5)
            case Qt.Key_6: self.place_number(6)
            case Qt.Key_7: self.place_number(7)
            case Qt.Key_8: self.place_number(8)
            case Qt.Key_9: self.place_number(9)
            case Qt.Key_Escape: self.place_number(0)
            case Qt.Key_Space: self.sudoku.do_logic_step()
            case Qt.Key_Z if event.modifiers() == Qt.ControlModifier: self.sudoku.undo()
            case Qt.Key_Y if event.modifiers() == Qt.ControlModifier: self.sudoku.redo()
            case _: super().keyPressEvent(event)
        self.update()

    def place_number(self, number: int) -> None:
        if self.selected_cell is None: return
        index = self.selected_cell.y() * 9 + self.selected_cell.x()
        if self.sudoku.get_initial(index) == 0:
            self.sudoku.set_value(index, number)


def main():
    app = QApplication(sys.argv)
    wnd = QMainWindow()
    wnd.resize(800, 800)

    wnd.show()

    wnd.setCentralWidget(SudokuWidget())
    wnd.keyPressEvent = wnd.centralWidget().keyPressEvent
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
