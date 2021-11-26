import locale

locale.setlocale(locale.LC_ALL, 'de_DE')
from PySide6.QtWidgets import QFrame, QMainWindow, QGridLayout, QLabel

from lastgang.lastgang_calculator import Lastgang
from lastgang.ui.form import FormItem
from lastgang.ui.group import Group


class OutputPage(QFrame):
    def __init__(self, window: QMainWindow):
        super().__init__()

        self.window_ = window
        self.layout_ = QGridLayout(self)

        self.g1 = Group("Lastwerte")
        self.g2 = Group("Spezielle Werte")

        self.f1 = FormItem("Betrachtungsjahr", QLabel())
        self.f2 = FormItem("Spitzenlast", QLabel())
        self.f3 = FormItem("Grundlast", QLabel())
        self.f4 = FormItem("Maximum", QLabel())
        self.f5 = FormItem("Minimum", QLabel())
        self.f6 = FormItem("Arbeit", QLabel())
        self.f7 = FormItem("Benutzungsstunden", QLabel())

        self.f8 = FormItem("EnPI", QLabel())
        self.f9 = FormItem("Peak Shaving", QLabel())

        self.g1.layout_.addWidget(self.f1)
        self.g1.layout_.addWidget(self.f2)
        self.g1.layout_.addWidget(self.f3)
        self.g1.layout_.addWidget(self.f4)
        self.g1.layout_.addWidget(self.f5)
        self.g1.layout_.addWidget(self.f6)
        self.g1.layout_.addWidget(self.f7)
        self.g2.layout_.addWidget(self.f8)
        self.g2.layout_.addWidget(self.f9)

        self.layout_.addWidget(self.g1, 0, 0)
        self.layout_.addWidget(self.g2, 0, 1)

    def set_values(self, lg: Lastgang):
        self.f1.widget.setText(f"{lg.year}")
        self.f2.widget.setText(lg.format_value(lg.top_load))
        self.f3.widget.setText(lg.format_value(lg.base_load))
        self.f4.widget.setText(lg.format_value(lg.maximum))
        self.f5.widget.setText(lg.format_value(lg.minimum))
        self.f6.widget.setText(locale.format_string('%.0f', lg.work, True) + " kWh")
        self.f7.widget.setText(locale.format_string('%.0f', lg.hours, True) + " h")
        self.f8.widget.setText(locale.format_string('%.2f', lg.EnPI, True))
        self.f9.widget.setText(locale.format_string('%.0f', lg.peak_shaving(116.15), True) + " EUR / a")
