# frontend.py
import streamlit as st
import streamlit.components.v1 as components
import requests
import uuid
import json

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cairo Care | مساعدك الطبي الذكي",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Inject Google Fonts + Full Design System CSS ────────────────────────────
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700;800;900&family=Noto+Kufi+Arabic:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

<style>
/* ════════════════════════════════════════════════
   DESIGN TOKENS
════════════════════════════════════════════════ */
:root {
  --bg-void:         #040810;
  --bg-deep:         #060D1A;
  --bg-surface:      #0A1628;
  --bg-glass:        rgba(8, 145, 178, 0.08);
  --bg-glass-hover:  rgba(8, 145, 178, 0.14);

  --color-primary:        #0891B2;
  --color-primary-bright: #22D3EE;
  --color-secondary:      #06B6D4;
  --color-accent:         #10B981;
  --color-accent-2:       #6366F1;

  --grad-brand:   linear-gradient(135deg, #0891B2 0%, #06B6D4 40%, #10B981 100%);
  --grad-user:    linear-gradient(135deg, #0891B2 0%, #6366F1 100%);
  --grad-ai:      linear-gradient(135deg, #0A1628 0%, #0F2035 100%);
  --grad-header:  linear-gradient(160deg, #040D1C 0%, #0A1A30 60%, #071520 100%);
  --grad-glow:    radial-gradient(ellipse at 50% 0%, rgba(8,145,178,0.22) 0%, transparent 65%);

  --text-primary:   #F0F9FF;
  --text-secondary: #94A3B8;
  --text-muted:     #4B6480;
  --text-brand:     #22D3EE;

  --border-subtle: rgba(8, 145, 178, 0.18);
  --border-glow:   rgba(34, 211, 238, 0.35);

  --radius-md:   14px;
  --radius-lg:   20px;
  --radius-xl:   28px;
  --radius-pill: 999px;

  --shadow-card: 0 4px 24px rgba(0,0,0,0.55), 0 1px 4px rgba(0,0,0,0.3);
  --shadow-glow: 0 0 32px rgba(8,145,178,0.3), 0 0 8px rgba(8,145,178,0.15);
  --shadow-btn:  0 4px 20px rgba(8,145,178,0.45);

  --font-en: 'Figtree', sans-serif;
  --font-ar: 'Noto Kufi Arabic', 'Figtree', sans-serif;
}

/* ════════════════════════════════════════════════
   GLOBAL BASE
════════════════════════════════════════════════ */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stApp"] {
  background-color: var(--bg-void) !important;
  font-family: var(--font-ar);
  color: var(--text-primary);
}
[data-testid="stAppViewContainer"] {
  background: var(--grad-glow), var(--bg-void) !important;
  background-attachment: fixed !important;
}
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

.block-container {
  max-width: 780px !important;
  padding: 0 !important;
  margin: 0 auto !important;
}

/* ════════════════════════════════════════════════
   ANIMATED HERO HEADER
════════════════════════════════════════════════ */
.cc-header {
  position: relative;
  overflow: hidden;
  padding: 44px 32px 36px;
  background: var(--grad-header);
  border-bottom: 1px solid var(--border-subtle);
  text-align: center;
}
.cc-header::before {
  content: '';
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse at 25% 50%, rgba(8,145,178,0.22) 0%, transparent 60%),
    radial-gradient(ellipse at 75% 50%, rgba(16,185,129,0.18) 0%, transparent 55%);
  pointer-events: none;
}
.cc-header::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-primary-bright), transparent);
}
.cc-logo-ring {
  position: relative;
  width: 84px; height: 84px;
  margin: 0 auto 18px;
  display: flex; align-items: center; justify-content: center;
}
.cc-logo-ring::before {
  content: '';
  position: absolute; inset: -8px;
  border-radius: 50%;
  background: var(--grad-brand);
  opacity: 0.2;
  animation: pulse-ring 2.6s ease-in-out infinite;
}
@keyframes pulse-ring {
  0%,100% { transform: scale(1);    opacity: 0.2; }
  50%      { transform: scale(1.12); opacity: 0.4; }
}
.cc-logo-icon {
  width: 76px; height: 76px;
  border-radius: 50%;
  background: var(--grad-brand);
  box-shadow: var(--shadow-glow);
  display: flex; align-items: center; justify-content: center;
  font-size: 36px; line-height: 1;
}
.cc-title {
  font-family: var(--font-en);
  font-size: 2.1rem; font-weight: 900;
  letter-spacing: -0.5px;
  background: var(--grad-brand);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 6px; line-height: 1.1;
}
.cc-subtitle {
  font-family: var(--font-ar);
  font-size: 1rem; font-weight: 400;
  color: var(--text-secondary);
  margin: 0 0 22px;
  direction: rtl;
}
.cc-badges {
  display: flex; justify-content: center;
  gap: 10px; flex-wrap: wrap;
}
.cc-badge {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 13px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border-subtle);
  background: rgba(8,145,178,0.1);
  font-size: 0.73rem; font-weight: 600;
  color: var(--text-brand); letter-spacing: 0.2px;
  direction: rtl;
}

/* ════════════════════════════════════════════════
   STATUS BAR
════════════════════════════════════════════════ */
.cc-status {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 8px;
  font-size: 0.72rem; color: var(--text-muted);
  border-bottom: 1px solid rgba(8,145,178,0.08);
  background: rgba(6,13,26,0.55);
  direction: rtl;
}
.cc-status-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--color-accent);
  box-shadow: 0 0 7px var(--color-accent);
  animation: blink 2s ease-in-out infinite;
}
@keyframes blink {
  0%,100% { opacity: 1;   }
  50%      { opacity: 0.3; }
}

/* ════════════════════════════════════════════════
   QUICK-ACTION CHIPS
════════════════════════════════════════════════ */
.cc-chips-wrap {
  padding: 14px 22px 10px;
  display: flex; gap: 8px; flex-wrap: wrap;
  justify-content: flex-end; direction: rtl;
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(6,13,26,0.6);
}
.cc-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 7px 14px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border-subtle);
  background: var(--bg-glass);
  color: var(--text-brand);
  font-size: 0.78rem; font-weight: 600;
  cursor: pointer;
  transition: all 0.22s ease;
  font-family: var(--font-ar);
  white-space: nowrap;
}
.cc-chip:hover {
  background: var(--bg-glass-hover);
  border-color: var(--border-glow);
  box-shadow: 0 0 14px rgba(34,211,238,0.2);
  transform: translateY(-1px);
}

/* ════════════════════════════════════════════════
   EMPTY STATE / WELCOME
════════════════════════════════════════════════ */
.cc-welcome {
  display: flex; flex-direction: column; align-items: center;
  text-align: center;
  padding: 48px 24px 28px; gap: 12px;
}
.cc-welcome-icon {
  width: 64px; height: 64px; border-radius: 50%;
  background: var(--grad-brand);
  display: flex; align-items: center; justify-content: center;
  font-size: 30px;
  box-shadow: var(--shadow-glow);
  margin-bottom: 6px;
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  0%,100% { transform: translateY(0);    }
  50%      { transform: translateY(-9px); }
}
.cc-welcome h2 {
  font-family: var(--font-ar);
  font-size: 1.5rem; font-weight: 700;
  color: var(--text-primary); margin: 0; direction: rtl;
}
.cc-welcome p {
  font-family: var(--font-ar);
  font-size: 0.91rem; color: var(--text-secondary);
  margin: 0; max-width: 420px;
  line-height: 1.85; direction: rtl;
}

/* ════════════════════════════════════════════════
   SUGGESTION CARDS
════════════════════════════════════════════════ */
.cc-suggestions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px; padding: 0 20px 28px;
  direction: rtl;
}
.cc-sug-card {
  background: var(--bg-glass);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 16px 14px;
  cursor: pointer;
  transition: all 0.25s ease;
  text-align: right;
}
.cc-sug-card:hover {
  background: var(--bg-glass-hover);
  border-color: var(--border-glow);
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(8,145,178,0.22);
}
.cc-sug-card .sug-icon { font-size: 1.55rem; margin-bottom: 9px; display: block; }
.cc-sug-card .sug-text {
  font-family: var(--font-ar);
  font-size: 0.8rem; font-weight: 600;
  color: var(--text-primary); line-height: 1.5;
}
.cc-sug-card .sug-label {
  font-size: 0.69rem; color: var(--text-brand);
  font-weight: 500; margin-top: 5px;
}

/* ════════════════════════════════════════════════
   CHAT MESSAGES
════════════════════════════════════════════════ */
[data-testid="stChatMessageContent"] {
  font-family: var(--font-ar) !important;
  font-size: 0.96rem !important;
  line-height: 1.8 !important;
  direction: rtl !important;
  text-align: right !important;
}
[data-testid="stChatMessage"] {
  background: transparent !important;
  border: none !important;
  padding: 4px 8px !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"])
[data-testid="stChatMessageContent"] {
  background: var(--grad-user) !important;
  border-radius: 20px 4px 20px 20px !important;
  padding: 14px 18px !important;
  box-shadow: 0 4px 20px rgba(8,145,178,0.38) !important;
  color: #fff !important;
  border: 1px solid rgba(34,211,238,0.22) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"])
[data-testid="stChatMessageContent"] {
  background: var(--grad-ai) !important;
  border-radius: 4px 20px 20px 20px !important;
  padding: 14px 18px !important;
  box-shadow: var(--shadow-card) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-subtle) !important;
}
[data-testid="chatAvatarIcon-user"] {
  background: var(--grad-user) !important;
  border: 2px solid rgba(34,211,238,0.3) !important;
}
[data-testid="chatAvatarIcon-assistant"] {
  background: var(--grad-brand) !important;
  border: 2px solid rgba(16,185,129,0.4) !important;
  box-shadow: 0 0 12px rgba(16,185,129,0.4) !important;
}

/* ════════════════════════════════════════════════
   CHAT INPUT
════════════════════════════════════════════════ */
[data-testid="stChatInput"] {
  background: rgba(6,13,26,0.95) !important;
  border-top: 1px solid var(--border-subtle) !important;
  padding: 16px 20px !important;
}
[data-testid="stChatInput"] textarea {
  background: var(--bg-surface) !important;
  border: 1.5px solid var(--border-subtle) !important;
  border-radius: var(--radius-xl) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ar) !important;
  font-size: 0.95rem !important;
  direction: rtl !important;
  text-align: right !important;
  padding: 14px 20px !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
  caret-color: var(--color-primary-bright) !important;
}
[data-testid="stChatInput"] textarea:focus {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 3px rgba(8,145,178,0.18), var(--shadow-glow) !important;
  outline: none !important;
}
[data-testid="stChatInput"] textarea::placeholder {
  color: var(--text-muted) !important; direction: rtl !important;
}
[data-testid="stChatInput"] button {
  background: var(--grad-brand) !important;
  border: none !important;
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-btn) !important;
  transition: all 0.2s !important;
}
[data-testid="stChatInput"] button:hover {
  transform: scale(1.06) !important;
  box-shadow: 0 6px 28px rgba(8,145,178,0.62) !important;
}
[data-testid="stChatInput"] button svg { color: #fff !important; }

/* ════════════════════════════════════════════════
   RESET BUTTON
════════════════════════════════════════════════ */
.stButton button {
  background: transparent !important;
  border: 1px solid var(--border-subtle) !important;
  border-radius: var(--radius-pill) !important;
  color: var(--text-secondary) !important;
  font-family: var(--font-ar) !important;
  font-size: 0.8rem !important;
  padding: 7px 16px !important;
  transition: all 0.2s !important;
}
.stButton button:hover {
  background: var(--bg-glass) !important;
  border-color: var(--border-glow) !important;
  color: var(--text-brand) !important;
}

/* ════════════════════════════════════════════════
   SCROLLBAR + MISC
════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--color-primary); border-radius: 99px; }
.stAlert {
  border-radius: var(--radius-md) !important;
  border: 1px solid rgba(220,38,38,0.3) !important;
  background: rgba(220,38,38,0.08) !important;
  direction: rtl !important; text-align: right !important;
}

/* ════════════════════════════════════════════════
   SIDEBAR — CHAT HISTORY
════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: #060D1A !important;
  border-left: 1px solid rgba(8,145,178,0.18) !important;
  min-width: 280px !important;
  max-width: 320px !important;
}
[data-testid="stSidebar"] > div:first-child {
  padding: 0 !important;
}
/* sidebar scrollbar */
[data-testid="stSidebar"] ::-webkit-scrollbar { width: 3px; }
[data-testid="stSidebar"] ::-webkit-scrollbar-thumb { background: rgba(8,145,178,0.4); border-radius: 99px; }

/* new-chat button full-width gradient */
.sb-new-btn > div > button {
  width: 100% !important;
  background: linear-gradient(135deg, #0891B2, #10B981) !important;
  border: none !important;
  border-radius: 12px !important;
  color: #fff !important;
  font-family: 'Noto Kufi Arabic', sans-serif !important;
  font-size: 0.9rem !important;
  font-weight: 700 !important;
  padding: 10px 0 !important;
  box-shadow: 0 4px 20px rgba(8,145,178,0.45) !important;
  transition: all 0.2s !important;
  letter-spacing: 0.2px;
}
.sb-new-btn > div > button:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 28px rgba(8,145,178,0.6) !important;
}

/* thread card */
.sb-thread {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  margin-bottom: 6px;
  position: relative;
}
.sb-thread:hover {
  background: rgba(8,145,178,0.1);
  border-color: rgba(8,145,178,0.25);
}
.sb-thread.active {
  background: rgba(8,145,178,0.14);
  border-color: rgba(34,211,238,0.38);
  box-shadow: 0 0 12px rgba(8,145,178,0.18);
}
.sb-thread-icon {
  width: 34px; height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0891B2, #10B981);
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; flex-shrink: 0;
  box-shadow: 0 0 8px rgba(8,145,178,0.35);
}
.sb-thread-body { flex: 1; min-width: 0; direction: rtl; text-align: right; }
.sb-thread-title {
  font-family: 'Noto Kufi Arabic', sans-serif;
  font-size: 0.82rem; font-weight: 600;
  color: #F0F9FF;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  line-height: 1.3;
}
.sb-thread-time {
  font-size: 0.68rem;
  color: #4B6480;
  margin-top: 3px;
}
.sb-delete-btn > div > button {
  background: transparent !important;
  border: none !important;
  color: #4B6480 !important;
  padding: 2px 6px !important;
  font-size: 0.75rem !important;
  border-radius: 6px !important;
  min-height: unset !important;
  line-height: 1 !important;
  transition: all 0.15s !important;
}
.sb-delete-btn > div > button:hover {
  color: #ef4444 !important;
  background: rgba(239,68,68,0.12) !important;
}

/* sidebar section label */
.sb-label {
  font-family: 'Figtree', sans-serif;
  font-size: 0.65rem; font-weight: 700;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: #4B6480;
  padding: 14px 14px 6px;
  direction: rtl;
}
.sb-divider {
  height: 1px;
  background: rgba(8,145,178,0.12);
  margin: 8px 14px;
}
.sb-empty {
  text-align: center;
  padding: 24px 16px;
  color: #4B6480;
  font-family: 'Noto Kufi Arabic', sans-serif;
  font-size: 0.8rem;
  direction: rtl;
  line-height: 1.7;
}

/* Location badge and sidebar styling */
.cc-loc-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 14px;
  border-radius: var(--radius-pill);
  border: 1px solid rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.12);
  font-size: 0.75rem; font-weight: 700;
  color: #34D399; letter-spacing: 0.2px;
  direction: rtl;
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
}
.cc-loc-badge .loc-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 8px #10B981;
  animation: blink 2s ease-in-out infinite;
}
.sb-loc-card {
  margin: 6px 14px 10px;
  padding: 12px 14px;
  background: rgba(8,145,178,0.09);
  border: 1px solid rgba(8,145,178,0.22);
  border-radius: 12px;
  direction: rtl;
  text-align: right;
}
.sb-loc-title {
  font-family: 'Noto Kufi Arabic', sans-serif;
  font-size: 0.8rem; font-weight: 700;
  color: #F0F9FF; margin-bottom: 3px;
  display: flex; align-items: center; justify-content: space-between;
}
.sb-loc-sub {
  font-size: 0.7rem; color: #22D3EE;
  margin-bottom: 8px; line-height: 1.4;
}
.sb-loc-coords {
  font-size: 0.65rem; color: #64748B;
  font-family: monospace; direction: ltr; text-align: right;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
  background: rgba(6, 13, 26, 0.9) !important;
  border: 1px solid rgba(8, 145, 178, 0.3) !important;
  border-radius: 10px !important;
  color: #F0F9FF !important;
  font-family: 'Noto Kufi Arabic', sans-serif !important;
  font-size: 0.82rem !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────
API_BASE = "http://localhost:8000"


def fetch_threads() -> list[dict]:
    """Fetch the list of threads from the backend, newest first."""
    try:
        r = requests.get(f"{API_BASE}/threads", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def load_thread_messages(thread_id: str) -> list[dict]:
    """Load message history for a thread from the backend checkpointer."""
    try:
        r = requests.get(f"{API_BASE}/threads/{thread_id}/messages", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def delete_thread_from_backend(thread_id: str) -> None:
    """Remove a thread from the backend registry."""
    try:
        requests.delete(f"{API_BASE}/threads/{thread_id}", timeout=3)
    except Exception:
        pass


def relative_time(iso_str: str) -> str:
    """Return a human-readable relative timestamp in Arabic."""
    from datetime import datetime, timezone
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        diff = (datetime.now(timezone.utc) - dt).total_seconds()
        if diff < 60:
            return "الآن"
        if diff < 3600:
            m = int(diff / 60)
            return f"منذ {m} دقيقة" if m == 1 else f"منذ {m} دقائق"
        if diff < 86400:
            h = int(diff / 3600)
            return f"منذ {h} ساعة" if h == 1 else f"منذ {h} ساعات"
        d = int(diff / 86400)
        return f"منذ {d} يوم" if d == 1 else f"منذ {d} أيام"
    except Exception:
        return ""


# ─── Cairo District Presets ───────────────────────────────────────────────────
CAIRO_DISTRICT_PRESETS = {
    "المعادي": {"lat": 29.9602, "lon": 31.2569, "area_slug": "المعادي", "display_name": "المعادي، القاهرة"},
    "مدينة نصر": {"lat": 30.0561, "lon": 31.3444, "area_slug": "مدينة-نصر", "display_name": "مدينة نصر، القاهرة"},
    "مصر الجديدة": {"lat": 30.0890, "lon": 31.3285, "area_slug": "مصر-الجديدة", "display_name": "مصر الجديدة، القاهرة"},
    "الدقي والمهندسين": {"lat": 30.0384, "lon": 31.2119, "area_slug": "الدقي-والمهندسين", "display_name": "الدقي والمهندسين، الجيزة"},
    "الزمالك": {"lat": 30.0610, "lon": 31.2201, "area_slug": "الزمالك", "display_name": "الزمالك، القاهرة"},
    "التجمع الخامس": {"lat": 30.0074, "lon": 31.4312, "area_slug": "التجمع", "display_name": "التجمع الخامس والقاهرة الجديدة"},
    "وسط البلد": {"lat": 30.0444, "lon": 31.2357, "area_slug": "وسط-البلد", "display_name": "وسط البلد والتحرير، القاهرة"},
    "شبرا": {"lat": 30.0784, "lon": 31.2442, "area_slug": "شبرا", "display_name": "شبرا، القاهرة"},
    "الهرم والجيزة": {"lat": 29.9972, "lon": 31.1856, "area_slug": "الهرم", "display_name": "الهرم وفيصل، الجيزة"},
    "6 أكتوبر": {"lat": 29.9723, "lon": 30.9419, "area_slug": "6-اكتوبر", "display_name": "مدينة 6 أكتوبر"},
    "الشيخ زايد": {"lat": 30.0450, "lon": 31.0020, "area_slug": "الشيخ-زايد", "display_name": "مدينة الشيخ زايد"},
    "المقطم": {"lat": 30.0080, "lon": 31.2980, "area_slug": "المقطم", "display_name": "المقطم، القاهرة"},
    "العباسية": {"lat": 30.0680, "lon": 31.2820, "area_slug": "الوايلي-والعباسية", "display_name": "العباسية والوايلي، القاهرة"},
    "عين شمس": {"lat": 30.1310, "lon": 31.3210, "area_slug": "عين-شمس", "display_name": "عين شمس، القاهرة"},
    "حلوان": {"lat": 29.8490, "lon": 31.3340, "area_slug": "حلوان", "display_name": "حلوان، القاهرة"},
}

# ─── Initialize Session State ─────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
# Flag set when user clicks a thread card — triggers message reload
if "switch_to_thread" not in st.session_state:
    st.session_state.switch_to_thread = None

def fetch_initial_location() -> dict:
    try:
        r = requests.get(f"{API_BASE}/api/location/ip", timeout=3)
        if r.status_code == 200:
            data = r.json()
            return {
                "lat": data.get("lat", 30.0444),
                "lon": data.get("lon", 31.2357),
                "area": data.get("district", "وسط البلد"),
                "area_slug": data.get("area_slug", "وسط-البلد"),
                "display_name": data.get("display_name", "وسط البلد، القاهرة"),
                "source": data.get("source", "تلقائي (IP)"),
            }
    except Exception:
        pass
    return {
        "lat": 30.0444,
        "lon": 31.2357,
        "area": "وسط البلد",
        "area_slug": "وسط-البلد",
        "display_name": "وسط البلد، القاهرة",
        "source": "افتراضي",
    }

# Initialize location with IP detection
if "user_location" not in st.session_state:
    st.session_state.user_location = fetch_initial_location()

# ─── Check Browser-Reported GPS Coordinates ──────────────────────────────────
try:
    r_gps = requests.get(
        f"{API_BASE}/api/location/browser/{st.session_state.thread_id}",
        timeout=1,
    )
    if r_gps.status_code == 200:
        gps_data = r_gps.json()
        if gps_data and "lat" in gps_data:
            if st.session_state.user_location.get("source") != "GPS دقيق":
                st.session_state.user_location = {
                    "lat": gps_data["lat"],
                    "lon": gps_data["lon"],
                    "area": gps_data.get("district", "القاهرة"),
                    "area_slug": gps_data.get("area_slug", "القاهرة"),
                    "display_name": gps_data.get("display_name", ""),
                    "source": "GPS دقيق",
                }
                st.rerun()
except Exception:
    pass

# ─── HTML5 Geolocation Bridge (Reports directly to Backend via fetch) ────────
components.html(f"""
<script>
(function() {{
    if ("geolocation" in navigator) {{
        navigator.geolocation.getCurrentPosition(
            function(pos) {{
                fetch("{API_BASE}/api/location/browser", {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify({{
                        thread_id: "{st.session_state.thread_id}",
                        lat: pos.coords.latitude,
                        lon: pos.coords.longitude
                    }})
                }}).then(function(r) {{ return r.json(); }})
                .then(function(d) {{
                    console.log("GPS Location saved:", d);
                }}).catch(function(e) {{
                    console.log("GPS fetch error:", e);
                }});
            }},
            function(err) {{
                console.log("Browser geolocation notice:", err.message);
            }},
            {{ enableHighAccuracy: true, timeout: 8000, maximumAge: 300000 }}
        );
    }}
}})();
</script>
""", height=0, width=0)

# ─── Handle thread switch (must happen before rendering) ──────────────────────
if st.session_state.switch_to_thread:
    tid = st.session_state.switch_to_thread
    st.session_state.switch_to_thread = None
    if tid != st.session_state.thread_id:
        st.session_state.thread_id = tid
        st.session_state.messages = load_thread_messages(tid)
        st.rerun()

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Brand mark ──
    st.markdown("""
    <div style="
      padding: 20px 16px 14px;
      border-bottom: 1px solid rgba(8,145,178,0.14);
      display: flex; align-items: center; gap: 10px;
      direction: rtl;
    ">
      <div style="
        width: 36px; height: 36px; border-radius: 50%;
        background: linear-gradient(135deg, #0891B2, #10B981);
        display: flex; align-items: center; justify-content: center;
        font-size: 18px; flex-shrink: 0;
        box-shadow: 0 0 12px rgba(8,145,178,0.4);
      ">⚕️</div>
      <div>
        <div style="font-family:'Figtree',sans-serif; font-weight:800;
                    font-size:1rem; color:#F0F9FF; letter-spacing:-0.3px;">
          Cairo Care
        </div>
        <div style="font-family:'Noto Kufi Arabic',sans-serif; font-size:0.65rem;
                    color:#4B6480; direction:rtl;">
          سجل المحادثات
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── New chat button ──
    st.markdown('<div style="padding: 14px 14px 8px;">', unsafe_allow_html=True)
    st.markdown('<div class="sb-new-btn">', unsafe_allow_html=True)
    if st.button("＋ محادثة جديدة", key="btn_new_chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()
    st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Location Section ──
    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-label">موقعك الحالي</div>', unsafe_allow_html=True)

    curr_loc = st.session_state.user_location
    c_area = curr_loc.get("area", "المعادي")
    c_src = curr_loc.get("source", "افتراضي")
    c_lat = curr_loc.get("lat", 0.0)
    c_lon = curr_loc.get("lon", 0.0)

    st.markdown(f"""
    <div class="sb-loc-card">
      <div class="sb-loc-title">
        <span>📍 {c_area}</span>
        <span style="font-size:0.65rem; color:#10B981; background:rgba(16,185,129,0.15); padding:2px 8px; border-radius:10px;">{c_src}</span>
      </div>
      <div class="sb-loc-sub">{curr_loc.get('display_name', '')[:48]}</div>
      <div class="sb-loc-coords">Lat: {c_lat:.4f}, Lon: {c_lon:.4f}</div>
    </div>
    """, unsafe_allow_html=True)

    preset_keys = list(CAIRO_DISTRICT_PRESETS.keys())
    cur_idx = preset_keys.index(c_area) if c_area in preset_keys else 0

    st.markdown('<div style="padding: 0 14px 6px;">', unsafe_allow_html=True)
    new_area = st.selectbox(
        "تغيير المنطقة يدوياً:",
        options=preset_keys,
        index=cur_idx,
        key="sb_district_select",
        label_visibility="collapsed",
    )
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        if st.button("تأكيد المنطقة", key="btn_apply_area", use_container_width=True):
            preset = CAIRO_DISTRICT_PRESETS[new_area]
            st.session_state.user_location = {
                "lat": preset["lat"],
                "lon": preset["lon"],
                "area": new_area,
                "area_slug": preset["area_slug"],
                "display_name": preset["display_name"],
                "source": "يدوي",
            }
            st.rerun()
    with col_l2:
        if st.button("📡 تحديث تلقائي", key="btn_req_gps", use_container_width=True):
            st.session_state.user_location = fetch_initial_location()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Thread list ──
    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-label">المحادثات السابقة</div>', unsafe_allow_html=True)

    threads = fetch_threads()
    active_tid = st.session_state.thread_id

    if not threads:
        st.markdown("""
        <div class="sb-empty">
          لا توجد محادثات سابقة بعد.<br>ابدأ محادثة جديدة!
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="padding: 6px 10px;">', unsafe_allow_html=True)
        for t in threads:
            tid     = t["thread_id"]
            title   = t.get("title", "محادثة")[:38] + ("…" if len(t.get("title", "")) > 38 else "")
            ts      = relative_time(t.get("created_at", ""))
            is_active = tid == active_tid
            active_cls = "active" if is_active else ""

            # Render card HTML (non-interactive display)
            st.markdown(f"""
            <div class="sb-thread {active_cls}">
              <div class="sb-thread-icon">💬</div>
              <div class="sb-thread-body">
                <div class="sb-thread-title">{title}</div>
                <div class="sb-thread-time">{ts}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Two tiny columns: switch button | delete button
            c1, c2 = st.columns([5, 1])
            with c1:
                if st.button(
                    "📂 فتح" if not is_active else "✓ نشطة",
                    key=f"open_{tid}",
                    use_container_width=True,
                    disabled=is_active,
                ):
                    st.session_state.switch_to_thread = tid
                    st.rerun()
            with c2:
                st.markdown('<div class="sb-delete-btn">', unsafe_allow_html=True)
                if st.button("🗑", key=f"del_{tid}"):
                    delete_thread_from_backend(tid)
                    if tid == active_tid:
                        st.session_state.messages = []
                        st.session_state.thread_id = str(uuid.uuid4())
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ─── HERO HEADER ─────────────────────────────────────────────────────────────
active_loc = st.session_state.user_location
area_display = active_loc.get('area', 'القاهرة')
src_display = active_loc.get('source', '')

st.markdown(f"""
<div class="cc-header">
  <div class="cc-logo-ring">
    <div class="cc-logo-icon">⚕️</div>
  </div>
  <h1 class="cc-title">Cairo Care</h1>
  <p class="cc-subtitle">مساعدك الذكي للمستشفيات والأطباء في القاهرة</p>
  <div class="cc-badges">
    <span class="cc-badge">🏥 مستشفيات القاهرة</span>
    <span class="cc-badge">🤖 ذكاء اصطناعي</span>
    <div class="cc-loc-badge">
      <span class="loc-dot"></span>
      <span>📍 موقعك: {area_display} ({src_display})</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── STATUS BAR ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="cc-status">
  <div class="cc-status-dot"></div>
  <span>المساعد متاح الآن · الموقع المعتمد: <strong>{area_display}</strong> · نموذج الذكاء الاصطناعي مُفعَّل · RAG متصل</span>
</div>
""", unsafe_allow_html=True)

# ─── QUICK-ACTION CHIPS ───────────────────────────────────────────────────────
st.markdown("""
<div class="cc-chips-wrap">
  <span class="cc-chip">🏥 مستشفى قريب</span>
  <span class="cc-chip">👨‍⚕️ أطباء القلب</span>
  <span class="cc-chip">🦷 طب أسنان</span>
  <span class="cc-chip">👁️ عيون</span>
  <span class="cc-chip">🚑 طوارئ</span>
</div>
""", unsafe_allow_html=True)

# ─── EMPTY STATE / WELCOME ────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="cc-welcome">
      <div class="cc-welcome-icon">💬</div>
      <h2>أهلاً وسهلاً في Cairo Care</h2>
      <p>
        يمكنني مساعدتك في إيجاد المستشفيات، الأطباء المتخصصين،
        والعيادات في جميع أنحاء القاهرة.
      </p>
    </div>
    <div class="cc-suggestions">
      <div class="cc-sug-card">
        <span class="sug-icon">🫀</span>
        <div class="sug-text">فين أقرب مستشفى قلب؟</div>
        <div class="sug-label">مستشفيات</div>
      </div>
      <div class="cc-sug-card">
        <span class="sug-icon">🧠</span>
        <div class="sug-text">محتاج دكتور مخ وأعصاب</div>
        <div class="sug-label">أطباء</div>
      </div>
      <div class="cc-sug-card">
        <span class="sug-icon">🔬</span>
        <div class="sug-text">أحسن معمل تحاليل في مدينة نصر</div>
        <div class="sug-label">معامل</div>
      </div>
      <div class="cc-sug-card">
        <span class="sug-icon">💊</span>
        <div class="sug-text">صيدلية 24 ساعة في المعادي</div>
        <div class="sug-label">صيدليات</div>
      </div>
      <div class="cc-sug-card">
        <span class="sug-icon">🦴</span>
        <div class="sug-text">دكتور عظام في الزمالك</div>
        <div class="sug-label">تخصصات</div>
      </div>
      <div class="cc-sug-card">
        <span class="sug-icon">🌡️</span>
        <div class="sug-text">حجز موعد أشعة مقطعية</div>
        <div class="sug-label">أشعة</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─── CHAT MESSAGES ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─── CHAT INPUT ───────────────────────────────────────────────────────────────
if prompt := st.chat_input("اكتب رسالتك هنا... (مثال: فين مستشفى قلب؟)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        api_url = "http://localhost:8000/chat"
        payload = {
            "message": prompt,
            "thread_id": st.session_state.thread_id,
            "user_location": st.session_state.user_location,
        }

        try:
            with requests.post(api_url, json=payload, stream=True) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        if decoded_line.startswith("data: "):
                            json_str = decoded_line[6:]
                            if json_str == "[DONE]":
                                break
                            try:
                                data = json.loads(json_str)
                                if "error" in data:
                                    full_response = f"⚠️ حدث خطأ: {data['error']}"
                                    break
                                full_response += data.get("token", data.get("content", ""))
                                message_placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                pass
                message_placeholder.markdown(full_response)
        except Exception as e:
            full_response = f"⚠️ خطأ في الاتصال بالسيرفر: {e}"
            message_placeholder.error(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    # After sending a message, sidebar thread list will auto-update on rerun
    st.rerun()