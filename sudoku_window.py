import datetime

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QCursor, QMouseEvent, QIcon, QResizeEvent, QEnterEvent, QAction
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QFrame, QHBoxLayout, QPushButton, \
    QWidget, QSizeGrip, QComboBox, QGridLayout, QMenu, QSizePolicy, QCheckBox, QApplication

from board import SudokuBoard
from components.cell_constraint import EvenDigit, OddDigit
from components.outside_components import Sandwich
from menus import ConstraintsMenu, ComponentMenu
from sudoku import Sudoku
from utils import monitor_size


class SudokuWindow(QMainWindow):
    RESIZE_GRIP_SIZE = 10

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.statusBar().hide()

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
            "QPushButton:checked{border: 4px solid #01C4FF; background: #CCCCCC; font-weight: bold}"
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

        self.sudoku = Sudoku.blank()

        ############################################################################################
        ############################################################################################

        self.central_frame = QFrame(self)
        self.central_frame.setObjectName("central")
        self.setCentralWidget(self.central_frame)

        self.title_bar = SudokuTitleBar(self)
        self.title_bar.move_center()

        self.mode_switch = QComboBox(self)
        self.mode_switch.setFixedHeight(40)
        self.mode_switch.addItems(["Normal", "Center", "Corner", "Color"])

        self.solve_btn = QPushButton("Solve")
        self.solve_btn.setFixedHeight(40)
        self.solve_btn.setMinimumWidth(150)
        self.solve_btn.setCursor(QCursor(Qt.PointingHandCursor))

        self.clear_btn = QPushButton("Clear Grid")
        self.clear_btn.setFixedHeight(40)
        self.clear_btn.setMinimumWidth(150)
        self.clear_btn.setCursor(QCursor(Qt.PointingHandCursor))

        self.save_btn = QPushButton("Save Grid")
        self.save_btn.setFixedHeight(40)
        self.save_btn.setMinimumWidth(200)
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))

        self.load_btn = QPushButton("Load Grid")
        self.load_btn.setFixedHeight(40)
        self.load_btn.setMinimumWidth(150)
        self.load_btn.setCursor(QCursor(Qt.PointingHandCursor))

        self.highlight_cells_box = QCheckBox("Highlight Cells seen from selection", self)
        self.highlight_cells_box.setChecked(False)
        self.highlight_cells_box.clicked.connect(self.update)

        self.constraints_menu = ConstraintsMenu(self)
        self.component_menu = ComponentMenu(self)

        ############################################################################################

        self.central_layout = QVBoxLayout(self.central_frame)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.board = SudokuBoard(self, self.sudoku)
        self.solve_btn.clicked.connect(self.board.solve_board)
        self.clear_btn.clicked.connect(self.board.clear_grid)
        self.save_btn.clicked.connect(self.sudoku.to_file)
        self.load_btn.clicked.connect(self.load_sudoku)

        self.mode_switch.currentIndexChanged.connect(
            lambda: self.board.setFocus()
        )

        self.content_layout = QGridLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)
        self.content_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.settings_layout = QGridLayout()
        self.settings_layout.setContentsMargins(10, self.board.cell_size, 10, 10)
        self.settings_layout.setSpacing(10)
        self.settings_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.central_layout.addWidget(self.title_bar)
        self.central_layout.addWidget(self.constraints_menu)
        self.central_layout.addLayout(self.content_layout)

        self.content_layout.addWidget(self.board, 0, 0, 1, 1)
        self.content_layout.addLayout(self.settings_layout, 0, 1, 1, 1)

        self.settings_layout.addWidget(self.component_menu, 0, 2, 2, 2)
        self.settings_layout.addWidget(self.mode_switch, 2, 2, 1, 1)
        self.settings_layout.addWidget(self.solve_btn, 2, 0, 1, 2)
        self.settings_layout.addWidget(self.clear_btn, 3, 0, 1, 2)
        self.settings_layout.addWidget(self.save_btn, 4, 0, 1, 2)
        self.settings_layout.addWidget(self.load_btn, 4, 2, 1, 2)

        self.settings_layout.addWidget(self.highlight_cells_box, 2, 3, 1, 1)

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

        self.board.setFocus()

    def load_sudoku(self):
        self.sudoku.from_file()
        self.constraints_menu.update()
        self.board.update()

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

    def create_new_sudoku(self):
        self.sudoku = Sudoku.blank()
        self.board.sudoku = self.sudoku
        self.constraints_menu.reset()
        self.update()


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

        # WIDGETS
        # ------------------------------------------------------------------------------------------

        self.grid_menu = QMenu(self)

        self.grid_menu_btn = QPushButton("Grid", self)
        self.grid_menu_btn.setFixedSize(2 * int(button_height * height),
                                        int(button_height * height))

        self.grid_menu_btn.setMenu(self.grid_menu)
        self.new_grid = QAction("New Grid")
        self.new_grid.triggered.connect(self.window.create_new_sudoku)
        self.grid_menu.addAction(self.new_grid)

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

        self.maximize_btn = QPushButton(self)
        self.maximize_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.maximize_btn.setObjectName("maximize_btn")
        self.maximize_btn.setFixedSize(int(height * button_height), int(height * button_height))
        self.maximize_btn.setToolTip("Maximize")
        self.maximize_btn.setIcon(QIcon("icons/maximize.svg"))

        self.restore_btn = QPushButton(self)
        self.restore_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.restore_btn.setObjectName("restore_btn")
        self.restore_btn.setFixedSize(int(height * button_height), int(height * button_height))
        self.restore_btn.setToolTip("Restore")
        self.restore_btn.hide()
        self.restore_btn.setIcon(QIcon("icons/minimize.svg"))

        self.exit_btn = QPushButton(self)
        self.exit_btn.setFixedSize(int(button_height * height), int(button_height * height))
        self.exit_btn.setObjectName("exit_btn")
        self.exit_btn.setToolTip("Exit")
        self.exit_btn.setIcon(QIcon("icons/x.svg"))

        # CONNECTIONS
        # ------------------------------------------------------------------------------------------

        self.minimize_btn.clicked.connect(self.window.showMinimized)
        self.maximize_btn.clicked.connect(self.maximize)
        self.restore_btn.clicked.connect(self.restore)
        self.exit_btn.clicked.connect(self.window.close)

        # LAYOUTS
        # ------------------------------------------------------------------------------------------

        self.layout_ = QHBoxLayout(self)
        self.layout_.setContentsMargins(5, 0, 5, 0)
        self.layout_.setSpacing(0)
        self.layout_.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        # FILL LAYOUTS
        # ------------------------------------------------------------------------------------------

        self.layout_.addWidget(self.grid_menu_btn)
        self.layout_.addStretch()
        self.layout_.addWidget(self.screenshot_btn)
        self.layout_.addWidget(self.minimize_btn)
        self.layout_.addWidget(self.maximize_btn)
        self.layout_.addWidget(self.restore_btn)
        self.layout_.addWidget(self.exit_btn)

    def maximize(self):
        self.restore_btn.show()
        self.maximize_btn.hide()

        self.window.showMaximized()
        self.maximized = True

    def restore(self):
        self.restore_btn.hide()
        self.maximize_btn.show()

        self.window.showNormal()
        self.maximized = False

        self.move_center()

    def mousePressEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.last_mouse_position = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.setCursor(QCursor(Qt.ArrowCursor))

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            if self.maximized:
                self.restore()

            self.window.move(self.window.pos() + (
                    event.pos() - self.last_mouse_position))

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            if self.maximized:
                self.restore()
            else:
                self.maximize()

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

    def move_center(self):
        width, height = monitor_size()
        screen = QApplication.primaryScreen()

        self.window.setGeometry(
            screen.geometry().width() // 2 - screen.geometry().width() // 2,
            screen.geometry().height() // 2 - screen.geometry().height() // 2,
            screen.geometry().width() // 2, screen.geometry().height() // 2
        )

        # surface: 2736 x 1824

