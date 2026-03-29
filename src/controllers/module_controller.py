from PyQt6.QtWidgets import QTableWidgetItem, QFileDialog, QHeaderView
from src.models.csv_handler import ModuleModel

class ModuleController:
    def __init__(self, view):
        self.view = view

        # Ubah teks tombol Refresh menjadi Import CSV
        self.view.btn_refresh_modules.setText("+ Import Module CSV")

        # Hubungkan tombol dengan fungsinya
        self.view.btn_refresh_modules.clicked.connect(self.handle_import)

        # Atur lebar kolom tabel agar menyesuaikan layar
        header = self.view.table_modules.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Topic
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Subtopic

        # Load tabel saat aplikasi pertama kali berjalan
        self.load_table_data()

    def load_table_data(self):
        """Mengambil rekap modul dari folder dan memasukkannya ke UI Tabel"""
        metadata_list = ModuleModel.get_all_modules_metadata()

        # Reset isi tabel
        self.view.table_modules.setRowCount(0)

        for row_index, data in enumerate(metadata_list):
            self.view.table_modules.insertRow(row_index)

            # Masukkan kolom demi kolom
            self.view.table_modules.setItem(row_index, 0, QTableWidgetItem(data['topic']))
            self.view.table_modules.setItem(row_index, 1, QTableWidgetItem(data['subtopic']))
            self.view.table_modules.setItem(row_index, 2, QTableWidgetItem(data['count']))
            self.view.table_modules.setItem(row_index, 3, QTableWidgetItem(data['difficulty']))

    def handle_import(self):
        """Membuka dialog file untuk memilih CSV dan mengimpornya"""
        # Buka jendela dialog file
        file_path, _ = QFileDialog.getOpenFileName(
            self.view,
            "Pilih File Module CSV",
            "",
            "CSV Files (*.csv)"
        )

        # Jika user memilih file (tidak membatalkan)
        if file_path:
            success = ModuleModel.import_module_csv(file_path)
            if success:
                self.view.show_popup("Module berhasil diimpor!")
                self.load_table_data() # Segarkan tabel
            else:
                self.view.show_popup("Gagal mengimpor module.")