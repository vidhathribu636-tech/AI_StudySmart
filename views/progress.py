"""
views/progress.py — Modern analytics dashboard with score-over-time chart.
"""
import streamlit as st
import pandas as pd
from database.database import get_connection
from ai.ai_service import analyze_weak_topics, is_ai_available
from views.theme import inject_theme, icon


def _load_topic_performance():
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT topic,total_score,total_max,attempts,last_studied "
                "FROM topic_performance ORDER BY last_studied DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        st.warning(f"⚠️ Could not load topic data: {e}")
        return []


def _load_recent_attempts(limit=30):
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT topic,score,max_score,attempted_at FROM quiz_attempts "
                "ORDER BY attempted_at ASC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        st.warning(f"⚠️ Could not load quiz history: {e}")
        return []


def show():
    inject_theme()

    st.markdown("""
    <div class="page-header">
        <div class="badge">✦ Learning Analytics</div>
        <h2>My Progress</h2>
        <p>Track your quiz scores, topic performance, and get AI-powered study recommendations.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:linear-gradient(90deg,transparent,rgba(192,132,252,0.08),transparent);margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    topic_perf = _load_topic_performance()
    recent     = _load_recent_attempts()

    # ── Empty state ───────────────────────────────────────────────────────────
    if not topic_perf:
        st.markdown(f"""
        <div style="text-align:center;padding:4rem 1rem;animation:fadeSlideUp 0.5s ease both;">
            <div style="display:flex;justify-content:center;margin-bottom:1.2rem;">
                {icon('bar-chart', 36)}
            </div>
            <div style="font-size:1rem;font-weight:700;color:#E6EDF3;margin-bottom:0.5rem;
                        font-family:'Sora',sans-serif;">No Data Yet</div>
            <div style="font-size:0.875rem;color:#8A93A6;max-width:340px;margin:0 auto;line-height:1.65;">
                Complete a quiz on the
                <strong style="color:#C084FC;">AI Quiz</strong> page and
                your results will appear here automatically.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Summary stats ─────────────────────────────────────────────────────────
    total_attempts = sum(r["attempts"] for r in topic_perf)
    overall_pct = (
        round(sum(r["total_score"] for r in topic_perf)
              / sum(r["total_max"]   for r in topic_perf) * 100)
        if topic_perf else 0
    )
    best_topic = max(topic_perf, key=lambda r: r["total_score"] / r["total_max"] if r["total_max"] else 0)
    best_pct   = round(best_topic["total_score"] / best_topic["total_max"] * 100) if best_topic["total_max"] else 0

    sc1, sc2, sc3, sc4 = st.columns(4, gap="small")
    for col, ico, val, lbl, delay in [
        (sc1, "layers",      str(len(topic_perf)),  "Topics Studied", "0.05s"),
        (sc2, "target",      str(total_attempts),   "Total Quizzes",  "0.10s"),
        (sc3, "trending-up", f"{overall_pct}%",     "Overall Score",  "0.15s"),
        (sc4, "trophy",      f"{best_pct}%",        "Best Topic",     "0.20s"),
    ]:
        with col:
            st.markdown(f"""
            <div class="stat-card" style="animation-delay:{delay};">
                <span class="icon">{icon(ico, 20)}</span>
                <div class="val">{val}</div>
                <div class="lbl">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin:2rem 0 0.4rem;'></div>", unsafe_allow_html=True)

    # ── Score over time chart ─────────────────────────────────────────────────
    if recent:
        st.markdown("<span class='section-label'>Score Over Time</span>", unsafe_allow_html=True)
        try:
            chart_data = pd.DataFrame([
                {
                    "Quiz": f"{r['topic']} ({r['attempted_at'][:10]})",
                    "Score %": round(r["score"] / r["max_score"] * 100) if r["max_score"] else 0,
                }
                for r in recent
            ])
            st.line_chart(chart_data.set_index("Quiz")["Score %"], use_container_width=True, height=200)
        except Exception:
            pass

    st.markdown("<div style='margin:1rem 0 0.4rem;'></div>", unsafe_allow_html=True)

    # ── Topic performance with search + sort ──────────────────────────────────
    st.markdown("<span class='section-label'>Topic Performance</span>", unsafe_allow_html=True)

    filter_col, sort_col = st.columns([3, 1])
    with filter_col:
        search = st.text_input("Search topics", placeholder="Filter by topic name…", label_visibility="collapsed")
    with sort_col:
        sort_by = st.selectbox("Sort", ["Latest", "Highest Score", "Lowest Score", "Most Attempts"],
                               label_visibility="collapsed")

    filtered = [r for r in topic_perf if search.lower() in r["topic"].lower()] if search else list(topic_perf)

    if sort_by == "Highest Score":
        filtered = sorted(filtered, key=lambda r: r["total_score"] / r["total_max"] if r["total_max"] else 0, reverse=True)
    elif sort_by == "Lowest Score":
        filtered = sorted(filtered, key=lambda r: r["total_score"] / r["total_max"] if r["total_max"] else 0)
    elif sort_by == "Most Attempts":
        filtered = sorted(filtered, key=lambda r: r["attempts"], reverse=True)

    if not filtered:
        st.markdown("<p style='color:#8A93A6;font-size:0.875rem;'>No topics match your search.</p>", unsafe_allow_html=True)
    else:
        for i, row in enumerate(filtered):
            pct     = round(row["total_score"] / row["total_max"] * 100) if row["total_max"] else 0
            bar_col = "#C084FC" if pct >= 70 else "#8A93A6" if pct >= 40 else "#4a5568"
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;
                        padding:0.9rem 1.2rem;margin-bottom:0.6rem;
                        animation:fadeSlideUp 0.4s {0.04*i:.2f}s ease both;transition:var(--transition);">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
                    <span style="font-size:0.9rem;font-weight:600;color:#E6EDF3;">{row['topic']}</span>
                    <span style="font-size:0.88rem;font-weight:800;color:{bar_col};">{pct}%</span>
                </div>
                <div style="background:rgba(192,132,252,0.06);border-radius:4px;height:5px;overflow:hidden;">
                    <div style="background:{bar_col};width:{pct}%;height:5px;border-radius:4px;
                                 transition:width 0.8s cubic-bezier(0.4,0,0.2,1);"></div>
                </div>
                <div style="font-size:0.75rem;color:#8A93A6;margin-top:0.4rem;">
                    {row['total_score']}/{row['total_max']} pts &nbsp;·&nbsp; {row['attempts']} attempt(s)
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Recent quizzes list ───────────────────────────────────────────────────
    recent_display = list(reversed(recent))[:8]
    if recent_display:
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<span class='section-label'>Recent Quizzes</span>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:14px;overflow:hidden;">
        """, unsafe_allow_html=True)
        for i, a in enumerate(recent_display):
            pct      = round(a["score"] / a["max_score"] * 100) if a["max_score"] else 0
            color    = "#C084FC" if pct >= 70 else "#8A93A6" if pct >= 40 else "#4a5568"
            date     = a["attempted_at"][:16] if a["attempted_at"] else ""
            border_b = "1px solid rgba(192,132,252,0.06)" if i < len(recent_display) - 1 else "none"
            st.markdown(f"""
            <div style="display:flex;align-items:center;justify-content:space-between;
                        padding:0.75rem 1.2rem;border-bottom:{border_b};">
                <span style="font-size:0.875rem;color:#E6EDF3;font-weight:500;">{a['topic']}</span>
                <div style="display:flex;align-items:center;gap:1.2rem;">
                    <span style="font-size:0.875rem;font-weight:700;color:{color};">
                        {a['score']}/{a['max_score']} ({pct}%)
                    </span>
                    <span style="font-size:0.78rem;color:#8A93A6;">{date}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── AI Recommendations ────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
    st.markdown("<span class='section-label'>AI Study Recommendations</span>", unsafe_allow_html=True)

    if not is_ai_available():
        st.markdown(f"""
        <div class="info-box">
            <h4>{icon('key', 16, circle=False)} API Key Required</h4>
            <p>Add your <code>GEMINI_API_KEY</code> to get personalized AI study recommendations.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    if st.button("Analyze My Weak Topics"):
        with st.spinner("AI is analyzing your performance…"):
            try:
                analysis = analyze_weak_topics(topic_perf)
                st.session_state["progress_analysis"] = analysis
            except RuntimeError as e:
                st.error(f"AI error: {e}")

    if st.session_state.get("progress_analysis"):
        st.markdown("""
        <div style="background:var(--bg-card);
                    border:1px solid var(--border-accent);border-radius:16px;
                    padding:1.5rem 1.7rem;font-size:0.9rem;color:#E6EDF3;
                    line-height:1.85;margin-top:0.8rem;animation:fadeSlideUp 0.4s ease both;">
        """, unsafe_allow_html=True)
        st.markdown(st.session_state["progress_analysis"])
        st.markdown("</div>", unsafe_allow_html=True)
