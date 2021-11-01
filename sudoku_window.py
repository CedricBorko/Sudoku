import datetime
import itertools
from datetime import date

from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QCursor, QMouseEvent, QIcon, QResizeEvent, QEnterEvent, QPixmap
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QFrame, QLabel, QHBoxLayout, QPushButton, \
    QWidget, QSizeGrip, QComboBox

from board import SudokuBoard
from components import Thermometer, Cage
from sudoku import Sudoku


class SudokuWindow(QMainWindow):
    RESIZE_GRIP_SIZE = 10

    def __init__(self):
        super().__init__()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.statusBar().hide()

        self.setFixedSize(770, 900)

        self.setStyleSheet(
            "QSizeGrip{border: none}"
            "QWidget{font: 12pt Times New Roman}"
            "QFrame#title_bar{border: none; border-bottom: 1px solid #8A8A8A}"
            "QFrame#title_bar QPushButton{background: transparent; border: none; border-radius: 4px}"
            "QFrame#title_bar QPushButton:hover{background: #DDDDDD}"
            "QFrame#title_bar QPushButton:hover#exit_btn{background: #DC143C}"
            "QFrame#title_bar QLabel{font-weight: bold}"
            "QPushButton{background: transparent; border: none}"
        )

        self.central_frame = QFrame(self)
        self.central_frame.setObjectName("central")
        self.setCentralWidget(self.central_frame)

        self.title_bar = SudokuTitleBar(self)
        self.mode_switch = QComboBox(self)
        self.mode_switch.addItems(["Normal", "Center", "Corner", "Color"])

        self.solve_btn = QPushButton("Solve")
        self.next_step_btn = QPushButton("Next Step")

        s = Sudoku.from_string(
            "000000000"
            "000000000"
            "000000000"
            "000000000"
            "000000000"
            "000000000"
            "000000000"
            "000000000"
            "000000000"
        )

        """s = Sudoku.from_string(
            "006300000"
            "700000008"
            "000000090"
            "002000040"
            "000000000"
            "000000050"
            "000050000"
            "009001005"
            "000000600"
        )"""

        s.diagonal_top_left = True
        s.diagonal_top_right = True

        s.thermometers.append(Thermometer(s, [18, 9, 0, 1, 11, 19]))
        s.thermometers.append(Thermometer(s, [54, 55, 64, 65]))
        s.thermometers.append(Thermometer(s, [64, 73]))
        s.thermometers.append(Thermometer(s, [78, 69, 60, 61, 62, 71, 80]))
        s.thermometers.append(Thermometer(s, [32, 31, 40, 49, 48]))
        s.thermometers.append(Thermometer(s, [15, 7, 16, 25]))

        s.cages.append(Cage([31, 40, 49], 12))
        s.cages.append(Cage([33, 42, 51], 24))
        s.cages.append(Cage([35, 44, 53], 15))
        s.cages.append(Cage([58, 67, 76], 24))
        s.cages.append(Cage([60, 69, 78], 15))
        s.cages.append(Cage([62, 71, 80], 6))

        self.board = SudokuBoard(self, s)
        # s.pencil_marks()

        self.solve_btn.clicked.connect(self.board.solve_board)
        self.next_step_btn.clicked.connect(self.board.next_step)

        self.central_layout = QVBoxLayout(self.central_frame)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        self.central_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.central_layout.addWidget(self.title_bar)
        self.central_layout.addWidget(self.board)
        self.central_layout.addWidget(self.mode_switch)
        self.central_layout.addSpacing(10)

        self.central_layout.addWidget(self.solve_btn)
        self.central_layout.addSpacing(10)
        self.central_layout.addWidget(self.next_step_btn)

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
        seconds = f"{delta.seconds}" if delta.seconds >= 10 else f"0{delta.seconds}"

        self.title_label.setText(f"{minutes}:{seconds}")
