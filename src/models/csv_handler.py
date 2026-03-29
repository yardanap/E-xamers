import csv
import os
import shutil
from utils.path_helper import resource_path

class AuthModel:
    @staticmethod
    def verify_login(username, password):
        file_path = resource_path("assets/db_credential/users.csv")
        try:
            with open(file_path, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file, delimiter=',')
                for row in reader:
                    db_user = row.get('username', '').strip()
                    db_pass = row.get('password', '').strip()
                    if db_user == username and db_pass == password:
                        return True
        except Exception as e:
            print("Error baca CSV:", e)
        return False

class ModuleModel:
    @staticmethod
    def get_all_modules_metadata():
        db_path = resource_path("assets/db_modules")
        os.makedirs(db_path, exist_ok=True)
        modules_data = []

        for filename in os.listdir(db_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(db_path, filename)
                try:
                    with open(file_path, mode='r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f, delimiter=',')
                        topics, subtopics, difficulties = set(), set(), set()
                        count = 0
                        for row in reader:
                            count += 1
                            if row.get('topic'): topics.add(row['topic'].strip())
                            if row.get('subtopic'): subtopics.add(row['subtopic'].strip())
                            if row.get('difficulty_levels'): difficulties.add(row['difficulty_levels'].strip())

                        modules_data.append({
                            'topic': ", ".join(topics) if topics else "Unknown",
                            'subtopic': ", ".join(subtopics) if subtopics else "-",
                            'count': str(count),
                            'difficulty': ", ".join(difficulties) if difficulties else "Unknown"
                        })
                except Exception as e:
                    pass
        return modules_data

    @staticmethod
    def get_raw_questions():
        """Membaca SEMUA soal dari semua module untuk filter di Dashboard"""
        db_path = resource_path("assets/db_modules")
        os.makedirs(db_path, exist_ok=True)
        all_questions = []

        for filename in os.listdir(db_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(db_path, filename)
                try:
                    with open(file_path, mode='r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f, delimiter=',')
                        for row in reader:
                            all_questions.append(row)
                except Exception:
                    pass
        return all_questions

    @staticmethod
    def import_module_csv(source_path):
        db_path = resource_path("assets/db_modules")
        os.makedirs(db_path, exist_ok=True)
        filename = os.path.basename(source_path)
        dest_path = os.path.join(db_path, filename)
        try:
            shutil.copy(source_path, dest_path)
            return True
        except Exception:
            return False