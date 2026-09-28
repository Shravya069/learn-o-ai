"""Per-student long-term memory on top of Hindsight (https://github.com/vectorize-io/hindsight).

One memory bank per student: bank_id = "student-<id>".
  retain  -> store quiz results, character choices, revision outcomes
  recall  -> fetch what the student struggles with / prefers
  reflect -> AI-written recommendation over the whole history

If the Hindsight server is unreachable we fall back to an in-process list so local dev still works.
"""
import os
from datetime import datetime, timezone

try:
    from hindsight_client import Hindsight
except ImportError:  # pragma: no cover
    Hindsight = None


class StudentMemory:
    def __init__(self):
        self.client = None
        self.local: dict[str, list[str]] = {}
        if Hindsight:
            try:
                kw = {"base_url": os.getenv("HINDSIGHT_URL", "http://localhost:8888")}
                if os.getenv("HINDSIGHT_API_KEY"):
                    kw["api_key"] = os.getenv("HINDSIGHT_API_KEY")
                self.client = Hindsight(**kw)
            except Exception as e:
                print("Hindsight unavailable, using local fallback:", e)

    @staticmethod
    def bank(student_id: str) -> str:
        return f"student-{student_id}"

    def retain(self, student_id: str, content: str, context: str = "learning event"):
        self.local.setdefault(student_id, []).append(content)
        if not self.client:
            return
        try:
            self.client.retain(
                bank_id=self.bank(student_id), content=content, context=context,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            print("Hindsight retain failed:", e)

    def recall(self, student_id: str, query: str) -> list[str]:
        if self.client:
            try:
                res = self.client.recall(bank_id=self.bank(student_id), query=query)
                return [r.text for r in res.results]
            except Exception as e:
                print("Hindsight recall failed:", e)
        return self.local.get(student_id, [])[-10:]

    def reflect(self, student_id: str, query: str) -> str:
        if self.client:
            try:
                ans = self.client.reflect(bank_id=self.bank(student_id), query=query)
                return getattr(ans, "text", None) or str(ans)
            except Exception as e:
                print("Hindsight reflect failed:", e)
        notes = self.local.get(student_id, [])
        return "Recent activity: " + " | ".join(notes[-3:]) if notes else "No history yet."


memory = StudentMemory()
