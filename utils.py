import itertools
import math
import os
import threading
from typing import Tuple, T, List

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QPainter


def n_digit_sums(amount: int, target: int,
                 allowed_digits: Tuple[int,...] = (1, 2, 3, 4, 5, 6, 7, 8, 9)):
    """

    :param allowed_digits: Digits that can be used in the sum, usually 1 to 9 including both
    :param amount: Amount of digits that can be used
    :param target: The target sum the n digits need to sum up to
    :return: List of unique combinations
    """
    return [comb for comb in itertools.combinations(allowed_digits, amount) if sum(comb) == target]


def sum_first_n(n: int):
    return sum(range(n + 1))


def sum_last_n(n: int):
    return 45 - sum(range(9 - n + 1))


def smallest_sum_including_x(x: int, amount: int):
    return sum(range(1, amount)) + (x if x not in range(1, amount) else amount)


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


import ctypes


def monitor_size():
    try:
        system = ctypes.windll.user32
        return system.GetSystemMetrics(0), system.GetSystemMetrics(1)
    except EnvironmentError:
        print("Only possible for Windows")
        return 1, 1


def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return path


class SmartList(list):
    def __init__(self, items: List = None, max_length: int = None, sort_: bool = False):
        super().__init__()

        self.max_length = max_length
        self.sort_ = sort_

        if items is not None:
            for item in items:
                self.append(item)

    def append(self, __object: T) -> None:
        if __object in self:
            self.remove(__object)
        else:
            if len(self) == self.max_length:
                return
            super(SmartList, self).append(__object)

        if self.sort_:
            if isinstance(__object, QColor):
                self.sort(key=lambda color: color.redF())
            else:
                self.sort()

    def only(self, __object: T) -> bool:
        return len(self) == 1 and __object in self


def distance(p1: QPoint, p2: QPoint) -> float:
    return math.sqrt((p2.x() - p1.x()) ** 2 + (p2.y() - p1.y()) ** 2)
