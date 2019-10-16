import math
import random
import time
from typing import Any, Tuple

sudokuBoard = {}
solvedBoard = {}
columns = []
rows = []
blocks = []
empty_tiles = set()

def emptySudoku():
    for i in range(9):
        columns.append({1, 2, 3, 4, 5, 6, 7, 8, 9})
        rows.append({1, 2, 3, 4, 5, 6, 7, 8, 9})
        blocks.append({1, 2, 3, 4, 5, 6, 7, 8, 9})
    for i in range(81):
        empty_tiles.add(numberToCoordinate(i))


def readSudoku(problem):
    global solvedBoard
    for i, num in enumerate(problem):
        if num in ('.', '0'):
            sudokuBoard[numberToCoordinate(i)] = 0
        else:
            setTile(numberToCoordinate(i), int(num))
    solvedBoard = sudokuBoard


def show(board):
    for i in range(81):
        coordinate = numberToCoordinate(i)
        print(board[coordinate], end=" ")
        if (i + 1) % 9 == 0:
            print()


def numberToCoordinate(i):
    col = i % 9
    row = i // 9
    block = row // 3 * 3 + col // 3
    return col, row, block


def setTile(pos, number):
    col, row, block = pos
    columns[col].remove(number)
    rows[row].remove(number)
    blocks[block].remove(number)
    empty_tiles.remove(pos)
    sudokuBoard[pos] = number


def deleteTile(pos, number):
    col, row, block = pos
    columns[col].add(number)
    rows[row].add(number)
    blocks[block].add(number)
    empty_tiles.add(pos)
    sudokuBoard[pos] = 0


def findBestEmptyTile():
    bestPossibility = 9
    for pos in empty_tiles:
        col, row, block = pos
        possibleNumbers = columns[col] & rows[row] & blocks[block]
        possibilities = len(possibleNumbers)
        if possibilities < 2:
            return pos, possibleNumbers
        if possibilities < bestPossibility:
            bestTile = (pos, possibleNumbers)
            bestPossibility = possibilities
    return bestTile


def solve():
    if not empty_tiles:
        return True
    pos, possibleNumbers = findBestEmptyTile()
    possibleNumbers = sorted(possibleNumbers)
    for num in possibleNumbers:
        setTile(pos, num)
        if solve():
            return True
        deleteTile(pos, num)


emptySudoku()


def chooseDifficulty():
    sudoku = ''
    difficulty = input('Difficulty: ')
    if difficulty == 'Easy':
        file = open("Sudoku1.txt", "r")
        line = random.randint(1, 10000)
        for i, l in enumerate(file):
            if i + 1 == line:
                sudoku = file.readline()
                sudoku = sudoku[:-1]
        file.close()
        return sudoku

    if difficulty == 'Medium':
        file = open("Sudoku2.txt", "r")
        line = random.randint(1, 10000)
        for i, l in enumerate(file):
            if i + 1 == line:
                sudoku = file.readline()
                sudoku = sudoku[:-1]
        file.close()
        return sudoku

    if difficulty == 'Hard':
        file = open("Sudoku3.txt", "r")
        line = random.randint(1, 10000)
        for i, l in enumerate(file):
            if i + 1 == line:
                sudoku = file.readline()
                sudoku = sudoku[:-1]
        file.close()
        return sudoku

    if difficulty == 'Very Hard':
        file = open("Sudoku4.txt", "r")
        line = random.randint(1, 9999)
        for i, l in enumerate(file):
            if i + 1 == line:
                sudoku = file.readline()
                sudoku = sudoku[:-1]
        file.close()
        return sudoku

    if difficulty == 'Expert':
        file = open("Sudoku5.txt", "r")
        line = random.randint(1, 9999)
        for i, l in enumerate(file):
            if i + 1 == line:
                sudoku = file.readline()
                sudoku = sudoku[:-1]
        file.close()
        return sudoku


readSudoku(chooseDifficulty())
show(sudokuBoard)
print()
show(solvedBoard)
