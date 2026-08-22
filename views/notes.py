"""
views/notes.py — Smart Notes with AI summarization and download.
"""
import datetime
import streamlit as st
from ai.ai_service import summarize_notes, is_ai_available
from utils.pdf_reader import extract_text_from_pdf
from database.database import get_connection
from views.theme import inject_theme, icon

_SUMMARY_KEY  = "notes_summary"
_TEXT_KEY     = "notes_extracted_text"
_TITLE_KEY    = "notes_current_title"

MAX_CHARS = 15_000


def _init_session():
    for key, default in [(_SUMMARY_KEY, ""), (_TEXT_KEY, ""), (_TITLE_KEY, "")]:
        if key not in st.session_state:
            st.session_state[key] = default


def _save_summary(title: str, summary: str):
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO saved_notes (title, summary) VALUES (?, ?)",
                (title, summary),
            )
    except Exception:
        pass


def _load_saved_summaries():
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, title, summary, created_at FROM saved_notes ORDER BY created_at DESC LIMIT 20"
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _delete_summary(note_id: int):
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM saved_notes WHERE id = ?", (note_id,))
    except Exception:
        pass


def _download_btn(title: str, summary: str, key: str):
    """Render a st.download_button for a summary as a .txt file."""
    content = f"{title}\n{'=' * len(title)}\n\n{summary}\n"
    filename = title.replace(" ", "_").replace("/", "-")[:60] + ".txt"
    st.download_button(
        label="⬇ Download Summary",
        data=content.encode("utf-8"),
        file_name=filename,
        mime="text/plain",
        key=key,
    )


def show():
    inject_theme()
    _init_session()

    # Fix: file-uploader browse button and download button text visibility
    st.markdown("""
    <style>
    /* ── File uploader: hide the default Streamlit dropzone entirely
          and replace with our own styled button via label trick ── */
    [data-testid="stFileUploaderDropzone"] {
        background: #17122A !important;
        border: 1.5px dashed rgba(192,132,252,0.3) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    /* All text inside the dropzone */
    [data-testid="stFileUploaderDropzone"] *,
    [data-testid="stFileUploaderDropzoneInstructions"] *,
    [data-testid="stFileUploaderDropzoneInstructions"] span,
    [data-testid="stFileUploaderDropzoneInstructions"] small {
        color: #C084FC !important;
        font-weight: 500 !important;
    }
    /* The actual Browse/Upload button inside the dropzone */
    [data-testid="stFileUploaderDropzone"] button,
    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"],
    [data-testid="stFileUploader"] button[kind="secondary"] {
        background: linear-gradient(135deg,#7C3AED,#C084FC) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        padding: 0.4rem 1rem !important;
        box-shadow: 0 2px 10px rgba(192,132,252,0.3) !important;
    }
    [data-testid="stFileUploaderDropzone"] button *,
    [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] *,
    [data-testid="stFileUploader"] button[kind="secondary"] * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }
    /* File uploader outer label */
    [data-testid="stFileUploader"] > label,
    [data-testid="stFileUploader"] label[data-testid="stWidgetLabel"] {
        color: #E6EDF3 !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
    }
    /* Uploaded file name chip */
    [data-testid="stFileUploader"] [data-testid="stFileUploaderFile"] span {
        color: #E6EDF3 !important;
    }
    /* ── Download button ── */
    [data-testid="stDownloadButton"] > button {
        background: rgba(192,132,252,0.15) !important;
        color: #E6EDF3 !important;
        border: 1px solid rgba(192,132,252,0.4) !important;
        box-shadow: none !important;
        animation: none !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background: rgba(192,132,252,0.28) !important;
        color: #FFFFFF !important;
        border-color: rgba(192,132,252,0.7) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 14px rgba(192,132,252,0.25) !important;
    }
    [data-testid="stDownloadButton"] > button *,
    [data-testid="stDownloadButton"] > button p,
    [data-testid="stDownloadButton"] > button span,
    [data-testid="stDownloadButton"] > button div {
        color: #E6EDF3 !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="page-header">
        <div class="badge">✦ AI Summarization</div>
        <h2>Smart Notes</h2>
        <p>Upload your PDF or paste text — AI extracts the key points so you study smarter.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:linear-gradient(90deg,transparent,rgba(192,132,252,0.08),transparent);margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    if not is_ai_available():
        st.markdown(f"""
        <div class="info-box">
            <h4>{icon('key', 16, circle=False)} API Key Required</h4>
            <p>Add your <code>GEMINI_API_KEY</code> to the <code>.env</code> file to use Smart Notes.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    main_tab, history_tab = st.tabs(["✦ Summarize", "📂 Saved Summaries"])

    with main_tab:
        tab_pdf, tab_paste = st.tabs(["📄 Upload PDF", "📝 Paste Text"])
        notes_text = ""

        with tab_pdf:
            st.markdown("<div style='margin:1rem 0 0.8rem;'></div>", unsafe_allow_html=True)
            # Upload area decoration
            st.markdown(f"""
            <div style="background:var(--bg-card);
                        border:1.5px dashed rgba(192,132,252,0.25);border-radius:16px;
                        padding:1.8rem 1.5rem;text-align:center;margin-bottom:0.8rem;">
                <div style="display:flex;justify-content:center;margin-bottom:0.7rem;">
                    {icon('upload', 26)}
                </div>
                <div style="font-size:0.9rem;font-weight:600;color:#E6EDF3;margin-bottom:0.25rem;">
                    Drop your PDF here or click to browse
                </div>
                <div style="font-size:0.78rem;color:#8A93A6;">Supported format: PDF · Max recommended: 10 MB</div>
            </div>
            """, unsafe_allow_html=True)

            # File uploader — label visible so button text is readable
            uploaded = st.file_uploader(
                "📄 Choose PDF file",
                type=["pdf"],
                label_visibility="visible",
            )
            if uploaded:
                with st.spinner("Reading PDF…"):
                    extracted = extract_text_from_pdf(uploaded)
                if extracted.startswith("PDF extraction is not available") or extracted.startswith("Could not read"):
                    st.error(extracted)
                else:
                    st.session_state[_TEXT_KEY] = extracted
                    st.success(f"✅ Extracted {len(extracted):,} characters from **{uploaded.name}**")

            if st.session_state[_TEXT_KEY]:
                with st.expander("Preview extracted text"):
                    st.text(st.session_state[_TEXT_KEY][:2000] + ("…" if len(st.session_state[_TEXT_KEY]) > 2000 else ""))
                notes_text = st.session_state[_TEXT_KEY]

        with tab_paste:
            st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
            pasted = st.text_area(
                "Paste your study notes",
                placeholder="Paste text from your notes, textbook, or any study material…",
                height=220,
                label_visibility="collapsed",
            )
            if pasted.strip():
                st.session_state[_TEXT_KEY] = pasted.strip()
                notes_text = pasted.strip()

        # Input length warning
        if notes_text and len(notes_text) > MAX_CHARS:
            st.warning(f"⚠️ Input is {len(notes_text):,} characters — only the first {MAX_CHARS:,} will be sent to AI.")
            notes_text = notes_text[:MAX_CHARS]

        st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)

        title_col, btn_col = st.columns([3, 1])
        with title_col:
            note_title = st.text_input(
                "Summary title (optional)",
                placeholder="e.g. Chapter 3 — OS Scheduling",
                label_visibility="collapsed",
            )
        with btn_col:
            summarize_clicked = st.button("✨ Summarize with AI", disabled=not bool(notes_text or st.session_state.get(_TEXT_KEY, "")), use_container_width=True)

        if summarize_clicked:
            effective_text = notes_text or st.session_state.get(_TEXT_KEY, "")
            with st.spinner("AI is summarizing your notes…"):
                try:
                    summary = summarize_notes(effective_text)
                    st.session_state[_SUMMARY_KEY] = summary
                    title = note_title.strip() or f"Summary {datetime.datetime.now().strftime('%b %d %H:%M')}"
                    st.session_state[_TITLE_KEY] = title
                    _save_summary(title, summary)
                    st.success("✅ Summary saved to history!")
                except RuntimeError as e:
                    st.error(f"AI error: {e}")

        # ── Summary display ───────────────────────────────────────────────────
        if st.session_state[_SUMMARY_KEY]:
            st.markdown("""
            <div style="margin-top:1.8rem;">
                <span class="section-label">AI Summary</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div style="background:var(--bg-card);
                        border:1px solid var(--border-accent);border-radius:16px;
                        padding:1.5rem 1.7rem;font-size:0.9rem;color:#E6EDF3;
                        line-height:1.85;margin-top:0.5rem;animation:fadeSlideUp 0.4s ease both;">
            """, unsafe_allow_html=True)
            st.markdown(st.session_state[_SUMMARY_KEY])
            st.markdown("</div>", unsafe_allow_html=True)

            # Action row: Download | Clear
            st.markdown("<div style='margin-top:0.9rem;'></div>", unsafe_allow_html=True)
            act1, act2, _ = st.columns([1, 1, 3])
            with act1:
                _download_btn(
                    title=st.session_state[_TITLE_KEY] or "AI_Summary",
                    summary=st.session_state[_SUMMARY_KEY],
                    key="dl_current",
                )
            with act2:
                if st.button("🗑 Clear", key="clear_summary"):
                    st.session_state[_SUMMARY_KEY] = ""
                    st.session_state[_TEXT_KEY] = ""
                    st.session_state[_TITLE_KEY] = ""
                    st.rerun()

    with history_tab:
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        saved = _load_saved_summaries()
        if not saved:
            st.markdown("""
            <div style="text-align:center;padding:3rem 1rem;color:#8A93A6;">
                No saved summaries yet. Summarize some notes and they'll appear here.
            </div>
            """, unsafe_allow_html=True)
        else:
            for note in saved:
                with st.expander(f"📄 {note['title']}  —  {note['created_at'][:16]}"):
                    st.markdown(note["summary"])
                    st.markdown("<div style='margin-top:0.6rem;'></div>", unsafe_allow_html=True)
                    dl_col, del_col, _ = st.columns([1, 1, 3])
                    with dl_col:
                        _download_btn(
                            title=note["title"],
                            summary=note["summary"],
                            key=f"dl_saved_{note['id']}",
                        )
                    with del_col:
                        if st.button("🗑 Delete", key=f"del_note_{note['id']}"):
                            _delete_summary(note["id"])
                            st.rerun()
