import locale
import sys

from lastgang.data_manager import DataManager
from lastgang.lastgang_calculator import Lastgang
from lastgang.ui.left_menu import LeftMenu
from lastgang.ui.loading_animation import LoadingWidget
from lastgang.ui.page_input import InputPage
from lastgang.ui.page_output import OutputPage
from lastgang.ui.page_plot import PlotPage
from lastgang.ui.page_prices import PricesPage

locale.setlocale(locale.LC_ALL, 'de_DE')
import datetime

from matplotlib import pyplot as plt

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QWidget, QStackedWidget, QApplication, \
    QFileDialog

TODAY = datetime.date.today()

LIGHT_GRAY = '#EDEDED'
BLUE = '#008F9B'
DARKER_GRAY = '#646464'


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.lg_: Lastgang | None = Lastgang("meissen.csv")
        self.dm = DataManager()

        self.setWindowTitle("Lastganganalyse")

        self.setStyleSheet(
            "QPushButton{background: #008F9B; color: white; font-weight: bold; font: 10pt Verdana; border: none; border-radius: 5px}"
            "QPushButton:hover{background: #00B9C6}"
            "QLineEdit{padding-left: 5px; padding-right: 5px; border: 1px solid #646464}"
        )

        ############################################################################################
        ############################################################################################

        self.cw = QWidget()
        self.setCentralWidget(self.cw)
        self.cl = QHBoxLayout(self.cw)

        ############################################################################################
        ############################################################################################

        self.left_menu = LeftMenu(self)
        self.stack = QStackedWidget()
        self.prices_page = PricesPage(self)
        self.pp = PlotPage(self)
        self.ip = InputPage(self)

        self.op = OutputPage(self)
        self.lw = LoadingWidget(self)

        self.stack.addWidget(self.op)
        self.stack.addWidget(self.ip)
        self.stack.addWidget(self.pp)
        self.stack.addWidget(self.prices_page)
        self.stack.addWidget(self.lw)
        self.stack.setCurrentWidget(self.lw)

        ############################################################################################
        ############################################################################################

        self.cl.addWidget(self.left_menu)
        self.cl.addWidget(self.stack)

        ############################################################################################
        ############################################################################################

    def show_output(self):
        self.stack.setCurrentIndex(0)

    def plot_day(self):
        if not self.lg_:
            return
        y, m, d = self.pp.cal_w.selectedDate().year(), self.pp.cal_w.selectedDate().month(), self.pp.cal_w.selectedDate().day()
        self.lg_.plot_day(datetime.date(y, m, d))
        plt.show()

    def plot_month(self):
        if not self.lg_:
            return
        self.lg_.plot_month(self.pp.cal_w.monthShown())
        plt.show()

    def plot_all(self):
        if not self.lg_:
            return

        self.stack.setCurrentWidget(self.lw)
        self.lw.start_animation()

    def load_lastgang(self):
        file, ext = QFileDialog.getOpenFileName(filter="*.csv")
        if not file:
            return

        self.set_lastgang(file)

    def set_lastgang(self, path: str):
        self.lg_ = Lastgang(path)
        self.ip.f11.widget.setText(path)
        self.pp.cal_w.setSelectedDate(QDate(self.lg_.year, 1, 1))
        self.op.set_values(self.lg_)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit((app.exec()))


if __name__ == '__main__':
    main()
