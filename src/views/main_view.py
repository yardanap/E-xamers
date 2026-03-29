from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import QTimer
from PyQt6 import uic
from utils.path_helper import resource_path

class MainView(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load file UI dari folder src/ui/
        ui_path = resource_path("src/ui/main.ui")
        uic.loadUi(ui_path, self)

        # Sembunyikan popup di awal
        self.popup_frame.hide()

    def show_popup(self, text):
        """Fungsi dinamis untuk menampilkan notifikasi pop-up"""
        self.popup_label.setText(text)
        self.popup_frame.adjustSize()

        # Letakkan popup di tengah window
        x = (self.width() - self.popup_frame.width()) // 2
        y = (self.height() - self.popup_frame.height()) // 2
        self.popup_frame.move(x, y)

        self.popup_frame.raise_()
        self.popup_frame.show()

        # Sembunyikan otomatis setelah 1.5 detik
        QTimer.singleShot(1500, self.popup_frame.hide)

    def center_window(self):
        """Fungsi untuk meletakkan window tepat di tengah layar monitor"""
        frameGm = self.frameGeometry()
        screen = self.screen().availableGeometry().center()
        frameGm.moveCenter(screen)
        self.move(frameGm.topLeft())