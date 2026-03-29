import os
import sys

def resource_path(relative_path):
    """
    Mendapatkan path absolut ke resource.
    Berfungsi saat menjalankan script Python biasa maupun setelah di-build jadi .exe (PyInstaller).
    """
    try:
        # PyInstaller menyimpan path sementara di _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)