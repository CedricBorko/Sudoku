import datetime

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QMainWindow, QCalendarWidget, QPushButton, \
    QFormLayout, QLineEdit, QComboBox, QCheckBox, QGroupBox, QVBoxLayout, QLabel

from lastgang.ui.form import FormItem
from lastgang.ui.group import Group

TODAY = datetime.date.today()

NETWORK_LEVELS = (
    "Niederspannung",
    "Umspannung in Niederspannung",
    "Mittelspannung",
    "Umspannung in Mittelspannung",
    "Hochspannung"
)


class InputPage(QFrame):
    def __init__(self, window: QMainWindow):
        super().__init__()

        self.window_ = window
        self.layout_ = QGridLayout(self)

        self.g1 = Group("Kunde")
        self.g2 = Group("Unternehmen")
        self.g3 = Group("Netzanschluss")
        self.g4 = Group("Lastgang")

        f1 = FormItem("Firma / Standort", QLineEdit())
        f2 = FormItem("Anschrift", QLineEdit())
        f3 = FormItem("Marktlokation", QLineEdit())

        self.g1.layout().addWidget(f1)
        self.g1.layout().addWidget(f2)
        self.g1.layout().addWidget(f3)

        f4 = FormItem("Anschlussebene", QComboBox())
        f4.widget.addItems(NETWORK_LEVELS)

        f5 = FormItem("Abrechnungsebene", QComboBox())
        f5.widget.addItems(NETWORK_LEVELS)

        self.g2.layout().addWidget(f4)
        self.g2.layout().addWidget(f5)

        f6 = FormItem("Produzierendes Gewerbe", QCheckBox())
        f7 = FormItem("Stromversorger (§ 4 StromStG)", QCheckBox())
        f8 = FormItem("Beliefert das Unternehmen Dritte mit Strom?", QCheckBox())

        self.g3.layout().addWidget(f6)
        self.g3.layout().addWidget(f7)
        self.g3.layout().addWidget(f8)

        f9 = FormItem("Einheit Messwerte", QComboBox())
        f9.widget.addItems(["kw", "kWh"])

        f10 = FormItem("Einheit Messwerte", QPushButton("Lastdaten einlesen"))
        f10.widget.clicked.connect(self.window_.load_lastgang)

        self.f11 = FormItem("Lastgang-Datei", QLabel())

        self.g4.layout().addWidget(f9)
        self.g4.layout().addWidget(f10)
        self.g4.layout().addWidget(self.f11)

        self.layout_.addWidget(self.g1, 0, 0)
        self.layout_.addWidget(self.g2, 1, 0)
        self.layout_.addWidget(self.g3, 0, 1)
        self.layout_.addWidget(self.g4, 1, 1)

