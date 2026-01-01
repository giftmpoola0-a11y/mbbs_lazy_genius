from db import delete_all_questions
import streamlit as st
import pandas as pd
from random import choice
import json
import os
from datetime import datetime
from io import BytesIO

from openai import OpenAI

from db import init_db, init_questions_table, add_question, get_questions, mark_answer
from ui import apply_girly_theme
apply_girly_theme()

# PDF tools (reportlab)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

st.title("🧠 Practice Questions (AI)")

# --- DB setup
init_db()
init_questions_table()

# --- OpenAI client setup (from Streamlit secrets)
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

client = OpenAI()


# -------------------------
# PDF helper
# -------------------------
def build_revision_pdf(topic: str, notes: str, questions: list) -> bytes:
    """
    Creates a PDF (bytes) containing:
    - Topic + date
    - Notes
    - Generated questions + answers
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=0.8 * inch,
        leftMargin=0.8 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title=f"{topic} - Revision Pack"
    )

    styles = getSampleStyleSheet()
    H = styles["Heading1"]
    H2 = styles["Heading2"]
    P = styles["BodyText"]

    story = []

    story.append(Paragraph(f"{topic} — Revision Pack", H))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", P))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Notes", H2))
    story.append(Spacer(1, 6))
    # Keep notes formatting readable (basic line breaks)
    for line in (notes or "").split("\n"):
        line = line.strip()
        if line:
            story.append(Paragraph(line, P))
        else:
            story.append(Spacer(1, 6))

    story.append(PageBreak())

    story.append(Paragraph("Questions + Answers", H2))
    story.append(Spacer(1, 12))

    for i, q in enumerate(questions, start=1):
        q_type = q.get("q_type", "Short Answer")
        q_text = q.get("question", "")
        ans = q.get("answer", "")

        story.append(Paragraph(f"{i}. [{q_type}] {q_text}", styles["Heading3"]))
        story.append(Spacer(1, 6))

        # Add choices if MCQ
        choices = q.get("choices") or []
        if choices:
            for j, opt in enumerate(choices):
                letter_ = ["A", "B", "C", "D"][j] if j < 4 else str(j + 1)
                story.append(Paragraph(f"{letter_}) {opt}", P))
            story.append(Spacer(1, 6))

        story.append(Paragraph("<b>Answer:</b>", P))
        for line in (ans or "").split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line, P))
            else:
                story.append(Spacer(1, 6))

        story.append(Spacer(1, 14))

    doc.build(story)
    return buf.getvalue()


# -------------------------
# AI generator
# -------------------------
def generate_questions_from_notes(topic: str, notes: str, n_mcq: int, n_short: int):
    schema = {
        "name": "question_pack",
        "schema": {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "q_type": {"type": "string", "enum": ["MCQ", "Short Answer"]},
                            "question": {"type": "string"},
                            "answer": {"type": "string"},
                            "choices": {"type": "array", "items": {"type": "string"}},
                            "correct_choice_index": {"type": "integer", "minimum": 0, "maximum": 3},
                        },
                        "required": ["q_type", "question", "answer", "choices", "correct_choice_index"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["questions"],
            "additionalProperties": False,
        },
    }

    # 🔥 Upgraded prompt for high-quality, memorable answers
    prompt = f"""
You are an MBBS final-year exam tutor and question writer.

ONLY use information found in the notes. Do NOT invent facts.
If a detail is missing in the notes, write: "Not in notes."

Topic: {topic}

Return JSON that matches the schema exactly.

You must generate:
- {n_mcq} MCQs
- {n_short} Short Answer questions

Formatting rules (IMPORTANT):
1) For EVERY question object, ALWAYS include: q_type, question, answer, choices, correct_choice_index.
2) MCQ:
   - choices MUST have exactly 4 options.
   - correct_choice_index MUST be 0-3.
   - answer MUST be LONG and include all of:
     - "Correct: <A/B/C/D> — <correct option text>"
     - "Explanation:" (high-yield, step-by-step)
     - "Why others are wrong:" (1 line per option)
     - "Memory hook / mnemonic:" (short but sticky)
     - "Exam trap:" (common confusion)
3) Short Answer:
   - choices MUST be [] and correct_choice_index MUST be 0.
   - answer MUST be LONG and include all of:
     - "Core answer:" (direct exam-style)
     - "Explanation:" (breakdown from the notes)
     - "Memory hook:" (sticky recall)
     - "Exam trap:" (common mistake)
     - "Mini self-check:" (1 quick question to test recall)

Notes:
{notes}
""".strip()

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "question_pack",
                "strict": True,
                "schema": schema["schema"],
            }
        },
    )

    data = json.loads(resp.output_text)
    return data["questions"]


# -------------------------
# UI tabs
# -------------------------
tab1, tab2 = st.tabs(["⚡ AI Generate", "🎯 Quiz Mode"])


# -------------------------
# TAB 1: AI GENERATE
# -------------------------
with tab1:
    st.subheader("Generate questions from your notes (AI)")

    topic = st.text_input("Topic", value="General")
    notes = st.text_area("Paste notes here", height=220, placeholder="Paste lecture notes or high-yield summary...")

    colA, colB = st.columns(2)
    with colA:
        n_mcq = st.number_input("How many MCQs?", min_value=0, max_value=30, value=6, step=1)
    with colB:
        n_short = st.number_input("How many Short Answer?", min_value=0, max_value=30, value=3, step=1)

    if "last_generated" not in st.session_state:
        st.session_state.last_generated = None

    if st.button("✨ Generate & Save to Bank", type="primary"):
        if not notes.strip():
            st.error("Paste some notes first.")
        else:
            with st.spinner("Generating high-yield questions + proper answers..."):
                qs = generate_questions_from_notes(topic.strip(), notes.strip(), int(n_mcq), int(n_short))

            # Save all generated into DB
            for q in qs:
                add_question(topic.strip(), q.get("q_type", "Short Answer"), q["question"], q["answer"])

            # Save for PDF download + preview
            st.session_state.last_generated = {
                "topic": topic.strip(),
                "notes": notes.strip(),
                "questions": qs
            }

            st.success(f"Saved {len(qs)} questions ✅")
            st.rerun()

    # --- Show generated preview + PDF download
    if st.session_state.last_generated:
        st.divider()
        st.subheader("✅ Latest Generated Pack (Preview)")

        pack = st.session_state.last_generated
        for i, q in enumerate(pack["questions"], start=1):
            st.markdown(f"### {i}. {q['q_type']}")
            st.write(q["question"])

            if q.get("choices"):
                letters = ["A", "B", "C", "D"]
                for idx, opt in enumerate(q["choices"]):
                    st.write(f"**{letters[idx]})** {opt}")

            with st.expander("Show full answer (high-yield)"):
                st.write(q["answer"])

        # PDF download
        pdf_bytes = build_revision_pdf(pack["topic"], pack["notes"], pack["questions"])
        st.download_button(
            "📄 Download Revision PDF (notes + Q&A)",
            data=pdf_bytes,
            file_name=f"{pack['topic']}_revision_pack.pdf".replace(" ", "_"),
            mime="application/pdf",
            type="primary"
        )

    st.divider()
    st.subheader("📚 Question Bank Preview (latest 20)")

    rows = get_questions(None)
    if rows:
        df = pd.DataFrame(rows[:20], columns=["ID", "Topic", "Type", "Question", "Answer", "Created", "Correct", "Wrong"])
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No questions yet. Generate some above.")

    st.divider()
    st.subheader("⚠️ Danger Zone")

    if st.button("🗑️ Delete ALL questions", type="secondary"):
        delete_all_questions()
        st.success("All questions deleted.")
        st.rerun()


# -------------------------
# TAB 2: QUIZ MODE
# -------------------------
with tab2:
    st.subheader("Quiz yourself (fast recall)")

    filter_topic = st.text_input("Filter topic (optional)", placeholder="Leave blank to quiz everything")

    rows = get_questions(filter_topic if filter_topic else None)
    if not rows:
        st.info("No questions available for this topic yet.")
        st.stop()

    if "quiz_q" not in st.session_state:
        st.session_state.quiz_q = None

    if st.button("🎲 Give me a question"):
        st.session_state.quiz_q = choice(rows)

    if st.session_state.quiz_q is None:
        st.write("Click **Give me a question** to start.")
    else:
        q_id, topic, q_type, q_text, a_text, created, correct, wrong = st.session_state.quiz_q

        st.markdown(f"### 📝 {q_type} — *{topic}*")
        st.write(q_text)

        with st.expander("Show Answer (full explanation)"):
            st.write(a_text)

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ I got it"):
                mark_answer(q_id, True)
                st.session_state.quiz_q = None
                st.toast("Logged ✅", icon="✅")
                st.rerun()
        with col2:
            if st.button("❌ I missed it"):
                mark_answer(q_id, False)
                st.session_state.quiz_q = None
                st.toast("Logged ❌", icon="❌")
                st.rerun()
        with col3:
            st.caption(f"Stats: ✅ {correct} | ❌ {wrong}")
