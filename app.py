import streamlit as st
from groq import Groq
import PyPDF2
import json
import os
import re
import time
import resend
from dotenv import load_dotenv

load_dotenv()

# ---- SECURE API KEY LOADING ----
api_key = os.getenv("GROQ_API_KEY", "")
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

client = Groq(api_key=api_key)

st.set_page_config(page_title="FlashLearn AI", page_icon="🧠", layout="centered")

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True


def initialize_session():
    defaults = {
        "cards": [], "current_index": 0, "show_answer": False,
        "show_hint": False, "known_cards": set(), "review_cards": set(),
        "skipped_cards": set(), "difficulty_ratings": {}, "deck_name": "",
        "study_mode": False, "review_queue": [], "streak": 0, "max_streak": 0,
        "card_start_time": None, "time_per_card": {}, "session_complete": False,
        "app_mode": "home", "timed_mode": False, "time_limit": 30,
        "mcq_questions": [], "mcq_index": 0, "mcq_score": 0,
        "mcq_answered": False, "mcq_selected": None, "mcq_complete": False,
        "mcq_skipped": set(), "pdf_text": "", "all_asked_flash": [],
        "all_asked_mcq": [], "study_history": [],
        "user_name": "", "user_grade": "", "user_email": "",
        "email_reports": False, "profile_set": False,
        "show_profile_setup": True, "dark_mode": True,
        "flash_order": [], "flash_position": 0,
        "performance_history": [],
        "start_mode": "flashcard",
        "last_timer_card": None,
        "last_timer_mcq": None,
        "confirm_switch": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


initialize_session()

# ---- THEME ----
if st.session_state.dark_mode:
    st.markdown("""
<style>
    .stApp { background-color: #0e1117 !important; }
    section[data-testid="stSidebar"] { background-color: #1e2130 !important; }
    header[data-testid="stHeader"] { background-color: #0e1117 !important; }
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3,
    .stApp label, .stApp span { color: #ffffff !important; }
    section[data-testid="stSidebar"] * { color: #ffffff !important; }
    .stTextInput input, .stTextArea textarea {
        background-color: #2e3347 !important;
        color: #ffffff !important;
        border-color: #2e3347 !important;
    }
    div[data-testid="metric-container"] {
        background-color: #1e2130 !important;
        border: 1px solid #2e3347 !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
    .streamlit-expanderHeader {
        background-color: #1e2130 !important;
        color: #ffffff !important;
    }
    .flashcard {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important; padding: 40px; border-radius: 16px;
        text-align: center; font-size: 20px; min-height: 200px;
        display: flex; align-items: center; justify-content: center;
        margin: 20px 0; box-shadow: 0 8px 32px rgba(102,126,234,0.3);
    }
    .answer-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white !important; padding: 40px; border-radius: 16px;
        text-align: center; font-size: 18px; min-height: 200px;
        display: flex; align-items: center; justify-content: center;
        margin: 20px 0; box-shadow: 0 8px 32px rgba(17,153,142,0.3);
    }
    .hint-card {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        color: white !important; padding: 25px; border-radius: 16px;
        text-align: center; font-size: 16px; margin: 10px 0;
    }
    .streak-box {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        color: white !important; padding: 10px 20px; border-radius: 12px;
        text-align: center; font-size: 18px; font-weight: bold;
        margin: 10px 0;
    }
    .summary-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important; padding: 30px; border-radius: 16px;
        text-align: center; margin: 20px 0;
    }
    .summary-box * { color: white !important; }
    .mode-card {
        background: #1e2130; border: 2px solid #2e3347;
        border-radius: 16px; padding: 25px; text-align: center; margin: 10px 0;
    }
    .mcq-option {
        background: #1e2130; border: 2px solid #2e3347;
        border-radius: 12px; padding: 15px; margin: 8px 0;
        color: #ffffff !important;
    }
    .mcq-correct {
        background: #1a3a2a; border: 2px solid #28a745;
        border-radius: 12px; padding: 15px; margin: 8px 0;
        color: #6fcf97 !important;
    }
    .mcq-wrong {
        background: #3a1a1a; border: 2px solid #dc3545;
        border-radius: 12px; padding: 15px; margin: 8px 0;
        color: #eb5757 !important;
    }
    .feedback-correct { color: #6fcf97 !important; font-size: 14px; font-weight: bold; }
    .feedback-wrong { color: #eb5757 !important; font-size: 14px; font-weight: bold; }
    .timer-warning { color: #eb5757 !important; font-size: 28px; font-weight: bold; text-align: center; }
    .timer-normal { color: #6fcf97 !important; font-size: 28px; font-weight: bold; text-align: center; }
    .progress-text { text-align: center; font-size: 16px; color: #aaaaaa; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)
    bg_color = "#0e1117"
    card_bg = "#1e2130"
    text_color = "#ffffff"
    subtext_color = "#aaaaaa"
    border_color = "#2e3347"
else:
    st.markdown("""
<style>
    .stApp { background-color: #ffffff !important; }
    section[data-testid="stSidebar"] { background-color: #f0f2f6 !important; }
    header[data-testid="stHeader"] { background-color: #ffffff !important; }
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3,
    .stApp label, .stApp span { color: #000000 !important; }
    section[data-testid="stSidebar"] * { color: #000000 !important; }
    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-color: #cccccc !important;
    }
    div[data-testid="metric-container"] {
        background-color: #f0f2f6 !important;
        border: 1px solid #cccccc !important;
        border-radius: 12px !important;
        padding: 10px !important;
    }
    .streamlit-expanderHeader {
        background-color: #f0f2f6 !important;
        color: #000000 !important;
    }
    .flashcard {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important; padding: 40px; border-radius: 16px;
        text-align: center; font-size: 20px; min-height: 200px;
        display: flex; align-items: center; justify-content: center;
        margin: 20px 0; box-shadow: 0 8px 32px rgba(102,126,234,0.3);
    }
    .answer-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white !important; padding: 40px; border-radius: 16px;
        text-align: center; font-size: 18px; min-height: 200px;
        display: flex; align-items: center; justify-content: center;
        margin: 20px 0; box-shadow: 0 8px 32px rgba(17,153,142,0.3);
    }
    .hint-card {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        color: white !important; padding: 25px; border-radius: 16px;
        text-align: center; font-size: 16px; margin: 10px 0;
    }
    .streak-box {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        color: white !important; padding: 10px 20px; border-radius: 12px;
        text-align: center; font-size: 18px; font-weight: bold;
        margin: 10px 0;
    }
    .summary-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important; padding: 30px; border-radius: 16px;
        text-align: center; margin: 20px 0;
    }
    .summary-box * { color: white !important; }
    .mode-card {
        background: #f0f2f6; border: 2px solid #cccccc;
        border-radius: 16px; padding: 25px; text-align: center; margin: 10px 0;
    }
    .mcq-option {
        background: #f0f2f6; border: 2px solid #cccccc;
        border-radius: 12px; padding: 15px; margin: 8px 0;
        color: #000000 !important;
    }
    .mcq-correct {
        background: #d4edda; border: 2px solid #28a745;
        border-radius: 12px; padding: 15px; margin: 8px 0;
        color: #155724 !important;
    }
    .mcq-wrong {
        background: #f8d7da; border: 2px solid #dc3545;
        border-radius: 12px; padding: 15px; margin: 8px 0;
        color: #721c24 !important;
    }
    .feedback-correct { color: #28a745 !important; font-size: 14px; font-weight: bold; }
    .feedback-wrong { color: #dc3545 !important; font-size: 14px; font-weight: bold; }
    .timer-warning { color: #dc3545 !important; font-size: 28px; font-weight: bold; text-align: center; }
    .timer-normal { color: #28a745 !important; font-size: 28px; font-weight: bold; text-align: center; }
    .progress-text { text-align: center; font-size: 16px; color: #666666; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)
    bg_color = "#ffffff"
    card_bg = "#f0f2f6"
    text_color = "#000000"
    subtext_color = "#666666"
    border_color = "#cccccc"


def get_grade_settings(grade):
    if grade in ["Grade 1", "Grade 2", "Grade 3"]:
        return (
            """- Use very simple words a 6-8 year old would understand
- Questions should be basic recall: 'What is...', 'Name the...'
- Answers should be one short sentence maximum
- Use fun friendly language
- Avoid any technical jargon completely""",
            "primary school child (ages 6-8)"
        )
    elif grade in ["Grade 4", "Grade 5", "Grade 6"]:
        return (
            """- Use simple clear language for ages 9-11
- Questions can involve basic understanding and recall
- Answers should be 1-2 short sentences
- Avoid complex terminology, explain if unavoidable""",
            "upper primary student (ages 9-11)"
        )
    elif grade in ["Grade 7", "Grade 8", "Grade 9"]:
        return (
            """- Use moderately simple language for ages 12-14
- Questions can test understanding, not just recall
- Include some 'Why' and 'How' questions
- Introduce subject-specific terms with brief context""",
            "middle school student (ages 12-14)"
        )
    elif grade in ["Grade 10", "Grade 11", "Grade 12"]:
        return (
            """- Use standard academic language for ages 15-18
- Questions should test deeper understanding and application
- Include analytical questions like 'Explain why...' or 'Compare...'
- Use subject-specific terminology appropriately""",
            "high school student (ages 15-18)"
        )
    elif grade == "Undergraduate":
        return (
            """- Use university-level academic language
- Questions should test analysis synthesis and critical thinking
- Include conceptual and application-based questions
- Use technical terminology freely and precisely
- Answers can be multi-faceted""",
            "undergraduate university student"
        )
    elif grade == "Postgraduate":
        return (
            """- Use advanced academic and research-level language
- Questions should test deep critical analysis and synthesis
- Include questions about implications limitations and connections
- Assume strong domain knowledge
- Answers should reflect expert-level understanding""",
            "postgraduate / research level student"
        )
    else:
        return (
            "- Use clear academic language appropriate for the topic",
            "general student"
        )


def extract_text_from_pdf(uploaded_file):
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text


def generate_flashcards(text, num_cards=15, existing_questions=None):
    exclude = ""
    if existing_questions:
        exclude = f"\nDo NOT repeat these questions:\n{json.dumps(existing_questions)}\n"

    grade = st.session_state.get("user_grade", "Undergraduate")
    difficulty, level = get_grade_settings(grade)

    prompt = f"""You are an expert educator creating flashcards for a {level}.
{exclude}
Create {num_cards} high-quality flashcards from the text below.

Difficulty and language guidelines for this student level:
{difficulty}

Each flashcard must have:
- A clear question appropriate for a {level}
- A concise answer at the right complexity level
- A hint that gives a partial clue without giving away the answer

Return ONLY a valid JSON array. No markdown, no extra text.
Format:
[
  {{"question": "What is...", "answer": "It is...", "hint": "Think about..."}},
  {{"question": "...", "answer": "...", "hint": "..."}}
]

Text to analyze:
{text[:6000]}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7, max_tokens=4000
    )
    response_text = response.choices[0].message.content.strip()
    response_text = re.sub(r'^```json\s*', '', response_text)
    response_text = re.sub(r'^```\s*', '', response_text)
    response_text = re.sub(r'\s*```$', '', response_text)
    return json.loads(response_text.strip())


def generate_mcq(cards, existing_questions=None):
    exclude = ""
    if existing_questions:
        exclude = f"\nDo NOT repeat these questions:\n{json.dumps(existing_questions)}\n"

    grade = st.session_state.get("user_grade", "Undergraduate")

    if grade in ["Grade 1", "Grade 2", "Grade 3"]:
        difficulty = "Keep options very simple. Use short words. Wrong options should be clearly different but not tricky."
        level = "primary school child (ages 6-8)"
    elif grade in ["Grade 4", "Grade 5", "Grade 6"]:
        difficulty = "Use simple language. Wrong options should be plausible but clearly wrong on reflection."
        level = "upper primary student (ages 9-11)"
    elif grade in ["Grade 7", "Grade 8", "Grade 9"]:
        difficulty = "Use moderate language. Wrong options can be somewhat tricky to make students think."
        level = "middle school student (ages 12-14)"
    elif grade in ["Grade 10", "Grade 11", "Grade 12"]:
        difficulty = "Use academic language. Wrong options should be plausible and require proper understanding to eliminate."
        level = "high school student (ages 15-18)"
    elif grade == "Undergraduate":
        difficulty = "Use university-level language. Wrong options should be closely related and require deep understanding to differentiate."
        level = "undergraduate student"
    elif grade == "Postgraduate":
        difficulty = "Use advanced language. Wrong options should be sophisticated and require expert knowledge to eliminate."
        level = "postgraduate student"
    else:
        difficulty = "Use clear language with plausible wrong options."
        level = "general student"

    prompt = f"""You are an expert educator creating MCQ questions for a {level}.
{exclude}
Flashcards:
{json.dumps(cards[:10], indent=2)}

Create one MCQ per flashcard.
{difficulty}

Each MCQ must have:
- The question from the flashcard
- The correct answer
- 3 plausible but wrong options
- All 4 options shuffled

Return ONLY a valid JSON array. No markdown, no extra text.
Format:
[
  {{
    "question": "What is...",
    "correct": "The correct answer",
    "options": ["Option A", "Option B", "Option C", "Option D"]
  }}
]"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7, max_tokens=4000
    )
    response_text = response.choices[0].message.content.strip()
    response_text = re.sub(r'^```json\s*', '', response_text)
    response_text = re.sub(r'^```\s*', '', response_text)
    response_text = re.sub(r'\s*```$', '', response_text)
    return json.loads(response_text.strip())


def is_session_complete():
    if st.session_state.app_mode == "flashcard":
        total = len(st.session_state.cards)
        known = len(st.session_state.known_cards)
        skipped = len(st.session_state.skipped_cards)
        return known == total or (known + skipped == total)
    elif st.session_state.app_mode == "mcq":
        return st.session_state.mcq_complete
    return True


def reset_study_session():
    cards = st.session_state.cards
    st.session_state.flash_order = list(range(len(cards)))
    st.session_state.flash_position = 0
    st.session_state.current_index = 0
    st.session_state.show_answer = False
    st.session_state.show_hint = False
    st.session_state.known_cards = set()
    st.session_state.review_cards = set()
    st.session_state.skipped_cards = set()
    st.session_state.difficulty_ratings = {}
    st.session_state.study_mode = False
    st.session_state.review_queue = []
    st.session_state.streak = 0
    st.session_state.max_streak = 0
    st.session_state.card_start_time = time.time()
    st.session_state.time_per_card = {}
    st.session_state.session_complete = False
    st.session_state.mcq_index = 0
    st.session_state.mcq_score = 0
    st.session_state.mcq_answered = False
    st.session_state.mcq_selected = None
    st.session_state.mcq_complete = False
    st.session_state.mcq_skipped = set()
    st.session_state.last_timer_card = None
    st.session_state.last_timer_mcq = None
    st.session_state.confirm_switch = None


def go_to_dashboard():
    for key in ["cards", "pdf_text", "all_asked_flash",
                "all_asked_mcq", "mcq_questions", "deck_name"]:
        st.session_state[key] = [] if key != "deck_name" else ""
    reset_study_session()
    st.rerun()


def switch_mode(new_mode):
    if is_session_complete():
        st.session_state.timed_mode = False
        st.session_state.last_timer_card = None
        st.session_state.last_timer_mcq = None
        st.session_state.card_start_time = None
        st.session_state.confirm_switch = None
        st.session_state.app_mode = new_mode
        if new_mode == "mcq" and not st.session_state.mcq_questions:
            return "generate_mcq"
        return "switched"
    else:
        st.session_state.confirm_switch = new_mode
        return "confirm"


def add_to_history(deck_name, activity, score=None):
    entry = {
        "deck": deck_name,
        "activity": activity,
        "time": time.strftime("%d %b %Y, %I:%M %p"),
        "score": score
    }
    if (not st.session_state.study_history or
            st.session_state.study_history[-1]["deck"] != deck_name or
            st.session_state.study_history[-1]["activity"] != activity):
        st.session_state.study_history.append(entry)


def record_performance(score_pct):
    st.session_state.performance_history.append({
        "score": score_pct,
        "time": time.strftime("%d %b, %I:%M %p"),
        "deck": st.session_state.deck_name
    })


# ==============================
# EMAIL FUNCTIONS
# ==============================
def configure_resend():
    key = os.getenv("RESEND_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("RESEND_API_KEY", "")
        except Exception:
            key = ""
    resend.api_key = key
    return bool(key)


def send_study_report_email(to_email, user_name, deck_name,
                             score, known, total, streak):
    if not configure_resend():
        st.warning("Add RESEND_API_KEY to your secrets to enable emails.")
        return
    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
        <div style="background:linear-gradient(135deg,#667eea,#764ba2);
                    padding:30px;border-radius:16px;text-align:center;margin-bottom:20px">
            <h1 style="color:white;margin:0">🧠 FlashLearn AI</h1>
            <p style="color:rgba(255,255,255,0.9);margin:8px 0 0">Study Report</p>
        </div>
        <p style="font-size:18px">Hi <b>{user_name}</b>! Here's your session summary 📊</p>
        <div style="background:#f8f9fa;border-radius:12px;padding:24px;margin:20px 0">
            <table style="width:100%;border-collapse:collapse">
                <tr><td style="padding:8px 0;font-size:16px">📚 Deck</td>
                    <td style="padding:8px 0;font-size:16px;font-weight:bold">{deck_name}</td></tr>
                <tr><td style="padding:8px 0;font-size:16px">✅ Cards Mastered</td>
                    <td style="padding:8px 0;font-size:16px;font-weight:bold">{known} / {total}</td></tr>
                <tr><td style="padding:8px 0;font-size:16px">🏆 Performance Score</td>
                    <td style="padding:8px 0;font-size:16px;font-weight:bold">{score:.0f} / 100</td></tr>
                <tr><td style="padding:8px 0;font-size:16px">🔥 Best Streak</td>
                    <td style="padding:8px 0;font-size:16px;font-weight:bold">{streak} cards in a row</td></tr>
            </table>
        </div>
        <p style="color:#666;font-size:13px;text-align:center;margin-top:24px">
            Sent by FlashLearn AI</p>
    </div>"""
    try:
        resend.Emails.send({
            "from": "FlashLearn AI <onboarding@resend.dev>",
            "to": [to_email],
            "subject": f"📊 Your FlashLearn Study Report — {deck_name}",
            "html": html
        })
        st.success(f"📧 Study report sent to {to_email}! ✅")
    except Exception as e:
        st.warning(f"Could not send report: {str(e)}")


def render_timer(remaining_time, placeholder):
    if remaining_time <= 10:
        placeholder.markdown(
            f'<p class="timer-warning">⏱️ {int(remaining_time)}s</p>',
            unsafe_allow_html=True)
    else:
        placeholder.markdown(
            f'<p class="timer-normal">⏱️ {int(remaining_time)}s</p>',
            unsafe_allow_html=True)


def show_improvement_tracker():
    history = st.session_state.performance_history
    if not history:
        return
    st.markdown("### 📈 Your Improvement Tracker")
    latest = history[-1]["score"]
    if len(history) >= 2:
        previous = history[-2]["score"]
        diff = latest - previous
        if diff > 0:
            trend = f"📈 Up {diff:.0f} points from last session!"
            trend_color = "#28a745"
        elif diff < 0:
            trend = f"📉 Down {abs(diff):.0f} points from last session."
            trend_color = "#dc3545"
        else:
            trend = "➡️ Same as last session."
            trend_color = "#ffc107"
    else:
        trend = "🎯 First session recorded!"
        trend_color = "#667eea"

    st.markdown(f"**Current Performance Score: {latest:.0f}/100**")
    st.markdown(
        f'<p style="color:{trend_color};font-weight:bold">{trend}</p>',
        unsafe_allow_html=True)
    st.slider("Performance Level", min_value=0, max_value=100,
              value=int(latest), disabled=True,
              help="Calculated from correct answers, streak and speed")
    if len(history) > 1:
        st.markdown("**Recent Sessions:**")
        for h in reversed(history[-5:]):
            color = ("#28a745" if h["score"] >= 70
                    else "#ffc107" if h["score"] >= 40 else "#dc3545")
            st.markdown(
                f'<div style="margin:4px 0">'
                f'<span style="font-size:12px;color:{subtext_color}">'
                f'{h["time"]} — {h["deck"][:20]}</span><br>'
                f'<div style="background:{color};width:{int(h["score"])}%;'
                f'height:8px;border-radius:4px"></div>'
                f'<span style="font-size:12px;color:{text_color}">'
                f'{h["score"]:.0f}/100</span></div>',
                unsafe_allow_html=True)


# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("## 🧠 FlashLearn AI")

    theme_label = "🌙 Dark Mode" if st.session_state.dark_mode else "☀️ Light Mode"
    dark_toggle = st.toggle(theme_label, value=st.session_state.dark_mode,
                            key="theme_toggle")
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    st.divider()

    if st.session_state.profile_set:
        st.markdown(f"👤 **{st.session_state.user_name}**")
        st.markdown(f"🎓 {st.session_state.user_grade}")
        if st.session_state.user_email:
            st.markdown(f"📧 {st.session_state.user_email}")
            st.markdown(
                f"📬 Reports: {'✅ On' if st.session_state.email_reports else '❌ Off'}")
        if st.button("✏️ Edit Profile", use_container_width=True):
            st.session_state.show_profile_setup = True
            st.rerun()
        st.divider()

    if st.session_state.cards:
        if st.button("🏠 Go to Dashboard", use_container_width=True):
            go_to_dashboard()
        st.divider()

    if st.session_state.cards:
        st.markdown("### ⚙️ Session Controls")
        timed_toggle = st.toggle(
            "⏱️ Timed Mode",
            value=st.session_state.timed_mode,
            help="Toggle timer on/off — takes effect on next card"
        )
        if timed_toggle != st.session_state.timed_mode:
            st.session_state.timed_mode = timed_toggle
            st.session_state.last_timer_card = None
            st.session_state.last_timer_mcq = None
            st.session_state.card_start_time = None
            st.rerun()

        if st.session_state.timed_mode:
            new_limit = st.select_slider(
                "Seconds per card",
                options=[10, 15, 20, 30, 45, 60],
                value=st.session_state.time_limit
            )
            if new_limit != st.session_state.time_limit:
                st.session_state.time_limit = new_limit
                st.session_state.last_timer_card = None
                st.session_state.last_timer_mcq = None
                st.session_state.card_start_time = None
                st.rerun()
        st.divider()

    st.markdown("### 📖 Study History")
    if not st.session_state.study_history:
        st.markdown("*No sessions yet!*")
    else:
        seen_decks = {}
        for entry in reversed(st.session_state.study_history):
            deck = entry["deck"]
            if deck not in seen_decks:
                seen_decks[deck] = {
                    "flashcard": 0, "mcq": [],
                    "last_studied": entry["time"]
                }
            if entry["activity"] == "Flashcards":
                seen_decks[deck]["flashcard"] += 1
            elif entry["activity"] == "MCQ":
                seen_decks[deck]["mcq"].append(entry.get("score", "N/A"))

        for deck, data in seen_decks.items():
            with st.expander(f"📄 {deck[:20]}"):
                st.markdown(f"🕐 Last: **{data['last_studied']}**")
                if data["flashcard"] > 0:
                    st.markdown(f"🃏 Sessions: **{data['flashcard']}**")
                if data["mcq"]:
                    scores = [s for s in data["mcq"] if isinstance(s, (int, float))]
                    best = max(scores) if scores else "N/A"
                    st.markdown(f"📝 MCQ attempts: **{len(data['mcq'])}**")
                    st.markdown(f"🏆 Best: **{best}%**")

        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.study_history = []
            st.rerun()


# ==============================
# MAIN
# ==============================
st.title("🧠 FlashLearn AI")
st.markdown(
    "*Turn any PDF into smart flashcards — and actually remember what you study.*")
st.divider()

# ==============================
# PROFILE SETUP
# ==============================
if st.session_state.show_profile_setup:
    st.markdown("### 👤 Let's get to know you first!")
    st.markdown("*This helps us personalize your experience.*")

    name = st.text_input("Your Name *",
                         value=st.session_state.user_name,
                         placeholder="e.g. Anisha",
                         key="profile_name")

    grade_options = [
        "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
        "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10",
        "Grade 11", "Grade 12", "Undergraduate", "Postgraduate"
    ]
    current_grade_idx = (grade_options.index(st.session_state.user_grade)
                        if st.session_state.user_grade in grade_options else 0)
    grade = st.selectbox("Your Grade / Level *",
                         options=grade_options, index=current_grade_idx,
                         key="profile_grade")

    email = st.text_input("Email Address (optional)",
                          value=st.session_state.user_email,
                          placeholder="e.g. you@gmail.com",
                          key="profile_email")

    st.markdown("---")
    st.markdown("📬 **Email Preferences**")

    if email.strip():
        email_reports = st.checkbox(
            "📊 Yes, send me study reports & streak reminders",
            value=st.session_state.email_reports,
            key="email_reports_check"
        )
        if email_reports:
            st.success(f"✅ Reports will be sent to **{email}**")
        else:
            st.info("📭 Reports disabled. You can turn this on anytime.")
    else:
        st.caption(
            "💡 Enter your email above to enable study reports and streak reminders.")
        email_reports = False

    st.markdown("")
    if st.button("🚀 Let's Start!", use_container_width=True, type="primary"):
        if not name:
            st.error("Please enter your name to continue.")
        else:
            st.session_state.user_name = name
            st.session_state.user_grade = grade
            st.session_state.user_email = email
            st.session_state.email_reports = email_reports
            st.session_state.profile_set = True
            st.session_state.show_profile_setup = False
            st.rerun()

# ==============================
# DASHBOARD / HOME
# ==============================
elif not st.session_state.cards:
    st.markdown(f"### 👋 Welcome back, {st.session_state.user_name}!")
    grade = st.session_state.user_grade
    st.markdown(f"*{grade} — ready to study?*")

    _, level = get_grade_settings(grade)
    st.info(f"🎓 Cards will be adapted for: **{level}**")

    if st.session_state.performance_history:
        show_improvement_tracker()

    st.divider()
    st.markdown("### 📚 Choose Your Study Mode")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
<div class="mode-card">
<h2>🃏</h2><h3>Flashcards</h3>
<p style="color:{subtext_color};font-size:14px">
Flip cards, rate difficulty, track progress.</p>
</div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
<div class="mode-card">
<h2>📝</h2><h3>MCQ Quiz</h3>
<p style="color:{subtext_color};font-size:14px">
Multiple choice questions with instant feedback.</p>
</div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📄 Upload Your Study Material")
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader("Drop a PDF here", type=["pdf"])
    with col2:
        num_cards = st.slider("Number of cards", min_value=5, max_value=25, value=15)

    deck_name = st.text_input("Give this deck a name:",
                               placeholder="e.g. Quadratic Equations, Chapter 3")

    st.markdown("### ⚙️ Initial Settings")
    col_a, col_b = st.columns(2)
    with col_a:
        timed_mode = st.toggle("⏱️ Start with Timed Mode", value=False)
    with col_b:
        if timed_mode:
            time_limit = st.select_slider("Seconds per card",
                                           options=[10, 15, 20, 30, 45, 60],
                                           value=30)
        else:
            time_limit = 30

    if uploaded_file is None:
        st.caption("⬆️ Upload a PDF above to get started.")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        flash_start = st.button("🃏 Start Flashcards",
                                use_container_width=True, type="primary",
                                disabled=uploaded_file is None)
    with col_btn2:
        quiz_start = st.button("📝 Start Quiz",
                               use_container_width=True,
                               disabled=uploaded_file is None)

    if (flash_start or quiz_start) and uploaded_file:
        mode = "flashcard" if flash_start else "mcq"
        with st.spinner(f"Reading your PDF and creating {level}-level content..."):
            try:
                text = extract_text_from_pdf(uploaded_file)
                if len(text.strip()) < 100:
                    st.error("Couldn't extract enough text. Try a different file.")
                else:
                    cards = generate_flashcards(text, num_cards)
                    st.session_state.cards = cards
                    st.session_state.pdf_text = text
                    st.session_state.deck_name = deck_name or uploaded_file.name
                    st.session_state.timed_mode = timed_mode
                    st.session_state.time_limit = time_limit
                    st.session_state.all_asked_flash = [c["question"] for c in cards]
                    st.session_state.app_mode = mode
                    reset_study_session()
                    add_to_history(st.session_state.deck_name,
                                  "Flashcards" if mode == "flashcard" else "MCQ")
                    if mode == "mcq":
                        with st.spinner("Generating quiz questions..."):
                            st.session_state.mcq_questions = generate_mcq(cards)
                            st.session_state.all_asked_mcq = [
                                q["question"]
                                for q in st.session_state.mcq_questions]
                    st.rerun()
            except json.JSONDecodeError:
                st.error("Had trouble parsing. Please try again.")
            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

# ==============================
# MAIN STUDY AREA
# ==============================
else:
    cards = st.session_state.cards
    total = len(cards)
    known = len(st.session_state.known_cards)
    reviewing = len(st.session_state.review_cards)
    skipped = len(st.session_state.skipped_cards)
    remaining = total - known - reviewing - skipped

    top_col1, top_col2 = st.columns([4, 1])
    with top_col1:
        st.markdown(f"### 📚 {st.session_state.deck_name}")
        if st.session_state.user_name:
            st.caption(
                f"Studying as: {st.session_state.user_name} "
                f"• {st.session_state.user_grade}")
    with top_col2:
        if st.button("🏠 Home", use_container_width=True,
                     help="Back to dashboard"):
            go_to_dashboard()

    if st.session_state.timed_mode:
        st.info(f"⏱️ Timed Mode ON — {st.session_state.time_limit}s per card")
    else:
        st.info("⏱️ Timed Mode OFF — toggle on in sidebar anytime")

    # ==============================
    # CONFIRMATION DIALOG
    # ==============================
    if st.session_state.confirm_switch:
        target = st.session_state.confirm_switch
        target_label = "MCQ Quiz" if target == "mcq" else "Flashcards"
        st.warning(
            f"⚠️ You haven't finished your current session. "
            f"If you switch to **{target_label}** now, your progress will be lost. "
            f"Are you sure?"
        )
        conf_col1, conf_col2 = st.columns(2)
        with conf_col1:
            if st.button(f"✅ Yes, switch to {target_label}",
                         use_container_width=True, type="primary"):
                st.session_state.timed_mode = False
                st.session_state.last_timer_card = None
                st.session_state.last_timer_mcq = None
                st.session_state.card_start_time = None
                st.session_state.confirm_switch = None
                if target == "mcq":
                    st.session_state.mcq_index = 0
                    st.session_state.mcq_score = 0
                    st.session_state.mcq_answered = False
                    st.session_state.mcq_selected = None
                    st.session_state.mcq_complete = False
                    st.session_state.mcq_skipped = set()
                    st.session_state.app_mode = "mcq"
                    if not st.session_state.mcq_questions:
                        with st.spinner("Generating quiz..."):
                            st.session_state.mcq_questions = generate_mcq(cards)
                            st.session_state.all_asked_mcq = [
                                q["question"]
                                for q in st.session_state.mcq_questions]
                else:
                    st.session_state.flash_position = 0
                    st.session_state.show_answer = False
                    st.session_state.show_hint = False
                    st.session_state.known_cards = set()
                    st.session_state.review_cards = set()
                    st.session_state.skipped_cards = set()
                    st.session_state.review_queue = []
                    st.session_state.streak = 0
                    st.session_state.max_streak = 0
                    st.session_state.app_mode = "flashcard"
                add_to_history(st.session_state.deck_name,
                              "MCQ" if target == "mcq" else "Flashcards")
                st.rerun()
        with conf_col2:
            if st.button("❌ No, keep studying", use_container_width=True):
                st.session_state.confirm_switch = None
                st.rerun()
        st.divider()

    if not st.session_state.confirm_switch:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            flash_btn_type = ("primary" if st.session_state.app_mode == "flashcard"
                              else "secondary")
            if st.button("🃏 Flashcards", use_container_width=True,
                         type=flash_btn_type):
                if st.session_state.app_mode != "flashcard":
                    result = switch_mode("flashcard")
                    if result in ("confirm", "switched"):
                        st.rerun()
        with col_m2:
            mcq_btn_type = ("primary" if st.session_state.app_mode == "mcq"
                            else "secondary")
            if st.button("📝 MCQ Quiz", use_container_width=True,
                         type=mcq_btn_type):
                if st.session_state.app_mode != "mcq":
                    result = switch_mode("mcq")
                    if result == "confirm":
                        st.rerun()
                    elif result in ("switched", "generate_mcq"):
                        if not st.session_state.mcq_questions:
                            with st.spinner("Generating quiz..."):
                                st.session_state.mcq_questions = generate_mcq(cards)
                                st.session_state.all_asked_mcq = [
                                    q["question"]
                                    for q in st.session_state.mcq_questions]
                        add_to_history(st.session_state.deck_name, "MCQ")
                        st.rerun()

    st.divider()

    # ==============================
    # FLASHCARD MODE
    # ==============================
    if st.session_state.app_mode == "flashcard":

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total", total)
        with col2:
            st.metric("Known ✅", known)
        with col3:
            st.metric("Reviewing 🔄", reviewing)
        with col4:
            st.metric("Skipped ⏭️", skipped)
        with col5:
            st.metric("Remaining 📖", remaining)

        current_streak = st.session_state.streak
        best_streak = st.session_state.max_streak
        if current_streak > 0:
            st.markdown(
                f'<div class="streak-box">🔥 {current_streak} card streak!</div>',
                unsafe_allow_html=True)
        elif best_streak > 0:
            st.markdown(
                f'<div class="streak-box" style="background:linear-gradient'
                f'(135deg,#667eea,#764ba2)">🏆 Best streak: {best_streak}</div>',
                unsafe_allow_html=True)

        st.divider()

        if total > 0:
            st.progress(known / total)
            st.markdown(
                f'<p class="progress-text">{known}/{total} mastered — '
                f'{int((known / total) * 100)}% complete</p>',
                unsafe_allow_html=True)

        if known == total or (known + skipped == total):
            st.balloons()
            avg_time = (
                sum(st.session_state.time_per_card.values()) /
                len(st.session_state.time_per_card)
            ) if st.session_state.time_per_card else 0

            perf_score = 0
            if total > 0:
                mastery_score = (known / total) * 70
                streak_score = min(st.session_state.max_streak / total, 1) * 20
                speed_score = 0
                if st.session_state.time_per_card:
                    avg_t = (sum(st.session_state.time_per_card.values()) /
                            len(st.session_state.time_per_card))
                    speed_score = max(0, 10 - (avg_t / 5))
                perf_score = min(100, mastery_score + streak_score + speed_score)
            record_performance(perf_score)

            st.markdown(f"""
<div class="summary-box">
<h2>🎉 Session Complete, {st.session_state.user_name}!</h2>
<p>✅ Mastered: {known} | ⏭️ Skipped: {skipped}</p>
<p>🔥 Best streak: {st.session_state.max_streak} in a row</p>
<p>⏱️ Avg time per card: {avg_time:.1f}s</p>
<p>🏆 Performance Score: {perf_score:.0f}/100</p>
</div>""", unsafe_allow_html=True)

            show_improvement_tracker()

            if st.session_state.user_email and st.session_state.email_reports:
                send_study_report_email(
                    to_email=st.session_state.user_email,
                    user_name=st.session_state.user_name,
                    deck_name=st.session_state.deck_name,
                    score=perf_score,
                    known=known,
                    total=total,
                    streak=st.session_state.max_streak
                )

            if skipped > 0:
                st.warning(f"You skipped {skipped} cards. Want to review them?")
                if st.button("📖 Review Skipped Cards",
                             use_container_width=True, type="primary"):
                    st.session_state.skipped_cards = set()
                    st.session_state.show_answer = False
                    st.session_state.show_hint = False
                    st.rerun()

            st.markdown("### What next?")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("🔄 Study Again", use_container_width=True,
                             type="primary"):
                    reset_study_session()
                    add_to_history(st.session_state.deck_name, "Flashcards")
                    st.rerun()
            with col2:
                if st.button("➕ More Cards", use_container_width=True):
                    with st.spinner("Generating new cards..."):
                        new_cards = generate_flashcards(
                            st.session_state.pdf_text, 10,
                            existing_questions=st.session_state.all_asked_flash)
                        st.session_state.all_asked_flash += [
                            c["question"] for c in new_cards]
                        st.session_state.cards = new_cards
                        reset_study_session()
                        add_to_history(st.session_state.deck_name, "Flashcards")
                        st.rerun()
            with col3:
                if st.button("📝 MCQ Quiz", use_container_width=True):
                    st.session_state.timed_mode = False
                    st.session_state.last_timer_card = None
                    st.session_state.last_timer_mcq = None
                    st.session_state.card_start_time = None
                    st.session_state.app_mode = "mcq"
                    if not st.session_state.mcq_questions:
                        with st.spinner("Generating quiz..."):
                            st.session_state.mcq_questions = generate_mcq(cards)
                    add_to_history(st.session_state.deck_name, "MCQ")
                    st.rerun()
            with col4:
                if st.button("🏠 Dashboard", use_container_width=True):
                    go_to_dashboard()

        else:
            if st.session_state.confirm_switch:
                st.stop()

            unseen = [i for i in range(total)
                     if i not in st.session_state.known_cards
                     and i not in st.session_state.review_cards
                     and i not in st.session_state.skipped_cards]

            all_active = (
                unseen +
                [i for i in st.session_state.review_queue
                 if i not in st.session_state.known_cards] +
                list(st.session_state.skipped_cards)
            )

            seen_set = set()
            ordered = []
            for i in all_active:
                if i not in seen_set:
                    seen_set.add(i)
                    ordered.append(i)

            if not ordered:
                st.rerun()

            if st.session_state.flash_position >= len(ordered):
                st.session_state.flash_position = len(ordered) - 1
            if st.session_state.flash_position < 0:
                st.session_state.flash_position = 0

            current_idx = ordered[st.session_state.flash_position]

            if st.session_state.last_timer_card != current_idx:
                st.session_state.card_start_time = time.time()
                st.session_state.last_timer_card = current_idx

            current_card = cards[current_idx]
            pos = st.session_state.flash_position

            nav1, nav2, nav3, nav4, nav5 = st.columns([1, 1, 3, 1, 1])
            with nav1:
                if st.button("⏮️", use_container_width=True,
                             disabled=pos == 0, help="First card"):
                    st.session_state.flash_position = 0
                    st.session_state.show_answer = False
                    st.session_state.show_hint = False
                    st.session_state.last_timer_card = None
                    st.rerun()
            with nav2:
                if st.button("◀️", use_container_width=True,
                             disabled=pos == 0, help="Previous card"):
                    st.session_state.flash_position = max(0, pos - 1)
                    st.session_state.show_answer = False
                    st.session_state.show_hint = False
                    st.session_state.last_timer_card = None
                    st.rerun()
            with nav3:
                st.markdown(
                    f"<p style='text-align:center;margin-top:8px;"
                    f"color:{text_color}'>"
                    f"<b>Card {pos + 1} of {len(ordered)}</b></p>",
                    unsafe_allow_html=True)
            with nav4:
                if st.button("▶️", use_container_width=True,
                             disabled=pos >= len(ordered) - 1,
                             help="Next card"):
                    st.session_state.flash_position = min(
                        len(ordered) - 1, pos + 1)
                    st.session_state.show_answer = False
                    st.session_state.show_hint = False
                    st.session_state.last_timer_card = None
                    st.rerun()
            with nav5:
                if st.button("⏭️", use_container_width=True,
                             disabled=pos >= len(ordered) - 1,
                             help="Last card"):
                    st.session_state.flash_position = len(ordered) - 1
                    st.session_state.show_answer = False
                    st.session_state.show_hint = False
                    st.session_state.last_timer_card = None
                    st.rerun()

            if current_idx in st.session_state.skipped_cards:
                st.warning("⏭️ This card was skipped")
            elif current_idx in st.session_state.review_cards:
                st.info("🔄 This card is in review")

            st.markdown(
                f'<div class="flashcard">❓ {current_card["question"]}</div>',
                unsafe_allow_html=True)

            if st.session_state.show_hint and not st.session_state.show_answer:
                hint = current_card.get("hint", "Think about the core concept.")
                st.markdown(
                    f'<div class="hint-card">💡 Hint: {hint}</div>',
                    unsafe_allow_html=True)

            if not st.session_state.show_answer:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("👀 Show Answer", use_container_width=True,
                                 type="primary"):
                        elapsed = time.time() - st.session_state.card_start_time
                        st.session_state.time_per_card[current_idx] = elapsed
                        st.session_state.show_answer = True
                        st.session_state.show_hint = False
                        st.rerun()
                with col2:
                    if not st.session_state.show_hint:
                        if st.button("💡 Get Hint", use_container_width=True):
                            st.session_state.show_hint = True
                            st.rerun()
                with col3:
                    if st.button("⏭️ Skip", use_container_width=True):
                        st.session_state.skipped_cards.add(current_idx)
                        st.session_state.review_cards.discard(current_idx)
                        if current_idx in st.session_state.review_queue:
                            st.session_state.review_queue.remove(current_idx)
                        st.session_state.show_answer = False
                        st.session_state.show_hint = False
                        st.session_state.last_timer_card = None
                        if pos < len(ordered) - 1:
                            st.session_state.flash_position += 1
                        st.rerun()
            else:
                st.markdown(
                    f'<div class="answer-card">✅ {current_card["answer"]}</div>',
                    unsafe_allow_html=True)

                st.markdown("**Did you get it?**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Got it!", use_container_width=True,
                                 type="primary"):
                        st.session_state.known_cards.add(current_idx)
                        st.session_state.review_queue = [
                            x for x in st.session_state.review_queue
                            if x != current_idx]
                        st.session_state.review_cards.discard(current_idx)
                        st.session_state.skipped_cards.discard(current_idx)
                        st.session_state.streak += 1
                        if st.session_state.streak > st.session_state.max_streak:
                            st.session_state.max_streak = st.session_state.streak
                        st.session_state.show_answer = False
                        st.session_state.show_hint = False
                        st.session_state.last_timer_card = None
                        if pos < len(ordered) - 1:
                            st.session_state.flash_position += 1
                        st.rerun()
                with col2:
                    if st.button("🔄 Need Review", use_container_width=True):
                        st.session_state.review_cards.add(current_idx)
                        st.session_state.skipped_cards.discard(current_idx)
                        if current_idx in st.session_state.review_queue:
                            st.session_state.review_queue.remove(current_idx)
                        st.session_state.review_queue.append(current_idx)
                        st.session_state.streak = 0
                        st.session_state.show_answer = False
                        st.session_state.show_hint = False
                        st.session_state.last_timer_card = None
                        if pos < len(ordered) - 1:
                            st.session_state.flash_position += 1
                        st.rerun()
                with col3:
                    if st.button("⏭️ Skip", use_container_width=True):
                        st.session_state.skipped_cards.add(current_idx)
                        st.session_state.review_cards.discard(current_idx)
                        if current_idx in st.session_state.review_queue:
                            st.session_state.review_queue.remove(current_idx)
                        st.session_state.show_answer = False
                        st.session_state.show_hint = False
                        st.session_state.last_timer_card = None
                        if pos < len(ordered) - 1:
                            st.session_state.flash_position += 1
                        st.rerun()

                st.markdown("**How difficult was this? (optional)**")
                diff_cols = st.columns(5)
                diff_labels = ["😰 Very Hard", "😟 Hard", "😐 Okay",
                               "🙂 Easy", "😄 Very Easy"]
                for col, label, val in zip(diff_cols, diff_labels, [1, 2, 3, 4, 5]):
                    with col:
                        if st.button(label, key=f"diff_{current_idx}_{val}",
                                    use_container_width=True):
                            st.session_state.difficulty_ratings[current_idx] = val
                            st.rerun()

            if st.session_state.timed_mode and not st.session_state.show_answer:
                elapsed = time.time() - st.session_state.card_start_time
                remaining_time = st.session_state.time_limit - elapsed
                timer_placeholder = st.empty()
                if remaining_time <= 0:
                    timer_placeholder.error("⏰ Time's up! Moving to next card.")
                    st.session_state.skipped_cards.add(current_idx)
                    st.session_state.streak = 0
                    st.session_state.last_timer_card = None
                    st.session_state.show_answer = False
                    st.session_state.show_hint = False
                    if pos < len(ordered) - 1:
                        st.session_state.flash_position += 1
                    st.rerun()
                else:
                    render_timer(remaining_time, timer_placeholder)
                    time.sleep(0.5)
                    st.rerun()

        st.divider()
        if st.button("📋 View All Cards", use_container_width=True):
            st.session_state.study_mode = not st.session_state.study_mode

        if st.session_state.study_mode:
            st.markdown("### 📋 All Cards in This Deck")
            for i, card in enumerate(cards):
                if i in st.session_state.known_cards:
                    status = "✅"
                elif i in st.session_state.skipped_cards:
                    status = "⏭️"
                elif i in st.session_state.review_cards:
                    status = "🔄"
                else:
                    status = "📖"
                diff = st.session_state.difficulty_ratings.get(i)
                diff_text = f" | Difficulty: {diff}/5" if diff else ""
                t = st.session_state.time_per_card.get(i)
                time_text = f" | Time: {t:.1f}s" if t else ""
                with st.expander(
                        f"{status} Card {i + 1}: "
                        f"{card['question'][:60]}..."
                        f"{diff_text}{time_text}"):
                    st.markdown(f"**Q:** {card['question']}")
                    st.markdown(f"**A:** {card['answer']}")
                    if card.get("hint"):
                        st.markdown(f"**💡 Hint:** {card['hint']}")

    # ==============================
    # MCQ MODE
    # ==============================
    elif st.session_state.app_mode == "mcq":

        if not st.session_state.mcq_questions:
            with st.spinner("Generating quiz questions..."):
                st.session_state.mcq_questions = generate_mcq(cards)
                st.session_state.all_asked_mcq = [
                    q["question"] for q in st.session_state.mcq_questions]
            st.rerun()

        mcqs = st.session_state.mcq_questions
        total_mcq = len(mcqs)
        mcq_skipped = len(st.session_state.mcq_skipped)

        if st.session_state.mcq_complete:
            score = st.session_state.mcq_score
            answered = total_mcq - mcq_skipped
            pct = int((score / total_mcq) * 100)
            emoji = "🏆" if pct >= 80 else "👍" if pct >= 60 else "📚"
            msg = ("Outstanding!" if pct >= 80
                   else "Good job!" if pct >= 60 else "Keep studying!")

            add_to_history(st.session_state.deck_name, "MCQ", score=pct)
            record_performance(pct)

            st.markdown(f"""
<div class="summary-box">
<h2>{emoji} Quiz Complete, {st.session_state.user_name}!</h2>
<p style="font-size:22px"><b>{score}/{total_mcq} correct — {pct}%</b></p>
<p>✅ Correct: {score} | ❌ Wrong: {answered - score} | ⏭️ Skipped: {mcq_skipped}</p>
<p>{msg}</p>
</div>""", unsafe_allow_html=True)

            show_improvement_tracker()

            if st.session_state.user_email and st.session_state.email_reports:
                send_study_report_email(
                    to_email=st.session_state.user_email,
                    user_name=st.session_state.user_name,
                    deck_name=st.session_state.deck_name,
                    score=pct,
                    known=score,
                    total=total_mcq,
                    streak=st.session_state.max_streak
                )

            st.markdown("### What next?")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("🔄 Retake Quiz", use_container_width=True,
                             type="primary"):
                    st.session_state.mcq_index = 0
                    st.session_state.mcq_score = 0
                    st.session_state.mcq_answered = False
                    st.session_state.mcq_selected = None
                    st.session_state.mcq_complete = False
                    st.session_state.mcq_skipped = set()
                    st.session_state.last_timer_mcq = None
                    add_to_history(st.session_state.deck_name, "MCQ")
                    st.rerun()
            with col2:
                if st.button("➕ New Questions", use_container_width=True):
                    with st.spinner("Generating new questions..."):
                        new_mcqs = generate_mcq(
                            cards,
                            existing_questions=st.session_state.all_asked_mcq)
                        st.session_state.all_asked_mcq += [
                            q["question"] for q in new_mcqs]
                        st.session_state.mcq_questions = new_mcqs
                        st.session_state.mcq_index = 0
                        st.session_state.mcq_score = 0
                        st.session_state.mcq_answered = False
                        st.session_state.mcq_selected = None
                        st.session_state.mcq_complete = False
                        st.session_state.mcq_skipped = set()
                        st.session_state.last_timer_mcq = None
                        add_to_history(st.session_state.deck_name, "MCQ")
                        st.rerun()
            with col3:
                if st.button("🃏 Flashcards", use_container_width=True):
                    st.session_state.timed_mode = False
                    st.session_state.last_timer_card = None
                    st.session_state.last_timer_mcq = None
                    st.session_state.card_start_time = None
                    st.session_state.app_mode = "flashcard"
                    st.rerun()
            with col4:
                if st.button("🏠 Dashboard", use_container_width=True):
                    go_to_dashboard()

        else:
            if st.session_state.confirm_switch:
                st.stop()

            idx = st.session_state.mcq_index
            current_mcq = mcqs[idx]

            if st.session_state.last_timer_mcq != idx:
                st.session_state.card_start_time = time.time()
                st.session_state.last_timer_mcq = idx

            nav1, nav2, nav3, nav4, nav5 = st.columns([1, 1, 3, 1, 1])
            with nav1:
                if st.button("⏮️", use_container_width=True,
                             disabled=idx == 0, help="First question"):
                    st.session_state.mcq_index = 0
                    st.session_state.mcq_answered = False
                    st.session_state.mcq_selected = None
                    st.session_state.last_timer_mcq = None
                    st.rerun()
            with nav2:
                if st.button("◀️", use_container_width=True,
                             disabled=idx == 0, help="Previous"):
                    st.session_state.mcq_index = max(0, idx - 1)
                    st.session_state.mcq_answered = False
                    st.session_state.mcq_selected = None
                    st.session_state.last_timer_mcq = None
                    st.rerun()
            with nav3:
                st.markdown(
                    f"<p style='text-align:center;margin-top:8px;"
                    f"color:{text_color}'>"
                    f"<b>Question {idx + 1} of {total_mcq}</b></p>",
                    unsafe_allow_html=True)
            with nav4:
                if st.button("▶️", use_container_width=True,
                             disabled=idx >= total_mcq - 1, help="Next"):
                    st.session_state.mcq_index = min(total_mcq - 1, idx + 1)
                    st.session_state.mcq_answered = False
                    st.session_state.mcq_selected = None
                    st.session_state.last_timer_mcq = None
                    st.rerun()
            with nav5:
                if st.button("⏭️", use_container_width=True,
                             disabled=idx >= total_mcq - 1, help="Last"):
                    st.session_state.mcq_index = total_mcq - 1
                    st.session_state.mcq_answered = False
                    st.session_state.mcq_selected = None
                    st.session_state.last_timer_mcq = None
                    st.rerun()

            mcq_c1, mcq_c2, mcq_c3, mcq_c4 = st.columns(4)
            with mcq_c1:
                st.metric("Total", total_mcq)
            with mcq_c2:
                st.metric("Correct ✅", st.session_state.mcq_score)
            with mcq_c3:
                st.metric("Skipped ⏭️", mcq_skipped)
            with mcq_c4:
                st.metric("Remaining 📖", total_mcq - idx)

            st.progress(idx / total_mcq)
            st.divider()

            if st.session_state.mcq_answered:
                sel = st.session_state.mcq_selected
                correct = current_mcq.get("correct", "")
                if sel in ("TIME_UP", "SKIPPED"):
                    feedback = '<span class="feedback-wrong"> ⏭️ skipped</span>'
                elif sel == correct:
                    feedback = '<span class="feedback-correct"> ✨ great!</span>'
                else:
                    feedback = '<span class="feedback-wrong"> it\'s okay, try again!</span>'
                st.markdown(
                    f'<div class="flashcard">❓ {current_mcq["question"]}'
                    f'{feedback}</div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="flashcard">❓ {current_mcq["question"]}</div>',
                    unsafe_allow_html=True)

            st.markdown("**Choose the correct answer:**")
            options = current_mcq.get("options", [])
            correct = current_mcq.get("correct", "")

            if not st.session_state.mcq_answered:
                if st.button("⏭️ Skip this question", use_container_width=False):
                    st.session_state.mcq_skipped.add(idx)
                    st.session_state.mcq_answered = True
                    st.session_state.mcq_selected = "SKIPPED"
                    st.session_state.last_timer_mcq = None
                    st.rerun()

            for option in options:
                if not st.session_state.mcq_answered:
                    if st.button(option, key=f"opt_{idx}_{option}",
                                use_container_width=True):
                        st.session_state.mcq_answered = True
                        st.session_state.mcq_selected = option
                        if option == correct:
                            st.session_state.mcq_score += 1
                        st.session_state.last_timer_mcq = None
                        st.rerun()
                else:
                    sel = st.session_state.mcq_selected
                    if option == correct:
                        st.markdown(
                            f'<div class="mcq-correct">✅ {option}</div>',
                            unsafe_allow_html=True)
                    elif option == sel and option != correct:
                        st.markdown(
                            f'<div class="mcq-wrong">❌ {option}</div>',
                            unsafe_allow_html=True)
                    else:
                        st.markdown(
                            f'<div class="mcq-option">{option}</div>',
                            unsafe_allow_html=True)

            if st.session_state.mcq_answered:
                sel = st.session_state.mcq_selected
                if sel == "TIME_UP":
                    st.error(f"⏰ Time's up! Correct: **{correct}**")
                elif sel == "SKIPPED":
                    st.warning(f"⏭️ Skipped! Correct answer: **{correct}**")
                elif sel == correct:
                    st.success("✅ Correct!")
                else:
                    st.error(f"❌ Wrong! Correct: **{correct}**")

                if idx + 1 >= total_mcq:
                    if st.button("📊 See Results", use_container_width=True,
                                 type="primary"):
                        st.session_state.mcq_complete = True
                        st.rerun()
                else:
                    if st.button("Next Question ➡️", use_container_width=True,
                                 type="primary"):
                        st.session_state.mcq_index += 1
                        st.session_state.mcq_answered = False
                        st.session_state.mcq_selected = None
                        st.session_state.last_timer_mcq = None
                        st.rerun()

            if st.session_state.timed_mode and not st.session_state.mcq_answered:
                elapsed = time.time() - st.session_state.card_start_time
                remaining_time = st.session_state.time_limit - elapsed
                timer_placeholder = st.empty()
                if remaining_time <= 0:
                    timer_placeholder.error("⏰ Time's up!")
                    st.session_state.mcq_answered = True
                    st.session_state.mcq_selected = "TIME_UP"
                    st.session_state.mcq_skipped.add(idx)
                    st.session_state.last_timer_mcq = None
                    st.rerun()
                else:
                    render_timer(remaining_time, timer_placeholder)
                    time.sleep(0.5)
                    st.rerun()