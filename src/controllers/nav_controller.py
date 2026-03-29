from PyQt6.QtCore import QTimer

class NavController:
    def __init__(self, view):
        self.view = view

        self.progress = 0
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.update_loading)

        # Hubungkan tombol Sidebar ke Tab Content
        self.view.menu_dashboard_btn.clicked.connect(lambda: self.switch_main_tab(0))
        self.view.menu_module_btn.clicked.connect(lambda: self.switch_main_tab(1))
        self.view.menu_stats_btn.clicked.connect(lambda: self.switch_main_tab(2))

    def start_app(self):
        self.switch_page(0)
        self.view.setFixedSize(320, 180)
        self.view.center_window()
        self.loading_timer.start(10)

    def update_loading(self):
        self.progress += 2
        self.view.progressBar.setValue(self.progress)
        self.view.label_loading.setText(f"{self.progress}% loading...")

        if self.progress >= 100:
            self.loading_timer.stop()
            self.go_to_login()

    def go_to_login(self):
        self.view.setFixedSize(320, 240)
        self.view.center_window()
        self.switch_page(1)

    def go_to_dashboard(self, username):
        self.view.setMinimumSize(0, 0)
        self.view.setMaximumSize(16777215, 16777215)
        self.view.showMaximized()
        self.view.username_output.setText(f"{username} !")

        self.switch_page(2)
        self.switch_main_tab(0) # Default ke Dashboard

    def switch_page(self, index):
        self.view.stackedWidget.setCurrentIndex(index)

    def switch_main_tab(self, index):
        self.view.content_stackedWidget.setCurrentIndex(index)
        self.update_sidebar_styles(index)

    def update_sidebar_styles(self, index):
        """Mengubah warna tombol sidebar sesuai tab yang aktif"""
        active_style = """
            QPushButton { background-color: black; color: white; border-radius: 22px; font-family: Cambria; font-weight: bold; font-size: 15px; }
        """
        inactive_style = """
            QPushButton { background-color: #6c757d; color: white; border-radius: 22px; font-family: Cambria; font-weight: bold; font-size: 15px; }
        """

        self.view.menu_dashboard_btn.setStyleSheet(active_style if index == 0 else inactive_style)
        self.view.menu_module_btn.setStyleSheet(active_style if index == 1 else inactive_style)
        self.view.menu_stats_btn.setStyleSheet(active_style if index == 2 else inactive_style)