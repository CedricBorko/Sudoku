from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QMainWindow, QFileDialog


class LeftMenu(QFrame):
    def __init__(self, window: QMainWindow):
        super().__init__()

        self.window_ = window
        self.layout_ = QVBoxLayout(self)

        ############################################################################################
        ############################################################################################

        # STEPS
        # 1) Customer data input
        # 2) Power usage / cost input
        # 3) Calculate
        # 4) Output

        self.data_input_btn = QPushButton("Kundendaten")
        self.power_data_btn = QPushButton("Berechnung")
        self.data_output_btn = QPushButton("Ausgabe")

        self.layout_.addWidget(self.data_input_btn)
        self.layout_.addWidget(self.power_data_btn)
        self.layout_.addWidget(self.data_output_btn)

        self.data_input_btn.clicked.connect(lambda : self.window_.stack.setCurrentIndex(1))
        self.power_data_btn.clicked.connect(lambda : self.window_.stack.setCurrentIndex(2))
        self.data_output_btn.clicked.connect(self.window_.show_output)



