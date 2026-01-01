import streamlit as st
from datetime import datetime
import pandas as pd

from db import init_db, save_session, get_today_sessions
from ui import apply_girly_theme
apply_girly_theme()

from streamlit_autorefresh import st_autorefresh

# -------------------------
# Modern CSS (Tracker)
# -------------------------
st.markdown("""
<style>
/* Center content area a bit */
.block-container { padding-top: 1.2rem; max-width: 1100px; }

/* Pills */
.pill-row { display:flex; gap:12px; flex-wrap:wrap; margin: 10px 0 6px; }
.pill {
  display:inline-flex; align-items:center; gap:10px;
  padding: 12px 16px;
  border-radius: 999px;
  background: rgba(255,255,255,0.70);
  border: 1px solid rgba(255,160,200,0.35);
  box-shadow: 0 10px 26px rgba(255,105,180,0.10);
  font-weight: 850;
  color: rgba(60,40,50,0.90);
}

/* Hero card */
.tracker-hero {
  background: linear-gradient(135deg, rgba(255,192,203,0.40), rgba(255,255,255,0.86));
  border: 1px solid rgba(255,160,200,0.38);
  box-shadow: 0 16px 46px rgba(255,105,180,0.14);
  border-radius: 28px;
  padding: 22px 22px;
  position: relative;
  overflow: hidden;
}
.hero-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: rgba(255,140,200,0.45);
  position: absolute;
  animation: floaty 6s infinite ease-in-out;
}
@keyframes floaty {
  0% { transform: translateY(0px); opacity: .55;}
  50% { transform: translateY(-14px); opacity: .95;}
  100% { transform: translateY(0px); opacity: .55;}
}

.hero-title {
  font-size: 36px;
  font-weight: 950;
  color: rgba(50,40,45,0.92);
  margin: 0 0 6px 0;
}
.hero-sub {
  color: rgba(50,40,45,0.72);
  font-weight: 700;
  margin-bottom: 10px;
}

/* Timer card */
.timer-wrap {
  display:flex;
  gap: 14px;
  align-items: stretch;
  flex-wrap: wrap;
  margin-top: 14px;
}
.glass {
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(255,160,200,0.35);
  box-shadow: 0 14px 40px rgba(255,105,180,0.12);
  border-radius: 22px;
  padding: 16px 16px;
}
.badge {
  display:inline-block;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255,180,210,0.55);
  border: 1px solid rgba(255,160,200,0.45);
  font-weight: 900;
  font-size: 12px;
}
.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
.digits {
  font-size: 44px;
  font-weight: 950;
  letter-spacing: 1px;
  margin-top: 8px;
  color: rgba(45,35,40,0.95);
}
.muted {
  color: rgba(60,40,50,0.70);
  font-weight: 750;
  margin-top: 6px;
}

/* Modern control buttons (Streamlit buttons will still be used; this is just spacing guidance) */
.controls-row { margin-top: 12px; display:flex; gap: 10px; flex-wrap: wrap; }

/* Table headline */
.h2ish { font-size: 22px; font-weight: 950; margin: 18px 0 10px; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Init DB
# -------------------------
init_db()

# -------------------------
# State
# -------------------------
if "current_activity" not in st.session_state:
    st.session_state.current_activity = None

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "paused" not in st.session_state:
    st.session_state.paused = False

if "pause_started" not in st.session_state:
    st.session_state.pause_started = None

if "paused_seconds" not in st.session_state:
    st.session_state.paused_seconds = 0.0

def _reset_session():
    st.session_state.current_activity = None
    st.session_state.start_time = None
    st.session_state.paused = False
    st.session_state.pause_started = None
    st.session_state.paused_seconds = 0.0

def _effective_elapsed_seconds():
    if not st.session_state.start_time:
        return 0.0

    now = datetime.now()
    if st.session_state.paused and st.session_state.pause_started:
        now = st.session_state.pause_started  # freeze while paused

    raw = (now - st.session_state.start_time).total_seconds()
    return max(0.0, raw - float(st.session_state.paused_seconds))

# -------------------------
# Header + activity pills
# -------------------------
st.markdown("""
<div class="tracker-hero">
  <div class="hero-dot" style="left:10%; top:16%;"></div>
  <div class="hero-dot" style="left:55%; top:10%; animation-delay:1.2s;"></div>
  <div class="hero-dot" style="left:88%; top:26%; animation-delay:2.1s;"></div>

  <div class="hero-title">⏱️ Time Tracker</div>
  <div class="hero-sub">Tap an activity to start. Pause/Resume if you get interrupted. Stop to save 💗</div>
</div>
""", unsafe_allow_html=True)

st.write("")

activities = ["Study 📚", "Ward 🏥", "Lecture 🧑‍🏫", "Break ☕", "Sleep 😴"]
cols = st.columns(len(activities))

for i, act in enumerate(activities):
    if cols[i].button(act, use_container_width=True):
        # start new activity
        st.session_state.current_activity = act
        st.session_state.start_time = datetime.now()
        st.session_state.paused = False
        st.session_state.pause_started = None
        st.session_state.paused_seconds = 0.0
        st.rerun()

st.write("")

# -------------------------
# Running session UI
# -------------------------
is_running = bool(st.session_state.current_activity and st.session_state.start_time)

# refresh only when running and not paused
if is_running and not st.session_state.paused:
    st_autorefresh(interval=1000, key="tracker_tick")

if is_running:
    elapsed_sec = _effective_elapsed_seconds()
    elapsed_h = int(elapsed_sec // 3600)
    elapsed_m = int((elapsed_sec % 3600) // 60)
    elapsed_s = int(elapsed_sec % 60)
    elapsed_str = f"{elapsed_h:02d}:{elapsed_m:02d}:{elapsed_s:02d}"

    target = st.selectbox("Session target (minutes)", [15, 25, 30, 45, 60, 90, 120], index=1)
    target_sec = float(target) * 60.0
    progress = min(1.0, elapsed_sec / target_sec) if target_sec > 0 else 0.0
    pct = int(progress * 100)

    left, right = st.columns([1.2, 1])

    with left:
        status = "⏸ Paused" if st.session_state.paused else "✅ Running"
        st.markdown(f"""
        <div class="glass">
          <span class="badge">{status}</span>
          <div style="margin-top:10px; font-weight:950; font-size:26px;">
            {st.session_state.current_activity}
          </div>
          <div class="muted">Started: {st.session_state.start_time.strftime('%H:%M:%S')}</div>
          <div class="muted">Target: {target} minutes</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown(f"""
        <div class="glass" style="text-align:right;">
          <span class="badge">Elapsed</span>
          <div class="digits mono">{elapsed_str}</div>
          <div class="muted">{pct}% complete</div>
        </div>
        """, unsafe_allow_html=True)

    st.progress(progress)

    # Controls
    a, b, c, d = st.columns([1,1,1,2])

    with a:
        if not st.session_state.paused:
            if st.button("⏸ Pause", use_container_width=True):
                st.session_state.paused = True
                st.session_state.pause_started = datetime.now()
                st.rerun()
        else:
            if st.button("▶️ Resume", use_container_width=True):
                # add paused duration
                if st.session_state.pause_started:
                    paused_add = (datetime.now() - st.session_state.pause_started).total_seconds()
                    st.session_state.paused_seconds += max(0.0, paused_add)
                st.session_state.paused = False
                st.session_state.pause_started = None
                st.rerun()

    with b:
        if st.button("🛑 Stop & Save", type="primary", use_container_width=True):
            end_time = datetime.now()
            # Save using REAL start/end; DB computes minutes, but paused time is excluded from display only.
            # If you want paused excluded in DB too, tell me and I'll adjust db.save_session.
            save_session(st.session_state.current_activity, st.session_state.start_time, end_time)
            st.toast("Saved ✅", icon="✅")
            _reset_session()
            st.rerun()

    with c:
        if st.button("🧹 Reset", use_container_width=True):
            _reset_session()
            st.rerun()

    with d:
        st.caption("Tip: Use **Pause** when you get interrupted so your timer still feels accurate.")

else:
    st.info("No activity running. Start one above 💗")

st.divider()

# -------------------------
# Today Log
# -------------------------
st.markdown('<div class="h2ish">📅 Today’s Log</div>', unsafe_allow_html=True)

rows = get_today_sessions()

if not rows:
    st.write("No sessions saved today yet.")
else:
    df = pd.DataFrame(rows, columns=["Activity", "Start", "End", "Minutes"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    totals = df.groupby("Activity")["Minutes"].sum().sort_values(ascending=False)
    st.markdown('<div class="h2ish">✅ Today’s Totals (minutes)</div>', unsafe_allow_html=True)
    st.bar_chart(totals)
