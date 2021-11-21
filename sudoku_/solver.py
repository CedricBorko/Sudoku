import math
import random
from typing import List

EMPTY = -1


class SudokuGenerator:
    def __init__(self, size: int = 9, empty_value: int | str = EMPTY):
        self.empty_value = empty_value
        self.size = size

    def show(self, grid: List[int]):
        out = ""
        for i in range(self.size * self.size):
            if i != 0 and i % self.size == 0:
                out += '\n'
            out += f"{grid[i]}  "
        print(out)

    def make_empty_grid(self) -> List[int]:
        return [EMPTY for _ in range(self.size ** 2)]

    def get_empty(self, grid: List[int]) -> int | None:
        for i in range(len(grid)):
            if grid[i] == self.empty_value:
                return i
        else:
            return None

    def row(self, index: int) -> int:
        return index // self.size

    def column(self, index: int) -> int:
        return index % self.size

    def num_used_in_row(self, grid, row, number):
        return number in [grid[i] for i in range(self.size ** 2) if i // self.size == row]

    def num_used_in_column(self, grid, column, number):
        return number in [grid[i] for i in range(self.size ** 2) if i % self.size == column]

    def num_used_in_box(self, grid, row, column, number):
        sub_row = (row // 3) * 3
        sub_col = (column // 3) * 3
        for i in range(sub_row, (sub_row + 3)):
            for j in range(sub_col, (sub_col + 3)):
                if grid[i * self.size + j] == number:
                    return True
        return False

    def can_set(self, grid: List[int], index: int, number: int) -> bool:
        row, column = self.row(index), self.column(index)

        return not (
            self.num_used_in_row(grid, row, number)
            or self.num_used_in_column(grid, column, number)
            or self.num_used_in_box(grid, row, column, number)
        )

    def brute_force(self, grid: List[int], random_pick: bool = True) -> List[int] | bool:

        current = self.get_empty(grid)

        if current is None:
            return grid

        options = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        if random_pick:
            random.shuffle(options)

        for number in options:

            if self.can_set(grid, current, number):
                grid[current] = number

                if self.brute_force(grid, random_pick):
                    return grid

                grid[current] = EMPTY

        return False


if __name__ == '__main__':
    s = SudokuGenerator()
    g = s.brute_force(s.make_empty_grid())
    s.show(g)
