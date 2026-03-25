import hashlib
import streamlit as st
from st_supabase_connection import SupabaseConnection
from streamlit_extras.stylable_container import stylable_container

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Take Survey — PUV Analytics",
    page_icon="🚌",
    layout="centered",
)

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
  --bdr:    rgba(84,119,146,0.25);
  --card:   #ffffff;
}

*, *::before, *::after { box-sizing: border-box; }
html, body, p, div, span, a, button, label, input, textarea, select {
  font-family: 'Mulish', sans-serif !important;
}

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: var(--off) !important; }

.block-container {
  max-width: 760px !important;
  padding: 3rem 1.5rem 5rem !important;
}

/* ── HEADER CARD ── */
.gf-header {
  background: var(--card);
  border-radius: 12px;
  border: 1px solid var(--bdr);
  border-top: 12px solid var(--navy);
  padding: 2.5rem 2.4rem 2rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 6px rgba(26,50,99,0.04);
}
.gf-header .badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(26,50,99,0.07); border-radius: 999px;
  padding: .25rem .8rem; margin-bottom: 1.2rem;
  font-size: .65rem; font-weight: 700; letter-spacing: .12em;
  text-transform: uppercase; color: var(--navy);
}

/* ── VERTICAL RADIO (Multiple Choice) ── */
[data-testid="stRadio"] div[aria-orientation="vertical"] label div:first-child {
    border-left: none !important;
}
[data-testid="stRadio"] div[aria-orientation="vertical"] label p {
    font-size: .95rem !important; color: var(--steel) !important;
    margin-left: 8px !important;
}
[data-testid="stRadio"] div[aria-orientation="vertical"] label:has(input:checked) p {
    color: var(--navy) !important; font-weight: 600 !important;
}

/* ── HORIZONTAL RADIO (Likert Scale Squares) ── */
[data-testid="stRadio"] > div > div[aria-orientation="horizontal"] {
    display: flex !important;
    flex-direction: row !important;
    width: 100% !important;
    gap: 10px !important;
    flex-wrap: nowrap !important;
}
[data-testid="stRadio"] > div > div[aria-orientation="horizontal"] > label {
    flex: 1 1 0px !important;
    height: 56px !important;
    min-width: 0 !important;
    background: #ffffff !important;
    border: 1.5px solid #dde3ef !important;
    border-radius: 8px !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    position: relative !important;
}
[data-testid="stRadio"] > div > div[aria-orientation="horizontal"] > label > div:first-child {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
    pointer-events: none !important;
}
[data-testid="stRadio"] > div > div[aria-orientation="horizontal"] > label > div:first-child > div { display: none !important; }
[data-testid="stRadio"] > div > div[aria-orientation="horizontal"] > label > div:first-child input { display: none !important; }
[data-testid="stRadio"] > div > div[aria-orientation="horizontal"] > label p {
    color: #3b5bdb !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    margin: 0 !important;
    padding: 0 !important;
    text-align: center !important;
    line-height: 1 !important;
}
[data-testid="stRadio"] > div > div[aria-orientation="horizontal"] > label:hover {
    border-color: #3b5bdb !important;
    background: #f5f7ff !important;
}
[data-testid="stRadio"] > div > div[aria-orientation="horizontal"] > label:has(input:checked) {
    border-color: #3b5bdb !important;
    background: #eef1ff !important;
    box-shadow: 0 0 0 2px #3b5bdb !important;
}
[data-testid="stRadio"] > div > div[aria-orientation="horizontal"] > label:has(input:checked) p {
    color: #3b5bdb !important;
}

/* ── INPUTS ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
  border: none !important;
  border-bottom: 1.5px solid rgba(84,119,146,0.35) !important;
  border-radius: 0 !important;
  background: transparent !important;
}

/* ── SUBMIT BUTTON ── */
div.stFormSubmitButton > button {
  background: var(--navy) !important; color: var(--gold) !important;
  border-radius: 6px !important; padding: .65rem 2.2rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── JS: forcibly hide radio circles ──
st.markdown("""
<script>
(function() {
    const hideRadioCircles = () => {
        document.querySelectorAll(
            '[data-testid="stRadio"] div[aria-orientation="horizontal"] > label > div:first-child'
        ).forEach(el => {
            el.style.cssText = [
                'display:none!important',
                'width:0!important',
                'height:0!important',
                'overflow:hidden!important',
                'position:absolute!important',
                'pointer-events:none!important'
            ].join(';');
        });
    };
    hideRadioCircles();
    setTimeout(hideRadioCircles, 100);
    setTimeout(hideRadioCircles, 500);
    const observer = new MutationObserver(() => hideRadioCircles());
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# ── 1. FETCH LOGIC ──
is_preview = False
if st.session_state.get("logged_in") and st.session_state.get("user_email"):
    target_form_id = hashlib.md5(st.session_state.user_email.encode()).hexdigest()[:12]
    is_preview = True
else:
    query_params = st.query_params
    if "form_id" not in query_params:
        st.error("⚠️ Invalid survey link.")
        st.stop()
    target_form_id = query_params["form_id"]

try:
    meta_res = conn.client.table("form_meta").select("*").eq("public_id", target_form_id).execute()
    form_meta = meta_res.data[0] if meta_res.data else {"title": "PUV Survey", "description": "", "include_demographics": False}
    q_res = conn.client.table("form_questions").select("*").eq("public_id", target_form_id).order("sort_order").execute()
    custom_questions = q_res.data or []
except Exception:
    st.stop()

# ── 2. SCHEMA ──
STANDARD_DEMO_QUESTIONS = [
    {"prompt": "What is your age bracket?", "q_type": "Multiple Choice", "options": ["18-24","25-34","35-44","45-54","55 and above"], "is_required": True, "servqual_dimension": "Commuter Profile"},
    {"prompt": "What is your gender?", "q_type": "Multiple Choice", "options": ["Male","Female","Prefer not to say"], "is_required": True, "servqual_dimension": "Commuter Profile"},
    {"prompt": "What is your primary occupation?", "q_type": "Multiple Choice", "options": ["Student","Employed","Self-employed","Unemployed","Retired"],"is_required": True, "servqual_dimension": "Commuter Profile"},
    {"prompt": "What primary PUV type do you usually ride?", "q_type": "Multiple Choice", "options": ["Jeepney","Bus","UV Express","Tricycle","Train"],"is_required": True, "servqual_dimension": "Commuter Profile"},
    {"prompt": "How often do you commute?", "q_type": "Multiple Choice", "options": ["Daily","3-4 times a week","1-2 times a week","Rarely"], "is_required": True, "servqual_dimension": "Commuter Profile"},
]

form_schema = []
if form_meta.get("include_demographics", False):
    form_schema.extend(STANDARD_DEMO_QUESTIONS)
form_schema.extend(custom_questions)

# ── 3. HEADER ──
st.markdown(f"""
<div class="gf-header">
  <div class="badge">🚌 PUV Analytics Platform</div>
  <h1 style="color:var(--navy);">{form_meta.get('title')}</h1>
  <p class="desc">{form_meta.get('description')}</p>
</div>
""", unsafe_allow_html=True)

# ── 4. FORM ──
if len(form_schema) > 0:
    question_map = {} 
    with st.form("public_survey_form", clear_on_submit=True):
        user_answers = {}
        for i, q in enumerate(form_schema):
            q_type, prompt, is_req = q["q_type"], q["prompt"], q.get("is_required", False)
            req_star = '<span style="color:#d63031;">*</span>' if is_req else ""
            key = f"ans_{q.get('id', f'demo_{i}')}"

            unique_prompt = prompt
            counter = 1
            while unique_prompt in user_answers:
                unique_prompt = f"{prompt} ({counter})"
                counter += 1
            
            question_map[unique_prompt] = q

            q_badge = {
                "Short Answer":     "✏️ Short Answer",
                "Paragraph":        "📝 Paragraph",
                "Multiple Choice":  "☑️ Multiple Choice",
                "Rating (Likert)":  "⭐ Likert"
            }.get(q_type, q_type)

            dim = q.get("servqual_dimension")
            dim_tag = (
                f'<span style="font-size:11px;font-weight:700;padding:2px 7px;border-radius:4px;'
                f'background:#e6f7eb;color:#2a7a3b;margin-right:6px;">{dim}</span>'
            ) if dim else ""

            with stylable_container(
                key=f"q_card_{i}",
                css_styles="{ background: #fff; border: 1px solid rgba(84,119,146,0.25); border-radius: 12px; padding: 1.8rem 2rem; margin-bottom: 1rem; }"
            ):
                st.markdown(f"""
                <div style="display:flex;gap:6px;margin-bottom:8px;">
                  <span style="font-size:11px;font-weight:700;color:#7c8db5;background:#eef1fa;padding:2px 6px;border-radius:4px;">Q{i+1}</span>
                  <span style="font-size:11px;color:#5566a0;background:#f0f3ff;padding:2px 7px;border-radius:4px;">{q_badge}</span>
                  {dim_tag}
                </div>
                <div style="font-size:1.05rem;font-weight:600;color:#1a3263;margin-bottom:1.2rem;">
                  {prompt}{req_star}
                </div>
                """, unsafe_allow_html=True)

                if q_type == "Short Answer":
                    user_answers[unique_prompt] = st.text_input(prompt, key=key, placeholder="Your answer", label_visibility="collapsed")
                elif q_type == "Paragraph":
                    user_answers[unique_prompt] = st.text_area(prompt, key=key, placeholder="Your answer", label_visibility="collapsed")
                elif q_type == "Multiple Choice":
                    user_answers[unique_prompt] = st.radio(prompt, q.get("options", []), key=key, label_visibility="collapsed")
                elif q_type in ("Rating (Likert)", "Rating (1-5)"):
                    scale_max = int(q.get("scale_max") or 5)
                    lbl_low  = q.get("scale_label_low", "")
                    lbl_high = q.get("scale_label_high", "")
                    user_answers[unique_prompt] = st.radio(prompt, [str(x) for x in range(1, scale_max + 1)], key=key, horizontal=True, label_visibility="collapsed")
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;margin-top:0.4rem;padding:0 0.25rem;">
                      <span style="font-size:11px;color:#7c8db5;font-weight:600;">{lbl_low}</span>
                      <span style="font-size:11px;color:#7c8db5;font-weight:600;">{lbl_high}</span>
                    </div>
                    """, unsafe_allow_html=True)

        if st.form_submit_button("Submit Response →", type="primary"):
            try:
                demo_answers = {}
                raw_feedback_list = []
                dim_scores = { "Tangibles": [], "Reliability": [], "Responsiveness": [], "Assurance": [], "Empathy": [] }

                for uprompt, ans in user_answers.items():
                    if not ans: continue 
                    
                    q_info = question_map[uprompt]
                    dim = q_info.get("servqual_dimension")
                    q_type = q_info.get("q_type")

                    if dim == "Commuter Profile":
                        demo_answers[q_info["prompt"]] = ans
                    elif q_type in ("Rating (Likert)", "Rating (1-5)") and dim in dim_scores:
                        dim_scores[dim].append(int(ans))
                    elif q_type in ("Short Answer", "Paragraph"):
                        raw_feedback_list.append(str(ans))

                payload = {
                    "public_id": target_form_id,
                    "admin_email": form_meta.get("admin_email", ""),
                    "answers": user_answers,
                    "demo_answers": demo_answers,
                    "raw_feedback": " | ".join(raw_feedback_list) if raw_feedback_list else None,
                    "sentiment_status": "pending",
                    "tangibles_avg": sum(dim_scores["Tangibles"])/len(dim_scores["Tangibles"]) if dim_scores["Tangibles"] else None,
                    "reliability_avg": sum(dim_scores["Reliability"])/len(dim_scores["Reliability"]) if dim_scores["Reliability"] else None,
                    "responsiveness_avg": sum(dim_scores["Responsiveness"])/len(dim_scores["Responsiveness"]) if dim_scores["Responsiveness"] else None,
                    "assurance_avg": sum(dim_scores["Assurance"])/len(dim_scores["Assurance"]) if dim_scores["Assurance"] else None,
                    "empathy_avg": sum(dim_scores["Empathy"])/len(dim_scores["Empathy"]) if dim_scores["Empathy"] else None,
                }
                
                conn.client.table("form_responses").insert(payload).execute()
                
                st.success("🎉 Response submitted successfully!")
                st.balloons()
            except Exception as e:
                st.error(f"⚠️ Error saving response: {e}")