from __future__ import annotations
import copy
import itertools
import math
import multiprocessing
import os
import random
import sys
import threading
import time
from typing import List, Optional, Set, Tuple

import numpy as np
from PySide6.QtCore import QPoint, QRect, QTimer
from PySide6.QtGui import QPainter, QPolygon
from PySide6.QtWidgets import QFileDialog

from utils import StoppableThread, uniquify

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3


class Cell:
    def __init__(self, index: int, value: int = 0):
        self.index = index

        self.valid_numbers = []
        self.corner = []
        self.value = value
        self.color = None

        self.impossible_numbers = []

        self.edge_id = [0, 0, 0, 0]
        self.edge_exists = [False, False, False, False]

    @property
    def row(self):
        return self.index // 9

    @property
    def column(self):
        return self.index % 9

    def rect(self, cell_size: int):
        return QRect(
            self.column * cell_size + cell_size,
            self.row * cell_size + cell_size,
            cell_size,
            cell_size
        )

    def scaled_rect(self, cell_size: int, factor: float = 1):
        shift_by = int(cell_size - (cell_size * factor)) // 2
        return QRect(
            self.column * cell_size + cell_size + shift_by,
            self.row * cell_size + cell_size + shift_by,
            int(cell_size * factor),
            int(cell_size * factor)
        )

    def __repr__(self):
        return f"Cell({self.index}, {self.value})"

    def reset(self):
        self.edge_id = [0, 0, 0, 0]
        self.edge_exists = [False, False, False, False]

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value


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
        if self.edge_type == NORTH:
            painter.drawLine(
                cell_size + self.sx + offset,
                cell_size + self.sy + offset,
                cell_size + self.ex - offset,
                cell_size + self.ey + offset
            )

        elif self.edge_type == EAST:
            painter.drawLine(
                cell_size + self.sx - offset,
                cell_size + self.sy + offset,
                cell_size + self.ex - offset,
                cell_size + self.ey - offset
            )

        elif self.edge_type == SOUTH:
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
            if cells[get_index(north)].edge_exists[WEST]:

                edges[cells[get_index(north)].edge_id[WEST]].ey += cell_size
                cells[i].edge_id[WEST] = cells[get_index(north)].edge_id[WEST]
                cells[i].edge_exists[WEST] = True

            else:

                sx = p.x() * cell_size
                sy = p.y() * cell_size
                ex, ey = sx, sy + cell_size
                edge = Edge(sx, sy, ex, ey, WEST)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[WEST] = edge.id_
                cells[i].edge_exists[WEST] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if south in selected and south_west in selected:
                edges[cells[i].edge_id[WEST]].ey += inner_offset * 2

            if north in selected and north_west in selected:
                edges[cells[i].edge_id[WEST]].sy -= inner_offset * 2

        if north not in selected:

            if (cells[get_index(west)].edge_exists[NORTH]
                and cells[get_index(p)].row == cells[
                    get_index(west)].row):  # Don't connect to row above

                edges[cells[get_index(west)].edge_id[NORTH]].ex += cell_size
                cells[i].edge_id[NORTH] = cells[get_index(west)].edge_id[NORTH]
                cells[i].edge_exists[NORTH] = True

            else:
                sx = p.x() * cell_size
                sy = p.y() * cell_size
                ex, ey = sx + cell_size, sy
                edge = Edge(sx, sy, ex, ey, NORTH)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[NORTH] = edge.id_
                cells[i].edge_exists[NORTH] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if east in selected and north_east in selected:
                edges[cells[i].edge_id[NORTH]].ex += inner_offset * 2

            if west in selected and north_west in selected:
                edges[cells[i].edge_id[NORTH]].sx -= inner_offset * 2

        if east not in selected:
            if cells[get_index(north)].edge_exists[EAST]:
                edges[cells[get_index(north)].edge_id[EAST]].ey += cell_size
                cells[i].edge_id[EAST] = cells[get_index(north)].edge_id[EAST]
                cells[i].edge_exists[EAST] = True

            else:
                sx = (1 + p.x()) * cell_size
                sy = p.y() * cell_size
                ex, ey = sx, sy + cell_size
                edge = Edge(sx, sy, ex, ey, EAST)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[EAST] = edge.id_
                cells[i].edge_exists[EAST] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if north in selected and north_east in selected:
                edges[cells[i].edge_id[EAST]].sy -= inner_offset * 2

            if south in selected and south_east in selected:
                edges[cells[i].edge_id[EAST]].ey += inner_offset * 2

        if south not in selected:
            if (cells[get_index(west)].edge_exists[SOUTH]
                and cells[get_index(p)].row == cells[
                    get_index(west)].row):  # Don't connect to row above

                edges[cells[get_index(west)].edge_id[SOUTH]].ex += cell_size
                cells[i].edge_id[SOUTH] = cells[get_index(west)].edge_id[SOUTH]
                cells[i].edge_exists[SOUTH] = True

            else:
                sx = p.x() * cell_size
                sy = (1 + p.y()) * cell_size
                ex, ey = sx + cell_size, sy
                edge = Edge(sx, sy, ex, ey, SOUTH)

                edge.id_ = len(edges)
                edges.append(edge)

                cells[i].edge_id[SOUTH] = edge.id_
                cells[i].edge_exists[SOUTH] = True

            # Fill the gap if a cell corner is shifted by a given offset

            if east in selected and south_east in selected:
                edges[cells[i].edge_id[SOUTH]].ex += inner_offset * 2

            if west in selected and south_west in selected:
                edges[cells[i].edge_id[SOUTH]].sx -= inner_offset * 2

    return edges


def get_index(p: QPoint) -> int:
    return p.y() * 9 + p.x()


def get_point(index: int) -> QPoint:
    return QPoint(index % 9, index // 9)


def valid(p: QPoint) -> bool:
    return 0 <= p.y() * 9 + p.x() <= 81


class Sudoku:
    NUMBERS = (1, 2, 3, 4, 5, 6, 7, 8, 9)

    def __init__(
        self,
        board: List[Cell],
    ):

        self.initial_state = copy.deepcopy(board)
        self.board = board

        self.board_copy = copy.deepcopy(board)

        self.solve_board = True

        self.diagonal_positive = False
        self.diagonal_negative = False

        self.antiking = False
        self.antiknight = False

        self.disjoint_groups = False
        self.nonconsecutive = False

        self.cages: List["Cage"] = []

        self.lines = []
        self.border_constraints = []

        self.forced_odds: List[int] = []
        self.forced_evens: List[int] = []

        self.brute_force_time = 5

    def start_process(self):
        thread = StoppableThread(target=self.brute_force_countdown)
        thread.start()

    def brute_force_countdown(self):
        while self.brute_force_time > 0:
            self.brute_force_time -= 1
            time.sleep(1)

    @classmethod
    def from_file(cls):
        with open("sudokus.txt", "r") as f:
            index = random.randint(0, 49)
            index = index * 10 + 1

            data = f.readlines()

            lines = ''.join(list(itertools.chain(*data[index:index + 9])))
            lines = lines.replace("\n", "")
            empty = ""
            for c in lines:
                if c not in cls.NUMBERS:
                    empty = c
                    break

            lines = lines.replace(empty, "0")

            return cls.from_string(lines)

    @classmethod
    def from_string(cls, board_str: str):
        return cls([Cell(i, int(board_str[i])) for i in range(81)])

    def __repr__(self):
        out = ""

        for i in range(81):
            if i != 0 and i % 9 == 0:
                out += '\n'
            out += f"{self.board[i].value}  " if self.board[i].value in self.NUMBERS else "-  "
        return out

    def boxes(self):
        return [self.get_entire_box(i) for i in [0, 3, 6, 27, 30, 33, 54, 57, 60]]

    def rows(self):
        return [self.get_entire_row(i) for i in range(0, 81, 9)]

    def columns(self):
        return [self.get_entire_column(i) for i in range(9)]

    def next_empty(self) -> Optional[int]:

        board_to_search = self.board if self.solve_board else self.board_copy

        cells = sorted([cell for cell in board_to_search if cell.value == 0],
                       key=lambda c: len(c.valid_numbers))
        if not cells:
            return None

        return cells[0].index

    def get_entire_row(self, index: int):

        board_to_search = self.board if self.solve_board else self.board_copy

        row_start = index // 9 * 9
        row_end = row_start + 9
        return board_to_search[row_start:row_end]

    def get_entire_column(self, index: int):
        board_to_search = self.board if self.solve_board else self.board_copy

        col_start = index % 9
        return [board_to_search[i] for i in range(col_start, col_start + 81, 9)]

    def get_entire_box(self, index: int):
        board_to_search = self.board if self.solve_board else self.board_copy

        cell = board_to_search[index]
        box_x = cell.row // 3 * 3 * 9
        box_y = cell.column // 3 * 3

        start = box_x + box_y
        box = [board_to_search[start + i * 9: start + 3 + i * 9] for i in range(3)]
        return list(itertools.chain(*box))

    def get_king_neighbours(self, index: int):
        board_to_search = self.board if self.solve_board else self.board_copy

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
        board_to_search = self.board if self.solve_board else self.board_copy

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
        board_to_search = self.board if self.solve_board else self.board_copy

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
        board_to_search = self.board if self.solve_board else self.board_copy

        return [board_to_search[i * 10] for i in range(9)]

    def get_diagonal_top_right(self):
        board_to_search = self.board if self.solve_board else self.board_copy

        return [board_to_search[i * 8] for i in range(1, 10)]

    @property
    def sorted_empties(self):
        board_to_search = self.board if self.solve_board else self.board_copy

        return sorted([cell for cell in board_to_search if cell.value == 0],
                      key=lambda c: len(c.valid_numbers))

    def get_disjoint_cells(self, index: int):
        this_box = self.get_entire_box(index)
        box_index = [cell.index for cell in this_box].index(index)

        return [box[box_index] for box in self.boxes()]

    def sees(self, index: int):
        neighbours = self.get_entire_box(index) + self.get_entire_row(
            index) + self.get_entire_column(index)
        if self.antiknight:
            neighbours += self.get_knight_neighbours(index)

        if self.antiking:
            neighbours += self.get_king_neighbours(index)

        if self.disjoint_groups:
            neighbours += self.get_disjoint_cells(index)

        if self.diagonal_negative and index in [c.index for c in self.get_diagonal_top_left()]:
            neighbours += self.get_diagonal_top_left()

        if self.diagonal_positive and index in [c.index for c in self.get_diagonal_top_right()]:
            neighbours += self.get_diagonal_top_right()

        if self.nonconsecutive:
            for cell in self.board:
                if cell.value not in (self.board[index].value + 1, self.board[index].value - 1):
                    continue

                neighbours += self.get_orthogonals(cell.index)

        return set(neighbours)

    def next_step(self):

        self.calculate_valid_numbers()

        empty_cells = self.sorted_empties

        if not empty_cells:
            print("DONE")
            return None

        best_cell = empty_cells[0]

        if len(best_cell.valid_numbers) == 1:
            best_cell.value = best_cell.valid_numbers[0]
            self.calculate_valid_numbers()
            return best_cell.index

        valids = best_cell.valid_numbers.copy()
        board_before = copy.deepcopy(self.board)

        for number in best_cell.valid_numbers:
            best_cell.value = number

            self.calculate_valid_numbers()

            if not self.solve():
                valids.remove(number)
                self.board = copy.deepcopy(board_before)

        best_cell.valid_numbers = valids

        return None

    def calculate_valid_numbers(self):
        for cell in self.board:
            cell.valid_numbers = self.valid_numbers(cell.index)

    def try_solve(self):
        before = copy.deepcopy(self.board)
        possible = self.solve()

        self.board = before
        return possible

    def solve(self):
        if self.brute_force_time == 0:
            return False

        self.calculate_valid_numbers()
        index = self.next_empty()

        if index is None:
            return True

        cell = self.board[index]

        for number in cell.valid_numbers:
            cell.value = number

            if self.solve():
                return True

            cell.value = 0
        return False

    def valid(self, number: int, index: int, show_constraints: bool = False):

        board_to_search = self.board if self.solve_board else self.board_copy

        show_constraint = show_constraints

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

        if index in self.forced_odds and number % 2 == 0:
            if show_constraint:
                print("Cell", index, "MUST BE ODD")
            return False

        if index in self.forced_evens and number % 2 != 0:
            if show_constraint:
                print("Cell", index, "MUST BE EVEN")
            return False

        if self.disjoint_groups:
            this_box = self.get_entire_box(index)
            box_index = [cell.index for cell in this_box].index(index)

            for box in self.boxes():

                values = [cell.value for cell in box]

                if number not in values: continue

                if this_box == box: continue

                if (y := values.index(number)) == box_index:
                    if show_constraint:
                        contradicting_index = y
                        print(number, "ALREADY IN ANOTHER BOX AT BOX POSITION",
                              box_index, f"({contradicting_index})")
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

        for cage in self.cages:
            if index not in cage.cells: continue

            if not cage.valid(board_to_search, number, show_constraint=show_constraints):
                return False

        for line in self.lines:
            if index not in line.indices: continue

            if not line.valid(index, number):
                return False
        for dot in self.border_constraints:
            if index not in dot.indices: continue

            if not dot.valid(index, number):
                return False

        return True

    def valid_numbers(self, index: int, show: bool = False):
        return [number for number in self.NUMBERS if
                self.valid(number, index, show_constraints=show) and self.board[
                    index].value not in self.NUMBERS]

    def all_valid_numbers(self):
        return sorted([(index, self.valid_numbers(index)) for index in range(81)],
                      key=lambda tpl: len(tpl[1]))

    @classmethod
    def blank(cls):
        return Sudoku.from_string(
            "0" * 81
        )

    def to_file(self):
        import json
        folder = QFileDialog.getExistingDirectory(dir=os.getcwd())
        data = {

            "digits": [''.join(str(cell.value) for cell in self.get_entire_row(i)) for i in
                       range(0, 81, 9)],
            "constraints": {
                "diagonal_pos": self.diagonal_positive,
                "diagonal_neg": self.diagonal_negative,
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
                "lines": [line.to_json() for line in self.lines],
                "dots": [dot.to_json() for dot in self.border_constraints],
                "cages": [cage.to_json() for cage in self.cages],
                "odds": self.forced_odds,
                "evens": self.forced_evens
            }

        }

        path = uniquify(folder + "/sudoku.json")
        with open(path, "w") as file:
            json.dump(data, file, indent=2)
