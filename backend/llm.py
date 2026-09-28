"""Thin wrapper around Claude. Returns `fallback` when no API key is set or a call fails."""
import json, os, re
from anthropic import Anthropic

MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5")
_client = Anthropic() if os.getenv("ANTHROPIC_API_KEY") else None


def ask_json(system: str, prompt: str, fallback):
    if not _client:
        return fallback
    try:
        r = _client.messages.create(
            model=MODEL, max_tokens=3000,
            system=system + " Respond with valid JSON only, no prose or code fences.",
            messages=[{"role": "user", "content": prompt}],
        )
        text = re.sub(r"^```(?:json)?|```$", "", r.content[0].text.strip(), flags=re.M).strip()
        return json.loads(text)
    except Exception as e:  # keep the app usable if the LLM misbehaves
        print("LLM error:", e)
        return fallback
