import datetime
import time

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QCursor, QMouseEvent, QIcon, QResizeEvent, QEnterEvent, QAction, QColor, \
    QPaintEvent, QPainter, QFont, QPen
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QFrame, QHBoxLayout, QPushButton, \
    QWidget, QSizeGrip, QComboBox, QGridLayout, QMenu, QSizePolicy, QCheckBox, QApplication, \
    QLabel, QTextEdit

from board import SudokuBoard
from menus import ConstraintsMenu, ComponentMenu
from sudoku_.sudoku import Sudoku
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
            "QPushButton:hover{background: white; border: 2px solid #01C4FF }"
            "QPushButton:checked{border: 4px solid #01C4FF; border-radius: 5px; font-weight: bold}"
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

        self.sudoku = Sudoku()

        # self.sudoku.from_file(file_path=r"C:\Users\Cedric\PycharmProjects\Sudoku\Files\puzzles\Thermodrome2.json")

        ############################################################################################
        ############################################################################################

        self.central_frame = QFrame(self)
        self.central_frame.setObjectName("central")
        self.setCentralWidget(self.central_frame)

        self.title_bar = SudokuTitleBar(self)
        self.title_bar.move_center()

        self.mode_switch = QComboBox(self)
        self.mode_switch.addItems(["Normal", "Center", "Corner", "Color"])

        self.solve_btn = QPushButton("Solve")
        self.solve_btn.setCursor(QCursor(Qt.PointingHandCursor))

        self.clear_btn = QPushButton("Clear Grid")
        self.clear_btn.setCursor(QCursor(Qt.PointingHandCursor))

        self.save_btn = QPushButton("Save Grid")
        self.save_btn.setCursor(QCursor(Qt.PointingHandCursor))

        self.load_btn = QPushButton("Load Grid")
        self.load_btn.setCursor(QCursor(Qt.PointingHandCursor))

        self.highlight_cells_box = QCheckBox("Highlight Cells seen from selection", self)
        self.highlight_cells_box.setChecked(False)
        self.highlight_cells_box.clicked.connect(self.update)

        self.constraints_menu = ConstraintsMenu(self)
        self.component_menu = ComponentMenu(self)

        self.step_btn = QPushButton("Next step")

        self.rule_view = RuleView()
        self.generate_btn = QPushButton("Generate")

        self.digit_frame = DigitFrame(self)

        ############################################################################################

        self.central_layout = QVBoxLayout(self.central_frame)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.board = SudokuBoard(self, self.sudoku)
        self.solve_btn.clicked.connect(self.board.solve_board)
        self.clear_btn.clicked.connect(self.board.clear_grid)
        self.save_btn.clicked.connect(self.sudoku.to_file)
        self.load_btn.clicked.connect(self.load_sudoku)
        self.step_btn.clicked.connect(self.board.next_step)
        self.generate_btn.clicked.connect(self.board.generate_sudoku)

        self.mode_switch.currentIndexChanged.connect(
            lambda: self.board.setFocus()
        )
        self.mode_switch.currentIndexChanged.connect(
            self.digit_frame.set_mode
        )

        self.step_by_step_solve = QCheckBox("Step by Step")

        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(10)
        self.content_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.left_view = QFrame(self)
        self.left_view.setMinimumWidth(250)
        self.left_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.right_view = QFrame(self)
        self.right_view.setMinimumWidth(250)
        self.right_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.left_layout = QGridLayout(self.left_view)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(10)
        self.left_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.right_layout = QGridLayout(self.right_view)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(10)
        self.right_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.central_layout.addWidget(self.title_bar)
        self.central_layout.addWidget(self.constraints_menu)
        self.central_layout.addLayout(self.content_layout)

        self.content_layout.addWidget(self.left_view)
        self.content_layout.addWidget(self.board)
        self.content_layout.addWidget(self.right_view)

        self.left_layout.addWidget(self.save_btn, 0, 0, 1, 1)
        self.left_layout.addWidget(self.load_btn, 0, 1, 1, 1)
        self.left_layout.addWidget(self.highlight_cells_box, 1, 0, 1, 1)
        self.left_layout.addWidget(self.step_by_step_solve, 1, 1, 1, 1)
        self.left_layout.addWidget(self.solve_btn, 2, 0, 1, 1)
        self.left_layout.addWidget(self.step_btn, 2, 1, 1, 1)
        self.left_layout.addWidget(self.clear_btn, 3, 0, 1, 2)
        self.left_layout.addWidget(self.generate_btn, 4, 0, 1, 2)
        self.left_layout.addWidget(self.mode_switch, 5, 0, 1, 2)
        self.left_layout.addWidget(self.digit_frame, 6, 0, 2, 2)

        self.right_layout.addWidget(self.rule_view, 0, 0, 2, 1)
        self.right_layout.addWidget(self.component_menu, 2, 0, 2, 1)

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
        geom = QApplication.primaryScreen().geometry()
        self.window.setGeometry(0, 0, geom.width() * (3 / 4), geom.height() * (3 / 4))
        width, height = geom.width(), geom.height()

        x = (width - self.window.width()) // 2
        y = (height - self.window.height()) // 2

        self.window.move(x, y)


class RuleView(QFrame):
    def __init__(self):
        super().__init__()

        self.rules = []
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setStyleSheet("QFrame{border: 1px solid black}"
                           "QLabel{background: white; border: none}"
                           "QTextEdit{background: white; border: none; padding: 15px}")

        self.setMinimumWidth(200)

        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 0)
        self.layout_.setSpacing(0)

        self.title_label = QLabel("Rules")
        self.title_label.setFixedHeight(40)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.rules_edit = QTextEdit()
        self.rules_edit.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.rules_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.layout_.addWidget(self.title_label)
        self.layout_.addWidget(self.rules_edit)

    def add_rule(self, rule: str):
        if rule in self.rules:
            return

        self.rules.append(rule)
        self.rules_edit.setHtml("")

        html_text = "<ul>"
        for rule in self.rules:
            html_text += "<li>" + rule + "</li>"
        self.rules_edit.setHtml(html_text)

    def remove_rule(self, rule: str):
        pass

    def update(self):
        super(RuleView, self).update()


class DigitFrame(QFrame):
    def __init__(self, window: SudokuWindow):
        super().__init__()

        self.mode = 0

        self.window_ = window

        self.layout_ = QGridLayout(self)
        self.layout_.setContentsMargins(10, 10, 10, 10)
        self.layout_.setSpacing(10)

        self.btns = [DigitButton(self, i) for i in range(10)]

        for i in range(9):
            self.layout_.addWidget(self.btns[i], i // 3, i % 3)

    def set_mode(self):
        self.mode = self.window_.mode_switch.currentIndex()
        for i in range(9):
            self.btns[i].update()
        self.update()


class DigitButton(QWidget):
    COLORS = [
        QColor("#88C1F2"),  # Blue
        QColor("#F29494"),  # Red
        QColor("#DCF2AC"),  # Green

        QColor("#EAAEF2"),  # Purple
        QColor("#F2AB91"),  # Orange
        QColor("#F2DC99"),  # YELLOW

        QColor("#BBBBBB"),  # Light Gray
        QColor("#666666"),  # Dark Gray
        QColor("#000000"),  # Black
        QColor("#FFFFFF")  # White
    ]

    def __init__(self, menu: DigitFrame, index: int):
        super().__init__()

        self.menu = menu
        self.index = index
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.menu.window_.board.set_value(self.index + 1)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.setFixedHeight(self.width())
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        if self.menu.mode == 3:
            painter.fillRect(self.rect(), self.COLORS[self.index])

        else:

            alignment = Qt.AlignCenter
            painter.setFont(QFont("Asap", 25 if self.menu.mode == 0 else 16))

            if self.menu.mode == 2:

                match self.index:
                    case 0:
                        alignment = Qt.AlignTop | Qt.AlignLeft
                    case 1:
                        alignment = Qt.AlignTop | Qt.AlignHCenter
                    case 2:
                        alignment = Qt.AlignTop | Qt.AlignRight
                    case 3:
                        alignment = Qt.AlignVCenter | Qt.AlignLeft
                    case 4:
                        alignment = Qt.AlignVCenter | Qt.AlignHCenter
                    case 5:
                        alignment = Qt.AlignVCenter | Qt.AlignRight
                    case 6:
                        alignment = Qt.AlignBottom | Qt.AlignLeft
                    case 7:
                        alignment = Qt.AlignBottom | Qt.AlignHCenter
                    case 8:
                        alignment = Qt.AlignBottom | Qt.AlignRight
                    case _:
                        alignment = Qt.AlignCenter

            painter.drawText(self.rect(), alignment, str(self.index + 1))

        painter.setPen(QPen(Qt.black, 3.0))
        painter.drawLine(self.rect().bottomLeft(), self.rect().bottomRight())
