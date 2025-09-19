# Task Completion Checklist for AgenticOS

## Code Quality Checks (REQUIRED)

### 1. Code Formatting
```bash
# Format code using ruff
./agent-infra-docker/scripts/format.sh

# Or manually:
ruff format .
ruff check --select I --fix .
```

### 2. Type Checking
```bash
# Run mypy for type checking
mypy .
```

### 3. Linting
```bash
# Additional linting checks
ruff check .
```

## Testing Requirements

### 1. Run Test Suite
```bash
# Full test suite
./agent-infra-docker/scripts/run_tests.sh

# Quick tests (exclude slow tests)
./agent-infra-docker/scripts/run_tests.sh fast
```

### 2. Test Coverage
- Ensure new features have corresponding tests
- Integration tests for API endpoints
- Agent functionality tests

## Dependency Management

### 1. Update Requirements (if dependencies changed)
```bash
# Regenerate requirements.txt
./agent-infra-docker/scripts/generate_requirements.sh
```

### 2. Virtual Environment
```bash
# Ensure using project virtual environment
source agent-infra-docker/.venv/bin/activate

# Use uv for package installation
uv pip install <package>
```

## Infrastructure Validation

### 1. Docker Build Test
```bash
# Test Docker build process
cd agent-infra-docker
docker compose up -d --build

# Verify services are running
docker compose ps

# Check logs for errors
docker compose logs

# Clean up
docker compose down
```

### 2. API Validation
```bash
# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/agents

# Or visit: http://localhost:8000/docs
```

## Git Workflow

### 1. Pre-commit Checks
```bash
# Check git status
git status

# Stage changes
git add .

# Verify changes
git diff --staged
```

### 2. Commit Guidelines
- Use descriptive commit messages
- Reference issue numbers if applicable
- Commit frequently with logical chunks

## Environment Variables

### 1. Required Variables
```bash
# Ensure these are set (in .env or environment)
OPENAI_API_KEY="your-api-key"
DB_HOST=localhost
DB_PORT=5432
DB_USER=ai
DB_PASS=ai
DB_DATABASE=ai
```

### 2. Environment File
```bash
# Load environment if using .env
source .env
```

## Production Readiness

### 1. Security Check
- No API keys committed to repository
- Sensitive data in environment variables only
- Database credentials properly configured

### 2. Documentation Update
- Update README if adding new features
- Document new environment variables
- Update API documentation if endpoints changed

## Final Validation Checklist

- [ ] Code formatted with ruff
- [ ] Type checking passes (mypy)
- [ ] All tests pass
- [ ] Docker build succeeds
- [ ] API endpoints respond correctly
- [ ] No sensitive data in commits
- [ ] Documentation updated
- [ ] Environment variables properly set
- [ ] Git status clean

## Command Summary for Quick Reference
```bash
# Complete validation workflow
./agent-infra-docker/scripts/format.sh
mypy .
./agent-infra-docker/scripts/run_tests.sh
docker compose up -d --build
curl http://localhost:8000/health
docker compose down
git status
```