import streamlit as st
import os
import pickle
import uuid
from groq import Groq
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import re

# =====================================================
# 🔑 USER ID (URL BASED — REFRESH SAFE)
# =====================================================
def get_user_id():
    params = st.query_params
    if "uid" in params:
        return params["uid"]

    uid = str(uuid.uuid4())
    st.query_params["uid"] = uid
    st.rerun()


USER_ID = get_user_id()
STATE_FILE = f"career_state_{USER_ID}.pkl"

# =====================================================
# PERSISTENCE
# =====================================================
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_state():
    with open(STATE_FILE, "wb") as f:
        pickle.dump(dict(st.session_state), f)

persisted = load_state()

# =====================================================
# DEFAULT STATE
# =====================================================
DEFAULTS = {
    "phase": "welcome",
    "q_index": 1,
    "answers": {},
    "careers": None,
    "selected_career": None,
    "roadmap_type": None,
    "roadmap_days": {},
    "current_day": 1,
    "chat": [],
    "empathy_text": "",
    "empathy_reply": "",
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = persisted.get(k, v)

mem = st.session_state

# =====================================================
# THEME
# =====================================================
phase_themes = {
    "welcome": "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
    "empathy": "linear-gradient(135deg, #2e1065 0%, #020617 100%)",
    "questions": "linear-gradient(135deg, #064e3b 0%, #020617 100%)",
    "career": "linear-gradient(135deg, #4c0519 0%, #020617 100%)",
    "roadmap_intro": "linear-gradient(135deg, #1e3a8a 0%, #020617 100%)",
    "day": "linear-gradient(135deg, #111827 0%, #000000 100%)",
}

st.set_page_config(page_title="Career Clarity", layout="centered")

st.markdown(f"""
<style>
.stApp {{
    background: {phase_themes.get(mem.phase)};
    transition: background 0.8s ease-in-out;
    color: #f8fafc;
}}
.career-box {{
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 2rem;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
}}
.career-title {{
    font-size: 1.6rem;
    font-weight: 800;
    color: #60a5fa;
}}
</style>
""", unsafe_allow_html=True)

# =====================================================
# GROQ
# =====================================================
def groq_call(prompt):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return res.choices[0].message.content.strip()

# =====================================================
# SIDEBAR
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
# WELCOME
# =====================================================
if mem.phase == "welcome":
    st.title("Career Clarity")
    st.markdown("#### You don’t need all the answers today. Let’s take this one step at a time.")

    col1, col2 = st.columns(2)
    if col1.button("Start gently", use_container_width=True):
        mem.phase = "questions"
        mem.q_index = 1
        st.rerun()
    if col2.button("Let it out first", use_container_width=True):
        mem.phase = "empathy"
        st.rerun()

# =====================================================
# EMPATHY
# =====================================================
elif mem.phase == "empathy":
    if st.button("⬅ Back"):
        mem.phase = "welcome"
        st.rerun()

    st.title("You're safe here.")
    mem.empathy_text = st.text_area("What’s been weighing on you lately?", mem.empathy_text, height=220)

    if st.button("I just want to be heard"):
        mem.empathy_reply = groq_call(
            "Respond empathetically, plainly, and humanly.\n"
            "No narration, no roleplay.\n\n"
            f"{mem.empathy_text}"
        )

    if mem.empathy_reply:
        st.markdown(f"<div class='career-box'>{mem.empathy_reply}</div>", unsafe_allow_html=True)

    if st.button("Continue"):
        mem.phase = "questions"
        mem.q_index = 1
        st.rerun()

# =====================================================
# QUESTIONS
# =====================================================
elif mem.phase == "questions":
    if st.button("⬅ Back"):
        if mem.q_index == 1:
            mem.phase = "welcome"
        else:
            mem.q_index -= 1
        st.rerun()

    q = mem.q_index
    questions = {
        1: lambda: st.multiselect("How are you feeling?", ["Stuck","Pressured","Ambitious","Confused","Hopeful"]),
        2: lambda: st.multiselect("What energizes you?", ["Solving problems","Building systems","Teaching","Helping"], max_selections=3),
        3: lambda: st.text_area("Topics you love?"),
        4: lambda: st.multiselect("What do you want to avoid?", ["Repetition","Stress","Low growth"]),
        5: lambda: st.text_input("Education / work?"),
        6: lambda: st.multiselect("What matters most?", ["Money","Growth","Stability","Impact"]),
        7: lambda: st.radio("Income goal?", ["Not sure","Stable","High"], index=None),
        8: lambda: st.radio("Pace?", ["Slow","Balanced","Aggressive"], index=None),
    }

    st.markdown(f"### Step {q} of 8")
    ans = questions[q]()

    if st.button("Next"):
        mem.answers[f"q{q}"] = ans
        if q == 8:
            mem.phase = "career"
        else:
            mem.q_index += 1
        st.rerun()

# =====================================================
# CAREER
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
            s = re.sub(r"\\", "", s)      # remove ** formatting
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
    st.write(mem.selected_career)
    st.subheader(mem.roadmap_type)

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
        mem.roadmap_days[day] = groq_call(f"Create Day {day} plan for:\n{mem.selected_career}")

    st.header(f"Day {day}")
    st.markdown(mem.roadmap_days[day])

    if st.checkbox("I completed today"):
        mem.current_day += 1
        st.rerun()

    if st.button("Download roadmap PDF"):
        doc = SimpleDocTemplate("roadmap.pdf")
        styles = getSampleStyleSheet()
        content = [Paragraph(f"<b>Day {d}</b><br/>{mem.roadmap_days[d]}", styles["Normal"]) for d in mem.roadmap_days]
        doc.build(content)
        st.success("roadmap.pdf downloaded")

    st.subheader("Support Mentor")
    msg = st.text_input("Ask something")
    if msg:
        mem.chat.append(("You", msg))
        mem.chat.append(("Mentor", groq_call(msg)))

    for r, m in mem.chat[-6:]:
        st.write(f"**{r}:** {m}")

# =====================================================
# SAVE
# =====================================================
save_state()



