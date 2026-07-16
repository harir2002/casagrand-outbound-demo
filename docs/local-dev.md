# Local development

## Prerequisites

- Python 3.11+
- Node.js 20+
- npm

## 1. Backend

```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health: http://127.0.0.1:8000/health

### Session contract

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| GET | `/projects` | Project list |
| POST | `/session/start` | Start call |
| POST | `/session/turn` | Simulate user turn |
| POST | `/session/reset` | Reset call |
| GET | `/session/state?session_id=` | Fetch state |

## 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173

`frontend/.env`:

```
VITE_USE_MOCK=false
VITE_API_BASE=
```

Empty `VITE_API_BASE` uses the Vite proxy to `http://127.0.0.1:8000`.

## 3. Tests

```bash
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

## Local demo checklist

1. Start backend, then frontend
2. Confirm "Backend online"
3. Start session → Introduction bucket
4. Send `yes` → Education
5. Send `What is the pricing?` → FAQ source updates
6. Send `book a site visit on saturday` → Next steps + memory
7. Send `yes, continue` → Closing summary
8. Reset → Introduction again

## Notes

- Sessions are in-memory only
- CORS allows `localhost:5173` / `127.0.0.1:5173`
- **Live demo providers:** Sarvam STT/TTS + Groq `llama-3.1-8b-instant`
- Set `SARVAM_API_KEY` and `GROQ_API_KEY` in `backend/.env` (never commit secrets)
- Missing keys → `/health` is `degraded` and `/session/turn` returns 503 with a clear message (no silent mock demo path)
- Runtime provider failures degrade to grounded text + warning (not mock swap)
- `PROVIDER_MODE=test` is for automated tests only
- Do not deploy until local tests pass
