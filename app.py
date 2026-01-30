import streamlit as st
import os
import pickle
import uuid
from io import BytesIO
from groq import Groq
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from streamlit_cookies_manager import EncryptedCookieManager

#COOKIE
cookies = EncryptedCookieManager(
    prefix="career_clarity",
    password="career-clarity-super-secret-key-123"
)

if not cookies.ready():
    st.stop()

def get_cookie_user_id():
    if "uid" not in cookies:
        cookies["uid"] = str(uuid.uuid4())
        cookies.save()
    return cookies["uid"]    

#USERID
def get_user_id():
    params = st.query_params
    if "uid" in params:
        return params["uid"]
    uid = str(uuid.uuid4())
    st.query_params["uid"] = uid
    st.rerun()

USER_ID = get_user_id()
USER_ID = get_cookie_user_id()
STATE_FILE = f"career_state_{USER_ID}.pkl"
# PERSISTENCE
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_state():
    with open(STATE_FILE, "wb") as f:
        pickle.dump(dict(st.session_state), f)

persisted = load_state()
# DEFAULT STATE
DEFAULTS = {
    "phase": "welcome",
    "q_index": 1,
    "answers": {},
    "mentor_chat":[],
    "mentor_input":"",
    "careers": None,
    "selected_career": None,
    "roadmap_type": None,
    "roadmap_days": {},
    "current_day": 1,
    "completed_days":set(),
    "mentor_input_key":0,
    "chat": [],
    "empathy_chat": [],
    "empathy_input_key": 0,
    "empathy_text": "",
    "empathy_reply": "",
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = persisted.get(k, v)

mem = st.session_state

#THEME
phase_themes = {
    "welcome": "linear-gradient(135deg, #0f172a, #1e293b)",
    "empathy": "linear-gradient(135deg, #2e1065, #020617)",
    "questions": "linear-gradient(135deg, #064e3b, #020617)",
    "career": "linear-gradient(135deg, #4c0519, #020617)",
    "roadmap_intro": "linear-gradient(135deg, #1e3a8a, #020617)",
    "day": "linear-gradient(135deg, #111827, #000000)",
}

st.set_page_config(page_title="Career Clarity", layout="centered")

st.markdown(f"""
<style>
.stApp {{
    background: {phase_themes.get(mem.phase)};
    color: #f8fafc;
}}
.career-box {{
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.4rem;
    margin-bottom: 1rem;
    background: rgba(255,255,255,0.06);
}}
.career-title {{
    font-size: 1.3rem;
    font-weight: 800;
    color: #60a5fa;
}}
.chat-user {{
    text-align: right;
    background: rgba(96,165,250,0.2);
    padding: 10px;
    border-radius: 12px;
    margin: 6px 0;
}}
.chat-mentor {{
    text-align: left;
    background: rgba(255,255,255,0.08);
    padding: 10px;
    border-radius: 12px;
    margin: 6px 0;
}}
</style>
""", unsafe_allow_html=True)

#GROQ
def groq_call(prompt):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    res = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )
    return res.choices[0].message.content.strip()

#SIDEBAR
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

# EMPATHY
elif mem.phase == "empathy":
        if st.button("⬅ Back"):
            mem.phase = "welcome"
            st.rerun()

        st.title("You're safe here.")
        st.caption("Say whatever you need. No judgement.")

    
        for role, msg in mem.empathy_chat:
            cls = "chat-user" if role == "You" else "chat-mentor"
            st.markdown(
            f"<div class='{cls}'>{msg}</div>",
            unsafe_allow_html=True
        )

  
        user_msg = st.text_input(
        "Type here…",
        key=f"empathy_input_{mem.empathy_input_key}"
    )

        if st.button("Send", key="empathy_send"):
            if user_msg.strip():
            
                mem.empathy_chat.append(("You", user_msg))

            
                reply = groq_call(f"""
You are a calm, deeply empathetic human listener.

Your job is NOT to ask questions.
Your job is to make the person feel less alone.

Rules:
- Speak gently and warmly.
- Validate their feelings without judging or fixing.
- Do NOT rush them.
- Do NOT interrogate them.
- Do NOT ask multiple questions.
- Avoid phrases like “tell me more” or “why do you feel this way”.

What to do instead:
- Reflect their emotional state.
- Offer comfort and reassurance.
- Normalize their feelings.
- Let them know it’s okay to feel this way.
- If you include a question, make it OPTIONAL and gentle.

IMPORTANT SAFETY RULE:
If the user expresses thoughts of self-harm, suicide, dying, or not wanting to exist:
- Respond with extra care.
- Clearly state that their life matters.
- Encourage reaching out to trusted people or local support.
- Stay calm and supportive.

User message:
{user_msg}
""")

            # store mentor reply
            mem.empathy_chat.append(("Mentor", reply))

            # 🔥 force input reset safely
            mem.empathy_input_key += 1
            st.rerun()

        st.markdown("---")

        if st.button("Continue"):
            mem.phase = "questions"
            mem.q_index = 1
            st.rerun()
def is_answer_valid(ans):
    if ans is None:
        return False
    if isinstance(ans, list):
        return len(ans) > 0
    if isinstance(ans, str):
        return len(ans.strip()) > 0
    return True
#QUESTIONS
if mem.phase == "questions":
    if st.button("⬅ Back"):
        mem.q_index = max(1, mem.q_index - 1)
        if mem.q_index == 1:
            mem.phase = "welcome"
        st.rerun()

    q = mem.q_index
    questions = {
        1: lambda: st.multiselect(
            "How are you feeling?",
            ["Stuck","Pressured","Ambitious","Confused","Hopeful","Burnt out","Lost","Motivated"]
        ),
        2: lambda: st.multiselect(
            "What energizes you?",
            ["Solving problems","Building systems","Helping people","Teaching",
             "Creative work","Leadership","Research","Storytelling"],
            max_selections=4
        ),
        3: lambda: st.text_area("Topics or fields you’re naturally drawn to?"),
        4: lambda: st.multiselect(
            "What do you want to avoid?",
            ["Repetition","High stress","Low growth","Night shifts",
             "Too much screen time","Too much social interaction"]
        ),
        5: lambda: st.text_input("Education / current path (be specific)"),
        6: lambda: st.multiselect(
            "What matters most?",
            ["Money","Growth","Stability","Impact","Recognition","Freedom"]
        ),
        7: lambda: st.radio("Income goal?", ["Not sure","Stable","High"], index=None),
        8: lambda: st.radio("Pace?", ["Slow","Balanced","Aggressive"], index=None),
    }

    st.markdown(f"### Step {q} of 8")
    ans = questions[q]()

    if st.button("Next"):
        if not is_answer_valid(ans):
            st.warning("Please answer this — it helps us guide you better 🌱")
        else:
            mem.answers[f"q{q}"] = ans
            if q == 8 :
                mem.phase = "career" 
            else :
                mem.phase="questions"
            mem.q_index = q + 1
            st.rerun()

#CAREER
elif mem.phase == "career":
    if st.button("⬅ Back"):
        mem.phase = "questions"
        mem.q_index = 8
        st.rerun()

    st.title("Your Recommended Career Paths")

    if mem.careers is None:
        raw = groq_call(f"""
You are a CAREER EXPERT.

FIRST:
Identify the user's PRIMARY DOMAIN based on education + interests.
Choose ONLY ONE base domain:
- Medicine
- Engineering
- Science
- Arts & Humanities
- Commerce & Business
- Gaming & Esports
- Film & Media
- Content Creation

SECOND:
Recommend EXACTLY 3 careers STRICTLY inside that domain.
DO NOT suggest adjacent or unrelated fields.

RULES:
- If MBBS → ONLY doctor/specialization paths like cardiology neurolgy etc
- If BSc → research / industry science / academia
- If Engineering → core/IT/product roles
- If Gaming → esports, streaming, game design
- If Film/Video → editor, producer, director
- If Arts/History → academia, policy, writing
- Be REALISTIC for India

FORMAT STRICTLY:

###
TITLE: ALL CAPS\n
DESCRIPTION: Why this aligns with users interst and how this many be useful, and what the role actually is.\n
SALARY: Fresher LPA | 3–5 Years LPA\n

###
TITLE: ALL CAPS\n
DESCRIPTION: Why this aligns with users interst and how this many be useful, and what the role actually is.\n
SALARY: Fresher LPA | 3–5 Years LPA\n

###
TITLE: ALL CAPS\n
DESCRIPTION: Why this aligns with users interst and how this many be useful, and what the role actually is.\n
SALARY: Fresher LPA | 3–5 Years LPA\n

User answers:
{mem.answers}
""")
        mem.careers = raw.split("###")[1:4]

    for i, c in enumerate(mem.careers, 1):
        st.markdown(
            f"<div class='career-box'><div class='career-title'>Career Option {i}</div>{c}</div>",
            unsafe_allow_html=True
        )
        cols = st.columns(3)
        if cols[0].button("🚀 30 Days", key=f"{i}_30"):
            mem.selected_career, mem.roadmap_type, mem.phase = c, "30 days", "roadmap_intro"
            st.rerun()
        if cols[1].button("📆 3–6 Months", key=f"{i}_6"):
            mem.selected_career, mem.roadmap_type, mem.phase = c, "3–6 months", "roadmap_intro"
            st.rerun()
        if cols[2].button("🧭 1 Year", key=f"{i}_12"):
            mem.selected_career, mem.roadmap_type, mem.phase = c, "1 year", "roadmap_intro"
            st.rerun()

#ROADMAP
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

#DAY+PDF
if mem.phase == "day":
    if st.button("⬅ Back"):
        mem.phase = "roadmap_intro"
        st.rerun()

    day = mem.current_day

    if day not in mem.roadmap_days:
        mem.roadmap_days[day] = groq_call(
            f"""
You are creating a CAREER-BUILDING roadmap.

Career:
{mem.selected_career}

Duration:
{mem.roadmap_type}

Create Day {day} with the following STRICT structure:

DAY {day}
GOAL:
(clear outcome)

WHAT TO LEARN:
(bullets)

YOUTUBE (give 2–3 real search-friendly titles):
- Title + channel
- Title + channel

WEBSITES / PLATFORMS:
- Website name + what to do there

PRACTICAL TASK:
(exact task to complete today)

END RESULT:
(what they should have by end of day)

Do NOT be generic.
Do NOT talk like a teacher.
Be practical.
"""
        )

    st.header(f"Day {day}")
    st.markdown(mem.roadmap_days[day])

    checkbox_key = f"completed_day_{day}"
    completed = st.checkbox("I completed today", key=checkbox_key)

    if completed and day not in mem.completed_days:
        mem.completed_days.add(day)
        mem.current_day += 1
        st.rerun()

    #PDF DOWNLOAD
    from io import BytesIO
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT

    buffer = BytesIO()

    doc = SimpleDocTemplate(
    buffer,
    rightMargin=36,
    leftMargin=36,
    topMargin=36,
    bottomMargin=36,
)

    styles = getSampleStyleSheet()

# Custom readable styles
    day_style = ParagraphStyle(
    "DayStyle",
    fontSize=16,
    leading=20,
    spaceAfter=12,
    spaceBefore=20,
    fontName="Helvetica-Bold",
)

    body_style = ParagraphStyle(
    "BodyStyle",
    fontSize=11,
    leading=16,
    spaceAfter=10,
    alignment=TA_LEFT,
)

    content = []

    for d in sorted(mem.roadmap_days):
        content.append(Paragraph(f"Day {d}", day_style))

        text = mem.roadmap_days[d]
        parts = text.split("\n")

        for p in parts:
            if p.strip():
                content.append(Paragraph(p.strip(), body_style))

        content.append(Spacer(1, 18))

    doc.build(content)
    buffer.seek(0)

    st.download_button(
    label="📄 Download roadmap PDF",
    data=buffer,
    file_name="career_roadmap.pdf",
    mime="application/pdf",
)
    #  SUPPORT MENTOR 

    st.subheader("Support Mentor")

    for role, msg in st.session_state.mentor_chat:
        if role == "You":
            st.markdown(
                f"<div class='chat-user'>{msg}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='chat-mentor'>{msg}</div>",
                unsafe_allow_html=True
            )

    mentor_msg = st.text_input(
    "Ask something about this career path",
    key=f"mentor_input_{mem.mentor_input_key}"
)

    if st.button("Send", key="mentor_send"):
        if mentor_msg.strip():
            mem.mentor_chat.append(("You", mentor_msg))

            reply = groq_call(f"""
You are a calm, practical career mentor.

Career:
{mem.selected_career}

Roadmap:
{mem.roadmap_type}

User question:
{mentor_msg}

Reply clearly and realistically.
""")

        mem.mentor_chat.append(("Mentor", reply))

        mem.mentor_input_key += 1
        st.rerun()

        for role, msg in mem.chat[-10:]:
            if role == "You":
                st.markdown(f"<div style='text-align:right;background:#3b82f620;padding:10px;border-radius:12px;margin:6px 0'>{msg}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background:#ffffff10;padding:10px;border-radius:12px;margin:6px 0'>{msg}</div>", unsafe_allow_html=True)

#SAVE
save_state()


