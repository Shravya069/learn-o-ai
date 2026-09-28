# Learn O AI

Turn a student's syllabus into story-based learning episodes, test them, find weak topics, and re-teach only those.
**Learn → Test → Analyze → Revise → Retest → Improve**

Each student gets a long-term **Hindsight memory bank**, so episodes and recommendations adapt over time.

## How Hindsight is used
| Moment | Hindsight call | What is stored / used |
|---|---|---|
| Student picks a character | `retain` | preferred character for a subject |
| Test submitted | `retain` | per-concept score + level (e.g. "Constructors 35% → Needs Revision") |
| Episode requested | `recall` | weak areas and preferences injected into the story prompt |
| Dashboard / next step | `reflect` | AI recommendation over the full history |

Banks are named `student-<id>`. If the Hindsight server is down, `backend/memory.py` falls back to an in-memory list so dev still works.

## Run it
```bash
cp .env.example .env            # add ANTHROPIC_API_KEY (optional) and Hindsight settings
docker compose up -d            # Hindsight API :8888, UI :9999
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd backend && uvicorn main:app --reload
```
Open http://localhost:8000 (prototype UI) or http://localhost:8000/docs (API).

Without `HINDSIGHT_LLM_API_KEY` in the environment, the Hindsight container can't extract facts; set it (see `.env.example`) before `docker compose up`.

## API
`POST /api/syllabus` · `POST /api/episode` · `POST /api/test` · `POST /api/submit` · `POST /api/revise` · `GET /api/recommend/{student_id}`

Try it:
```bash
curl -X POST localhost:8000/api/submit -H 'content-type: application/json' -d '{"student_id":"riya","subject":"Java","topic":"OOP","answers":[{"concept":"Constructors","correct":false},{"concept":"Constructors","correct":false},{"concept":"Classes","correct":true}]}'
curl "localhost:8000/api/recommend/riya?subject=Java"
```

## Status
- `frontend/index.html` is the standalone clickable prototype (pre-written Java content). Wiring it to `/api/*` is the next step.
- Animated video episodes need a separate video-generation pipeline.
- Use **original characters**. Licensed characters (Doraemon, Shinchan, etc.) need permission for commercial use.
- Check the Hindsight docs for current client options: https://hindsight.vectorize.io
