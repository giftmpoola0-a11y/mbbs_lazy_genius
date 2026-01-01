import streamlit as st
import pandas as pd
from datetime import date, timedelta

from db import init_db, get_sessions_between
from ui import apply_girly_theme
apply_girly_theme()


st.title("📊 Analytics (Weekly / Monthly)")

init_db()

# Default range: last 7 days
today = date.today()
default_start = today - timedelta(days=6)
default_end = today

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start date", value=default_start)
with col2:
    end_date = st.date_input("End date", value=default_end)

if start_date > end_date:
    st.error("Start date must be before end date.")
    st.stop()

rows = get_sessions_between(start_date, end_date)

st.divider()
st.subheader("🧾 Sessions in Range")

if not rows:
    st.write("No sessions found in this range.")
    st.stop()

df = pd.DataFrame(rows, columns=["Activity", "Start", "End", "Minutes"])

# Add a Date column for grouping
df["Date"] = df["Start"].str.slice(0, 10)

st.dataframe(df, use_container_width=True)

st.divider()

# Totals per activity
st.subheader("✅ Totals per Activity (minutes)")
totals = df.groupby("Activity")["Minutes"].sum().sort_values(ascending=False)
st.bar_chart(totals)

# Daily totals trend
st.subheader("📅 Daily Total Minutes (trend)")
daily = df.groupby("Date")["Minutes"].sum().sort_index()
st.line_chart(daily)

# Summary stats
st.subheader("📌 Summary")
total_minutes = df["Minutes"].sum()
st.metric("Total minutes", f"{total_minutes:.1f}")
st.metric("Total hours", f"{total_minutes/60:.2f}")
