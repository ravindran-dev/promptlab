# ProductOS PromptLab

PromptLab is a production-grade AI platform designed to generate Product Requirement Documents (PRDs) using LLMs and continuously evaluate prompt quality through automated benchmarking, LLM-as-a-Judge scoring, and metrics analytics.

The primary goal is prompt experimentation, evaluation, benchmarking, and continuous improvement, answering the question: **"Is Prompt Version B objectively better than Prompt Version A?"**

---

## High-Level Architecture

```
                       +-------------------+
                       |  React Dashboard  | <----------+
                       +-------------------+            |
                                 |                      |
                            REST | HTTP                 | WebSockets / SSE
                                 v                      | (or Polling)
                       +-------------------+            |
                       |  FastAPI Backend  | -----------+
                       +-------------------+
                                 |
                                 v
                       +-------------------+
                       |    LangGraph      |
                       +-------------------+
                                 |
        +------------------------+------------------------+
        |                        |                        |
        v                        v                        v
+---------------+        +---------------+        +---------------+
|  PostgreSQL   |        |  Redis Cache  |        |  Ollama LLM   |
| (Metric Logs) |        | (Leaderboards)|        | (Judge/Gen)   |
+---------------+        +---------------+        +---------------+
```

### LangGraph Node Workflow
1. **Input Node**: Receives user inputs (`problem`, `solution`, `goals`, `template`, `prompt_version`).
2. **Prompt Loader**: Retrieves active prompt content from Redis Cache, PostgreSQL, or Filesystem fallback.
3. **PRD Generator**: Runs local generation using Ollama and Qwen 3.5 and logs latency and token usage.
4. **Evaluator**: Runs an LLM-as-a-Judge evaluation across 8 core metrics.
5. **Metrics Collector**: Synthesizes and groups the generated text and execution metrics.
6. **Database Writer**: Stores the compiled `MetricRun` in PostgreSQL.
7. **Dashboard API**: Invalidates cached leaderboard statistics in Redis and yields final responses.

---

## Technical Stack

* **Frontend**: React, TypeScript, Tailwind CSS, Recharts
* **Backend**: FastAPI, LangGraph, LangChain, SQLAlchemy (PostgreSQL ORM)
* **Database**: PostgreSQL (metric tracking and case storage)
* **Caching**: Redis (prompt registry caching and leaderboard speedup)
* **Offline Runner**: Node.js package scripts running Python CLI engines
* **Containerization**: Docker & Docker Compose

---

## Getting Started

### Prerequisites
- Docker & Docker Compose for the database, cache, backend, and frontend.
- [Ollama](https://ollama.com/download) running on your computer.

Both PRD generation and judge scoring use the local `qwen3.5` model by default.
[Qwen 3.5](https://ollama.com/library/qwen3.5) is an open-source model family.
No hosted AI API key is required. Ollama must be running and the selected model
must be downloaded; connection errors are reported instead of generating demo content.

### 1. Download the model and configure the project

```bash
ollama pull qwen3.5
cp .env.example .env
```

On PowerShell, use `Copy-Item .env.example .env`. If you already have a `.env`,
keep your database settings and add the Ollama settings from `.env.example`.
If `backend/.env` also exists, its values override the root `.env`; keep the
Ollama settings consistent in both files.

### 2. Launch with Docker Compose

Keep the Ollama desktop app/server running, then:

```bash
docker compose up --build
```

The backend container connects to the host Ollama server at
`http://host.docker.internal:11434`. If the container cannot connect, configure
Ollama to listen on `0.0.0.0:11434` using `OLLAMA_HOST` and restart Ollama.
The Compose file includes a host-gateway mapping for Linux.

### Local development

With PostgreSQL and Redis running at the addresses in `.env`:

```bash
python -m pip install -r backend/requirements.txt
npm --prefix frontend install
npm run backend:start
# In another terminal:
npm run frontend:start
```

Local runs use `OLLAMA_BASE_URL=http://localhost:11434`.
`OLLAMA_MODEL` controls generation and `OLLAMA_JUDGE_MODEL` controls scoring;
pull each selected model before using it. `OLLAMA_MAX_TOKENS`,
`JUDGE_MAX_TOKENS`, and `OLLAMA_TIMEOUT_SECONDS` control generation limits and
timeouts. The API root reports the configured provider and models.

Gemini remains an explicit opt-in for local runs: set `LLM_PROVIDER=gemini`,
`GOOGLE_API_KEY`, `GEMINI_MODEL`, and `JUDGE_MODEL`. Docker Compose uses Ollama.

Access the React dashboard at: **[http://localhost:5173](http://localhost:5173)**
Access the backend API documentation at: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## Running Offline Benchmarks

You can execute prompt benchmarking offline directly in your CLI using:

```bash
npm run benchmark
```

This script:
1. Loads the seeded benchmark cases.
2. Runs the prompt versions (`V1`, `V2`, `V3`) against those test cases.
3. Scores each generated PRD across coverage, factuality, design, engineering, QA, prototype, repetition, and format compliance.
4. Records all evaluations in the database.
5. Prints a clean comparative report comparing averages directly to the terminal.

---

## Score Weights (LLM-as-a-Judge)

The final quality score is computed using the following weights:
- **Requirement Coverage**: 20%
- **Hallucination Resistance**: 20%
- **Design Readiness**: 15%
- **Engineering Readiness**: 15%
- **QA Readiness**: 10%
- **Prototype Readiness**: 10%
- **Non-Repetition**: 5%
- **Format Compliance**: 5%
