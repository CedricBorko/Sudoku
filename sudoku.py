from __future__ import annotations

import itertools
import time
from collections import defaultdict
from typing import Callable, Set, List

from PySide6.QtWidgets import QWidget

NUMBERS = {1, 2, 3, 4, 5, 6, 7, 8, 9}


#  0   1   2   3   4   5   6   7   8
#  9  10  11  12  13  14  15  16  17
# 18  19  20  21  22  23  24  25  26
# 27  28  29  30  31  32  33  34  35
# 36  37  38  39  40  41  42  43  44
# 45  46  47  48  49  50  51  52  53
# 54  55  56  57  58  59  60  61  62
# 63  64  65  66  67  68  69  70  71
# 72  73  74  75  76  77  78  79  80


def validate_index(func: Callable) -> Callable:
    def validator(*args, **kwargs) -> None:
        _, cell_index, *_ = args
        if not 0 <= cell_index <= 80: raise ValueError(f"Index must be between 0 and 80, got {cell_index}.")
        return func(*args, **kwargs)

    return validator


class Sudoku:

    def __init__(self) -> None:
        self._current_state = [0] * 81
        self._initial_state = self._current_state.copy()

        self._states = [self._current_state]
        self._state_index = 0

        self._options = {}

    def __repr__(self) -> str:
        return '\n'.join('  '.join(str(cell) if cell != 0 else '-' for cell in row) for row in self.rows())

    def __iter__(self):
        return zip(range(81), self._current_state)

    def __copy__(self) -> Sudoku:
        cls = self.__class__
        copy_sudoku = cls.__new__(cls)
        copy_sudoku.__dict__.update(self.__dict__)
        return copy_sudoku

    @classmethod
    def from_string(cls: Sudoku, sudoku_str: str):
        """

        :param sudoku_str: A string containing information about values of cells
        :return: Filled Sudoku
        """
        sudoku_from_string = Sudoku()
        for index, number in enumerate(sudoku_str):
            sudoku_from_string.set_value(index, int(number))
        sudoku_from_string._initial_state = sudoku_from_string._current_state.copy()
        sudoku_from_string._states = [sudoku_from_string._initial_state.copy()]
        sudoku_from_string._state_index = 0
        return sudoku_from_string

    def to_string(self) -> str:
        return ''.join(str(value) for _, value in self)

    def rotated(self, angle: int) -> Sudoku:
        if angle < 0: angle += 360

        angle = 90 * round(angle / 90)

        if angle in (0, 360): return self.__copy__()

        quarter_turns = angle // 90
        copy_sudoku = self.__copy__()

        for iteration in range(quarter_turns):
            new_values = list(itertools.chain.from_iterable(column[::-1] for column in self.columns()))
            for index, value in enumerate(new_values):
                copy_sudoku.set_value(index, value)

        return copy_sudoku

    def as_index_grid(self) -> str:
        def pad_idx(index: int) -> str:
            return " " * (3 - len(str(index))) + str(index)

        return '\n'.join(
            ' '.join(
                map(lambda idx: pad_idx(idx), self.get_entire_row_indices(row_index))
            )
            for row_index in range(9)
        )

    @validate_index
    def set_value(self, cell_index: int, value: int) -> None:
        if not (0 <= cell_index <= 80 and value in NUMBERS.union({0})): return

        # Clear redo history
        if self._state_index != len(self._states) - 1:
            self._states = self._states[:self._state_index + 1]
            self._current_state = self._states[-1].copy()
            self._state_index = len(self._states) - 1

        self._current_state[cell_index] = value
        self._states.append(self._current_state.copy())
        self._state_index += 1

        self.do_logic_step()

    @validate_index
    def get_value(self, cell_index: int) -> int:
        return self._current_state[cell_index]

    def get_initial(self, cell_index: int) -> int:
        return self._initial_state[cell_index]

    def get_entire_row(self, row_index: int) -> list[int]:
        return self._current_state[row_index * 9: 9 + row_index * 9]

    @staticmethod
    def get_entire_row_indices(row_index: int) -> list[int]:
        return list(range(row_index * 9, 9 + row_index * 9))

    def rows(self) -> list[list[int]]:
        return [self.get_entire_row(row_index) for row_index in range(9)]

    def get_entire_column(self, column_index: int) -> list[int]:
        return [self._current_state[column_index + offset * 9] for offset in range(9)]

    @staticmethod
    def get_entire_column_indices(column_index: int) -> list[int]:
        return list(range(column_index, 81, 9))

    def columns(self) -> list[list[int]]:
        return [self.get_entire_column(column_index) for column_index in range(9)]

    def get_entire_box(self, box_index: int) -> list[int]:
        box_top_left = 3 * box_index + (box_index // 3) * 18
        return self.get_cell_box(box_top_left)

    @staticmethod
    def get_entire_box_indices(box_index: int) -> list[int]:
        box_top_left = 3 * box_index + (box_index // 3) * 18
        return [box_top_left + column_offset + row_offset * 9
                for row_offset in range(3)
                for column_offset in range(3)]

    def boxes(self) -> list[list[int]]:
        return [self.get_entire_box(box_index) for box_index in range(9)]

    def get_cell_row(self, cell_index: int) -> list[int]:
        return self.get_entire_row(cell_index // 9)

    def get_cell_column(self, cell_index: int) -> list[int]:
        return self.get_entire_column(cell_index % 9)

    def get_cell_box(self, cell_index: int) -> list[int]:
        """
         0   1   2   3   4   5   6   7   8
         9  10  11  12  13  14  15  16  17
        18  19  20  21  22  23  24  25  26
        27  28  29  30  31  32  33  34  35
        36  37  38  39  40  41  42  43  44
        45  46  47  48  49  50  51  52  53
        54  55  56  57  58  59  60  61  62
        63  64  65  66  67  68  69  70  71
        72  73  74  75  76  77  78  79  80

        Given index 12, we calculate:
            box_column = 12  % 9 % 3 = 0
            box_row    = 12 // 9 % 3 = 1

        To get the index of the top left cell in the box we subtract box_column
        and 9 * box_row from the given index.
        This gives us box_top_left = 12 - 0 - 9 * 1 = 3.
        btl = 3 * bi + (bi // 3) * 18
        bi = (btl % 9) // 3 + btl // 9

        :param cell_index:
        :return: The box the cell_index is inside
        """

        column, row = cell_index % 9, cell_index // 9
        box_column, box_row = column % 3, row % 3
        box_top_left = cell_index - box_column - 9 * box_row
        box_index = (box_top_left % 9) // 3 + box_top_left // 9
        return [self.get_value(index) for index in self.get_entire_box_indices(box_index)]

    @staticmethod
    def cell_row_index(cell_index: int) -> int:
        return cell_index // 9

    @staticmethod
    def cell_column_index(cell_index: int) -> int:
        return cell_index % 9

    @staticmethod
    def cell_box_index(cell_index: int) -> int:
        return (cell_index % 9 // 3) + (cell_index // 9 // 3) * 3

    @staticmethod
    def cell_box_row_sub_index(cell_index: int) -> int:
        return cell_index // 9 % 3

    @staticmethod
    def cell_box_column_sub_index(cell_index: int) -> int:
        return cell_index % 9 % 3

    @staticmethod
    def cell_box_sub_index(cell_index: int) -> int:
        return Sudoku.cell_box_column_sub_index(cell_index) + Sudoku.cell_box_row_sub_index(cell_index) * 3

    def undo(self) -> None:
        if self._state_index == 0: return

        self._state_index -= 1
        self._current_state = self._states[self._state_index]

    def redo(self) -> None:
        if self._state_index == len(self._states) - 1: return

        self._state_index += 1
        self._current_state = self._states[self._state_index]

    def seen_indices(self, cell_index: int) -> list[int]:
        column, row = cell_index % 9, cell_index // 9
        box_column, box_row = column % 3, row % 3
        box_top_left = cell_index - box_column - 9 * box_row
        box_index = (box_top_left % 9) // 3 + box_top_left // 9
        return list(
            set(
                filter(
                    lambda index: cell_index != index,
                    self.get_entire_row_indices(row)
                    + self.get_entire_column_indices(column)
                    + self.get_entire_box_indices(box_index)
                )
            )
        )

    def calculate_options(self, index: int) -> set[int]:
        base_options = NUMBERS

        row = self.get_cell_row(index)
        base_options = base_options.difference(set(row))

        column = self.get_cell_column(index)
        base_options = base_options.difference(set(column))

        box = self.get_cell_box(index)
        base_options = base_options.difference(set(box))

        return base_options

    def get_options(self, index: int) -> set[int]:
        return self._options.get(index, set())

    def do_logic_step(self) -> None:
        self._options = {
            index: self.calculate_options(index)
            for index in range(80)
            if self.get_value(index) == 0
        }

        self._options = dict(sorted(self._options.items(), key=lambda item: len(item[1])))
        # cell_index, options = next(iter(self._options.items()))
        self.find_hidden_singles()
        # self.find_duplicates()

    def get_next_empty_index(self) -> int:
        try:
            empty_indices = list(filter(lambda index: self.get_value(index) == 0, range(81)))
            return empty_indices.pop(0)
        except IndexError:
            return -1

    def brute_force(self, parent: QWidget = None) -> bool:
        next_empty_index = self.get_next_empty_index()
        if next_empty_index == -1: return True

        for number in self.calculate_options(next_empty_index):
            self.set_value(next_empty_index, number)
            if parent:
                time.sleep(0.01)
                parent.repaint()

            if self.brute_force(parent): return True
            self.set_value(next_empty_index, 0)
        return False

    def find_hidden_singles(self) -> None:
        for box_index in range(9):
            counter = {}
            hidden_singles = []
            for index in self.get_entire_box_indices(box_index):
                value = self.get_value(index)
                if value != 0: continue

                options = self.get_options(index)
                for option in options:
                    if option in counter: counter[option].append(index)
                    else: counter[option] = [index]

            for value, indices in counter.items():
                if len(indices) == 1:
                    hidden_singles.append((indices[0], value))

            for index, value in hidden_singles:
                self._options[index] = {value}

    def find_duplicates(self) -> None:
        for index in range(9):
            ...
            # self._find_duplicates(self.get_entire_column_indices(index))
            # self._find_duplicates(self.get_entire_row_indices(index))
            # self._find_duplicates(self.get_entire_box_indices(index))

    def _find_duplicates(self, indices: list[int]) -> None:
        options = {
            index: self.get_options(index)
            for index in indices if self.get_value(index) == 0
        }

        duplicates = {}
        for index, opts in options.items():
            for o_index, o_opts in options.items():
                if o_index == index: continue
                if opts == o_opts: duplicates[index] = opts

        if not duplicates: return

        if len(duplicates) != len(duplicates[list(duplicates.keys())[0]]): return

        options_to_remove = duplicates[list(duplicates.keys())[0]]
        for index in indices:
            if self.get_value(index) != 0 or not self.get_options(index): continue
            for option in options_to_remove:
                if index not in duplicates: self._options[index].discard(option)


if __name__ == '__main__':
    s = Sudoku.from_string(
        "200080300060070084030500209000105408000000000402706000301007040720040060004010003"
    )
    # 245981376169273584837564219976125438513498627482736951391657842728349165654812793
    s.brute_force()
    print(s)
