import itertools
import locale
import random

locale.setlocale(locale.LC_ALL, 'de_DE')
import datetime
import os
import time
from typing import List, Dict

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
import sys

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, \
    QCalendarWidget

# LP = 116.15
LP = 11.51
STYLES = (
    "bmh",
    "fivethirtyeight",
    "seaborn"
)

WEEKDAYS = (
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag"
)


class Lastgang:

    def __init__(self, path: os.PathLike | str, is_kw: bool = True, year: int = 2020):
        self.path = path

        self.df = pd.read_csv(path, usecols=[0, 1], sep=";")
        self.df["Zeit"] = pd.to_datetime(self.df["Zeit"], format="%d.%m.%Y %H:%M")
        self.df["weekday"] = self.df["Zeit"].dt.dayofweek
        self.df["time"] = self.df["Zeit"].dt.time

        self.is_kw = is_kw
        self.year = year

        self.unit = "kW" if self.is_kw else "kWh"
        self.start_datetime = self.df["Zeit"].iloc[0]

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
        print(weekday)
        days_ahead = weekday - self.start_datetime.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return self.start_datetime + datetime.timedelta(days_ahead)

    def first_weekday(self, wd: int) -> datetime.datetime:
        day = self.next_weekday(wd)
        days = (day - self.start_datetime).days

        if days == 7:
            return self.get_timestamp(0)
        first_index = days * 24 * 4
        return self.get_timestamp(first_index)

    def time_stamps(self) -> List[datetime.time]:
        ts = datetime.datetime(self.year, 1, 1, 0, 0, 0)
        return [(ts + (i * datetime.timedelta(minutes=15))).time() for i in range(96)]

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

    def weekday_values(self, weekday: int = 0) -> pd.DataFrame:
        """

        :param weekday: 0 = monday ... 6 = sunday
        :return: All rows that match a specified weekday
        """
        return self.df.iloc[self.get_weekday_indices(weekday)]

    def weekday_max(self, weekday: int = 0) -> pd.DataFrame:
        """

        :param weekday: weekday: 0 = monday ... 6 = sunday
        :return: Maximum power used on that day of the week
        """

        values = self.weekday_values(weekday)
        max_idx = values["Leistung"].idxmax()
        return self.df.iloc[max_idx]

    def weekday_min(self, weekday: int = 0) -> pd.DataFrame:
        """

        :param weekday: weekday: 0 = monday ... 6 = sunday
        :return: Maximum power used on that day of the week
        """

        values = self.weekday_values(weekday)
        min_idx = values["Leistung"].idxmin()
        return self.df.iloc[min_idx]

    def weekday_time_mean(self, weekday: int = 0,
                          ts: datetime.time = datetime.time(0, 0, 0)) -> float:
        return round(self.get_rows_for_day_and_time(weekday, ts)["Leistung"].mean())

    def weekday_time_max(self, weekday: int = 0,
                         ts: datetime.time = datetime.time(0, 0, 0)) -> float:
        return round(self.get_rows_for_day_and_time(weekday, ts)["Leistung"].max())

    def weekday_time_min(self, weekday: int = 0,
                         ts: datetime.time = datetime.time(0, 0, 0)) -> float:
        return round(self.get_rows_for_day_and_time(weekday, ts)["Leistung"].min())

    def get_rows_for_day_and_time(self, weekday: int, time_stamp: datetime.time) -> pd.DataFrame:
        return self.df[
            (self.df['Zeit'].dt.dayofweek == weekday) & (self.df['Zeit'].dt.time == time_stamp)
            ]

    def top_50(self) -> pd.Series:
        return self.df.nlargest(50, columns="Leistung")

    @property
    def date_max(self) -> datetime.datetime:
        idx = self.df["Leistung"].idxmax()
        return self.df["Zeit"].iloc[idx]

    def calc_day_time_mean(self) -> List[float]:
        import multiprocessing as mp
        pool = mp.Pool(mp.cpu_count())
        return pool.starmap(self.weekday_time_mean,
                            [(i, self.time_stamps()[x]) for i in range(7) for x in
                             range(len(self.time_stamps()))])

    def calc_day_time_mean_split(self) -> List[List[float]]:
        return [self.__calc_day_time_mean_split(i) for i in range(7)]

    def __calc_day_time_mean_split(self, day: int = 0) -> List[float]:
        import multiprocessing as mp
        pool = mp.Pool(mp.cpu_count())
        return pool.starmap(self.weekday_time_mean, [(day, ts) for ts in self.time_stamps()])

    def calc_day_time_mean_max(self) -> List[float]:
        return [self.__calc_day_time_mean_max(i) for i in range(7)]

    def __calc_day_time_mean_max(self, day: int = 0) -> float:
        import multiprocessing as mp
        pool = mp.Pool(mp.cpu_count())
        values = pool.starmap(self.weekday_time_mean, [(day, ts) for ts in self.time_stamps()])
        return max(values)

    def calc_day_time_max(self) -> List[float]:
        import multiprocessing as mp
        pool = mp.Pool(mp.cpu_count())
        return pool.starmap(self.weekday_time_max,
                            [(i, self.time_stamps()[x]) for i in range(7) for x in
                             range(len(self.time_stamps()))])

    def calc_day_time_min(self) -> List[float]:
        import multiprocessing as mp
        pool = mp.Pool(mp.cpu_count())
        return pool.starmap(self.weekday_time_min,
                            [(i, self.time_stamps()[x]) for i in range(7) for x in
                             range(len(self.time_stamps()))])

    def week_max_min(self) -> Dict[str, List]:
        """y = lg.calc_day_time_mean_split()"""

        """
        for k, v in lg.week_max_min().items():
        for k2, v2 in v.items():
            print(k, k2, v2[0].date(), v2[1])
            
        """

        return {
            WEEKDAYS[i]: {
                "Max": self.weekday_max(i)[["Zeit", "Leistung"]].to_list(),
                "Min": self.weekday_min(i)[["Zeit", "Leistung"]].to_list()

            } for i in range(7)
        }

    def plot_lastgang(self):
        plt.style.use('bmh')

        # fivethirtyeight
        figure, axis = plt.subplots(1, 1, figsize=(16, 9))

        axis.set_title(f"Lastgang {self.year}", loc="center")
        axis.set_ylabel("Leistung [kW]")

        axis.xaxis.set_major_locator(mdates.MonthLocator())
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%B"))

        max_x = self.df["Leistung"].idxmax()
        date_ = self.df["Zeit"].iloc[max_x].strftime("%d. %B %Y")
        time_ = self.df["Zeit"].iloc[max_x].strftime("%H:%M:%S")

        x = [self.get_timestamp(i) for i in range(self.measure_points())]
        y2 = np.full(self.measure_points(), np.nan)
        y2[max_x] = self.maximum
        axis.set_facecolor((1.0, 1.0, 1.0))

        axis.axhline(self.base_load, label="Grundlast", ls=":", c="#646464")
        axis.plot(x, self.df["Leistung"], c="#008F9B", label="Lastgang")
        axis.plot(x, y2, 'ro', markersize=8.0, label=f"Maximum {self.maximum} {self.unit} am {date_} um {time_}")

        figure.figimage(plt.imread("logo.png"), 0, 0, alpha=.5, zorder=1)
        plt.legend(loc='upper center', fancybox=True, shadow=True, ncol=3)

        plt.xticks(rotation=45)
        plt.tight_layout()

    def plot_leistungskurve(self):

        plt.style.use('bmh')

        figure, axis = plt.subplots(1, 1, figsize=(16, 9))

        axis.set_title(f"Jahresleistungskurve {self.year}", loc="center")
        axis.set_ylabel("Leistung [kW]")
        axis.set_xlabel("Stunden")

        x = np.arange(self.measure_points())
        offset = 75
        axis.set_facecolor((1.0, 1.0, 1.0))
        axis.xaxis.grid(False)

        axis.fill_between(
            x,
            0,
            self.df.sort_values('Leistung', ascending=False)["Leistung"],
            facecolor="#646464", alpha=0.75, label="Leistung [kW]"
        )

        axis.axhline(self.base_load, xmin=0, label="Grundlast", ls="-", c="#009B8F", linewidth=3.0)
        axis.axhline(self.top_load, xmin=0, label="Spitzenlast", ls="-", c="#00C3C6", linewidth=3.0)

        axis.plot(
            np.arange(offset, 8000),
            np.full(8000 - offset, self.df["Leistung"].nlargest(51).iloc[-1]),
            c="#646464",
            linewidth=3.0,
            label="Top 50"
        )
        axis.set_xticks(range(0, self.measure_points(), self.measure_points() // 9))
        axis.set_xticklabels(list(map(str, range(0, 9000, 1000))))

        plt.text(4500, self.top_50()["Leistung"].min() + 25,
                 f"Potenzial Peak Shaving (Top 50): {locale.format_string('%.0f', self.peak_shaving(), True)} €/a",
                 size=10,
                 weight="bold",
                 ha="center", va="center",
                 bbox=dict(boxstyle="round",
                           ec=(1., 1., 1.),
                           fc=(1., 1., 1.),

                           )
                 )

        figure.figimage(plt.imread("logo.png"), 0, 0, alpha=.7, zorder=1)

        plt.legend(loc='upper center', fancybox=True, shadow=True, ncol=5)
        plt.tight_layout()

    def plot_flexibilisierung(self):
        plt.style.use('bmh')

        # fivethirtyeight
        figure, axis = plt.subplots(1, 1, figsize=(16, 9))

        axis.set_title(f"Flexibilisierung {self.year}", loc="center")
        axis.set_ylabel("Leistung [kW]")

        x = np.arange(96 * 7)

        y1 = self.calc_day_time_mean()
        y2 = self.calc_day_time_max()
        y3 = self.calc_day_time_min()

        axis.set_facecolor((1.0, 1.0, 1.0))

        axis.plot(x, y1, c="#008F9B", label="Jahresmittelwert zur gleichen Uhrzeit")
        axis.fill_between(
            x,
            y3,
            y2,
            facecolor="#DADADA",
            alpha=0.75,
            label="Leistungsschwankung zur gleichen Uhrzeit"
        )
        # axis.plot(x, y2, 'ro', markersize=8.0)

        axis.set_xticks(np.arange(0, 96 * 7, 12))
        axis.xaxis.grid(False)
        days = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
        axis.set_xticklabels(
            itertools.chain.from_iterable(
                [
                    [f"{days[m]}{self.time_stamps()[x].strftime('%H:%M')}" for x in
                     range(0, 96, 12)]
                    for m in range(7)
                ]
            )
        )

        figure.figimage(plt.imread("logo.png"), 0, 0, alpha=.7, zorder=1)

        plt.xticks(rotation=90)
        plt.legend(loc='upper right', fancybox=True, shadow=True, ncol=1)
        plt.tight_layout()

    def plot_day(self, day: datetime.date):
        from scipy.interpolate import make_interp_spline

        plt.style.use('bmh')

        # fivethirtyeight
        figure, axis = plt.subplots(figsize=(16, 9))

        data = self.df[self.df["Zeit"].dt.date == day]

        axis.set_title(f"Lastgang {day.strftime('%d. %B %Y')}", loc="center")
        axis.set_ylabel("Leistung [kW]")

        axis.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        max_y = data["Leistung"].max()
        max_x = data["Leistung"].to_list().index(max_y)
        time_ = data["Zeit"].iloc[max_x].strftime("%H:%M:%S")

        y = np.full(len(data["Zeit"]), np.nan)
        y[max_x] = max(data["Leistung"])
        axis.set_facecolor((1.0, 1.0, 1.0))

        axis.plot(data["Zeit"], data["Leistung"], c="#008F9B", label="Lastgang")
        axis.plot(data["Zeit"], y, 'ro', markersize=8.0, label=f"Maximum {max_y} {self.unit} um {time_}")

        figure.figimage(plt.imread("logo.png"), 0, 0, alpha=.5, zorder=1)
        plt.legend(fancybox=True, shadow=True, ncol=3)
        plt.xticks(rotation=45)
        plt.tight_layout()

    def plot_month(self, month: int):
        from scipy.interpolate import make_interp_spline

        plt.style.use('bmh')

        # fivethirtyeight
        figure, axis = plt.subplots(figsize=(16, 9))
        axis.set_title(f"Lastgang {datetime.date(self.year, month, 1).strftime('%B')}", loc="center")
        axis.set_ylabel("Leistung [kW]")

        data = self.df[(self.df["Zeit"].dt.month == month) & (self.df["Zeit"].dt.year == self.year)]

        axis.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%d"))

        max_y = data["Leistung"].max()
        max_x = data["Leistung"].to_list().index(max_y)
        date_ = data["Zeit"].iloc[max_x].strftime("%d. %B %Y")
        time_ = data["Zeit"].iloc[max_x].strftime("%H:%M:%S")

        y = np.full(len(data["Zeit"]), np.nan)
        y[max_x] = max(data["Leistung"])
        axis.set_facecolor((1.0, 1.0, 1.0))

        axis.plot(data["Zeit"], data["Leistung"], c="#008F9B", label="Lastgang")
        axis.plot(data["Zeit"], y, 'ro', markersize=8.0, label=f"Maximum {max_y} {self.unit} am {date_} um {time_}")

        figure.figimage(plt.imread("logo.png"), 0, 0, alpha=.5, zorder=1)
        plt.legend(fancybox=True, shadow=True, ncol=3)

        plt.xticks(rotation=45)
        plt.tight_layout()


def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        sol = func(*args, **kwargs)
        print(time.time() - start)
        return sol

    return wrapper


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.cw = QWidget()
        self.setCentralWidget(self.cw)

        self.cl = QVBoxLayout(self.cw)

        self.btn = QPushButton("Plot Day")
        self.btn2 = QPushButton("Plot Month")
        self.btn3 = QPushButton("Plot All")
        self.cal_w = QCalendarWidget()

        self.cl.addWidget(self.btn)
        self.cl.addWidget(self.btn2)
        self.cl.addWidget(self.btn3)

        self.cl.addWidget(self.cal_w)

        self.lg_ = Lastgang(path="meissen.csv")
        self.cal_w.setSelectedDate(QDate(self.lg_.year, 1, 1))
        self.btn.clicked.connect(self.plot_day)
        self.btn2.clicked.connect(self.plot_month)
        self.btn3.clicked.connect(self.plot_all)

    def plot_day(self):
        y, m, d = self.cal_w.selectedDate().year(), self.cal_w.selectedDate().month(), self.cal_w.selectedDate().day()
        self.lg_.plot_day(datetime.date(y, m, d))
        plt.show()

    def plot_month(self):
        self.lg_.plot_month(self.cal_w.monthShown())
        plt.show()

    def plot_all(self):
        self.lg_.plot_lastgang()
        self.lg_.plot_leistungskurve()
        # self.lg_.plot_flexibilisierung()
        plt.show()


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit((app.exec()))


if __name__ == '__main__':
    main()
