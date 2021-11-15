from __future__ import annotations

import copy
import itertools
import os
import time
from typing import List, Optional, Set

from PySide6.QtCore import QPoint, QRect, Qt, QThread, QObject
from PySide6.QtGui import QPainter, QPolygon, QColor
from PySide6.QtWidgets import QFileDialog

from utils import StoppableThread, SmartList

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3


class Cell:
    def __init__(self, index: int, value: int = 0):
        self.index = index

        self.valid_numbers = SmartList(sort_=True)
        self.corner = SmartList(max_length=4, sort_=True)
        self.value = value
        self.colors = SmartList(max_length=4, sort_=True)

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

    def scaled_rect(self, cell_size: int, factor: float = 1) -> QRect:
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

    def reset_values(self, skip_value: bool = False):
        if not skip_value:
            self.value = 0
        self.valid_numbers.clear()
        self.corner.clear()
        self.colors.clear()

    @property
    def neighbours(self) -> List[int]:
        indices = [-10, -9, -8, -1, 1, 8, 9, 10]

        return [self.index + n for n in indices if self.is_neighbour(n)]

    def is_neighbour(self, offset: int):
        if not 0 <= self.index + offset <= 80:
            return False

        if self.index % 9 == 0 and offset in (-10, -1, 8):
            return False

        if self.index % 9 == 8 and offset in (-8, 1, 10):
            return False

        return True

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
                self.valid_numbers.append(value)

            case 2:  # CORNER
                self.corner.append(value)

            case 3:  # COLOR
                self.colors.append(COLORS[value - 1])

    def clear_values(self, sudoku: Sudoku, mode: int):
        match mode:

            case 0:  # NORMAL
                if sudoku.initial_state[self.index].value == 0:
                    self.value = 0

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

        self.lines_components = SmartList()
        self.border_components = SmartList()
        self.cell_components = SmartList()
        self.region_components = SmartList()
        self.outside_components = SmartList()

        self.brute_force_time = 60

    @property
    def components(self):
        return itertools.chain.from_iterable([
            self.lines_components,
            self.border_components,
            self.cell_components,
            self.region_components,
            self.outside_components
        ])

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

            "digits": ''.join(str(cell.value) for cell in self.board),
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
            "constraints": {
                "lines": [line.to_json() for line in self.lines_components],
                "border": [cmp.to_json() for cmp in self.border_components],
                "cells": [cell_cmp.to_json() for cell_cmp in self.cell_components],
                "regions": [region_cmp.to_json() for region_cmp in self.region_components],
                "outside": [outside_cmp.to_json() for outside_cmp in self.outside_components]
            }

        }

        with open(filename, "w") as file:
            json.dump(data, file, indent=2)

    def from_file(self):
        import json

        from constraints import border_components, cell_components, outside_components, \
            line_components, region_components

        path, extension = QFileDialog.getOpenFileName(dir=os.getcwd(), filter="(*.json)")

        self.lines_components.clear()
        self.border_components.clear()
        self.cell_components.clear()
        self.region_components.clear()
        self.outside_components.clear()

        with open(path, "r") as file:
            data = json.load(file)
            for i in range(81):
                self.initial_state[i].value = int(data["digits"][i])
                self.board[i].value = int(data["digits"][i])
                self.board[i].valid_numbers = SmartList(sort_=True)
                self.board[i].corner = SmartList(max_length=4, sort_=True)
                self.board[i].colors = SmartList(max_length=4, sort_=True)

            for key, val in data["constraints"].items():
                setattr(self, key, val)

            for item in data["constraints"]["border"]:
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
                                                          SmartList(max_length=4))
                        for val in item["numbers"]:
                            obj.numbers.append(val)

                    case "LessGreater":
                        obj = border_components.LessGreater(self, item["indices"], item["less"])

                self.border_components.append(obj)

            for item in data["constraints"]["cells"]:
                match item["type"]:

                    case "EvenDigit":
                        obj = cell_components.EvenDigit(self, item["index"])
                        self.cell_components.append(obj)

                    case "OddDigit":
                        obj = cell_components.OddDigit(self, item["index"])
                        self.cell_components.append(obj)

            for item in data["constraints"]["lines"]:
                match item["type"]:

                    case "Arrow":
                        obj = line_components.Arrow(self, SmartList())
                        obj.setup(item["index"])

                        for branch in item["branches"]:
                            obj.branches.append([self.board[ix] for ix in branch])

                        self.lines_components.append(obj)

                    case "Thermometer":
                        obj = line_components.Thermometer(self, SmartList())
                        obj.setup(item["index"])

                        for branch in item["branches"]:
                            obj.branches.append([self.board[ix] for ix in branch])

                        self.lines_components.append(obj)

                    case "LockoutLine":
                        obj = line_components.LockoutLine(self, SmartList())
                        obj.setup(item["index"])

                        for branch in item["branches"]:
                            obj.branches.append([self.board[ix] for ix in branch])

                        self.lines_components.append(obj)

                    case "BetweenLine":
                        obj = line_components.BetweenLine(self, SmartList())
                        obj.setup(item["index"])

                        for branch in item["branches"]:
                            obj.branches.append([self.board[ix] for ix in branch])

                        self.lines_components.append(obj)

                    case "PalindromeLine":
                        obj = line_components.PalindromeLine(self, SmartList(item["indices"]))
                        self.lines_components.append(obj)

                    case "GermanWhispersLine":
                        obj = line_components.GermanWhispersLine(self, SmartList(item["indices"]))
                        self.lines_components.append(obj)

            for item in data["constraints"]["outside"]:
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

            for item in data["constraints"]["regions"]:
                match item["type"]:
                    case "Cage":
                        self.region_components.append(region_components.Cage.from_json(self, item))

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

    def get_zones(self, index: int):
        return self.get_entire_row(index) + self.get_entire_column(index) + self.get_entire_box(index)

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

    def try_solve(self, thread):
        before = copy.deepcopy(self.board)
        possible = self.solve(thread)

        self.board = before
        return possible

    def solve(self, thread: QObject = None):
        if self.brute_force_time == 0:
            return False

        self.calculate_valid_numbers()
        index = self.next_empty()
        if thread is not None:
            thread.progressChanged.emit()
            time.sleep(1 / thread.speed)

        if index is None:
            return True

        cell = self.board[index]

        for number in cell.valid_numbers:
            cell.value = number

            if self.solve(thread):
                return True

            cell.value = 0
        return False

    def valid(self, number: int, index: int, show_constraints: bool = False):

        show_constraint = show_constraints

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
