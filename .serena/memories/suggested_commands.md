# Suggested Commands for AgenticOS Development

## Environment Setup Commands

### Virtual Environment (uv-based)
```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Development setup (creates .venv and installs dependencies)
./agent-infra-docker/scripts/dev_setup.sh

# Activate virtual environment
source agent-infra-docker/.venv/bin/activate

# Install packages (use uv instead of pip)
uv pip install <package-name>
```

## Development Commands

### Code Quality & Formatting
```bash
# Format code using ruff
./agent-infra-docker/scripts/format.sh

# Or manually:
ruff format .
ruff check --select I --fix .

# Type checking (mypy configured in pyproject.toml)
mypy .
```

### Testing
```bash
# Run all tests
./agent-infra-docker/scripts/run_tests.sh

# Run specific test types
./agent-infra-docker/scripts/run_tests.sh health
./agent-infra-docker/scripts/run_tests.sh agents
./agent-infra-docker/scripts/run_tests.sh fast

# Manual pytest (after containers are running)
pytest tests/ -v
```

## Infrastructure Commands

### Docker Development
```bash
# Start full stack (database + API)
cd agent-infra-docker
docker compose up -d --build

# Stop services
docker compose down

# View logs
docker compose logs -f

# Build custom image
./scripts/build_image.sh
```

### Agno Infrastructure (if available)
```bash
# Start infrastructure
ag infra up

# Stop infrastructure
ag infra down
```

## Application Commands

### Development Server
```bash
# Run with reload (development)
cd agent-infra-docker
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Python direct execution
python app/main.py
```

### Database Management
```bash
# Environment variables for database
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=ai
export DB_PASS=ai
export DB_DATABASE=ai
```

## macOS-Specific Commands (Darwin)
```bash
# Standard Unix commands work on Darwin
ls, cd, grep, find, git

# Package management
brew install <package>

# Environment file loading (if using .env)
source .env
```

## API Testing
```bash
# API documentation
open http://localhost:8000/docs

# Health check
curl http://localhost:8000/health

# Agent list
curl http://localhost:8000/agents
```