from __future__ import annotations
from PySide6.QtCore import QRect, Qt, QPoint, QObject, QEvent, QTimer
from PySide6.QtGui import QPaintEvent, QPainter, QPen, QColor, QResizeEvent, QMouseEvent, QFont, \
    QKeyEvent, QEnterEvent, QPolygon
from PySide6.QtWidgets import QWidget, QSizePolicy, QGridLayout

from sudoku import Sudoku
from sudoku import tile_to_poly

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

NORMAL = 4
CENTER = 5
CORNER = 6
COLOR = 7

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


class SudokuBoard(QWidget):
    def __init__(self, parent: QWidget, sudoku: Sudoku):
        super().__init__(parent)

        self.sudoku = sudoku
        self.mode_switch = parent.mode_switch

        self.ctrl_pressed = False
        self.unsolved = True

        self.selected = {self.sudoku.next_empty() or 0}

        self.steps_done = []

        self.setMouseTracking(True)
        self.cell_size = 70
        self.setFixedSize(11 * self.cell_size, 11 * self.cell_size)

    def solve_board(self):
        t = QTimer(self)
        t.timeout.connect(self.next_step)
        t.setInterval(100)
        t.start()
        self.unsolved = False

        self.update()

    def next_step(self):
        i = self.sudoku.next_step()
        if i is not None:
            self.selected = {i}
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        grid_size = self.cell_size * 9

        pen = QPen(QColor("#FCC603"), 10.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        offset = 6
        edges = tile_to_poly(self.sudoku.board, self.cell_size, self.selected, offset)

        for i, cell in enumerate(self.sudoku.board):

            rect = QRect(
                cell.column * self.cell_size + grid_size // 9,
                cell.row * self.cell_size + grid_size // 9,
                grid_size // 9,
                grid_size // 9
            )

            if cell.color:
                painter.fillRect(rect, cell.color)

        for edge in edges:
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

        painter.setFont(QFont("Arial Black", 8))

        for thermo in self.sudoku.thermometers:
            thermo.draw(painter, self.cell_size)

        for cage in self.sudoku.cages:
            cage.draw(self.sudoku.board, painter, self.cell_size)

        painter.setBrush(Qt.NoBrush)

        if len(self.selected) == 1 and self.unsolved:

            c = self.sudoku.board[next(iter(self.selected))]
            if c.value != 0:
                for cell in set(self.sudoku.get_entire_column(c.index) + self.sudoku.get_entire_row(
                    c.index) + self.sudoku.get_entire_box(c.index)):
                    rect = QRect(
                        cell.column * self.cell_size + grid_size // 9,
                        cell.row * self.cell_size + grid_size // 9,
                        grid_size // 9,
                        grid_size // 9
                    )
                    painter.fillRect(rect, QColor(0, 0, 255, 50))

        painter.setPen(QPen(QColor(255, 0, 0, 90), 3.0))

        if self.sudoku.diagonal_top_left:
            painter.drawLine(
                self.cell_size, self.cell_size, self.cell_size * 10, self.cell_size * 10
            )

        if self.sudoku.diagonal_top_right:
            painter.drawLine(
                self.cell_size * 10, self.cell_size, self.cell_size, self.cell_size * 10
            )

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

        for i, cell in enumerate(self.sudoku.board):

            painter.setFont(QFont("Arial Black", 20))
            painter.setPen(QPen(QColor("#000000"), 1.0))

            rect = QRect(
                cell.column * self.cell_size + grid_size // 9,
                cell.row * self.cell_size + grid_size // 9,
                grid_size // 9,
                grid_size // 9
            )

            if cell.color == QColor("#000000"):
                painter.setPen(QPen(QColor("#FFFFFF"), 1.0))

            if cell.value != 0:

                painter.drawText(rect, Qt.AlignCenter, str(cell.value))

            else:
                size = 10 if len(cell.center) <= 5 else 16 - len(cell.center)
                painter.setFont(QFont("Arial Black", size))
                painter.setPen(QPen(QColor("#666666"), 1.0))
                painter.drawText(rect, Qt.AlignCenter, ''.join(sorted(map(str, cell.center))))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()

        # CELL

        x = (event.x() - self.cell_size) // self.cell_size
        y = (event.y() - self.cell_size) // self.cell_size

        #

        if not (0 <= x <= 8 and 0 <= y <= 8):
            return

        location = y * 9 + x

        if event.buttons() == Qt.LeftButton:

            if not self.ctrl_pressed:
                self.selected = {location}
            else:
                self.selected.add(location)

        elif event.buttons() == Qt.RightButton and location in self.selected:
            self.selected.remove(location)

        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:

        if event.buttons() == Qt.NoButton:
            return

        x = (event.x() - self.cell_size) // self.cell_size
        y = (event.y() - self.cell_size) // self.cell_size

        if not (0 <= x <= 8 and 0 <= y <= 8):
            return

        new_location = y * 9 + x

        if event.buttons() == Qt.LeftButton:
            self.selected.add(new_location)
            self.update()


        elif event.buttons() == Qt.RightButton and new_location in self.selected:
            self.selected.remove(new_location)
            self.update()


    def keyPressEvent(self, event: QKeyEvent) -> None:
        self.ctrl_pressed = event.key() == Qt.Key_Control
        # 1 = 49 ... 9 = 57
        mode = self.mode_switch.currentIndex() + 4
        key = event.key()

        if key in [i for i in range(49, 58)]:
            for index in self.selected:

                cell = self.sudoku.board[index]

                # Color
                if mode == COLOR:
                    cell.color = COLORS[key - 49]

                else:

                    if cell.value != 0:
                        return

                    if mode == NORMAL:
                        self.steps_done.append((cell.index, cell.value))
                        print(self.sudoku.valid(event.key() - 48, cell.index, True))
                        cell.value = event.key() - 48


                    elif mode == CENTER:

                        if str(event.key() - 48) in cell.center:
                            cell.center.remove(str(event.key() - 48))

                        else:
                            cell.center.add(str(event.key() - 48))


                    else:
                        if str(event.key() - 48) in cell.corner:
                            cell.corner.remove(str(event.key() - 48))
                        else:
                            cell.corner.add(str(event.key() - 48))

        """if event.key() == Qt.Key_Delete:

            for cell in self.selected:
                if mode == 0 and self.sudoku.initial[cell.y()][
                    cell.x()] == self.sudoku.empty_character:
                    self.cells[cell.y() * 9 + cell.x()].value = ""


                elif mode == 1 and self.sudoku.initial[cell.y()][
                    cell.x()] == self.sudoku.empty_character:
                    self.cells[cell.y() * 9 + cell.x()].center.clear()

                elif mode == 3:
                    self.cells[cell.y() * 9 + cell.x()].color = None"""

        if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            self.selected = {i for i in range(81)}

        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            step = self.steps_done.pop()
            self.sudoku.board[step[0]].value = step[1]

        self.update()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = False

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        x = (event.x() - self.cell_size) // self.cell_size
        y = (event.y() - self.cell_size) // self.cell_size

        if not (0 <= x <= 8 and 0 <= y <= 8):
            return

        value = self.sudoku.board[y * 9 + x].value
        color = self.sudoku.board[y * 9 + x].color
        for i, cell in enumerate(self.sudoku.board):
            if cell.value == value and value != 0 and self.mode_switch.currentIndex() == 0:
                self.selected.add(i)

            if cell.color == color and color is not None and self.mode_switch.currentIndex() == 3:
                self.selected.add(i)

        self.update()
