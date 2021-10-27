from __future__ import annotations
from PySide6.QtCore import QRect, Qt, QPoint, QObject, QEvent
from PySide6.QtGui import QPaintEvent, QPainter, QPen, QColor, QResizeEvent, QMouseEvent, QFont, \
    QKeyEvent, QEnterEvent
from PySide6.QtWidgets import QWidget, QSizePolicy, QGridLayout

from components import Sudoku
from polymap import tile_to_poly

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

COLORS = [
    QColor("#6495ED"),  # Blue
    QColor("#FA8072"),  # Red
    QColor("#00D258"),  # Green

    QColor("#C57FFF"),  # Purple
    QColor("#FFA500"),  # Orange
    QColor("#FCC603"),  # YELLOW

    QColor("#BBBBBB"),  # Light Gray
    QColor("#666666"),  # Dark Gray
    QColor("#000000")  # Black
]


class GridCell(QWidget):
    def __init__(self, parent: SudokuBoard, row: int, col: int, value: str):
        super().__init__(parent)

        self.value = value
        self.row = row
        self.col = col

        self.cell_size = 50

        self.setFixedSize(self.cell_size, self.cell_size)
        self.setCursor(Qt.PointingHandCursor)

        self.selected = False

    def __repr__(self):
        return f"GridCell(x={self.col}, y={self.row}, value={self.value})"

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), Qt.white)
        painter.drawText(self.rect(), Qt.AlignCenter, self.value)

        if self.selected:
            painter.setPen(QPen(QColor("#6495ED"), 5.0))
            painter.drawRect(self.rect())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.selected = not self.selected
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton:
            self.selected = True
        self.update()


class OuterCell(QWidget):
    def __init__(self, parent: SudokuBoard, row: int, col: int, value: str):
        super().__init__(parent)

        self.value = value
        self.row = row
        self.col = col

        self.cell_size = 50

        self.setFixedSize(self.cell_size, self.cell_size)
        self.setCursor(Qt.PointingHandCursor)

    def __repr__(self):
        return f"OuterCell(x={self.col}, y={self.row}, value={self.value})"

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.drawText(self.rect(), Qt.AlignCenter, self.value)


class Cell:
    def __init__(self, index: int):
        self.edge_id = [0, 0, 0, 0]
        self.edge_exists = [False, False, False, False]

        self.index = index

        self.center = set()
        self.corner = set()
        self.value = ""
        self.color = None

    def reset(self):
        self.edge_id = [0, 0, 0, 0]
        self.edge_exists = [False, False, False, False]


class SudokuBoard(QWidget):
    def __init__(self, parent: QWidget, sudoku: Sudoku):
        super().__init__(parent)

        self.sudoku = sudoku
        self.mode_switch = parent.mode_switch

        self.ctrl_pressed = False

        self.selected = {QPoint(*self.sudoku.next_empty()[::-1])}

        self.setMouseTracking(True)
        self.cell_size = 50
        self.setFixedSize(11 * self.cell_size, 11 * self.cell_size)

        self.cells = [Cell(i) for i in range(81)]

        for i, cell in enumerate(self.cells):
            val = self.sudoku.board[i // 9][i % 9]
            cell.value = val if val != self.sudoku.empty_character else ""

        self.states = [(self.sudoku.board.copy(), self.cells.copy())]
        self.current_state = 0

    def undo(self):
        if self.current_state == 0:
            return
        self.current_state -= 1

        self.sudoku.board = self.states[self.current_state][0]
        self.cells = self.states[self.current_state][1]

        self.update()

    def redo(self):
        if self.current_state == len(self.states) - 1:
            return

        self.current_state += 1

        self.sudoku.board = self.states[self.current_state][0]
        self.cells = self.states[self.current_state][1]

        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        grid_size = self.cell_size * 9

        for i, cell in enumerate(self.cells):
            painter.setFont(QFont("Arial Black", 20))
            painter.setPen(QPen(QColor("#000000"), 1.0))
            row, col = i // 9, i % 9
            rect = QRect(
                col * self.cell_size + grid_size // 9,
                row * self.cell_size + grid_size // 9,
                grid_size // 9,
                grid_size // 9
            )

            if cell.color:
                painter.fillRect(rect, cell.color)

            if cell.color == QColor("#000000"):
                painter.setPen(QPen(QColor("#FFFFFF"), 1.0))

            if cell.value != "":

                painter.drawText(rect, Qt.AlignCenter, cell.value)
            else:
                size = 10 if len(cell.center) <= 5 else 16 - len(cell.center)
                painter.setFont(QFont("Arial Black", size))
                painter.setPen(QPen(QColor("#444444"), 1.0))
                painter.drawText(rect, Qt.AlignCenter, ''.join(sorted(cell.center)))

        painter.setPen(QPen(QColor("#000"), 4.0))
        painter.drawRect(
            QRect(
                self.cell_size,
                self.cell_size,
                grid_size,
                grid_size
            )
        )

        painter.drawLine(
            self.cell_size,
            self.cell_size + grid_size // 3,
            self.cell_size * 10,
            self.cell_size + grid_size // 3
        )

        painter.drawLine(
            self.cell_size,
            self.cell_size + grid_size // 3 * 2,
            self.cell_size * 10,
            self.cell_size + grid_size // 3 * 2
        )

        painter.drawLine(
            self.cell_size + grid_size // 3,
            self.cell_size,
            self.cell_size + grid_size // 3,
            self.cell_size * 10
        )
        painter.drawLine(
            self.cell_size + grid_size // 3 * 2,
            self.cell_size,
            self.cell_size + grid_size // 3 * 2,
            self.cell_size * 10
        )

        painter.setPen(QPen(QColor("#000"), 1.0))

        for num in [1, 2, 4, 5, 7, 8]:
            painter.drawLine(
                self.cell_size,
                self.cell_size + grid_size // 9 * num,
                self.cell_size * 10,
                self.cell_size + grid_size // 9 * num
            )

        for num in [1, 2, 4, 5, 7, 8]:
            painter.drawLine(
                self.cell_size + grid_size // 9 * num,
                self.cell_size,
                self.cell_size + grid_size // 9 * num,
                self.cell_size * 10
            )

        painter.setPen(QPen(QColor("#FCC603"), 6.0))
        painter.pen().setCapStyle(Qt.FlatCap)

        offset = 4
        for edge in tile_to_poly(self.cells, self.cell_size, self.selected):

            if edge.edge_type == NORTH:
                painter.drawLine(
                    self.cell_size + edge.sx + offset,
                    self.cell_size + edge.sy + offset,
                    self.cell_size + edge.ex - offset,
                    self.cell_size + edge.ey + offset
                )

            elif edge.edge_type == EAST:
                painter.drawLine(
                    self.cell_size + edge.sx - offset,
                    self.cell_size + edge.sy + offset,
                    self.cell_size + edge.ex - offset,
                    self.cell_size + edge.ey - offset
                )

            elif edge.edge_type == SOUTH:
                painter.drawLine(
                    self.cell_size + edge.sx + offset,
                    self.cell_size + edge.sy - offset,
                    self.cell_size + edge.ex - offset,
                    self.cell_size + edge.ey - offset
                )

            else:
                painter.drawLine(
                    self.cell_size + edge.sx + offset,
                    self.cell_size + edge.sy + offset,
                    self.cell_size + edge.ex + offset,
                    self.cell_size + edge.ey - offset
                )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()

        x = (event.x() - self.cell_size) // self.cell_size
        y = (event.y() - self.cell_size) // self.cell_size

        if not (0 <= x <= 8 and 0 <= y <= 8):
            return

        new_location = QPoint(x, y)

        if event.buttons() == Qt.LeftButton:

            if not self.ctrl_pressed:
                self.selected = {new_location}
            else:
                self.selected.add(new_location)
        elif event.buttons() == Qt.RightButton and new_location in self.selected:
            self.selected.remove(new_location)

        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        x = (event.x() - self.cell_size) // self.cell_size
        y = (event.y() - self.cell_size) // self.cell_size

        if not (0 <= x <= 8 and 0 <= y <= 8):
            return

        new_location = QPoint(x, y)

        if event.buttons() == Qt.LeftButton:
            self.selected.add(new_location)
        elif event.buttons() == Qt.RightButton and new_location in self.selected:
            self.selected.remove(new_location)

        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        self.ctrl_pressed = event.key() == Qt.Key_Control
        # 1 = 49 ... 9 = 57
        mode = self.mode_switch.currentIndex()

        if event.key() in [i for i in range(49, 59)]:

            for cell in self.selected:

                if (mode == 0 and event.key() != 58 and
                        self.sudoku.initial[cell.y()][cell.x()] == self.sudoku.empty_character):
                    self.cells[cell.y() * 9 + cell.x()].value = str(event.key() - 48)

                if (mode == 1 and event.key() != 58 and
                        self.sudoku.initial[cell.y()][cell.x()] == self.sudoku.empty_character):
                    if str(event.key() - 48) in self.cells[cell.y() * 9 + cell.x()].center:
                        self.cells[cell.y() * 9 + cell.x()].center.remove(str(event.key() - 48))

                    else:
                        self.cells[cell.y() * 9 + cell.x()].center.add(str(event.key() - 48))

                if mode == 3:
                    self.cells[cell.y() * 9 + cell.x()].color = COLORS[event.key() - 49]

        if event.key() == Qt.Key_Delete:

            for cell in self.selected:
                if mode == 0 and self.sudoku.initial[cell.y()][cell.x()] == self.sudoku.empty_character:
                    self.cells[cell.y() * 9 + cell.x()].value = ""


                elif mode == 1 and self.sudoku.initial[cell.y()][cell.x()] == self.sudoku.empty_character:
                    self.cells[cell.y() * 9 + cell.x()].center.clear()

                elif mode == 3:
                    self.cells[cell.y() * 9 + cell.x()].color = None

        if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            self.selected = {QPoint(i, j) for i in range(9) for j in range(9)}

        self.update()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = False

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        x = (event.x() - self.cell_size) // self.cell_size
        y = (event.y() - self.cell_size) // self.cell_size

        if not (0 <= x <= 8 and 0 <= y <= 8):
            return

        value = self.sudoku.board[y][x]
        color = self.cells[y * 9 + x].color
        for i, cell in enumerate(self.cells):
            if cell.value == value and self.mode_switch.currentIndex() == 0:
                self.selected.add(QPoint(i % 9, i // 9))

            if cell.color == color and color is not None and self.mode_switch.currentIndex() == 3:
                self.selected.add(QPoint(i % 9, i // 9))

        self.update()
