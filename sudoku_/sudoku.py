from __future__ import annotations

import copy
import itertools
import os
import random
import time
from collections import Counter
from typing import List, Optional, Set, Dict, Tuple

from PySide6.QtCore import QPoint, QRect, Qt, QObject
from PySide6.QtGui import QPainter, QPolygon, QColor
from PySide6.QtWidgets import QFileDialog

from utils import StoppableThread, BoundList, Constants, LogicResult


class Cell:
    def __init__(self, sudoku: Sudoku, index: int, value: int = Constants.EMPTY):

        self.sudoku = sudoku
        self.index = index

        self.valid_numbers = BoundList(max_length=9, sort_=True)
        self.corner = BoundList(max_length=4, sort_=True)
        self.value = value
        self.colors = BoundList(max_length=4, sort_=True)
        self.candidates = {1, 2, 3, 4, 5, 6, 7, 8, 9}

        self.impossible_numbers = []

        self.edge_id = [0, 0, 0, 0]
        self.edge_exists = [False, False, False, False]

    @property
    def coordinates(self) -> str:
        return f"R{self.row + 1}C{self.column + 1}"

    @property
    def box(self) -> int:
        box_x = self.row // 3 * 3 * 9
        box_y = self.column // 3 * 3
        return (box_y * 9 // 3 + box_x) // 9

    @property
    def row(self):
        return self.index // self.sudoku.size

    @property
    def column(self):
        return self.index % self.sudoku.size

    @property
    def is_empty(self):
        return self.value == Constants.EMPTY

    def rect(self, cell_size: int):
        return QRect(
            self.column * cell_size + cell_size,
            self.row * cell_size + cell_size,
            cell_size,
            cell_size
        )

    def scaled_rect(self, cell_size: int, factor: float = 1) -> QRect:
        shift_by = int(cell_size - (cell_size * factor)) // 2
        return QRect(
            self.column * cell_size + cell_size + shift_by,
            self.row * cell_size + cell_size + shift_by,
            int(cell_size * factor),
            int(cell_size * factor)
        )

    @property
    def orthogonal_neighbours(self) -> List[Cell]:
        return [
            self.sudoku.get_cell(self.index + offset)
            for offset in (-9, -1, 1, 9) if self.sudoku.is_valid(self.index, offset)
        ]

    @property
    def diagonal_neighbours(self) -> List[Cell]:
        return [
            self.sudoku.get_cell(self.index + offset)
            for offset in (-10, -8, 8, 10) if self.sudoku.is_valid(self.index, offset)
        ]

    @property
    def knight_neighbours(self) -> List[Cell]:
        return [
            self.sudoku.get_cell(self.index + offset)
            for offset in (-19, -17, -11, -7, 7, 11, 17, 19) if
            self.sudoku.is_valid(self.index, offset)
        ]

    @property
    def neighbours(self) -> List[Cell]:
        return sorted(self.orthogonal_neighbours + self.diagonal_neighbours)

    @property
    def num_neighbours(self) -> int:
        return len(self.neighbours)

    def __repr__(self):
        return f"Cell({self.index}, {self.value})"

    def reset(self):
        self.edge_id = [0, 0, 0, 0]
        self.edge_exists = [False, False, False, False]

    def reset_values(self, skip_value: bool = False):
        if not skip_value:
            self.value = Constants.EMPTY
        self.valid_numbers.clear()
        self.corner.clear()
        self.colors.clear()

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def draw_colors(self, painter: QPainter, cell_size: int):
        amount = len(self.colors)
        rect = self.rect(cell_size)
        center = rect.center()
        painter.setPen(Qt.NoPen)

        match amount:
            case 1:
                painter.fillRect(self.rect(cell_size), self.colors[0])

            case 2:
                painter.setBrush(self.colors[0])
                painter.drawPolygon(
                    QPolygon(
                        [
                            QPoint(rect.x(), rect.y()),
                            QPoint(rect.x() + cell_size, rect.y()),
                            QPoint(rect.x() + cell_size, rect.y() + cell_size),
                        ]
                    )
                )

                painter.setBrush(self.colors[1])
                painter.drawPolygon(
                    QPolygon(
                        [
                            QPoint(rect.x() + cell_size, rect.y() + cell_size),
                            QPoint(rect.x(), rect.y() + cell_size),
                            QPoint(rect.x(), rect.y()),
                        ]
                    )
                )

            case 3:
                painter.setPen(Qt.NoPen)
                painter.setBrush(self.colors[0])
                painter.drawPolygon(
                    QPolygon(
                        [
                            QPoint(rect.x() + cell_size // 3, rect.y()),
                            center,
                            QPoint(rect.x(), rect.y() + cell_size),
                            QPoint(rect.x(), rect.y())
                        ]
                    )
                )

                painter.setBrush(self.colors[1])
                painter.drawPolygon(
                    QPolygon(
                        [
                            QPoint(rect.x() + cell_size // 3, rect.y()),
                            QPoint(rect.x() + cell_size, rect.y()),
                            QPoint(rect.x() + cell_size, rect.y() + cell_size // 3 * 2),
                            center
                        ]
                    )
                )

                painter.setBrush(self.colors[2])
                painter.drawPolygon(
                    QPolygon(
                        [
                            QPoint(rect.x() + cell_size, rect.y() + cell_size // 3 * 2),
                            QPoint(rect.x() + cell_size, rect.y() + cell_size),
                            QPoint(rect.x(), rect.y() + cell_size),
                            center
                        ]
                    )
                )

            case 4:
                painter.setBrush(self.colors[0])
                painter.drawPolygon(
                    QPolygon(
                        [
                            QPoint(rect.x(), rect.y()),
                            QPoint(rect.x() + cell_size, rect.y()),
                            center
                        ]
                    )
                )

                painter.setBrush(self.colors[1])
                painter.drawPolygon(
                    QPolygon(
                        [
                            QPoint(rect.x() + cell_size, rect.y()),
                            QPoint(rect.x() + cell_size, rect.y() + cell_size),
                            center
                        ]
                    )
                )

                painter.setBrush(self.colors[2])
                painter.drawPolygon(
                    QPolygon(
                        [
                            QPoint(rect.x() + cell_size, rect.y() + cell_size),
                            QPoint(rect.x(), rect.y() + cell_size),
                            center
                        ]
                    )
                )

                painter.setBrush(self.colors[3])
                painter.drawPolygon(
                    QPolygon(
                        [
                            QPoint(rect.x(), rect.y() + cell_size),
                            QPoint(rect.x(), rect.y()),
                            center
                        ]
                    )
                )

    def corners(self, number: int) -> Qt.Alignment:
        match sorted(self.corner).index(number):
            case 0:
                return Qt.AlignTop | Qt.AlignLeft
            case 1:
                return Qt.AlignTop | Qt.AlignRight
            case 2:
                return Qt.AlignBottom | Qt.AlignLeft
            case 3:
                return Qt.AlignBottom | Qt.AlignRight
            case _:
                return Qt.AlignHCenter | Qt.AlignVCenter

    def set_values(self, mode: int, value: int | QColor, COLORS: List[QColor]):

        match mode:

            case 0:  # NORMAL
                self.value = value

            case 1:  # CENTER
                if value not in self.valid_numbers:
                    self.valid_numbers.append(value)
                else:
                    self.valid_numbers.remove(value)

            case 2:  # CORNER
                self.corner.append(value)

            case 3:  # COLOR
                self.colors.append(COLORS[value - 1])

    def clear_values(self, sudoku: Sudoku, mode: int):
        match mode:

            case 0:  # NORMAL
                if sudoku.initial_state[self.index].value == Constants.EMPTY:
                    self.value = Constants.EMPTY

            case 1:  # CENTER

                self.valid_numbers.clear()

            case 2:  # CORNER
                self.corner.clear()

            case 3:  # COLOR
                self.colors.clear()


class Edge:
    def __init__(self, sx: int, sy: int, ex: int, ey: int, edge_type: int):
        self.sx = sx
        self.sy = sy
        self.ex = ex
        self.ey = ey

        self.id_ = None
        self.edge_type = edge_type

    def __repr__(self):
        return f"({self.sx}, {self.sy}) -> ({self.ex}, {self.ey})"

    def draw(self, painter: QPainter, cell_size: int, offset: int):
        if self.edge_type == Constants.NORTH:
            painter.drawLine(
                cell_size + self.sx + offset,
                cell_size + self.sy + offset,
                cell_size + self.ex - offset,
                cell_size + self.ey + offset
            )

        elif self.edge_type == Constants.EAST:
            painter.drawLine(
                cell_size + self.sx - offset,
                cell_size + self.sy + offset,
                cell_size + self.ex - offset,
                cell_size + self.ey - offset
            )

        elif self.edge_type == Constants.SOUTH:
            painter.drawLine(
                cell_size + self.sx + offset,
                cell_size + self.sy - offset,
                cell_size + self.ex - offset,
                cell_size + self.ey - offset
            )

        else:
            painter.drawLine(
                cell_size + self.sx + offset,
                cell_size + self.sy + offset,
                cell_size + self.ex + offset,
                cell_size + self.ey - offset
            )


def tile_to_poly(cells: List[Cell], cell_size: int, selected: Set, inner_offset: int):
    edges = []

    selected = {QPoint(i % 9, i // 9) for i in selected}

    for cell in cells:
        cell.reset()

    for i in range(81):

        p = get_point(i)
        if p not in selected:
            continue

        north = QPoint(p.x(), p.y() - 1)
        north_east = QPoint(p.x() + 1, p.y() - 1)

        east = QPoint(p.x() + 1, p.y())
        south_east = QPoint(p.x() + 1, p.y() + 1)

        south = QPoint(p.x(), p.y() + 1)
        south_west = QPoint(p.x() - 1, p.y() + 1)

        west = QPoint(p.x() - 1, p.y())
        north_west = QPoint(p.x() - 1, p.y() - 1)

        if west not in selected:
            if cells[get_index(north)].edge_exists[Constants.WEST]:

                edges[cells[get_index(north)].edge_id[Constants.WEST]].ey += cell_size
                cells[i].edge_id[Constants.WEST] = cells[get_index(north)].edge_id[Constants.WEST]
                cells[i].edge_exists[Constants.WEST] = True

            else:

                sx = p.x() * cell_size
                sy = p.y() * cell_size
                ex, ey = sx, sy + cell_size
                edge = Edge(sx, sy, ex, ey, Constants.WEST)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[Constants.WEST] = edge.id_
                cells[i].edge_exists[Constants.WEST] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if south in selected and south_west in selected:
                edges[cells[i].edge_id[Constants.WEST]].ey += inner_offset * 2

            if north in selected and north_west in selected:
                edges[cells[i].edge_id[Constants.WEST]].sy -= inner_offset * 2

        if north not in selected:

            if (cells[get_index(west)].edge_exists[Constants.NORTH]
                and cells[get_index(p)].row == cells[
                    get_index(west)].row):  # Don't connect to row above

                edges[cells[get_index(west)].edge_id[Constants.NORTH]].ex += cell_size
                cells[i].edge_id[Constants.NORTH] = cells[get_index(west)].edge_id[Constants.NORTH]
                cells[i].edge_exists[Constants.NORTH] = True

            else:
                sx = p.x() * cell_size
                sy = p.y() * cell_size
                ex, ey = sx + cell_size, sy
                edge = Edge(sx, sy, ex, ey, Constants.NORTH)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[Constants.NORTH] = edge.id_
                cells[i].edge_exists[Constants.NORTH] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if east in selected and north_east in selected:
                edges[cells[i].edge_id[Constants.NORTH]].ex += inner_offset * 2

            if west in selected and north_west in selected:
                edges[cells[i].edge_id[Constants.NORTH]].sx -= inner_offset * 2

        if east not in selected:
            if cells[get_index(north)].edge_exists[Constants.EAST]:
                edges[cells[get_index(north)].edge_id[Constants.EAST]].ey += cell_size
                cells[i].edge_id[Constants.EAST] = cells[get_index(north)].edge_id[Constants.EAST]
                cells[i].edge_exists[Constants.EAST] = True

            else:
                sx = (1 + p.x()) * cell_size
                sy = p.y() * cell_size
                ex, ey = sx, sy + cell_size
                edge = Edge(sx, sy, ex, ey, Constants.EAST)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[Constants.EAST] = edge.id_
                cells[i].edge_exists[Constants.EAST] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if north in selected and north_east in selected:
                edges[cells[i].edge_id[Constants.EAST]].sy -= inner_offset * 2

            if south in selected and south_east in selected:
                edges[cells[i].edge_id[Constants.EAST]].ey += inner_offset * 2

        if south not in selected:
            if (cells[get_index(west)].edge_exists[Constants.SOUTH]
                and cells[get_index(p)].row == cells[
                    get_index(west)].row):  # Don't connect to row above

                edges[cells[get_index(west)].edge_id[Constants.SOUTH]].ex += cell_size
                cells[i].edge_id[Constants.SOUTH] = cells[get_index(west)].edge_id[Constants.SOUTH]
                cells[i].edge_exists[Constants.SOUTH] = True

            else:
                sx = p.x() * cell_size
                sy = (1 + p.y()) * cell_size
                ex, ey = sx + cell_size, sy
                edge = Edge(sx, sy, ex, ey, Constants.SOUTH)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[Constants.SOUTH] = edge.id_
                cells[i].edge_exists[Constants.SOUTH] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if east in selected and south_east in selected:
                edges[cells[i].edge_id[Constants.SOUTH]].ex += inner_offset * 2

            if west in selected and south_west in selected:
                edges[cells[i].edge_id[Constants.SOUTH]].sx -= inner_offset * 2

    return edges


def get_index(p: QPoint) -> int:
    return p.y() * 9 + p.x()


def get_point(index: int) -> QPoint:
    return QPoint(index % 9, index // 9)


def valid(p: QPoint) -> bool:
    return 0 <= p.y() * 9 + p.x() <= 81


class Sudoku:
    NUMBERS = Constants.NUMBERS

    def __init__(
        self,
        size: int = 9,
        **kwargs
    ):

        self.size = size
        self.cells = [Cell(self, i) for i in range(size ** 2)]

        self.initial_state = copy.deepcopy(self.cells)
        self.board_copy = copy.deepcopy(self.cells)

        self.solve_board = True

        self.diagonal_positive = False
        self.diagonal_negative = False

        self.antiking = False
        self.antiknight = False

        self.disjoint_groups = False
        self.nonconsecutive = False

        self.lines_components = BoundList()
        self.border_components = BoundList()
        self.cell_components = BoundList()
        self.region_components = BoundList()
        self.outside_components = BoundList()

        self.brute_force_time = 60

        for kw, value in kwargs.items():

            if kw in self.constraints:
                setattr(self, kw, value)

    def __repr__(self):
        out = ""
        for i in range(self.size * self.size):
            if i != 0 and i % self.size == 0:
                out += '\n'
            out += f"{self.cells[i]}  "
        return out

    def __eq__(self, other):
        if isinstance(other, Sudoku):
            return self.to_string() == other.to_string()

    def to_string(self) -> str:
        return ''.join([str(c.value) for c in self.cells])

    def to_table(self) -> List[List[int]]:
        return [self.values(self.get_row(i)) for i in range(9)]

    @classmethod
    def from_string(cls, board_str: str):
        """

        :param board_str: A string containing information about values of cells
        :return: Sudoku where cell i holds the value of the string at index i
        """
        new_sudoku = cls()
        for i, value in enumerate(board_str):
            new_sudoku.cells[i].value = int(value) if value != "0" else Constants.EMPTY
        return new_sudoku

    @classmethod
    def blank(cls, size: int = 9):
        """

        :param size: Width and height of the Sudoku
        :return: A blank Sudoku with size x size empty cells
        """
        new_sudoku = cls(size=size)
        for cell in new_sudoku.cells:
            cell.value = Constants.EMPTY
        return new_sudoku

    def get_coordinate_1D(self, row: int, column: int) -> int:
        """
        Returns the Index associated with a given Row and Column..
        :param row:
        :param column:
        :return: Index
        """
        return row * self.size + column

    def get_coordinate_2D(self, index: int) -> Tuple[int, int]:
        """
        Returns the Row and Column associated with a given index.
        :param index: Coordinate of a Cell
        :return: Row, Column
        """
        return index // self.size, index % self.size

    def is_valid(self, index: int, offset: int) -> bool:
        """

        :param index: index being checked
        :param offset: offset from the index being checked e.g. index = 4 offset = 1 -> checking 5
        :return: index in bounds of the grid
        """
        return 0 <= index + offset < self.size ** 2 and not self.is_exclusion(index, offset)

    def is_exclusion(self, index: int, offset: int) -> bool:
        """

        Exclusions are "edge" cases. E.g. Cell 9 has no left neighbours because the 8th Cell is
        in the row above on the other side of the grid but index 9 - offset 1 = 8 would return
        true in the is_valid method. These cases are being checked here and excluded in the Cells
        neighours.

        :param index: index being checked
        :param offset: offset from the index being checked e.g. index = 4 offset = 1 -> checking 5
        :return: index in bounds of the grid
        """

        return (
            index % self.size == 0 and offset in (-19, -11, -10, -1, 7, 8, 17)  # Column 1
            or index % self.size == 1 and offset in (-11, 7)  # Column 2
            or index % self.size == self.size - 2 and offset in (-7, 11)  # Column 7
            or index % self.size == self.size - 1 and offset in (
                -17, -8, -7, 1, 10, 11, 19)  # Column 8
            or index // self.size == 0 and offset in (-10, -9, -8)
            or index // self.size == self.size - 1 and offset in (8, 9, 10)
        )

    def get_row(self, index: int) -> List[Cell]:
        """

        :param index: Index of a cell
        :return: Full List of all Cells in the cell's row
        """
        row_start = index // 9 * 9
        row_end = row_start + 9
        return self.cells[row_start:row_end]

    def get_column(self, index: int) -> List[Cell]:
        """

        :param index: Index of a cell
        :return: Full list of all cells in the cell's column
        """
        col_start = index % 9
        return [self.cells[i] for i in range(col_start, col_start + 81, 9)]

    def get_box(self, index: int) -> List[Cell]:
        """

        :param index: Index of a cell
        :return: Full List of all Cells in the cell's box
        """
        cell = self.cells[index]
        box_x = cell.row // 3 * 3 * self.size
        box_y = cell.column // 3 * 3

        start = box_x + box_y
        box = [self.cells[start + i * self.size: start + 3 + i * self.size] for i in range(3)]
        return list(itertools.chain(*box))

    def get_index_of_box(self, index: int) -> int:
        """

        :param index: Index of a cell in the Sudoku
        :return: Index of the box this cell is part of
        """
        row, column = index // self.size, index % self.size

        box_x = (row // 3) * 3 * self.size
        box_y = column // 3 * 3
        return (box_y * self.size // 3 + box_x) // self.size

    def get_cell(self, index: int) -> Cell:
        return self.cells[index]

    def get_positive_diagonal(self) -> List[Cell]:
        """

        :return: Full List of cells on the positive diagonal (bottom left to top right)
        """
        return self.get_diagonal(self.size - 1, (1, -1))

    def get_negative_diagonal(self) -> List[Cell]:
        """

        :return: Full List of cells on the positive diagonal (top left to bottom right)
        """
        return self.get_diagonal(0, (1, 1))

    def get_diagonal(self, start: int, direction: Tuple[int, int]) -> List[Cell]:
        """

        :param start: Index of the cell the diagonal should start at
        :param direction: Tuple of tow integers that indicate the vertical and horizontal direction
        :return: Full List of cells that on that diagonal
        """
        row, col = self.get_coordinate_2D(start)
        cells = []

        while 0 <= row <= self.size - 1 and 0 <= col <= self.size - 1:
            cells.append(self.get_cell(row * self.size + col))
            row += direction[0]
            col += direction[1]

        return cells

    def get_disjoint_group(self, index: int) -> List[Cell]:
        """

        :param index: Index of a cell
        :return: Full List of all Cells in the cell's disjoint group (relative position in the box)
        """

        r, c = self.get_coordinate_2D(index)
        offset = (r % 3 * 9) + (c % 3)

        indices = [
            offset + i * self.size * 3 + x * self.size // 3
            for i in range(3)
            for x in range(3)
        ]

        return [self.cells[ix] for ix in indices]

    def get_empty(self) -> Cell | None:
        """

        :return: The first empty cell in the Sudoku
        """
        cells = list(filter(lambda c: c.is_empty, self.cells))

        if not cells:
            return None

        return sorted(cells, key=lambda c: len(c.valid_numbers))[0]

    @staticmethod
    def indices(cells: List[Cell]) -> List[int]:
        """
        Convenience method to get all indices in a list of cells

        :param cells: A List of cell objects
        :return: Full List of indices that these cell objects have
        """
        return [cell.index for cell in cells]

    @staticmethod
    def values(cells: List[Cell]) -> List[int]:
        """
        Convenience method to get all values in a list of cells

        :param cells: A List of cell objects
        :return: Full List of values that these cell objects have
        """
        return [cell.value for cell in cells]

    def solve_in_thread(self, solver: QObject, random_pick: bool = False) -> bool:
        """
        Solve the sudoku using a thread to get updates for the GUI

        :param solver: QObject that is connected to a thread and sends updates to the Application
        :param random_pick: Should a number be tested at random or in order
        :return: If Sudoku is solved
        """
        if self.brute_force_time == 0:
            return False

        self.calculate_valid_numbers()
        cell = self.get_empty()

        solver.progressChanged.emit()
        time.sleep(1 / solver.speed)

        if cell is None:
            return True

        numbers = cell.valid_numbers
        if random_pick:
            random.shuffle(numbers)

        for number in numbers:
            cell.value = number

            if self.solve_in_thread(solver, random_pick):
                return True

            cell.value = Constants.EMPTY
        return False

    def solve(self, random_pick: bool = False):
        """
        Solve the Sudoku via backtracking.

        :param random_pick: Should a number be tested at random or in order
        :return: If Sudoku is solved
        """
        if self.brute_force_time == 0:
            return False

        self.calculate_valid_numbers()
        cell = self.get_empty()

        if cell is None:
            return True

        numbers = cell.valid_numbers
        if random_pick:
            random.shuffle(numbers)

        for number in numbers:
            cell.value = number

            if self.solve(random_pick):
                return True

            cell.value = Constants.EMPTY
        return False

    def check_number(self, index: int, number: int) -> bool:
        """

        :param index: Index of the cell being checked
        :param number: The number being checked
        :return: LogicResult indicating if the number can be placed in the cell
        """

        cell_to_check = self.get_cell(index)

        if self.diagonal_positive and index in self.indices(ix := self.get_positive_diagonal()):
            for cell in ix:
                if cell.value == number:
                    return False

        if self.diagonal_negative and index % (self.size + 1) == 0:
            for cell in self.get_negative_diagonal():
                if cell.value == number:
                    return False

        if self.antiknight:
            for cell in cell_to_check.knight_neighbours:
                if cell.value == number:
                    return False

        if self.antiking:
            for cell in cell_to_check.neighbours:
                if cell.value == number:
                    return False
        if self.disjoint_groups:
            for cell in self.get_disjoint_group(index):
                if cell.value == number:
                    return False

        if self.nonconsecutive:
            for cell in cell_to_check.orthogonal_neighbours:
                if cell.value != Constants.EMPTY and cell.value in (number - 1, number + 1):
                    return False

        for cell in self.get_row(index):
            if cell.value == number:
                return False

        for cell in self.get_column(index):
            if cell.value == number:
                return False

        for cell in self.get_box(index):
            if cell.value == number:
                return False

        for line in self.lines_components:
            if not line.valid(index, number):
                return False

        for border_cmp in self.border_components:
            if index not in border_cmp.indices: continue

            if not border_cmp.valid(index, number):
                return False

        for out_cmp in self.outside_components:
            if not out_cmp.valid(index, number):
                return False

        for reg_cmp in self.region_components:
            if not reg_cmp.valid(index, number):
                return False

        for cell_cmp in self.cell_components:
            if index != cell_cmp.index:
                continue

            if not cell_cmp.valid(index, number):
                return False

        return True

    def check_numbers(self, index: int) -> List[int]:
        """

        :param index: Index of cell being checked for valid candidates
        :return: List of valid numbers for that cell
        """
        return [
            number for number in self.NUMBERS
            if self.check_number(index, number)
               and self.cells[index].is_empty
        ]

    def valid(self, number: int, index: int, show_constraints: bool = False):

        show_constraint = show_constraints

        if self.disjoint_groups:
            for cell in self.get_disjoint_cells(index):
                if cell.value == number:
                    return False

        if self.antiking:
            for cell in self.get_king_neighbours(index):

                if cell.value == number:
                    if show_constraint: print(number, "KINGS MOVE APART FROM", cell.value, "in",
                                              cell.index)

                    return False

        if self.antiknight:
            for cell in self.get_knight_neighbours(index):
                if cell.value == number:
                    if show_constraint: print(number, "KNIGHTS MOVE APART FROM", cell.value, "in",
                                              cell.index)
                    return False

        if self.nonconsecutive:
            consecutives = {number - 1, number + 1}.intersection({1, 2, 3, 4, 5, 6, 7, 8, 9})
            for cell in self.get_orthogonals(index):
                if cell.value in consecutives:

                    if show_constraint:
                        print(number, "CONSECUTIVE WITH", cell.value, "in", cell.index)
                    return False

        if self.diagonal_negative:
            if index in [c.index for c in self.get_diagonal_top_left()]:

                for cell in self.get_diagonal_top_left():

                    if cell.value == number:
                        if show_constraint:
                            print(number, "TWICE ON DIAGONAL TOP LEFT")
                        return False

        if self.diagonal_positive:
            if index in [c.index for c in self.get_diagonal_top_right()]:
                for cell in self.get_diagonal_top_right():
                    if cell.value == number:
                        if show_constraint:
                            print(number, "TWICE ON DIAGONAL TOP RIGHT")
                        return False

        for line in self.lines_components:
            if not line.valid(index, number):
                return False

        for border_cmp in self.border_components:
            if index not in border_cmp.indices: continue

            if not border_cmp.valid(index, number):
                return False

        for out_cmp in self.outside_components:
            if not out_cmp.valid(index, number):
                return False

        for reg_cmp in self.region_components:
            if not reg_cmp.valid(index, number):
                return False

        for cell in self.get_entire_row(index):
            if cell.value == number:
                if show_constraint: print(number, "TWICE IN ROW", cell.row)
                return False

        for cell in self.get_entire_column(index):
            if cell.value == number:
                if show_constraint: print(number, "TWICE IN COLUMN", cell.column)
                return False

        for cell in self.get_entire_box(index):
            if cell.value == number:
                if show_constraint: print(number, "TWICE IN BOX")
                return False

        for cell_cmp in self.cell_components:
            if index != cell_cmp.index:
                continue

            if not cell_cmp.valid(index, number):
                return False

        return True

    def valid_numbers(self, index: int, show: bool = False):

        return [number for number in self.NUMBERS if
                self.valid(number, index) and self.cells[index].is_empty]

    def all_valid_numbers(self):
        return sorted([(index, self.valid_numbers(index)) for index in range(81)],
                      key=lambda tpl: len(tpl[1]))

    @property
    def board_constraints(self):
        return itertools.chain.from_iterable(
            [
                self.lines_components,
                self.border_components,
                self.cell_components,
                self.region_components,
                self.outside_components
            ]
        )

    @property
    def constraints(self) -> Dict[str, bool]:
        return {
            "diagonal_positive": self.diagonal_positive,
            "diagonal_negative": self.diagonal_negative,
            "antiknight": self.antiknight,
            "antiking": self.antiking,
            "disjoint_groups": self.disjoint_groups,
            "nonconsecutive": self.nonconsecutive
        }

    def start_process(self):
        thread = StoppableThread(target=self.brute_force_countdown)
        thread.start()

    def brute_force_countdown(self):
        while self.brute_force_time > 0:
            self.brute_force_time -= 1
            time.sleep(1)

    def to_file(self):
        import json
        filename, ext = QFileDialog.getSaveFileName(dir=os.getcwd() + "/puzzles", filter="(*.json)")

        data = {

            "digits": ''.join(str(cell.value) for cell in self.cells),
            "constraints": {
                "diagonal_positive": self.diagonal_positive,
                "diagonal_negative": self.diagonal_negative,
                "antiknight": self.antiknight,
                "antiking": self.antiking,
                "disjoint_groups": self.disjoint_groups,
                "nonconsecutive": self.nonconsecutive
            },
            "negative_constraints": {
                "ratio": False,
                "XV": False
            },
            "components": {
                "lines": [line.to_json() for line in self.lines_components],
                "border": [cmp.to_json() for cmp in self.border_components],
                "cells": [cell_cmp.to_json() for cell_cmp in self.cell_components],
                "regions": [region_cmp.to_json() for region_cmp in self.region_components],
                "outside": [outside_cmp.to_json() for outside_cmp in self.outside_components]
            }

        }

        with open(filename, "w") as file:
            json.dump(data, file, indent=2)

    def from_file(self, file_path: str = None):
        import json

        from constraints import border_components, cell_components, outside_components, \
            line_components, region_components

        if file_path is None:
            path, extension = QFileDialog.getOpenFileName(dir=os.getcwd(), filter="(*.json)")
        else:
            path = file_path

        self.lines_components.clear()
        self.border_components.clear()
        self.cell_components.clear()
        self.region_components.clear()
        self.outside_components.clear()

        with open(path, "r") as file:
            data = json.load(file)
            for i in range(81):
                self.initial_state[i].value = int(data["digits"][i])
                self.cells[i].value = int(data["digits"][i])
                self.cells[i].valid_numbers = BoundList(sort_=True)
                self.cells[i].corner = BoundList(max_length=4, sort_=True)
                self.cells[i].colors = BoundList(max_length=4, sort_=True)

            for key, val in data["constraints"].items():
                setattr(self, key, val)

            for item in data["components"]["border"]:
                match item["type"]:

                    case "XVSum":
                        obj = border_components.XVSum(self, item["indices"], item["total"])

                    case "Difference":
                        obj = border_components.Difference(self, item["indices"],
                                                           item["difference"])

                    case "Ratio":
                        obj = border_components.Ratio(self, item["indices"], item["ratio"])

                    case "Quadruple":
                        obj = border_components.Quadruple(self, item["indices"],
                                                          BoundList(max_length=4))
                        for val in item["numbers"]:
                            obj.numbers.append(val)

                    case "LessGreater":
                        obj = border_components.LessGreater(self, item["indices"], item["less"])

                self.border_components.append(obj)

            for item in data["components"]["cells"]:
                match item["type"]:

                    case "EvenDigit":
                        obj = cell_components.EvenDigit(self, item["index"])
                        self.cell_components.append(obj)

                    case "OddDigit":
                        obj = cell_components.OddDigit(self, item["index"])
                        self.cell_components.append(obj)

            for item in data["components"]["lines"]:
                match item["type"]:

                    case "Arrow":
                        obj = line_components.Arrow(self, BoundList())
                        obj.setup(item["index"])

                        for branch in item["branches"]:
                            obj.branches.append([self.cells[ix] for ix in branch])

                        self.lines_components.append(obj)

                    case "Thermometer":
                        obj = line_components.Thermometer(self, BoundList())
                        obj.setup(item["index"])

                        for branch in item["branches"]:
                            obj.branches.append([self.cells[ix] for ix in branch])

                        self.lines_components.append(obj)

                    case "LockoutLine":
                        obj = line_components.LockoutLine(self, BoundList())
                        obj.setup(item["index"])

                        for branch in item["branches"]:
                            obj.branches.append([self.cells[ix] for ix in branch])

                        self.lines_components.append(obj)

                    case "BetweenLine":
                        obj = line_components.BetweenLine(self, BoundList())
                        obj.setup(item["index"])

                        for branch in item["branches"]:
                            obj.branches.append([self.cells[ix] for ix in branch])

                        self.lines_components.append(obj)

                    case "PalindromeLine":
                        obj = line_components.PalindromeLine(self, BoundList(item["indices"]))
                        self.lines_components.append(obj)

                    case "GermanWhispersLine":
                        obj = line_components.GermanWhispersLine(self, BoundList(item["indices"]))
                        self.lines_components.append(obj)

            for item in data["components"]["outside"]:
                match item["type"]:
                    case "Sandwich":
                        obj = outside_components.Sandwich(self, item["col"], item["row"],
                                                          item["total"])
                        self.outside_components.append(obj)

                    case "XSumsClue":
                        obj = outside_components.XSumsClue(self, item["col"], item["row"],
                                                           item["total"])
                        self.outside_components.append(obj)

                    case "LittleKiller":
                        obj = outside_components.LittleKiller(self, item["col"], item["row"],
                                                              item["total"], item["direction"])
                        self.outside_components.append(obj)

            for item in data["components"]["regions"]:
                match item["type"]:
                    case "Cage":
                        self.region_components.append(region_components.Cage.from_json(self, item))

    @property
    def boxes(self):
        return [self.get_entire_box(i) for i in [0, 3, 6, 27, 30, 33, 54, 57, 60]]

    @property
    def rows(self):
        return [self.get_row(i) for i in range(0, self.size * self.size, self.size)]

    @property
    def columns(self):
        return [self.get_column(i) for i in range(self.size)]

    def get_entire_row(self, index: int):

        board_to_search = self.cells if self.solve_board else self.board_copy

        row_start = index // 9 * 9
        row_end = row_start + 9
        return board_to_search[row_start:row_end]

    def get_entire_column(self, index: int):
        board_to_search = self.cells if self.solve_board else self.board_copy

        col_start = index % 9
        return [board_to_search[i] for i in range(col_start, col_start + 81, 9)]

    def get_entire_box(self, index: int):
        board_to_search = self.cells if self.solve_board else self.board_copy

        cell = board_to_search[index]
        box_x = cell.row // 3 * 3 * 9
        box_y = cell.column // 3 * 3

        start = box_x + box_y
        box = [board_to_search[start + i * 9: start + 3 + i * 9] for i in range(3)]
        return list(itertools.chain(*box))

    def get_zones(self, index: int):
        return self.get_entire_row(index) + self.get_entire_column(index) + self.get_entire_box(
            index)

    def get_king_neighbours(self, index: int):
        board_to_search = self.cells if self.solve_board else self.board_copy

        offsets = (-10, -9, -8, -1, 1, 8, 9, 10)
        cell = board_to_search[index]
        neighbours = []

        for offset in offsets:

            if index + offset > 80 or index + offset < 0:
                continue

            if cell.column == 0 and offset in (-10, -1, 8):
                continue

            if cell.column == 8 and offset in (-8, 1, 10):
                continue

            neighbours.append(board_to_search[index + offset])

        return neighbours

    def get_knight_neighbours(self, index: int):
        board_to_search = self.cells if self.solve_board else self.board_copy

        offsets = (-19, -17, -11, -7, 7, 11, 17, 19)
        cell = board_to_search[index]
        neighbours = []

        for offset in offsets:

            if index + offset > 80 or index + offset < 0:
                continue

            if cell.column == 0 and offset in (-19, -11, 7, 17):
                continue

            if cell.column == 1 and offset in (-11, 7):
                continue

            if cell.column == 7 and offset in (-7, 11):
                continue

            if cell.column == 8 and offset in (-17, -7, 11, 19):
                continue

            neighbours.append(board_to_search[index + offset])

        return neighbours

    def get_orthogonals(self, index: int):
        board_to_search = self.cells if self.solve_board else self.board_copy

        offsets = (-9, -1, 1, 9)
        orthogonal = []
        cell = board_to_search[index]

        for offset in offsets:
            if index + offset > 80 or index + offset < 0:
                continue

            if cell.column == 0 and offset == -1:
                continue

            if cell.column == 8 and offset == 1:
                continue

            orthogonal.append(board_to_search[index + offset])

        return orthogonal

    def get_diagonal_top_left(self):
        board_to_search = self.cells if self.solve_board else self.board_copy

        return [board_to_search[i * 10] for i in range(9)]

    def get_diagonal_top_right(self):
        board_to_search = self.cells if self.solve_board else self.board_copy

        return [board_to_search[i * 8] for i in range(1, 10)]

    def get_disjoint_cells(self, index: int):
        this_box = self.get_entire_box(index)
        box_index = [cell.index for cell in this_box].index(index)

        return [box[box_index] for box in self.boxes]

    def sees(self, index: int):

        cell = self.cells[index]

        neighbours = list(itertools.chain.from_iterable(
            [self.get_row(index), self.get_column(index), self.get_box(index)]
        ))

        if self.antiknight:
            neighbours += cell.knight_neighbours

        if self.antiking:
            neighbours += cell.neighbours

        if self.disjoint_groups:
            neighbours += self.get_disjoint_group(index)

        if self.diagonal_positive and cell in (plus := self.get_positive_diagonal()):
            neighbours += plus

        if self.diagonal_negative and cell in (neg := self.get_negative_diagonal()):
            neighbours += neg

        return set(neighbours)

    def look_for_pairs(self, cells: List[Cell]):
        nothing_found = False
        removed = []

        while not nothing_found:
            restrictions = []

            amounts = {}

            for cell in cells:
                if not cell.is_empty: continue

                if ''.join(map(str, cell.valid_numbers)) not in amounts:
                    amounts[''.join(map(str, cell.valid_numbers))] = [cell]
                else:
                    amounts[''.join(map(str, cell.valid_numbers))].append(cell)

            for key, val in amounts.items():
                if len(key) == len(val) != 1 and key not in removed:
                    restrictions.append((key, val))
                    removed.append(key)

            for restriction in restrictions:
                for cell in cells:
                    if cell not in restriction[1]:
                        for val in restriction[0]:
                            if int(val) in cell.valid_numbers:
                                cell.valid_numbers.remove(int(val))

            if len(restrictions) == 0:
                nothing_found = True

    def calculate_valid_numbers(self):
        for cell in self.cells:
            if not cell.is_empty:
                continue
            cell.valid_numbers = self.check_numbers(cell.index)

        """for box in self.boxes:
            self.look_for_pairs(box)

        for row in self.rows:
            self.look_for_pairs(row)

        for column in self.columns:
            self.look_for_pairs(column)"""
