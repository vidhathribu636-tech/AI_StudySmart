"""
views/theme.py
--------------
Single source of truth for all CSS / design tokens.

Call inject_theme() at the very top of every page's show() function.
It is safe to call multiple times — Streamlit deduplicates identical
st.markdown() calls within the same run.
"""

import streamlit as st

# ── Lucide SVG icon helpers ────────────────────────────────────────────────────
# All icons are rendered at 20×20 px, stroke sky-blue #38BDF8, inside a tinted
# circle so they drop-in replace emoji anywhere.

_ICONS: dict[str, str] = {
    # name: SVG path(s) only — wrapper is added by icon()
    "bot":          '<circle cx="12" cy="12" r="3"/><path d="M12 3v3m0 12v3M3 12h3m12 0h3M5.6 5.6l2.1 2.1m8.6 8.6 2.1 2.1M5.6 18.4l2.1-2.1m8.6-8.6 2.1-2.1"/>',
    "book-open":    '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    "target":       '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "flame":        '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    "layers":       '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9A1 1 0 0 0 21.4 6.08z"/><path d="m22 12.5-8.58 3.91a2 2 0 0 1-1.66 0L3 12.5"/><path d="m22 17.5-8.58 3.91a2 2 0 0 1-1.66 0L3 17.5"/>',
    "bar-chart":    '<line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>',
    "trophy":       '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/>',
    "help-circle":  '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "layout":       '<rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><line x1="3" x2="21" y1="9" y2="9"/><line x1="9" x2="9" y1="21" y2="9"/>',
    "file-text":    '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/>',
    "copy":         '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    "zap":          '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "settings":     '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    "key":          '<circle cx="7.5" cy="15.5" r="5.5"/><path d="m21 2-9.6 9.6"/><path d="m15.5 7.5 3 3L22 7l-3-3"/>',
    "upload":       '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>',
    "sparkles":     '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3z"/><path d="M5 3v4"/><path d="M3 5h4"/><path d="M19 17v4"/><path d="M17 19h4"/>',
    "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "x-circle":     '<circle cx="12" cy="12" r="10"/><line x1="15" x2="9" y1="9" y2="15"/><line x1="9" x2="15" y1="9" y2="15"/>',
    "refresh-cw":   '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    "skip-forward": '<polygon points="5 4 15 12 5 20 5 4"/><line x1="19" x2="19" y1="5" y2="19"/>',
    "trash-2":      '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>',
    "trending-up":  '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>',
    "award":        '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
    "cpu":          '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2M9 2v2M15 22v-2M9 22v-2M2 15h2M2 9h2M22 15h-2M22 9h-2"/>',
    "home":         '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    "message-square": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "book":         '<path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/>',
    "pie-chart":    '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>',
    "more-horizontal": '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',
    "calendar":        '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/>',
    "clock":           '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
}


def icon(name: str, size: int = 20, color: str = "#C084FC", circle: bool = True) -> str:
    """
    Return an HTML string containing a Lucide SVG icon.

    Args:
        name:   key from _ICONS dict
        size:   icon size in px (default 20)
        color:  stroke color (default sky-blue)
        circle: if True, wrap in a tinted sky-blue circle div
    """
    paths = _ICONS.get(name, _ICONS["zap"])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
    )
    if not circle:
        return svg
    bg_size = size + 16
    return (
        f'<div style="background:rgba(192,132,252,0.12);'
        f'border:1px solid rgba(192,132,252,0.22);'
        f'border-radius:9px;width:{bg_size}px;height:{bg_size}px;'
        f'display:flex;align-items:center;justify-content:center;'
        f'flex-shrink:0;">{svg}</div>'
    )


# ── Full CSS ───────────────────────────────────────────────────────────────────

_CSS = """
<style>
/* ═══════════════════════════════════════════════
   DESIGN SYSTEM — AI Study Buddy
   Palette: #08060F bg · #100D1A panels · #17122A cards
            #C084FC purple accent · #E6EDF3 primary text
   Fonts:   Sora (headings) · Inter (body)
   ═══════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── CSS variables ─────────────────────────────── */
:root {
  --bg-base:       #08060F;
  --bg-surface:    #100D1A;
  --bg-card:       #17122A;
  --bg-card-hover: #1f1838;
  --border:        rgba(230,237,243,0.07);
  --border-accent: rgba(192,132,252,0.35);
  --accent:        #C084FC;
  --accent-hover:  #A855F7;
  --accent-dim:    rgba(192,132,252,0.12);
  --accent-glow:   rgba(192,132,252,0.25);
  --text-primary:  #E6EDF3;
  --text-secondary:#8A93A6;
  --text-muted:    #4a5568;
  --radius-sm:     8px;
  --radius-md:     12px;
  --radius-lg:     16px;
  --radius-xl:     24px;
  --transition:    all 0.25s cubic-bezier(0.4,0,0.2,1);
}

/* ── Base reset ─────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"] {
  background: var(--bg-base) !important;
  color: var(--text-primary) !important;
  font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif !important;
}

/* Sora for every heading level */
h1, h2, h3, h4,
.page-header h2,
.fc-card .fc-text,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
  font-family: 'Sora', -apple-system, sans-serif !important;
  color: var(--text-primary) !important;
}

.block-container {
  padding: 2rem 2.5rem 4rem 2.5rem !important;
  max-width: 1100px !important;
}

/* ── Hide Streamlit chrome ──────────────────────── */
#MainMenu, header[data-testid="stHeader"],
footer, [data-testid="stSidebarNav"],
[data-testid="stDecoration"] {
  display: none !important;
  visibility: hidden !important;
}
.stRadio > label { display: none !important; }

/* ══════════════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #130D22 0%, #08060F 100%) !important;
  border-right: 1px solid var(--border) !important;
  width: 240px !important;
  min-width: 240px !important;
  max-width: 240px !important;
}
[data-testid="stSidebar"] > div:first-child {
  display: flex !important;
  flex-direction: column !important;
  height: 100vh !important;
  overflow: hidden !important;
  padding-bottom: 0 !important;
}
[data-testid="stSidebar"] section[data-testid="stSidebarContent"] {
  display: flex !important;
  flex-direction: column !important;
  height: 100% !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  padding-bottom: 80px !important;
}
[data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
[data-testid="stSidebar"] .stRadio label {
  display: flex !important;
  align-items: center !important;
  padding: 0.6rem 1rem !important;
  border-radius: var(--radius-sm) !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  color: var(--text-secondary) !important;
  cursor: pointer !important;
  transition: var(--transition) !important;
  border: 1px solid transparent !important;
  margin: 1px 6px !important;
  letter-spacing: 0.01em !important;
}
[data-testid="stSidebar"] .stRadio label:hover {
  background: var(--accent-dim) !important;
  color: var(--text-primary) !important;
  border-color: var(--border-accent) !important;
  transform: translateX(2px) !important;
}
[data-testid="stSidebar"] .stRadio div[data-baseweb="radio"] > div:first-child {
  display: none !important;
}

/* ══════════════════════════════════════════════
   ANIMATIONS
   ══════════════════════════════════════════════ */
@keyframes fadeSlideUp {
  from { opacity:0; transform:translateY(20px); }
  to   { opacity:1; transform:translateY(0); }
}
@keyframes fadeIn {
  from { opacity:0; }
  to   { opacity:1; }
}
@keyframes pulseAmber {
  0%,100% {
    background: linear-gradient(135deg,#7C3AED,#C084FC) !important;
    box-shadow: 0 2px 12px rgba(192,132,252,0.3) !important;
  }
  50% {
    background: linear-gradient(135deg,#C084FC,#E879F9) !important;
    box-shadow: 0 4px 28px rgba(192,132,252,0.6), 0 0 0 4px rgba(192,132,252,0.12) !important;
  }
}
@keyframes float {
  0%,100% { transform: translateY(0px); }
  50%      { transform: translateY(-8px); }
}
@keyframes bgMove {
  0%   { transform: translate(0,0) scale(1); }
  33%  { transform: translate(30px,-20px) scale(1.05); }
  66%  { transform: translate(-20px,30px) scale(0.97); }
  100% { transform: translate(0,0) scale(1); }
}
.anim-fadeup   { animation: fadeSlideUp 0.5s ease both; }
.anim-fadeup-1 { animation: fadeSlideUp 0.5s 0.05s ease both; }
.anim-fadeup-2 { animation: fadeSlideUp 0.5s 0.10s ease both; }
.anim-fadeup-3 { animation: fadeSlideUp 0.5s 0.15s ease both; }
.anim-fadeup-4 { animation: fadeSlideUp 0.5s 0.20s ease both; }

/* ══════════════════════════════════════════════
   SHARED COMPONENTS
   ══════════════════════════════════════════════ */
hr.divider {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.2rem 0 !important;
}
.page-header {
  padding: 0.5rem 0 1.2rem 0;
  animation: fadeSlideUp 0.4s ease both;
}
.page-header .badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--accent-dim);
  border: 1px solid var(--border-accent);
  border-radius: 20px;
  padding: 0.25rem 0.8rem;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 0.7rem;
}
.page-header h2 {
  font-size: 1.7rem !important;
  font-weight: 800 !important;
  color: var(--text-primary) !important;
  margin: 0 0 0.3rem 0 !important;
  letter-spacing: -0.03em !important;
  line-height: 1.2 !important;
  font-family: 'Sora', -apple-system, sans-serif !important;
}
.page-header p {
  font-size: 0.9rem !important;
  color: var(--text-secondary) !important;
  margin: 0 !important;
  line-height: 1.6 !important;
}

/* Cards — fade-in on load */
.glass-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.4rem 1.6rem;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
  animation: fadeSlideUp 0.5s ease both;
}
.glass-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg,transparent,rgba(192,132,252,0.2),transparent);
}
.glass-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-accent);
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(192,132,252,0.15);
}

/* Stat card */
.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.2rem 1.4rem;
  text-align: center;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
  animation: fadeSlideUp 0.5s ease both;
}
.stat-card:hover {
  border-color: var(--border-accent);
  transform: translateY(-3px);
  box-shadow: 0 8px 30px rgba(192,132,252,0.12);
}
.stat-card .icon {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 0.6rem auto;
}
.stat-card .val {
  font-size: 1.9rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 0.3rem;
  background: linear-gradient(135deg,#C084FC,#E879F9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-family: 'Sora', -apple-system, sans-serif;
}
.stat-card .lbl {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 600;
}

/* Info/alert box */
.info-box {
  background: var(--accent-dim);
  border: 1px solid var(--border-accent);
  border-radius: var(--radius-md);
  padding: 1.2rem 1.5rem;
  margin: 0.8rem 0;
  animation: fadeIn 0.3s ease;
}
.info-box h4 {
  margin: 0 0 0.35rem 0 !important;
  font-size: 0.9rem !important;
  font-weight: 700 !important;
  color: var(--accent) !important;
  font-family: 'Sora', -apple-system, sans-serif !important;
}
.info-box p {
  margin: 0 !important;
  font-size: 0.85rem !important;
  color: var(--text-secondary) !important;
  line-height: 1.6 !important;
}

/* Section label */
.section-label {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.8rem;
  display: block;
}

/* Progress bar */
.prog-bar-wrap {
  background: rgba(255,255,255,0.05);
  border-radius: 4px;
  height: 5px;
  overflow: hidden;
}
.prog-bar-fill {
  height: 5px;
  border-radius: 4px;
  transition: width 0.8s cubic-bezier(0.4,0,0.2,1);
}

/* Chat bubbles */
.chat-user-wrap {
  display: flex;
  justify-content: flex-end;
  margin: 0.7rem 0;
  animation: fadeSlideUp 0.3s ease both;
}
.chat-user-bubble {
  background: linear-gradient(135deg,#7C3AED,#C084FC);
  color: #FFFFFF;
  padding: 0.7rem 1.1rem;
  border-radius: 18px 18px 3px 18px;
  max-width: 70%;
  font-size: 0.9rem;
  line-height: 1.6;
  font-weight: 600;
  box-shadow: 0 4px 15px rgba(192,132,252,0.2);
}
.chat-ai-wrap {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  margin: 0.7rem 0;
  animation: fadeSlideUp 0.3s ease both;
}
.chat-ai-avatar {
  background: linear-gradient(135deg,#100D1A,#17122A);
  border: 1px solid var(--border-accent);
  border-radius: 50%;
  width: 34px; height: 34px;
  min-width: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  box-shadow: 0 0 12px var(--accent-glow);
}
.chat-ai-bubble {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 3px 18px 18px 18px;
  padding: 0.75rem 1.1rem;
  max-width: 80%;
  font-size: 0.9rem;
  color: var(--text-primary);
  line-height: 1.75;
  box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

/* Flashcard */
.fc-card {
  border-radius: var(--radius-xl);
  padding: 2.5rem 2rem;
  min-height: 180px;
  text-align: center;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
  cursor: pointer;
}
.fc-card:hover { transform: translateY(-4px); }
.fc-card .fc-label {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 1.2rem;
  display: block;
}
.fc-card .fc-text {
  font-size: 1.15rem;
  font-weight: 600;
  line-height: 1.65;
  color: var(--text-primary);
  font-family: 'Sora', -apple-system, sans-serif;
}

/* ══════════════════════════════════════════════
   BUTTONS — Sky-blue theme, NO exceptions
   ══════════════════════════════════════════════ */
/* Every button variant: stButton, stFormSubmitButton, baseButton */
.stButton > button,
.stFormSubmitButton > button,
button[data-testid="baseButton-primary"],
button[data-testid="baseButton-secondary"],
button[kind="primary"],
button[kind="secondary"],
[data-testid="stFormSubmitButton"] > button {
  background: linear-gradient(135deg,#7C3AED,#C084FC) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: var(--radius-sm) !important;
  font-size: 0.875rem !important;
  font-weight: 700 !important;
  padding: 0.5rem 1.2rem !important;
  transition: var(--transition) !important;
  letter-spacing: 0.01em !important;
  box-shadow: 0 2px 12px rgba(192,132,252,0.25) !important;
  font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover,
button[data-testid="baseButton-primary"]:hover,
button[data-testid="baseButton-secondary"]:hover,
[data-testid="stFormSubmitButton"] > button:hover {
  background: linear-gradient(135deg,#C084FC,#E879F9) !important;
  color: #FFFFFF !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 20px rgba(192,132,252,0.4) !important;
}
/* Force white text — high-specificity selectors targeting nested elements */
.stButton > button p,
.stButton > button div,
.stButton > button span,
.stFormSubmitButton > button p,
.stFormSubmitButton > button div,
.stFormSubmitButton > button span,
[data-testid="stFormSubmitButton"] > button p,
[data-testid="stFormSubmitButton"] > button div,
[data-testid="baseButton-primary"] p,
[data-testid="baseButton-secondary"] p {
  color: #FFFFFF !important;
  font-weight: 700 !important;
  opacity: 1 !important;
}

.stButton > button:active,
.stFormSubmitButton > button:active { transform: translateY(0) !important; }
.stButton > button:disabled,
.stFormSubmitButton > button:disabled {
  background: rgba(255,255,255,0.05) !important;
  color: var(--text-muted) !important;
  box-shadow: none !important;
  transform: none !important;
}

/* Pulsing form submit button (Ask AI / Generate / Submit) */
form[data-testid="stForm"] .stFormSubmitButton > button,
form[data-testid="stForm"] .stButton > button {
  animation: pulseAmber 2.8s ease-in-out infinite !important;
}
form[data-testid="stForm"] .stFormSubmitButton > button:hover,
form[data-testid="stForm"] .stButton > button:hover {
  animation: none !important;
}

/* ══════════════════════════════════════════════
   INPUTS
   ══════════════════════════════════════════════ */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-primary) !important;
  font-size: 0.9rem !important;
  font-family: 'Inter', sans-serif !important;
  transition: var(--transition) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: rgba(192,132,252,0.5) !important;
  box-shadow: 0 0 0 3px rgba(192,132,252,0.1) !important;
  outline: none !important;
}
.stTextInput label, .stTextArea label, .stNumberInput label,
.stFileUploader label, .stSlider label {
  color: var(--text-secondary) !important;
  font-size: 0.85rem !important;
  font-weight: 500 !important;
  font-family: 'Inter', sans-serif !important;
}

/* ══════════════════════════════════════════════
   SLIDER — Sky-blue, not red/pink
   ══════════════════════════════════════════════ */
[data-testid="stSlider"] [role="slider"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(56,189,248,0.25) !important;
}
/* Filled track */
[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stSliderThumb"],
[data-testid="stSlider"] div[data-baseweb="slider"] > div:nth-child(3) > div {
  background: var(--accent) !important;
}
/* Base UI slider overrides — catches the thumb and filled range */
div[data-baseweb="slider"] [role="slider"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
}
div[data-baseweb="slider"] div[data-testid="stThumbValue"] {
  color: var(--accent) !important;
}
/* Filled portion of the track */
div[data-baseweb="slider"] > div > div:nth-child(2) {
  background: var(--accent) !important;
}
/* Tick marks / min-max labels */
[data-testid="stSlider"] [data-testid="stTickBar"] span,
[data-testid="stSlider"] p {
  color: var(--text-secondary) !important;
}
/* Generic base-web override — covers all slider variants */
[data-baseweb="slider"] [role="slider"]::before,
[data-baseweb="slider"] [role="slider"]::after {
  background: var(--accent) !important;
}
/* Streamlit 1.35+ internal class names */
[class*="StyledSlider"] [role="slider"],
[class*="StyledThumb"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
}

/* ══════════════════════════════════════════════
   TABS — Sky-blue indicator, not red/pink
   ══════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-muted) !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  padding: 0.55rem 1.1rem !important;
  border-bottom: 2px solid transparent !important;
  transition: var(--transition) !important;
  font-family: 'Inter', sans-serif !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--text-primary) !important;
}
/* Selected tab */
.stTabs [aria-selected="true"],
.stTabs [data-baseweb="tab"][aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom: 2px solid var(--accent) !important;
  background: transparent !important;
}
/* The animated underline bar that Streamlit renders separately */
[data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] {
  background: var(--accent) !important;
}

/* ══════════════════════════════════════════════
   LINKS — Sky-blue accent
   ══════════════════════════════════════════════ */
a, a:visited {
  color: var(--accent) !important;
  text-decoration: none !important;
}
a:hover { text-decoration: underline !important; opacity: 0.85; }
[data-testid="stMarkdownContainer"] a,
[data-testid="stMarkdownContainer"] a:visited {
  color: var(--accent) !important;
}

/* ══════════════════════════════════════════════
   OTHER WIDGETS
   ══════════════════════════════════════════════ */
/* Expander */
[data-testid="stExpander"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
}
[data-testid="stExpander"] summary {
  color: var(--text-secondary) !important;
  font-size: 0.875rem !important;
}

/* Spinner */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* Alerts */
[data-testid="stAlert"] {
  background: var(--accent-dim) !important;
  border: 1px solid var(--border-accent) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-secondary) !important;
}

/* Slider track wrapper */
[data-testid="stSlider"] { padding: 0.5rem 0 !important; }

/* File uploader */
[data-testid="stFileUploader"] {
  background: var(--bg-card) !important;
  border: 1.5px dashed rgba(192,132,252,0.18) !important;
  border-radius: var(--radius-lg) !important;
  transition: var(--transition) !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: rgba(192,132,252,0.4) !important;
  background: var(--accent-dim) !important;
}

/* Radio (quiz answers) */
.stRadio [data-testid="stMarkdownContainer"] p {
  color: var(--text-secondary) !important;
  font-size: 0.875rem !important;
}

/* Number input arrows */
.stNumberInput [data-testid="stNumberInputStepDown"],
.stNumberInput [data-testid="stNumberInputStepUp"] {
  color: var(--accent) !important;
}

/* Select box */
.stSelectbox [data-baseweb="select"] > div {
  background: var(--bg-card) !important;
  border-color: var(--border) !important;
  color: var(--text-primary) !important;
}

/* Checkbox */
[data-testid="stCheckbox"] [data-baseweb="checkbox"] > span {
  border-color: var(--border-accent) !important;
}
[data-testid="stCheckbox"] input:checked ~ span {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
}

/* Global text */
h1,h2,h3,h4 { color: var(--text-primary) !important; }
p, li { color: var(--text-secondary); }
strong { color: var(--text-primary) !important; }
code {
  background: rgba(192,132,252,0.08) !important;
  color: var(--accent) !important;
  border-radius: 4px !important;
  padding: 1px 6px !important;
  font-size: 0.85em !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb {
  background: rgba(192,132,252,0.12);
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(192,132,252,0.25); }
</style>
"""


def inject_theme() -> None:
    """
    Inject the full design-system CSS into the current Streamlit page.
    Call at the very top of every page's show() function.
    """
    st.markdown(_CSS, unsafe_allow_html=True)
