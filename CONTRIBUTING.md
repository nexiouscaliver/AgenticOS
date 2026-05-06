# Contributing to AgenticOS

Thanks for your interest in contributing. This document covers the basics.

## Development Setup

```bash
cd agent-infra-docker

# Install dependencies
./scripts/dev_setup.sh
source .venv/bin/activate

# Start PostgreSQL
./scripts/start_db.sh
```

## Making Changes

1. Create a branch from `main`
2. Make your changes
3. Run formatting and type checks before committing:

```bash
./scripts/format.sh
mypy .
```

4. Run the relevant tests:

```bash
./scripts/run_tests.sh
```

5. Open a pull request against `main`

## Code Standards

- **Line length**: 120 characters (enforced by ruff)
- **Type hints**: Required on all public functions
- **Imports**: Auto-organized by ruff (`ruff check --select I --fix .`)
- **Agent pattern**: Follow the factory pattern in `app/agents/` — see `web_agent.py` as a reference
- **Models**: Use `ModelFactory.create_model()` — don't instantiate models directly

## Adding a New Agent

1. Create `app/agents/your_agent.py` with a `get_your_agent(model_id, debug_mode)` function
2. Import and add it to `get_optimized_agents()` in `app/main.py`
3. Add any new tools to `app/registry.py`

## Adding a New Workflow

1. Create `app/workflows/your_workflow.py` with a `get_your_workflow(debug_mode)` function
2. Import and add it to `get_workflow_systems()` in `app/main.py`
3. Use Agno primitives (`Step`, `Parallel`, `Condition`) for pipeline construction

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Include a clear description of what changed and why
- Ensure tests pass before requesting review
- Follow the existing commit message style: `type: description`

## Reporting Issues

Open a [GitHub Issue](https://github.com/nexiouscaliver/AgenticOS/issues) with:

- What you expected to happen
- What actually happened
- Steps to reproduce
- Relevant logs or error messages
