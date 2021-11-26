from __future__ import annotations
from PySide6.QtCore import QTimer, QRect, QObject, Signal, QThread, Qt
from PySide6.QtGui import QPaintEvent, QPainter, QPen, QColor, QImage, QFont
from PySide6.QtWidgets import QWidget, QMainWindow
from matplotlib import pyplot as plt


class Loader(QObject):
    progressChanged = Signal(int, float)
    finished = Signal()

    def __init__(self, lw: LoadingWidget):
        super().__init__()

        self.lw = lw
        self.data = ()

        self.progress = 0.0
        self.step = 1
        self.progressChanged.connect(self.set_progress)

    def set_progress(self, step: int = 1, progress: float = 0.0):
        self.progress = progress
        self.step = step

    def calculate(self):
        self.progress = 0.0
        self.data = self.lw.window_.lg_.calc_flexibiliserung(self)
        self.finished.emit()


class LoadingWidget(QWidget):
    def __init__(self, window: QMainWindow):
        super().__init__()

        self.window_ = window

        self.angle = 90

        self.timer = QTimer(self)
        self.timer.setInterval(8)
        self.timer.timeout.connect(self.onProgressChanged)

        self.loader = Loader(self)
        self.thread_ = QThread(self.loader)
        self.loader.moveToThread(self.thread_)

        self.loader.finished.connect(self.tidy_up_thread)
        self.thread_.started.connect(self.loader.calculate)

    def onProgressChanged(self):
        self.angle -= 1
        self.update()

    def start_animation(self):
        self.thread_.start()
        self.timer.start()

    def tidy_up_thread(self):
        self.thread_.quit()
        self.thread_.wait()
        self.timer.stop()
        self.window_.lg_.plot_flexibilisierung(*self.loader.data)
        self.window_.lg_.plot_lastgang()
        self.window_.lg_.plot_leistungskurve()

        plt.show()

        self.window_.stack.setCurrentWidget(self.window_.op)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        painter.drawRect(self.rect())

        size = min(self.width(), self.height()) // 2
        center = self.rect().center()

        rect = QRect(
            center.x() - size // 2, center.y() - size // 2, size, size
        )

        pen = QPen(QColor(170, 170, 170, 100), 10.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        painter.drawArc(
            rect, self.angle * 16, 360 * 16
        )

        pen = QPen(QColor("#008F9B"), 12.0)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        painter.setFont(QFont("Asap", 20))

        painter.drawText(
            rect, Qt.AlignCenter, f"{self.loader.progress} %"
        )

        painter.drawArc(
            rect, self.angle * 16, 90 * 16
        )
