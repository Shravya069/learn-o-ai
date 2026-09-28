"""Learn O AI backend: syllabus -> episode -> test -> analysis -> revision, with Hindsight memory."""
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from llm import ask_json
from memory import memory

app = FastAPI(title="Learn O AI")


# ---------- models ----------
class SyllabusIn(BaseModel):
    text: str

class EpisodeIn(BaseModel):
    student_id: str
    subject: str
    topic: str
    character: str = "Learn O Robot"
    concepts: list[str] | None = None   # set for revision episodes
    level: str = "Beginner"

class TestIn(BaseModel):
    subject: str
    topic: str
    concepts: list[str]
    per_concept: int = 2

class Answer(BaseModel):
    concept: str
    correct: bool

class SubmitIn(BaseModel):
    student_id: str
    subject: str
    topic: str
    answers: list[Answer]


# ---------- helpers ----------
def level(pct: int) -> str:
    return "Strong" if pct >= 80 else "Developing" if pct >= 50 else "Needs Revision"


# ---------- routes ----------
@app.post("/api/syllabus")
def parse_syllabus(body: SyllabusIn):
    """Break raw syllabus text into subject -> units -> topics."""
    lines = [l.strip() for l in body.text.splitlines() if l.strip()]
    fallback = {"subject": "Your Subject", "units": [{"title": "Unit 1", "topics": lines}]}
    return ask_json(
        "You structure syllabi.",
        'Return {"subject": str, "units": [{"title": str, "topics": [str]}]} for this syllabus:\n' + body.text,
        fallback,
    )


@app.post("/api/episode")
def episode(body: EpisodeIn):
    """Story episode. Hindsight memories personalise it (weak areas, past choices)."""
    focus = body.concepts or [body.topic]
    past = memory.recall(body.student_id, f"What does this student struggle with or prefer in {body.subject}?")
    memory.retain(body.student_id, f"Student chose the character '{body.character}' to learn {body.subject}: {body.topic}.", "character choice")
    fallback = {
        "title": f"{body.character}'s {body.subject} Adventure",
        "scenes": [{"speaker": body.character, "line": f"Today we learn about {c}!", "visual": "🎬", "concept": c} for c in focus],
        "ask": None,
    }
    return ask_json(
        "You write short, accurate, kid-friendly educational story episodes. Use ONLY original characters/worlds.",
        f"""Subject: {body.subject}. Topic: {body.topic}. Level: {body.level}. Character: {body.character}.
Concepts to teach: {focus}.
What we remember about this student: {past}.
If memory shows weak areas, spend extra time on those and use simpler examples.
Return {{"title": str, "scenes": [{{"speaker": str, "line": str, "visual": emoji, "concept": str}}],
"ask": {{"q": str, "options": [str], "answer": int, "feedback": str}} }} with 4-6 scenes.""",
        fallback,
    )


@app.post("/api/test")
def make_test(body: TestIn):
    fallback = {"questions": [{"concept": c, "type": "mcq", "q": f"Which best describes {c}?",
                               "options": ["Option A", "Option B"], "answer": 0} for c in body.concepts]}
    return ask_json(
        "You write fair quiz questions.",
        f"""Subject: {body.subject}, topic: {body.topic}. Write {body.per_concept} questions per concept for: {body.concepts}.
Mix types "mcq", "tf", "fill". Return {{"questions": [{{"concept": str, "type": str, "q": str, "options": [str], "answer": str|int|bool}}]}}""",
        fallback,
    )


@app.post("/api/submit")
def submit(body: SubmitIn):
    """Score per concept, save each result to the student's memory bank, return the report."""
    stats: dict[str, list[int]] = {}
    for a in body.answers:
        s = stats.setdefault(a.concept, [0, 0]); s[1] += 1; s[0] += int(a.correct)
    report = []
    for concept, (c, t) in stats.items():
        pct = round(100 * c / t)
        report.append({"concept": concept, "percent": pct, "level": level(pct)})
        memory.retain(
            body.student_id,
            f"In {body.subject} ({body.topic}), the student scored {pct}% on '{concept}' -> {level(pct)}.",
            "quiz result",
        )
    total = round(100 * sum(a.correct for a in body.answers) / max(1, len(body.answers)))
    return {"score": total, "report": report,
            "weak": [r["concept"] for r in report if r["percent"] < 80]}


@app.post("/api/revise")
def revise(body: EpisodeIn):
    """Targeted revision episode: pass the weak concepts in `concepts`."""
    memory.retain(body.student_id, f"Student started a revision episode on {body.concepts} in {body.subject}.", "revision")
    return episode(body)


@app.get("/api/recommend/{student_id}")
def recommend(student_id: str, subject: str = ""):
    """Hindsight `reflect` over the whole history -> what to study next."""
    text = memory.reflect(
        student_id,
        f"Based on this student's history{' in ' + subject if subject else ''}, which topic should they study next and why? Be brief.",
    )
    return {"recommendation": text}


# Serve the prototype UI (register last so /api routes win)
app.mount("/", StaticFiles(directory=Path(__file__).parent.parent / "frontend", html=True), name="ui")
