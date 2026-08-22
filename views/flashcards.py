"""
views/flashcards.py — Flashcard UI with shuffle, Still Learning / Know It mastery tracking.
"""
import json
import random
import streamlit as st
from ai.ai_service import generate_flashcards, is_ai_available
from database.database import get_connection
from views.theme import inject_theme, icon

_CARDS_KEY        = "flashcard_deck"
_ORDER_KEY        = "flashcard_order"      # shuffled list of indices
_INDEX_KEY        = "flashcard_index"      # position in _ORDER_KEY
_FLIPPED_KEY      = "flashcard_flipped"
_KNOWN_KEY        = "flashcard_known"      # set of card indices marked Know It
_LEARNING_KEY     = "flashcard_learning"   # set of card indices marked Still Learning
_TOPIC_KEY        = "flashcard_topic"


def _init_session():
    for key, default in [
        (_CARDS_KEY,    []),
        (_ORDER_KEY,    []),
        (_INDEX_KEY,    0),
        (_FLIPPED_KEY,  False),
        (_KNOWN_KEY,    set()),
        (_LEARNING_KEY, set()),
        (_TOPIC_KEY,    ""),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default


def _reset_deck():
    for key in [_CARDS_KEY, _ORDER_KEY, _INDEX_KEY,
                _FLIPPED_KEY, _KNOWN_KEY, _LEARNING_KEY, _TOPIC_KEY]:
        st.session_state.pop(key, None)


def _save_deck(topic: str, cards: list):
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO saved_decks (topic, cards_json) VALUES (?, ?)",
                (topic or "Untitled Deck", json.dumps(cards)),
            )
    except Exception as e:
        st.warning(f"⚠️ Could not save deck: {e}")


def _load_saved_decks():
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, topic, cards_json, created_at FROM saved_decks ORDER BY created_at DESC LIMIT 20"
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        st.warning(f"⚠️ Could not load saved decks: {e}")
        return []


def _delete_deck(deck_id: int):
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM saved_decks WHERE id = ?", (deck_id,))
    except Exception as e:
        st.warning(f"⚠️ Could not delete deck: {e}")


def show():
    inject_theme()
    _init_session()

    st.markdown("""
    <div class="page-header">
        <div class="badge">✦ Spaced Repetition</div>
        <h2>Flashcards</h2>
        <p>Generate AI-powered flashcard decks from your study material for rapid revision.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:1px;background:linear-gradient(90deg,transparent,rgba(192,132,252,0.08),transparent);margin-bottom:1.5rem;'></div>", unsafe_allow_html=True)

    if not is_ai_available():
        st.markdown(f"""
        <div class="info-box">
            <h4>{icon('key', 16, circle=False)} API Key Required</h4>
            <p>Add your <code>GEMINI_API_KEY</code> to the <code>.env</code> file to use Flashcards.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    cards: list[dict] = st.session_state[_CARDS_KEY]

    # ── No active deck — show create / saved tabs ─────────────────────────────
    if not cards:
        gen_tab, saved_tab = st.tabs(["✦ Create Deck", "📂 Saved Decks"])

        with gen_tab:
            st.markdown("<span class='section-label'>Create a Deck</span>", unsafe_allow_html=True)
            with st.form("fc_gen_form"):
                st.markdown("""
                <div style="background:var(--bg-card);border:1px solid var(--border);
                            border-radius:14px;padding:1.5rem 1.8rem;margin-bottom:0.5rem;">
                """, unsafe_allow_html=True)
                deck_topic = st.text_input("Deck topic / title", placeholder="e.g. Python OOP, Cell Biology…")
                notes = st.text_area(
                    "Study notes",
                    placeholder="Paste your study notes or lecture material here to generate flashcards…",
                    height=190,
                    label_visibility="collapsed",
                )
                num_cards = st.slider("Number of flashcards", min_value=5, max_value=20, value=10)
                st.markdown("</div>", unsafe_allow_html=True)
                generate = st.form_submit_button("Generate Flashcards", use_container_width=True)

            if generate:
                if not notes.strip():
                    st.warning("⚠️ Please paste some study notes first.")
                    return
                notes_input = notes.strip()[:15_000]
                with st.spinner(f"Generating {num_cards} flashcards…"):
                    try:
                        deck = generate_flashcards(notes_input, num_cards)
                        if not deck:
                            st.error("AI returned no flashcards. Try adding more detailed notes.")
                            return
                        topic  = deck_topic.strip() or "Untitled Deck"
                        order  = list(range(len(deck)))
                        random.shuffle(order)
                        st.session_state[_CARDS_KEY]    = deck
                        st.session_state[_ORDER_KEY]    = order
                        st.session_state[_INDEX_KEY]    = 0
                        st.session_state[_FLIPPED_KEY]  = False
                        st.session_state[_KNOWN_KEY]    = set()
                        st.session_state[_LEARNING_KEY] = set()
                        st.session_state[_TOPIC_KEY]    = topic
                        _save_deck(topic, deck)
                        st.rerun()
                    except RuntimeError as e:
                        st.error(f"AI error: {e}")

        with saved_tab:
            st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
            decks = _load_saved_decks()
            if not decks:
                st.markdown("""
                <div style="text-align:center;padding:3rem 1rem;">
                    <div style="font-size:1rem;font-weight:700;color:#E6EDF3;margin-bottom:0.5rem;">No Saved Decks Yet</div>
                    <div style="font-size:0.875rem;color:#8A93A6;">Generate a deck and it will be saved automatically.</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for deck in decks:
                    deck_cards = json.loads(deck["cards_json"])
                    with st.expander(f"🃏 {deck['topic']}  —  {deck['created_at'][:16]}  ({len(deck_cards)} cards)"):
                        col_load, col_del = st.columns([2, 1])
                        with col_load:
                            if st.button("▶ Study this deck", key=f"load_deck_{deck['id']}", use_container_width=True):
                                order = list(range(len(deck_cards)))
                                random.shuffle(order)
                                st.session_state[_CARDS_KEY]    = deck_cards
                                st.session_state[_ORDER_KEY]    = order
                                st.session_state[_INDEX_KEY]    = 0
                                st.session_state[_FLIPPED_KEY]  = False
                                st.session_state[_KNOWN_KEY]    = set()
                                st.session_state[_LEARNING_KEY] = set()
                                st.session_state[_TOPIC_KEY]    = deck["topic"]
                                st.rerun()
                        with col_del:
                            if st.button("🗑 Delete", key=f"del_deck_{deck['id']}", use_container_width=True):
                                _delete_deck(deck["id"])
                                st.rerun()
        return

    # ── Active deck ───────────────────────────────────────────────────────────
    order   = st.session_state[_ORDER_KEY]
    idx     = st.session_state[_INDEX_KEY]
    flipped = st.session_state[_FLIPPED_KEY]
    known   = st.session_state[_KNOWN_KEY]
    learning = st.session_state[_LEARNING_KEY]
    total   = len(cards)

    # Pending = not yet marked Know It
    pending = [pos for pos in order if pos not in known]

    # ── Deck complete ─────────────────────────────────────────────────────────
    if not pending:
        st.balloons()
        still_learning_count = len(learning)
        st.markdown(f"""
        <div style="background:var(--bg-card);border:1px solid var(--border-accent);border-radius:20px;
                    padding:3rem 2rem;text-align:center;animation:fadeSlideUp 0.4s ease both;">
            <div style="display:flex;justify-content:center;margin-bottom:1rem;">{icon('award', 36)}</div>
            <div style="font-size:1.2rem;font-weight:800;color:#E6EDF3;margin-bottom:0.4rem;
                        font-family:'Sora',sans-serif;">Deck Complete!</div>
            <div style="font-size:0.9rem;color:#8A93A6;margin-bottom:0.5rem;">
                You reviewed all {total} cards in
                <strong style="color:#C084FC;">{st.session_state[_TOPIC_KEY]}</strong>.
            </div>
            <div style="font-size:0.85rem;color:#8A93A6;">
                {total - still_learning_count} known &nbsp;·&nbsp;
                {still_learning_count} still learning
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("↺ Restart deck", use_container_width=True):
                order_new = list(range(total))
                random.shuffle(order_new)
                st.session_state[_ORDER_KEY]    = order_new
                st.session_state[_INDEX_KEY]    = 0
                st.session_state[_FLIPPED_KEY]  = False
                st.session_state[_KNOWN_KEY]    = set()
                st.session_state[_LEARNING_KEY] = set()
                st.rerun()
        with c2:
            if still_learning_count > 0:
                if st.button(f"📖 Review {still_learning_count} still learning", use_container_width=True):
                    # Only loop through cards marked Still Learning
                    new_order = list(learning)
                    random.shuffle(new_order)
                    st.session_state[_ORDER_KEY]    = new_order
                    st.session_state[_INDEX_KEY]    = 0
                    st.session_state[_FLIPPED_KEY]  = False
                    st.session_state[_KNOWN_KEY]    = set()
                    st.session_state[_LEARNING_KEY] = set()
                    st.rerun()
        with c3:
            if st.button("✦ New deck — same topic", use_container_width=True):
                prev = st.session_state[_TOPIC_KEY]
                _reset_deck()
                st.session_state["fc_prefill_topic"] = prev
                st.rerun()
        return

    if idx >= len(pending):
        idx = 0
        st.session_state[_INDEX_KEY] = 0

    card_pos = pending[idx]
    card     = cards[card_pos]
    prog_pct = int(len(known) / total * 100)

    # Header bar
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem;">
        <span style="font-size:0.8rem;font-weight:600;color:#C084FC;">{st.session_state[_TOPIC_KEY]}</span>
        <span style="font-size:0.8rem;color:#8A93A6;">
            {len(known)} known &nbsp;·&nbsp; {len(learning)} learning &nbsp;·&nbsp; {len(pending)} remaining
        </span>
    </div>
    <div style="background:rgba(192,132,252,0.06);border-radius:4px;height:4px;margin-bottom:1.4rem;overflow:hidden;">
        <div style="background:linear-gradient(90deg,#C084FC,#E879F9);
                    width:{prog_pct}%;height:4px;border-radius:4px;
                    transition:width 0.6s cubic-bezier(0.4,0,0.2,1);"></div>
    </div>
    """, unsafe_allow_html=True)

    # Card face
    side_label = "DEFINITION" if flipped else "TERM"
    side_text  = card["back"] if flipped else card["front"]
    if flipped:
        bg      = "linear-gradient(135deg,rgba(192,132,252,0.08),rgba(192,132,252,0.04))"
        border  = "rgba(192,132,252,0.35)"
        top_col = "#C084FC"
        lbl_col = "#E879F9"
    else:
        bg      = "linear-gradient(135deg,rgba(23,18,42,0.95),rgba(16,13,26,0.9))"
        border  = "rgba(230,237,243,0.08)"
        top_col = "#8A93A6"
        lbl_col = "#4a5568"

    st.markdown(f"""
    <div style="background:{bg};border:1px solid {border};
                border-top:3px solid {top_col};border-radius:20px;
                padding:2.8rem 2rem;min-height:190px;text-align:center;
                margin-bottom:1.3rem;transition:all 0.3s ease;
                box-shadow:0 8px 40px rgba(0,0,0,0.25);animation:fadeSlideUp 0.3s ease both;">
        <div style="font-size:0.68rem;font-weight:800;letter-spacing:0.14em;
                     text-transform:uppercase;color:{lbl_col};margin-bottom:1.2rem;">{side_label}</div>
        <div style="font-size:1.15rem;font-weight:600;color:#E6EDF3;line-height:1.7;
                    font-family:'Sora',sans-serif;">{side_text}</div>
    </div>
    """, unsafe_allow_html=True)

    # Controls — 4 buttons: Flip | Still Learning | Know It | Next
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("↩ Flip", use_container_width=True):
            st.session_state[_FLIPPED_KEY] = not flipped
            st.rerun()
    with c2:
        if st.button("📖 Still Learning", use_container_width=True):
            learning.add(card_pos)
            st.session_state[_LEARNING_KEY] = learning
            st.session_state[_FLIPPED_KEY]  = False
            # Move to next pending card
            st.session_state[_INDEX_KEY] = (idx + 1) % len(pending)
            st.rerun()
    with c3:
        if st.button("✅ Know It", use_container_width=True):
            known.add(card_pos)
            learning.discard(card_pos)
            st.session_state[_KNOWN_KEY]    = known
            st.session_state[_LEARNING_KEY] = learning
            st.session_state[_FLIPPED_KEY]  = False
            new_pending = [p for p in order if p not in known]
            st.session_state[_INDEX_KEY] = min(idx, len(new_pending) - 1) if new_pending else 0
            st.rerun()
    with c4:
        if st.button("→ Next", use_container_width=True):
            st.session_state[_INDEX_KEY]   = (idx + 1) % len(pending)
            st.session_state[_FLIPPED_KEY] = False
            st.rerun()
