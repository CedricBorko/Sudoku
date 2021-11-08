import itertools
import os
import threading
from typing import List, Tuple, T


def n_digit_sums(amount: int, target: int,
                 allowed_digits: Tuple[int] = (1, 2, 3, 4, 5, 6, 7, 8, 9)):
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
    return sum(range(1, amount + 1)) + (x if x not in range(1, amount + 1) else amount + 1)


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


def uniquify(path):
    filename, extension = os.path.splitext(path)
    counter = 1

    while os.path.exists(path):
        path = filename + " (" + str(counter) + ")" + extension
        counter += 1

    return path


class SmartList(list):
    def __init__(self):
        super().__init__()

    def append(self, __object: T) -> None:
        if __object in self:
            self.remove(__object)
        else:
            super(SmartList, self).append(__object)


s = SmartList()
