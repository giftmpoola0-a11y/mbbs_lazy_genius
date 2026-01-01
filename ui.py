import base64
from pathlib import Path
import streamlit as st

def _img_to_base64(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return base64.b64encode(p.read_bytes()).decode()

def apply_girly_theme():
    # Load local background (optional)
    bg_b64 = _img_to_base64("assets/teddy_bg.png")
    bg_css = ""
    if bg_b64:
        bg_css = f"""
.stApp {{
    background:
      linear-gradient(rgba(255,247,251,0.80), rgba(255,227,241,0.80)),
      url("data:image/png;base64,{bg_b64}");
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center center;
    background-attachment: fixed;
}}
"""


    st.markdown(
        f"""
        <style>
        /* Import cute fonts */
        @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@400;600;700&family=Pacifico&display=swap');

        {bg_css}

        /* Main font */
        html, body, [class*="css"] {{
            font-family: 'Quicksand', sans-serif !important;
        }}

        /* Cute title font */
        h1, h2, h3 {{
            font-family: 'Pacifico', cursive !important;
            letter-spacing: 0.5px;
        }}

        /* Make content area look like a soft card */
        .block-container {{
            background: rgba(255, 255, 255, 0.78);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 95, 162, 0.25);
            border-radius: 22px;
            padding: 1.6rem 1.6rem 2rem 1.6rem;
            box-shadow: 0 10px 30px rgba(255, 95, 162, 0.12);
        }}

        /* Sidebar styling */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(255, 227, 241, 0.95), rgba(255, 247, 251, 0.95));
            border-right: 1px solid rgba(255, 95, 162, 0.18);
        }}

        /* Inputs */
        .stTextInput input, .stTextArea textarea, .stNumberInput input {{
            border-radius: 16px !important;
            border: 1px solid rgba(255, 95, 162, 0.25) !important;
            background: rgba(255,255,255,0.9) !important;
        }}

        /* Buttons */
        .stButton button {{
            border-radius: 18px !important;
            border: 1px solid rgba(255, 95, 162, 0.35) !important;
            padding: 0.55rem 1.1rem !important;
            font-weight: 700 !important;
            background: linear-gradient(135deg, #ff5fa2, #ff9ac7) !important;
            color: white !important;
            box-shadow: 0 10px 22px rgba(255, 95, 162, 0.22);
            transition: transform 0.08s ease-in-out;
        }}
        .stButton button:hover {{
            transform: translateY(-1px) scale(1.01);
        }}

        /* Tabs */
        button[data-baseweb="tab"] {{
            border-radius: 16px 16px 0 0 !important;
            padding: 0.6rem 1rem !important;
        }}
        div[data-baseweb="tab-list"] {{
            gap: 8px;
        }}

        /* Dataframe */
        .stDataFrame {{
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(255, 95, 162, 0.18);
            background: rgba(255,255,255,0.85);
        }}

        /* Cute little sparkle animation (subtle) */
        @keyframes sparkle {{
            0% {{ opacity: 0.6; transform: translateY(0px); }}
            50% {{ opacity: 1; transform: translateY(-2px); }}
            100% {{ opacity: 0.6; transform: translateY(0px); }}
        }}
        .sparkle {{
            display: inline-block;
            animation: sparkle 2s infinite;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
