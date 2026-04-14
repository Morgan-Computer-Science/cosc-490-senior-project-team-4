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

ROUTER_PROMPT = """You are the Morgan State University CS Student Support Router.
Read the student's question and reply with ONLY one of these three words — nothing else:

ADVISING  — degree requirements, prerequisites, course sequencing, graduation pathways, academic planning, advising policies
LEARNING  — CS concepts, programming help, study guidance, course explanations, algorithms, data structures
SUPPORT   — tutoring services, faculty contacts, advisor info, campus resources, department offices, student services

Reply with exactly one word."""

def make_advising_prompt(catalog):
    return f"""You are the Morgan State University Computer Science Advising Agent.

You MUST answer ONLY using the official Morgan State University CS program information provided below.
Do NOT answer based on general knowledge or other universities.
If the answer is not in the catalog data, say: "I don't have that specific information in the official catalog. Please contact the CS department or visit morgan.edu for more details."

=== OFFICIAL MORGAN STATE CS CATALOG ===
{catalog}
=== END OF CATALOG ===

Help students with course prerequisites, sequencing, degree requirements, graduation pathways, and academic planning.
Be clear, organized, and student-friendly."""

def make_learning_prompt(catalog):
    return f"""You are the Morgan State University Computer Science Learning Support Agent.

When explaining CS concepts, align your explanations with the Morgan State CS program and courses listed below.
Reference specific Morgan State courses (e.g. COSC 220, COSC 111) when relevant.
Do NOT give advice about other universities' programs.

=== OFFICIAL MORGAN STATE CS CATALOG (for course context) ===
{catalog}
=== END OF CATALOG ===

Help students understand CS concepts, programming topics, algorithms, data structures, and study strategies.
Be encouraging, clear, and beginner-friendly."""

def make_support_prompt(catalog):
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
        self.prompts = {}

    def set_up(self):
        print("Fetching Morgan State CS catalog...")
        catalog = fetch_catalog()
        print(f"Catalog loaded ({len(catalog)} chars)")
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.prompts = {
            "ADVISING": make_advising_prompt(catalog),
            "LEARNING":  make_learning_prompt(catalog),
            "SUPPORT":   make_support_prompt(catalog),
        }

    def _route(self, query):
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user",   "content": query},
            ],
            max_tokens=5, temperature=0,
        )
        decision = response.choices[0].message.content.strip().upper()
        if "ADVISING" in decision:   return "ADVISING"
        elif "LEARNING" in decision: return "LEARNING"
        else:                        return "SUPPORT"

    def query(self, message, user_id="test"):
        agent_type = self._route(message)
        labels = {
            "ADVISING": "CS Advising Agent",
            "LEARNING":  "Learning Support Agent",
            "SUPPORT":   "Student Support Navigator",
        }
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": self.prompts[agent_type]},
                {"role": "user",   "content": message},
            ],
            temperature=0.7, max_tokens=1024,
        )
        return {"reply": response.choices[0].message.content, "agent": labels[agent_type]}


app = AgentClass()