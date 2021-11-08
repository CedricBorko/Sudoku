from __future__ import annotations

import copy
from typing import List

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPaintEvent, QPainter, QPen, QColor, QMouseEvent, QFont, \
    QKeyEvent, QBrush
from PySide6.QtWidgets import QWidget

from components.border_constraints import XVSum, Quadruple
from components.line_constraints import Thermometer
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

        self.window_ = parent
        self.sudoku = sudoku
        self.mode_switch = parent.mode_switch

        self.ctrl_pressed = False
        self.unsolved = True

        self.selected = set()

        self.steps_done = []

        self.setMouseTracking(True)
        self.cell_size = 70
        self.setFixedSize(11 * self.cell_size, 11 * self.cell_size)

        self.border_component = None
        self.cell_component = None

        self.selected_border = None
        self.selected_cells = []
        self.making_quadruple = False

        self.x_pressed = False
        self.v_pressed = False

        self.cell_component_selected = False

    def solve_board(self):
        self.sudoku.brute_force_time = 5
        self.sudoku.start_process()

        self.sudoku.solve()
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

        painter.fillRect(QRect(self.cell_size, self.cell_size, grid_size, grid_size),
                         QColor("#FFF"))

        # DRAW CELL COLORS

        for cell in self.sudoku.board:
            if cell.color:
                painter.fillRect(cell.rect(self.cell_size), cell.color)

        # DRAW SELECTION

        pen = QPen(QColor("#FCC603"), 10.0)  # YELLOW LINES
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        offset = 6  # SHIFTS THE SELECTION LINES INWARDS

        for edge in tile_to_poly(self.sudoku.board, self.cell_size, self.selected, offset):
            if self.cell_component is None:
                edge.draw(painter, self.cell_size, offset)

        if len(self.selected) == 1 and self.window_.highlight_cells_box.isChecked():

            c = self.sudoku.board[next(iter(self.selected))]

            if c.value != 0:
                for cell in self.sudoku.sees(c.index):

                    if cell == c:
                        painter.fillRect(cell.rect(self.cell_size), QColor("#f2d044"))
                    else:
                        painter.fillRect(cell.rect(self.cell_size), QColor("#edda8c"))

        # DRAW ODD CIRCLES AND EVEN SQUARES CONSTRAINTS

        painter.setBrush(QBrush(QColor("#888888")))  # MEDIUM GRAY COLOR
        painter.setPen(Qt.NoPen)

        for cell in [self.sudoku.board[i] for i in self.sudoku.forced_odds]:
            painter.drawEllipse(cell.scaled_rect(self.cell_size, factor=0.6))

        for cell in [self.sudoku.board[i] for i in self.sudoku.forced_evens]:
            painter.drawRect(cell.scaled_rect(self.cell_size, factor=0.6))

        # DRAW DIAGONALS

        painter.setPen(QPen(QColor(255, 0, 0, 90), 3.0))

        if self.sudoku.diagonal_negative:
            painter.drawLine(
                self.cell_size, self.cell_size, self.cell_size * 10, self.cell_size * 10
            )

        if self.sudoku.diagonal_positive:
            painter.drawLine(
                self.cell_size * 10, self.cell_size, self.cell_size, self.cell_size * 10
            )

        # DRAW CAGES

        for cage in self.sudoku.cages:
            cage.draw(
                painter,
                self.sudoku.board,
                self.cell_size
            )

        # DRAW RENBAN / WHISPER / PALINDROME LINES / THERMOMETERS

        for line in self.sudoku.lines:
            line.draw(painter, self.cell_size)

        painter.setBrush(Qt.NoBrush)

        # DRAW GRID

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

        painter.setPen(QPen(QColor("#000"), 1.0))

        # INDICATE CELLS SEEN BY SINGLE SELECTED CELL

        for dot in self.sudoku.border_constraints:
            dot.draw(painter, self.cell_size)

        painter.setPen(QPen(QColor("#000"), 1.0))

        # DRAW CELL CONTENTS

        for i, cell in enumerate(self.sudoku.board):

            painter.setFont(QFont("Guardians", 20))
            painter.setPen(QPen(QColor("#000000"), 1.0))

            if cell.color == QColor("#000000"):
                painter.setPen(QPen(QColor("#FFFFFF"), 1.0))

            if cell.value != 0:

                if self.sudoku.initial_state[i].value != 0:
                    painter.setPen(QPen(QColor("#3b7cff"), 1.0))
                else:
                    painter.setPen(QPen(QColor("#000000"), 1.0))

                painter.drawText(cell.rect(self.cell_size), Qt.AlignCenter, str(cell.value))

            else:
                size = 10
                painter.setFont(QFont("Arial Black", size))
                painter.setPen(QPen(QColor("#333333"), 1.0))

                txt = ''.join(sorted(map(str, cell.valid_numbers)))
                if len(txt) > 5:
                    txt = txt[0:5] + "\n" + txt[5:]

                painter.drawText(cell.rect(self.cell_size), Qt.AlignCenter, txt)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()

        # CELL
        x = event.x() - self.cell_size
        y = event.y() - self.cell_size

        col = x // self.cell_size
        row = y // self.cell_size

        if not (0 <= col <= 8 and 0 <= row <= 8):
            return

        location = row * 9 + col
        print(self.sudoku.valid_numbers(location))

        # CELLS BORDER IS SHARED BY
        self.selected_border = self.get_border(x, y, location)

        if self.border_component is not None and self.selected_border is not None:

            self.border_component.indices = self.selected_border

            for quad in [quad for quad in self.sudoku.border_constraints if
                         isinstance(quad, Quadruple)]:
                quad.selected = False

            selected_quad = [
                quad for quad in self.sudoku.border_constraints + [self.border_component]
                if sorted(quad.indices) == sorted(self.selected_border)
            ][0]

            selected_quad.selected = True
            self.update()

            if event.modifiers() == Qt.ShiftModifier:
                return

            self.border_component.create(self.selected_border)

            self.border_component = copy.copy(self.border_component)
            self.border_component.indices = []
            if isinstance(self.border_component, Quadruple):
                self.border_component.numbers = []

            self.update()
            return

        if event.buttons() == Qt.LeftButton and self.border_component is None:

            if not self.ctrl_pressed:
                self.selected = {location}
            else:
                self.selected.add(location)

        elif event.buttons() == Qt.RightButton and location in self.selected:
            self.selected.remove(location)

        if self.cell_component is not None:

            for cmp in self.sudoku.lines:
                if location in cmp.indices and cmp is not self.cell_component:
                    if event.modifiers() == Qt.ShiftModifier:
                        self.cell_component = cmp
                        print(self.cell_component)
                        self.cell_component_selected = True

                        break
                    else:
                        self.sudoku.lines.remove(cmp)
                        del cmp
                        self.update()
                        self.cell_component_selected = False
                        return

            if self.cell_component not in self.sudoku.lines:
                self.sudoku.lines.append(self.cell_component)
                self.cell_component.indices.append(location)
                self.update()

        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:

        if event.buttons() == Qt.NoButton:
            return

        x = (event.x() - self.cell_size) // self.cell_size
        y = (event.y() - self.cell_size) // self.cell_size

        cell_x = (event.x() - self.cell_size) % self.cell_size
        cell_y = (event.y() - self.cell_size) % self.cell_size

        if not (0 <= x <= 8 and 0 <= y <= 8):
            return

        new_location = y * 9 + x

        not_on_border = (
            10 <= cell_x <= self.cell_size - 10 and 10 <= cell_y <= self.cell_size - 10)

        if event.buttons() == Qt.LeftButton and self.border_component is None and not_on_border:
            self.selected.add(new_location)

        elif event.buttons() == Qt.RightButton and new_location in self.selected:
            self.selected.remove(new_location)

        if self.cell_component is not None and not_on_border:

            for cmp in self.sudoku.lines:
                if isinstance(cmp, Thermometer) and isinstance(self.cell_component, Thermometer):

                    if cmp is not self.cell_component and new_location == cmp.bulb.index:
                        return

            if self.cell_component not in self.sudoku.lines:
                self.sudoku.lines.append(self.cell_component)
            else:
                self.cell_component_selected = False

            if new_location not in self.cell_component.indices:
                if not self.is_orthogonal(new_location, self.cell_component.indices):
                    return
                else:
                    if isinstance(self.cell_component, Thermometer) and len(
                        self.cell_component.indices) > 8:
                        return

                self.cell_component.indices.append(new_location)
                if isinstance(self.cell_component, Thermometer):
                    self.cell_component.bulb = self.sudoku.board[self.cell_component.indices[0]]

            else:
                if new_location != self.cell_component.indices[-1]:
                    return

            self.update()

        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.cell_component is not None and self.cell_component.indices:
            if not self.cell_component.check_valid():
                self.sudoku.lines.remove(self.cell_component)

            if not self.cell_component_selected:
                self.cell_component = copy.copy(self.cell_component)
                self.cell_component.indices = []

            self.selected.clear()
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()

        if key == Qt.Key_Control:
            self.ctrl_pressed = True

        if key == Qt.Key_V:
            self.v_pressed = True

        if key == Qt.Key_X:
            self.x_pressed = True

        if event.key() == Qt.Key_Escape:
            self.border_component = None
            self.making_quadruple = False
            self.cell_component = None

            for quad in [quad for quad in self.sudoku.border_constraints if
                         isinstance(quad, Quadruple)]:
                quad.selected = False

        # 1 = 49 ... 9 = 57
        mode = self.mode_switch.currentIndex() + 4

        if self.selected_border is not None and len(self.sudoku.border_constraints) != 0:

            selected_constraints = [
                constraint for constraint in self.sudoku.border_constraints
                if sorted(constraint.indices) == sorted(self.selected_border)
            ]
            if not selected_constraints:
                return

            selected_constraint = selected_constraints[0]

            if isinstance(self.border_component, XVSum):

                match (self.v_pressed, self.x_pressed):
                    case (True, False):
                        selected_constraint.total = 5

                    case (False, True):
                        selected_constraint.total = 10

                    case (True, True):
                        selected_constraint.total = 15

                self.update()
                return

            if key in [i for i in range(49, 58)]:

                number = event.key() - 48

                if isinstance(self.border_component, Quadruple):

                    if number in selected_constraint.numbers:
                        selected_constraint.numbers.remove(number)
                        self.update()
                        return

                    if len(selected_constraint.numbers) >= 4:
                        selected_constraint.numbers.pop(-1)

                    selected_constraint.numbers.append(number)
                    selected_constraint.numbers.sort()

                    self.update()
                    return

        if key in [i for i in range(49, 58)]:

            for index in self.selected:

                cell = self.sudoku.board[index]

                # Color
                if mode == COLOR:
                    if cell.color == COLORS[key - 49]:
                        cell.color = None
                    else:
                        cell.color = COLORS[key - 49]

                else:

                    if self.sudoku.initial_state[index].value != 0:
                        return

                    if mode == NORMAL:
                        self.steps_done.append((cell.index, cell.value))
                        cell.value = event.key() - 48
                        self.sudoku.calculate_valid_numbers()

                    elif mode == CENTER:

                        if event.key() - 48 in cell.valid_numbers:
                            cell.valid_numbers.remove(event.key() - 48)

                        else:
                            cell.valid_numbers.append(event.key() - 48)

                    else:
                        if str(event.key() - 48) in cell.corner:
                            cell.corner.remove(event.key() - 48)
                        else:
                            cell.corner.add(event.key() - 48)

        if event.key() == Qt.Key_Delete:

            for i in self.selected:
                if self.sudoku.initial_state[i].value == 0:
                    self.sudoku.board[i].value = 0

        if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            self.selected = {i for i in range(81)}

        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            step = self.steps_done.pop()
            self.sudoku.board[step[0]].value = step[1]
            # self.sudoku.calculate_valid_numbers()

        if len(self.selected) == 1:
            index = next(iter(self.selected))

            if event.key() in (Qt.Key_W, Qt.Key_Up) and index >= 9:
                self.selected = {index - 9}

            if event.key() in (Qt.Key_A, Qt.Key_Left) and index % 9 != 0:
                self.selected = {index - 1}

            if event.key() in (Qt.Key_S, Qt.Key_Down) and index <= 71:
                self.selected = {index + 9}

            if event.key() in (Qt.Key_D, Qt.Key_Right) and index % 9 != 8:
                self.selected = {index + 1}

        self.update()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = False

        if event.key() == Qt.Key_V:
            self.v_pressed = False

        if event.key() == Qt.Key_X:
            self.x_pressed = False

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

    def get_border(self, x: int, y: int, location: int):

        col, row = location % 9, location // 9
        threshhold = self.cell_size // 3

        if self.making_quadruple:

            if x % self.cell_size <= threshhold and y % self.cell_size <= threshhold:
                # TOP_LEFT

                if row > 1 and col > 0:
                    return [location, location - 1, location - 10, location - 9]

            if x % self.cell_size >= self.cell_size - threshhold and y % self.cell_size <= threshhold:
                # TOP_RIGHT
                if row > 1 and col < 8:
                    return [location, location + 1, location - 9, location - 8]

            if x % self.cell_size <= threshhold \
                and y % self.cell_size >= self.cell_size - threshhold:
                # BOTTOM_LEFT

                if row < 8 and col > 0:
                    return [location, location - 1, location + 9, location + 8]

            if (x % self.cell_size >= self.cell_size - threshhold
                and y % self.cell_size >= self.cell_size - threshhold):
                # BOTTOM_RIGHT
                if row < 8 and col < 8:
                    return [location, location + 1, location + 9, location + 10]

            return None

        else:

            if x % self.cell_size <= 10 and col > 0:
                return [location, location - 1]
            elif x % self.cell_size >= self.cell_size - 10 and col < 9:
                return [location, location + 1]
            elif y % self.cell_size <= 10 and row > 0:
                return [location, location - 9]
            elif y % self.cell_size >= self.cell_size - 10 and row < 9:
                return [location, location + 9]
            else:
                return None
                # NO BORDER HIT

    def is_orthogonal(self, location: int, lst: List[int]):
        if len(lst) <= 1:
            return True
        return location in [c.index for c in self.sudoku.get_king_neighbours(lst[-1])]
