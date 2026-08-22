"""
views/dashboard.py — AI StudySmart premium dashboard.
"""
import time
import streamlit as st
from database.database import get_connection
from views.theme import inject_theme, icon


def _get_stats() -> dict:
    s = {"quizzes": 0, "topics": 0, "avg_score": 0, "streak": 0}
    try:
        with get_connection() as conn:
            r = conn.execute("SELECT COUNT(*) AS c FROM quiz_attempts").fetchone()
            s["quizzes"] = r["c"] if r else 0
            r2 = conn.execute("SELECT COUNT(*) AS c FROM topic_performance").fetchone()
            s["topics"] = r2["c"] if r2 else 0
            r3 = conn.execute(
                "SELECT ROUND(AVG(CAST(score AS FLOAT)/max_score*100)) AS a FROM quiz_attempts WHERE max_score>0"
            ).fetchone()
            s["avg_score"] = int(r3["a"]) if r3 and r3["a"] else 0
            # Streak: count consecutive distinct days with activity, most recent first
            rows = conn.execute(
                "SELECT DISTINCT date(attempted_at) AS d FROM quiz_attempts ORDER BY d DESC"
            ).fetchall()
            if rows:
                import datetime
                streak = 1
                today  = datetime.date.today()
                first  = datetime.date.fromisoformat(rows[0]["d"])
                # streak only counts if activity was today or yesterday
                if (today - first).days > 1:
                    streak = 0
                else:
                    for i in range(1, len(rows)):
                        prev = datetime.date.fromisoformat(rows[i-1]["d"])
                        curr = datetime.date.fromisoformat(rows[i]["d"])
                        if (prev - curr).days == 1:
                            streak += 1
                        else:
                            break
                s["streak"] = streak
    except Exception:
        pass
    return s


def _pomodoro():
    st.markdown("<span class='section-label'>Pomodoro Study Timer</span>", unsafe_allow_html=True)

    if "pomo_running"    not in st.session_state: st.session_state.pomo_running    = False
    if "pomo_end_time"   not in st.session_state: st.session_state.pomo_end_time   = None
    if "pomo_mode"       not in st.session_state: st.session_state.pomo_mode       = "Study"
    if "pomo_sessions"   not in st.session_state: st.session_state.pomo_sessions   = 0

    DURATIONS = {"Study": 25 * 60, "Short Break": 5 * 60, "Long Break": 15 * 60}

    col_mode, col_ctrl, col_stat = st.columns([2, 2, 1])
    with col_mode:
        mode = st.selectbox("Mode", list(DURATIONS.keys()), key="pomo_mode_sel",
                            index=list(DURATIONS.keys()).index(st.session_state.pomo_mode),
                            label_visibility="collapsed")
    with col_ctrl:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶ Start" if not st.session_state.pomo_running else "⏸ Pause",
                         use_container_width=True, key="pomo_toggle"):
                if not st.session_state.pomo_running:
                    st.session_state.pomo_mode     = mode
                    st.session_state.pomo_end_time = time.time() + DURATIONS[mode]
                    st.session_state.pomo_running  = True
                else:
                    st.session_state.pomo_running  = False
                    st.session_state.pomo_end_time = None
                st.rerun()
        with c2:
            if st.button("↺ Reset", use_container_width=True, key="pomo_reset"):
                st.session_state.pomo_running  = False
                st.session_state.pomo_end_time = None
                st.rerun()
    with col_stat:
        st.markdown(f"""
        <div style="text-align:center;padding:0.3rem 0;">
            <span style="font-size:0.7rem;color:#8A93A6;text-transform:uppercase;letter-spacing:0.1em;">Sessions</span><br>
            <span style="font-size:1.4rem;font-weight:800;color:#C084FC;">{st.session_state.pomo_sessions}</span>
        </div>
        """, unsafe_allow_html=True)

    # Timer display
    if st.session_state.pomo_running and st.session_state.pomo_end_time:
        remaining = max(0, int(st.session_state.pomo_end_time - time.time()))
        if remaining == 0:
            st.session_state.pomo_running = False
            if st.session_state.pomo_mode == "Study":
                st.session_state.pomo_sessions += 1
            st.success(f"✅ {st.session_state.pomo_mode} session complete!")
            st.rerun()
        mins, secs = divmod(remaining, 60)
        label_color = "#C084FC" if st.session_state.pomo_mode == "Study" else "#34D399"
        st.markdown(f"""
        <div style="background:var(--bg-card);border:1px solid var(--border-accent);
                    border-radius:14px;padding:1.2rem;text-align:center;margin-top:0.6rem;">
            <div style="font-size:0.7rem;font-weight:700;letter-spacing:0.12em;
                        text-transform:uppercase;color:{label_color};margin-bottom:0.4rem;">
                {st.session_state.pomo_mode}
            </div>
            <div style="font-size:2.8rem;font-weight:900;color:#E6EDF3;
                        font-family:'Sora',sans-serif;letter-spacing:-0.02em;">
                {mins:02d}:{secs:02d}
            </div>
        </div>
        """, unsafe_allow_html=True)
        time.sleep(1)
        st.rerun()
    else:
        total = DURATIONS[st.session_state.pomo_mode]
        mins, secs = divmod(total, 60)
        st.markdown(f"""
        <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:14px;padding:1.2rem;text-align:center;margin-top:0.6rem;">
            <div style="font-size:0.7rem;font-weight:700;letter-spacing:0.12em;
                        text-transform:uppercase;color:#4a5568;margin-bottom:0.4rem;">
                {st.session_state.pomo_mode}
            </div>
            <div style="font-size:2.8rem;font-weight:900;color:#4a5568;
                        font-family:'Sora',sans-serif;letter-spacing:-0.02em;">
                {mins:02d}:{secs:02d}
            </div>
        </div>
        """, unsafe_allow_html=True)


def show():
    inject_theme()
    stats = _get_stats()

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="position:relative;overflow:hidden;border-radius:20px;
                background:linear-gradient(135deg,#0d0a18 0%,#100D1A 50%,#160f28 100%);
                border:1px solid rgba(192,132,252,0.12);
                padding:3rem 2.5rem 2.8rem;margin-bottom:2rem;
                animation:fadeSlideUp 0.5s ease both;">
        <div style="position:absolute;top:-60px;right:-60px;width:280px;height:280px;
                    background:radial-gradient(circle,rgba(192,132,252,0.07) 0%,transparent 70%);
                    border-radius:50%;animation:bgMove 12s ease-in-out infinite;"></div>
        <div style="position:absolute;bottom:-40px;left:20%;width:200px;height:200px;
                    background:radial-gradient(circle,rgba(192,132,252,0.04) 0%,transparent 70%);
                    border-radius:50%;animation:bgMove 16s ease-in-out infinite reverse;"></div>
        <div style="display:inline-flex;align-items:center;gap:0.4rem;
                    background:rgba(192,132,252,0.1);border:1px solid rgba(192,132,252,0.22);
                    border-radius:20px;padding:0.25rem 0.85rem;margin-bottom:1.1rem;">
            <span style="width:6px;height:6px;background:#C084FC;border-radius:50%;
                         display:inline-block;box-shadow:0 0 6px #C084FC;"></span>
            <span style="font-size:0.7rem;font-weight:700;color:#C084FC;
                         letter-spacing:0.1em;text-transform:uppercase;">AI-Powered Learning Platform</span>
        </div>
        <h1 style="font-size:2.4rem;font-weight:900;color:#E6EDF3;margin:0 0 0.5rem 0;
                   letter-spacing:-0.04em;line-height:1.15;font-family:'Sora',sans-serif;">
            Welcome to
            <span style="background:linear-gradient(135deg,#C084FC,#E879F9,#A855F7);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                         background-clip:text;">AI StudySmart</span>
        </h1>
        <p style="font-size:1.05rem;color:#C084FC;font-weight:600;margin:0 0 0.5rem 0;
                  font-family:'Sora',sans-serif;letter-spacing:0.01em;">
            Your Intelligent AI Learning Companion
        </p>
        <p style="font-size:0.95rem;color:#8A93A6;max-width:520px;line-height:1.7;margin:0 0 1.8rem 0;">
            Ask AI questions, summarize notes, generate quizzes, and track your
            academic progress — all in one place.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick actions ─────────────────────────────────────────────────────────
    qa1, qa2, qa3, _sp = st.columns([1, 1, 1, 2])
    with qa1:
        if st.button("💬 Ask AI", use_container_width=True):
            st.rerun()
    with qa2:
        if st.button("📄 Upload Notes", use_container_width=True):
            st.rerun()
    with qa3:
        if st.button("🧠 Take a Quiz", use_container_width=True):
            st.rerun()

    st.markdown("<div style='margin:1.8rem 0 0.3rem;height:1px;background:linear-gradient(90deg,transparent,rgba(192,132,252,0.08),transparent);'></div>", unsafe_allow_html=True)

    # ── Stats ─────────────────────────────────────────────────────────────────
    st.markdown("<span class='section-label' style='animation:fadeIn 0.4s ease both;'>Overview</span>", unsafe_allow_html=True)
    sc1, sc2, sc3, sc4 = st.columns(4, gap="small")
    stats_data = [
        (sc1, "book-open",  str(stats["quizzes"]) if stats["quizzes"] else "0",     "Study Sessions", "0.05s"),
        (sc2, "target",     f"{stats['avg_score']}%" if stats["avg_score"] else "—", "Average Score",  "0.10s"),
        (sc3, "flame",      str(stats["streak"]),                                    "Day Streak",     "0.15s"),
        (sc4, "layers",     str(stats["topics"]) if stats["topics"] else "0",         "Topics Studied", "0.20s"),
    ]
    for col, ico, val, lbl, delay in stats_data:
        with col:
            st.markdown(f"""
            <div class="stat-card" style="animation-delay:{delay};">
                <span class="icon">{icon(ico, 20)}</span>
                <div class="val">{val}</div>
                <div class="lbl">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin:2rem 0 0.3rem;'></div>", unsafe_allow_html=True)

    # ── Pomodoro Timer ────────────────────────────────────────────────────────
    with st.container():
        st.markdown("""
        <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:16px;padding:1.4rem 1.6rem;margin-bottom:1.5rem;">
        """, unsafe_allow_html=True)
        _pomodoro()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin:0.5rem 0 0.3rem;height:1px;background:linear-gradient(90deg,transparent,rgba(192,132,252,0.08),transparent);'></div>", unsafe_allow_html=True)

    # ── Feature cards ─────────────────────────────────────────────────────────
    st.markdown("<span class='section-label'>Features</span>", unsafe_allow_html=True)
    fc = [
        ("bot",         "AI Study Assistant", "Ask any question — concepts, definitions, explanations. Your AI tutor is available 24/7."),
        ("file-text",   "Smart Notes",        "Upload PDFs or paste text. AI extracts the key points so you study the essentials, not the filler."),
        ("help-circle", "AI Quiz",            "Generate custom multiple-choice quizzes on any topic with instant feedback on every answer."),
        ("copy",        "Flashcards",         "Auto-generate term-definition flashcard decks from your notes. Track what you know."),
        ("bar-chart",   "My Progress",        "Analytics on quiz scores and topic performance. AI recommendations on weak areas."),
        ("settings",    "More Coming Soon",   "Study schedules, mind maps, collaborative notes, and more AI tools are on the roadmap."),
    ]
    row1 = st.columns(3, gap="medium")
    row2 = st.columns(3, gap="medium")
    for i, (ico, title, desc) in enumerate(fc):
        col = (row1 + row2)[i]
        delay = f"{0.05 * i:.2f}s"
        with col:
            st.markdown(f"""
            <div class="glass-card" style="margin-bottom:1rem;animation:fadeSlideUp 0.5s {delay} ease both;">
                <div style="display:flex;align-items:center;gap:0.7rem;margin-bottom:0.7rem;">
                    {icon(ico, 20)}
                    <span style="font-size:0.95rem;font-weight:700;color:#E6EDF3;font-family:'Sora',sans-serif;">{title}</span>
                </div>
                <p style="font-size:0.84rem;color:#8A93A6;line-height:1.65;margin:0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin:1.5rem 0 0.3rem;height:1px;background:linear-gradient(90deg,transparent,rgba(192,132,252,0.08),transparent);'></div>", unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────────────────────
    st.markdown("<span class='section-label'>How It Works</span>", unsafe_allow_html=True)
    steps = [
        ("01", "Upload",    "Add your PDFs, notes, or textbook chapters to the platform."),
        ("02", "Understand","AI reads and extracts the key knowledge from your material."),
        ("03", "Practice",  "Generate quizzes and flashcards to reinforce your learning."),
        ("04", "Improve",   "Track progress and get AI guidance on where to focus next."),
    ]
    sc = st.columns(4, gap="small")
    for i, (num, step, desc) in enumerate(steps):
        with sc[i]:
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:14px;padding:1.3rem 1.2rem;text-align:center;
                        transition:var(--transition);animation:fadeSlideUp 0.5s {0.05*i:.2f}s ease both;">
                <div style="font-size:1.4rem;font-weight:900;
                             background:linear-gradient(135deg,#C084FC,#E879F9);
                             -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                             background-clip:text;margin-bottom:0.6rem;
                             font-family:'Sora',sans-serif;">{num}</div>
                <div style="font-size:0.9rem;font-weight:700;color:#E6EDF3;margin-bottom:0.4rem;
                            font-family:'Sora',sans-serif;">{step}</div>
                <div style="font-size:0.8rem;color:#8A93A6;line-height:1.6;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
