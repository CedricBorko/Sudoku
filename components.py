import time
from typing import List, Tuple


class Cage:
    def __init__(self, cells: List[Tuple[int, int]], total: int):
        self.cells = cells
        self.total = total

    def valid(self, board: List[List[str]]) -> bool:
        s = 0
        for cell in self.cells:
            row, col = cell
            s += int(board[row][col]) if board[row][col] != "?" else 0

        return s <= self.total


class Arrow:
    def __init__(self, origin: Tuple[int, int], path: List[Tuple[int, int]], total: int):
        self.origin = origin
        self.path = path

        self.total = total

    def valid(self, board: List[List[str]]) -> bool:
        s = 0
        for cell in self.path:
            row, col = cell
            s += board[row][col]

        return s <= self.total


class Sudoku:
    NUMBERS = "123456789"

    def __init__(self, content: List[List[str]], empty_character: str = "-"):

        self.board = content
        self.initial = content.copy()

        self.empty_character = empty_character

        self.cages: List[Cage] = []

        self.arrows: List[Arrow] = []

    def add_cage(self, cage: Cage):
        self.cages.append(cage)

    def add_arrow(self, arrow: Arrow):
        self.arrows.append(arrow)

    @classmethod
    def from_string(cls, content: str, empty_character: str = "-"):
        obj = cls([[content[x * 9 + y] for y in range(9)] for x in range(9)])
        obj.empty_character = empty_character
        return obj

    def show(self):
        for row in range(9):
            for col in range(9):
                print(f"{self.initial[row][col]}", end="  ")
            print()

    def __repr__(self):
        s = ""

        for row in range(9):
            for col in range(9):
                s += f"{self.board[row][col]}  "
            s += '\n'
        return s

    def next_empty(self) -> Tuple[int, int]:
        for row in range(9):
            for col in range(9):
                if self.board[row][col] == self.empty_character:
                    return row, col
        return -1, -1

    def solve(self):
        ne = self.next_empty()
        if ne == (-1, -1):
            return True
        else:
            row, col = ne

        for num in self.NUMBERS:

            if self.valid(num, row, col):
                self.board[row][col] = str(num)

                if self.solve():
                    return True
                self.board[row][col] = self.empty_character

        return False

    def valid(self, number: str, row: int, col: int):

        for r in range(9):
            if self.board[row][r] == number and col != r:
                return False

        for c in range(9):
            if self.board[c][col] == number and row != c:
                return False

        box_x = col // 3
        box_y = row // 3

        for i in range(box_y * 3, box_y * 3 + 3):
            for j in range(box_x * 3, box_x * 3 + 3):
                if self.board[i][j] == number and (i, j) != (row, col):
                    return False

        for cage in self.cages:
            if not cage.valid(self.board): return False

        for arrow in self.arrows:
            if not arrow.valid(self.board): return False

        return True


if __name__ == '__main__':
    b = Sudoku(
        [
            ["4", "?", "?", "?", "2", "9", "?", "8", "1"],
            ["8", "?", "5", "?", "3", "1", "?", "?", "?"],
            ["?", "?", "2", "?", "7", "?", "3", "5", "?"],
            ["7", "4", "?", "9", "?", "?", "?", "?", "?"],
            ["?", "?", "?", "?", "?", "8", "5", "7", "9"],
            ["?", "?", "?", "6", "1", "7", "?", "?", "3"],
            ["?", "?", "?", "?", "?", "?", "?", "1", "6"],
            ["9", "7", "8", "?", "?", "?", "?", "?", "5"],
            ["?", "?", "?", "2", "9", "5", "?", "?", "?"]
        ],
        empty_character="?"
    )



    template = (
        "?????????"
        "?????????"
        "?????????"
        "?????????"
        "?????????"
        "?????????"
        "?????????"
        "?????????"
        "?????????"
    )
