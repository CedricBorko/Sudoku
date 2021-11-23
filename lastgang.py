import enum
import locale

from matplotlib.offsetbox import AnchoredText

locale.setlocale(locale.LC_ALL, 'de_DE')
import datetime
import os
import random
import time
from typing import List

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import multiprocessing as mp
import matplotlib.dates as mdates

LP = 116.15

STYLES = (
    "bmh",
    "fivethirtyeight",
    "seaborn"
)


class Lastgang:

    def __init__(self, path: os.PathLike | str, is_kw: bool = True, year: int = 2020):
        self.path = path

        self.df = pd.read_csv(path, usecols=[0, 1], sep=";")
        self.is_kw = is_kw
        self.year = year

        self.unit = "kW" if self.is_kw else "kWh"
        self.start_datetime = datetime.datetime(self.year, 1, 1, 0, 0, 0)

    def __repr__(self):
        return f"Lastgang für das Jahr {self.year}."

    def show(self):
        print(f"Mittelwert {self.mean} {self.unit}")
        print(f"Mittlere Abweichung: {self.mad} {self.unit}")
        print(f"Spitzenlast: {self.top_load} {self.unit}")
        print(f"Grundlast: {self.base_load} {self.unit}")
        print(f"Maximum: {self.maximum} {self.unit}")
        print(f"Minimum: {self.minimum} {self.unit}")
        print(f"Work: {self.work} kWh")
        print(f"Hours: {self.hours} h")

    @staticmethod
    def format_date(date_):
        return date_.strftime("%A %d. %B %Y %H:%M:%S")

    def get_timestamp(self, index: int) -> datetime.datetime:
        """

        :param index: nth time stamp
        :return: the nth quarter hour of the year (this object's year)
        """
        return self.start_datetime + datetime.timedelta(minutes=15) * index

    def is_leap_year(self) -> bool:
        return self.year % 4 == 0 and (self.year % 100 != 0 or self.year % 400 == 0)

    def measure_points(self) -> int:
        """

        :return: Number of values measured (differs for leap and non leap years)
        """
        return 24 * 4 * (366 if self.is_leap_year() else 365)

    @property
    def mean(self) -> float:
        return self.df["Leistung"].mean() * (1 if self.is_kw else 4)

    @property
    def mad(self) -> float:
        return self.df["Leistung"].mad() * (1 if self.is_kw else 4)

    @property
    def top_load(self) -> float:
        return self.mean + self.mad

    @property
    def base_load(self) -> float:
        return self.mean - self.mad

    @property
    def maximum(self) -> float:
        return self.df["Leistung"].max() * (1 if self.is_kw else 4)

    @property
    def minimum(self) -> float:
        return self.df["Leistung"].min() * (1 if self.is_kw else 4)

    @property
    def work(self) -> int:
        return int(self.df["Leistung"].sum() / (4 if self.is_kw else 1))

    @property
    def hours(self) -> float:
        return self.work // self.maximum

    @property
    def EnPI(self) -> float:
        return self.base_load / self.top_load

    def peak_shaving(self, lp: float = LP) -> float:
        fifty_first = self.df["Leistung"].nlargest(51).iloc[-1]
        return int((self.maximum - fifty_first) * lp)

    def next_weekday(self, weekday):
        days_ahead = weekday - self.start_datetime.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return self.start_datetime + datetime.timedelta(days_ahead)

    def first_weekday(self, wd: int) -> int:
        monday = self.next_weekday(wd)
        days = (monday - self.start_datetime).days
        if days == 7:
            return 0
        first_index = days * 24 * 4
        return first_index

    def get_weekday_indices(self, weekday: int) -> List[int]:
        """


        :param weekday: 0 = monday ... 6 = sunday
        :return: List of all indices that map to a power value (in the dataframe) on that weekday
        """
        return list(
            filter(
                lambda x: self.get_timestamp(x).weekday() == weekday,
                np.arange(self.measure_points())
            )
        )

    def get_time_avg(self, weekday: int, time_stamp: datetime.datetime):
        indices = [index for index in self.get_weekday_indices(weekday) if
                   self.get_timestamp(index).time() == time_stamp.time()]
        return self.df["Leistung"].iloc[indices].mean()

    def time_stamps(self) -> List[datetime.datetime]:
        return [self.start_datetime + datetime.timedelta(minutes=15) * i for i in range(24 * 4)]

    def top_50(self) -> pd.Series:
        return self.df.nlargest(50, columns="Leistung")

    def plot_lastgang(self):
        plt.style.use('bmh')

        # fivethirtyeight
        figure, axis = plt.subplots(1, 1, figsize=(16, 9))

        axis.set_title(f"Lastgang {self.year}", loc="center")
        axis.set_ylabel("Leistung [kW]")

        axis.xaxis.set_major_locator(mdates.MonthLocator())
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%B"))

        max_x = self.df["Leistung"].idxmax()

        x = [self.get_timestamp(i) for i in range(self.measure_points())]
        y2 = np.full(self.measure_points(), np.nan)
        y2[max_x] = self.maximum

        axis.plot(x, self.df["Leistung"], c="#008F9B")
        axis.plot(x, y2, 'ro', markersize=8.0)

        figure.figimage(plt.imread("logo.png"), 100, 100, alpha=.5, zorder=1)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def plot_leistungskurve(self):

        plt.style.use('bmh')

        figure, axis = plt.subplots(1, 1, figsize=(16, 9))

        axis.set_title(f"Jahresleistungskurve {self.year}", loc="center")
        axis.set_ylabel("Leistung [kW]")
        axis.set_xlabel("Stunden")

        x = np.arange(self.measure_points())
        offset = 75

        axis.fill_between(
            x,
            0,
            self.df.sort_values('Leistung', ascending=False)["Leistung"],
            facecolor="#646464", alpha=0.75
        )

        axis.plot(
            x,
            np.full(self.measure_points(), self.base_load),
            c="#009B8F",
            ls="--",
            linewidth=3.0,
            label="Grundlast"
        )

        axis.plot(
            np.arange(offset, self.measure_points()),
            np.full(self.measure_points() - offset, self.top_load),
            c="#00C3C6",
            linewidth=3.0,
            label="Spitzenlast"
        )

        axis.plot(
            np.arange(offset, 8000),
            np.full(8000 - offset, self.df["Leistung"].nlargest(51).iloc[-1]),
            c="#646464",
            linewidth=3.0,
            label="Top 50"
        )
        axis.set_xticks(range(0, self.measure_points(), self.measure_points() // 9))
        axis.set_xticklabels(list(map(str, range(0, 9000, 1000))))

        plt.text(3100, self.top_50()["Leistung"].min() + 25,
                 f"Potenzial Peak Shaving: {locale.format_string('%.0f', self.peak_shaving(), True)} €",
                 size=10,
                 ha="center", va="center",
                 bbox=dict(boxstyle="round",
                           ec=(1., 1., 1.),
                           fc=(1., 1., 1.),

                           )
                 )

        figure.figimage(plt.imread("logo.png"), 100, 100, alpha=.5, zorder=1)

        plt.legend(loc='upper center', fancybox=True, shadow=True, ncol=5)
        plt.tight_layout()
        plt.show()


def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        sol = func(*args, **kwargs)
        print(time.time() - start)
        return sol

    return wrapper


if __name__ == '__main__':
    lg = Lastgang(path=r"C:\Users\Cedric\Desktop\meissen.csv")
    lg.plot_lastgang()
    # lg.plot_leistungskurve()
