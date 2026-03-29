import time

class ReviewEngine:
    def __init__(self, config):
        self.config = config
        self.questions = config.get('questions', [])
        self.current_idx = 0
        self.score = 0
        self.start_time = time.time()
        self.topic_name = config.get('topics', 'Multiple Topics')

        self.answers = {}
        self.flags = set()
        self.wrong_indices = []
        self.performance_log = {}

    def get_current_question(self):
        if 0 <= self.current_idx < len(self.questions):
            return self.questions[self.current_idx]
        return None

    def set_answer(self, ans):
        self.answers[self.current_idx] = ans

    def toggle_flag(self):
        if self.current_idx in self.flags:
            self.flags.remove(self.current_idx)
        else:
            self.flags.add(self.current_idx)

    def calculate_score(self):
        self.score = 0
        self.wrong_indices = []
        for i, q in enumerate(self.questions):
            correct = str(q.get('answer', '')).strip().upper()
            user_ans = self.answers.get(i, "").upper()

            if user_ans == correct and user_ans != "":
                self.score += 1
            else:
                self.wrong_indices.append(i)

    def log_error_classification(self, idx, error_type):
        q = self.questions[idx]
        self.performance_log[idx] = {
            'topic': q.get('topic', 'Unknown').strip(),
            'subtopic': q.get('subtopic', '-').strip(),
            'error_type': error_type
        }

    def get_statistics(self, time_spent_str):
        total_q = len(self.questions)
        topic_breakdown = {}

        for entry in self.performance_log.values():
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

        # REVISI: Tambahan 'Tidak Terjawab' untuk Challenge Mode
        error_counts = {"Knowledge Gap": 0, "Guessing": 0, "Misread": 0, "Accident Click": 0, "Waktu Habis": 0, "Tidak Terjawab": 0}
        for entry in self.performance_log.values():
            etype = entry['error_type']
            if etype in error_counts: error_counts[etype] += 1
            else: error_counts[etype] = 1

        total_errors = sum(error_counts.values())
        error_lines = []
        plain_error_lines = []

        if total_errors > 0:
            max_err_count = max(error_counts.values())
            for err, count in error_counts.items():
                if count > 0 or err not in ["Waktu Habis", "Tidak Terjawab"]:
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
            'score_text': score_text, 'time_spent': time_spent_str,
            'topic_summary': topic_summary, 'error_summary': error_summary,
            'raw_errors': error_counts, 'main_topic': self.topic_name,
            'full_report_plain': full_report_plain
        }