import streamlit as st
import hashlib
from st_supabase_connection import SupabaseConnection

# ── STYLING ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Mulish:wght@300;400;500;600;700&display=swap');

:root {
  --gold:   rgb(255, 197, 112);
  --sand:   rgb(239, 210, 176);
  --steel:  rgb(84, 119, 146);
  --navy:   rgb(26, 50, 99);
  --navydk: rgb(18, 34, 68);
  --off:    #f0f4f8;
  --muted:  rgb(120, 148, 172);
  --bdr:    rgba(84,119,146,0.2);
  --card:   #ffffff;
}

*, *::before, *::after { box-sizing: border-box; }
html, body, p, div, span, a, button, label, input, textarea, select {
  font-family: 'Mulish', sans-serif !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: var(--off) !important; }

.block-container { max-width: 760px !important; padding: 2rem 1.2rem 5rem !important; }

#MainMenu, footer, header,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── HEADER CARD ── */
.gf-header {
  background: var(--card); border: 1px solid var(--bdr);
  border-top: 10px solid var(--navy); border-radius: 10px;
  padding: 1.8rem 2rem; margin-bottom: 1rem;
}
.gf-header h1 {
  font-family: 'Libre Baskerville', serif !important;
  font-size: 1.6rem !important; font-weight: 700 !important;
  color: var(--navy) !important; margin: 0 0 .3rem !important;
}
.gf-header .subtitle { font-size: .82rem; color: var(--steel); margin: 0; }

/* ── LINK CARD ── */
.link-card {
  background: rgba(26,50,99,0.04); border: 1px solid var(--bdr);
  border-left: 4px solid var(--navy); border-radius: 8px;
  padding: 1rem 1.4rem; margin-top: 1rem;
}
.link-card .link-label {
  font-size: .62rem; font-weight: 700; letter-spacing: .14em;
  text-transform: uppercase; color: var(--steel); display: block; margin-bottom: .35rem;
}
.link-card a {
  font-size: .85rem; font-weight: 600; color: var(--navy);
  word-break: break-all; text-decoration: none;
  border-bottom: 1.5px solid rgba(26,50,99,0.25);
}
.link-card a:hover { border-bottom-color: var(--navy); }
.link-card .link-hint { font-size: .7rem; color: var(--muted); margin-top: .3rem; display: block; }

/* ── SECTION HEAD ── */
.section-head {
  font-family: 'Libre Baskerville', serif !important;
  font-size: 1rem !important; font-weight: 700 !important;
  color: var(--navy) !important; margin: 1.4rem 0 .7rem !important;
  padding-bottom: .35rem !important;
  border-bottom: 2px solid rgba(26,50,99,0.1) !important;
  display: flex; align-items: center; justify-content: space-between;
}

/* ── QUESTION CARDS ── */
.gf-q-card {
  background: var(--card); border: 1px solid var(--bdr);
  border-radius: 8px; border-left: 4px solid transparent;
  padding: 1.4rem 1.6rem; margin-bottom: .75rem;
  transition: border-left-color .2s, box-shadow .2s;
}
.gf-q-card.active {
  border-left-color: var(--navy);
  box-shadow: 0 3px 14px rgba(26,50,99,0.1);
}
.gf-q-num {
  font-size: .62rem; font-weight: 700; letter-spacing: .1em;
  text-transform: uppercase; color: var(--muted); margin-bottom: .5rem; display: block;
}
.gf-q-prompt {
  font-size: 1rem; font-weight: 600; color: var(--navy);
  margin-bottom: .8rem; line-height: 1.4;
}
.gf-q-meta { display: flex; gap: .45rem; align-items: center; flex-wrap: wrap; margin-top: .5rem; }
.q-badge {
  font-size: .58rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;
  padding: .12rem .5rem; border-radius: 999px;
  background: rgba(26,50,99,0.08); color: var(--navy);
}
.q-badge.demo { background: rgba(255,197,112,0.22); color: var(--navydk); }

/* ── PREVIEW WIDGETS ── */
.gf-preview-input {
  width: 100%; border: none; border-bottom: 1.5px solid rgba(84,119,146,0.3);
  background: transparent; font-size: .88rem; color: var(--muted);
  padding: .35rem 0; outline: none; font-family: 'Mulish', sans-serif;
  pointer-events: none;
}
.gf-preview-textarea {
  width: 100%; border: none; border-bottom: 1.5px solid rgba(84,119,146,0.3);
  background: transparent; font-size: .88rem; color: var(--muted);
  padding: .35rem 0; outline: none; font-family: 'Mulish', sans-serif;
  resize: none; pointer-events: none; height: 52px;
}
.gf-radio-opt {
  display: flex; align-items: center; gap: .6rem;
  padding: .4rem .6rem; border-radius: 5px; font-size: .88rem; color: var(--steel);
  border: 1px solid var(--bdr); margin-bottom: .3rem;
}
.gf-radio-dot {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid var(--steel); flex-shrink: 0;
}
.gf-rating-row { display: flex; gap: .4rem; margin-top: .3rem; }
.gf-rating-pip {
  flex: 1; text-align: center; padding: .5rem .2rem;
  border: 1px solid var(--bdr); border-radius: 5px;
  font-size: .75rem; color: var(--muted); font-weight: 600;
}

/* ── ADD QUESTION CARD ── */
.add-q-card {
  background: var(--card); border: 1.5px dashed var(--bdr);
  border-radius: 8px; padding: 1.4rem 1.6rem; margin-bottom: .75rem;
}

/* ── INPUTS ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
  background: #ffffff !important; color: var(--navy) !important;
  border: 1.5px solid var(--bdr) !important; border-radius: 6px !important;
  font-size: .9rem !important; padding: .42rem .75rem !important;
  transition: border-color .2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-color: var(--navy) !important;
  box-shadow: 0 0 0 3px rgba(26,50,99,0.08) !important;
}
[data-testid="stTextInput"] label, [data-testid="stTextArea"] label {
  font-size: .68rem !important; font-weight: 700 !important;
  letter-spacing: .1em !important; text-transform: uppercase !important;
  color: var(--steel) !important;
}
[data-testid="stSelectbox"] > div > div {
  background: #ffffff !important; border: 1.5px solid var(--bdr) !important;
  border-radius: 6px !important; color: var(--navy) !important;
}
[data-testid="stSelectbox"] label {
  font-size: .68rem !important; font-weight: 700 !important;
  letter-spacing: .1em !important; text-transform: uppercase !important;
  color: var(--steel) !important;
}
[data-testid="stCheckbox"] label {
  font-size: .82rem !important; color: var(--navy) !important; font-weight: 600 !important;
}

/* ── BUTTONS ── */
div.stButton > button {
  background: var(--navy) !important; color: var(--gold) !important;
  border: none !important; border-radius: 6px !important;
  font-size: .73rem !important; font-weight: 700 !important;
  letter-spacing: .1em !important; text-transform: uppercase !important;
  padding: .48rem 1.2rem !important;
  box-shadow: 0 2px 8px rgba(26,50,99,0.16) !important;
  transition: background .2s, transform .15s !important;
}
div.stButton > button:hover {
  background: var(--navydk) !important; transform: translateY(-1px) !important;
}
[data-testid="stButton"] button[kind="secondary"] {
  background: transparent !important; color: #b03a2e !important;
  border: 1px solid rgba(176,58,46,0.3) !important;
  box-shadow: none !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover {
  background: rgba(176,58,46,0.06) !important; transform: none !important;
}

/* ── ALERT ── */
[data-testid="stAlert"] { border-radius: 8px !important; font-size: .85rem !important; }

/* ── EMPTY STATE ── */
.gf-empty {
  background: var(--card); border: 1.5px dashed var(--bdr); border-radius: 8px;
  padding: 3rem 2rem; text-align: center; color: var(--muted); font-size: .88rem;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# SETUP
# ══════════════════════════════════════════
conn = st.connection("supabase", type=SupabaseConnection)
admin_email = st.session_state.user_email
public_id = hashlib.md5(admin_email.encode()).hexdigest()[:12]

try:
    host = st.context.headers.get("Host")
    protocol = "https" if "localhost" not in host else "http"
    base_url = f"{protocol}://{host}"
except Exception:
    base_url = "http://localhost:8501"

shareable_link = f"{base_url}/?form_id={public_id}"

def fetch_my_questions():
    try:
        res = (conn.client.table("form_questions")
               .select("*")
               .eq("admin_email", admin_email)
               .order("id")
               .execute())
        return res.data
    except Exception:
        return []

def render_question_preview(q, i):
    q_type = q["q_type"]
    demo_badge = '<span class="q-badge demo">👥 Demographic</span>' if q.get("is_demographic") else ""

    if q_type == "Short Answer":
        preview = '<input class="gf-preview-input" placeholder="Short answer text" disabled />'
    elif q_type == "Paragraph":
        preview = '<textarea class="gf-preview-textarea" placeholder="Long answer text" disabled></textarea>'
    elif q_type == "Multiple Choice":
        opts = q.get("options") or ["Option 1"]
        preview = "".join([
            f'<div class="gf-radio-opt"><div class="gf-radio-dot"></div>{o}</div>'
            for o in opts
        ])
    elif q_type == "Rating (1-5)":
        pips = "".join([
            f'<div class="gf-rating-pip">{n}<br>'
            f'<span style="font-size:.62rem;font-weight:400;">{"Poor" if n==1 else "Great" if n==5 else ""}</span></div>'
            for n in range(1, 6)
        ])
        preview = f'<div class="gf-rating-row">{pips}</div>'
    else:
        preview = ""

    st.markdown(f"""
    <div class="gf-q-card active">
      <span class="gf-q-num">Question {i+1} · {q_type}</span>
      <div class="gf-q-prompt">{q['prompt']}</div>
      {preview}
      <div class="gf-q-meta">
        <span class="q-badge">{q_type}</span>
        {demo_badge}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════
form_schema = fetch_my_questions()

# ── HEADER ──
st.markdown(f"""
<div class="gf-header">
  <h1>🛠️ Form Builder</h1>
  <p class="subtitle">Build your commuter survey — questions appear as a live preview below.</p>
  <div class="link-card">
    <span class="link-label">🔗 Your unique survey link</span>
    <a href="{shareable_link}" target="_blank">{shareable_link}</a>
    <span class="link-hint">Copy and share this with your commuters</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── ADD QUESTION CARD (top, like Google Forms) ──
st.markdown('<div class="section-head">➕ Add a Question</div>', unsafe_allow_html=True)
st.markdown('<div class="add-q-card">', unsafe_allow_html=True)

col1, col2 = st.columns([3, 2])
with col1:
    new_prompt = st.text_input("Question text", placeholder="e.g. How was the driver's behavior?")
with col2:
    q_type = st.selectbox("Question type", ["Short Answer", "Paragraph", "Multiple Choice", "Rating (1-5)"])

new_options = []
if q_type == "Multiple Choice":
    opts_raw = st.text_input("Options (comma-separated)", placeholder="e.g. Good, Okay, Bad")
    if opts_raw:
        new_options = [o.strip() for o in opts_raw.split(",")]

col_chk, col_btn = st.columns([3, 1])
with col_chk:
    is_demographic = st.checkbox("👥 Mark as demographic question")
with col_btn:
    st.markdown("<div style='margin-top:1.75rem;'></div>", unsafe_allow_html=True)
    add_clicked = st.button("Add Question", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

if add_clicked:
    if new_prompt.strip():
        conn.client.table("form_questions").insert({
            "prompt": new_prompt.strip(),
            "q_type": q_type,
            "options": new_options,
            "is_demographic": is_demographic,
            "admin_email": admin_email,
            "public_id": public_id
        }).execute()
        st.rerun()
    else:
        st.warning("⚠️ Please enter a question first.")

# ── QUESTIONS PREVIEW LIST (below add card) ──
total = len(form_schema)
st.markdown(
    f'<div class="section-head">'
    f'Your Form'
    f'<span style="font-size:.8rem;font-weight:400;color:var(--muted);">'
    f'{total} question{"s" if total != 1 else ""}'
    f'</span></div>',
    unsafe_allow_html=True
)

if total == 0:
    st.markdown(
        '<div class="gf-empty">📋 No questions yet — add your first one above.</div>',
        unsafe_allow_html=True
    )
else:
    for i, q in enumerate(form_schema):
        render_question_preview(q, i)
        _, col_del = st.columns([5, 1])
        with col_del:
            if st.button("🗑 Delete", key=f"del_{q['id']}", type="secondary"):
                conn.client.table("form_questions").delete().eq("id", q["id"]).execute()
                st.rerun()