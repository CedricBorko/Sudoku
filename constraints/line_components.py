from __future__ import annotations
import math
from typing import List, Tuple, Optional

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygon

from constraints.border_components import Component
from sudoku_.sudoku import Sudoku, Cell
from utils import smallest_sum_including_x, sum_first_n, BoundList


class LineComponent(Component):
    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        super().__init__(sudoku, indices)

        self.color = QColor("#CCCCCC")
        self.thickness = 10

    def __len__(self):
        return len(self.indices)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            for index in self.indices:
                if index in other.indices:
                    return True
        return False

    def get(self, index: int) -> LineComponent:
        for cmp in self.sudoku.lines_components:
            if isinstance(cmp, self.__class__) and index in cmp.indices:
                return cmp

    @property
    def ends(self):
        return self.first.index, self.last.index

    def setup(self, index: int):
        self.indices = BoundList([index])

    def clear(self):
        self.indices = BoundList()

    def position_on_line(self, cell_index: int) -> int:
        return self.indices.index(cell_index)

    def center(self) -> Tuple:
        if (length := len(self.indices)) % 2 == 0:
            return self.indices[length // 2 - 1:length // 2 + 1]

        return self.sudoku.cells[self.indices[length // 2]],

    def check_valid(self):
        return True

    def next_cell(self, cell_index: int) -> Cell:
        if cell_index != self.indices[-1]:
            n = self.indices[self.position_on_line(cell_index) + 1]
            return self.sudoku.cells[n]

    def previous_cell(self, cell_index: int) -> Cell:
        if cell_index != self.indices[0]:
            p = self.indices[self.position_on_line(cell_index) - 1]
            return self.sudoku.cells[p]

    def on_end(self, cell_index: int):
        return cell_index in (self.indices[0], self.indices[-1])

    def distance(self, i1: int, i2: int):
        return math.fabs(self.position_on_line(i1) - self.position_on_line(i2))

    @staticmethod
    def draw_path(painter, cells: List[QPoint]):
        for i in range(len(cells) - 1):
            painter.drawLine(cells[i], cells[i + 1])

    def draw(self, painter: QPainter, cell_size: int):

        pen = QPen(self.color, self.thickness)
        pen.setCapStyle(Qt.RoundCap)
        painter.setBrush(QBrush(self.color))
        painter.setPen(pen)

        if len(self.indices) == 1:
            painter.drawEllipse(
                self.cells[0].scaled_rect(cell_size, 0.2)
            )

        else:
            self.draw_path(painter, [c.rect(cell_size).center() for c in self.cells])

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices
        }


class GermanWhispersLine(LineComponent):
    """
    A constraint that forces digits on the line to have a difference of at least 5
    to the cell before and after
    """

    NAME = "German Whispers Line"
    HIGHS = {6, 7, 8, 9}
    LOWS = {1, 2, 3, 4}

    LAYER = 5
    RULE = "Cells on a green line must have a difference of at least 5."

    def __init__(self, sudoku: Sudoku, indices: List[int]):
        super().__init__(sudoku, indices)

        self.color = QColor("#10b558")
        self.thickness = 10.0

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
        }

    def __eq__(self, other):
        if isinstance(other, GermanWhispersLine):
            for index in self.indices:
                if index in other.indices:
                    return True
        return False

    def valid(self, index: int, number: int):
        if index not in self.indices:
            return True

        if number == 5:
            return False

        prev = self.previous_cell(index)
        nxt = self.next_cell(index)

        if prev is not None and prev.value != 0 and math.fabs(prev.value - number) < 5:
            return False

        if nxt is not None and nxt.value != 0 and math.fabs(nxt.value - number) < 5:
            return False

        return True

    def valid_location(self, index: int, not_on_border: bool):
        if index in self.sudoku.indices(self.first.neighbours) and not_on_border:
            if index not in self.indices:
                self.indices.insert(0, index)
                return True

        elif index in self.sudoku.indices(self.last.neighbours) and not_on_border:
            if index not in self.indices:
                self.indices.append(index)
                return True
        return False

    def setup(self, index: int):
        self.indices = BoundList([index])

    @property
    def ends(self):
        return self.first.index, self.last.index

    def get(self, index: int):
        for cmp in self.sudoku.lines_components:
            if isinstance(cmp, GermanWhispersLine) and index in cmp.indices:
                return cmp

    def clear(self):
        self.indices = BoundList([])


class PalindromeLine(LineComponent):
    NAME = "Palindrome Line"

    LAYER = 4
    RULE = "The numbers on the grey line appear the same forward and backward."

    def __init__(self, sudoku: "Sudoku", indices: BoundList[int]):
        super().__init__(sudoku, indices)

        self.color = QColor("#999999")
        self.thickness = 10.0

        for index in self.indices:
            self.opposite(index)

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "indices": self.indices,
        }

    def opposite(self, cell_index: int):
        pos = self.position_on_line(cell_index)
        sop = len(self) - pos - 1

        return sop

    def setup(self, index: int):
        self.indices = BoundList([index])

    @property
    def ends(self):
        return self.first.index, self.last.index

    def __repr__(self):
        return f"{self.ends}"

    def __eq__(self, other):
        if isinstance(other, PalindromeLine):
            for index in self.indices:
                if index in other.indices:
                    return True
        return False

    def get(self, index: int):
        for cmp in self.sudoku.lines_components:
            if isinstance(cmp, PalindromeLine) and index in cmp.indices:
                return cmp

    def clear(self):
        self.indices = BoundList([])

    def valid(self, index: int, number: int):
        if index not in self.indices:
            return True

        opp = self.opposite(index)

        if self.cells[opp].value != 0 and number != self.cells[opp].value:
            return False

        return True

    def valid_location(self, index: int, diagonal: bool):

        if index in self.sudoku.indices(self.first.neighbours) and diagonal:
            if index not in self.indices:
                self.indices.insert(0, index)
                return True

        elif index in self.sudoku.indices(self.last.neighbours) and diagonal:
            if index not in self.indices:
                self.indices.append(index)
                return True
        return False


class Thermometer(LineComponent):
    NAME = "Thermometer"
    RULE = "The numbers on the thermometer must strictly increase starting from the bulb end."

    LAYER = 1

    def __init__(self, sudoku: "Sudoku", indices: List[int]):
        super().__init__(sudoku, indices)

        self.bulb = None
        self.branches: List[List[Cell]] = []

        self.current_branch = None

    def clear(self):
        self.branches = []
        self.indices = BoundList()

    def setup(self, index: int):
        self.indices = [index]
        self.bulb = self.sudoku.cells[index]
        self.branches = []

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "index": self.bulb.index,
            "branches": [[c.index for c in branch] for branch in self.branches]
        }

    def get(self, index: int):
        for cmp in self.sudoku.lines_components:
            if isinstance(cmp, Thermometer) and cmp.bulb.index == index:
                return cmp

    def __eq__(self, other):
        if isinstance(other, Thermometer):
            return self.bulb.index == other.bulb.index
        return False

    def can_remove(self, index: int):
        if len(self.current_branch) > 1 and index == self.current_branch[-2].index:
            return True
        return False

    def valid_location(self, index: int) -> bool:
        return (
            index in self.sudoku.indices(self.current_branch[-1].neighbours)
            and index != self.bulb.index
            and index not in [c.index for c in self.current_branch]
            and len(self.current_branch) < 8
        )

    def __repr__(self):
        return ' -> '.join(map(str, self.indices))

    def valid(self, index: int, number: int) -> bool:
        for branch in self.branches:
            if index in [c.index for c in branch]:
                break
        else:
            branch = None

        if branch is None and index != self.bulb.index:
            return True

        if not self.branches:
            return True

        if index == self.bulb.index:

            if number > 9 - max([len(branch) for branch in self.branches]):
                return False

            for branch in self.branches:
                full = [self.bulb] + branch

                if any([number >= n.value for n in full[1:len(full)] if n.value != 0]):
                    return False

            return True

        else:
            values = [c.value for c in branch]

            if number in values or number == self.bulb.value:
                return False

            full = [self.bulb] + branch

            indices = [c.index for c in full]
            pos_on_branch = indices.index(index)

            if any([number <= n.value for n in full[0:pos_on_branch] if n.value != 0]):
                return False

            if any([number >= n.value for n in full[pos_on_branch + 1:len(full)] if n.value != 0]):
                return False

            if len(full) == 9:
                return number == pos_on_branch + 1

            smaller = [i for i in range(1, number)]
            bigger = [i for i in range(number + 1, 10)]
            # print(smaller, "<", number, "<", bigger)

            if len(full[pos_on_branch + 1:]) > len(bigger):
                return False

            if len(full[:pos_on_branch]) > len(smaller):
                return False

            return True

    def check_valid(self):
        if len(self.indices) <= 1 or len(self.indices) > 9:
            return False
        return True

    def draw(self, painter: QPainter, cell_size: int):

        pen = QPen(QColor("#CCCCCC"), cell_size / 4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if self.bulb is None:
            return

        for branch in self.branches:
            if not branch:
                continue

            painter.drawLine(
                self.bulb.rect(cell_size).center(),
                branch[0].rect(cell_size).center()
            )

        for branch in self.branches:
            self.draw_path(painter, [c.rect(cell_size).center() for c in branch])

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#CCCCCC")))
        painter.drawEllipse(self.bulb.scaled_rect(cell_size, 0.75))

        return

    def get_branch(self, index: int) -> List[Cell]:

        for branch in self.branches:
            if index in [c.index for c in branch]:
                return branch

    def delete_branch(self, index: int) -> bool:
        if (branch := self.get_branch(index)) is not None:
            self.branches.remove(branch)
            del branch
            return True
        return False

    def can_add_branch(self, index: int):
        return index in self.sudoku.indices(self.bulb.neighbours)


class Arrow(LineComponent):
    NAME = "Arrow"

    LAYER = 2
    RULE = "Number on the arrow sum to the number in the circle at its start."

    def __init__(self, sudoku: "Sudoku", indices: BoundList[int]):
        super().__init__(sudoku, indices)

        self.bulb = None
        self.branches: List[List[Cell]] = []

        self.current_branch = None

    def get(self, index: int):
        for cmp in self.sudoku.lines_components:
            if isinstance(cmp, Arrow) and cmp.bulb.index == index:
                return cmp

    @property
    def ends(self):
        return self.first.index,

    def clear(self):
        self.branches = []
        self.indices = BoundList()

    def __eq__(self, other):
        if isinstance(other, Arrow):
            return self.bulb == other.bulb
        return False

    def __repr__(self):
        return f"{' -> '.join(map(str, self.cells))}"

    def sum_so_far(self):
        return sum([c.value for c in self.cells[self.bulb.index:] if c.value != 0])

    def can_add_branch(self, index: int):
        return index in self.sudoku.indices(self.bulb.neighbours)

    def get_branch(self, index: int) -> List[Cell]:

        for branch in self.branches:
            if index in [c.index for c in branch]:
                return branch

    def delete_branch(self, index: int) -> bool:
        if (branch := self.get_branch(index)) is not None:
            self.branches.remove(branch)
            del branch
            return True
        return False

    def setup(self, index: int):
        self.indices = [index]
        self.bulb = self.sudoku.cells[index]
        self.branches = []

    def valid_location(self, index: int) -> bool:
        return (
            index in self.sudoku.indices(self.current_branch[-1].neighbours)
            and index != self.bulb.index
            and index not in [c.index for c in self.current_branch]
        )

    def can_remove(self, index: int):
        if len(self.current_branch) > 1 and index == self.current_branch[-2].index:
            return True
        return False

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "index": self.bulb.index,
            "branches": [[c.index for c in branch] for branch in self.branches]
        }

    @property
    def arrow_cells(self) -> Optional[List[Cell]]:
        return self.cells[:1]

    def can_create(self, click_x: int, click_y: int) -> bool:
        return len(self.cells) > 1

    @property
    def arrow_filled(self):
        return all([c.value != 0 for c in self.arrow_cells])

    @property
    def unique(self):
        for branch in self.branches:
            for cell in branch:
                for other in branch:
                    if cell == other:
                        continue
                    if other not in self.sudoku.sees(cell.index):
                        return False
        return True

    def valid(self, index: int, number: int):
        if index == self.bulb.index:

            if self.unique:
                return number >= sum_first_n(len(self.arrow_cells))

                # Only one number is possible now! The sum of all other digits
            if self.arrow_filled:
                return number == sum([c.value for c in self.arrow_cells])

            # In Case Arrow is just one extra Cell (Bulb and Tip)
            if len(self.cells) == 2:
                return self.cells[1] not in self.sudoku.get_orthogonals(index)

            return True

        else:

            if smallest_sum_including_x(number, len(self.arrow_cells)) > 9:
                return False

            if self.sum_so_far() + number > self.bulb.value:
                return False

            return True

    @staticmethod
    def dot_product(v1: QPoint, v2: QPoint = QPoint(0, 1)):
        return v1.x() * v2.x() + v1.y() * v2.y()

    def length(self, vec: QPoint):
        return math.sqrt(self.dot_product(vec, vec))

    def angle(self, vec1: Tuple[int, int], vec2: Tuple[int, int] = (0, 1)):
        return math.acos(self.dot_product(vec1, vec2) / (self.length(vec1) * self.length(vec2)))

    def draw(self, painter: QPainter, cell_size: int):

        pen = QPen(QColor("#BBBBBB"), 5.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        if self.bulb is None:
            return

        for branch in self.branches:
            if not branch:
                continue

            painter.drawLine(
                self.bulb.rect(cell_size).center(),
                branch[0].rect(cell_size).center()
            )

        for branch in self.branches:
            self.draw_path(painter, [c.rect(cell_size).center() for c in branch])

        for branch in self.branches:
            start = branch[-1]
            end = self.bulb if len(branch) == 1 else branch[-2]

            tip_end = start.rect(cell_size).center()

            p1 = QPoint(
                int(cell_size * 1.5) + end.column * cell_size,
                int(cell_size * 1.5) + end.row * cell_size,
            )

            p2 = QPoint(
                int(cell_size * 1.5) + start.column * cell_size,
                int(cell_size * 1.5) + start.row * cell_size,
            )

            vector = p2 - p1

            length = self.length(vector)
            width = cell_size // 2

            arrow_head = width / (2 * (math.tan(45) / 2) * length)
            arrow_head_start = p2 + (-arrow_head * vector)

            normal = QPoint(-vector.y(), vector.x())
            t_normal = width / (2 * length)
            left = arrow_head_start + t_normal * normal
            right = arrow_head_start - t_normal * normal

            painter.drawLine(tip_end, left)
            painter.drawLine(tip_end, right)

        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(self.bulb.scaled_rect(cell_size, 0.8))

        return


class BetweenLine(LineComponent):
    NAME = "Between Line"

    LAYER = 6
    RULE = "Numbers on a line with 2 circles at its end must be strictly between the numbers in these circles."

    def __init__(self, sudoku: "Sudoku", indices: BoundList[int]):
        super().__init__(sudoku, indices)

        self.bulb = None
        self.branches: List[List[Cell]] = []

        self.current_branch = None

        self.color = QColor("#CCCCCC")

    def get(self, index: int):

        for cmp in self.sudoku.lines_components:
            if isinstance(cmp, BetweenLine) and cmp.bulb.index == index:
                return cmp

    def can_add_branch(self, index: int):
        return index in self.sudoku.indices(self.bulb.neighbours)

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "index": self.bulb.index,
            "branches": [[c.index for c in branch] for branch in self.branches]
        }

    @property
    def ends(self):
        return [self.first.index] + [branch[-1].index for branch in self.branches]

    def clear(self):
        self.branches = []
        self.indices = BoundList()

    def setup(self, index: int):
        self.indices = [index]
        self.bulb = self.sudoku.cells[index]
        self.branches = []

    @property
    def bulbs(self):
        return [branch[-1] for branch in self.branches]

    def valid_location(self, index: int) -> bool:
        return (
            index in self.sudoku.indices(self.current_branch[-1].neighbours)
            and index != self.bulb.index
            and index not in [c.index for c in self.current_branch]
        )

    def get_branch(self, index: int) -> List[Cell]:

        for branch in self.branches:
            if index in [c.index for c in branch]:
                return branch

    def delete_branch(self, index: int) -> bool:
        if (branch := self.get_branch(index)) is not None:
            self.branches.remove(branch)
            del branch
            return True
        return False

    def can_remove(self, index: int):
        if len(self.current_branch) > 1 and index == self.current_branch[-2].index:
            return True
        return False

    def valid(self, index: int, number: int) -> bool:
        for branch in self.branches:
            if index in [c.index for c in branch]:
                break
        else:
            branch = None

        if branch is None and index != self.bulb.index:
            return True

        if index == self.bulb.index:

            for branch_ in self.branches:
                end = branch_[-1]

                if end.value != 0:
                    return math.fabs(number - end.value) >= 4

            return True

        elif index == branch[-1].index:
            return math.fabs(number - self.bulb.value) >= 4 or self.bulb.value == 0

        else:

            if number in (1, 9):
                return False

            if (m := branch[-1].value) != 0 and (m2 := self.bulb.value) != 0:
                return min(m, m2) < number < max(m, m2)

            return True

    def draw(self, painter: QPainter, cell_size: int):

        radius = cell_size - 10

        if self.bulb is None:
            return

        for branch in self.branches:
            pen = QPen(QColor("#BBBBBB"), 5.0)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

            self.draw_path(painter,
                           [self.bulb.rect(cell_size).center()] + [c.rect(cell_size).center() for c
                                                                   in branch])

            pen = QPen(QColor("#BBBBBB"), 5.0)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(240, 240, 240)))

            rect_end = branch[-1].rect(cell_size)
            painter.drawEllipse(rect_end.center(), radius // 2, radius // 2)

        pen = QPen(QColor("#BBBBBB"), 5.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(240, 240, 240)))

        rect_start = self.bulb.rect(cell_size)
        painter.drawEllipse(rect_start.center(), radius // 2, radius // 2)


class LockoutLine(LineComponent):
    NAME = "Lockout Line"

    RULE = (
        "Numbers on a line with 2 diamonds at its end cannot be between the numbers in these diamonds."
        " Additionally numbers in directly connected diamonds have a difference of at least 4.")

    LAYER = 6

    def __init__(self, sudoku: "Sudoku", indices: BoundList[int]):
        super().__init__(sudoku, indices)

        self.bulb = None
        self.branches: List[List[Cell]] = []

        self.current_branch = None

        self.color = QColor("#3C01FF")

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "index": self.bulb.index,
            "branches": [[c.index for c in branch] for branch in self.branches]
        }

    def get(self, index: int):

        for cmp in self.sudoku.lines_components:
            if isinstance(cmp, LockoutLine) and cmp.bulb.index == index:
                return cmp

    @property
    def ends(self):
        return [self.first.index] + [branch[-1].index for branch in self.branches]

    def clear(self):
        self.branches = []
        self.indices = BoundList()

    def setup(self, index: int):
        self.indices = [index]
        self.bulb = self.sudoku.cells[index]
        self.branches = []

    def can_add_branch(self, index: int):
        return index in self.sudoku.indices(self.bulb.neighbours)

    @property
    def bulbs(self):
        return [branch[-1] for branch in self.branches]

    def valid_location(self, index: int) -> bool:
        return (
            index in self.sudoku.indices(self.current_branch[-1].neighbours)
            and index != self.bulb.index
            and index not in [c.index for c in self.current_branch]
        )

    def get_branch(self, index: int) -> List[Cell]:

        for branch in self.branches:
            if index in [c.index for c in branch]:
                return branch

    def delete_branch(self, index: int) -> bool:
        if (branch := self.get_branch(index)) is not None:
            self.branches.remove(branch)
            del branch
            return True
        return False

    def can_remove(self, index: int):
        if len(self.current_branch) > 1 and index == self.current_branch[-2].index:
            return True
        return False

    def valid(self, index: int, number: int) -> bool:
        for branch in self.branches:
            if index in [c.index for c in branch]:
                break
        else:
            branch = None

        if branch is None and index != self.bulb.index:
            return True

        if index == self.bulb.index:

            for branch_ in self.branches:
                end = branch_[-1]

                if end.value != 0:
                    return math.fabs(number - end.value) >= 4

            return True

        elif index == branch[-1].index:
            if self.bulb.value != 0:
                return math.fabs(number - self.bulb.value) >= 4
            return True

        else:

            m, m2 = branch[-1].value, self.bulb.value
            return not min(m, m2) <= number <= max(m, m2) or (m == 0 or m2 == 0)

    def draw(self, painter: QPainter, cell_size: int):

        radius = cell_size - 10

        if self.bulb is None:
            return

        for branch in self.branches:
            pen = QPen(self.color, 3.0)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

            self.draw_path(painter,
                           [self.bulb.rect(cell_size).center()] + [c.rect(cell_size).center() for c
                                                                   in branch])

            rect_end = branch[-1].rect(cell_size)
            pen = QPen(QColor("#FB01FF"), 4.0)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(255, 255, 255)))

            painter.drawPolygon(
                QPolygon(
                    [
                        QPoint(rect_end.center().x(), rect_end.center().y() - radius // 2),
                        QPoint(rect_end.center().x() + radius // 2, rect_end.center().y()),
                        QPoint(rect_end.center().x(), rect_end.center().y() + radius // 2),
                        QPoint(rect_end.center().x() - radius // 2, rect_end.center().y())
                    ]
                )
            )

        rect_start = self.cells[0].rect(cell_size)

        pen = QPen(QColor("#FB01FF"), 4.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255)))

        painter.drawPolygon(
            QPolygon(
                [
                    QPoint(rect_start.center().x(), rect_start.center().y() - radius // 2),
                    QPoint(rect_start.center().x() + radius // 2, rect_start.center().y()),
                    QPoint(rect_start.center().x(), rect_start.center().y() + radius // 2),
                    QPoint(rect_start.center().x() - radius // 2, rect_start.center().y())
                ]
            )
        )
