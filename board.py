from __future__ import annotations

import copy
from typing import List

from PySide6.QtCore import QRect, Qt, QPoint
from PySide6.QtGui import QPaintEvent, QPainter, QPen, QColor, QMouseEvent, QFont, \
    QKeyEvent, QBrush
from PySide6.QtWidgets import QWidget

from components.border_constraints import XVSum, Quadruple, BorderComponent, Difference, Ratio, \
    LessGreater
from components.outside_components import Sandwich, XSumsClue, LittleKiller, OutsideComponent
from components.region_constraints import RegionComponent, Cage
from sudoku import Sudoku
from sudoku import tile_to_poly


NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

SELECTION_COLOR = QColor("#01C4FF")

COLORS = [
    QColor("#6495ED"),  # Blue
    QColor("#FA8072"),  # Red
    QColor("#98fc03"),  # Green

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

        self.unsolved = True

        self.selected = set()

        self.steps_done = []

        self.setMouseTracking(True)

        self.cell_size = 70
        self.setFixedSize(self.cell_size * 11, self.cell_size * 11)

        self.current_component = None
        self.selected_component = None

        self.border_component = None
        self.cell_component = None

        self.selected_border = None
        self.selected_cells = []
        self.making_quadruple = False

        self.x_pressed = False
        self.v_pressed = False

        self.cell_component_selected = False

    def solve_board(self):
        self.sudoku.brute_force_time = 20
        self.sudoku.start_process()

        self.sudoku.solve()
        self.unsolved = False

        self.update()

    def clear_grid(self):
        for i in range(81):
            self.sudoku.board[i].reset_values(skip_value=self.sudoku.initial_state[i].value != 0)
        self.selected.clear()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawRect(self.rect())

        grid_size = self.cell_size * 9

        painter.fillRect(QRect(self.cell_size, self.cell_size, grid_size, grid_size),
                         QColor("#FFF"))

        # DRAW CELL COLORS

        for cell in self.sudoku.board:
            cell.draw_colors(painter, self.cell_size)

        for cell_cmp in self.sudoku.cell_components:
            cell_cmp.draw(painter, self.cell_size)

        # DRAW SELECTION

        pen = QPen(QColor(SELECTION_COLOR), self.cell_size // 8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        offset = self.cell_size // 16  # SHIFTS THE SELECTION LINES INWARDS

        for edge in tile_to_poly(self.sudoku.board, self.cell_size, self.selected, offset):
            if self.cell_component is None:
                edge.draw(painter, self.cell_size, offset)

        if len(self.selected) == 1 and self.window_.highlight_cells_box.isChecked():

            c = self.sudoku.board[next(iter(self.selected))]

            if c.value != 0:
                for cell in self.sudoku.sees(c.index):

                    if cell != c:
                        painter.fillRect(cell.rect(self.cell_size), QColor(245, 230, 39, 69))

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

        for region_cmp in self.sudoku.region_components:
            region_cmp.draw(painter, self.cell_size)

        for outside_cmp in self.sudoku.outside_components:
            outside_cmp.draw(painter, self.cell_size)

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

            painter.setFont(QFont("Varela Round", 32, QFont.Bold))
            painter.setPen(QPen(QColor("#000000"), 1.0))

            if cell.colors.only(QColor("#000000")):
                painter.setPen(QPen(QColor("#FFFFFF"), 1.0))

            if cell.value != 0:

                if self.sudoku.initial_state[i].value != 0:
                    painter.setPen(QPen(QColor("#3b7cff"), 1.0))
                else:
                    painter.setPen(
                        QPen(Qt.black if not COLORS[-1] in cell.colors else Qt.white, 1.0))

                painter.drawText(cell.rect(self.cell_size), Qt.AlignCenter, str(cell.value))

            else:
                size = 10
                painter.setBrush(Qt.NoBrush)
                painter.setFont(QFont("Arial Black", size))
                painter.setPen(QPen(QColor("#333333"), 1.0))

                txt = ''.join(sorted(map(str, cell.valid_numbers)))

                if len(txt) > 5:
                    txt = txt[0:5] + "\n" + txt[5:]

                painter.drawText(cell.rect(self.cell_size), Qt.AlignCenter, txt)

                painter.setFont(QFont("Arial Black", size))

                for num in cell.corner:
                    painter.drawText(cell.scaled_rect(self.cell_size, 0.75), cell.corners(num),
                                     str(num))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()

        x = event.x() - self.cell_size
        y = event.y() - self.cell_size

        # CELL

        col = x // self.cell_size
        row = y // self.cell_size

        location = row * 9 + col

        col_s = event.x() // self.cell_size
        row_s = event.y() // self.cell_size

        if (isinstance(self.current_component, OutsideComponent)
                and (col_s in (0, 10) and 1 <= row_s <= 9) or (row_s in (0, 10) and 1 <= col_s <= 9)
                or isinstance(self.current_component, LittleKiller)
                and ((col_s in (0, 10) and 0 <= row_s <= 10) or (row_s in (0, 10) and 0 <= col_s <= 10))
        ):

            if event.modifiers() == Qt.ShiftModifier:
                cmps = [cmp for cmp in self.sudoku.outside_components if
                        isinstance(cmp, OutsideComponent) and (cmp.row, cmp.col) == (row_s, col_s)]

                if cmps:
                    self.selected_component = cmps[0]

                    self.update()
                    return
            else:

                # IF LITTLER KILLER GET POSITION IN CELL CLICKED
                self.current_component.col = col_s
                self.current_component.row = row_s

                if isinstance(self.current_component, LittleKiller):
                    self.current_component.get_direction(event.pos(), self.cell_size)

                self.sudoku.outside_components.append(self.current_component)

                opp = self.current_component.opposite()

                if opp is not None and opp in self.sudoku.outside_components:
                    self.sudoku.outside_components.remove(opp)

                self.selected_component = self.current_component

                self.current_component = copy.copy(self.current_component)
                self.current_component.clear()

                self.update()


        if row < 0 or row > 8 or col < 0 or col > 8:
            return

        if event.buttons() == Qt.LeftButton:  # Add stuff

            selected_border = self.get_component_indices(x, y, location)

            if event.modifiers() == Qt.ShiftModifier:

                cmps = [cmp for cmp in self.sudoku.border_constraints if
                        sorted(cmp.indices) == sorted(selected_border)]

                if cmps:
                    self.selected_component = cmps[0]
                    self.selected = {*self.selected_component.indices}

                    if isinstance(self.selected_component, LessGreater):
                        self.selected_component.invert()
                    self.update()
                    return
            else:

                if self.current_component is not None:

                    if isinstance(self.current_component, BorderComponent):
                        if selected_border is not None:
                            self.current_component.indices = selected_border

                            self.sudoku.border_constraints.append(self.current_component)
                            self.selected_component = self.current_component

                            self.current_component = copy.copy(self.current_component)
                            self.current_component.clear()

                            self.selected = {*self.selected_component.indices}
                            self.update()
                            return

            if event.modifiers() == Qt.ControlModifier:
                self.selected.add(location)
            else:
                self.selected = {location}

        elif event.buttons() == Qt.RightButton:  # Remove stuff
            self.selected.discard(location)

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

        self.update()

        """if self.cell_component is not None and not_on_border:

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

        self.update()"""

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """if self.cell_component is not None and self.cell_component.indices:
        if not self.cell_component.check_valid():
            self.sudoku.lines.remove(self.cell_component)

        if not self.cell_component_selected:
            self.cell_component = copy.copy(self.cell_component)
            self.cell_component.indices = []

        self.selected.clear()"""
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()

        mode = self.mode_switch.currentIndex()

        match key:
            case Qt.Key_V:
                self.v_pressed = True

            case Qt.Key_X:
                self.x_pressed = True

            case Qt.Key_Delete:
                for i in self.selected:
                    cell = self.sudoku.board[i]
                    cell.clear_values(self.sudoku, mode)

        F_KEYS = [Qt.Key_F1, Qt.Key_F2, Qt.Key_F3, Qt.Key_F4]
        if key in F_KEYS:
            self.mode_switch.setCurrentIndex(F_KEYS.index(key))
            mode = self.mode_switch.currentIndex()

        if event.key() == Qt.Key_Escape:
            self.selected_component = None
            self.current_component = None
            self.making_quadruple = False
            self.selected.clear()
            self.window_.component_menu.uncheck()

        if key == Qt.Key_Backspace:
            if isinstance(self.selected_component, Sandwich | Cage | LittleKiller | XSumsClue):
                self.selected_component.reduce_total()
                self.update()
                return

        number_keys = [
            Qt.Key_1,
            Qt.Key_2,
            Qt.Key_3,
            Qt.Key_4,
            Qt.Key_5,
            Qt.Key_6,
            Qt.Key_7,
            Qt.Key_8,
            Qt.Key_9
        ]

        if isinstance(self.selected_component, XVSum):
            self.selected_component.set_value(self.v_pressed, self.x_pressed)
            self.update()
            return

        if key == Qt.Key_0:

            if isinstance(self.selected_component, Sandwich | Cage | LittleKiller | XSumsClue):
                self.selected_component.increase_total(0)
                self.update()
                return

        if key in number_keys:

            val = number_keys.index(key) + 1

            if self.selected_component is not None:
                if isinstance(self.selected_component, Difference | Ratio | Quadruple):
                    self.selected_component.set_value(val)
                    self.update()
                    return
                elif isinstance(self.selected_component, Sandwich | Cage | LittleKiller | XSumsClue):
                    self.selected_component.increase_total(val)
                    self.update()
                    return

            self.steps_done.append(copy.deepcopy(self.sudoku.board))
            for index in self.selected:
                cell = self.sudoku.board[index]

                if mode == 0 and self.sudoku.initial_state[index].value != 0:
                    continue
                else:
                    cell.set_values(mode, val, COLORS)
                    # self.sudoku.calculate_valid_numbers()

        self.update()

        if event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            self.selected = {i for i in range(81)}

        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            if self.steps_done:
                step = self.steps_done.pop()
                self.sudoku.board = copy.deepcopy(step)

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
        if event.key() == Qt.Key_V:
            self.v_pressed = False

        if event.key() == Qt.Key_X:
            self.x_pressed = False

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        x = (event.x() - self.cell_size) // self.cell_size
        y = (event.y() - self.cell_size) // self.cell_size

        location = y * 9 + x

        if not 0 <= location <= 80:
            return

        selected_cell = self.sudoku.board[location]
        self.selected.clear()

        match self.mode_switch.currentIndex():

            case 0 if selected_cell.value != 0:  # NORMAL
                similar_cells = [c for c in self.sudoku.board if c.value == selected_cell.value]
            case 1:  # CENTER
                similar_cells = [c for c in self.sudoku.board if
                                 c.valid_numbers == selected_cell.valid_numbers]
            case 2:  # CORNER
                similar_cells = [c for c in self.sudoku.board if c.corner == selected_cell.corner]
            case 3:  # COLOR
                similar_cells = [c for c in self.sudoku.board if c.colors == selected_cell.colors]
            case _:  # NONE OF THE ABOVE
                similar_cells = [selected_cell]

        for cell in similar_cells:
            self.selected.add(cell.index)

        self.update()

    def get_component_indices(self, x: int, y: int, cell_index: int) -> List[int]:
        """

        @param x: Mouse Click X
        @param y: Mouse Click Y
        @param cell_index: Index of clicked Cell
        @return: List of indices that correspond tho the cells that share a clicked border
        """

        col, row = cell_index % 9, cell_index // 9
        threshhold = self.cell_size // 3  # How far from a border can you click to select it

        if self.making_quadruple:

            if x % self.cell_size <= threshhold and y % self.cell_size <= threshhold:
                # TOP_LEFT

                if row > 1 and col > 0:
                    return [cell_index - 10, cell_index - 9, cell_index - 1, cell_index]

            if x % self.cell_size >= self.cell_size - threshhold and y % self.cell_size <= threshhold:
                # TOP_RIGHT
                if row > 1 and col < 8:
                    return [cell_index - 9, cell_index - 8, cell_index, cell_index + 1, ]

            if x % self.cell_size <= threshhold \
                    and y % self.cell_size >= self.cell_size - threshhold:
                # BOTTOM_LEFT

                if row < 8 and col > 0:
                    return [cell_index - 1, cell_index, cell_index + 9, cell_index + 8]

            if (x % self.cell_size >= self.cell_size - threshhold
                    and y % self.cell_size >= self.cell_size - threshhold):
                # BOTTOM_RIGHT
                if row < 8 and col < 8:
                    return [cell_index, cell_index + 1, cell_index + 9, cell_index + 10]

            return None

        else:

            if x % self.cell_size <= 10 and col > 0:
                return [cell_index - 1, cell_index]

            elif x % self.cell_size >= self.cell_size - 10 and col < 8:
                return [cell_index, cell_index + 1]

            elif y % self.cell_size <= 10 and row > 0:
                return [cell_index - 9, cell_index]

            elif y % self.cell_size >= self.cell_size - 10 and row < 8:
                return [cell_index, cell_index + 9]

            else:
                return None
                # NO BORDER HIT

    def is_orthogonal(self, location: int, lst: List[int]):
        if len(lst) <= 1:
            return True
        return location in [c.index for c in self.sudoku.get_king_neighbours(lst[-1])]
