# 🎓 AI StudySmart — Your Intelligent AI Learning Companion

> **Learn smarter. Understand faster. Study better with AI.**

A Streamlit-based web application that helps students study more effectively
through AI-powered explanations, summaries, quizzes, and flashcards.

---

## 🎯 Project Objective

AI StudySmart helps students by:

- Explaining complex concepts in simple language
- Summarizing lengthy PDF notes automatically
- Generating multiple-choice quizzes for self-testing
- Creating flashcard decks for quick revision
- Tracking topic-wise performance over time

---

## 🛠️ Technology Stack

| Layer        | Technology          |
|--------------|---------------------|
| Language     | Python 3.10+        |
| Frontend/UI  | Streamlit           |
| Database     | SQLite              |
| AI           | Google Gemini API   |
| PDF parsing  | PyMuPDF             |
| Config       | python-dotenv       |

---

## 🏗️ Architecture

```
User (Browser)
      │
      ▼
  Streamlit (app.py)
      │
      ├── views/          ← One file per feature screen
      ├── ai/             ← AI service + prompt templates
      ├── database/       ← SQLite via Python sqlite3
      └── utils/          ← PDF reader and helpers
```

- **Streamlit** handles the entire frontend — no HTML/JavaScript needed.
- **SQLite** stores quiz results and progress data locally.
- **ai/ai_service.py** is the single integration point for the AI model.
- **views/** keeps each feature isolated and easy to maintain.

---

## 📁 Folder Structure

```
AI_Study_Buddy/
│
├── app.py               ← Main entry point; page routing + sidebar
├── requirements.txt     ← Python dependencies
├── .env.example         ← Environment variable template
├── .gitignore
├── README.md
│
├── ai/
│   ├── __init__.py
│   ├── ai_service.py    ← Gemini API calls (explain, summarize, quiz…)
│   └── prompts.py       ← Prompt templates for each AI feature
│
├── database/
│   ├── __init__.py
│   └── database.py      ← SQLite setup; init_db() and get_connection()
│
├── utils/
│   ├── __init__.py
│   └── pdf_reader.py    ← PDF text extraction via PyMuPDF
│
├── views/
│   ├── __init__.py
│   ├── theme.py         ← Shared CSS design system (do not modify)
│   ├── dashboard.py     ← Home screen with stats and feature overview
│   ├── study_chat.py    ← AI Study Assistant (Gemini Q&A)
│   ├── notes.py         ← Smart Notes (PDF upload + AI summary)
│   ├── quiz.py          ← AI Quiz (MCQ generation + scoring)
│   ├── flashcards.py    ← Flashcard generation + mastery tracking
│   └── progress.py      ← Analytics + AI weak-topic recommendations
│
├── data/                ← SQLite database file (auto-created)
│   └── .gitkeep
│
└── uploads/             ← Uploaded PDF files (auto-created)
    └── .gitkeep
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/ai-studysmart.git
cd ai-studysmart/AI_Study_Buddy
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
# Open .env and add your Gemini API key
# GEMINI_API_KEY=your_key_here
```

---

## ▶️ Running the App

```bash
python -m streamlit run app.py
```

Open your browser at **https://aistudysmart-j6y8gnvqgb9bcyolxmgm5p.streamlit.app/**

---

## 🤖 AI Features

| Feature              | Page                  | AI Function             |
|----------------------|-----------------------|-------------------------|
| Concept explanations | AI Study Assistant    | `generate_ai_response()`|
| PDF summarization    | Smart Notes           | `summarize_notes()`     |
| MCQ quiz generation  | AI Quiz               | `generate_mcqs()`       |
| Flashcard generation | Flashcards            | `generate_flashcards()` |
| Weak topic analysis  | My Progress           | `analyze_weak_topics()` |

---

## 📝 Developer Notes

- All AI logic lives in `ai/` — views never call the API directly.
- API keys are read from environment variables only — never hardcoded.
- The database is auto-created in `data/study_buddy.db` on first run.
- Each view module exposes a single `show()` function called by `app.py`.
- `views/theme.py` is the single CSS source of truth — do not modify.

---

*Built with Streamlit · SQLite · Python · Google Gemini*
