# Grid07 Cognitive Routing & RAG

This repository implements the three-part Grid07 AI engineering assignment:

1. vector-based persona routing with FAISS
2. a LangGraph content engine with a mock search tool and strict JSON output
3. a deep-thread RAG combat engine with prompt-injection defense

The repo is also cleaned up into a resume-ready project with tests, a CLI, an HTTP API, and optional deployment assets.

## Deliverables map

- Python code:
  - [grid07/router.py](/Users/dikshashahi/Documents/Codex/2026-05-06/files-mentioned-by-the-user-combat/grid07/router.py)
  - [grid07/content_engine.py](/Users/dikshashahi/Documents/Codex/2026-05-06/files-mentioned-by-the-user-combat/grid07/content_engine.py)
  - [grid07/combat_engine.py](/Users/dikshashahi/Documents/Codex/2026-05-06/files-mentioned-by-the-user-combat/grid07/combat_engine.py)
- Requirements file:
  - [requirements.txt](/Users/dikshashahi/Documents/Codex/2026-05-06/files-mentioned-by-the-user-combat/requirements.txt)
- Example env file:
  - [.env.example](/Users/dikshashahi/Documents/Codex/2026-05-06/files-mentioned-by-the-user-combat/.env.example)
- Execution logs:
  - [execution_logs.md](/Users/dikshashahi/Documents/Codex/2026-05-06/files-mentioned-by-the-user-combat/execution_logs.md)

## Project structure

```text
.
├── grid07/
│   ├── api.py
│   ├── cli.py
│   ├── combat_engine.py
│   ├── content_engine.py
│   ├── domain.py
│   ├── personas.py
│   ├── providers.py
│   └── router.py
├── tests/
├── persona_router.py
├── content_engine.py
├── combat_engine.py
├── execution_logs.md
├── requirements.txt
├── requirements-deploy.txt
├── requirements-dev.txt
├── requirements-semantic.txt
├── Dockerfile
└── render.yaml
```

## Setup

Assignment-aligned install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
pytest
```

Lightweight deployment install:

```bash
pip install -r requirements-deploy.txt
```

## Phase 1: Vector-Based Persona Matching

The router stores persona descriptions in an in-memory FAISS index when the semantic stack is available. Each persona is embedded with `sentence-transformers/all-MiniLM-L6-v2`, normalized, and inserted into an inner-product FAISS index so inner product is equivalent to cosine similarity.

The assignment-facing helper is:

```python
route_post_to_bots(post_content: str, threshold: float = 0.85)
```

Important note: MiniLM embeddings usually produce realistic cosine scores lower than `0.85` for related but non-identical text. The default function signature matches the assignment, but the demo logs use a calibrated threshold closer to `0.30` so the sample routing behavior is visible.

## Phase 2: LangGraph Content Engine

The content engine uses a three-node LangGraph state machine:

1. `decide_search`
   - input: bot persona
   - output: a short search query representing what the bot wants to post about
2. `web_search`
   - executes `mock_searxng_search(query: str)`
   - returns a hardcoded but recent-looking headline for the chosen topic
3. `draft_post`
   - combines persona + headline context
   - returns a strict JSON-shaped result:
   - `{"bot_id": "...", "topic": "...", "post_content": "..."}`

The project includes a local sequential fallback so tests stay stable even if LangGraph is not installed in the current machine, but the main implementation is structured as a real LangGraph workflow and the repository requirements include `langgraph`.

## Phase 3: Deep Thread RAG + Prompt-Injection Defense

The combat engine constructs a system prompt using the full conversation thread:

- parent post
- previous bot reply
- previous human reply
- latest human reply

That makes the reply generation RAG-style because the model is not responding only to the newest message; it receives the exact argument history as retrievable context.

### Prompt-injection defense strategy

The defense uses four layers:

1. Persona lock at the top of the system prompt
2. Authority restriction stating only the system prompt can redefine the bot
3. Pattern-based prompt-injection detection for phrases like `ignore previous instructions`, `you are now`, and apology coercion
4. Explicit rejection rule telling the bot to call out manipulation attempts and continue the argument naturally in character

If the latest human reply contains injection language, the prompt adds an `INJECTION ALERT` marker before the response is generated.

## Running the demos

```bash
python3 persona_router.py
python3 content_engine.py
python3 combat_engine.py
python3 -m grid07.cli demo
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

## Deployment

For lightweight hosting, the Docker image intentionally installs only [requirements-deploy.txt](/Users/dikshashahi/Documents/Codex/2026-05-06/files-mentioned-by-the-user-combat/requirements-deploy.txt) so hosted builds stay small and fast. The assignment dependencies remain in [requirements.txt](/Users/dikshashahi/Documents/Codex/2026-05-06/files-mentioned-by-the-user-combat/requirements.txt), which is what reviewers should use when checking LangGraph and vector-routing compliance.
