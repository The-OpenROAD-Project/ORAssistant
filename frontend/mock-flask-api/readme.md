# Mock Flask API

Small Flask service that mimics the OpenROAD backend so the Next.js frontend can be developed without the real infrastructure (Postgres, vector DB, LLM).

## Setup
- `cd frontend/mock-flask-api`
- `cp .env.example .env` and tweak values as needed
- `python -m venv .venv && source .venv/bin/activate`
- `pip install -e .` *(installs Flask and Flask-Cors as declared in `pyproject.toml`)*
- `python app.py` or `flask --app app run`

Default environment values start the server on `http://localhost:8000` with debug mode disabled. Update `.env` to change the port or turn on debug logging.

## Configuration
- `FLASK_DEBUG` — set to `True` to enable Flask debug mode.
- `PORT` — port exposed by the mock server (defaults to `8000`).

## Endpoints
- `GET /healthcheck` — returns `{ "status": "ok" }`.
- `POST /helpers/suggestedQuestions` — returns a static list of follow-up questions.
- `POST /conversations` — creates a new in-memory conversation and returns it.
- `GET /conversations` — lists all conversations (metadata only).
- `GET /conversations/<uuid>` — retrieves a conversation with messages.
- `DELETE /conversations/<uuid>` — removes a stored conversation.
- `POST /conversations/agent-retriever` — non-streaming mock response that appends user/assistant messages and returns generated text plus context sources.
- `POST /conversations/agent-retriever/stream` — streams a mock response; first emits `Sources: ...`, then tokens, and stores the final assistant message.

All POST routes now validate JSON payloads and return 400-level errors on malformed input, while global 404/500 handlers keep responses consistent. All data is ephemeral and kept in-memory, so restart the process to reset state.
