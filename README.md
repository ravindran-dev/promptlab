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
|  PostgreSQL   |        |  Redis Cache  |        |  OpenAI LLM   |
| (Metric Logs) |        | (Leaderboards)|        | (Judge/Gen)   |
+---------------+        +---------------+        +---------------+
```

### LangGraph Node Workflow
1. **Input Node**: Receives user inputs (`problem`, `solution`, `goals`, `template`, `prompt_version`).
2. **Prompt Loader**: Retrieves active prompt content from Redis Cache, PostgreSQL, or Filesystem fallback.
3. **PRD Generator**: Runs standard generation using ChatOpenAI (or Mock LLM fallback) and logs latency and token usage.
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
- Docker & Docker Compose installed.
- (Optional) OpenAI API Key set in environment.

### 1. Launch with Docker Compose
To build and spin up the complete microservice architecture:

```bash
# Set your API Key (Optional. If not set, system launches in Mock Mode)
export OPENAI_API_KEY="your-actual-api-key-here"

# Spin up containers
docker compose up --build
```

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
