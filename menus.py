from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu

from components.border_constraints import XVSum, KropkiDot, LessGreater, Quadruple, Constraint
from components.line_constraints import Arrow, Thermometer, GermanWhispersLine, PalindromeLine


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

    def set_border_component(self, component: Constraint):
        self.window_.board.making_quadruple = isinstance(component, Quadruple)
        self.window_.board.border_component = component
        self.window_.board.cell_component = None

        self.window_.current_component_label.setText(f"Creating {component.NAME}")

    def set_cell_component(self, component: Constraint):
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


class ConstraintsMenu(QMenu):
    def __init__(self, parent: "SudokuWindow"):
        super().__init__(parent)

        self.setTitle("Constraints")

        self.window_ = parent
        self.sudoku = parent.sudoku

        self.diagonal_pos = ConstraintAction(self, "Diagonal +")
        self.diagonal_neg = ConstraintAction(self, "Diagonal -")

        self.antiknight = ConstraintAction(self, "Antiknight")
        self.antiking = ConstraintAction(self, "Antiking")

        self.disjoint_groups = ConstraintAction(self, "Disjoint Groups")
        self.nonconsecutive = ConstraintAction(self, "Nonconsecutive")

        self.addAction(self.diagonal_pos)
        self.addAction(self.diagonal_neg)
        self.addAction(self.antiknight)
        self.addAction(self.antiking)
        self.addAction(self.disjoint_groups)
        self.addAction(self.nonconsecutive)

    def update(self) -> None:
        self.window_.update()


class ConstraintAction(QAction):
    def __init__(self, parent: ConstraintsMenu, name: str):
        super().__init__(parent)

        self.setText(name)
        self.setCheckable(True)

        self.menu = parent
        self.name = name

        self.triggered.connect(
            self.toggle_constraint
        )

    def toggle_constraint(self):
        match self.name:
            case "Diagonal +":
                self.menu.sudoku.diagonal_positive = not self.menu.sudoku.diagonal_positive
            case "Diagonal -":
                self.menu.sudoku.diagonal_negative = not self.menu.sudoku.diagonal_negative
            case "Antiknight":
                self.menu.sudoku.antiknight = not self.menu.sudoku.antiknight
            case "Antiking":
                self.menu.sudoku.antiking = not self.menu.sudoku.antiking
            case "Disjoint Groups":
                self.menu.sudoku.disjoint_groups = not self.menu.sudoku.disjoint_groups
            case "Nonconsecutive":
                self.menu.sudoku.nonconsecutive = not self.menu.sudoku.nonconsecutive

        self.menu.parent().update()
