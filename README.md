# Casagrand Voice Agent Demo

Local-first multilingual voice-agent MVP (Tamil / English / Tanglish) for Casagrand Highcity, Avenuepark, and Mercury.

## Stack

- **Frontend:** React + Vite
- **Backend:** FastAPI (Python)
- **Providers:** Swappable STT / TTS / LLM adapters (mock for local demo)

## Quick start

See [docs/local-dev.md](docs/local-dev.md).

```bash
# Backend
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — UI calls the FastAPI contract via Vite proxy.
## Tests

```bash
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

## Scope

1. Introduction
2. Education about the apartment
3. Next steps: book site visit
4. Final summary

Supports intent routing for project info, pricing, location, amenities, site visit, callback, language switch, context switch, out-of-domain fallback, and human handoff.

**Not in this MVP:** cloud deploy, live STT/TTS, paid LLM wiring, persistent session storage.
