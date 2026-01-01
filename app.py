
import textwrap  # add this near the top with imports
import streamlit as st
import pandas as pd
import os
import base64
from pathlib import Path
from datetime import date

# -------------------------
# DB imports (your db.py)
# -------------------------
from db import init_db

PROFILE_OK = True
QUESTIONS_OK = True
TRACKER_OK = True

try:
    from db import get_profile
except Exception:
    PROFILE_OK = False

try:
    from db import get_questions
except Exception:
    QUESTIONS_OK = False

try:
    from db import get_today_sessions
except Exception:
    TRACKER_OK = False


# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="Marcia The Lazy Genius",
    page_icon="🧸",
    layout="wide",
)

# -------------------------
# Init DB
# -------------------------
init_db()

# -------------------------
# Helpers
# -------------------------
def safe_strip(x):
    return x.strip() if isinstance(x, str) else ""

def photo_path_to_data_uri(photo_path: str) -> str:
    """Turn a local image path into a browser-loadable data URI."""
    if not photo_path:
        return ""
    p = Path(photo_path)
    if not p.exists() or not p.is_file():
        return ""

    ext = p.suffix.lower().replace(".", "")
    if ext not in ["png", "jpg", "jpeg", "webp"]:
        ext = "png"

    data = p.read_bytes()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/{ext};base64,{b64}"

def minutes_to_pretty(m):
    try:
        m = float(m)
    except Exception:
        return "0 min"
    if m < 60:
        return f"{m:.1f} min"
    return f"{m/60:.1f} hrs"

# =========================
# DAILY TASKS (Checklist)
# =========================
import sqlite3
from datetime import date, datetime

# If you already have DB_PATH or a get_connection() function, reuse it.
# Below tries to be compatible with most db.py styles.

def _get_conn():
    # If you already defined DB_PATH earlier, this will use it.
    # Otherwise, fallback to "mbbs.db" (change if your DB name is different).
    db_path = globals().get("DB_PATH", "mbbs.db")
    return sqlite3.connect(db_path, check_same_thread=False)


def init_daily_tasks_table():
    with _get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_date TEXT NOT NULL,
            task_text TEXT NOT NULL,
            is_done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_tasks_date ON daily_tasks(task_date);")
        conn.commit()


def add_daily_task(task_text: str, task_date: str = None):
    task_text = (task_text or "").strip()
    if not task_text:
        return

    if task_date is None:
        task_date = date.today().isoformat()

    with _get_conn() as conn:
        conn.execute("""
        INSERT INTO daily_tasks (task_date, task_text, is_done, created_at)
        VALUES (?, ?, 0, ?)
        """, (task_date, task_text, datetime.now().isoformat(timespec="seconds")))
        conn.commit()


def get_daily_tasks(task_date: str = None):
    if task_date is None:
        task_date = date.today().isoformat()

    with _get_conn() as conn:
        rows = conn.execute("""
        SELECT id, task_text, is_done
        FROM daily_tasks
        WHERE task_date = ?
        ORDER BY id DESC
        """, (task_date,)).fetchall()

    # returns list of tuples: (id, text, is_done)
    return rows


def set_task_done(task_id: int, is_done: bool):
    with _get_conn() as conn:
        conn.execute("""
        UPDATE daily_tasks
        SET is_done = ?
        WHERE id = ?
        """, (1 if is_done else 0, int(task_id)))
        conn.commit()


def clear_completed_tasks(task_date: str = None):
    if task_date is None:
        task_date = date.today().isoformat()

    with _get_conn() as conn:
        conn.execute("""
        DELETE FROM daily_tasks
        WHERE task_date = ? AND is_done = 1
        """, (task_date,))
        conn.commit()



# -------------------------
# Cute Pink Theme CSS
# -------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600;700&family=Pacifico&display=swap');

html, body, [class*="css"]  {
  font-family: "Quicksand", sans-serif !important;
}

.main {
  background: radial-gradient(circle at 15% 10%, rgba(255,192,203,0.35) 0%, rgba(255,255,255,0.95) 40%),
              radial-gradient(circle at 90% 20%, rgba(255,182,193,0.25) 0%, rgba(255,255,255,0.95) 50%);
}

.pink-card {
  background: rgba(255,255,255,0.7);
  border: 1px solid rgba(255,160,200,0.35);
  box-shadow: 0 10px 30px rgba(255,105,180,0.10);
  border-radius: 22px;
  padding: 18px 18px;
}

.hero {
  background: linear-gradient(135deg, rgba(255,192,203,0.35), rgba(255,255,255,0.85));
  border: 1px solid rgba(255,160,200,0.35);
  box-shadow: 0 12px 34px rgba(255,105,180,0.12);
  border-radius: 26px;
  padding: 28px 28px;
  position: relative;
  overflow: hidden;
}

.dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: rgba(255,140,200,0.45);
  position: absolute;
  animation: floaty 6s infinite ease-in-out;
}

@keyframes floaty {
  0% { transform: translateY(0px); opacity: .6;}
  50% { transform: translateY(-16px); opacity: .9;}
  100% { transform: translateY(0px); opacity: .6;}
}

.hero-title {
  font-family: "Pacifico", cursive !important;
  font-size: 54px;
  line-height: 1.0;
  margin: 0;
  color: rgba(50,40,45,0.9);
}

.badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(255,180,210,0.55);
  border: 1px solid rgba(255,160,200,0.45);
  font-weight: 700;
  font-size: 12px;
}

.subtitle {
  font-size: 16px;
  color: rgba(50,40,45,0.75);
}

.quick-btn {
  display: inline-block;
  padding: 10px 16px;
  border-radius: 999px;
  border: 1px solid rgba(255,160,200,0.40);
  background: rgba(255,255,255,0.75);
  font-weight: 700;
  margin-right: 10px;
  text-decoration: none;
  color: rgba(40,30,35,0.85);
}

.avatar {
  width: 74px;
  height: 74px;
  border-radius: 50%;
  border: 4px solid rgba(255,150,200,0.75);
  box-shadow: 0 10px 25px rgba(255,105,180,0.18);
  background: rgba(255,255,255,0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34px;
  overflow: hidden;
  flex: 0 0 auto;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Sidebar Settings
# -------------------------
st.sidebar.markdown("## 💗 Home Settings")
daily_goal = st.sidebar.number_input("Daily study goal (minutes)", min_value=10, max_value=1440, value=60, step=10)
exam_date = st.sidebar.date_input("Exam date (optional)", value=date.today())

# -------------------------
# Load Profile
# -------------------------
display_name = "Marcia"
photo_path = ""
avatar_src = ""

if PROFILE_OK:
    try:
        prof = get_profile() or {}
        nickname = safe_strip(prof.get("nickname"))
        full_name = safe_strip(prof.get("full_name"))
        display_name = nickname if nickname else (full_name if full_name else "Marcia")

        photo_path = safe_strip(prof.get("photo_path"))
        avatar_src = photo_path_to_data_uri(photo_path)
    except Exception:
        pass

# -------------------------
# Load Today's Sessions
# -------------------------
today_total = 0.0
top_activity = "None"
top_minutes = 0.0
today_rows = []

if TRACKER_OK:
    try:
        today_rows = get_today_sessions() or []
        if today_rows:
            df_today = pd.DataFrame(today_rows, columns=["Activity", "Start", "End", "Minutes"])
            today_total = float(df_today["Minutes"].sum())
            by_act = df_today.groupby("Activity")["Minutes"].sum().sort_values(ascending=False)
            if len(by_act) > 0:
                top_activity = str(by_act.index[0])
                top_minutes = float(by_act.iloc[0])
    except Exception:
        pass

# -------------------------
# Question bank total
# -------------------------
q_total = 0
if QUESTIONS_OK:
    try:
        q_total = len(get_questions(None) or [])
    except Exception:
        pass

# -------------------------
# Progress %
# -------------------------
progress = 0
if daily_goal > 0:
    progress = min(100, int((today_total / float(daily_goal)) * 100))

# -------------------------
# HERO HEADER (NO components.html)
# -------------------------
avatar_html = ""
if avatar_src:
    avatar_html = (
        f'<div class="avatar">'
        f'  <img class="avatar-img" src="{avatar_src}" />'
        f'</div>'
    )
else:
    avatar_html = '<div class="avatar">🧸</div>'

hero_html = (
    '<div class="hero">'
    '  <div class="dot" style="left:15%; top:18%;"></div>'
    '  <div class="dot" style="left:55%; top:12%; animation-delay:1.2s;"></div>'
    '  <div class="dot" style="left:88%; top:30%; animation-delay:2.1s;"></div>'
    '  <div style="display:flex; gap:18px; align-items:center;">'
    f'    {avatar_html}'
    '    <div style="flex:1;">'
    '      <div class="badge">MBBS Final Year Helper</div>'
    f'      <h1 class="hero-title">{display_name} The Lazy Genius 💗</h1>'
    '      <div class="subtitle">Track your time, generate questions from notes, and study smarter ✨</div>'
    '      <div style="margin-top:14px;">'
    '        <span class="quick-btn">⏱ Tracker</span>'
    '        <span class="quick-btn">🧠 Questions</span>'
    '        <span class="quick-btn">📊 Analytics</span>'
    '        <span class="quick-btn">💗 Profile</span>'
    '      </div>'
    '      <div style="margin-top:10px; color: rgba(50,40,45,0.70); font-weight:600;">'
    '        Tip: Paste notes into Questions → generate MCQs + short answers → quiz mode 🎯'
    '      </div>'
    '    </div>'
    '  </div>'
    '</div>'
)

st.markdown(hero_html, unsafe_allow_html=True)
st.write("")
# -------------------------
# Stat Cards
# -------------------------
c1, c2, c3 = st.columns([1.4, 1, 1])

with c1:
    st.markdown(f"""
    <div class="pink-card">
      <div class="badge">Today Goal</div>
      <div style="display:flex; gap:18px; align-items:center; margin-top:12px;">
        <div style="
            width:84px;height:84px;border-radius:50%;
            border:10px solid rgba(255,170,210,0.25);
            display:flex;align-items:center;justify-content:center;
            font-weight:800;
            color: rgba(60,40,50,0.85);
        ">
          {progress}%
        </div>
        <div>
          <div style="font-weight:800; font-size:20px; color: rgba(60,40,50,0.9);">
            {minutes_to_pretty(today_total)} / {daily_goal} min
          </div>
          <div style="color: rgba(60,40,50,0.7); font-weight:700;">
            Keep going bestie 💗
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="pink-card">
      <div class="badge">Study Streak</div>
      <div style="margin-top:10px; font-weight:800; font-size:22px;">1 💖</div>
      <div style="color: rgba(60,40,50,0.7); font-weight:700;">days in a row</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    days_left = (exam_date - date.today()).days if exam_date else 0
    if days_left < 0:
        days_left = 0
    st.markdown(f"""
    <div class="pink-card">
      <div class="badge">Finals Countdown</div>
      <div style="margin-top:10px; font-weight:900; font-size:26px;">
        {days_left} days left ⏳
      </div>
      <div style="color: rgba(60,40,50,0.7); font-weight:700;">future doctor loading 🩺</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

c4, c5, c6 = st.columns(3)

with c4:
    st.markdown(f"""
    <div class="pink-card">
      <div class="badge">Question Bank</div>
      <div style="margin-top:10px; font-weight:900; font-size:28px;">{q_total}</div>
      <div style="color: rgba(60,40,50,0.7); font-weight:700;">total saved questions</div>
    </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
    <div class="pink-card">
      <div class="badge">Top Activity</div>
      <div style="margin-top:10px; font-weight:900; font-size:26px;">
        {top_activity} ({minutes_to_pretty(top_minutes)})
      </div>
      <div style="color: rgba(60,40,50,0.7); font-weight:700;">most time today</div>
    </div>
    """, unsafe_allow_html=True)

with c6:
    st.markdown("""
    <div class="pink-card">
      <div class="badge">Motivation</div>
      <div style="margin-top:10px; font-weight:900; font-size:18px;">
        “Study smart, rest cute 🥺💖”
      </div>
      <div style="color: rgba(60,40,50,0.7); font-weight:700;">you got this bestie 💗</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.divider()

# -------------------------
# Today's Log Preview
# -------------------------
st.markdown("## 📌 Today’s Log (preview)")

if TRACKER_OK and today_rows:
    df_today = pd.DataFrame(today_rows, columns=["Activity", "Start", "End", "Minutes"])
    st.dataframe(df_today, use_container_width=True, hide_index=True)
else:
    st.info("No sessions logged today yet. Go to **Tracker** and start tracking 💖")
