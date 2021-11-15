from __future__ import annotations

import copy
from typing import Type

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QFrame, QVBoxLayout, QPushButton, \
    QButtonGroup, QSizePolicy, QHBoxLayout, QGridLayout

from constraints.border_components import XVSum, LessGreater, Quadruple, BorderComponent, Ratio, \
    Difference, Component
from constraints.cell_components import OddDigit, EvenDigit
from constraints.line_components import LineComponent, GermanWhispersLine, Thermometer, \
    PalindromeLine, Arrow, BetweenLine, LockoutLine
from constraints.region_components import RegionComponent, Cage, Clone
from constraints.outside_components import Sandwich, XSumsClue, LittleKiller, OutsideComponent
from utils import SmartList


class ComponentMenu(QFrame):
    def __init__(self, parent: "SudokuWindow"):
        super().__init__(parent)

        self.window_ = parent
        self.sudoku = parent.sudoku

        self.toggle_btn = QPushButton("Toggle Components")
        self.toggle_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.toggle_btn.setFixedHeight(40)
        self.toggle_btn.setFixedWidth(400)
        self.toggle_btn.clicked.connect(self.toggle_buttons)

        self.component_group = QButtonGroup()

        self.layout_ = QGridLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(5)
        self.layout_.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.layout_.addWidget(self.toggle_btn, 0, 0, 1, 2)

        self.digit_btn = QPushButton("Digits")
        self.digit_btn.setFixedHeight(40)
        self.digit_btn.setFixedWidth(400)
        self.digit_btn.setCheckable(True)
        self.digit_btn.setChecked(True)
        self.digit_btn.clicked.connect(self.uncheck)

        self.component_group.addButton(self.digit_btn)
        self.layout_.addWidget(self.digit_btn, 10, 0, 1, 2)

        self.add_button(ComponentButton(self, Ratio(self.sudoku, [])), 1, 0)
        self.add_button(ComponentButton(self, Difference(self.sudoku, [])), 1, 1)
        self.add_button(ComponentButton(self, XVSum(self.sudoku, [])), 2, 0)
        self.add_button(ComponentButton(self, Quadruple(self.sudoku, [], SmartList(max_length=4, sort_=True))),
                        2, 1)
        self.add_button(ComponentButton(self, LessGreater(self.sudoku, [])), 3, 0)
        self.add_button(ComponentButton(self, Sandwich(self.sudoku, col=0, row=1, total=0)), 3, 1)
        self.add_button(ComponentButton(self, XSumsClue(self.sudoku, col=0, row=1, total=0)), 4, 0)
        self.add_button(
            ComponentButton(
                self,
                LittleKiller(self.sudoku, col=10, row=1, total=0, direction=LittleKiller.TOP_LEFT)
            ),
            4, 1
        )
        self.add_button(ComponentButton(self, EvenDigit(self.sudoku, 0)), 5, 0)
        self.add_button(ComponentButton(self, OddDigit(self.sudoku, 0)), 5, 1)
        self.add_button(ComponentButton(self, Thermometer(self.sudoku, SmartList())), 6, 0)
        self.add_button(ComponentButton(self, GermanWhispersLine(self.sudoku, SmartList())), 6, 1)
        self.add_button(ComponentButton(self, Cage(self.sudoku, SmartList(max_length=9))), 7, 0)
        self.add_button(ComponentButton(self, PalindromeLine(self.sudoku, SmartList())), 7, 1)
        self.add_button(ComponentButton(self, Arrow(self.sudoku, SmartList())), 8, 0)
        self.add_button(ComponentButton(self, BetweenLine(self.sudoku, SmartList())), 8, 1)
        self.add_button(ComponentButton(self, LockoutLine(self.sudoku, SmartList())), 9, 0)
        # self.add_button(ComponentButton(self, Clone(self.sudoku, SmartList())), 9, 1)

    def toggle_buttons(self):
        for button in self.component_group.buttons():
            button.setVisible(not button.isVisible())

    def add_button(self, button: ComponentButton, row: int, col: int, r_span: int = 1,
                   c_span: int = 1):
        self.component_group.addButton(button)
        self.layout_.addWidget(button, row, col, r_span, c_span)

    def set_component(self,
                      component: Component):
        self.window_.board.making_quadruple = isinstance(component, Quadruple)
        self.window_.board.current_component = copy.copy(component)
        self.window_.board.selected.clear()
        self.window_.update()

    def uncheck(self):
        self.digit_btn.setChecked(True)
        self.window_.board.current_component = None
        self.window_.board.selected.clear()



class ComponentButton(QPushButton):
    def __init__(
        self,
        parent: ComponentMenu,
        component: Component
    ):
        super().__init__(parent)

        self.menu = parent
        self.sudoku = parent.sudoku
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.setFixedHeight(40)

        self.component = component

        self.setCheckable(True)
        self.setChecked(False)

        self.setText(component.NAME)

        self.clicked.connect(lambda: self.menu.set_component(self.component))


class ConstraintsMenu(QFrame):
    def __init__(self, parent: "SudokuWindow"):
        super().__init__(parent)

        self.window_ = parent
        self.sudoku = parent.sudoku

        self.diagonal_positive = ConstraintCheckBox(self, "Diagonal +")
        self.diagonal_negative = ConstraintCheckBox(self, "Diagonal -")

        self.antiknight = ConstraintCheckBox(self, "Antiknight")
        self.antiking = ConstraintCheckBox(self, "Antiking")

        self.disjoint_groups = ConstraintCheckBox(self, "Disjoint Groups")
        self.nonconsecutive = ConstraintCheckBox(self, "Nonconsecutive")

        self.toggle_btn = QPushButton("Toggle Constraints")
        self.toggle_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toggle_btn.setMinimumWidth(200)
        self.toggle_btn.setFixedHeight(40)

        self.toggle_btn.clicked.connect(self.toggle_menu)

        self.layout_ = QHBoxLayout(self)
        self.layout_.setContentsMargins(10, 0, 10, 0)
        self.layout_.setSpacing(5)
        self.layout_.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.layout_.addWidget(self.toggle_btn)
        self.layout_.addWidget(self.diagonal_positive)
        self.layout_.addWidget(self.diagonal_negative)
        self.layout_.addWidget(self.antiknight)
        self.layout_.addWidget(self.antiking)
        self.layout_.addWidget(self.disjoint_groups)
        self.layout_.addWidget(self.nonconsecutive)

    def update(self) -> None:
        self.window_.update()
        self.diagonal_positive.setChecked(self.sudoku.diagonal_positive)
        self.diagonal_negative.setChecked(self.sudoku.diagonal_negative)

        self.antiknight.setChecked(self.sudoku.antiknight)
        self.antiking.setChecked(self.sudoku.antiking)
        self.disjoint_groups.setChecked(self.sudoku.disjoint_groups)
        self.nonconsecutive.setChecked(self.sudoku.nonconsecutive)

    def toggle_menu(self):
        for item in self.children():
            if not isinstance(item, ConstraintCheckBox):
                continue
            item.setVisible(not item.isVisible())

    def reset(self):
        for item in self.children():
            if not isinstance(item, ConstraintCheckBox):
                continue
            item.setChecked(False)


class ConstraintCheckBox(QCheckBox):
    def __init__(self, frame: ConstraintsMenu, name: str):
        super().__init__(frame)

        self.setText(name)
        self.setCheckable(True)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setFixedHeight(40)

        self.frame = frame
        self.name = name

        self.clicked.connect(
            self.toggle_constraint
        )

    def toggle_constraint(self):
        match self.name:
            case "Diagonal +":
                self.frame.sudoku.diagonal_positive = not self.frame.sudoku.diagonal_positive
            case "Diagonal -":
                self.frame.sudoku.diagonal_negative = not self.frame.sudoku.diagonal_negative
            case "Antiknight":
                self.frame.sudoku.antiknight = not self.frame.sudoku.antiknight
            case "Antiking":
                self.frame.sudoku.antiking = not self.frame.sudoku.antiking
            case "Disjoint Groups":
                self.frame.sudoku.disjoint_groups = not self.frame.sudoku.disjoint_groups
            case "Nonconsecutive":
                self.frame.sudoku.nonconsecutive = not self.frame.sudoku.nonconsecutive

        self.frame.update()
