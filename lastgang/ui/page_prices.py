import locale

locale.setlocale(locale.LC_ALL, 'de_DE')
from PySide6.QtWidgets import QFrame, QMainWindow, QGridLayout, QLabel, QLineEdit

from lastgang.lastgang_calculator import Lastgang
from lastgang.ui.form import FormItem
from lastgang.ui.group import Group

MONTHS = (
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember"
)


class PricesPage(QFrame):
    def __init__(self, window: QMainWindow):
        super().__init__()

        self.window_ = window
        self.layout_ = QGridLayout(self)

        self.g1 = Group("Liefervertrag")

        self.f1 = FormItem("Stromlieferant", QLineEdit())
        self.f2 = FormItem("Vertragsmengen [kWh]", QLineEdit())
        self.f3 = FormItem("Mindestabnahmemenge [kWh]", QLineEdit())
        self.f4 = FormItem("Maximalabnahmemenge [kWh]", QLineEdit())

        self.g1.layout_.addWidget(self.f1)
        self.g1.layout_.addWidget(self.f2)
        self.g1.layout_.addWidget(self.f3)
        self.g1.layout_.addWidget(self.f4)

        self.g2 = Group("Fixierte Vertragspreise (monatlich)", grid=True)
        self.prices = [FormItem(f"Arbeitspreis {month}", QLineEdit()) for month in MONTHS]

        for i, p in enumerate(self.prices):
            if i < 6:
                self.g2.layout_.addWidget(p, i, 0)
            else:
                self.g2.layout_.addWidget(p, i - 6, 1)

        self.layout_.addWidget(self.g1, 0, 0)
        self.layout_.addWidget(self.g2, 0, 1)
