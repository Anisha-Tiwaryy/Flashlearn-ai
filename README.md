
# 🧠 FlashLearn AI

> Turn any PDF into smart, grade-adapted flashcards — and actually remember what you study.



![Python](https://img.shields.io/badge/Python-3.9+-blue)




![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red)




![Groq](https://img.shields.io/badge/Groq-LLaMA3-green)




![License](https://img.shields.io/badge/License-MIT-yellow)



## 🌐 Live Demo
👉 [flashlearn-ai.streamlit.app](https://flashlearn-ai-ndq2s24njrqcimpdijiwnp.streamlit.app/)

---

## 📌 What is FlashLearn AI?

FlashLearn AI is an AI-powered study tool that transforms any PDF into 
an interactive study session in under 30 seconds. Upload your notes, 
textbook chapters, or research papers and instantly get:

- **Grade-adapted flashcards** — content difficulty automatically adjusts 
  based on your grade level (Grade 1 through Postgraduate)
- **MCQ Quiz mode** — multiple choice questions generated from your content
- **Timed mode** — countdown timer per card to sharpen focus
- **Streak tracking** — stay motivated with streak counters and performance scores
- **Email study reports** — get a summary sent to your inbox after every session

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 PDF Upload | Upload any PDF and extract study content instantly |
| 🎓 Grade Adaptation | Cards adapt in language and depth from Grade 1 to Postgraduate |
| 🃏 Flashcard Mode | Flip cards, get hints, mark as Known / Review / Skip |
| 📝 MCQ Quiz | Auto-generated multiple choice with instant feedback |
| ⏱️ Timed Mode | Countdown timer per card, auto-skips on timeout |
| 🔥 Streak Tracker | Tracks consecutive correct answers and best streak |
| 📊 Performance Score | Calculated from mastery, streak and speed |
| 📧 Email Reports | Study summaries sent via Resend after session completion |
| 🌙 Dark / Light Mode | Toggle between themes anytime |
| 🏠 Dashboard Navigation | Clean home button to go back anytime |

---

## 🛠️ Tech Stack

- **Frontend & Backend** — [Streamlit](https://streamlit.io)
- **LLM** — [Groq API](https://groq.com) with LLaMA 3.3 70B Versatile
- **PDF Parsing** — PyPDF2
- **Email** — [Resend](https://resend.com)
- **Deployment** — Streamlit Community Cloud

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/Anisha-Tiwaryy/Flashlearn-ai.git
cd Flashlearn-ai
2. Install dependencies
pip install -r requirements.txt
3. Set up environment variables
Create a .env file in the root folder:
GROQ_API_KEY=your_groq_api_key_here
RESEND_API_KEY=your_resend_api_key_here
4. Run the app
streamlit run app.py
📁 Project Structure
flashlearn-ai/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .gitignore          # Ignores .env and secrets
└── README.md           # This file
🔑 API Keys Required
Service
Purpose
Free Tier
Groq
LLM for generating flashcards and MCQs
Free
Resend
Email study reports
3,000 emails/month free
🧠 How It Works
Upload any PDF study material
Set your grade — the AI adapts question complexity accordingly
Study with flashcards — flip, hint, mark, skip
Take the MCQ quiz — test yourself with multiple choice
Track your progress — streaks, scores, history
Receive your report — email summary after each session
🎯 Key Design Decisions
Grade-adaptive prompts — Instead of one generic prompt, the app maps
each grade level to specific difficulty instructions. A Grade 6 student
and a Postgraduate uploading the same PDF get completely different
questions — different language, different depth, different complexity.
Timer architecture — The timer renders after the question and buttons
load, never before. This prevents the common Streamlit issue where
time.sleep() causes the page to rerun before content renders,
making questions disappear.
Mode-switch protection — Switching between flashcards and MCQ
mid-session shows a confirmation dialog so progress is never
accidentally lost.
Secure API handling — No API keys in the codebase. Keys are loaded
from environment variables locally and Streamlit secrets in production.
📈 What I'd Add With More Time
Supabase integration — persistent user accounts so history
survives across sessions
SM-2 spaced repetition — proper algorithm replacing the
current review queue
OCR support — handle scanned PDFs using pytesseract
Anki export — download flashcards as Anki-compatible CSV
Scheduled streak reminders — daily email reminders via cron,
not just on session complete
👩‍💻 Built By
Anisha Tiwary
📧 anishadgp04@gmail.com
🐙 github.com/Anisha-Tiwaryy



