import hashlib
import html
import time
import uuid
import streamlit as st
from st_supabase_connection import SupabaseConnection
from streamlit_extras.stylable_container import stylable_container

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Take Survey — Land public transportation",
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
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] {
    display: flex !important;
    flex-direction: row !important;
    width: 100% !important;
    gap: 12px !important;
    flex-wrap: nowrap !important;
}
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] > label,
[data-testid="stRadio"] div[aria-orientation="horizontal"] > label {
    flex: 1 1 0 !important;
    height: 52px !important;
    min-width: 0 !important;
    background: #ffffff !important;
    border: 1px solid #c9d5ea !important;
    border-radius: 6px !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    cursor: pointer !important;
    transition: all .15s ease !important;
    position: relative !important;
}
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] > label > div:first-child,
[data-testid="stRadio"] div[aria-orientation="horizontal"] > label > div:first-child {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
    pointer-events: none !important;
}
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] > label p,
[data-testid="stRadio"] div[aria-orientation="horizontal"] > label p {
    color: #2f4fd1 !important;
    font-weight: 600 !important;
    font-size: .98rem !important;
    margin: 0 !important;
    padding: 0 !important;
    text-align: center !important;
    line-height: 1 !important;
}
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] > label:hover,
[data-testid="stRadio"] div[aria-orientation="horizontal"] > label:hover {
    border-color: #9fb2dc !important;
    background: #f8faff !important;
}
[data-testid="stRadio"] div[role="radiogroup"][aria-orientation="horizontal"] > label:has(input:checked),
[data-testid="stRadio"] div[aria-orientation="horizontal"] > label:has(input:checked) {
    border-color: #2f4fd1 !important;
    background: #eef3ff !important;
    box-shadow: 0 0 0 1px #2f4fd1 !important;
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
    form_meta = meta_res.data[0] if meta_res.data else {
        "title": "Land public transportation survey",
        "description": "",
        "include_demographics": False,
        "allow_multiple_responses": True,
        "reach_out_contact": "",
    }
    q_res = conn.client.table("form_questions").select("*").eq("public_id", target_form_id).order("sort_order").execute()
    custom_questions = q_res.data or []
except Exception:
    st.stop()

# Stable browser-tab id in URL so "one response" survives reload (not just session_state).
client_cid = None
if not is_preview:
    qp = st.query_params
    if "cid" not in qp or not str(qp.get("cid", "")).strip():
        qp["cid"] = str(uuid.uuid4())
        st.rerun()
    client_cid = str(qp["cid"]).strip()


def _already_submitted_for_client(public_id: str, cid: str) -> bool:
    if not cid:
        return False
    try:
        r = conn.client.rpc(
            "has_form_submission",
            {"p_public_id": public_id, "p_client_id": cid},
        ).execute()
        if r.data is True or r.data is False:
            return bool(r.data)
        if isinstance(r.data, list) and len(r.data) > 0:
            return bool(r.data[0])
    except Exception:
        pass
    try:
        chk = (
            conn.client.table("form_responses")
            .select("id")
            .eq("public_id", public_id)
            .eq("client_submission_id", cid)
            .limit(1)
            .execute()
        )
        return bool(chk.data)
    except Exception:
        return False


# ── 2. SCHEMA ──
LPT_TRANSPORT_MODE_OPTIONS = [
    "Jeepney",
    "Modern jeepney / E-jeep",
    "Ordinary bus",
    "Air-conditioned bus",
    "UV Express",
    "Van pool (UV-style)",
    "Tricycle",
    "Motorcycle taxi (habal-habal)",
    "Train (MRT / LRT / PNR)",
    "Taxi",
    "TNVS (Grab, etc.)",
    "Ferry / boat",
    "Walking / cycling",
    "Company or school service",
    "Private car (as passenger)",
    "Other",
]

STANDARD_DEMO_QUESTIONS = [
    {"prompt": "What is your age bracket?", "q_type": "Multiple Choice", "options": ["18-24", "25-34", "35-44", "45-54", "55 and above"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {"prompt": "What is your gender?", "q_type": "Multiple Choice", "options": ["Male", "Female", "Prefer not to say"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {"prompt": "What is your primary occupation?", "q_type": "Multiple Choice", "options": ["Student", "Employed", "Self-employed", "Unemployed", "Retired"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
    {
        "prompt": "Which land public transportation modes do you usually use? (Select all that apply)",
        "q_type": "Multiple Select",
        "options": LPT_TRANSPORT_MODE_OPTIONS,
        "is_required": True,
        "servqual_dimension": "Commuter Profile",
        "is_demographic": True,
    },
    {"prompt": "How often do you commute?", "q_type": "Multiple Choice", "options": ["Daily", "3-4 times a week", "1-2 times a week", "Rarely"], "is_required": True, "servqual_dimension": "Commuter Profile", "is_demographic": True},
]

form_schema = []
if form_meta.get("include_demographics", False):
    form_schema.extend(STANDARD_DEMO_QUESTIONS)
form_schema.extend(custom_questions)

allow_multiple_responses = form_meta.get("allow_multiple_responses", True)


def _render_reach_out_contact():
    txt = (form_meta.get("reach_out_contact") or "").strip()
    if not txt:
        return
    safe = html.escape(txt)
    st.markdown(
        f"""
        <div style="margin-top:1rem;padding:12px 14px;border-radius:8px;background:rgba(26,50,99,0.06);border:1px solid rgba(26,50,99,0.12);">
          <div style="font-size:.7rem;font-weight:800;color:rgb(26,50,99);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;">How to reach us</div>
          <div style="font-size:.9rem;color:rgb(60,85,120);white-space:pre-wrap;">{safe}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
submitted_key = f"submitted_once_{target_form_id}"
just_submitted_key = f"just_submitted_{target_form_id}"
form_ready_key = f"form_ready_{target_form_id}"
if submitted_key not in st.session_state:
    st.session_state[submitted_key] = False
if just_submitted_key not in st.session_state:
    st.session_state[just_submitted_key] = False
if form_ready_key not in st.session_state:
    st.session_state[form_ready_key] = False

if not st.session_state[form_ready_key]:
    with st.spinner("Loading full survey form..."):
        # Keep loader visible long enough so users can perceive it.
        time.sleep(0.8)
        st.session_state[form_ready_key] = True
    st.rerun()

# ── 3. HEADER ──
st.markdown(f"""
<div class="gf-header">
  <div class="badge">🚌 Land public transportation feedback</div>
  <h1 style="color:var(--navy);">{form_meta.get('title')}</h1>
  <p class="desc">{form_meta.get('description')}</p>
</div>
""", unsafe_allow_html=True)

# ── 4. FORM ──
locked_one_response = (
    (not allow_multiple_responses)
    and (not is_preview)
    and client_cid
    and _already_submitted_for_client(target_form_id, client_cid)
)

if allow_multiple_responses and st.session_state.get(just_submitted_key):
    st.success("✅ Response submitted successfully.")
    st.info("Thank you for your feedback.")
    _render_reach_out_contact()
    if st.button("Submit another response", type="secondary", key=f"submit_again_{target_form_id}"):
        st.session_state[just_submitted_key] = False
        st.session_state[form_ready_key] = False
        st.rerun()
elif (not allow_multiple_responses) and (
    locked_one_response or st.session_state.get(submitted_key)
):
    st.success("✅ Thank you — we have already received your response.")
    st.info("This survey allows only one submission per device.")
    _render_reach_out_contact()
    if not (form_meta.get("reach_out_contact") or "").strip():
        st.info("If you need to follow up, please contact the survey organizer.")
elif len(form_schema) > 0:
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
                "Multiple Select":  "☑️ Multiple Select",
                "Rating (Likert)":  "⭐ Likert",
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
                    ans_mc = st.radio(
                        prompt,
                        q.get("options", []),
                        key=key,
                        index=None,
                        label_visibility="collapsed",
                    )
                    user_answers[unique_prompt] = ans_mc
                elif q_type == "Multiple Select":
                    opts = q.get("options") or []
                    picked = []
                    st.markdown(
                        "<div style='font-size:0.8rem;color:#7c8db5;margin:0 0 6px 0;'>Select all that apply.</div>",
                        unsafe_allow_html=True,
                    )
                    for j, opt in enumerate(opts):
                        if st.checkbox(opt, key=f"{key}_ms_{j}", label_visibility="visible"):
                            picked.append(opt)
                    user_answers[unique_prompt] = picked
                elif q_type in ("Rating (Likert)", "Rating (1-5)"):
                    scale_max = int(q.get("scale_max") or 5)
                    lbl_low  = q.get("scale_label_low", "")
                    lbl_high = q.get("scale_label_high", "")
                    ans_likert = st.radio(
                        prompt,
                        [str(x) for x in range(1, scale_max + 1)],
                        key=key,
                        index=None,
                        horizontal=True,
                        label_visibility="collapsed",
                    )
                    user_answers[unique_prompt] = ans_likert
                    if lbl_low or lbl_high:
                        lbl_cols = st.columns(scale_max)
                        with lbl_cols[0]:
                            st.markdown(
                                f"<div style='font-size:11px;color:#7c8db5;font-weight:600;text-align:left;line-height:1.2;'>{lbl_low}</div>",
                                unsafe_allow_html=True,
                            )
                        with lbl_cols[-1]:
                            st.markdown(
                                f"<div style='font-size:11px;color:#7c8db5;font-weight:600;text-align:right;line-height:1.2;'>{lbl_high}</div>",
                                unsafe_allow_html=True,
                            )

        if st.form_submit_button("Submit Response →", type="primary"):
            try:
                missing_required = []
                for uprompt, q_info in question_map.items():
                    if not q_info.get("is_required", False):
                        continue
                    ans = user_answers.get(uprompt)
                    q_type = q_info.get("q_type")
                    if q_type in ("Short Answer", "Paragraph"):
                        if ans is None or str(ans).strip() == "":
                            missing_required.append(q_info.get("prompt", uprompt))
                    elif q_type == "Multiple Select":
                        if not ans or not isinstance(ans, list) or len(ans) == 0:
                            missing_required.append(q_info.get("prompt", uprompt))
                    else:
                        if ans is None or str(ans).strip() == "":
                            missing_required.append(q_info.get("prompt", uprompt))

                if missing_required:
                    st.error("⚠️ Please answer all required questions before submitting.")
                elif (
                    (not allow_multiple_responses)
                    and (not is_preview)
                    and client_cid
                    and _already_submitted_for_client(target_form_id, client_cid)
                ):
                    st.warning("We already have a response from this session. Thank you.")
                    st.session_state[submitted_key] = True
                    st.rerun()
                else:
                    demo_answers = {}
                    raw_feedback_list = []
                    dim_scores = { "Tangibles": [], "Reliability": [], "Responsiveness": [], "Assurance": [], "Empathy": [] }
                    general_ratings = []
                    
                    for uprompt, ans in user_answers.items():
                        if ans is None:
                            continue
                        if isinstance(ans, list) and len(ans) == 0:
                            continue
                        if not isinstance(ans, list) and str(ans).strip() == "":
                            continue

                        q_info = question_map[uprompt]
                        dim = q_info.get("servqual_dimension")
                        q_type = q_info.get("q_type")

                        if dim == "Commuter Profile" or q_info.get("is_demographic"):
                            demo_answers[q_info["prompt"]] = ans
                        elif q_type in ("Rating (Likert)", "Rating (1-5)"):
                            if dim in dim_scores:
                                dim_scores[dim].append(int(ans))
                            else:
                                general_ratings.append(int(ans))
                        elif q_type in ("Short Answer", "Paragraph"):
                            raw_feedback_list.append(str(ans))

                    payload = {
                        "public_id": target_form_id,
                        "admin_email": form_meta.get("admin_email", ""),
                        **({"client_submission_id": client_cid} if client_cid else {}),
                        "answers": user_answers,
                        "demo_answers": demo_answers,
                        "raw_feedback": " | ".join(raw_feedback_list) if raw_feedback_list else None,
                        "sentiment_status": "pending",
                        "tangibles_avg": sum(dim_scores["Tangibles"])/len(dim_scores["Tangibles"]) if dim_scores["Tangibles"] else None,
                        "reliability_avg": sum(dim_scores["Reliability"])/len(dim_scores["Reliability"]) if dim_scores["Reliability"] else None,
                        "responsiveness_avg": sum(dim_scores["Responsiveness"])/len(dim_scores["Responsiveness"]) if dim_scores["Responsiveness"] else None,
                        "assurance_avg": sum(dim_scores["Assurance"])/len(dim_scores["Assurance"]) if dim_scores["Assurance"] else None,
                        "empathy_avg": sum(dim_scores["Empathy"])/len(dim_scores["Empathy"]) if dim_scores["Empathy"] else None,
                        "general_ratings_avg": sum(general_ratings)/len(general_ratings) if general_ratings else None,

                    }
                    
                    conn.client.table("form_responses").insert(payload).execute()
                    
                    st.session_state[submitted_key] = True
                    st.session_state[just_submitted_key] = True
                    st.rerun()
            except Exception as e:
                st.error(f"⚠️ Error saving response: {e}")