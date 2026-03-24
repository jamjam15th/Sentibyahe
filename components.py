# components.py
import streamlit as st
from servqual_utils import SERVQUAL_DIMENSIONS

def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Mulish:wght@300;400;500;600;700&display=swap');

:root {
  --gold:   rgb(255, 197, 112);
  --steel:  rgb(84, 119, 146);
  --navy:   rgb(26, 50, 99);
  --navydk: rgb(18, 34, 68);
  --off:    #f0f4f8;
  --muted:  rgb(120, 148, 172);
  --bdr:    rgba(84,119,146,0.2);
  --card:   #ffffff;
  --danger: #b03a2e;
  --tangibles:      #4a7c59;
  --reliability:    #1a5276;
  --responsiveness: #6c3483;
  --assurance:      #7d6608;
  --empathy:        #922b21;
}

*, *::before, *::after { box-sizing: border-box; }
html, body, p, div, span, a, button, label, input, textarea, select { font-family: 'Mulish', sans-serif !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"] { background: var(--off) !important; }
.block-container { max-width: 860px !important; padding: 2rem 1.2rem 5rem !important; }
#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }

/* ── HEADER ── */
.gf-header {
  background: var(--card); border: 1px solid var(--bdr);
  border-top: 10px solid var(--navy); border-radius: 10px;
  padding: 1.8rem 2rem; margin-bottom: 1rem;
}
.gf-header h1 {
  font-family: 'Libre Baskerville', serif !important;
  font-size: 1.8rem !important; font-weight: 700 !important;
  color: var(--navy) !important; margin: 0 0 .8rem !important;
}

/* ── LINK CARD ── */
.link-card {
  background: rgba(26,50,99,0.04); border: 1px solid var(--bdr);
  border-left: 4px solid var(--navy); border-radius: 8px;
  padding: 1rem 1.4rem; margin-top: 1rem; margin-bottom: 1rem;
}
.link-card .link-label { font-size: .62rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: var(--steel); display: block; margin-bottom: .35rem; }
.link-card a { font-size: .85rem; font-weight: 600; color: var(--navy); word-break: break-all; text-decoration: none; border-bottom: 1.5px solid rgba(26,50,99,0.25); }
.link-card a:hover { border-bottom-color: var(--navy); }
.link-card .link-hint { font-size: .7rem; color: var(--muted); margin-top: .3rem; display: block; }

.section-head { font-family: 'Libre Baskerville', serif !important; font-size: 1rem !important; font-weight: 700 !important; color: var(--navy) !important; margin: 1.4rem 0 .7rem !important; padding-bottom: .35rem !important; border-bottom: 2px solid rgba(26,50,99,0.1) !important; display: flex; align-items: center; justify-content: space-between; }
.dim-group-header { font-size: .85rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--steel); margin: 1.8rem 0 .5rem; padding-left: .5rem; }

/* ── QUESTION CARDS ── */
.gf-q-card {
  background: var(--card); border: 1px solid var(--bdr);
  border-radius: 8px; border-left: 4px solid var(--navy);
  padding: 1.3rem 1.5rem; margin-bottom: .4rem; transition: box-shadow .2s;
}
.gf-q-card.dim-tangibles      { border-left-color: var(--tangibles); }
.gf-q-card.dim-reliability    { border-left-color: var(--reliability); }
.gf-q-card.dim-responsiveness { border-left-color: var(--responsiveness); }
.gf-q-card.dim-assurance      { border-left-color: var(--assurance); }
.gf-q-card.dim-empathy        { border-left-color: var(--empathy); }

.gf-q-num { font-size: .6rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); margin-bottom: .45rem; display: block; }
.gf-q-prompt { font-size: .97rem; font-weight: 600; color: var(--navy); margin-bottom: .7rem; line-height: 1.4; }
.gf-q-meta { display: flex; gap: .4rem; align-items: center; flex-wrap: wrap; margin-top: .5rem; }

.q-badge { font-size: .57rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; padding: .1rem .45rem; border-radius: 999px; background: rgba(26,50,99,0.08); color: var(--navy); }
.q-badge.required  { background: rgba(176,58,46,0.1); color: var(--danger); }
.q-badge.demo      { background: rgba(255,197,112,0.22); color: var(--navydk); }

/* ── PREVIEW WIDGETS ── */
.gf-preview-input { width: 100%; border: none; border-bottom: 1.5px solid rgba(84,119,146,0.3); background: transparent; font-size: .88rem; color: var(--muted); padding: .35rem 0; outline: none; pointer-events: none; }
.gf-preview-textarea { width: 100%; border: none; border-bottom: 1.5px solid rgba(84,119,146,0.3); background: transparent; font-size: .88rem; color: var(--muted); padding: .35rem 0; outline: none; resize: none; pointer-events: none; height: 52px; }
.gf-radio-opt { display: flex; align-items: center; gap: .6rem; padding: .4rem .6rem; border-radius: 5px; font-size: .88rem; color: var(--steel); border: 1px solid var(--bdr); margin-bottom: .3rem; }
.gf-radio-dot { width: 14px; height: 14px; border-radius: 50%; border: 2px solid var(--steel); flex-shrink: 0; }
.gf-rating-row { display: flex; gap: .4rem; margin-top: .3rem; }
.gf-rating-pip { flex: 1; text-align: center; padding: .5rem .2rem; border: 1px solid var(--bdr); border-radius: 5px; font-size: .75rem; color: var(--muted); font-weight: 600; }

/* ── INPUTS (global) ── */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { background: #ffffff !important; color: var(--navy) !important; border: 1.5px solid var(--bdr) !important; border-radius: 6px !important; font-size: .9rem !important; padding: .42rem .75rem !important; }
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color: var(--navy) !important; box-shadow: 0 0 0 3px rgba(26,50,99,0.08) !important; }
[data-testid="stTextInput"] label, [data-testid="stTextArea"] label, [data-testid="stSelectbox"] label, [data-testid="stNumberInput"] label { font-size: .67rem !important; font-weight: 700 !important; letter-spacing: .1em !important; text-transform: uppercase !important; color: var(--steel) !important; }
[data-testid="stSelectbox"] > div > div { background: #ffffff !important; border: 1.5px solid var(--bdr) !important; border-radius: 6px !important; color: var(--navy) !important; }
[data-testid="stCheckbox"] label { font-size: .82rem !important; color: var(--navy) !important; font-weight: 600 !important; }

/* ── BUTTONS ── */
div.stButton > button { background: var(--navy) !important; color: var(--gold) !important; border: none !important; border-radius: 6px !important; font-size: .72rem !important; font-weight: 700 !important; letter-spacing: .1em !important; text-transform: uppercase !important; padding: .46rem 1.1rem !important; box-shadow: 0 2px 8px rgba(26,50,99,0.16) !important; transition: background .2s, transform .15s !important; }
div.stButton > button:hover { background: var(--navydk) !important; transform: translateY(-1px) !important; }
[data-testid="stButton"] button[kind="secondary"] { background: transparent !important; color: var(--navy) !important; border: 1px solid rgba(26,50,99,0.3) !important; box-shadow: none !important; }
[data-testid="stButton"] button[kind="secondary"]:hover { background: rgba(26,50,99,0.06) !important; transform: none !important; }

/* ── MISC ── */
[data-testid="stAlert"] { border-radius: 8px !important; font-size: .85rem !important; }
.gf-empty { background: var(--card); border: 1.5px dashed var(--bdr); border-radius: 8px; padding: 3rem 2rem; text-align: center; color: var(--muted); font-size: .88rem; }
.preview-mode-banner { background: rgba(26,50,99,0.06); border: 1px solid var(--bdr); border-radius: 8px; padding: .7rem 1.2rem; margin-bottom: 1rem; font-size: .8rem; color: var(--steel); text-align: center; font-weight: 600; }

.sq-dim-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px,1fr)); gap: .65rem; margin-top: .5rem;}
.sq-dim-card { border-radius: 8px; padding: .9rem 1.1rem; border: 2px solid transparent; background: #fff;}
.sq-dim-card.tangibles      { border-color: rgba(74,124,89,0.25); }
.sq-dim-card.reliability    { border-color: rgba(26,82,118,0.25); }
.sq-dim-card.responsiveness { border-color: rgba(108,52,131,0.25); }
.sq-dim-card.assurance      { border-color: rgba(125,102,8,0.25); }
.sq-dim-card.empathy        { border-color: rgba(146,43,33,0.25); }
.sq-dim-icon { font-size: 1.3rem; margin-bottom: .35rem; }
.sq-dim-name { font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; margin-bottom: .2rem; color: var(--navy); }
.sq-dim-desc { font-size: .71rem; color: var(--steel); line-height: 1.45; }
</style>
""", unsafe_allow_html=True)

def section_head(label: str, right: str = ""):
    right_html = f'<span style="font-size:.78rem;font-weight:400;color:var(--muted);">{right}</span>' if right else ""
    st.markdown(f'<div class="section-head">{label}{right_html}</div>', unsafe_allow_html=True)

def _rating_pips(label1="Poor", label5="Great"):
    pips = "".join([
        f'<div class="gf-rating-pip">{n}<br>'
        f'<span style="font-size:.6rem;font-weight:400;">'
        f'{"" if n not in (1, 5) else (label1 if n == 1 else label5)}'
        f'</span></div>'
        for n in range(1, 6)
    ])
    return f'<div class="gf-rating-row">{pips}</div>'

def render_question_preview(q: dict, index: int, preview_mode: bool = False):
    q_type   = q["q_type"]
    dim      = q.get("servqual_dimension") or ""
    dim_key  = dim.lower() if dim else ""
    dim_class = f"dim-{dim_key}" if dim_key else ""

    req_badge  = '<span class="q-badge required">Required</span>' if q.get("is_required") else ""
    demo_badge = '<span class="q-badge demo">👥 Demographic</span>' if q.get("is_demographic") else ""

    if q_type == "Short Answer":
        preview = '<input class="gf-preview-input" placeholder="Short answer text" disabled />'
    elif q_type == "Paragraph":
        preview = '<textarea class="gf-preview-textarea" placeholder="Long answer text" disabled></textarea>'
    elif q_type == "Multiple Choice":
        opts = q.get("options") or ["Option 1"]
        preview = "".join([f'<div class="gf-radio-opt"><div class="gf-radio-dot"></div>{o}</div>' for o in opts])
    elif q_type == "Rating (1-5)":
        preview = _rating_pips()
    else:
        preview = ""

    st.markdown(f"""
<div class="gf-q-card {dim_class}">
  <span class="gf-q-num">Question {index + 1} · {q_type}</span>
  <div class="gf-q-prompt">{q['prompt']}</div>
  {preview}
  <div class="gf-q-meta">{req_badge}{demo_badge}</div>
</div>
""", unsafe_allow_html=True)

def render_dimension_cards():
    html = '<div class="sq-dim-grid">'
    for dname, d in SERVQUAL_DIMENSIONS.items():
        html += f"""
<div class="sq-dim-card {d['key']}">
  <div class="sq-dim-icon">{d['icon']}</div>
  <div class="sq-dim-name">{dname}</div>
  <div class="sq-dim-desc">{d['desc']}</div>
</div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)