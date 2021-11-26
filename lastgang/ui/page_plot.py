import datetime

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QFrame, QGridLayout, QMainWindow, QCalendarWidget, QPushButton

TODAY = datetime.date.today()


class PlotPage(QFrame):
    def __init__(self, window: QMainWindow):
        super().__init__()

        self.window_ = window
        self.layout_ = QGridLayout(self)

        self.btn = QPushButton("Plot Day")
        self.btn2 = QPushButton("Plot Month")
        self.btn3 = QPushButton("Plot All")
        self.cal_w = QCalendarWidget()
        self.cal_w.setSelectedDate(QDate(TODAY.year, TODAY.month, TODAY.day))

        self.btn.clicked.connect(self.window_.plot_day)
        self.btn2.clicked.connect(self.window_.plot_month)
        self.btn3.clicked.connect(self.window_.plot_all)

        self.layout_.addWidget(self.btn)
        self.layout_.addWidget(self.btn2)
        self.layout_.addWidget(self.btn3)
        self.layout_.addWidget(self.cal_w)