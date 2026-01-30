# Career Clarity

Career Clarity is a web-based career guidance application designed to help users reflect on their interests, emotions, and goals, and receive structured career recommendations with actionable learning roadmaps.

The app focuses on clarity over pressure, combining reflective questioning, empathetic support, and practical next steps.

---

## Features

### 1. Guided Career Questions
- Step-by-step questionnaire
- Mix of multi-select, single-choice, and open-text inputs
- Designed to capture interests, values, pace preferences, and goals
- Progress preserved across refreshes using per-user state

### 2. Empathy Session
- Optional venting space before starting questions
- Chat-style interface with persistent conversation history
- Focused on emotional validation and reassurance
- Input clears automatically after sending messages

### 3. Career Recommendations
- Generates exactly three career paths
- Recommendations are domain-consistent (engineering, medicine, arts, etc.)
- Tailored to Indian education and salary realities
- Clear descriptions and expected salary ranges

### 4. Personalized Roadmaps
- Choose roadmap duration: 30 days, 3–6 months, or 1 year
- Daily structured plans with learning goals and tasks
- Progress tracking per day
- Downloadable PDF of the roadmap

### 5. Support Mentor Chat
- Career-focused Q&A during roadmap execution
- Persistent chat history
- Input refreshes after each message

---

## Tech Stack

- Frontend & Backend: Streamlit
- LLM Integration: Groq API (LLaMA-based models)
- State Management: Streamlit session state with encrypted cookies
- Persistence: Pickle-based per-user state files
- PDF Generation: ReportLab

---

## Key Design Principles

- User-first flow
- Emotional safety before decision-making
- Minimal cognitive load per screen
- Persistence across refreshes
- Clear separation of application phases

---

## Running Locally

1. Clone the repository:
2. Install dependencies:
3. Set the Groq API key:
4. Run the application:

---

## Current Status

- Core features complete
- Stable user flow
- Deployed and functional
- Version 1

---

## License

This project is intended for educational and experimental use.
