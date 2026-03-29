from PyQt6.QtCore import QTimer
from src.models.csv_handler import AuthModel

class AuthController:
    def __init__(self, view, nav_controller):
        self.view = view
        self.nav = nav_controller

        # Hubungkan tombol login dengan fungsinya
        self.view.btn_login.clicked.connect(self.handle_login)

    def handle_login(self):
        """Logika pengecekan login user"""
        user_input = self.view.Input_user.text().strip()
        pass_input = self.view.Input_pass.text().strip()

        if not user_input or not pass_input:
            self.view.show_popup("Tolong isi Username & Password!")
            return

        # Panggil fungsi verify_login dari CSV handler
        login_success = AuthModel.verify_login(user_input, pass_input)

        if login_success:
            self.view.show_popup(f"Welcome {user_input}!")
            # Beri jeda 1.5 detik agar user bisa baca pop up, lalu pindah ke dashboard
            QTimer.singleShot(1500, lambda: self.nav.go_to_dashboard(user_input))
        else:
            self.view.show_popup("Login gagal! Cek lagi usn/pass.")