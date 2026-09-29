import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "retinaguard.db")

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screening_id TEXT UNIQUE NOT NULL,
                patient_id TEXT NOT NULL,
                patient_name TEXT,
                age INTEGER,
                sex TEXT,
                hba1c REAL,
                diabetes_duration REAL,
                hypertension INTEGER,
                image_path TEXT,
                quality_status TEXT NOT NULL,
                quality_score REAL,
                quality_metrics_json TEXT,
                failure_reasons_json TEXT,
                icdr_grade TEXT,
                predicted_class_name TEXT,
                confidence_score REAL,
                uncertainty_index REAL,
                class_probabilities_json TEXT,
                triage_state TEXT NOT NULL,
                referral_priority TEXT,
                urgency_level TEXT,
                clinical_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_screening(self, data: dict) -> str:
        conn = self.get_connection()
        cursor = conn.cursor()

        screening_id = data.get("screening_id") or f"RG-{datetime.now().strftime('%Y%m%d')}-{os.urandom(2).hex().upper()}"
        
        cursor.execute("""
            INSERT INTO screenings (
                screening_id, patient_id, patient_name, age, sex, hba1c,
                diabetes_duration, hypertension, image_path, quality_status,
                quality_score, quality_metrics_json, failure_reasons_json,
                icdr_grade, predicted_class_name, confidence_score,
                uncertainty_index, class_probabilities_json, triage_state,
                referral_priority, urgency_level, clinical_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            screening_id,
            data.get("patient_id", "ANONYMOUS"),
            data.get("patient_name", "N/A"),
            data.get("age"),
            data.get("sex"),
            data.get("hba1c"),
            data.get("diabetes_duration"),
            1 if data.get("hypertension") else 0,
            data.get("image_path", ""),
            data.get("quality_status", "UNKNOWN"),
            data.get("quality_score", 0.0),
            json.dumps(data.get("quality_metrics", {})),
            json.dumps(data.get("failure_reasons", [])),
            data.get("icdr_grade", "N/A"),
            data.get("predicted_class_name", "N/A"),
            data.get("confidence_score", 0.0),
            data.get("uncertainty_index", 0.0),
            json.dumps(data.get("class_probabilities", [])),
            data.get("triage_state", "UNKNOWN"),
            data.get("referral_priority", "UNKNOWN"),
            data.get("urgency_level", "N/A"),
            data.get("clinical_summary", "")
        ))

        conn.commit()
        conn.close()
        return screening_id

    def get_all_screenings(self, search: str = None, result_filter: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM screenings WHERE 1=1"
        params = []

        if search:
            query += " AND (patient_id LIKE ? OR patient_name LIKE ? OR screening_id LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])

        if result_filter:
            if result_filter == "RECHECK":
                query += " AND triage_state = 'RECHECK_IMAGE'"
            elif result_filter == "GRADE0":
                query += " AND icdr_grade = 'Grade 0'"
            elif result_filter == "GRADE1":
                query += " AND icdr_grade = 'Grade 1'"
            elif result_filter == "GRADE2":
                query += " AND icdr_grade = 'Grade 2'"
            elif result_filter == "GRADE3":
                query += " AND icdr_grade = 'Grade 3'"
            elif result_filter == "GRADE4":
                query += " AND icdr_grade = 'Grade 4'"
            elif result_filter == "REFERRAL":
                query += " AND icdr_grade IN ('Grade 2', 'Grade 3', 'Grade 4')"

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        results = []
        for r in rows:
            row_dict = dict(r)
            row_dict["quality_metrics"] = json.loads(row_dict["quality_metrics_json"]) if row_dict["quality_metrics_json"] else {}
            row_dict["failure_reasons"] = json.loads(row_dict["failure_reasons_json"]) if row_dict["failure_reasons_json"] else []
            row_dict["class_probabilities"] = json.loads(row_dict["class_probabilities_json"]) if row_dict["class_probabilities_json"] else []
            results.append(row_dict)

        return results

    def get_screening_by_id(self, screening_id: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM screenings WHERE screening_id = ?", (screening_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        row_dict = dict(row)
        row_dict["quality_metrics"] = json.loads(row_dict["quality_metrics_json"]) if row_dict["quality_metrics_json"] else {}
        row_dict["failure_reasons"] = json.loads(row_dict["failure_reasons_json"]) if row_dict["failure_reasons_json"] else []
        row_dict["class_probabilities"] = json.loads(row_dict["class_probabilities_json"]) if row_dict["class_probabilities_json"] else []
        return row_dict

    def get_dashboard_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM screenings")
        total_screenings = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM screenings WHERE icdr_grade = 'Grade 0'")
        grade0_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM screenings WHERE icdr_grade = 'Grade 1'")
        grade1_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM screenings WHERE icdr_grade = 'Grade 2'")
        grade2_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM screenings WHERE icdr_grade = 'Grade 3'")
        grade3_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM screenings WHERE icdr_grade = 'Grade 4'")
        grade4_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM screenings WHERE triage_state = 'RECHECK_IMAGE'")
        recheck_cases = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM screenings WHERE triage_state = 'SPECIALIST_REVIEW_RECOMMENDED'")
        uncertain_cases = cursor.fetchone()[0]

        conn.close()

        return {
            "total_screenings": total_screenings,
            "grade0_count": grade0_count,
            "grade1_count": grade1_count,
            "grade2_count": grade2_count,
            "grade3_count": grade3_count,
            "grade4_count": grade4_count,
            "recheck_cases": recheck_cases,
            "uncertain_cases": uncertain_cases
        }
