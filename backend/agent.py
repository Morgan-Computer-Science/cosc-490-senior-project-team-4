import os
import requests
from bs4 import BeautifulSoup
from groq import Groq

CATALOG_URL  = "https://catalog.morgan.edu/preview_program.php?catoid=26&poid=5968&returnto=1880&print"
TUTORING_URL = "https://www.morgan.edu/tutoring"
FACULTY_URL  = "https://www.morgan.edu/computer-science/faculty-and-staff"
CALENDAR_URL = "https://www.morgan.edu/academic-calendar"

# ── Static fallbacks used when a page cannot be scraped ──────────────────────
TUTORING_FALLBACK = """Morgan State University Academic Success Center provides tutoring services for students.
Tutoring is available for CS courses including introductory programming, data structures, algorithms, and more.
Peer tutoring and Supplemental Instruction sessions are offered each semester.
For current hours, locations, and scheduling visit: https://www.morgan.edu/tutoring
Students can also attend faculty office hours — check the CS department for schedules."""

FACULTY_FALLBACK = """The Morgan State University Computer Science Department faculty and staff directory
is available at: https://www.morgan.edu/computer-science/faculty-and-staff
Contact the CS Department office for specific faculty information, office hours, or email addresses.
The CS Department is located in the Earl S. Richardson Library building."""

CALENDAR_FALLBACK = """The Morgan State University Academic Calendar contains important dates including:
registration periods, add/drop deadlines, holidays, final exam schedules, and commencement dates.
Full calendar: https://www.morgan.edu/academic-calendar
Contact the Registrar's office for specific deadline questions."""

CATALOG_FALLBACK = """Morgan State University Computer Science program information is available at:
https://catalog.morgan.edu
Contact the CS Department or academic advisor for degree requirements and course planning."""


def _scrape(url: str, label: str, fallback: str) -> str:
    """Scrape a URL and return clean text, or fallback if unavailable."""
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "aside"]):
            tag.decompose()
        text  = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if l.strip()]
        result = "\n".join(lines)
        if len(result) < 200:
            print(f"  WARNING: {label} returned very little content — using fallback.")
            return fallback
        return result
    except Exception as e:
        print(f"  WARNING: Could not fetch {label} ({e}) — using fallback.")
        return fallback


def fetch_catalog() -> str:
    try:
        r = requests.get(CATALOG_URL, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            tag.decompose()
        text  = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if l.strip()]
        full  = "\n".join(lines)
        start = full.find("School-wide Requirements")
        result = full[start:] if start != -1 else full
        if len(result) < 200:
            print("  WARNING: Catalog returned very little content — using fallback.")
            return CATALOG_FALLBACK
        return result
    except Exception as e:
        print(f"  WARNING: Could not fetch catalog ({e}) — using fallback.")
        return CATALOG_FALLBACK


def fetch_tutoring() -> str:
    return _scrape(TUTORING_URL, "Tutoring page", TUTORING_FALLBACK)

def fetch_faculty() -> str:
    return _scrape(FACULTY_URL, "Faculty & Staff page", FACULTY_FALLBACK)

def fetch_calendar() -> str:
    return _scrape(CALENDAR_URL, "Academic Calendar page", CALENDAR_FALLBACK)


def format_profile(profile: dict) -> str:
    if not profile:
        return ""
    lines = ["\n=== STUDENT PROFILE (use this to personalize your response) ==="]
    if profile.get("name"):
        lines.append(f"Student name: {profile['name']}")
    if profile.get("year"):
        lines.append(f"Class year: {profile['year']}")
    if profile.get("gpa"):
        lines.append(f"Current GPA: {profile['gpa']}")
    if profile.get("coursesTaken"):
        lines.append(f"Courses already completed: {profile['coursesTaken']}")
    if profile.get("helpNeeded"):
        lines.append(f"Areas needing most help: {profile['helpNeeded']}")
    if profile.get("goals"):
        lines.append(f"Student goals/notes: {profile['goals']}")
    lines.append("=== END OF STUDENT PROFILE ===")
    lines.append(
        "Address the student by name if provided. "
        "Tailor your response specifically to their year, completed courses, and goals. "
        "If they are a freshman or sophomore, be extra detailed and encouraging. "
        "If they are a junior or senior, you can assume more background knowledge."
    )

    # ── Transcript ──
    if profile.get("transcriptText"):
        lines.append(
            "\n=== STUDENT TRANSCRIPT / DEGREEWORKS (uploaded by student) ===\n"
            + profile["transcriptText"].strip()
            + "\n=== END OF TRANSCRIPT ==="
        )
        lines.append(
            "Use the transcript above to identify exactly which courses this student has "
            "already completed, their grades, credit hours earned, and what requirements "
            "remain. Base course recommendations and degree planning on this data."
        )

    # ── Resume ──
    if profile.get("resumeText"):
        lines.append(
            "\n=== STUDENT RESUME (uploaded by student) ===\n"
            + profile["resumeText"].strip()
            + "\n=== END OF RESUME ==="
        )
        lines.append(
            "Use the resume above to give targeted career guidance. Reference the student's "
            "actual skills, projects, work experience, and internships when suggesting "
            "next steps, job roles, or areas to strengthen."
        )

    return "\n".join(lines)


ROUTER_PROMPT = """You are the Morgan State University CS Student Support Router.
Read the student's question and reply with ONLY one of these three words — nothing else:

ADVISING  — degree requirements, prerequisites, course sequencing, graduation pathways, academic planning,
             which courses to take, how many credits, GPA requirements, transfer credits, advising policies

LEARNING  — CS concepts, programming help, study guidance, how to code something, debugging,
             algorithms, data structures, explaining course material, homework concepts

SUPPORT   — tutoring services, where to get help, who teaches a course, professor names, faculty contacts,
             advisor contacts, office locations, department phone/email, campus resources, student services,
             academic calendar, registration dates, deadlines, add/drop, financial aid deadlines

When in doubt about faculty/professors/who-teaches, always reply SUPPORT.
Reply with exactly one word."""


def make_advising_prompt(catalog: str) -> str:
    return f"""You are the Morgan State University Computer Science Advising Agent.

You MUST answer ONLY using the official Morgan State University CS program information provided below.
Do NOT answer based on general knowledge or other universities.
If the answer is not in the catalog data, say: "I don't have that specific information in the official catalog. Please contact the CS department or visit morgan.edu for more details."

=== OFFICIAL MORGAN STATE CS CATALOG ===
{catalog}
=== END OF CATALOG ===

Help students with course prerequisites, sequencing, degree requirements, graduation pathways, and academic planning.
Be clear, organized, and student-friendly. Use bullet points and numbered lists for clarity.
If the student has uploaded a transcript or DegreeWorks audit, use it to give specific, accurate advice about what they still need to complete.
Focus especially on freshmen and sophomores but remain helpful for all."""


def make_learning_prompt(catalog: str) -> str:
    return f"""You are the Morgan State University Computer Science Learning Support Agent.

When explaining CS concepts, align your explanations with the Morgan State CS program and courses listed below.
Reference specific Morgan State courses (e.g. COSC 220, COSC 111) when relevant.
Do NOT give advice about other universities' programs.

=== OFFICIAL MORGAN STATE CS CATALOG (for course context) ===
{catalog}
=== END OF CATALOG ===

Help students understand CS concepts, programming topics, algorithms, data structures, and study strategies.
Be encouraging, clear, and beginner-friendly. Use examples, step-by-step explanations, and code snippets where helpful."""


def make_support_prompt(catalog: str, tutoring: str, faculty: str, calendar: str) -> str:
    return f"""You are the Morgan State University Computer Science Student Support Navigator.

Answer ONLY using the official Morgan State information provided below.
Do NOT reference other universities or make up contact details, names, or links.

=== MORGAN STATE TUTORING SERVICES (morgan.edu/tutoring) ===
{tutoring}
=== END OF TUTORING ===

=== MORGAN STATE CS FACULTY & STAFF (morgan.edu/computer-science/faculty-and-staff) ===
{faculty}
=== END OF FACULTY & STAFF ===

=== MORGAN STATE ACADEMIC CALENDAR (morgan.edu/academic-calendar) ===
{calendar}
=== END OF ACADEMIC CALENDAR ===

=== OFFICIAL MORGAN STATE CS CATALOG (for additional context) ===
{catalog}
=== END OF CATALOG ===

Use the actual content above to answer student questions in detail.
When sharing URLs always use the exact official links:
  - Tutoring:       https://www.morgan.edu/tutoring
  - Faculty/Staff:  https://www.morgan.edu/computer-science/faculty-and-staff
  - Calendar:       https://www.morgan.edu/academic-calendar
If the student has uploaded a resume, use it to give specific career guidance based on their actual skills, experience, and projects.
If information is not in any source above, say so and direct students to morgan.edu."""


class AgentClass:

    def __init__(self):
        self.client = None
        self.base_prompts = {}
        self.ready = False

    def set_up(self):
        print("=" * 50)
        print("MorganCS Assist — loading data sources...")
        print("=" * 50)

        catalog  = fetch_catalog();  print(f"  Catalog loaded       ({len(catalog):,} chars)")
        tutoring = fetch_tutoring(); print(f"  Tutoring loaded      ({len(tutoring):,} chars)")
        faculty  = fetch_faculty();  print(f"  Faculty/Staff loaded ({len(faculty):,} chars)")
        calendar = fetch_calendar(); print(f"  Calendar loaded      ({len(calendar):,} chars)")

        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.base_prompts = {
            "ADVISING": make_advising_prompt(catalog),
            "LEARNING":  make_learning_prompt(catalog),
            "SUPPORT":   make_support_prompt(catalog, tutoring, faculty, calendar),
        }
        self.ready = True
        print("=" * 50)
        print("All agents ready. Starting server...")
        print("=" * 50)

    def _route(self, query: str) -> str:
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user",   "content": query},
            ],
            max_tokens=5,
            temperature=0,
        )
        decision = response.choices[0].message.content.strip().upper()
        if "ADVISING" in decision:   return "ADVISING"
        elif "LEARNING" in decision: return "LEARNING"
        else:                        return "SUPPORT"

    def query(self, message: str, user_id: str = "test",
              history: list = None, profile: dict = None) -> dict:

        if not self.ready:
            return {"error": "The AI is still loading. Please wait a moment and try again."}

        agent_type = self._route(message)

        labels = {
            "ADVISING": "CS Advising Agent",
            "LEARNING":  "Learning Support Agent",
            "SUPPORT":   "Student Support Navigator",
        }

        system = self.base_prompts[agent_type]
        if profile:
            system += format_profile(profile)

        messages = [{"role": "system", "content": system}]
        if history:
            for h in history[-6:]:
                role    = h.get("role", "user")
                content = h.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": message})

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )

        return {
            "reply": response.choices[0].message.content,
            "agent": labels[agent_type],
        }


app = AgentClass()