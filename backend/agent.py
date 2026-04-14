import os
import requests
from bs4 import BeautifulSoup
from groq import Groq

CATALOG_URL = "https://catalog.morgan.edu/preview_program.php?catoid=26&poid=5968&returnto=1880&print"

def fetch_catalog() -> str:
    try:
        r = requests.get(CATALOG_URL, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.split("\n") if l.strip()]
        full = "\n".join(lines)
        start = full.find("School-wide Requirements")
        return full[start:] if start != -1 else full
    except Exception as e:
        return f"(Catalog unavailable: {e})"


def format_profile(profile: dict) -> str:
    """Turn the student profile dict into a text block for system prompts."""
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
    return "\n".join(lines)


ROUTER_PROMPT = """You are the Morgan State University CS Student Support Router.
Read the student's question and reply with ONLY one of these three words — nothing else:

ADVISING  — degree requirements, prerequisites, course sequencing, graduation pathways, academic planning, advising policies
LEARNING  — CS concepts, programming help, study guidance, course explanations, algorithms, data structures
SUPPORT   — tutoring services, faculty contacts, advisor info, campus resources, department offices, student services

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
Be clear, organized, and student-friendly. Focus especially on freshmen and sophomores but remain helpful for all."""


def make_learning_prompt(catalog: str) -> str:
    return f"""You are the Morgan State University Computer Science Learning Support Agent.

When explaining CS concepts, align your explanations with the Morgan State CS program and courses listed below.
Reference specific Morgan State courses (e.g. COSC 220, COSC 111) when relevant.
Do NOT give advice about other universities' programs.

=== OFFICIAL MORGAN STATE CS CATALOG (for course context) ===
{catalog}
=== END OF CATALOG ===

Help students understand CS concepts, programming topics, algorithms, data structures, and study strategies.
Be encouraging, clear, and beginner-friendly. Use examples and step-by-step explanations."""


def make_support_prompt(catalog: str) -> str:
    return f"""You are the Morgan State University Computer Science Student Support Navigator.

Help students find official Morgan State resources only — do NOT reference other universities.

=== OFFICIAL MORGAN STATE CS CATALOG (for context) ===
{catalog}
=== END OF CATALOG ===

Help students find: professors, advisors, department offices, tutoring, and official morgan.edu pages.
If you don't have specific contact details, direct students to morgan.edu or the CS department directly.
Never guess contact info or links."""


class AgentClass:

    def __init__(self):
        self.client = None
        self.base_prompts = {}

    def set_up(self):
        print("Fetching Morgan State CS catalog...")
        catalog = fetch_catalog()
        print(f"Catalog loaded ({len(catalog)} chars)")
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.base_prompts = {
            "ADVISING": make_advising_prompt(catalog),
            "LEARNING":  make_learning_prompt(catalog),
            "SUPPORT":   make_support_prompt(catalog),
        }

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

        agent_type = self._route(message)

        labels = {
            "ADVISING": "CS Advising Agent",
            "LEARNING":  "Learning Support Agent",
            "SUPPORT":   "Student Support Navigator",
        }

        # Build system prompt: base + optional student profile
        system = self.base_prompts[agent_type]
        if profile:
            system += format_profile(profile)

        # Build message list: system + last 6 history messages + current message
        messages = [{"role": "system", "content": system}]
        if history:
            for h in history[-6:]:
                role = h.get("role", "user")
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