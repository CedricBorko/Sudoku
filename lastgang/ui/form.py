from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QGridLayout, QSizePolicy, QWidget, QLabel, \
    QComboBox, QCheckBox, QLineEdit, QPushButton


class FormItem(QFrame):
    def __init__(self, title: str, widget: QLineEdit | QComboBox | QCheckBox | QPushButton | QLabel):
        super().__init__()


        # VARIABLES
        # ---------------------------------------------------------------------

        self.setObjectName("form_item")

        # STYLE
        # ---------------------------------------------------------------------

        # SETUP
        # ---------------------------------------------------------------------

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        ############################################################################################
        ############################################################################################

        self.lbl = QLabel(title)
        self.lbl.setObjectName("form_title")
        self.lbl.setFixedHeight(20)

        self.widget = widget
        self.widget.setMinimumHeight(30)
        self.widget.setObjectName("form_widget")

        self.setMaximumHeight(self.lbl.height() + self.widget.maximumHeight())

        ############################################################################################
        ############################################################################################

        ############################################################################################
        ############################################################################################

        self.layout_ = QVBoxLayout(self)
        self.layout_.setSpacing(0)
        self.layout_.setContentsMargins(0, 0, 0, 0)

        # FILL LAYOUTS
        # ---------------------------------------------------------------------

        self.layout_.addWidget(self.lbl)
        self.layout_.addWidget(self.widget)
