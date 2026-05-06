<div align="center">

# AgenticOS

**Production-ready multi-agent AI system built on the [Agno Framework](https://github.com/agno-agi/agno)**

Specialized agents, coordinated research teams, and automated workflows — served through a FastAPI backend with optional local UI proxy.

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MPL 2.0](https://img.shields.io/badge/license-MPL%202.0-green.svg)](LICENSE)
[![Agno 2.6](https://img.shields.io/badge/agno-2.6.4-purple.svg)](https://github.com/agno-agi/agno)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-teal.svg)](https://fastapi.tiangolo.com/)

[Getting Started](#getting-started) · [Agents](#agents) · [Teams & Workflows](#teams--workflows) · [Frontend Proxy](#frontend-proxy) · [Contributing](#contributing)

</div>

---

## What is AgenticOS?

AgenticOS is a self-hosted multi-agent platform that provides:

- **8 specialized AI agents** — web research, content writing, fact-checking, SEO, RAG, knowledge base curation, and more
- **Multi-agent teams** — coordinated research with parallel execution and cross-verification
- **Automated workflows** — multi-step pipelines with branching, parallelism, and quality gates
- **AgentOS Studio** — visual builder UI with drag-and-drop tools, models, and databases
- **Knowledge bases** — RAG with hybrid vector search over uploaded documents and URLs
- **Local or cloud LLMs** — Google Gemini with native chain-of-thought thinking, pluggable model factory

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Python 3.12+ (for local development)
- [uv](https://docs.astral.sh/uv/) package manager
- Google Gemini API key

### Run with Docker

```bash
git clone https://github.com/nexiouscaliver/AgenticOS.git
cd AgenticOS/agent-infra-docker

# Set your API key
export GOOGLE_API_KEY=your-key-here

# Start PostgreSQL + API
docker compose up -d --build
```

The API is now live at `http://localhost:8000`.

### Run Locally

```bash
cd AgenticOS/agent-infra-docker

# Install dependencies
./scripts/dev_setup.sh
source .venv/bin/activate

# Start PostgreSQL
./scripts/start_db.sh

# Start the API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Load a Knowledge Base

```bash
# Load Agno framework docs (default)
python -m app.main --loadkb

# Load a custom URL
python -m app.main --loadkb https://example.com/docs.txt
```

## Agents

Each agent is a self-contained unit with its own model config, tools, memory, and knowledge base. All agents use Google Gemini with native chain-of-thought thinking enabled (`thinking_budget=5000`).

| Agent | ID | Tools | Description |
|-------|----|-------|-------------|
| **Web Research** | `advanced-web-research-agent` | DuckDuckGo | Multi-source investigation with citation tracking and source credibility assessment |
| **Agno Assist** | `agno-assist` | DuckDuckGo + RAG | Documentation assistant powered by a knowledge base of Agno framework docs |
| **Research Analyst** | `research-analyst-agent` | DuckDuckGo | Academic-quality analysis, pattern recognition, and synthesis |
| **Content Writer** | `content-writer-agent` | DuckDuckGo | Professional blog and long-form content creation |
| **Fact Checker** | `fact-checker-agent` | DuckDuckGo | Claim verification with cross-referencing and confidence scoring |
| **SEO Optimizer** | `seo-optimizer-agent` | DuckDuckGo | Search engine optimization and keyword strategy |
| **RAG Agent** | `rag-agent` | RAG + Python + CSV + File | Retrieval-augmented generation over uploaded documents |
| **KB Curator** | `kb-curator-agent` | DuckDuckGo + KB tools | Approval-gated knowledge base management (add/remove documents) |

### Model Factory

The `ModelFactory` in `app/models/factory.py` handles model selection by task type (research, creative, analysis, coding, etc.) and priority (budget, balanced, premium). All models get native Gemini thinking by default.

```python
from models.factory import ModelFactory, TaskType

model = ModelFactory.create_model(
    ModelFactory.get_optimal_model(task_type=TaskType.RESEARCH, priority="balanced")
)
```

## Teams & Workflows

### Research Team

A 4-agent coordinated research team that distributes work in parallel:

```
Team Lead (coordinates)
├── Web Research Agent     → primary multi-source investigation
├── Research Analyst       → academic analysis and synthesis
├── Fact Checker           → verification and accuracy validation
└── Secondary Web Agent    → supplementary research and alternative perspectives
```

Phases: planning → parallel research → analysis → verification → report compilation.

### Blog Writing Workflow (Comprehensive)

7-step automated pipeline:

```
Topic Analysis → Research → Content Planning → Blog Writing
    → [Conditional: Additional Research]
    → [Parallel: SEO + Fact-Check]
    → Final Integration
```

Uses Agno workflow primitives (`Step`, `Parallel`, `Condition`) for branching and concurrent execution.

### Blog Writing Workflow (Simple)

3-step streamlined version: Research → Write → Optimize.

## Project Structure

```
AgenticOS/
├── agent-infra-docker/              # Backend application
│   ├── app/
│   │   ├── main.py                  # AgentOS entrypoint
│   │   ├── registry.py              # Studio component registry
│   │   ├── config.yaml              # Quick-prompts config
│   │   ├── agents/                  # 8 agent definitions
│   │   │   ├── web_agent.py
│   │   │   ├── agno_assist.py
│   │   │   ├── research_analyst.py
│   │   │   ├── content_writer.py
│   │   │   ├── fact_checker.py
│   │   │   ├── seo_optimizer.py
│   │   │   ├── rag_agent.py
│   │   │   └── kb_curator.py
│   │   ├── teams/
│   │   │   └── research_team.py
│   │   ├── workflows/
│   │   │   ├── blog_workflow.py
│   │   │   └── steps/              # Workflow step helpers
│   │   ├── models/
│   │   │   ├── factory.py           # Model factory with cost optimization
│   │   │   └── gemini_thinking.py   # Thinking model variants
│   │   └── db/
│   │       ├── session.py           # SQLAlchemy session
│   │       └── url.py               # DB URL builder
│   ├── tests/                       # Integration tests
│   ├── scripts/                     # Dev automation scripts
│   ├── compose.yaml                 # Docker Compose services
│   ├── Dockerfile                   # Multi-stage production build
│   └── pyproject.toml
│
├── agent-frontend/                  # Nginx reverse proxy (optional)
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── entrypoint.sh
│   ├── docker-compose.yml
│   └── stable/                      # Simplified configs (no local backend)
│
└── pyproject.toml                   # Root meta-package
```

## Frontend Proxy

The `agent-frontend/` directory provides an nginx reverse proxy that serves the Agno OS Studio UI locally. It handles:

- **JS bundle patching** — fetches bundles from `os.agno.com` at startup, rewrites API URLs to point to localhost
- **API proxying** — forwards `/api-proxy/` to `os-api.agno.com` with CORS headers
- **Local backend routing** — forwards `/local-backend/` to `host.docker.internal:7777`
- **WebSocket support** — enabled on all proxy locations for streaming

```bash
cd agent-frontend

# With local backend proxy
docker compose up -d --build

# Studio UI at http://localhost:8080
```

Use the `stable/` configs for a simpler setup without the local backend proxy.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | — | Google Gemini API key (required) |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `DB_USER` | `ai` | PostgreSQL user |
| `DB_PASSWORD` | `ai` | PostgreSQL password |
| `DB_NAME` | `ai` | PostgreSQL database |
| `DEBUG_MODE` | `false` | Enable debug logging |

### Registry

The `app/registry.py` exposes components to AgentOS Studio's visual builder:

- **Tools**: DuckDuckGo, Calculator, File, Python, CSV
- **Models**: Gemini 2.5 Flash Lite / Flash / Pro (standard + thinking variants)
- **Databases**: Shared PostgresDb + PgVector for RAG

Agents and teams are auto-registered from the `agents=` and `teams=` lists in `main.py`.

## Development

### Code Quality

```bash
cd agent-infra-docker

# Format and fix imports (required before commits)
./scripts/format.sh

# Type check
mypy .
```

### Testing

```bash
# Full suite (auto-starts Docker containers)
./scripts/run_tests.sh

# Specific categories
./scripts/run_tests.sh health
./scripts/run_tests.sh agents
./scripts/run_tests.sh fast

# Manual
pytest tests/ -v
```

### Adding Dependencies

```bash
uv pip install <package>
./scripts/generate_requirements.sh
```

### Adding an Agent

1. Create `app/agents/your_agent.py` following the existing pattern (see `web_agent.py`)
2. Import and add to `get_optimized_agents()` in `app/main.py`
3. Add any new tools to `app/registry.py` for Studio visibility

## Tech Stack

| Component | Technology |
|-----------|-----------|
| AI Framework | [Agno](https://github.com/agno-agi/agno) 2.6.4 |
| API | [FastAPI](https://fastapi.tiangolo.com/) 0.116 |
| ASGI Server | Uvicorn 0.35 |
| Database | PostgreSQL 16 + [pgvector](https://github.com/pgvector/pgvector) |
| LLM | Google Gemini 2.5 (with native thinking) |
| Embeddings | Gemini Embedding 2 |
| Search | DuckDuckGo |
| Observability | OpenTelemetry |
| Containers | Docker + Docker Compose |
| Package Manager | [uv](https://docs.astral.sh/uv/) |

## License

This project is licensed under the [Mozilla Public License 2.0](https://mozilla.org/MPL/2.0/).

## Acknowledgments

- [Agno Framework](https://github.com/agno-agi/agno) — the agent framework this project is built on
- [pgvector](https://github.com/pgvector/pgvector) — PostgreSQL vector similarity search
