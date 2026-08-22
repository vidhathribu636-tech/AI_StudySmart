"""
views/study_chat.py — AI StudySmart chat interface.
"""
import streamlit as st
from ai.ai_service import generate_ai_response, is_ai_available
from views.theme import inject_theme, icon

_HISTORY_KEY = "study_chat_history"
_VERSION_KEY = "study_chat_version"
_CURRENT_VERSION = 2  # bump this to force-clear old sessions

SUGGESTED = [
    "Explain the concept of recursion with a simple example",
    "What is photosynthesis and how does it work?",
    "Summarise the main causes of World War I",
    "Explain Newton's three laws of motion",
]


def _init_session():
    if st.session_state.get(_VERSION_KEY) != _CURRENT_VERSION:
        st.session_state[_HISTORY_KEY] = []
        st.session_state[_VERSION_KEY] = _CURRENT_VERSION
    elif _HISTORY_KEY not in st.session_state:
        st.session_state[_HISTORY_KEY] = []


def _render_message(role: str, text: str):
    if role == "user":
        st.markdown(f"""
        <div class="chat-user-wrap">
            <div class="chat-user-bubble">{text}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="chat-ai-wrap" style="align-items:center;margin-bottom:0.3rem;">
            <div class="chat-ai-avatar">🤖</div>
            <span style="font-size:0.72rem;font-weight:600;color:#8A93A6;
                         letter-spacing:0.04em;text-transform:uppercase;">AI StudySmart</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="chat-ai-bubble" style="margin-left:2.8rem;margin-bottom:0.8rem;">
        """, unsafe_allow_html=True)
        st.markdown(text)
        st.markdown("</div>", unsafe_allow_html=True)


def _api_key_banner():
    st.markdown("""
    <div class="info-box" style="margin-top:1rem;">
        <h4>🔑 API Key Required</h4>
        <p>To use the AI Study Assistant, add your free Google Gemini API key to the
        <code>.env</code> file in the project root.</p>
    </div>
    <ol style="color:#8A93A6;font-size:0.85rem;line-height:2.2;padding-left:1.4rem;margin:1rem 0 0;">
        <li>Get a free key at <a href="https://aistudio.google.com/app/apikey"
            style="color:#C084FC;text-decoration:none;">aistudio.google.com/app/apikey</a></li>
        <li>Open <code>.env</code> in the project folder</li>
        <li>Set: <code style="color:#C084FC;">GEMINI_API_KEY=your_key_here</code></li>
        <li>Restart the app</li>
    </ol>
    """, unsafe_allow_html=True)


def show():
    inject_theme()
    _init_session()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-header">
        <div class="badge">✦ Live AI</div>
        <h2>AI Study Assistant</h2>
        <p>Ask questions, explore concepts, and learn at your own pace with your AI tutor.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:linear-gradient(90deg,transparent,rgba(192,132,252,0.08),transparent);margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    if not is_ai_available():
        _api_key_banner()
        return

    history: list[dict] = st.session_state[_HISTORY_KEY]

    # ── Empty state ───────────────────────────────────────────────────────────
    if not history:
        st.markdown(f"""
        <div style="text-align:center;padding:2.5rem 1rem 1.5rem;animation:fadeSlideUp 0.5s ease both;">
            <div style="display:inline-flex;align-items:center;justify-content:center;
                        width:64px;height:64px;border-radius:50%;
                        background:linear-gradient(135deg,#100D1A,#17122A);
                        border:1px solid rgba(192,132,252,0.25);
                        box-shadow:0 0 30px rgba(192,132,252,0.15);
                        margin-bottom:1rem;
                        animation:float 4s ease-in-out infinite;">
                {icon('bot', 28, circle=False)}
            </div>
            <div style="font-size:1.1rem;font-weight:700;color:#E6EDF3;margin-bottom:0.4rem;
                        font-family:'Sora',sans-serif;">
                AI StudySmart Assistant
            </div>
            <div style="font-size:0.875rem;color:#8A93A6;max-width:400px;margin:0 auto;line-height:1.65;">
                Ask me anything — concepts, definitions, or a topic you're struggling with.
                I'll give you clear, structured explanations.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<span class='section-label' style='display:block;text-align:center;margin:1rem 0 0.6rem;'>Try asking</span>", unsafe_allow_html=True)
        sq_col1, sq_col2 = st.columns(2, gap="medium")
        for i, q in enumerate(SUGGESTED):
            with (sq_col1 if i % 2 == 0 else sq_col2):
                if st.button(q, key=f"sq_{i}", use_container_width=True):
                    history.append({"role": "user", "text": q})
                    with st.spinner("Thinking…"):
                        try:
                            ans = generate_ai_response(user_prompt=q, conversation_history=[])
                            history.append({"role": "model", "text": ans})
                        except Exception as e:
                            history.pop()
                            st.error(f"⚠️ {e}")
                    st.rerun()
    else:
        # ── Chat history ──────────────────────────────────────────────────────
        for turn in history:
            _render_message(turn["role"], turn["text"])

        st.markdown("<div style='margin-top:0.6rem;'></div>", unsafe_allow_html=True)
        if st.button("Clear chat", key="clear_chat"):
            st.session_state[_HISTORY_KEY] = []
            st.rerun()

    # ── Input ─────────────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1.4rem;'></div>", unsafe_allow_html=True)
    with st.form("chat_form", clear_on_submit=True):
        ci, cb = st.columns([6, 1])
        with ci:
            user_input = st.text_input(
                "Ask a question",
                placeholder="e.g. What is the difference between RAM and ROM?",
                label_visibility="collapsed",
            )
        with cb:
            submitted = st.form_submit_button("Ask", use_container_width=True)

    if submitted and user_input.strip():
        q = user_input.strip()
        history.append({"role": "user", "text": q})
        with st.spinner("Thinking…"):
            try:
                ans = generate_ai_response(user_prompt=q, conversation_history=history[:-1])
                history.append({"role": "model", "text": ans})
            except EnvironmentError as e:
                st.error(f"⚠️ Config error: {e}")
                history.pop()
            except RuntimeError as e:
                st.error(f"⚠️ {e}")
                history.pop()
        st.rerun()
