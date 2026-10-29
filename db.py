import sqlite3

DB_PATH = "qa.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # better read/write concurrency
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS qa (
                id INTEGER PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

def add_qa(question, answer, category=None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO qa (question, answer, category) VALUES (?, ?, ?)",
            (question, answer, category),
        )

def search_qa(text, limit=5):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT question, answer FROM qa "
            "WHERE question LIKE ? OR answer LIKE ? LIMIT ?",
            (f"%{text}%", f"%{text}%", limit),
        ).fetchall()
    return [dict(r) for r in rows]