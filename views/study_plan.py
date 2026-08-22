"""
views/study_plan.py — Personalized AI Study Plan
"""
import sqlite3
import datetime
import streamlit as st
from database.database import get_connection, DB_PATH
from ai.ai_service import generate_ai_response, is_ai_available
from views.theme import inject_theme, icon

_PLAN_KEY  = "study_plan_content"
_FORM_KEY  = "study_plan_form"


# ── Prompt ───────────────────────────────────────────────────────────────────

def _build_study_plan_prompt(
    subjects, exam_date, days_remaining, hours_per_day,
    session_length, level, difficult_topics, priority_topics,
    study_days, performance_summary,
) -> str:
    perf_section = (
        f"\n\nSTUDENT PERFORMANCE DATA (from quiz history):\n{performance_summary}"
        if performance_summary
        else "\n\nNo prior quiz performance data is available for this student."
    )
    return f"""You are an expert academic study planner.

Generate a detailed, realistic, day-by-day study plan for a student with the following profile:

SUBJECTS/TOPICS: {subjects}
EXAM DATE: {exam_date}
DAYS REMAINING: {days_remaining}
DAILY STUDY TIME: {hours_per_day} hours/day
PREFERRED SESSION LENGTH: {session_length} minutes per session
CURRENT LEVEL: {level}
DIFFICULT TOPICS: {difficult_topics or 'None specified'}
PRIORITY TOPICS: {priority_topics or 'None specified'}
PREFERRED STUDY DAYS: {study_days or 'All days'}{perf_section}

INSTRUCTIONS:
- Create a day-by-day plan covering all {days_remaining} days until the exam.
- If days_remaining > 14, group similar days and show a representative week pattern, then list each day for the final 7 days.
- Each day must show time-blocked sessions using the student's preferred session length.
- Include short breaks (10-15 min) between sessions.
- Include flashcard revision and practice quiz sessions.
- Reserve the last 2-3 days for full revision only.
- Prioritize weak/difficult topics in the first half of the plan.
- Do NOT ignore strong topics — include them for maintenance.
- Each session entry must include: time slot, subject, topic, activity type (Study/Quiz/Flashcards/Revision/Break), priority (High/Medium/Low), and a one-line objective.

OUTPUT FORMAT — use EXACTLY this structure:

## STUDY PLAN OVERVIEW
[One paragraph personalizing the plan based on the student's data]

## WHY THIS PLAN IS PERSONALIZED
[2-4 bullet points explaining specific personalization decisions based on performance data or stated preferences. If no performance data, base it on level and stated difficult topics.]

## DAY-BY-DAY SCHEDULE

### DAY 1 — [Date or Day Label]
| Time | Subject | Topic | Activity | Priority | Objective |
|------|---------|-------|----------|----------|-----------|
| HH:MM-HH:MM | Subject | Topic | Study/Quiz/Flashcards/Break/Revision | High/Medium/Low | One-line objective |

### DAY 2 — [Date or Day Label]
[same table format]

[Continue for all days...]

## FINAL REVISION DAYS
[Last 2-3 days focused on full revision — same table format]

Be realistic. Do not schedule more hours than the student has available. Keep objectives concise (under 10 words each)."""


# ── DB helpers ────────────────────────────────────────────────────────────────

def _ensure_table():
    """Create study_plans table if it doesn't exist (does not touch other tables)."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT    NOT NULL,
                created_at TEXT    DEFAULT (datetime('now')),
                plan_content TEXT  NOT NULL
            )
        """)


def _save_plan(title: str, content: str):
    _ensure_table()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO study_plans (title, plan_content) VALUES (?, ?)",
            (title, content),
        )


def _load_saved_plans():
    _ensure_table()
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, title, created_at FROM study_plans ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _delete_plan(plan_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM study_plans WHERE id = ?", (plan_id,))


def _load_plan_content(plan_id: int) -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT plan_content FROM study_plans WHERE id = ?", (plan_id,)
        ).fetchone()
    return row["plan_content"] if row else ""


# ── Performance data from existing DB ────────────────────────────────────────

def _get_performance_summary() -> str:
    """Pull real quiz/topic data from existing tables. Returns empty string if none."""
    try:
        with get_connection() as conn:
            topics = conn.execute(
                "SELECT topic, total_score, total_max, attempts "
                "FROM topic_performance ORDER BY attempts DESC"
            ).fetchall()
        if not topics:
            return ""
        lines = []
        for t in topics:
            pct = round(t["total_score"] / t["total_max"] * 100) if t["total_max"] else 0
            tag = "WEAK" if pct < 60 else ("AVERAGE" if pct < 80 else "STRONG")
            lines.append(
                f"- {t['topic']}: {pct}% ({t['total_score']}/{t['total_max']} pts, "
                f"{t['attempts']} attempt(s)) [{tag}]"
            )
        return "\n".join(lines)
    except Exception:
        return ""


def _get_weak_topics() -> list[str]:
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT topic, total_score, total_max FROM topic_performance"
            ).fetchall()
        return [
            r["topic"] for r in rows
            if r["total_max"] and (r["total_score"] / r["total_max"]) < 0.6
        ]
    except Exception:
        return []


# ── UI helpers ────────────────────────────────────────────────────────────────

def _stat_card(col, ico, val, lbl, delay="0s"):
    with col:
        st.markdown(f"""
        <div class="stat-card" style="animation-delay:{delay};">
            <span class="icon">{icon(ico, 20)}</span>
            <div class="val">{val}</div>
            <div class="lbl">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)


def _plan_card(content: str):
    st.markdown("""
    <div style="background:var(--bg-card);border:1px solid var(--border-accent);
                border-radius:16px;padding:1.8rem 2rem;margin-top:1rem;
                animation:fadeSlideUp 0.4s ease both;">
    """, unsafe_allow_html=True)
    st.markdown(content)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Main view ─────────────────────────────────────────────────────────────────

def show():
    inject_theme()
    _ensure_table()

    st.markdown("""
    <div class="page-header">
        <div class="badge">✦ AI Powered</div>
        <h2>Personalized Study Plan</h2>
        <p>Generate a day-by-day AI study plan tailored to your exam date, subjects, and performance.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        "<div style='height:1px;background:linear-gradient(90deg,transparent,"
        "rgba(192,132,252,0.08),transparent);margin-bottom:1.5rem;'></div>",
        unsafe_allow_html=True,
    )

    if not is_ai_available():
        st.markdown("""
        <div class="info-box" style="margin-top:1rem;">
            <h4>🔑 API Key Required</h4>
            <p>Add your <code>GEMINI_API_KEY</code> to <code>.env</code> to use this feature.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Pull existing performance data ────────────────────────────────────────
    perf_summary = _get_performance_summary()
    weak_topics  = _get_weak_topics()

    if perf_summary:
        st.markdown("""
        <div style="background:rgba(192,132,252,0.07);border:1px solid rgba(192,132,252,0.2);
                    border-radius:10px;padding:0.7rem 1.1rem;margin-bottom:1.2rem;
                    font-size:0.82rem;color:#C084FC;">
            Your existing quiz performance data has been detected and will be used to personalize your plan.
        </div>
        """, unsafe_allow_html=True)

    # ── Input form ────────────────────────────────────────────────────────────
    with st.expander("Study Plan Setup", expanded=st.session_state.get(_PLAN_KEY) is None):
        with st.form(_FORM_KEY):
            st.markdown("<span class='section-label'>Student Information</span>", unsafe_allow_html=True)

            subjects = st.text_input(
                "Subjects / Topics to study *",
                placeholder="e.g. DBMS, Computer Networks, Operating Systems",
            )

            col1, col2 = st.columns(2)
            with col1:
                exam_date = st.date_input(
                    "Exam Date *",
                    min_value=datetime.date.today() + datetime.timedelta(days=1),
                    value=datetime.date.today() + datetime.timedelta(days=14),
                )
            with col2:
                level = st.selectbox(
                    "Current Level *",
                    ["Beginner", "Intermediate", "Advanced"],
                    index=1,
                )

            col3, col4 = st.columns(2)
            with col3:
                hours_per_day = st.slider(
                    "Available study hours per day", 1.0, 10.0, 2.0, 0.5
                )
            with col4:
                session_length = st.selectbox(
                    "Preferred session length (minutes)",
                    [25, 30, 45, 60, 90],
                    index=2,
                )

            st.markdown(
                "<span class='section-label' style='margin-top:0.8rem;display:block;'>"
                "Optional Information</span>",
                unsafe_allow_html=True,
            )

            # Pre-fill difficult topics from weak quiz topics if available
            weak_default = ", ".join(weak_topics) if weak_topics else ""
            difficult_topics = st.text_input(
                "Topics you find difficult",
                value=weak_default,
                placeholder="e.g. Normalization, Subnetting",
                help="Pre-filled from your quiz history where available.",
            )
            priority_topics = st.text_input(
                "Topics to prioritize",
                placeholder="e.g. SQL Queries, OSI Model",
            )

            all_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            study_days = st.multiselect(
                "Preferred study days (leave blank for all days)",
                all_days,
            )

            submitted = st.form_submit_button("Generate Study Plan", use_container_width=True)

    # ── Generate ──────────────────────────────────────────────────────────────
    if submitted:
        if not subjects.strip():
            st.error("Please enter at least one subject or topic.")
            return

        days_remaining = (exam_date - datetime.date.today()).days
        if days_remaining < 1:
            st.error("Exam date must be in the future.")
            return

        study_days_str = ", ".join(study_days) if study_days else "All days"

        prompt = _build_study_plan_prompt(
            subjects        = subjects.strip(),
            exam_date       = exam_date.strftime("%d %B %Y"),
            days_remaining  = days_remaining,
            hours_per_day   = hours_per_day,
            session_length  = session_length,
            level           = level,
            difficult_topics= difficult_topics.strip(),
            priority_topics = priority_topics.strip(),
            study_days      = study_days_str,
            performance_summary = perf_summary,
        )

        with st.spinner("AI is building your personalized study plan…"):
            try:
                plan = generate_ai_response(user_prompt=prompt, system_instruction=" ")
                st.session_state[_PLAN_KEY] = {
                    "content":       plan,
                    "subjects":      subjects.strip(),
                    "exam_date":     exam_date.strftime("%d %B %Y"),
                    "days_remaining": days_remaining,
                    "hours_per_day": hours_per_day,
                    "num_subjects":  len([s.strip() for s in subjects.split(",") if s.strip()]),
                }
            except RuntimeError as e:
                st.error(f"AI error: {e}")
                return

    # ── Display plan ──────────────────────────────────────────────────────────
    plan_data = st.session_state.get(_PLAN_KEY)
    if not plan_data:
        return

    content = plan_data["content"]

    # Overview stat cards
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("<span class='section-label'>Study Plan Overview</span>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap="small")
    _stat_card(c1, "calendar",    plan_data["exam_date"],          "Exam Date",         "0.05s")
    _stat_card(c2, "clock",       f"{plan_data['days_remaining']}d", "Days Remaining",  "0.10s")
    _stat_card(c3, "book-open",   f"{plan_data['hours_per_day']}h", "Daily Study Time", "0.15s")
    _stat_card(c4, "layers",      str(plan_data["num_subjects"]),  "Subjects",          "0.20s")

    # Plan content
    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("<span class='section-label'>Your Personalized Plan</span>", unsafe_allow_html=True)
    _plan_card(content)

    # ── Actions ───────────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)
    a1, a2, a3, a4 = st.columns([2, 2, 2, 2], gap="small")

    with a1:
        if st.button("Regenerate Plan", use_container_width=True):
            st.session_state.pop(_PLAN_KEY, None)
            st.rerun()

    with a2:
        if st.button("Clear Plan", use_container_width=True):
            st.session_state.pop(_PLAN_KEY, None)
            st.rerun()

    with a3:
        title = f"Study Plan — {plan_data['subjects'][:30]} ({plan_data['exam_date']})"
        if st.button("Save Plan", use_container_width=True):
            try:
                _save_plan(title, content)
                st.success("Plan saved!")
            except Exception as e:
                st.error(f"Could not save: {e}")

    with a4:
        st.download_button(
            label="Download (.txt)",
            data=content.encode("utf-8"),
            file_name=f"study_plan_{datetime.date.today()}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # ── Saved plans ───────────────────────────────────────────────────────────
    saved = _load_saved_plans()
    if saved:
        st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
        st.markdown("<span class='section-label'>Saved Plans</span>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:14px;overflow:hidden;">
        """, unsafe_allow_html=True)
        for i, p in enumerate(saved):
            border_b = "1px solid rgba(192,132,252,0.06)" if i < len(saved) - 1 else "none"
            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
                        padding:0.75rem 1.2rem;border-bottom:{border_b};">
                <div>
                    <span style="font-size:0.875rem;color:#E6EDF3;font-weight:500;">{p['title']}</span>
                    <span style="font-size:0.75rem;color:#8A93A6;margin-left:0.8rem;">{p['created_at'][:16]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            sc1, sc2 = st.columns([1, 1])
            with sc1:
                if st.button("View", key=f"view_{p['id']}", use_container_width=True):
                    loaded = _load_plan_content(p["id"])
                    st.session_state[_PLAN_KEY] = {
                        "content":        loaded,
                        "subjects":       p["title"],
                        "exam_date":      "",
                        "days_remaining": 0,
                        "hours_per_day":  0,
                        "num_subjects":   0,
                    }
                    st.rerun()
            with sc2:
                if st.button("Delete", key=f"del_{p['id']}", use_container_width=True):
                    _delete_plan(p["id"])
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
