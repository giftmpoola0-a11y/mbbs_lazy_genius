import sqlite3
from datetime import datetime

DB_NAME = "lazy_genius.db"


def get_conn():
    """Create (or open) the SQLite database file and return a connection."""
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_db():
    """Create tables if they don't exist yet."""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration_minutes REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def save_session(activity: str, start_time: datetime, end_time: datetime):
    """Save one tracked session to the database."""
    duration_minutes = (end_time - start_time).total_seconds() / 60.0

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO sessions (activity, start_time, end_time, duration_minutes)
        VALUES (?, ?, ?, ?)
    """, (
        activity,
        start_time.isoformat(timespec="seconds"),
        end_time.isoformat(timespec="seconds"),
        duration_minutes
    ))

    conn.commit()
    conn.close()


def get_today_sessions():
    """Return all sessions for today."""
    today = datetime.now().date().isoformat()  # YYYY-MM-DD

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT activity, start_time, end_time, duration_minutes
        FROM sessions
        WHERE start_time LIKE ?
        ORDER BY start_time DESC
    """, (f"{today}%",))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_sessions_between(start_date, end_date):
    """
    Return sessions between start_date and end_date (inclusive).
    start_date / end_date are date objects or strings 'YYYY-MM-DD'
    """
    # Convert to strings
    if hasattr(start_date, "isoformat"):
        start_date = start_date.isoformat()
    if hasattr(end_date, "isoformat"):
        end_date = end_date.isoformat()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT activity, start_time, end_time, duration_minutes
        FROM sessions
        WHERE substr(start_time, 1, 10) BETWEEN ? AND ?
        ORDER BY start_time DESC
    """, (start_date, end_date))

    rows = cur.fetchall()
    conn.close()
    return rows

def init_questions_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            q_type TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TEXT NOT NULL,
            correct_count INTEGER DEFAULT 0,
            wrong_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def add_question(topic: str, q_type: str, question: str, answer: str):
    from datetime import datetime
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO questions (topic, q_type, question, answer, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (topic, q_type, question, answer, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()


def get_questions(topic: str = None):
    conn = get_conn()
    cur = conn.cursor()

    if topic and topic.strip():
        cur.execute("""
            SELECT id, topic, q_type, question, answer, created_at, correct_count, wrong_count
            FROM questions
            WHERE topic = ?
            ORDER BY created_at DESC
        """, (topic.strip(),))
    else:
        cur.execute("""
            SELECT id, topic, q_type, question, answer, created_at, correct_count, wrong_count
            FROM questions
            ORDER BY created_at DESC
        """)

    rows = cur.fetchall()
    conn.close()
    return rows


def mark_answer(q_id: int, is_correct: bool):
    conn = get_conn()
    cur = conn.cursor()
    if is_correct:
        cur.execute("UPDATE questions SET correct_count = correct_count + 1 WHERE id = ?", (q_id,))
    else:
        cur.execute("UPDATE questions SET wrong_count = wrong_count + 1 WHERE id = ?", (q_id,))
    conn.commit()
    conn.close()

def delete_all_questions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM questions")
    conn.commit()
    conn.close()

def init_home_tables():
    conn = get_conn()
    cur = conn.cursor()

    # Settings (goal minutes + exam date)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Daily todo checklist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            todo_date TEXT NOT NULL,        -- YYYY-MM-DD
            task TEXT NOT NULL,
            done INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def set_setting(key: str, value: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings(key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def get_setting(key: str, default: str = "") -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default


def add_todo(todo_date: str, task: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO todos(todo_date, task, done) VALUES (?, ?, 0)", (todo_date, task))
    conn.commit()
    conn.close()


def get_todos(todo_date: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, task, done
        FROM todos
        WHERE todo_date = ?
        ORDER BY id DESC
    """, (todo_date,))
    rows = cur.fetchall()
    conn.close()
    return rows


def set_todo_done(todo_id: int, done: bool):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE todos SET done = ? WHERE id = ?", (1 if done else 0, todo_id))
    conn.commit()
    conn.close()


def delete_todo(todo_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()


def get_active_days():
    """Returns list of dates (YYYY-MM-DD) that have at least 1 session."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT substr(start_time, 1, 10) as d
        FROM sessions
        ORDER BY d DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_minutes_for_date(d: str) -> float:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(duration_minutes), 0)
        FROM sessions
        WHERE substr(start_time, 1, 10) = ?
    """, (d,))
    val = cur.fetchone()[0]
    conn.close()
    return float(val or 0)




def init_profile_table():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            full_name TEXT,
            nickname TEXT,
            school TEXT,
            year TEXT,
            university TEXT,
            email TEXT,
            phone TEXT,
            bio TEXT,
            photo_path TEXT,
            updated_at TEXT
        )
    """)

    # Ensure one row exists
    cur.execute("INSERT OR IGNORE INTO profile (id) VALUES (1)")

    conn.commit()
    conn.close()


def get_profile():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT full_name, nickname, school, year, university, email, phone, bio, photo_path, updated_at
        FROM profile
        WHERE id = 1
    """)
    row = cur.fetchone()
    conn.close()

    keys = ["full_name", "nickname", "school", "year", "university", "email", "phone",
            "bio", "photo_path", "updated_at"]

    if not row:
        return {k: "" for k in keys}

    return dict(zip(keys, row))


def update_profile(full_name="", nickname="", school="", year="", university="",
                   email="", phone="", bio="", photo_path=""):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE profile
        SET full_name = ?, nickname = ?, school = ?, year = ?, university = ?,
            email = ?, phone = ?, bio = ?, photo_path = ?, updated_at = ?
        WHERE id = 1
    """, (
        full_name, nickname, school, year, university,
        email, phone, bio, photo_path, datetime.now().isoformat(timespec="seconds")
    ))

    conn.commit()
    conn.close()
