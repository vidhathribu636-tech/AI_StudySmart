"""
views/quiz.py — AI Quiz with per-question feedback, running score, and wrong-topic summary.
"""
import random
import streamlit as st
from ai.ai_service import generate_mcqs, is_ai_available
from database.database import get_connection
from views.theme import inject_theme, icon

_QUESTIONS_KEY  = "quiz_questions"
_ANSWERS_KEY    = "quiz_user_answers"
_SUBMITTED_KEY  = "quiz_submitted"
_TOPIC_KEY      = "quiz_topic"
_CURRENT_KEY    = "quiz_current_q"   # index of question being answered
_LIVE_SCORE_KEY = "quiz_live_score"  # running correct count
_SAVED_KEY      = "quiz_score_saved"


def _init_session():
    defaults = [
        (_QUESTIONS_KEY,  []),
        (_ANSWERS_KEY,    {}),
        (_SUBMITTED_KEY,  False),
        (_TOPIC_KEY,      ""),
        (_CURRENT_KEY,    0),
        (_LIVE_SCORE_KEY, 0),
        (_SAVED_KEY,      False),
    ]
    for key, default in defaults:
        if key not in st.session_state:
            st.session_state[key] = default


def _save_score(topic, score, max_score, questions, answers):
    try:
        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO quiz_attempts (topic, score, max_score) VALUES (?, ?, ?)",
                (topic, score, max_score),
            )
            attempt_id = cur.lastrowid
            for i, q in enumerate(questions):
                user_ans    = answers.get(f"q_{i}", "")
                correct_ans = q["answer"]
                is_correct  = 1 if str(user_ans).upper() == str(correct_ans).upper() else 0
                conn.execute(
                    "INSERT INTO quiz_scores (attempt_id, question, user_answer, correct_answer, is_correct) "
                    "VALUES (?,?,?,?,?)",
                    (attempt_id, q["question"], user_ans, correct_ans, is_correct),
                )
            existing = conn.execute(
                "SELECT id FROM topic_performance WHERE topic = ?", (topic,)
            ).fetchone()
            if existing:
                conn.execute(
                    """UPDATE topic_performance
                       SET total_score=total_score+?,total_max=total_max+?,
                           attempts=attempts+1,last_studied=datetime('now')
                       WHERE topic=?""",
                    (score, max_score, topic),
                )
            else:
                conn.execute(
                    "INSERT INTO topic_performance (topic,total_score,total_max,attempts) VALUES(?,?,?,1)",
                    (topic, score, max_score),
                )
    except Exception as e:
        st.error(f"⚠️ Could not save score: {e}")


def _reset_quiz():
    for key in [_QUESTIONS_KEY, _ANSWERS_KEY, _SUBMITTED_KEY,
                _TOPIC_KEY, _CURRENT_KEY, _LIVE_SCORE_KEY, _SAVED_KEY]:
        st.session_state.pop(key, None)


def show():
    inject_theme()
    _init_session()

    st.markdown("""
    <div class="page-header">
        <div class="badge">✦ AI Generated</div>
        <h2>AI Quiz</h2>
        <p>Generate custom multiple-choice quizzes on any topic to test your knowledge.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:linear-gradient(90deg,transparent,rgba(192,132,252,0.08),transparent);margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    if not is_ai_available():
        st.markdown(f"""
        <div class="info-box">
            <h4>{icon('key', 16, circle=False)} API Key Required</h4>
            <p>Add your <code>GEMINI_API_KEY</code> to the <code>.env</code> file to use AI Quiz.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    questions = st.session_state[_QUESTIONS_KEY]

    # ── Setup form ────────────────────────────────────────────────────────────
    if not questions:
        st.markdown("<span class='section-label'>Quiz Setup</span>", unsafe_allow_html=True)
        with st.form("quiz_gen_form"):
            st.markdown("""
            <div style="background:var(--bg-card);border:1px solid var(--border);
                        border-radius:14px;padding:1.5rem 1.8rem;margin-bottom:0.5rem;">
            """, unsafe_allow_html=True)
            col1, col2 = st.columns([3, 1])
            with col1:
                topic = st.text_input("Topic", placeholder="e.g. Operating Systems, Photosynthesis, Python OOP")
            with col2:
                num_q = st.number_input("Questions", min_value=3, max_value=15, value=5)
            notes = st.text_area(
                "Study notes (optional)",
                placeholder="Paste relevant notes — AI will use them to generate more specific questions…",
                height=90,
            )
            st.markdown("</div>", unsafe_allow_html=True)
            generate = st.form_submit_button("Generate Quiz", use_container_width=True)

        if generate:
            if not topic.strip():
                st.warning("⚠️ Please enter a topic before generating a quiz.")
                return
            if not (3 <= int(num_q) <= 15):
                st.warning("⚠️ Question count must be between 3 and 15.")
                return
            notes_input = notes.strip()[:15_000]
            with st.spinner(f"Generating {num_q} questions on **{topic}**…"):
                try:
                    qs = generate_mcqs(topic.strip(), notes_input, int(num_q))
                    if not qs:
                        st.error("AI returned no questions. Try rephrasing the topic.")
                        return
                    # Deduplicate by question text, then shuffle
                    seen, unique = set(), []
                    for q in qs:
                        if q["question"] not in seen:
                            seen.add(q["question"])
                            unique.append(q)
                    random.shuffle(unique)
                    st.session_state[_QUESTIONS_KEY]  = unique
                    st.session_state[_TOPIC_KEY]      = topic.strip()
                    st.session_state[_CURRENT_KEY]    = 0
                    st.session_state[_LIVE_SCORE_KEY] = 0
                    st.session_state[_ANSWERS_KEY]    = {}
                    st.session_state[_SUBMITTED_KEY]  = False
                    st.session_state[_SAVED_KEY]      = False
                    st.rerun()
                except RuntimeError as e:
                    st.error(f"AI error: {e}")
        return

    # ── Active quiz — one question at a time ──────────────────────────────────
    topic     = st.session_state[_TOPIC_KEY]
    total     = len(questions)
    current   = st.session_state[_CURRENT_KEY]
    answers   = st.session_state[_ANSWERS_KEY]
    submitted = st.session_state[_SUBMITTED_KEY]

    # Running score bar
    answered_count = len(answers)
    live_score     = st.session_state[_LIVE_SCORE_KEY]
    prog_pct       = int(answered_count / total * 100)

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
                background:var(--bg-card);border:1px solid var(--border);
                border-radius:12px;padding:0.85rem 1.2rem;margin-bottom:0.8rem;">
        <div style="display:flex;align-items:center;gap:0.7rem;">
            {icon('book-open', 18, circle=False)}
            <span style="font-size:0.9rem;font-weight:600;color:#E6EDF3;">{topic}</span>
        </div>
        <div style="display:flex;align-items:center;gap:1rem;">
            <span style="font-size:0.82rem;color:#8A93A6;">{answered_count}/{total} answered</span>
            <span style="font-size:0.9rem;font-weight:800;color:#C084FC;">Score: {live_score}/{answered_count if answered_count else '—'}</span>
        </div>
    </div>
    <div style="background:rgba(192,132,252,0.06);border-radius:4px;height:4px;margin-bottom:1.4rem;overflow:hidden;">
        <div style="background:linear-gradient(90deg,#C084FC,#E879F9);
                    width:{prog_pct}%;height:4px;border-radius:4px;
                    transition:width 0.5s ease;"></div>
    </div>
    """, unsafe_allow_html=True)

    # ── All questions submitted — show full review ────────────────────────────
    if submitted:
        score = sum(
            1 for i, q in enumerate(questions)
            if answers.get(f"q_{i}", "").upper() == q["answer"].upper()
        )
        pct   = round(score / total * 100)
        color = "#C084FC" if pct >= 70 else "#8A93A6" if pct >= 40 else "#4a5568"
        msg   = "Excellent work!" if pct >= 70 else "Keep practising!" if pct >= 40 else "Review the material and try again."

        st.markdown(f"""
        <div style="background:var(--bg-card);border:1px solid {color}44;border-radius:16px;
                    padding:2rem;text-align:center;margin-bottom:1.5rem;animation:fadeSlideUp 0.4s ease both;">
            <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.12em;
                         text-transform:uppercase;color:{color};opacity:0.7;margin-bottom:0.6rem;">Quiz Complete</div>
            <div style="font-size:3rem;font-weight:900;color:{color};line-height:1;margin-bottom:0.4rem;
                        font-family:'Sora',sans-serif;">{score}/{total}</div>
            <div style="font-size:1.2rem;font-weight:700;color:{color};margin-bottom:0.3rem;">{pct}%</div>
            <div style="font-size:0.875rem;color:#8A93A6;">{msg}</div>
        </div>
        """, unsafe_allow_html=True)

        # Wrong topics summary
        wrong = [q for i, q in enumerate(questions)
                 if answers.get(f"q_{i}", "").upper() != q["answer"].upper()]
        if wrong:
            st.markdown("<span class='section-label'>Questions to Review</span>", unsafe_allow_html=True)
            for q in wrong:
                correct_opt = next((o for o in q["options"] if o[0].upper() == q["answer"]), q["answer"])
                st.markdown(f"""
                <div style="background:var(--bg-card);border:1px solid rgba(192,132,252,0.2);
                            border-left:3px solid #C084FC;border-radius:10px;
                            padding:0.9rem 1.2rem;margin-bottom:0.6rem;">
                    <div style="font-size:0.875rem;font-weight:600;color:#E6EDF3;margin-bottom:0.3rem;">
                        {q['question']}
                    </div>
                    <div style="font-size:0.8rem;color:#C084FC;">✅ Correct answer: {correct_opt}</div>
                </div>
                """, unsafe_allow_html=True)

        # Save once
        if not st.session_state[_SAVED_KEY]:
            _save_score(topic, score, total, questions, answers)
            st.session_state[_SAVED_KEY] = True

        # Full question-by-question review
        st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<span class='section-label'>Full Review</span>", unsafe_allow_html=True)
        for i, q in enumerate(questions):
            chosen     = answers.get(f"q_{i}", "")
            is_correct = chosen.upper() == q["answer"].upper()
            border_col = "rgba(192,132,252,0.4)" if is_correct else "rgba(239,68,68,0.4)"
            icon_str   = "✅" if is_correct else "❌"
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid {border_col};
                        border-radius:12px;padding:1rem 1.3rem;margin-bottom:0.8rem;">
                <div style="font-size:0.75rem;color:#8A93A6;margin-bottom:0.3rem;">Q{i+1} {icon_str}</div>
                <div style="font-size:0.9rem;font-weight:600;color:#E6EDF3;margin-bottom:0.6rem;">{q['question']}</div>
            """, unsafe_allow_html=True)
            for opt in q["options"]:
                letter     = opt[0].upper()
                is_ans     = letter == q["answer"].upper()
                is_chosen  = letter == chosen.upper()
                if is_ans and is_chosen:
                    st.markdown(f"✅ **{opt}** — Your answer · Correct")
                elif is_ans:
                    st.markdown(f"✅ **{opt}** — Correct answer")
                elif is_chosen:
                    st.markdown(f"❌ {opt} — Your answer")
                else:
                    st.markdown(f"&nbsp;&nbsp;{opt}")
            st.markdown("</div>", unsafe_allow_html=True)

        if st.button("New Quiz", use_container_width=False):
            _reset_quiz()
            st.rerun()
        return

    # ── One question at a time ────────────────────────────────────────────────
    if current >= total:
        st.session_state[_SUBMITTED_KEY] = True
        st.rerun()

    q       = questions[current]
    opts    = q["options"]
    ans_key = f"q_{current}"

    # If already answered, show feedback then next
    if ans_key in answers:
        chosen     = answers[ans_key]
        is_correct = chosen.upper() == q["answer"].upper()
        correct_opt = next((o for o in opts if o[0].upper() == q["answer"]), q["answer"])

        st.markdown(f"""
        <div style="background:var(--bg-card);border:1px solid var(--border);
                    border-radius:12px;padding:1.1rem 1.3rem;margin-bottom:0.8rem;">
            <div style="font-size:0.78rem;font-weight:700;letter-spacing:0.1em;
                         text-transform:uppercase;color:#8A93A6;margin-bottom:0.5rem;">
                Question {current+1} of {total}
            </div>
            <div style="font-size:0.925rem;font-weight:600;color:#E6EDF3;line-height:1.5;">
                {q['question']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        for opt in opts:
            letter    = opt[0].upper()
            is_ans    = letter == q["answer"].upper()
            is_chosen = letter == chosen.upper()
            if is_ans and is_chosen:
                st.markdown(f"✅ **{opt}** — Correct!")
            elif is_ans:
                st.markdown(f"✅ **{opt}** — Correct answer")
            elif is_chosen:
                st.markdown(f"❌ {opt} — Your answer")
            else:
                st.markdown(f"&nbsp;&nbsp;{opt}")

        result_color = "#C084FC" if is_correct else "#EF4444"
        result_text  = "Correct! 🎉" if is_correct else f"Incorrect. The answer was: **{correct_opt}**"
        st.markdown(f"""
        <div style="background:{'rgba(192,132,252,0.08)' if is_correct else 'rgba(239,68,68,0.08)'};
                    border:1px solid {result_color}44;border-radius:10px;
                    padding:0.8rem 1.1rem;margin:0.8rem 0;">
            <span style="font-size:0.9rem;font-weight:600;color:{result_color};">{result_text}</span>
        </div>
        """, unsafe_allow_html=True)

        col_next, _ = st.columns([1, 3])
        with col_next:
            btn_label = "Next Question →" if current + 1 < total else "See Results"
            if st.button(btn_label, use_container_width=True, key="next_q"):
                st.session_state[_CURRENT_KEY] = current + 1
                if current + 1 >= total:
                    st.session_state[_SUBMITTED_KEY] = True
                st.rerun()
        return

    # Show unanswered question
    st.markdown(f"""
    <div style="background:var(--bg-card);border:1px solid var(--border);
                border-radius:12px;padding:1.1rem 1.3rem;margin-bottom:0.8rem;
                animation:fadeSlideUp 0.3s ease both;">
        <div style="font-size:0.78rem;font-weight:700;letter-spacing:0.1em;
                     text-transform:uppercase;color:#8A93A6;margin-bottom:0.5rem;">
            Question {current+1} of {total}
        </div>
        <div style="font-size:0.925rem;font-weight:600;color:#E6EDF3;line-height:1.5;">
            {q['question']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    chosen = st.radio(
        label=f"q{current+1}",
        options=[o[0].upper() for o in opts],
        format_func=lambda x, opts=opts: next((o for o in opts if o[0].upper() == x), x),
        key=f"radio_{current}",
        label_visibility="collapsed",
        index=None,          # no default selection — student must choose
    )

    if st.button("Submit Answer", use_container_width=False, key="submit_ans"):
        if not chosen:
            st.warning("⚠️ Please select an answer before submitting.")
        else:
            answers[ans_key] = chosen
            st.session_state[_ANSWERS_KEY] = answers
            if chosen.upper() == q["answer"].upper():
                st.session_state[_LIVE_SCORE_KEY] += 1
            st.rerun()
