from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QTableWidgetItem, QFrame, QVBoxLayout, QLabel, QPushButton
from src.models.iterative_engine import IterativeEngine
from src.models.review_engine import ReviewEngine

class ExamController:
    def __init__(self, view, nav_controller, dashboard_controller):
        self.view = view
        self.nav = nav_controller
        self.dashboard = dashboard_controller
        self.engine = None
        self.current_mode = ""
        self.is_showing_explanation = False
        self.last_answer_correct = False
        self.is_review_classification_phase = False

        self.setup_timeout_popup()

        self.stopwatch_timer = QTimer()
        self.stopwatch_timer.timeout.connect(self.update_timer)
        self.seconds_elapsed = 0
        self.time_per_question = 0
        self.question_time_left = 0
        self.challenge_total_sec = 0
        self.global_time_left = 0

        self.view.frame_evaluation.hide()
        self.view.report_frame.hide()

        self.view.btn_exam_next.clicked.connect(self.handle_next_action)
        self.view.btn_exam_prev.clicked.connect(self.handle_prev_action)
        self.view.btn_exam_flag.clicked.connect(self.handle_flag_action)
        self.view.btn_exam_finish.clicked.connect(self.finish_exam)
        self.view.btn_close_report.clicked.connect(self.close_report_and_exit)

        for radio in [self.view.radio_A, self.view.radio_B, self.view.radio_C, self.view.radio_D, self.view.radio_E]:
            radio.clicked.connect(self.on_radio_clicked)

    def setup_timeout_popup(self):
        self.timeout_frame = QFrame(self.view.page_exam)
        self.timeout_frame.resize(260, 100)
        self.timeout_frame.setStyleSheet("background-color: #fdfefe; border: 2px solid #e74c3c; border-radius: 10px;")
        self.timeout_layout = QVBoxLayout(self.timeout_frame)
        self.timeout_label = QLabel("WAKTU HABIS!")
        self.timeout_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timeout_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 16px; border: none;")
        self.timeout_btn = QPushButton("Lanjut Soal Berikutnya")
        self.timeout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.timeout_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        self.timeout_btn.clicked.connect(self.handle_timeout_next)
        self.timeout_layout.addWidget(self.timeout_label)
        self.timeout_layout.addWidget(self.timeout_btn)
        self.timeout_frame.hide()

        original_resize = self.view.page_exam.resizeEvent
        def responsive_resize(event):
            original_resize(event)
            self.timeout_frame.move(self.view.page_exam.width() - self.timeout_frame.width() - 30, 70)
        self.view.page_exam.resizeEvent = responsive_resize

    def start_exam(self, config):
        self.current_mode = config['mode']
        self.view.report_frame.hide()
        self.timeout_frame.hide()
        self.view.exam_mode_label.setText(f"Mode: {self.current_mode}")

        self.view.combo_error_class.clear()
        self.view.combo_error_class.addItems(["-- Pilih Klasifikasi --", "Knowledge Gap", "Guessing", "Misread", "Accident Click", "Waktu Habis", "Tidak Terjawab"])

        if self.current_mode in ["Iterative", "Time Attack"]:
            self.engine = IterativeEngine(config)
            self.view.frame_question_grid.hide()
            self.view.btn_exam_prev.hide()
            self.view.btn_exam_flag.hide()
            if hasattr(self, 'submit_grid_btn'): self.submit_grid_btn.hide()

            if self.current_mode == "Time Attack":
                h, m, s = map(int, config['timer'].split(':'))
                total_sec = h * 3600 + m * 60 + s
                qty = config['qty']
                self.time_per_question = max(1, total_sec // qty) if qty > 0 else 60
                self.question_time_left = self.time_per_question
            else:
                self.seconds_elapsed = 0
            self.stopwatch_timer.start(1000)

        elif self.current_mode in ["Review", "Challenge"]:
            self.engine = ReviewEngine(config)
            self.is_review_classification_phase = False

            self.view.frame_question_grid.show()
            self.view.btn_exam_prev.show()
            self.view.btn_exam_flag.show()
            self.setup_review_grid()

            if self.current_mode == "Challenge":
                h, m, s = map(int, config['timer'].split(':'))
                self.challenge_total_sec = h * 3600 + m * 60 + s
                self.global_time_left = self.challenge_total_sec
                self.update_timer_display(self.global_time_left)
            else:
                self.seconds_elapsed = 0
                self.update_timer_display(0)

            self.stopwatch_timer.start(1000)

        self.view.stackedWidget.setCurrentIndex(3)
        self.load_question()

    def setup_review_grid(self):
        while self.view.gridLayout_question_numbers.count():
            item = self.view.gridLayout_question_numbers.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self.view.scrollAreaGridContents.setStyleSheet("background-color: #ffffff;")
        self.view.frame_question_grid.setStyleSheet("background-color: #ffffff; border-left: 2px solid #e0e0e0;")

        self.view.gridLayout_question_numbers.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.view.gridLayout_question_numbers.setSpacing(8)

        self.grid_buttons = []
        for i in range(len(self.engine.questions)):
            btn = QPushButton(str(i + 1))
            btn.setFixedSize(40, 40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda ch, idx=i: self.jump_to_question(idx))
            self.view.gridLayout_question_numbers.addWidget(btn, i // 5, i % 5)
            self.grid_buttons.append(btn)

        if not hasattr(self, 'submit_grid_btn'):
            self.submit_grid_btn = QPushButton("Submit Test")
            self.submit_grid_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.submit_grid_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px; border-radius: 5px; margin-top: 10px;")
            self.submit_grid_btn.clicked.connect(self.initiate_review_submit)
            self.view.verticalLayout_grid.addWidget(self.submit_grid_btn)
        self.submit_grid_btn.show()

    def update_grid_colors(self):
        if self.current_mode not in ["Review", "Challenge"]: return
        for i, btn in enumerate(self.grid_buttons):
            style = "font-weight: bold; border-radius: 5px; border: 1px solid black; "

            if self.is_review_classification_phase:
                user_ans = self.engine.answers.get(i, "")
                if user_ans == "": bg, fg = "white", "black"
                elif i in self.engine.wrong_indices: bg, fg = "#e74c3c", "white"
                else: bg, fg = "#27ae60", "white"
            else:
                if i in self.engine.flags: bg, fg = "#f39c12", "white"
                elif i in self.engine.answers: bg, fg = "#3498db", "white"
                else: bg, fg = "white", "black"

            style += f"background-color: {bg}; color: {fg};"
            if i == self.engine.current_idx: style += " border: 3px solid #2c3e50;"
            btn.setStyleSheet(style)

    def update_timer(self):
        if self.current_mode in ["Iterative", "Review"]:
            self.seconds_elapsed += 1
            self.update_timer_display(self.seconds_elapsed)
        elif self.current_mode == "Time Attack":
            if self.question_time_left > 0:
                self.question_time_left -= 1
                self.update_timer_display(self.question_time_left)
                if self.question_time_left <= 0 and not self.is_showing_explanation:
                    self.trigger_timeout()
        elif self.current_mode == "Challenge":
            if not self.is_review_classification_phase:
                if self.global_time_left > 0:
                    self.global_time_left -= 1
                    self.update_timer_display(self.global_time_left)
                    if self.global_time_left <= 0:
                        self.trigger_timeout()

    def update_timer_display(self, secs):
        h = secs // 3600; m = (secs % 3600) // 60; s = secs % 60
        self.view.exam_timer_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def get_time_string(self):
        if self.current_mode == "Challenge":
            spent = self.challenge_total_sec - self.global_time_left
            h = spent // 3600; m = (spent % 3600) // 60; s = spent % 60
            return f"{h:02d}:{m:02d}:{s:02d}"
        else:
            h = self.seconds_elapsed // 3600; m = (self.seconds_elapsed % 3600) // 60; s = self.seconds_elapsed % 60
            return f"{h:02d}:{m:02d}:{s:02d}"

    def load_question(self):
        q = self.engine.get_current_question()
        if not q: return self.finish_exam()

        self.timeout_frame.hide()
        self.view.btn_exam_next.show()
        self.view.btn_exam_finish.hide()

        self.view.exam_question_text.setText(f"<b>Pertanyaan {self.engine.current_idx + 1}</b><br><br>{q.get('question', '')}")

        self.block_radios(True)
        for r in [self.view.radio_A, self.view.radio_B, self.view.radio_C, self.view.radio_D, self.view.radio_E]:
            r.setAutoExclusive(False); r.setChecked(False); r.setAutoExclusive(True); r.setEnabled(True)
        self.view.radio_A.setText(f"A. {q.get('A', '')}")
        self.view.radio_B.setText(f"B. {q.get('B', '')}")
        self.view.radio_C.setText(f"C. {q.get('C', '')}")
        self.view.radio_D.setText(f"D. {q.get('D', '')}")
        self.view.radio_E.setText(f"E. {q.get('E', '')}")

        # ==== LOGIKA REVIEW & CHALLENGE ====
        if self.current_mode in ["Review", "Challenge"]:
            saved_ans = self.engine.answers.get(self.engine.current_idx, "")
            if saved_ans == "A": self.view.radio_A.setChecked(True)
            elif saved_ans == "B": self.view.radio_B.setChecked(True)
            elif saved_ans == "C": self.view.radio_C.setChecked(True)
            elif saved_ans == "D": self.view.radio_D.setChecked(True)
            elif saved_ans == "E": self.view.radio_E.setChecked(True)

            self.update_grid_colors()

            if self.is_review_classification_phase:
                self.view.frame_evaluation.show()
                for r in [self.view.radio_A, self.view.radio_B, self.view.radio_C, self.view.radio_D, self.view.radio_E]:
                    r.setEnabled(False)

                correct_ans = str(q.get('answer', '')).strip().upper()
                user_ans = saved_ans if saved_ans else "KOSONG"
                is_correct = (user_ans == correct_ans) and user_ans != "KOSONG"

                self.view.eval_explanation_text.setText(f"<b>Jawaban Anda: {user_ans} | Kunci: {correct_ans}</b><br><br><b>Pembahasan:</b><br>{q.get('explanation', '')}")
                self.view.combo_error_class.setEnabled(True) # Pastikan terbuka dulu

                if is_correct:
                    self.view.eval_result_label.setText("JAWABAN BENAR")
                    self.view.eval_result_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                    self.view.label_error_class.hide(); self.view.combo_error_class.hide()
                else:
                    self.view.eval_result_label.setText("JAWABAN SALAH / KOSONG")
                    self.view.eval_result_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                    self.view.label_error_class.show(); self.view.combo_error_class.show()

                    # LOGIKA CHALLENGE: Kunci "Tidak Terjawab" otomatis
                    if self.current_mode == "Challenge" and user_ans == "KOSONG":
                        idx = self.view.combo_error_class.findText("Tidak Terjawab")
                        if idx >= 0: self.view.combo_error_class.setCurrentIndex(idx)
                        self.view.combo_error_class.setEnabled(False) # Kunci mati agar user tidak perlu milih
                    else:
                        if self.engine.current_idx in self.engine.performance_log:
                            prev = self.engine.performance_log[self.engine.current_idx]['error_type']
                            idx = self.view.combo_error_class.findText(prev)
                            if idx >= 0: self.view.combo_error_class.setCurrentIndex(idx)
                        else:
                            self.view.combo_error_class.setCurrentIndex(0)

                if self.engine.current_idx == len(self.engine.questions) - 1:
                    self.view.btn_exam_next.setText("Selesai & Lihat Laporan")
                else:
                    self.view.btn_exam_next.setText("Lanjut ke Soal Berikutnya")
            else:
                self.view.frame_evaluation.hide()
                if self.engine.current_idx == len(self.engine.questions) - 1:
                    self.view.btn_exam_next.hide()
                    self.view.btn_exam_finish.show()
                    self.view.btn_exam_finish.setText("Finish Test")
                else:
                    self.view.btn_exam_next.setText("Lanjut")

        # ==== LOGIKA ITERATIVE / TIME ATTACK ====
        elif self.current_mode in ["Iterative", "Time Attack"]:
            self.is_showing_explanation = False
            self.view.frame_evaluation.hide()
            self.view.combo_error_class.setCurrentIndex(0)
            self.view.btn_exam_next.setText("Submit Jawaban")

            if self.current_mode == "Time Attack":
                self.question_time_left = self.time_per_question
                self.update_timer_display(self.question_time_left)
                self.stopwatch_timer.start(1000)

        self.block_radios(False)

    def block_radios(self, state):
        for r in [self.view.radio_A, self.view.radio_B, self.view.radio_C, self.view.radio_D, self.view.radio_E]:
            r.blockSignals(state)

    def on_radio_clicked(self):
        if self.current_mode in ["Review", "Challenge"] and not self.is_review_classification_phase:
            ans = self.get_selected_answer()
            if ans:
                self.engine.set_answer(ans)
                self.update_grid_colors()

    def jump_to_question(self, idx):
        if self.current_mode in ["Review", "Challenge"]:
            if self.is_review_classification_phase and self.engine.current_idx in self.engine.wrong_indices:
                if self.view.combo_error_class.isEnabled() and self.view.combo_error_class.currentIndex() == 0:
                    self.view.show_popup("Pilih Klasifikasi Kesalahan terlebih dahulu!")
                    return
                self.engine.log_error_classification(self.engine.current_idx, self.view.combo_error_class.currentText())

            self.engine.current_idx = idx
            self.load_question()

    def handle_prev_action(self):
        if self.current_mode in ["Review", "Challenge"]:
            if self.engine.current_idx > 0:
                if self.is_review_classification_phase and self.engine.current_idx in self.engine.wrong_indices:
                    if self.view.combo_error_class.isEnabled() and self.view.combo_error_class.currentIndex() == 0:
                        self.view.show_popup("Pilih Klasifikasi Kesalahan terlebih dahulu!")
                        return
                    self.engine.log_error_classification(self.engine.current_idx, self.view.combo_error_class.currentText())
                self.engine.current_idx -= 1
                self.load_question()

    def handle_flag_action(self):
        if self.current_mode in ["Review", "Challenge"] and not self.is_review_classification_phase:
            self.engine.toggle_flag()
            self.update_grid_colors()

    def initiate_review_submit(self):
        self.stopwatch_timer.stop()
        self.engine.calculate_score()
        self.view.show_popup(f"Ujian disubmit!\nMari bahas soal dan pelajari klasifikasi kesalahan Anda.")

        self.is_review_classification_phase = True
        self.engine.current_idx = 0

        self.view.frame_question_grid.show()
        self.view.btn_exam_prev.show()
        self.view.btn_exam_flag.hide()
        if hasattr(self, 'submit_grid_btn'): self.submit_grid_btn.hide()
        self.view.btn_exam_next.show()

        self.load_question()

    def handle_next_action(self):
        if self.current_mode in ["Iterative", "Time Attack"]:
            self.handle_iterative_next()
        elif self.current_mode in ["Review", "Challenge"]:
            self.handle_review_next()

    def handle_review_next(self):
        if self.is_review_classification_phase:
            if self.engine.current_idx in self.engine.wrong_indices:
                if self.view.combo_error_class.isEnabled() and self.view.combo_error_class.currentIndex() == 0:
                    self.view.show_popup("Pilih Klasifikasi Kesalahan terlebih dahulu!")
                    return
                self.engine.log_error_classification(self.engine.current_idx, self.view.combo_error_class.currentText())

            if self.engine.current_idx == len(self.engine.questions) - 1:
                self.finish_exam()
            else:
                self.engine.current_idx += 1
                self.load_question()
        else:
            if self.engine.current_idx == len(self.engine.questions) - 1:
                self.view.show_popup("Gunakan tombol 'Submit Test' atau 'Finish Test' untuk mengakhiri.")
            else:
                self.engine.current_idx += 1
                self.load_question()

    def handle_iterative_next(self):
        # ... logic unchanged ...
        if not self.is_showing_explanation:
            selected = self.get_selected_answer()
            if not selected:
                self.view.show_popup("Pilih salah satu jawaban dulu!")
                return
            self.stopwatch_timer.stop()
            self.last_answer_correct, correct_ans, explanation = self.engine.check_answer(selected)
            self.view.frame_evaluation.show()
            self.view.eval_explanation_text.setText(f"<b>Kunci Jawaban: {correct_ans}</b><br><br><b>Pembahasan:</b><br>{explanation}")

            if self.last_answer_correct:
                self.view.eval_result_label.setText("JAWABAN ANDA BENAR!")
                self.view.eval_result_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                self.view.label_error_class.hide(); self.view.combo_error_class.hide()
            else:
                self.view.eval_result_label.setText("JAWABAN ANDA SALAH!")
                self.view.eval_result_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                self.view.label_error_class.show(); self.view.combo_error_class.show()
            self.is_showing_explanation = True

            if self.engine.current_idx == len(self.engine.questions) - 1:
                self.view.btn_exam_next.hide(); self.view.btn_exam_finish.show(); self.view.btn_exam_finish.setText("Selesai & Lihat Hasil")
            else:
                self.view.btn_exam_next.setText("Lanjut ke Soal Berikutnya")
        else:
            if not self.last_answer_correct:
                if self.view.combo_error_class.currentIndex() == 0:
                    self.view.show_popup("Pilih Klasifikasi Kesalahan terlebih dahulu!")
                    return
                self.engine.log_error_classification(self.view.combo_error_class.currentText())
            self.engine.next_question()
            self.load_question()

    def trigger_timeout(self):
        self.stopwatch_timer.stop()

        if self.current_mode == "Time Attack":
            self.is_showing_explanation = True
            self.last_answer_correct = False
            q = self.engine.get_current_question()
            correct_ans = str(q.get('answer', '')).strip().upper()
            explanation = q.get('explanation', 'Tidak ada pembahasan khusus.')

            for r in [self.view.radio_A, self.view.radio_B, self.view.radio_C, self.view.radio_D, self.view.radio_E]:
                r.setEnabled(False)

            self.view.frame_evaluation.show()
            self.view.eval_explanation_text.setText(f"<b>Kunci Jawaban: {correct_ans}</b><br><br><b>Pembahasan:</b><br>{explanation}")
            self.view.eval_result_label.setText("WAKTU HABIS!")
            self.view.eval_result_label.setStyleSheet("color: #e67e22; font-weight: bold;")
            self.view.label_error_class.hide(); self.view.combo_error_class.hide()
            self.view.btn_exam_next.hide(); self.view.btn_exam_finish.hide()

            current_w = self.view.page_exam.width()
            self.timeout_frame.move(current_w - self.timeout_frame.width() - 30, 70)
            self.timeout_frame.show(); self.timeout_frame.raise_()

            if self.engine.current_idx == len(self.engine.questions) - 1:
                self.timeout_btn.setText("Selesai & Lihat Hasil")
            else:
                self.timeout_btn.setText("Lanjut Soal Berikutnya")

        elif self.current_mode == "Challenge":
            # LOGIKA TIMEOUT CHALLENGE (Memaksa masuk ke Mode Pembahasan)
            self.block_radios(True)
            self.view.frame_question_grid.hide()
            self.view.btn_exam_prev.hide()
            self.view.btn_exam_next.hide()
            self.view.btn_exam_flag.hide()
            if hasattr(self, 'submit_grid_btn'): self.submit_grid_btn.hide()

            self.timeout_label.setText("WAKTU UJIAN HABIS!")
            self.timeout_btn.setText("Masuk Pembahasan & Hasil")

            current_w = self.view.page_exam.width()
            self.timeout_frame.move(current_w - self.timeout_frame.width() - 30, 70)
            self.timeout_frame.show(); self.timeout_frame.raise_()

    def handle_timeout_next(self):
        self.timeout_frame.hide()
        if self.current_mode == "Time Attack":
            self.engine.log_error_classification("Waktu Habis")
            self.engine.next_question()
            if self.engine.is_finished(): self.finish_exam()
            else: self.load_question()
        elif self.current_mode == "Challenge":
            self.initiate_review_submit()

    def get_selected_answer(self):
        if self.view.radio_A.isChecked(): return "A"
        if self.view.radio_B.isChecked(): return "B"
        if self.view.radio_C.isChecked(): return "C"
        if self.view.radio_D.isChecked(): return "D"
        if self.view.radio_E.isChecked(): return "E"
        return None

    def finish_exam(self):
        if self.current_mode in ["Iterative", "Time Attack"]:
            if self.view.frame_evaluation.isVisible() and not self.last_answer_correct and self.view.combo_error_class.isVisible():
                if self.view.combo_error_class.currentIndex() == 0:
                    self.view.show_popup("Pilih Klasifikasi Kesalahan untuk soal terakhir!")
                    return
                self.engine.log_error_classification(self.view.combo_error_class.currentText())

        if self.current_mode in ["Review", "Challenge"]:
            if not self.is_review_classification_phase:
                self.initiate_review_submit()
                return
            else:
                if self.engine.current_idx in self.engine.wrong_indices:
                    if self.view.combo_error_class.isEnabled() and self.view.combo_error_class.currentIndex() == 0:
                        self.view.show_popup("Pilih Klasifikasi Kesalahan terlebih dahulu!")
                        return
                    self.engine.log_error_classification(self.engine.current_idx, self.view.combo_error_class.currentText())

                if len(self.engine.performance_log) < len(self.engine.wrong_indices):
                    sisa = len(self.engine.wrong_indices) - len(self.engine.performance_log)
                    self.view.show_popup(f"Masih ada {sisa} soal salah/kosong yang belum diklasifikasi!\n(Cek grid kotak yang berwarna merah)")
                    return

        self.stopwatch_timer.stop()
        final_time_str = self.get_time_string()

        stats = self.engine.get_statistics(final_time_str)

        self.view.report_score_label.setText(f"Skor Akhir: {stats['score_text']}")
        self.view.report_time_label.setText(f"Waktu Dihabiskan: {final_time_str}")
        self.view.report_topic_details.setText(stats['topic_summary'])
        self.view.report_error_details.setText(stats['error_summary'])

        self.dashboard.add_new_stat(stats, self.current_mode)

        self.view.report_frame.show()
        self.view.report_frame.raise_()

    def close_report_and_exit(self):
        self.view.report_frame.hide()
        self.nav.switch_page(2)