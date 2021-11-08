import datetime
import itertools
from datetime import date

from PySide6.QtCore import Qt, QTimer, QEvent, QPoint
from PySide6.QtGui import QCursor, QMouseEvent, QIcon, QResizeEvent, QEnterEvent, QPixmap, QAction
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QFrame, QLabel, QHBoxLayout, QPushButton, \
    QWidget, QSizeGrip, QComboBox, QGridLayout, QMenu, QSizePolicy, QCheckBox

from board import SudokuBoard
from components.border_constraints import KropkiDot, XVSum, LessGreater, Quadruple, Ratio, Difference

from menus import ConstraintsMenu, ComponentsMenu, ComponentMenu
from sudoku import Sudoku
from components.line_constraints import GermanWhispersLine, PalindromeLine, Thermometer, Arrow


class SudokuWindow(QMainWindow):
    RESIZE_GRIP_SIZE = 10

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.statusBar().hide()

        self.setFixedSize(1280, 900)

        self.setStyleSheet(
            "QSizeGrip{border: none}"
            "QWidget{font: 12pt Times New Roman}"
            "QFrame#title_bar{border: none; border-bottom: 1px solid #8A8A8A}"
            "QFrame#title_bar QPushButton{background: transparent; border: none; border-radius: 4px}"
            "QFrame#title_bar QPushButton:hover{background: #DDDDDD}"
            "QFrame#title_bar QPushButton:hover#exit_btn{background: #DC143C}"
            "QFrame#title_bar QLabel{font-weight: bold}"
            "QPushButton{background: transparent; border: 1px solid rgb(120, 120, 120)}"
            "QPushButton:hover{background: white}"
            "QMenu{background: white}"
            "QMenu:separator{background: #6A6A6A; height: 2px; margin: 4px}"
            "QMenu:item{padding-right: 10px; padding-left: 10px; height: 30px; width: 250px; border: none}"
            "QMenu:item:selected{background: #6495ED; color: white}"
            "QMenu:indicator:checked{image: url(icons/check.svg)}"
            "QMenu:indicator:!checked{image: url(icons/x_red.svg)}"
            "QMenu:icon{padding-left: 10px}"
            "QCheckBox:!checked{color: rgb(120, 120, 120)}"
            "QCheckBox:checked{color: rgb(0, 0, 0)}"


            "QCheckBox:indicator:checked{image: url(icons/check.svg)}"
            "QCheckBox:indicator:!checked{image: url(icons/x_red.svg)}"

        )

        ############################################################################################
        ############################################################################################

        self.adding_component = False

        self.sudoku = Sudoku.from_string(
            "000000000"
            "500000000"
            "000000000"
            "400000000"
            "200000000"
            "000000000"
            "000000000"
            "000000000"
            "300000000"
        )

        self.sudoku.border_constraints.append(Difference(self.sudoku, [4, 5], 5))
        self.sudoku.border_constraints.append(Difference(self.sudoku, [5, 6], 3))

        self.sudoku.border_constraints.append(Difference(self.sudoku, [13, 14], 2))
        self.sudoku.border_constraints.append(Difference(self.sudoku, [14, 15], 4))

        self.sudoku.calculate_valid_numbers()

        ############################################################################################
        ############################################################################################

        self.central_frame = QFrame(self)
        self.central_frame.setObjectName("central")
        self.setCentralWidget(self.central_frame)

        self.title_bar = SudokuTitleBar(self)

        self.mode_switch = QComboBox(self)
        self.mode_switch.setFixedHeight(40)
        self.mode_switch.addItems(["Normal", "Center", "Corner", "Color"])

        self.solve_btn = QPushButton("Solve")
        self.solve_btn.setFixedHeight(40)
        self.solve_btn.setCursor(QCursor(Qt.PointingHandCursor))

        self.highlight_cells_box = QCheckBox("Highlight Cells seen from selection", self)
        self.highlight_cells_box.setChecked(True)
        self.highlight_cells_box.clicked.connect(self.update)

        ############################################################################################

        self.component_menu = ComponentsMenu(self)

        self.component_btn = QPushButton("Components")
        self.component_btn.setMenu(self.component_menu)
        self.component_btn.setFixedHeight(40)
        self.component_btn.setMinimumWidth(200)

        self.constraints_menu = ConstraintsMenu(self)
        self.components_menu = ComponentMenu(self)

        self.current_component_label = QLabel(self)

        ############################################################################################

        self.board = SudokuBoard(self, self.sudoku)
        self.solve_btn.clicked.connect(self.board.solve_board)

        self.central_layout = QGridLayout(self.central_frame)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.settings_layout = QGridLayout()
        self.settings_layout.setContentsMargins(20, 20, 20, 20)
        self.settings_layout.setSpacing(10)

        self.components_layout = QGridLayout()
        self.components_layout.setContentsMargins(20, 20, 20, 20)
        self.components_layout.setSpacing(10)

        self.central_layout.addWidget(self.title_bar, 0, 0, 1, 1)

        self.content_layout = QGridLayout()
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(10)

        self.content_layout.addWidget(self.board, 0, 0, 2, 1)
        self.content_layout.addLayout(self.components_layout, 1, 1, 1, 1)

        self.components_layout.addWidget(self.constraints_menu, 0, 0, 1, 1)
        self.components_layout.addWidget(self.components_menu, 0, 1, 1, 1)
        self.components_layout.addWidget(self.current_component_label, 1, 0, 1, 1)

        self.settings_layout.addWidget(self.mode_switch, 0, 0, 1, 1)
        self.settings_layout.addWidget(self.solve_btn, 0, 1, 1, 1)
        self.settings_layout.addWidget(self.highlight_cells_box, 1, 0, 1, 1)

        self.central_layout.addLayout(self.content_layout, 1, 0, 1, 1)
        self.central_layout.addLayout(self.settings_layout, 2, 0, 1, 1)

        # Resizing

        self.size_grip_top_left = QSizeGrip(self)
        self.size_grip_top_left.setFixedSize(self.RESIZE_GRIP_SIZE, self.RESIZE_GRIP_SIZE)

        self.size_grip_top_right = QSizeGrip(self)
        self.size_grip_top_right.setFixedSize(self.RESIZE_GRIP_SIZE, self.RESIZE_GRIP_SIZE)

        self.size_grip_bottom_right = QSizeGrip(self)
        self.size_grip_bottom_right.setFixedSize(self.RESIZE_GRIP_SIZE, self.RESIZE_GRIP_SIZE)

        self.size_grip_bottom_left = QSizeGrip(self)
        self.size_grip_bottom_left.setFixedSize(self.RESIZE_GRIP_SIZE, self.RESIZE_GRIP_SIZE)

        self.size_grip_left = SizeGrip(self, Qt.LeftEdge)
        self.size_grip_top = SizeGrip(self, Qt.TopEdge)
        self.size_grip_right = SizeGrip(self, Qt.RightEdge)
        self.size_grip_bottom = SizeGrip(self, Qt.BottomEdge)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.board.resizeEvent(event)

        self.size_grip_top_left.move(0, 0)
        self.size_grip_top_right.move(self.width() - self.RESIZE_GRIP_SIZE, 0)

        self.size_grip_bottom_right.move(self.width() - self.RESIZE_GRIP_SIZE,
                                         self.height() - self.RESIZE_GRIP_SIZE)

        self.size_grip_bottom_left.move(0, self.height() - self.RESIZE_GRIP_SIZE)

        self.size_grip_left.setGeometry(
            0,
            self.RESIZE_GRIP_SIZE,
            self.RESIZE_GRIP_SIZE,
            self.height() - 2 * self.RESIZE_GRIP_SIZE
        )
        self.size_grip_top.setGeometry(
            self.RESIZE_GRIP_SIZE,
            0,
            self.width() - 2 * self.RESIZE_GRIP_SIZE,
            self.RESIZE_GRIP_SIZE
        )
        self.size_grip_right.setGeometry(
            self.width() - self.RESIZE_GRIP_SIZE,
            self.RESIZE_GRIP_SIZE,
            self.RESIZE_GRIP_SIZE,
            self.height() - 2 * self.RESIZE_GRIP_SIZE
        )
        self.size_grip_bottom.setGeometry(
            self.RESIZE_GRIP_SIZE,
            self.height() - self.RESIZE_GRIP_SIZE,
            self.width() - 2 * self.RESIZE_GRIP_SIZE,
            self.RESIZE_GRIP_SIZE
        )


class SizeGrip(QWidget):
    def __init__(self, parent: QWidget, pos):
        super().__init__(parent)

        self.window = parent
        self.position = pos

        self.RESIZE_GRIP_SIZE = self.window.RESIZE_GRIP_SIZE

        if pos in (Qt.LeftEdge, Qt.RightEdge):
            self.setMaximumWidth(self.RESIZE_GRIP_SIZE)
        else:
            self.setMaximumHeight(self.RESIZE_GRIP_SIZE)

    def enterEvent(self, event: QEnterEvent) -> None:

        if self.position in (Qt.LeftEdge, Qt.RightEdge):
            self.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.SizeVerCursor))

    def leaveEvent(self, event: QEvent) -> None:
        self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:

            if self.position == Qt.LeftEdge:

                delta = event.pos()
                width = max(self.window.minimumWidth(), self.window.width() - delta.x())
                geo = self.window.geometry()
                geo.setLeft(geo.right() - width)
                self.window.setGeometry(geo)

            elif self.position == Qt.TopEdge:
                delta = event.pos()
                height = max(self.window.minimumHeight(), self.window.height() - delta.y())
                geo = self.window.geometry()
                geo.setTop(geo.bottom() - height)
                self.window.setGeometry(geo)

            elif self.position == Qt.RightEdge:
                delta = event.pos()
                width = max(self.window.minimumWidth(), self.window.width() + delta.x())
                self.window.resize(width, self.window.height())

            else:  # BOTTOM

                delta = event.pos()
                height = max(self.window.minimumHeight(), self.window.height() + delta.y())
                self.window.resize(self.window.width(), height)


class SudokuTitleBar(QFrame):
    def __init__(self, window: QMainWindow, height: int = 40, button_height: float = 0.8):
        super().__init__()

        # VARIABLES
        # ------------------------------------------------------------------------------------------

        self.last_mouse_position = None
        self.window = window
        self.maximized = False

        # SETUP
        # ------------------------------------------------------------------------------------------

        self.setFixedHeight(height)
        self.setMouseTracking(True)
        self.setObjectName("title_bar")
        window.statusBar().setSizeGripEnabled(True)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.start_time = datetime.datetime.now()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.setInterval(1000)
        self.timer.start()

        # WIDGETS
        # ------------------------------------------------------------------------------------------

        self.title_label = QLabel(self)
        self.title_label.setObjectName("title_label")
        self.update_time()

        self.screenshot_btn = QPushButton(self)
        self.screenshot_btn.setObjectName("screenshot_btn")
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        self.screenshot_btn.setFixedSize(int(button_height * height), int(button_height * height))
        self.screenshot_btn.setToolTip("Screenshot")
        self.screenshot_btn.setIcon(QIcon("icons/image.svg"))

        self.minimize_btn = QPushButton(self)
        self.minimize_btn.setObjectName("minimize_btn")
        self.minimize_btn.setFixedSize(int(button_height * height), int(button_height * height))
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.setIcon(QIcon("icons/minus.svg"))

        self.exit_btn = QPushButton(self)
        self.exit_btn.setFixedSize(int(button_height * height), int(button_height * height))
        self.exit_btn.setObjectName("exit_btn")
        self.exit_btn.setToolTip("Exit")
        self.exit_btn.setIcon(QIcon("icons/x.svg"))

        # CONNECTIONS
        # ------------------------------------------------------------------------------------------

        self.minimize_btn.clicked.connect(self.window.showMinimized)
        self.exit_btn.clicked.connect(self.window.close)

        # LAYOUTS
        # ------------------------------------------------------------------------------------------

        self.layout_ = QHBoxLayout(self)
        self.layout_.setContentsMargins(5, 0, 5, 0)
        self.layout_.setSpacing(0)
        self.layout_.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        # FILL LAYOUTS
        # ------------------------------------------------------------------------------------------

        self.layout_.addWidget(self.title_label)
        self.layout_.addStretch()
        self.layout_.addWidget(self.screenshot_btn)
        self.layout_.addWidget(self.minimize_btn)
        self.layout_.addWidget(self.exit_btn)

    def mousePressEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.last_mouse_position = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.LeftButton:
            self.window.move(0, 0)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            new_pos = self.window.pos() + (event.pos() - self.last_mouse_position)
            if new_pos.x() < 0:
                new_pos.setX(0)
            if new_pos.y() < 0:
                new_pos.setY(0)

            self.window.move(new_pos)

    def take_screenshot(self):
        import datetime
        self.parent().grab().save(
            f"screenshots/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_img.png")

    def update_time(self):

        delta = datetime.datetime.now() - self.start_time
        minutes = delta.seconds // 60
        minutes = f"{minutes}" if minutes >= 10 else f"0{minutes}"
        seconds = f"{delta.seconds % 60}" if delta.seconds >= 10 else f"0{delta.seconds % 60}"

        self.title_label.setText(f"{minutes}:{seconds}")
