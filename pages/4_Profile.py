import streamlit as st
import os
import json
import base64
from pathlib import Path

from db import init_db, init_profile_table, get_profile, update_profile

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Profile", page_icon="💗", layout="wide")

st.markdown("## 💗 Profile")
st.caption("Update your details and your cute profile pic 🧸✨")

# -------------------------
# Helpers (TEACH MODE)
# -------------------------
def s(x):
    """Safe string: prevents None.strip() crashes."""
    return (x or "").strip()

def ensure_dir(p: str):
    Path(p).mkdir(parents=True, exist_ok=True)

def circular_avatar_from_file(photo_path: str, size: int = 190):
    """
    Shows a PERFECT circular avatar using base64 HTML.
    This avoids Streamlit sizing issues and always fills the circle.
    """
    if not photo_path or not Path(photo_path).exists():
        st.markdown(
            f"""
            <div style="
                width:{size}px;height:{size}px;border-radius:999px;
                border:4px solid rgba(255,95,162,0.45);
                background:rgba(255,255,255,0.95);
                display:flex;align-items:center;justify-content:center;
                box-shadow:0 18px 40px rgba(255,95,162,0.18);
                font-size:52px;
            ">🧸</div>
            """,
            unsafe_allow_html=True
        )
        return

    img_bytes = Path(photo_path).read_bytes()
    b64 = base64.b64encode(img_bytes).decode("utf-8")

    st.markdown(
        f"""
        <div style="
            width:{size}px;height:{size}px;border-radius:999px; overflow:hidden;
            border:4px solid rgba(255,95,162,0.45);
            background:rgba(255,255,255,0.95);
            box-shadow:0 18px 40px rgba(255,95,162,0.18);
        ">
            <img src="data:image/png;base64,{b64}"
                 style="width:100%;height:100%;object-fit:cover;border-radius:999px;" />
        </div>
        """,
        unsafe_allow_html=True
    )

def save_uploaded_photo(uploaded_file) -> str:
    """
    Save uploaded image into /assets/profile/ and return saved file path.
    """
    ensure_dir("assets/profile")
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        ext = ".png"

    out_path = Path("assets/profile/profile_pic" + ext)
    out_path.write_bytes(uploaded_file.getbuffer())
    return str(out_path)

# -------------------------
# DB init + Load profile
# -------------------------
init_db()
init_profile_table()

profile = get_profile() or {}  # if DB returns None, use empty dict

# pull values safely
full_name = s(profile.get("full_name"))
nickname  = s(profile.get("nickname"))
school    = s(profile.get("school"))
year      = s(profile.get("year"))
university= s(profile.get("university"))
email     = s(profile.get("email"))
phone     = s(profile.get("phone"))
bio       = s(profile.get("bio"))
photo_path= s(profile.get("photo_path"))

# -------------------------
# Layout
# -------------------------
left, right = st.columns([1, 2], gap="large")

# ===== LEFT: PHOTO =====
with left:
    st.markdown("### 🖼️ Profile Picture")

    circular_avatar_from_file(photo_path, size=210)
    st.write("")  # spacing

    st.markdown("**Upload a new picture**")
    uploaded = st.file_uploader(
        " ",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed"
    )

    colA, colB = st.columns(2)
    with colA:
        if uploaded is not None:
            if st.button("✨ Use this photo", type="primary", use_container_width=True):
                new_path = save_uploaded_photo(uploaded)
                photo_path = new_path  # update local state
                # Save just the photo now, keep other fields same
                update_profile(
                    full_name=full_name,
                    nickname=nickname,
                    school=school,
                    year=year,
                    university=university,
                    email=email,
                    phone=phone,
                    bio=bio,
                    photo_path=photo_path
                )
                st.success("Photo updated ✅")
                st.rerun()

    with colB:
        if st.button("🗑️ Remove photo", use_container_width=True):
            # remove file if exists
            try:
                if photo_path and Path(photo_path).exists():
                    Path(photo_path).unlink()
            except Exception:
                pass

            photo_path = ""
            update_profile(
                full_name=full_name,
                nickname=nickname,
                school=school,
                year=year,
                university=university,
                email=email,
                phone=phone,
                bio=bio,
                photo_path=photo_path
            )
            st.success("Removed ✅")
            st.rerun()

# ===== RIGHT: DETAILS =====
with right:
    st.markdown("### 🧸 Your Details")

    # We use a form so Streamlit only saves when you click (less bugs)
    with st.form("profile_form", clear_on_submit=False):
        full_name_in = st.text_input("Full name", value=full_name, placeholder="e.g., Marcia Chiwalo")
        nickname_in  = st.text_input("Nickname (optional)", value=nickname, placeholder="e.g., Marcia")
        school_in    = st.text_input("School / College", value=school, placeholder="e.g., KUHES")
        year_in      = st.text_input("Year (e.g., Final Year)", value=year, placeholder="Final Year")
        university_in= st.text_input("University", value=university, placeholder="e.g., KUHES")

        c1, c2 = st.columns(2)
        with c1:
            email_in = st.text_input("Email", value=email, placeholder="name@email.com")
        with c2:
            phone_in = st.text_input("Phone", value=phone, placeholder="+265 / +1 ...")

        bio_in = st.text_area("Bio / Focus right now", value=bio, height=120, placeholder="What are you focusing on this week?")

        save = st.form_submit_button("💾 Save Profile", type="primary")

    if save:
        update_profile(
            full_name=s(full_name_in),
            nickname=s(nickname_in),
            school=s(school_in),
            year=s(year_in),
            university=s(university_in),
            email=s(email_in),
            phone=s(phone_in),
            bio=s(bio_in),
            photo_path=s(photo_path),
        )
        st.success("Saved! 💗")
        st.rerun()
