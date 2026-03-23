import streamlit as st
import hashlib
from st_supabase_connection import SupabaseConnection
from streamlit_extras.stylable_container import stylable_container # ⭐️ Added this import

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
  --off:    #f0f4f8; /* Softer background to make white cards pop */
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

/* Page Background */
[data-testid="stAppViewContainer"],
[data-testid="stMain"] { background: var(--off) !important; }

/* Google Forms Width */
.block-container {
  max-width: 760px !important;
  padding: 3rem 1.5rem 5rem !important;
}

/* ── HEADER CARD (Google Forms Style) ── */
.gf-header {
  background: var(--card);
  border-radius: 12px;
  border: 1px solid var(--bdr);
  border-top: 12px solid var(--navy); /* Classic thick top border */
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
.gf-header h1 {
  font-family: 'Libre Baskerville', serif !important;
  font-size: clamp(1.8rem, 4vw, 2.2rem) !important; font-weight: 700 !important;
  color: var(--navy) !important; margin: 0 0 .8rem !important;
  line-height: 1.25 !important;
}
.gf-header .desc {
  font-size: .95rem; color: var(--steel); line-height: 1.65; margin: 0;
}
.gf-header .preview-pill {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(255,197,112,0.18); border: 1px solid rgba(255,197,112,0.45);
  border-radius: 999px; padding: .25rem .8rem; margin-top: 1.2rem;
  font-size: .7rem; font-weight: 700; color: var(--navydk);
}

/* ── INPUTS — Google Forms underline style ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
  border: none !important;
  border-bottom: 1.5px solid rgba(84,119,146,0.35) !important;
  border-radius: 0 !important;
  background: transparent !important;
  font-size: .95rem !important;
  color: var(--navy) !important;
  padding: .5rem 0 !important;
  box-shadow: none !important;
  transition: border-color .2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
  border-bottom: 2px solid var(--navy) !important;
  box-shadow: none !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
  color: var(--muted) !important; font-size: .9rem !important;
}

/* Hide Native Labels */
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stRadio"] > label,
[data-testid="stSlider"] > label { display: none !important; }

[data-testid="stTextInput"] > div,
[data-testid="stTextArea"] > div {
  border: none !important; box-shadow: none !important; background: transparent !important;
}

/* ── RADIO ── */
[data-testid="stRadio"] > div { gap: .6rem !important; flex-direction: column !important; }
[data-testid="stRadio"] > div > label {
  display: flex !important; align-items: center !important; gap: .75rem !important;
  padding: 0 !important;
  font-size: .95rem !important; color: var(--steel) !important;
  cursor: pointer !important; background: transparent !important;
}
[data-testid="stRadio"] > div > label:has(input:checked) {
  color: var(--navy) !important; font-weight: 600 !important;
}

/* ── SLIDER ── */
[data-testid="stSlider"] { padding: .25rem 0 !important; }
[data-testid="stSlider"] > div > div > div { background: var(--navy) !important; }
.rating-labels {
  display: flex; justify-content: space-between;
  margin-top: .3rem;
}
.rating-labels span {
  font-size: .75rem; color: var(--muted); text-align: center; flex: 1;
}

/* ── SUBMIT BUTTON ── */
div.stFormSubmitButton > button {
  background: var(--navy) !important; color: var(--gold) !important;
  border: none !important; border-radius: 6px !important;
  font-size: .85rem !important; font-weight: 700 !important;
  letter-spacing: .1em !important; text-transform: uppercase !important;
  padding: .65rem 2.2rem !important; margin-top: .75rem !important;
  box-shadow: 0 3px 10px rgba(26,50,99,0.15) !important;
  transition: opacity .2s, transform .15s !important;
}
div.stFormSubmitButton > button:hover {
  opacity: 0.9 !important; transform: translateY(-1px) !important;
}

/* ── FORM CONTAINER REMOVAL ── */
/* Removes the default ugly box Streamlit puts around forms */
[data-testid="stForm"] { border: none !important; padding: 0 !important; }

/* ── FOOTER ── */
.gf-footer {
  text-align: center; margin-top: 2rem;
  font-size: .75rem; color: var(--muted); line-height: 1.8;
}
.gf-footer strong { color: var(--steel); font-weight: 700; }

/* ── EMPTY STATE ── */
.gf-empty {
  background: var(--card); border: 1px solid var(--bdr); border-radius: 12px;
  padding: 4rem 2rem; text-align: center; box-shadow: 0 2px 6px rgba(26,50,99,0.04);
}
.gf-empty h3 { color: var(--navy); margin-bottom: .5rem; }
.gf-empty p { color: var(--muted); font-size: .95rem; margin: 0; }
</style>
""", unsafe_allow_html=True)

# ── 1. DETERMINE WHICH FORM TO SHOW ──
conn = st.connection("supabase", type=SupabaseConnection)

is_preview = False
if st.session_state.get("logged_in") and st.session_state.get("user_email"):
    target_form_id = hashlib.md5(st.session_state.user_email.encode()).hexdigest()[:12]
    is_preview = True
else:
    query_params = st.query_params
    if "form_id" not in query_params:
        st.error("⚠️ Invalid survey link. Please make sure you copied the full link.")
        st.stop()
    target_form_id = query_params["form_id"]

# ── 2. FETCH QUESTIONS ──
try:
    res = conn.client.table("form_questions").select("*").eq("public_id", target_form_id).order("id").execute()
    form_schema = res.data
except Exception:
    form_schema = []

# ── 3. HEADER ──
preview_html = '<div class="preview-pill">👁 Live Preview Mode</div>' if is_preview else ""
st.markdown(f"""
<div class="gf-header">
  <div class="badge">🚌 PUV Analytics Platform</div>
  <h1>PUV Commuter Feedback</h1>
  <p class="desc">Please share your honest experience. Your feedback is completely anonymous and helps improve public transport services.</p>
  {preview_html}
</div>
""", unsafe_allow_html=True)

# ── 4. EMPTY STATE ──
if len(form_schema) == 0:
    st.markdown("""
    <div class="gf-empty">
      <h3>📋 No questions yet</h3>
      <p>This survey is currently closed or has no questions added yet.</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── 5. FORM ──
    with st.form("public_survey_form", clear_on_submit=True):
        user_answers = {}

        for i, q in enumerate(form_schema):
            q_type = q["q_type"]
            prompt = q["prompt"]
            key    = f"ans_{q['id']}"

            # ⭐️ THE MAGIC GOOGLE FORMS CARD ⭐️
            with stylable_container(
                key=f"q_card_{i}",
                css_styles="""
                    {
                        background: #ffffff;
                        border: 1px solid var(--bdr);
                        border-radius: 12px;
                        padding: 1.8rem 2rem 1.6rem;
                        margin-bottom: 1rem;
                        border-left: 5px solid transparent;
                        box-shadow: 0 2px 6px rgba(26,50,99,0.03);
                        transition: all 0.25s ease;
                    }
                    {
                        /* Focus effect: Left border highlights Navy when active */
                        &:focus-within {
                            border-left: 5px solid var(--navy);
                            box-shadow: 0 5px 15px rgba(26,50,99,0.08);
                        }
                    }
                """
            ):
                # Put the Question Text inside the Card
                st.markdown(f"""
                    <div style="font-size:1.05rem; font-weight:600; color:var(--navy); margin-bottom:1.2rem; line-height:1.4;">
                        {prompt} <span style="font-size:0.65rem; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:0.1em; float:right;">{q_type}</span>
                    </div>
                """, unsafe_allow_html=True)

                # Put the Input Widget inside the Card
                if q_type == "Short Answer":
                    user_answers[prompt] = st.text_input(
                        prompt, key=key,
                        placeholder="Your answer",
                        label_visibility="collapsed"
                    )

                elif q_type == "Paragraph":
                    user_answers[prompt] = st.text_area(
                        prompt, key=key,
                        placeholder="Your answer",
                        height=90,
                        label_visibility="collapsed"
                    )

                elif q_type == "Multiple Choice":
                    opts = q["options"] if q["options"] else ["Option 1"]
                    user_answers[prompt] = st.radio(
                        prompt, opts, key=key,
                        label_visibility="collapsed"
                    )

                elif q_type == "Rating (1-5)":
                    user_answers[prompt] = st.slider(
                        prompt, min_value=1, max_value=5, value=3,
                        key=key, label_visibility="collapsed"
                    )
                    st.markdown("""
                    <div class="rating-labels">
                      <span>1 (Poor)</span>
                      <span>2</span>
                      <span>3 (Okay)</span>
                      <span>4</span>
                      <span>5 (Great)</span>
                    </div>
                    """, unsafe_allow_html=True)

        # Submit row
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Submit Response →", type="primary")

        if submitted:
            try:
                hidden_admin_email = form_schema[0]["admin_email"]
                conn.client.table("form_responses").insert({
                    "answers": user_answers,
                    "public_id": target_form_id,
                    "admin_email": hidden_admin_email
                }).execute()
                st.success("🎉 Thank you! Your response has been securely submitted.")
            except Exception as e:
                st.error(f"❌ Submission failed: {e}")

    # ── 6. FOOTER ──
    st.markdown("""
    <div class="gf-footer">
      🔒 Responses are anonymous and encrypted<br>
      <strong>Powered by PUV Sentiment Analytics</strong>
    </div>
    """, unsafe_allow_html=True)