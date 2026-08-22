"""
AI StudySmart — Your Intelligent AI Learning Companion
Main entry point. Run with: streamlit run app.py
"""

import streamlit as st
from database.database import init_db
from views.theme import inject_theme, icon

st.set_page_config(
    page_title="AI StudySmart",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()
init_db()

# ── Sidebar extra CSS (active state + nav polish) ──────────────────────────────
st.markdown("""
<style>
/* ── Sidebar width lock ── */
[data-testid="stSidebar"] {
  width: 252px !important;
  min-width: 252px !important;
  max-width: 252px !important;
}

/* ── Hide the radio dot entirely ── */
[data-testid="stSidebar"] .stRadio div[data-baseweb="radio"] > div:first-child {
  display: none !important;
}

/* ── Nav item base ── */
[data-testid="stSidebar"] .stRadio label {
  display: flex !important;
  align-items: center !important;
  padding: 0.55rem 0.9rem !important;
  border-radius: 9px !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  color: #8A93A6 !important;
  cursor: pointer !important;
  transition: all 0.18s ease !important;
  border: 1px solid transparent !important;
  margin: 1px 8px !important;
  letter-spacing: 0.01em !important;
  gap: 0.55rem !important;
}

/* ── Hover ── */
[data-testid="stSidebar"] .stRadio label:hover {
  background: rgba(192,132,252,0.08) !important;
  color: #E6EDF3 !important;
  border-color: rgba(192,132,252,0.18) !important;
}

/* ── Active / selected ── */
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked),
[data-testid="stSidebar"] .stRadio div[data-baseweb="radio"]:has(input:checked) label,
[data-testid="stSidebar"] .stRadio label:has(input:checked) {
  background: rgba(192,132,252,0.13) !important;
  color: #E6EDF3 !important;
  border-color: rgba(192,132,252,0.32) !important;
  font-weight: 600 !important;
}

/* ── Sidebar content scroll area — leave room for footer ── */
[data-testid="stSidebar"] section[data-testid="stSidebarContent"] {
  padding-bottom: 90px !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

/* ── Remove default radio label ── */
.stRadio > label { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
_NAV_ITEMS = [
    "Dashboard",
    "AI Study Assistant",
    "Smart Notes",
    "AI Quiz",
    "Flashcards",
    "My Progress",
    "Study Plan",
]

with st.sidebar:
    # ── Brand block ────────────────────────────────────────────────────────────
    _logo_svg = icon("sparkles", 18, color="#0A0D12", circle=False)
    st.markdown(f"""
    <div style="padding:1.6rem 1.1rem 0.9rem 1.1rem;">
        <div style="display:flex;align-items:center;gap:0.65rem;">
            <div style="background:linear-gradient(135deg,#7C3AED,#C084FC);
                        border-radius:11px;width:38px;height:38px;flex-shrink:0;
                        display:flex;align-items:center;justify-content:center;
                        box-shadow:0 4px 16px rgba(192,132,252,0.35);">
                {_logo_svg}
            </div>
            <div>
                <div style="font-size:1.05rem;font-weight:800;color:#E6EDF3;
                             font-family:'Sora',sans-serif;letter-spacing:-0.02em;
                             line-height:1.15;">AI StudySmart</div>
                <div style="font-size:0.63rem;color:#8A93A6;letter-spacing:0.02em;
                             margin-top:1px;line-height:1.3;">
                    Your Intelligent AI Learning Companion
                </div>
            </div>
        </div>
    </div>
    <div style="height:1px;
                background:linear-gradient(90deg,transparent,rgba(192,132,252,0.18),transparent);
                margin:0 0.9rem 0.7rem;"></div>
    <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.13em;
                text-transform:uppercase;color:#4a5568;
                padding:0 0.5rem 0.35rem 1.1rem;">Menu</div>
    """, unsafe_allow_html=True)

    # ── Navigation radio ───────────────────────────────────────────────────────
    # Prepend emoji to each label so items look distinct without custom HTML
    page = st.radio(
        label="Navigation",
        options=_NAV_ITEMS,
        label_visibility="collapsed",
    )

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="position:fixed;bottom:0;left:0;width:252px;
                background:linear-gradient(180deg,transparent,#08060F 55%);
                padding:1rem 1.1rem 0.9rem;
                border-top:1px solid rgba(192,132,252,0.07);">
        <div style="font-size:0.62rem;color:#4a5568;line-height:1.7;">
            Python · Streamlit · SQLite
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── ROUTING ───────────────────────────────────────────────────────────────────
if page == "Dashboard":
    from views.dashboard import show
    show()
elif page == "AI Study Assistant":
    from views.study_chat import show
    show()
elif page == "Smart Notes":
    from views.notes import show
    show()
elif page == "AI Quiz":
    from views.quiz import show
    show()
elif page == "Flashcards":
    from views.flashcards import show
    show()
elif page == "My Progress":
    from views.progress import show
    show()
elif page == "Study Plan":
    from views.study_plan import show
    show()
