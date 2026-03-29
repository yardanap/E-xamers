import sys
from PyQt6.QtWidgets import QApplication
from src.views.main_view import MainView
from src.controllers.nav_controller import NavController
from src.controllers.auth_controller import AuthController
from src.controllers.module_controller import ModuleController
from src.controllers.dashboard_controller import DashboardController
from src.controllers.exam_controller import ExamController
import os
# ... import lainnya ...

def resource_path(relative_path):
    """ Dapatkan path absolut, bekerja untuk dev dan untuk PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main():
    os.chdir(resource_path('.'))
    app = QApplication(sys.argv)
    view = MainView()

    # Inisialisasi Controller
    nav_controller = NavController(view)
    auth_controller = AuthController(view, nav_controller)
    module_controller = ModuleController(view)
    dashboard_controller = DashboardController(view)

    # Oper dashboard_controller ke dalam ExamController untuk auto-save
    exam_controller = ExamController(view, nav_controller, dashboard_controller)

    module_controller.view.btn_refresh_modules.clicked.connect(dashboard_controller.refresh_dashboard_data)

    def trigger_exam():
        prefs = dashboard_controller.get_test_preferences()
        if not prefs['questions'] or prefs['qty'] == 0:
            view.show_popup("Pilih Topik dan pastikan jumlah soal Valid!")
            return
        exam_controller.start_exam(prefs)

    view.start_test_btn.clicked.connect(trigger_exam)

    nav_controller.start_app()
    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()