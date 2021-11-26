from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QGridLayout


class Group(QGroupBox):
    def __init__(self, title: str, grid: bool = False):
        super().__init__()

        self.setTitle(title)

        self.layout_ = QVBoxLayout(self) if not grid else QGridLayout(self)
        self.layout_.setSpacing(5)
        self.layout_.setAlignment(Qt.AlignTop | Qt.AlignLeft)
