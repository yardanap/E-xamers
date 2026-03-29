import json
import os
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIntValidator
from PyQt6.QtWidgets import (QComboBox, QLineEdit, QAbstractItemView,
                             QTableWidgetItem, QWidget, QHBoxLayout, QLabel,
                             QPushButton, QDialog, QTextEdit, QVBoxLayout)
from src.models.csv_handler import ModuleModel
import random

class DashboardController:
    def __init__(self, view):
        self.view = view
        self.all_questions = []
        self.available_count = 0
        self.stats_file = "user_stats.json"

        self.setup_tables()
        self.setup_modes()
        self.setup_editable_inputs()

        self.view.btn_reset_stats.clicked.connect(self.reset_stats)

        self.refresh_dashboard_data()
        self.load_saved_stats()

    def setup_tables(self):
        self.view.table_modules.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.view.table_stats.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def load_saved_stats(self):
        self.view.table_stats.setRowCount(0)
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r") as f:
                    data = json.load(f)
                    for row in data:
                        self.render_stat_row(row)
            except Exception as e:
                print(f"Gagal memuat stats: {e}")

    def add_new_stat(self, stats, mode):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        raw = stats['raw_errors']

        row_data = [
            date_str, mode, stats['main_topic'], stats['score_text'],
            str(raw['Knowledge Gap']), str(raw['Guessing']),
            str(raw['Misread']), str(raw['Accident Click']),
            stats['full_report_plain']
        ]

        data = []
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r") as f:
                    data = json.load(f)
            except: pass
        data.append(row_data)

        with open(self.stats_file, "w") as f:
            json.dump(data, f)

        self.render_stat_row(row_data)

    def render_stat_row(self, row_data):
        table = self.view.table_stats
        row_idx = table.rowCount()
        table.insertRow(row_idx)

        for col in range(8):
            item = QTableWidgetItem(str(row_data[col]))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, col, item)

        full_text = row_data[8]
        short_text = full_text.split('\n')[0][:25] + "..." if full_text else "..."

        cell_widget = QWidget()
        layout = QHBoxLayout(cell_widget)
        layout.setContentsMargins(5, 2, 5, 2)

        lbl = QLabel(short_text)
        # Jangan set color di sini, biarkan inherit dari stylesheet QTableWidget kamu!

        btn = QPushButton("Expand")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("background-color: #3498db; color: white; border-radius: 4px; padding: 4px 10px; font-weight: bold;")
        btn.clicked.connect(lambda ch, text=full_text: self.show_full_report_dialog(text))

        layout.addWidget(lbl)
        layout.addWidget(btn)
        table.setCellWidget(row_idx, 8, cell_widget)
        table.resizeRowToContents(row_idx)

    def show_full_report_dialog(self, text):
        dialog = QDialog(self.view)
        dialog.setWindowTitle("Full Report Detail")
        dialog.resize(500, 450)
        dialog.setStyleSheet("background-color: #f4f6f9;")

        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(text)
        text_edit.setStyleSheet("color: black; background-color: white; font-family: Cambria; font-size: 14px; padding: 10px; border: 1px solid #ccc;")

        btn_close = QPushButton("Tutup")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("background-color: #e74c3c; color: white; padding: 8px; border-radius: 5px; font-weight: bold; font-family: Cambria; font-size: 14px;")
        btn_close.clicked.connect(dialog.accept)

        layout.addWidget(text_edit)
        layout.addWidget(btn_close)
        dialog.exec()

    def reset_stats(self):
        self.view.table_stats.setRowCount(0)
        if os.path.exists(self.stats_file):
            os.remove(self.stats_file)
        self.view.show_popup("Statistik berhasil direset!")

    def setup_modes(self):
        modes = ["Iterative", "Review", "Challenge", "Time Attack"]
        self.view.modes_selector.clear()
        self.view.modes_selector.addItems(modes)
        self.view.modes_selector.currentTextChanged.connect(self.handle_mode_change)

    def handle_mode_change(self, mode):
        """Timer DIMATIKAN di Iterative dan Review. HIDUP di Time Attack dan Challenge"""
        is_disabled = (mode in ["Iterative", "Review"])
        for box in self.timer_boxes:
            box.setEnabled(not is_disabled)
            if is_disabled:
                box.setText("0")
                box.setStyleSheet("background-color: #e0e0e0; color: #888888; border-radius: 8px;")
            else:
                box.setStyleSheet("background-color: white; color: black; border-radius: 8px;")

    def setup_editable_inputs(self):
        self.view.questionvalues_selector.setEditable(True)
        self.view.questionvalues_selector.lineEdit().setPlaceholderText("Ketik jumlah soal...")
        self.view.questionvalues_selector.lineEdit().setValidator(QIntValidator(1, 9999))
        self.view.questionvalues_selector.lineEdit().textChanged.connect(self.validate_question_value)

        self.timer_boxes = [self.view.t_h1, self.view.t_h2, self.view.t_m1, self.view.t_m2, self.view.t_s1, self.view.t_s2]
        for i, box in enumerate(self.timer_boxes):
            box.setMaxLength(1)
            box.setText("0")
            box.textEdited.connect(lambda text, idx=i: self.handle_timer_typing(text, idx))
            self.apply_auto_select(box)
        self.handle_mode_change(self.view.modes_selector.currentText())

    def apply_auto_select(self, box):
        box.focusInEvent = lambda e: QTimer.singleShot(0, box.selectAll)
        box.mousePressEvent = lambda e: QTimer.singleShot(0, box.selectAll)

    def handle_timer_typing(self, text, idx):
        if not text or not text.isdigit(): return
        val = int(text)
        if idx == 0 and val > 2: self.view.t_h1.setText('2')
        elif idx == 1 and self.view.t_h1.text() == '2' and val > 4: self.view.t_h2.setText('4')
        elif idx == 2 and val > 5: self.view.t_m1.setText('5')
        elif idx == 4 and val > 5: self.view.t_s1.setText('5')
        if idx < 5:
            self.timer_boxes[idx+1].setFocus()
            QTimer.singleShot(0, self.timer_boxes[idx+1].selectAll)

    def get_timer_value(self):
        v = [b.text() or "0" for b in self.timer_boxes]
        return f"{v[0]}{v[1]}:{v[2]}{v[3]}:{v[4]}{v[5]}"

    def get_test_preferences(self):
        mode = self.view.modes_selector.currentText()
        timer = self.get_timer_value()

        selected_topics = self.get_checked_items(self.view.Topic_selector)
        selected_subtopics = self.get_checked_items(self.view.subtopic_selector)
        selected_diffs = self.get_checked_items(self.view.difficulty_selector)

        filtered_pool = []
        for q in self.all_questions:
            t_match = q.get('topic', '').strip() in selected_topics
            s_match = not selected_subtopics or q.get('subtopic', '').strip() in selected_subtopics
            d_match = not selected_diffs or q.get('difficulty_levels', '').strip() in selected_diffs
            if t_match and s_match and d_match: filtered_pool.append(q)

        random.shuffle(filtered_pool)
        try: qty = int(self.view.questionvalues_selector.lineEdit().text())
        except: qty = 0
        final_questions = filtered_pool[:qty]

        return {
            'mode': mode, 'timer': timer, 'topics': ", ".join(selected_topics),
            'questions': final_questions, 'qty': len(final_questions)
        }

    def refresh_dashboard_data(self):
        self.all_questions = ModuleModel.get_raw_questions()
        topics = set(q.get('topic', '').strip() for q in self.all_questions if q.get('topic'))
        self.setup_checkable_combobox(self.view.Topic_selector, sorted(list(topics)), "Pilih Topic...", is_primary=True)
        self.reset_and_lock_combobox(self.view.subtopic_selector, "Pilih Subtopic...")
        self.reset_and_lock_combobox(self.view.difficulty_selector, "Pilih Kesulitan...")

    def reset_and_lock_combobox(self, cb, ph):
        cb.setModel(QStandardItemModel()); le = QLineEdit(); le.setReadOnly(True); le.setPlaceholderText(ph)
        cb.setLineEdit(le); cb.setEnabled(False)

    def setup_checkable_combobox(self, cb, items, ph, is_primary=False):
        model = QStandardItemModel(); cb.setModel(model); le = QLineEdit(); le.setReadOnly(True); le.setPlaceholderText(ph)
        cb.setLineEdit(le); cb.setEnabled(True)
        for t in items:
            item = QStandardItem(t); item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setData(Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole); model.appendRow(item)
        cb.setCurrentIndex(-1)
        model.itemChanged.connect(lambda i: QTimer.singleShot(10, lambda: self.update_combobox_text(cb)))
        if is_primary: model.itemChanged.connect(lambda i: QTimer.singleShot(20, self.update_dependent_dropdowns))
        else: model.itemChanged.connect(lambda i: QTimer.singleShot(20, self.calculate_available_questions))

    def update_dependent_dropdowns(self):
        st = self.get_checked_items(self.view.Topic_selector)
        if not st:
            self.reset_and_lock_combobox(self.view.subtopic_selector, "Pilih Subtopic..."); self.reset_and_lock_combobox(self.view.difficulty_selector, "Pilih Kesulitan...")
            self.available_count = 0; self.validate_question_value(); return
        vs, vd = set(), set()
        for q in self.all_questions:
            if q.get('topic', '').strip() in st:
                if q.get('subtopic'): vs.add(q.get('subtopic').strip())
                if q.get('difficulty_levels'): vd.add(q.get('difficulty_levels').strip())
        self.setup_checkable_combobox(self.view.subtopic_selector, sorted(list(vs)), "Pilih Subtopic...")
        self.setup_checkable_combobox(self.view.difficulty_selector, sorted(list(vd)), "Pilih Kesulitan...")
        self.calculate_available_questions()

    def update_combobox_text(self, cb):
        items = self.get_checked_items(cb)
        cb.lineEdit().setText(", ".join(items)) if items else cb.lineEdit().clear()

    def calculate_available_questions(self):
        st, ss, sd = self.get_checked_items(self.view.Topic_selector), self.get_checked_items(self.view.subtopic_selector), self.get_checked_items(self.view.difficulty_selector)
        if not st: self.available_count = 0
        else: self.available_count = sum(1 for q in self.all_questions if q.get('topic','').strip() in st and (not ss or q.get('subtopic','').strip() in ss) and (not sd or q.get('difficulty_levels','').strip() in sd))
        self.validate_question_value()

    def get_checked_items(self, cb):
        m = cb.model(); return [m.item(r).text() for r in range(m.rowCount()) if m.item(r).checkState() == Qt.CheckState.Checked]

    def validate_question_value(self):
        txt = self.view.questionvalues_selector.lineEdit().text()
        if not txt: return
        try:
            val, mx = int(txt), getattr(self, 'available_count', 0)
            if val > mx:
                self.view.show_popup(f"Modul soal tidak cukup! (Maks: {mx})")
                self.view.questionvalues_selector.lineEdit().blockSignals(True)
                self.view.questionvalues_selector.lineEdit().setText(str(mx) if mx > 0 else "")
                self.view.questionvalues_selector.lineEdit().blockSignals(False)
        except: pass