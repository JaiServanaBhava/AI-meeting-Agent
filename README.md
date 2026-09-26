# 🎙️ AI Chief of Staff: Intelligent Meeting Coordinator & Summarizer

> **CittaAI RISE Hackathon — Problem Statement 2**  
> **Level 4 Autonomous Multi-Agent Solution** with Level 2 Multimodal Perception  
> Powered Exclusively by **Google Gemini 2.5 Flash** & **SQLite Memory**

---

## 🌟 Executive Summary

Traditional meeting tools merely transcribe audio. The **AI Chief of Staff** manages the complete end-to-end lifecycle of organizational meetings:
1. **Live Capture & Audio Upload**: Records microphone audio in real-time or accepts MP3, WAV, and M4A files.
2. **Speech-to-Text & Acoustic Speaker Diarization**: Converts speech with Whisper and segments conversation by speaker (`Speaker A`, `Speaker B`, `Speaker C`) with Pyannote / acoustic fallback.
3. **CrewAI Multi-Agent Coordination (5 Specialized Agents)**:
   - **🧠 Memory Agent**: Recalls previous commitments from SQLite (e.g. *"Sathwik promised UI by Friday"*), reconciles fulfilled tasks, and logs new pledges.
   - **📝 Meeting Summarizer Agent**: Distills discussions into concise executive summaries and binding decisions.
   - **🎯 Action Item Agent**: Extracts concrete tasks with single owners, hard deadlines, and priority rankings (`High`, `Medium`, `Low`).
   - **📅 Scheduler Agent**: Analyzes follow-up needs, simulates participant calendars, detects conflicts, and suggests consensus slots.
   - **✉️ Email Draft Agent**: Generates personalized follow-up emails for each participant highlighting their specific deliverables.
4. **Persistent SQLite Memory**: Stores meeting records, decisions, action items, email drafts, and cross-meeting commitments.
5. **Modern Streamlit Command Center**: 6 high-end views (Dashboard, Meeting History, Meeting Analysis, Tasks, Follow-up Emails, Memory).

---

## 🏗️ Architecture & Component Flow

```
Live Microphone / Audio File (MP3, WAV, M4A) / Demo Preset
                           │
                           ▼
          Whisper Speech-to-Text Engine
                           │
                           ▼
      Pyannote Speaker Diarization (Speaker A, B, C)
                           │
                           ▼
      ┌──────────────────────────────────────────────┐
      │     CrewAI Multi-Agent Pipeline              │
      │         (Google Gemini 2.5 Flash)            │
      ├──────────────────────────────────────────────┤
      │  1. Memory Agent     ➔ Past Commitments      │
      │  2. Summarizer Agent ➔ Decisions & Brief     │
      │  3. Action Agent     ➔ Owners, Deadlines     │
      │  4. Scheduler Agent  ➔ Calendar Availability │
      │  5. Email Agent      ➔ Personalized Drafts   │
      └──────────────────────────────────────────────┘
                           │
                           ▼
          SQLite Persistent Database (meetings.db)
                           │
                           ▼
         Streamlit Multi-Page Command Center
```

---

## 📁 Repository Structure

```
AI meeting Agent/
├── app.py                       # Root launcher (streamlit run app.py)
├── config.py                    # Environment and path settings
├── requirements.txt             # Pinned Python dependencies
├── .env.example                 # Configuration template
├── .env                         # Active credentials (GEMINI_API_KEY)
│
├── audio/                       # Ingestion, Transcription & Diarization
│   ├── __init__.py
│   ├── recorder.py              # Cross-platform live audio recorder (Mac/Win/Linux)
│   ├── diarizer.py              # Pyannote acoustic speaker clustering & fallback
│   └── transcriber.py           # Whisper STT engine with speaker alignment
│
├── database/                    # SQLite Persistence Engine
│   ├── __init__.py
│   └── db.py                    # Schema initialization, queries, and atomic writes
│
├── memory/                      # Cross-Meeting Intelligence
│   ├── __init__.py
│   └── memory_manager.py        # Commitment reconciliation & accountability engine
│
├── models/                      # Pydantic Schemas & Data Transfer Objects
│   ├── __init__.py
│   └── schemas.py               # Strict structured output definitions
│
├── tools/                       # CrewAI Tools
│   ├── __init__.py
│   ├── memory_tool.py           # Retrieves past commitments from SQLite
│   ├── calendar_tool.py         # Mock availability & conflict detection
│   └── email_tool.py            # Follow-up email dispatcher via SMTP
│
├── agents/                      # Multi-Agent Coordination
│   ├── __init__.py
│   ├── prompts.py               # Specialized agent roles, goals, and backstories
│   └── meeting_crew.py          # CrewAI pipeline + Gemini 2.5 Flash fallback
│
├── services/                    # LLM Clients
│   ├── __init__.py
│   └── gemini_service.py        # Centralized Gemini 2.5 Flash client
│
└── frontend/                    # Streamlit Command Center
    ├── __init__.py
    ├── styles.py                # Modern glassmorphism CSS & badges
    └── app.py                   # Main 6-page dashboard
```

---

## ⚡ Quick Start Guide

### 1. Configure Credentials
Edit `.env` inside `AI meeting Agent/` and insert your **Google Gemini API Key**:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Modes

#### Option A: Standalone Desktop Window with Auto-Meeting Detection (Recommended)
Run in your terminal as a pure Python script (works on **macOS & Windows**):
```bash
python desktop_agent.py
```
* Opens a sleek **native Desktop Pop-up Window** powered by modern HTML5/CSS3.
* **Auto-Detects** when Google Meet (Chrome, Edge, Brave, Safari) or Zoom starts!
* **Auto-Records** audio while you attend the meeting in another tab or app.
* **Auto-Stops & Auto-Analyzes** when the meeting finishes, immediately displaying your Executive Summary, Action Items, Commitments, Calendar, and Follow-up Email!

#### Option B: Streamlit Web Dashboard
Run the multi-page browser interface:
```bash
streamlit run app.py
```

---

## 🎯 6 Interactive Streamlit Views

1. **Dashboard**:
   - Live Microphone capture (`Start Meeting` / `Stop Meeting`).
   - Audio file upload (`.mp3`, `.wav`, `.m4a`).
   - One-click **Simulated Demo Meeting** for instant, zero-latency judging presentations.
   - Status monitor displaying CrewAI agent execution in real time.
2. **Meeting History**:
   - Filterable, searchable archive of all past meetings with full transcripts and executive summaries.
3. **Meeting Analysis**:
   - Diarized conversational turn breakdown with distinct badges for `Speaker A`, `Speaker B`, and `Speaker C`.
   - Simulated calendar conflict resolution and consensus meeting slots.
4. **Tasks & Action Items**:
   - Action item tracker with task description, owner, deadline, and priority badges (`High`, `Medium`, `Low`).
   - Interactive status toggles (`Mark Done` / `Reopen`).
5. **Follow-up Emails**:
   - Tailored, individual follow-up emails for each attendee.
   - In-app editor with 1-click SMTP dispatch.
6. **Meeting Memory**:
   - Persistent ledger tracking promises across meetings.
   - Live query audit proving how promises made in Meeting 1 are recalled and verified in Meeting 2.

---

## 🏆 Hackathon Judging Criteria Alignment

| Criteria | Implementation in Project |
| :--- | :--- |
| **Agentic Autonomy** | 5 autonomous CrewAI agents dynamically chain tasks from transcript to email dispatch without hardcoded scripts. |
| **Tool Reliability** | Dedicated tools for SQLite memory querying, simulated calendar conflict detection, and SMTP mail dispatch. |
| **Error Handling** | Multi-layer fallbacks: If Pyannote token is absent, heuristic acoustic clustering activates; if CrewAI has library conflicts, direct Gemini multi-agent chaining executes. |
| **Scalability** | Clean modular architecture separating audio, agents, memory, tools, services, and frontend. |
| **Demo Quality** | Instant pre-seeded database, rich dark-mode UI, live microphone recording, and instant demo presets. |
# AI-meeting-Agent
