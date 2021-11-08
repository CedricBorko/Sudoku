from __future__ import annotations

from typing import Type

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QCheckBox, QWidget, QFrame, QVBoxLayout, QLabel, QPushButton, QButtonGroup

from components.border_constraints import XVSum, KropkiDot, LessGreater, Quadruple, Component, BorderComponent
from components.line_constraints import Arrow, Thermometer, GermanWhispersLine, PalindromeLine, LineComponent
from components.region_constraints import RegionComponent


class ComponentsMenu(QMenu):
    def __init__(self, window: "SudokuWindow"):
        super().__init__(window)

        self.setTitle("Components")

        self.window_ = window
        self.sudoku = window.sudoku

        self.kropki_menu = KropkiSubMenu(self)
        self.xv_menu = XVSubMenu(self)
        self.less_greater = LessGreaterSubMenu(self)

        self.quadruple_action = QAction("Quadruple")
        self.quadruple_action.triggered.connect(
            lambda: self.set_border_component(Quadruple(self.sudoku, [], []))
        )

        self.thermometer_action = QAction("Thermometer")
        self.thermometer_action.triggered.connect(
            lambda: self.set_cell_component(Thermometer(self.sudoku, []))
        )

        self.german_whispers_action = QAction("German Whispers")
        self.german_whispers_action.triggered.connect(
            lambda: self.set_cell_component(GermanWhispersLine(self.sudoku, []))
        )

        self.palindrome_action = QAction("Palindrome")
        self.palindrome_action.triggered.connect(
            lambda: self.set_cell_component(PalindromeLine(self.sudoku, []))
        )

        self.addMenu(self.kropki_menu)
        self.addMenu(self.xv_menu)
        self.addMenu(self.less_greater)
        self.addAction(self.quadruple_action)
        self.addAction(self.thermometer_action)
        self.addAction(self.german_whispers_action)
        self.addAction(self.palindrome_action)

    def update(self) -> None:
        self.window_.update()

    def set_border_component(self, component: Component):
        self.window_.board.making_quadruple = isinstance(component, Quadruple)
        self.window_.board.border_component = component
        self.window_.board.cell_component = None

        self.window_.current_component_label.setText(f"Creating {component.NAME}")

    def set_cell_component(self, component: Component):
        self.window_.board.border_component = None
        self.window_.board.cell_component = component
        self.window_.current_component_label.setText(f"Creating {component.NAME}")


class KropkiSubMenu(QMenu):
    def __init__(self, parent: ComponentsMenu):
        super().__init__(parent)

        self.setTitle("Kropki Dot")

        self.menu = parent

        self.white = ComponentAction(self, "White")
        self.black = ComponentAction(self, "Black")

        self.white.triggered.connect(
            lambda: self.menu.set_border_component(KropkiDot(self.menu.sudoku, [], True))
        )

        self.black.triggered.connect(
            lambda: self.menu.set_border_component(KropkiDot(self.menu.sudoku, [], False))
        )

        self.addAction(self.white)
        self.addAction(self.black)


class XVSubMenu(QMenu):
    def __init__(self, parent: ComponentsMenu):
        super().__init__(parent)

        self.setTitle("XV Sum")

        self.menu = parent

        self.v_sum = ComponentAction(self, "V")
        self.x_sum = ComponentAction(self, "X")
        self.xv_sum = ComponentAction(self, "XV")

        self.v_sum.triggered.connect(
            lambda: self.menu.set_border_component(XVSum(self.menu.sudoku, [], 5))
        )

        self.x_sum.triggered.connect(
            lambda: self.menu.set_border_component(XVSum(self.menu.sudoku, [], 10))
        )

        self.xv_sum.triggered.connect(
            lambda: self.menu.set_border_component(XVSum(self.menu.sudoku, [], 15))
        )

        self.addAction(self.v_sum)
        self.addAction(self.x_sum)
        self.addAction(self.xv_sum)


class LessGreaterSubMenu(QMenu):
    def __init__(self, parent: ComponentsMenu):
        super().__init__(parent)

        self.setTitle("Less / Greater")

        self.menu = parent

        self.less = ComponentAction(self, "Less")
        self.greater = ComponentAction(self, "Greater")

        self.less.triggered.connect(
            lambda: self.menu.set_border_component(LessGreater(self.menu.sudoku, [], True))
        )

        self.greater.triggered.connect(
            lambda: self.menu.set_border_component(LessGreater(self.menu.sudoku, [], False))
        )

        self.addAction(self.less)
        self.addAction(self.greater)


class ComponentAction(QAction):

    def __init__(self, parent: QMenu, name: str, border: bool = False):
        super().__init__(parent)

        self.setText(name)

        self.menu = parent
        self.name = name
        self.is_border_component = border

    def set_component(self):

        if self.is_border_component:
            match self.name:

                case "White":
                    pass


class ComponentMenu(QFrame):
    def __init__(self, parent: "SudokuWindow"):
        super().__init__(parent)

        self.window_ = parent
        self.sudoku = parent.sudoku

        self.component_group = QButtonGroup()

        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(5)

        self.add_button(ComponentButton(self, KropkiDot))

    def add_button(self, button: ComponentButton):
        self.component_group.addButton(button)
        self.layout_.addWidget(button)

    def set_component(self, component: BorderComponent | LineComponent | RegionComponent):
        print(component)


class ComponentButton(QPushButton):
    def __init__(
            self,
            parent: ComponentMenu,
            component: Type[BorderComponent] | Type[LineComponent] | Type[RegionComponent]
    ):
        super().__init__(parent)

        self.menu = parent
        self.sudoku = parent.sudoku

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

        self.diagonal_pos = ConstraintCheckBox(self, "Diagonal +")
        self.diagonal_neg = ConstraintCheckBox(self, "Diagonal -")

        self.antiknight = ConstraintCheckBox(self, "Antiknight")
        self.antiking = ConstraintCheckBox(self, "Antiking")

        self.disjoint_groups = ConstraintCheckBox(self, "Disjoint Groups")
        self.nonconsecutive = ConstraintCheckBox(self, "Nonconsecutive")

        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(5)

        self.layout_.addWidget(QLabel("Constraints", self))
        self.layout_.addWidget(self.diagonal_pos)
        self.layout_.addWidget(self.diagonal_neg)
        self.layout_.addWidget(self.antiknight)
        self.layout_.addWidget(self.antiking)
        self.layout_.addWidget(self.disjoint_groups)
        self.layout_.addWidget(self.nonconsecutive)

    def update(self) -> None:
        self.window_.update()


class ConstraintCheckBox(QCheckBox):
    def __init__(self, frame: QFrame, name: str):
        super().__init__(frame)

        self.setText(name)
        self.setCheckable(True)

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
