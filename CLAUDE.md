# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

### Directory Structure
- **Root (`/home/user/AgenticOS`)**: Meta-package with project configuration
- **`agent-infra-docker/`**: Complete FastAPI application with Docker infrastructure
  - **`app/`**: Core application code
    - **`agents/`**: 6 specialized agent implementations
    - **`teams/`**: Multi-agent team coordination systems
    - **`workflows/`**: Automated workflow orchestration
    - **`models/`**: Model provider implementations and factory
    - **`db/`**: Database configuration
    - **`main.py`**: FastAPI application entry point
  - **`scripts/`**: Development automation scripts
  - **`tests/`**: Comprehensive test suite

### Essential Commands

```bash
# Environment Setup
cd agent-infra-docker
./scripts/dev_setup.sh
source .venv/bin/activate

# Code Quality (REQUIRED before commits)
./scripts/format.sh              # Format code and fix imports
mypy .                           # Type checking

# Testing
./scripts/run_tests.sh           # Full test suite with Docker
./scripts/run_tests.sh health    # Health checks only
./scripts/run_tests.sh agents    # Agent tests only
./scripts/run_tests.sh fast      # Fast tests without Docker

# Infrastructure
docker compose up -d --build     # Start all services
docker compose down              # Stop all services
uvicorn app.main:app --reload    # Dev server (alternative)

# Package Management (use uv, not pip)
uv pip install <package-name>
./scripts/generate_requirements.sh    # Update requirements.txt
```

## Architecture Overview

### Core Framework: Agno 2.0.4

This is an **AgenticOS** - a multi-agent orchestration system built on the Agno framework that provides:

1. **Multiple Specialized Agents**: 6 production-ready agents with professional prompts
2. **Team Coordination**: Multi-agent collaboration with parallel processing
3. **Automated Workflows**: End-to-end pipelines for complex tasks
4. **Cost Optimization**: Intelligent model selection across 4 providers
5. **Database Integration**: PostgreSQL with pgvector for memory and RAG

### Project Organization

**Two-Project Structure**:
1. **Root project** (`pyproject.toml`): Meta-package depending on Agno
2. **Agent infrastructure** (`agent-infra-docker/pyproject.toml`): Complete application

**When working on agents, teams, workflows, or the API, focus on the `agent-infra-docker/` directory.**

### Main Application Flow

**File**: `agent-infra-docker/app/main.py`

```python
# Creates AgentOS instance with all systems
agent_os = AgentOS(
    os_id="agenticos-enhanced",
    agents=[...],      # 6 specialized agents
    teams=[...],       # Research team
    workflows=[...],   # Blog writing workflows
    config=os_config_path
)
app = agent_os.get_app()  # Returns FastAPI application
```

## Specialized Agents

### Available Agents (in `app/agents/`)

| Agent | File | Purpose | Default Model | Cost/1K |
|-------|------|---------|---------------|---------|
| **Advanced Web Research** | `web_agent.py` | Multi-source research with verification | deepseek-chat | $0.00014 |
| **Agno Documentation Expert** | `agno_assist.py` | Agno framework expertise & code generation | gpt-4o-mini | $0.00015 |
| **Research Analyst** | `research_analyst.py` | Academic-quality analysis with statistical rigor | deepseek-chat | $0.00014 |
| **Content Writer** | `content_writer.py` | Professional blog/article creation | gpt-4o-mini | $0.00015 |
| **Fact Checker** | `fact_checker.py` | Rigorous verification and accuracy validation | gpt-4o-mini | $0.00015 |
| **SEO Optimizer** | `seo_optimizer.py` | Search engine optimization specialist | gpt-4o-mini | $0.00015 |

### Agent Pattern

All agents follow this standardized pattern:

```python
def get_agent_name(model_id: str, debug_mode: bool = False) -> Agent:
    """
    Create an agent instance with specified model

    Args:
        model_id: Model identifier (e.g., "gpt-4o-mini", "deepseek-chat")
        debug_mode: Enable detailed logging

    Returns:
        Configured Agent instance
    """
    # Get optimal model using factory
    model = ModelFactory.get_optimal_model(
        task_type=TaskType.RESEARCH,  # Or CREATIVE, ANALYSIS, CODING
        priority="balanced"  # Or "budget", "premium"
    )
    model_instance = ModelFactory.create_model(model)

    return Agent(
        id="agent-id",
        name="Agent Name",
        model=model_instance,
        tools=[DuckDuckGoTools()],
        description=dedent("Detailed persona description"),
        instructions=dedent("Comprehensive methodology and guidelines"),
        db=PostgresDb(url=db_url),  # Optional: For conversation history
        markdown=True,
        show_tool_calls=debug_mode,
        debug_mode=debug_mode,
    )
```

### Key Agent Features

- **Professional Prompts**: Detailed, publication-quality instructions
- **Multi-Model Support**: Works with OpenAI, DeepSeek, GLM, Gemini
- **Persistent Memory**: PostgreSQL storage for conversation history
- **Tool Integration**: DuckDuckGo web search, knowledge bases (RAG)
- **Debug Mode**: Detailed logging for development

## Team Systems

### Research Team (`app/teams/research_team.py`)

**Purpose**: Coordinated multi-agent research with parallel processing

**Members** (4 agents):
1. **Advanced Web Research Agent** (deepseek-chat) - Primary research
2. **Research Analyst Agent** (deepseek-chat) - Analysis & synthesis
3. **Fact Checker Agent** (gpt-4o-mini) - Verification
4. **Secondary Web Agent** (glm-4.5-air) - Additional research

**Capabilities**:
- Parallel research execution across multiple agents
- Cross-verification protocols for accuracy
- Academic methodology standards
- Source credibility assessment
- Publication-quality output

**Usage**:
```python
research_team = get_research_team(debug_mode=False)
result = research_team.run("Analyze the impact of AI on healthcare")
```

## Workflow Systems

### Blog Writing Workflows (`app/workflows/blog_workflow.py`)

**Two Workflow Options**:

#### 1. Comprehensive Blog Workflow
**Steps**:
1. **Topic Analysis** - Strategic planning and research strategy
2. **Parallel Research** - Multi-source investigation + competitive analysis
3. **Content Planning** - SEO-optimized outline and structure
4. **Blog Writing** - Professional content creation
5. **Parallel Enhancement** - SEO optimization + Fact-checking
6. **Final Review** - Quality assurance and polish

**Features**:
- Multi-agent collaboration
- Parallel execution for efficiency
- Quality gates and conditional processing
- SEO integration throughout
- Citation and sourcing standards

#### 2. Simple Blog Workflow
**Steps**:
1. **Research** - Team-based investigation
2. **Writing** - Professional content creation
3. **SEO Optimization** - Search engine optimization

**Usage**:
```python
# Comprehensive workflow
workflow = get_blog_writing_workflow(debug_mode=False)
result = workflow.run(
    message="Write about sustainable technology trends",
    additional_data={
        "target_audience": "business professionals",
        "seo_priority": "high",
        "content_type": "blog"
    }
)

# Simple workflow
simple_workflow = get_simple_blog_workflow(debug_mode=False)
result = simple_workflow.run("Write about AI in education")
```

### Workflow Step Functions (`app/workflows/steps/`)

**Research Steps** (`research_steps.py`):
- `topic_analyzer_function`: Topic decomposition and research strategy

**Writing Steps** (`writing_steps.py`):
- `content_planner_function`: Detailed content structure and SEO outline

**Optimization Steps** (`optimization_steps.py`):
- `seo_analyzer_function`: Comprehensive SEO analysis
- `fact_verifier_function`: Accuracy verification

## Model Factory & Cost Optimization

### Model Factory (`app/models/factory.py`)

**Purpose**: Intelligent, cost-aware model selection

**Task-Specific Recommendations**:

| Task Type | Budget | Balanced | Premium |
|-----------|--------|----------|---------|
| **RESEARCH** | deepseek-chat | gpt-4o-mini | gemini-2.0-flash |
| **CREATIVE** | glm-4.5-air | gpt-4o-mini | gpt-4o |
| **ANALYSIS** | deepseek-chat | glm-4.5-air | gpt-4o |
| **CODING** | deepseek-coder | gpt-4o-mini | gpt-4o |

**Cost Per 1K Tokens**:

| Model | Input/Output Cost | Provider | Best For |
|-------|-------------------|----------|----------|
| deepseek-chat | $0.00014 | DeepSeek | Budget research/analysis |
| gpt-4o-mini | $0.00015 | OpenAI | Balanced performance |
| glm-4.5-air | $0.00015 | Zhipu GLM | Multilingual, fast |
| glm-4.5 | $0.00020 | Zhipu GLM | Enhanced reasoning |
| gemini-2.0-flash | $0.00030 | Google | Fast premium |
| gpt-3.5-turbo | $0.00050 | OpenAI | Legacy support |
| gpt-4o | $0.00300 | OpenAI | Premium quality |
| gemini-1.5-pro | $0.00350 | Google | Advanced reasoning |

**Usage Examples**:

```python
from models.factory import ModelFactory, TaskType

# Get optimal model for task type
model = ModelFactory.get_optimal_model(
    task_type=TaskType.RESEARCH,
    priority="budget",  # or "balanced", "premium"
    max_cost_per_1k=0.0002  # Optional cost constraint
)

# Create model instance
model_instance = ModelFactory.create_model(model)

# Compare models
comparison = ModelFactory.compare_models([
    "gpt-4o-mini", "deepseek-chat", "glm-4.5-air"
])

# Get cheapest available
cheapest = ModelFactory.get_cheapest_model()  # Returns "deepseek-chat"

# Get recommendation based on requirements
recommendation = ModelFactory.get_model_recommendation(
    task_complexity="medium",
    budget_sensitivity="high",
    quality_requirement="publication"
)
```

### Model Providers (`app/models/`)

**OpenAI Provider** (`openai_models.py`):
- Standard OpenAI API integration
- Models: gpt-4o, gpt-4o-mini, gpt-3.5-turbo

**DeepSeek Provider** (`deepseek_models.py`):
- OpenAI-compatible API with custom base URL
- Models: deepseek-chat, deepseek-coder
- Most cost-effective option ($0.00014/1K tokens)

**GLM Provider** (`glm_models.py` + `glm45_provider.py`):
- Zhipu GLM models with enhanced features
- Models: glm-4.5, glm-4.5-air
- Features:
  - Thinking mode with adjustable budget
  - Arabic language optimization
  - Query complexity analysis
  - Reflection and reasoning support

**Google Provider**:
- Gemini models via standard API
- Models: gemini-2.0-flash, gemini-1.5-pro

## Database Configuration

### Database Setup (`app/db/`)

**Connection** (`url.py`):
```python
# Format: postgresql+psycopg://{user}:{password}@{host}:{port}/{database}
db_url = f"postgresql+psycopg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
```

**Session Management** (`session.py`):
- SQLAlchemy Engine with connection pooling
- `SessionLocal` for database sessions
- `get_db()` dependency for FastAPI

**Environment Variables** (from `compose.yaml`):
```bash
DB_HOST=pgvector          # Docker service name (or localhost)
DB_PORT=5432              # PostgreSQL port
DB_USER=ai                # Database user
DB_PASS=ai                # Database password
DB_DATABASE=ai            # Database name
OPENAI_API_KEY=...        # Required for OpenAI models
DEEPSEEK_API_KEY=...      # Optional for DeepSeek
GLM_API_KEY=...           # Optional for GLM
GOOGLE_API_KEY=...        # Optional for Gemini
```

### Database Features

- **Session Storage**: Agent conversation history with pgvector
- **Knowledge Base**: RAG with vector embeddings (128K context)
- **User Memory**: Persistent user context across sessions
- **Embeddings**: Semantic search for knowledge retrieval

## Development Workflows

### Code Quality Standards

**Configuration** (`pyproject.toml`):
- **Line length**: 120 characters (ruff)
- **Type hints**: Required for all public functions (mypy)
- **Import organization**: Automatic via ruff
- **Multi-line strings**: Use `textwrap.dedent()` for agent descriptions

**Pre-Commit Requirements**:
```bash
# ALWAYS run before committing
./scripts/format.sh      # Formats code and fixes imports
mypy .                   # Type checking (must pass)
```

### Testing Strategy

**Test Files** (`tests/`):
- `test_health.py`: Service health and database connectivity
- `test_agents.py`: Individual agent functionality
- `test_enhanced_agents.py`: Enhanced agent capabilities
- `test_teams_and_workflows.py`: Team coordination and workflows
- `test_model_factory.py`: Model factory and cost optimization
- `test_performance_integration.py`: Performance and integration tests

**Test Configuration** (`pytest.ini`):
- Coverage reporting: HTML, XML, term-missing
- Markers: slow, integration, docker, database
- Verbose output with short tracebacks

**Running Tests**:
```bash
# Full test suite (starts/stops Docker automatically)
./scripts/run_tests.sh

# Specific test categories
./scripts/run_tests.sh health     # Health checks only
./scripts/run_tests.sh agents     # Agent tests only
./scripts/run_tests.sh fast       # Fast tests (no Docker)

# Manual testing (requires running services)
docker compose up -d
pytest tests/ -v
docker compose down
```

### Development Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `dev_setup.sh` | Create venv and install dependencies |
| `format.sh` | Code formatting and import organization |
| `run_tests.sh` | Execute test suite with Docker orchestration |
| `generate_requirements.sh` | Generate requirements.txt from pyproject.toml |
| `build_image.sh` | Build and push production Docker images |
| `validate.sh` | Code validation and linting |
| `start_db.sh` | Start PostgreSQL database service |
| `entrypoint.sh` | Docker container entry point |
| `_utils.sh` | Shared utility functions |

### Package Management

**IMPORTANT**: Always use `uv` instead of `pip`

```bash
# Add a package
uv pip install <package-name>

# After modifying pyproject.toml
./scripts/generate_requirements.sh

# Upgrade all dependencies
./scripts/generate_requirements.sh upgrade

# Rebuild Docker images with new dependencies
docker compose up -d --build
```

## Docker Infrastructure

### Docker Compose (`compose.yaml`)

**Services**:

1. **pgvector**: PostgreSQL 16 with pgvector extension
   - Port: 5432
   - Database: ai (default)
   - User: ai (default)
   - Volume: pgdata (persistent)

2. **api**: FastAPI application
   - Port: 8000
   - Auto-reload: enabled
   - Depends on: pgvector
   - Mounts: Current directory for live updates

### Dockerfile

**Multi-Stage Build**:
1. **Base**: agnohq/python:3.12 with non-root user
2. **Deps**: Install dependencies via `uv pip sync`
3. **Production**: Final optimized image

**Entry Point**: `/app/scripts/entrypoint.sh`
**Exposed Port**: 8000

## API Endpoints

### Individual Agents
```
POST /agents/advanced-web-research-agent/chat
POST /agents/agno-documentation-expert/chat
POST /agents/research-analyst-agent/chat
POST /agents/content-writer-agent/chat
POST /agents/fact-checker-agent/chat
POST /agents/seo-optimizer-agent/chat
```

### Team Systems
```
POST /teams/comprehensive-research-team/chat
```

### Workflows
```
POST /workflows/comprehensive-blog-workflow/run
POST /workflows/simple-blog-workflow/run
```

### System Information
```
GET /                    # Welcome page
GET /agents              # List all agents
GET /teams               # List all teams
GET /workflows           # List all workflows
GET /health              # Health check
GET /docs                # API documentation (Swagger)
```

## Key Dependencies

### Core Framework
- **Agno 2.0.4**: Multi-agent orchestration framework
- **Agno Infra 1.0.2**: Infrastructure utilities
- **FastAPI 0.116.1**: Web API framework
- **Uvicorn 0.35.0**: ASGI web server

### Database & Vector Storage
- **PostgreSQL 16**: Relational database (via pgvector image)
- **pgvector 0.4.1**: Vector embeddings for RAG
- **SQLAlchemy 2.0.41**: ORM
- **Psycopg 3.2.9**: PostgreSQL driver

### AI/LLM Providers
- **OpenAI 1.97.1**: GPT models
- **Google Genai 1.38.0+**: Gemini models
- **Custom GLM Provider**: GLM 4.5 models
- **DeepSeek Integration**: deepseek-chat, deepseek-coder

### Tools & Utilities
- **DuckDuckGo 9.5.5**: Web search
- **httpx 0.28.1**: HTTP client
- **lxml 6.0.0**: HTML parsing

### Development Tools
- **mypy**: Type checking
- **ruff**: Formatting and linting
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support

## Production Deployment

### Building Production Image

```bash
# 1. Update build script
# Edit scripts/build_image.sh to set IMAGE_NAME and IMAGE_TAG

# 2. Build and push
./scripts/build_image.sh

# 3. Deploy to cloud provider
# Examples: Cloud Run, ECS, GKE, AKS, Railway, Render
```

### Cloud Provider Options

**Serverless Container Platforms**:
- Google Cloud Run
- AWS App Runner
- Azure Container Apps

**Container Orchestration**:
- Amazon ECS (with Fargate or EC2)
- Google Kubernetes Engine (GKE)
- Azure Kubernetes Service (AKS)

**Platform as a Service**:
- Railway.app
- Render
- Heroku (Docker support)

### Production Database

Use managed PostgreSQL services:
- **AWS**: RDS for PostgreSQL (with pgvector extension)
- **Google Cloud**: Cloud SQL for PostgreSQL
- **Azure**: Database for PostgreSQL
- **Managed Options**: Supabase, Neon, Railway

Update database connection via environment variables.

## Common Tasks & Patterns

### Adding a New Agent

1. Create agent file in `app/agents/new_agent.py`:
```python
from textwrap import dedent
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from models.factory import ModelFactory, TaskType

def get_new_agent(model_id: str, debug_mode: bool = False) -> Agent:
    model = ModelFactory.get_optimal_model(
        task_type=TaskType.RESEARCH,
        priority="balanced"
    )
    model_instance = ModelFactory.create_model(model)

    return Agent(
        id="new-agent",
        name="New Agent",
        model=model_instance,
        tools=[DuckDuckGoTools()],
        description=dedent("""
            Detailed persona and capabilities
        """),
        instructions=dedent("""
            Comprehensive methodology and guidelines
        """),
        markdown=True,
        debug_mode=debug_mode,
    )
```

2. Import in `app/main.py` and add to `get_optimized_agents()`

3. Write tests in `tests/test_agents.py`

4. Run formatting and tests:
```bash
./scripts/format.sh
./scripts/run_tests.sh
```

### Creating a New Workflow

1. Create workflow file in `app/workflows/new_workflow.py`:
```python
from agno.workflow import Workflow, RunResponse
from agno.tools.duckduckgo import DuckDuckGoTools

def get_new_workflow(debug_mode: bool = False) -> Workflow:
    return Workflow(
        id="new-workflow",
        name="New Workflow",
        description="Workflow description",
        steps=[
            # Define workflow steps
        ],
        tools=[DuckDuckGoTools()],
        debug_mode=debug_mode,
    )
```

2. Create step functions in `app/workflows/steps/`

3. Import in `app/main.py` and add to `get_workflow_systems()`

4. Test thoroughly

### Adding a Model Provider

1. Create provider file in `app/models/new_provider.py`:
```python
from agno.models.openai import OpenAIChat

def get_new_model(model_id: str):
    return OpenAIChat(
        id=model_id,
        api_key="...",
        base_url="...",  # If custom endpoint
    )
```

2. Update `app/models/factory.py` to include new models

3. Add cost information to factory

4. Test model selection and usage

## Troubleshooting

### Common Issues

**Database Connection Errors**:
```bash
# Check if database is running
docker compose ps

# Restart database
docker compose restart pgvector

# Check logs
docker compose logs pgvector
```

**API Not Starting**:
```bash
# Check environment variables
echo $OPENAI_API_KEY

# Check logs
docker compose logs api

# Rebuild
docker compose up -d --build
```

**Import Errors**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
./scripts/dev_setup.sh
```

**Type Checking Failures**:
```bash
# Run mypy to see errors
mypy .

# Common fixes:
# - Add type hints to function signatures
# - Add # type: ignore comments for unavoidable issues
# - Update mypy configuration in pyproject.toml
```

**Tests Failing**:
```bash
# Ensure services are running
docker compose up -d

# Run specific test
pytest tests/test_agents.py::test_web_agent -v

# Check test logs
pytest tests/ -v --log-cli-level=DEBUG
```

## Best Practices

### When Writing Agents

1. **Use ModelFactory** for cost-optimized model selection
2. **Include detailed prompts** with `textwrap.dedent()`
3. **Add type hints** to all functions
4. **Enable debug mode** during development
5. **Test with multiple queries** before committing
6. **Document capabilities** in agent description

### When Creating Workflows

1. **Break into logical steps** with clear responsibilities
2. **Use parallel execution** where possible for efficiency
3. **Add quality gates** between steps
4. **Include error handling** for robustness
5. **Test end-to-end** with realistic scenarios
6. **Document required additional_data** fields

### When Working with Code

1. **Always run format.sh** before committing
2. **Ensure mypy passes** with no errors
3. **Write tests** for new functionality
4. **Use uv** for package management, not pip
5. **Update requirements.txt** after pyproject.toml changes
6. **Test with Docker** to match production environment
7. **Keep line length** ≤ 120 characters

## Additional Resources

- **Agno Documentation**: https://docs.agno.com
- **Agno GitHub**: https://github.com/agno-agi/agno
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **PostgreSQL + pgvector**: https://github.com/pgvector/pgvector
- **Project README**: `agent-infra-docker/README.md`
- **Enhancement Details**: `agent-infra-docker/ENHANCEMENT_README.md`

---

**Built with Agno Framework 2.0.4** - Production-ready multi-agent AI system with cost optimization, comprehensive testing, and enterprise-grade infrastructure.
