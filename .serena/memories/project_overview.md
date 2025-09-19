# AgenticOS Project Overview

## Project Purpose
AgenticOS is a **Multi-Modal Retrieval-Augmented Generation (RAG) Agent system** for Intelligent Knowledge Querying Across Heterogeneous Data Sources. It serves as an operating system for agentic applications.

### Core Components
1. **Root Project** (`agenticos` v0.1.3): Main package that depends on Agno framework
2. **Agent Infrastructure** (`agent-infra-docker`): Production-ready Docker-based API service for serving agentic applications

## Key Features
- **AgentOS API**: FastAPI-based web service for agent orchestration
- **PostgreSQL Integration**: Uses pgvector for vector storage and embeddings
- **Pre-built Agents**: Web Search Agent and Agno Assist Agent
- **Knowledge Management**: RAG capabilities with embedding search
- **Session Management**: Persistent conversation history and memory
- **Docker Infrastructure**: Complete containerized deployment

## Architecture
```
AgenticOS/
├── agenticos (main package)           # Root Python package
├── agent-infra-docker/               # Docker infrastructure
│   ├── app/                         # FastAPI application
│   │   ├── main.py                  # Application entry point
│   │   ├── agents/                  # Pre-built agents
│   │   └── db/                      # Database configuration
│   ├── scripts/                     # Development & deployment scripts
│   └── tests/                       # Integration tests
└── configuration files              # MCP, env, project configs
```

## Technology Stack
- **Python 3.12+** (specified in .python-version)
- **Agno Framework** (v2.0.4) - Core AI agent framework
- **FastAPI** - Web API framework
- **PostgreSQL + pgvector** - Vector database for embeddings
- **Docker & Docker Compose** - Containerization
- **OpenAI/Google Gemini** - Language model providers
- **DuckDuckGo** - Web search capabilities