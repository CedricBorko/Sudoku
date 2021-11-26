from __future__ import annotations

import copy
import math
import random
import time
from typing import List

from PySide6.QtCore import QRect, Qt, QObject, Signal, QThread
from PySide6.QtGui import QPaintEvent, QPainter, QPen, QColor, QMouseEvent, QFont, \
    QKeyEvent, QResizeEvent
from PySide6.QtWidgets import QWidget, QSizePolicy

from constraints.border_components import XVSum, Quadruple, BorderComponent, Difference, Ratio, \
    LessGreater
from constraints.cell_components import CellComponent
from constraints.line_components import Arrow, LineComponent, PalindromeLine, GermanWhispersLine, \
    BetweenLine, LockoutLine, Thermometer
from constraints.outside_components import Sandwich, XSumsClue, LittleKiller, OutsideComponent
from constraints.region_components import RegionComponent, Cage
from sudoku_.sudoku import Sudoku
from sudoku_.edge import tile_to_poly
from utils import BoundList, Constants
import sudoku_.board as b

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

SELECTION_COLOR = QColor("#01C4FF")

COLORS = [
    QColor("#88C1F2"),  # Blue
    QColor("#F29494"),  # Red
    QColor("#DCF2AC"),  # Green

    QColor("#EAAEF2"),  # Purple
    QColor("#F2AB91"),  # Orange
    QColor("#F2DC99"),  # YELLOW

    QColor("#BBBBBB"),  # Light Gray
    QColor("#666666"),  # Dark Gray
    QColor("#000000")  # Black
]


class Solver(QObject):
    progressChanged = Signal()
    finished = Signal()

    def __init__(self, sudoku):
        super().__init__()

        self.sudoku = sudoku
        self.speed = 1000

    def solve(self):
        self.sudoku.solve_in_thread(self, random_pick=True)
        self.finished.emit()


class Generator(QObject):
    progressChanged = Signal()
    finished = Signal()

    def __init__(self, sudoku):
        super().__init__()

        self.sudoku = sudoku

    def generate(self):
        sudo = b.Sudoku(9)
        sudo.generate_random_board()
        sudo.genereate_board_with_unique_solution(random.randint(17, 56))
        for i in range(81):
            self.sudoku.cells[i].value = sudo.cells[i].value if sudo.cells[
                                                                    i].value != -1 else Constants.EMPTY

        self.finished.emit()


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
        self.setMinimumSize(440, 440)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.cell_size = 40

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
        self.solver = Solver(self.sudoku)
        self.thread_ = QThread(self.solver)

        self.generator = Generator(self.sudoku)
        self.thread_gen = QThread(self.generator)

    def onProgressChanged(self):
        self.update()

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.setFixedWidth(self.height())
        self.cell_size = self.height() // (self.sudoku.size + 2)
        self.update()

    def set_speed(self):
        self.solver.speed = self.window_.speed_slider.value()

    def set_value(self, value: int):
        self.steps_done.append(copy.deepcopy(self.sudoku.cells))
        mode = self.mode_switch.currentIndex()
        for index in self.selected:
            cell = self.sudoku.cells[index]

            if mode == 0 and self.sudoku.initial_state[index].value != 0:
                continue
            else:
                cell.set_values(mode, value, COLORS)
        self.update()

    def solve_board(self):
        self.sudoku.brute_force_time = 60
        if self.window_.step_by_step_solve.isChecked():
            self.solver.progressChanged.connect(self.onProgressChanged)
            self.solver.moveToThread(self.thread_)
            self.thread_.started.connect(self.solver.solve)
            self.solver.finished.connect(self.tidy_up_thread)
            self.thread_.start()
            self.unsolved = False
        else:
            self.sudoku.solve(random_pick=True)
            self.sudoku.start_process()
        self.update()

    def generate_sudoku(self):

        self.generator.moveToThread(self.thread_gen)
        self.thread_gen.started.connect(self.generator.generate)
        self.generator.finished.connect(self.tidy_gen)
        self.generator.progressChanged.connect(self.onProgressChanged)
        self.thread_gen.start()
        self.update()

    def tidy_gen(self):
        self.thread_gen.quit()
        self.thread_gen.wait()
        self.update()

    def tidy_up_thread(self):
        self.thread_.quit()
        self.thread_.wait()

    def next_step(self):

        self.sudoku.calculate_valid_numbers()

        self.update()
        self.setFocus()

    def clear_grid(self):
        for i in range(81):
            self.sudoku.cells[i].reset_values(
                skip_value=self.sudoku.initial_state[i].value != Constants.EMPTY)
        self.selected.clear()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.drawRect(self.rect())

        grid_size = self.cell_size * self.sudoku.size

        painter.fillRect(QRect(self.cell_size, self.cell_size, grid_size, grid_size),
                         QColor("#FFF"))

        # DRAW CELL COLORS

        for cell in self.sudoku.cells:
            cell.draw_colors(painter, self.cell_size)

        for cell_cmp in self.sudoku.cell_components:
            cell_cmp.draw(painter, self.cell_size)

        # DRAW PHISTOMEFEL RING

        """indices = (0, 1, 7, 8, 9, 10, 16, 17, 63, 64, 70, 71, 72, 73, 79, 80)

        for index in indices:
            painter.fillRect(self.sudoku.cells[index].rect(self.cell_size), COLORS[3])

        for index in (20, 21, 22, 23, 24, 29, 33, 38, 42, 47, 51, 56, 57, 58, 59, 60):
            painter.fillRect(self.sudoku.cells[index].rect(self.cell_size), COLORS[2])"""

        painter.setBrush(Qt.NoBrush)

        # DRAW SELECTION

        pen = QPen(QColor(SELECTION_COLOR), self.cell_size // 8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        offset = self.cell_size // 16  # SHIFTS THE SELECTION LINES INWARDS

        for edge in tile_to_poly(self.sudoku.cells, self.cell_size, self.selected, offset):
            if self.cell_component is None:
                edge.draw(painter, self.cell_size, offset)

        if len(self.selected) == 1 and self.window_.highlight_cells_box.isChecked():

            c = self.sudoku.cells[next(iter(self.selected))]

            if c.value != 0:
                for cell in c.sees:

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

        for i in range(self.sudoku.size):
            painter.setPen(QPen(QColor("#000"), 1.0))
            if i % (self.sudoku.size // (math.sqrt(self.sudoku.size))) == 0:
                painter.setPen(QPen(QColor("#000"), 4.0))

            painter.drawLine(
                self.cell_size,
                self.cell_size + i * self.cell_size,
                self.cell_size * (self.sudoku.size + 1),
                self.cell_size + i * self.cell_size,
            )

            painter.drawLine(
                self.cell_size + i * self.cell_size,
                self.cell_size,
                self.cell_size + i * self.cell_size,
                self.cell_size * (self.sudoku.size + 1),
            )

        # INDICATE CELLS SEEN BY SINGLE SELECTED CELL

        for line_cmp in sorted(self.sudoku.lines_components, key=lambda l_cmp: l_cmp.LAYER):
            line_cmp.draw(painter, self.cell_size)

        for region_cmp in self.sudoku.region_components:
            region_cmp.draw(painter, self.cell_size)

        for outside_cmp in self.sudoku.outside_components:
            outside_cmp.draw(painter, self.cell_size)

        for border_cmp in self.sudoku.border_components:
            border_cmp.draw(painter, self.cell_size)

        painter.setBrush(Qt.NoBrush)

        painter.setPen(QPen(QColor("#000"), 1.0))

        # DRAW CELL CONTENTS

        for i, cell in enumerate(self.sudoku.cells):

            painter.setFont(QFont("Asap", self.cell_size // 2, QFont.Bold))
            painter.setPen(QPen(QColor("#000000"), 1.0))

            if cell.colors.only(QColor("#000000")):
                painter.setPen(QPen(QColor("#FFFFFF"), 1.0))

            if cell.value != Constants.EMPTY:

                if self.sudoku.initial_state[i].value != Constants.EMPTY:
                    painter.setPen(QPen(QColor("#000000"), 1.0))
                else:
                    painter.setPen(
                        QPen(QColor("#3b7cff") if not COLORS[-1] in cell.colors else Qt.white, 1.0))

                painter.drawText(cell.rect(self.cell_size), Qt.AlignCenter, str(cell.value))

            else:
                size = self.cell_size // 6
                painter.setBrush(Qt.NoBrush)
                painter.setFont(QFont("Asap", size))
                painter.setPen(QPen(QColor("#333333"), 1.0))

                txt = ''.join(sorted(map(str, cell.valid_numbers)))

                if len(txt) > 5:
                    txt = txt[0:5] + "\n" + txt[5:]

                painter.drawText(cell.rect(self.cell_size), Qt.AlignCenter, txt)

                painter.setFont(QFont("Asap", size))

                for num in cell.corner:
                    painter.drawText(cell.scaled_rect(self.cell_size, 0.75), str(num),
                                     cell.corners(num))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()

        x = event.x() - self.cell_size
        y = event.y() - self.cell_size

        # CELL

        grid_col = x // self.cell_size
        grid_row = y // self.cell_size

        location = grid_row * 9 + grid_col

        if 0 <= location <= 80:
            # print(self.sudoku.valid_numbers(location))
            print(self.sudoku.check_numbers(location))

        outside_col = event.x() // self.cell_size
        outside_row = event.y() // self.cell_size

        outside_grid = grid_row < 0 or grid_row > 8 or grid_col < 0 or grid_col > 8

        cell_x = (event.x() - self.cell_size) % self.cell_size
        cell_y = (event.y() - self.cell_size) % self.cell_size

        selected_border = self.get_component_indices(x, y, location)

        threshhold = 10
        not_on_border = not (
            (cell_x <= threshhold and cell_y < threshhold)
            or (cell_x <= threshhold and cell_y >= self.cell_size - threshhold)
            or (cell_x >= self.cell_size - threshhold and cell_y < threshhold)
            or (cell_x >= self.cell_size - threshhold and cell_y >= self.cell_size - threshhold)
        )

        # Manage Components
        ############################################################################################
        ############################################################################################

        if event.buttons() == Qt.LeftButton:
            match cmp := self.current_component:

                #  XSum, Sandwhich, Little Killer
                ####################################################################################
                case OutsideComponent():

                    if not cmp.can_create(outside_col, outside_row):
                        return

                    # SELECT OUTSIDE
                    if event.modifiers() == Qt.ShiftModifier:
                        self.selected_component = self.current_component.get(outside_col,
                                                                             outside_row)
                        self.update()
                        return

                    # CREATE / DELETE
                    else:

                        self.current_component.setup(outside_col, outside_row)

                        if isinstance(self.current_component, LittleKiller):
                            # Little Killer needs to determine the direction of its Diagonal
                            self.current_component.get_direction(event.pos(), self.cell_size)

                        self.sudoku.outside_components.append(self.current_component)

                        opp = self.current_component.opposite()

                        # E.g. There can only be one Sandwich Clue per row / column
                        if opp is not None and opp in self.sudoku.outside_components:
                            self.sudoku.outside_components.remove(opp)

                        self.selected_component = self.current_component

                        self.current_component = copy.copy(self.current_component)
                        self.current_component.clear()

                        self.window_.rule_view.add_rule(self.current_component.RULE)
                        self.selected.clear()

                        self.update()
                        return

                #  Difference, Ratio, LessGreater, XVSum, Quadruple
                ####################################################################################
                case BorderComponent() if not outside_grid and selected_border is not None:

                    if event.modifiers() == Qt.ShiftModifier:

                        self.selected_component = self.current_component.get(selected_border)

                        if self.selected_component is None:
                            return

                        if isinstance(self.selected_component, LessGreater):
                            self.selected_component.invert()

                        self.selected = {*self.selected_component.indices}
                        self.update()
                        return
                    else:

                        if isinstance(self.current_component, Quadruple):
                            self.current_component.setup(selected_border)
                        else:
                            self.current_component.indices = selected_border

                        self.sudoku.border_components.append(self.current_component)
                        self.selected_component = self.current_component

                        self.current_component = copy.copy(self.current_component)
                        self.current_component.clear()

                        self.window_.rule_view.add_rule(self.current_component.RULE)

                        self.selected = {*self.selected_component.indices}
                        self.update()

                        return

                #  Even, Odd
                ####################################################################################
                case CellComponent() if not outside_grid:

                    if event.modifiers() == Qt.ShiftModifier:

                        self.selected_component = self.current_component.get(location)
                        if self.selected_component is None:
                            return

                        self.selected = {self.selected_component.index}
                        self.update()

                        return
                    else:
                        self.current_component.index = location

                        self.sudoku.cell_components.append(self.current_component)
                        self.selected_component = self.current_component

                        self.current_component = copy.copy(self.current_component)
                        self.current_component.clear()
                        self.window_.rule_view.add_rule(self.current_component.RULE)

                        self.selected = {self.selected_component.index}
                        self.update()
                        return

                #  Arrow, Thermo, GW, Renban, Palindrome...
                ####################################################################################
                case LineComponent() if not outside_grid:

                    if event.modifiers() == Qt.ControlModifier:
                        if (self.selected_component is not None
                            and not isinstance(self.selected_component,
                                               Arrow | BetweenLine | LockoutLine | Thermometer)):
                            if self.selected_component.valid_location(location, not_on_border):
                                self.update()
                                self.selected = {*self.selected_component.ends}
                        return

                    if event.modifiers() == Qt.ShiftModifier:
                        self.selected_component = self.current_component.get(location)
                        if not self.selected_component:
                            self.selected.clear()
                            return

                        self.selected = {*self.selected_component.ends}
                        self.update()
                        return

                    if event.modifiers() == Qt.NoModifier:
                        if isinstance(self.selected_component,
                                      Arrow | LockoutLine | BetweenLine | Thermometer):
                            if self.selected_component.delete_branch(location):
                                self.update()
                                self.selected.clear()
                                return

                        self.current_component.setup(location)

                        self.sudoku.lines_components.append(self.current_component)
                        self.selected_component = self.current_component

                        self.current_component = copy.copy(self.current_component)
                        self.current_component.clear()
                        self.window_.rule_view.add_rule(self.current_component.RULE)

                        self.update()
                        return

                case RegionComponent() if not outside_grid:
                    if event.modifiers() == Qt.ShiftModifier:
                        self.selected_component = self.current_component.get(location)

                        if not self.selected_component:
                            return

                        self.selected = {*self.selected_component.indices}
                        self.update()
                        return

                    else:

                        self.current_component.indices = BoundList([location], max_length=9)

                        self.sudoku.region_components.append(self.current_component)
                        self.selected_component = self.current_component

                        self.current_component = copy.copy(self.current_component)
                        self.current_component.clear()
                        self.window_.rule_view.add_rule(self.current_component.RULE)

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

        grid_col = x // self.cell_size
        grid_row = y // self.cell_size

        if not (0 <= x <= 8 and 0 <= y <= 8):
            return

        new_location = y * 9 + x

        outside_grid = grid_row < 0 or grid_row > 8 or grid_col < 0 or grid_col > 8

        threshhold = 15
        not_on_border = not (
            (cell_x <= threshhold and cell_y < threshhold)
            or (cell_x <= threshhold and cell_y >= self.cell_size - threshhold)
            or (cell_x >= self.cell_size - threshhold and cell_y < threshhold)
            or (cell_x >= self.cell_size - threshhold and cell_y >= self.cell_size - threshhold)
        )

        match cmp := self.selected_component:

            case Arrow() | LockoutLine() | BetweenLine() | Thermometer() if not outside_grid:
                if not event.modifiers() == Qt.ShiftModifier:
                    return

                self.selected = {*cmp.ends}
                if cmp.current_branch is None:
                    if cmp.can_add_branch(new_location) and not_on_border:
                        cmp.branches.append([self.sudoku.cells[new_location]])
                        cmp.current_branch = cmp.branches[-1]

                else:
                    if cmp.valid_location(new_location) and not_on_border:
                        cmp.current_branch.append(self.sudoku.cells[new_location])
                        self.update()
                    else:
                        if cmp.can_remove(new_location):
                            cmp.current_branch.remove(cmp.current_branch[-1])

            case PalindromeLine() | GermanWhispersLine() if not outside_grid:
                if self.selected_component.valid_location(new_location, not_on_border):
                    self.update()

                    self.selected = {*cmp.ends}
                    return

            case RegionComponent() if not outside_grid:

                if (new_location in self.selected_component.get_neighbours()
                    and self.selected_component.valid_location(new_location)):
                    self.selected_component.indices.append(new_location)

                self.update()

                self.selected = {*cmp.indices}

        if event.buttons() == Qt.LeftButton:
            self.selected.add(new_location)

        elif event.buttons() == Qt.RightButton and new_location in self.selected:
            self.selected.remove(new_location)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:

        if isinstance(self.selected_component, Arrow | BetweenLine | LockoutLine | Thermometer):
            self.selected_component.current_branch = None

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
                    cell = self.sudoku.cells[i]
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
                elif isinstance(self.selected_component,
                                Sandwich | Cage | LittleKiller | XSumsClue):
                    self.selected_component.increase_total(val)
                    self.update()
                    return

            self.steps_done.append(copy.deepcopy(self.sudoku.cells))
            for index in self.selected:
                cell = self.sudoku.cells[index]

                if mode == 0 and self.sudoku.initial_state[index].value != Constants.EMPTY:
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
                self.sudoku.cells = copy.deepcopy(step)

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

        selected_cell = self.sudoku.cells[location]
        self.selected.clear()

        match self.mode_switch.currentIndex():

            case 0 if selected_cell.value != 0:  # NORMAL
                similar_cells = [c for c in self.sudoku.cells if c.value == selected_cell.value]
            case 1:  # CENTER
                similar_cells = [c for c in self.sudoku.cells if
                                 c.valid_numbers == selected_cell.valid_numbers]
            case 2:  # CORNER
                similar_cells = [c for c in self.sudoku.cells if c.corner == selected_cell.corner]
            case 3:  # COLOR
                similar_cells = [c for c in self.sudoku.cells if c.colors == selected_cell.colors]
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

                if row > 0 and col > 0:
                    return [cell_index - 10, cell_index - 9, cell_index - 1, cell_index]

            if x % self.cell_size >= self.cell_size - threshhold and y % self.cell_size <= threshhold:
                # TOP_RIGHT
                if row > 0 and col < 8:
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
        return location in [c.index for c in self.sudoku.get_cell(lst[-1]).neighbours]
