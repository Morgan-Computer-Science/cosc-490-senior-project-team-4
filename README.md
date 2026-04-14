[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=22437819&assignment_repo_type=AssignmentRepo)

# MorganCS Assist

An AI-powered academic assistant for Morgan State University Computer Science students. Built with Flask, Groq (Llama 3.3), and a multi-agent routing system grounded in real Morgan State official data.

---

## What It Does

Students ask questions in plain English and are automatically routed to the right agent:

| Question Type | Agent |
|---|---|
| Degree requirements, prerequisites, course planning | **CS Advising Agent** |
| Programming concepts, algorithms, data structures | **Learning Support Agent** |
| Tutoring, faculty/staff, academic calendar, campus resources | **Student Support Navigator** |

All agents answer exclusively from scraped Morgan State official pages — no generic AI guessing.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask, Flask-CORS |
| AI | Groq API — `llama-3.3-70b-versatile` |
| Data | BeautifulSoup (scrapes 4 Morgan State pages at startup) |
| Frontend | Vanilla HTML / CSS / JS |

---

## Setup

### 1. Clone the repo
```bash
git clone <repo-url>
cd cosc-490-senior-project-team-4
```

### 2. Create a virtual environment and install dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add your Groq API key
Create a file called `.env` inside the `backend/` folder:
```
GROQ_API_KEY=your_key_here
```
Get a free key at [console.groq.com](https://console.groq.com)

### 4. Run the server
```bash
python app.py
```

Open [http://localhost:5001](http://localhost:5001) in your browser.

> **Note:** On first startup the server fetches 4 pages from Morgan State (~10 seconds). A status banner shows when the AI is ready.

---

## Data Sources (scraped live at startup)

| Source | URL |
|--------|-----|
| CS Degree Catalog | catalog.morgan.edu |
| Tutoring Services | morgan.edu/tutoring |
| CS Faculty & Staff | morgan.edu/computer-science/faculty-and-staff |
| Academic Calendar | morgan.edu/academic-calendar |

If any page is unreachable, a static fallback is used so the server never crashes.

---

## Features

- 3 specialized AI agents with automatic routing
- Student profile personalization (name, year, GPA, completed courses, goals)
- Conversation memory — last 6 messages sent with each request
- Chat history persists across page refreshes (localStorage)
- Markdown rendering — bullet lists, bold, code blocks render correctly
- Health check endpoint (`/api/health`) — frontend shows loading banner until ready

---

## Project Structure

```
backend/
├── app.py              # Flask server + API routes
├── agent.py            # Router + 3 AI agents
├── requirements.txt    # Python dependencies
├── .env                # API key (not committed — see .gitignore)
└── static/
    ├── index.html
    ├── style.css
    └── images/
```

---

## Team

COSC 490 Senior Project — Team 4
Morgan State University, Department of Computer Science
