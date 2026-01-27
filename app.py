import streamlit as st
import os
import pickle
from groq import Groq
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import re

# =====================================================
# PERSISTENCE & STATE INITIALIZATION
# =====================================================
STATE_FILE = "career_state.pkl"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_state():
    with open(STATE_FILE, "wb") as f:
        pickle.dump(dict(st.session_state), f)

persisted = load_state()

DEFAULTS = {
    "phase": "welcome",
    "q_index": 1,
    "answers": {},
    "careers": None,
    "selected_career": None,
    "roadmap_type": None,
    "roadmap_days": {},
    "current_day": 1,
    "completed_days": set(),
    "chat": [],
    "empathy_text": "",
    "empathy_reply": "",
    "dev_mode": False,
    "_dev_loaded": False,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = persisted.get(k, v)

mem = st.session_state

# =====================================================
# DYNAMIC THEME ENGINE
# =====================================================
# Map colors to phases for better psychological flow
phase_themes = {
    "welcome": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",   # Deep Slate
    "empathy": "linear-gradient(135deg, #2e1065 0%, #020617 100%)",   # Royal Purple
    "questions": "linear-gradient(135deg, #064e3b 0%, #020617 100%)", # Forest Green
    "career": "linear-gradient(135deg, #4c0519 0%, #020617 100%)",    # Deep Rose
    "roadmap_intro": "linear-gradient(135deg, #1e3a8a 0%, #020617 100%)", # Electric Blue
    "day": "linear-gradient(135deg, #111827 0%, #000000 100%)",       # Dark Mode
}

current_bg = phase_themes.get(mem.phase, "#0E1117")

st.set_page_config(page_title="Career Clarity", layout="centered")

st.markdown(f"""
<style>
    /* Smooth background transition */
    .stApp {{
        background: {current_bg};
        transition: background 0.8s ease-in-out;
        color: #f8fafc;
    }}

    /* Glassmorphism Card Style */
    .career-box {{
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        background: rgba(255,255,255,0.05);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }}

    .career-title {{
        font-size: 1.6rem;
        font-weight: 800;
        color: #60a5fa;
        margin-bottom: 0.8rem;
    }}

    /* Global Typography */
    h1, h2, h3 {{ font-family: 'Inter', sans-serif; font-weight: 700; }}
    
    /* Button Enhancements */
    .stButton>button {{
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1);
        background: rgba(255,255,255,0.08);
        color: white;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background: rgba(255,255,255,0.2);
        border-color: #60a5fa;
        transform: translateY(-2px);
    }}
</style>
""", unsafe_allow_html=True)

# =====================================================
# GROQ CLIENT
# =====================================================
def groq_call(prompt):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return "Groq API key missing."
    client = Groq(api_key=key)
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return res.choices[0].message.content

# =====================================================
# SIDEBAR & DEV MODE
# =====================================================
with st.sidebar:
    st.header("Control Center")

    if st.button("💬 Vent anytime"):
        mem.phase = "empathy"
        st.rerun()

    if st.button("Reset App"):
        st.session_state.clear()
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        st.rerun()

# =====================================================
# PHASE: WELCOME
# =====================================================
if mem.phase == "welcome":
    st.title("Career Clarity")
    st.markdown("#### You don’t need all the answers today. Let’s take this one step at a time.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start gently", use_container_width=True):
            mem.phase = "questions"
            mem.q_index = 1
            st.rerun()
    with col2:
        if st.button("Let it out first", use_container_width=True):
            mem.phase = "empathy"
            st.rerun()

# =====================================================
# PHASE: EMPATHY SCREEN
# =====================================================
elif mem.phase == "empathy":
    st.title("You're safe here.")
    st.caption("No fixing. No judgement. Just space to be honest.")

    mem.empathy_text = st.text_area(
        "What’s been weighing on you lately?",
        value=mem.empathy_text, height=220,
        placeholder="Say it the way it feels..."
    )

    if st.button("I just want to be heard"):
        mem.empathy_reply = groq_call(
            f"You are a calm, deeply empathetic listener. Reflect feelings with warmth and validation in 4–6 sentences. User says: {mem.empathy_text}"
        )

    if mem.empathy_reply:
        st.markdown(f'<div class="career-box">💙<br><br>{mem.empathy_reply}</div>', unsafe_allow_html=True)

    if st.button("I feel ready to continue"):
        mem.phase = "questions"
        mem.q_index = 1
        st.rerun()

# =====================================================
# PHASE: QUESTIONS
# =====================================================
elif mem.phase == "questions":
    if st.button("⬅ Back"):
        mem.phase = "welcome"
        st.rerun()

    q = mem.q_index
    questions = {
        1: lambda: st.multiselect("How are you feeling inside right now?", ["I feel stuck","I feel pressured","I feel ambitious","I feel confused","I feel hopeful"]),
        2: lambda: st.multiselect("What feels energizing?", ["Solving complex problems","Building systems","Explaining concepts","Helping people","Leading teams"], max_selections=3),
        3: lambda: st.text_area("What topics naturally pull your attention?"),
        4: lambda: st.multiselect("What do you want to avoid?", ["Repetitive work","High stress","Low growth","Too much social interaction"]),
        5: lambda: st.text_input("Current education or work situation?"),
        6: lambda: st.multiselect("What matters most?", ["Money","Growth","Stability","Impact"]),
        7: lambda: st.radio("Desired income level?", ["Not sure","Stable income","High income"], index=None),
        8: lambda: st.radio("Pace for the next few years?", ["Slow","Balanced","Aggressive"], index=None),
    }

    st.markdown(f"### Step {q} of 8")
    answer = questions[q]()
    
    if st.button("Next"):
        mem.answers[f"q{q}"] = answer
        if q == 8:
            mem.phase = "career"
        else:
            mem.q_index += 1
        st.rerun()

# =====================================================
# PHASE: CAREER RECOMMENDATION
# =====================================================

# (The rest of your roadmap_intro and day view logic goes here)

# =====================================================
# QUESTIONS → CAREER → ROADMAP → DAY
# 🔒 COMPLETELY UNCHANGED BELOW
# =====================================================

# (Everything from your career, roadmap_intro, day, pdf, mentor sections remains EXACTLY the same)

# =====================================================
# SAVE STATE
# =====================================================
elif mem.phase == "career":
    if st.button("⬅ Back"):
        mem.phase = "questions"
        st.rerun()

    st.title("Your Recommended Career Paths")
    st.caption("Based on your responses, these roles best match your interests and long-term goals.")

    st.markdown("##  Top 3 Career Matches")

    if mem.careers is None:
        prompt = f"""
Give EXACTLY 3 career paths.

FORMAT STRICTLY:

###
TITLE:FULL CAPITAL IN BOLD TEXT\n new line
description:give how the interests and path of the user aligns to the job and how it suits them and also a description about the role\n new line
Salary:realistic  LPA for the  a job for a fresher/3-5 years experience\n new line

###
TITLE:FULL CAPITAL IN BOLD TEXT\n new line
description:give how the interests and path of the user aligns to the job and how it suits them and also a description about the role\n new line
Salary:realistic  LPA for the job for a fresher/3-5 years experience\nnew line

###
TITLE:FULL CAPITAL IN BOLD TEXT\n new line
description:give how the interests and path of the user aligns to the job and how it suits them and also a description about the role\n new line
Salary:realistic  LPA for the job for a fresher/3-5 years experience\n new line

Do NOT include profile, education, interests, or explanations.

Profile:
Education: {mem.answers['q5']}
Interests: {mem.answers['q3']}
Strengths: {mem.answers['q2']}
Avoids: {mem.answers['q4']}
Income goal: {mem.answers['q7']}
"""
        raw = groq_call(prompt)
        sections = raw.split("###")[1:]
        cleaned = []

        for s in sections[:3]:
            s = re.sub(r"\*\*", "", s)      # remove ** formatting
            s = re.sub(r"Profile:.*", "", s, flags=re.DOTALL)  # remove profile if leaked
            cleaned.append(s.strip())

        mem.careers = cleaned

    for i, c in enumerate(mem.careers, start=1):
        st.markdown(f"""
        <div class="career-box">
            <div class="career-title">Career Option {i}</div>
            <div>{c}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Choose a roadmap")

        cols = st.columns(3, gap="large")

        if cols[0].button("🚀 30 Days", key=f"{i}_30", use_container_width=True):
            mem.selected_career = c
            mem.roadmap_type = "30 days"
            mem.phase = "roadmap_intro"
            st.rerun()

        if cols[1].button("📆 3–6 Months", key=f"{i}_6", use_container_width=True):
            mem.selected_career = c
            mem.roadmap_type = "3–6 months"
            mem.phase = "roadmap_intro"
            st.rerun()

        if cols[2].button("🧭 1 Year", key=f"{i}_12", use_container_width=True):
            mem.selected_career = c
            mem.roadmap_type = "1 year"
            mem.phase = "roadmap_intro"
            st.rerun()

# =====================================================
# ROADMAP INTRO
# =====================================================
elif mem.phase == "roadmap_intro":
    if st.button("⬅ Back"):
        mem.phase = "career"
        st.rerun()

    st.title("Your Personalized Roadmap")
    st.caption("A focused, step-by-step plan with maximum 2 hours per day.")

    st.write(mem.selected_career)
    st.subheader(f"Duration: {mem.roadmap_type}")

    if st.button("Start Day 1"):
        mem.current_day = 1
        mem.phase = "day"
        st.rerun()

# =====================================================
# DAY VIEW
# =====================================================
elif mem.phase == "day":
    if st.button("⬅ Back"):
        mem.phase = "roadmap_intro"
        st.rerun()

    day = mem.current_day

    if day not in mem.roadmap_days:
        mem.roadmap_days[day] = groq_call(
            f"Create Day {day} plan (max 2 hours) for:\n{mem.selected_career}"
        )

    st.header(f"Day {day}")
    st.markdown(mem.roadmap_days[day])

    if st.checkbox("I completed today", key=f"done_{day}"):
        mem.completed_days.add(day)
        mem.current_day += 1
        st.rerun()

    if st.button("Download roadmap PDF"):
        doc = SimpleDocTemplate("roadmap.pdf")
        styles = getSampleStyleSheet()
        content = []
        for d in sorted(mem.roadmap_days):
            content.append(Paragraph(f"<b>Day {d}</b><br/>{mem.roadmap_days[d]}", styles["Normal"]))
        doc.build(content)
        st.success("roadmap.pdf downloaded")

    st.divider()
    st.subheader("Support Mentor")

    msg = st.text_input("Ask something")
    if msg:
        mem.chat.append(("You", msg))
        reply = groq_call(f"You are a calm mentor. Reply briefly:\n{msg}")
        mem.chat.append(("Mentor", reply))

    for r, m in mem.chat[-6:]:
        st.write(f"**{r}:** {m}")

# =====================================================
# SAVE STATE
# =====================================================
save_state()
