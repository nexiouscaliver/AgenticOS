# AgenticOS Codebase Structure

## Root Directory Structure
```
AgenticOS/
├── .env                           # Environment variables (not committed)
├── .gitignore                     # Git ignore patterns
├── .mcp.json                      # MCP server configuration (Agno)
├── .python-version                # Python version (3.12)
├── README.md                      # Empty/placeholder
├── pyproject.toml                 # Root project configuration
├── uv.lock                        # uv lock file
└── agent-infra-docker/            # Main application directory
```

## Agent Infrastructure Directory (`agent-infra-docker/`)

### Application Code (`app/`)
```
app/
├── __init__.py                    # Package initialization
├── main.py                        # FastAPI application entry point
├── config.yaml                    # Application configuration
├── agents/                        # Agent implementations
│   ├── __init__.py
│   ├── agno_assist.py            # Agno documentation assistant
│   └── web_agent.py              # Web search agent
└── db/                           # Database configuration
    ├── __init__.py
    ├── session.py                # Database session configuration
    └── url.py                    # Database URL utilities
```

### Development Scripts (`scripts/`)
```
scripts/
├── _utils.sh                     # Shared utilities for scripts
├── build_image.sh                # Docker image build script
├── dev_setup.sh                  # Development environment setup
├── entrypoint.sh                 # Docker container entrypoint
├── format.sh                     # Code formatting (ruff)
├── generate_requirements.sh      # Generate requirements.txt from pyproject.toml
├── run_tests.sh                  # Test runner with Docker orchestration
├── start_db.sh                   # Database startup script
└── validate.sh                   # Validation script
```

### Testing (`tests/`)
```
tests/
├── __init__.py                   # Test package initialization
├── conftest.py                   # pytest configuration and fixtures
├── test_agents.py                # Agent functionality tests
└── test_health.py                # Health check tests
```

### Infrastructure Files
```
agent-infra-docker/
├── .dockerignore                 # Docker ignore patterns
├── .gitignore                    # Git ignore patterns
├── compose.yaml                  # Docker Compose configuration
├── Dockerfile                    # Container build definition
├── LICENSE                       # License file
├── pyproject.toml               # Python project configuration
├── pytest.ini                   # pytest configuration
├── README.md                     # Comprehensive documentation
├── requirements.txt              # Generated from pyproject.toml
└── uv.lock                       # uv dependency lock file
```

## Key Components Deep Dive

### 1. Application Entry Point (`app/main.py`)
- Creates AgentOS instance with pre-built agents
- Configures FastAPI application
- Sets up async knowledge loading for Agno Assist
- Serves application with reload capability

### 2. Agent Implementations

#### Agno Assist (`app/agents/agno_assist.py`)
- Specialized agent for Agno framework documentation
- Uses PostgreSQL knowledge base with vector embeddings
- Implements hybrid search with OpenAI embeddings
- Maintains conversation history and agentic memory

#### Web Agent (`app/agents/web_agent.py`)
- General-purpose web search agent
- Uses DuckDuckGo for web searches
- Maintains conversation context
- Provides cited responses from web sources

### 3. Database Configuration (`app/db/`)
- PostgreSQL with pgvector extension for embeddings
- Session management for agent persistence
- URL configuration for different environments

### 4. Configuration Management
- **config.yaml**: Quick prompts for agents
- **pyproject.toml**: Dependencies, tool configuration (ruff, mypy)
- **compose.yaml**: Multi-service Docker setup

### 5. Development Workflow Scripts
- **dev_setup.sh**: Complete development environment setup
- **format.sh**: Code formatting with ruff
- **run_tests.sh**: Comprehensive test runner with Docker orchestration
- **generate_requirements.sh**: Dependency management

## Architecture Patterns

### Agent Pattern
```python
def get_agent_name(model_id: str, debug_mode: bool = False) -> Agent:
    return Agent(
        id="unique-id",
        name="Display Name", 
        model=ModelClass(id=model_id),
        tools=[Tools()],
        description=dedent("..."),
        instructions=dedent("..."),
        # Storage, memory, knowledge configuration
    )
```

### Database Integration
- **PostgresDb**: Chat history and session state
- **PgVector**: Vector embeddings for knowledge search
- **Knowledge**: Content management with embeddings

### Infrastructure Pattern
- **Docker Compose**: Multi-service orchestration
- **Environment Variables**: Configuration management
- **Health Checks**: Service monitoring
- **Volume Persistence**: Data persistence

## File Dependencies

### Root Dependencies
- `pyproject.toml` → Defines project metadata and dependencies
- `.python-version` → Specifies Python 3.12 requirement

### Agent Infrastructure Dependencies
- `app/main.py` → Core application assembly
- `app/agents/*.py` → Individual agent implementations
- `app/db/session.py` → Database configuration for all agents
- `scripts/*.sh` → Development and deployment automation
- `compose.yaml` → Infrastructure orchestration