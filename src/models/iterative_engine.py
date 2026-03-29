import time

class IterativeEngine:
    def __init__(self, config):
        self.questions = config.get('questions', [])
        self.current_idx = 0
        self.score = 0
        self.performance_log = []
        self.start_time = time.time()
        self.topic_name = config.get('topics', 'Multiple Topics')

    def get_current_question(self):
        if self.current_idx < len(self.questions):
            return self.questions[self.current_idx]
        return None

    def check_answer(self, user_ans):
        q = self.get_current_question()
        if not q: return False, "", ""
        correct = str(q.get('answer', '')).strip().upper()

        # Validasi jika Waktu Habis (user_ans kosong pada Time Attack)
        if not user_ans:
            return False, correct, q.get('explanation', 'Tidak ada pembahasan khusus untuk soal ini.')

        is_ok = (user_ans.upper() == correct)
        if is_ok: self.score += 1
        return is_ok, correct, q.get('explanation', 'Tidak ada pembahasan khusus untuk soal ini.')

    def log_error_classification(self, error_type):
        q = self.get_current_question()
        if q:
            self.performance_log.append({
                'topic': q.get('topic', 'Unknown').strip(),
                'subtopic': q.get('subtopic', '-').strip(),
                'error_type': error_type
            })

    def get_statistics(self, time_spent_str):
        """
        REVISI: Menambahkan parameter time_spent_str agar sinkron dengan Controller
        serta menyesuaikan dengan mekanisme yang ada di ReviewEngine.
        """
        total_q = len(self.questions)

        topic_breakdown = {}
        for entry in self.performance_log:
            t = entry['topic']
            st = entry['subtopic']
            err = entry['error_type']

            if t not in topic_breakdown: topic_breakdown[t] = {}
            if st not in topic_breakdown[t]: topic_breakdown[t][st] = {}
            if err not in topic_breakdown[t][st]: topic_breakdown[t][st][err] = 0

            topic_breakdown[t][st][err] += 1

        topic_lines = []
        plain_topic_lines = []

        for t, subtopics in topic_breakdown.items():
            topic_lines.append(f"<b style='color:#2c3e50;'>Topik: {t}</b>")
            plain_topic_lines.append(f"Topik: {t}")
            for st, errors in subtopics.items():
                topic_lines.append(f"&nbsp;&nbsp;&nbsp;<i>Subtopik: {st}</i>")
                plain_topic_lines.append(f"   Subtopik: {st}")
                for err, count in errors.items():
                    topic_lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;• Kesalahan {err} : {count} soal")
                    plain_topic_lines.append(f"      - {err} : {count} soal")
            topic_lines.append("")
            plain_topic_lines.append("")

        topic_summary = "<br>".join(topic_lines)
        plain_topic_str = "\n".join(plain_topic_lines)

        if not topic_summary.strip():
            topic_summary = "<i>Tidak ada kesalahan (Sempurna!)</i>"
            plain_topic_str = "Tidak ada kesalahan (Sempurna!)"

        # Tambahkan klasifikasi Waktu Habis ke Hitungan Error
        error_counts = {"Knowledge Gap": 0, "Guessing": 0, "Misread": 0, "Accident Click": 0, "Waktu Habis": 0}
        for entry in self.performance_log:
            etype = entry['error_type']
            if etype in error_counts: error_counts[etype] += 1

        total_errors = sum(error_counts.values())
        error_lines = []
        plain_error_lines = []

        if total_errors > 0:
            max_err_count = max(error_counts.values())
            for err, count in error_counts.items():
                if count > 0 or err != "Waktu Habis": # Sembunyikan "Waktu Habis" jika 0 agar bersih
                    pct = (count / total_errors) * 100
                    line = f"• {err}: <b>{count}</b> ({pct:.1f}%)"
                    plain_line = f"- {err}: {count} ({pct:.1f}%)"

                    if count == max_err_count and max_err_count > 0:
                        line = f"<span style='color: #c0392b; font-weight: bold;'>{line} &lt;-- Terbanyak!</span>"
                        plain_line += " <-- Terbanyak!"

                    error_lines.append(line)
                    plain_error_lines.append(plain_line)
        else:
            error_lines.append("<i>Tidak ada proporsi kesalahan.</i>")
            plain_error_lines.append("Tidak ada proporsi kesalahan.")

        error_summary = "<br>".join(error_lines)
        plain_error_str = "\n".join(plain_error_lines)

        score_pct = (self.score / total_q * 100) if total_q > 0 else 0
        score_text = f"{self.score} / {total_q} ({score_pct:.1f}%)"

        full_report_plain = (
            f"Skor Akhir: {score_text}\n"
            f"Waktu Dihabiskan: {time_spent_str}\n\n"
            f"Rincian Topik Salah:\n{plain_topic_str}\n"
            f"Proporsi Kesalahan:\n{plain_error_str}"
        )

        return {
            'score_text': score_text,
            'time_spent': time_spent_str, # <-- Memakai waktu akurat dari Controller
            'topic_summary': topic_summary,
            'error_summary': error_summary,
            'raw_errors': error_counts,
            'main_topic': self.topic_name,
            'full_report_plain': full_report_plain
        }

    def next_question(self):
        self.current_idx += 1

    def is_finished(self):
        return self.current_idx >= len(self.questions)