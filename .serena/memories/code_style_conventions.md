# Code Style and Conventions for AgenticOS

## Code Formatting & Linting

### Tools Used
- **ruff**: Primary formatter and linter (configured in pyproject.toml)
- **mypy**: Static type checking
- **pytest**: Testing framework

### Ruff Configuration
```toml
[tool.ruff]
line-length = 120
exclude = [".venv*"]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401", "F403"]  # Allow unused imports in __init__.py files
```

### MyPy Configuration
```toml
[tool.mypy]
check_untyped_defs = true
no_implicit_optional = true
warn_unused_configs = true
plugins = ["pydantic.mypy"]
exclude = [".venv*"]
```

## Python Conventions

### Import Organization
- **Ruff manages import sorting** automatically (`--select I --fix`)
- Standard library imports first
- Third-party imports second  
- Local imports last

### Naming Conventions
- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `snake_case.py`
- **Modules**: `snake_case`

### Type Hints
- **Required**: All public functions should have type hints
- **Pydantic models**: Use for data validation (configured in mypy)
- **Optional types**: Use explicit `Optional[T]` (no implicit optional)

### Docstrings
- **Style**: Uses `textwrap.dedent()` for multi-line strings in agent descriptions
- **Agent definitions**: Comprehensive instructions using dedent for readability

Example from codebase:
```python
description=dedent("""\
    You are AgnoAssist, an advanced AI Agent specializing in Agno: 
    a lightweight framework for building multi-modal, reasoning Agents.
    
    Your goal is to help developers understand and use Agno...
"""),
```

## Project Structure Conventions

### Directory Organization
```
agent-infra-docker/
├── app/                    # Main application code
│   ├── agents/            # Agent implementations
│   ├── db/                # Database configuration
│   └── main.py            # Application entry point
├── scripts/               # Development and deployment scripts
├── tests/                 # Test files (pytest)
└── pyproject.toml         # Project configuration
```

### Agent Implementation Pattern
```python
def get_agent_name(
    model_id: str = "default-model",
    debug_mode: bool = False,
) -> Agent:
    return Agent(
        id="agent-id",
        name="Agent Name",
        model=ModelClass(id=model_id),
        tools=[ToolClass()],
        description=dedent("""..."""),
        instructions=dedent("""..."""),
        # Additional configuration...
    )
```

## Configuration Management

### Environment Variables
- Use `.env` files for local development
- Docker environment variables in `compose.yaml`
- Required variables: `OPENAI_API_KEY`, database credentials

### Configuration Files
- **pyproject.toml**: Python project configuration, dependencies, tools
- **config.yaml**: Application-specific configuration (chat prompts, etc.)
- **compose.yaml**: Docker infrastructure definition

## Testing Conventions

### Test Organization
- **Integration tests**: `tests/` directory
- **Test naming**: `test_*.py` files
- **Test functions**: `test_*` function names
- **Fixtures**: Defined in `conftest.py`

### Test Patterns
```python
def test_feature_description(api_client):
    """Test description with clear purpose."""
    # Arrange
    form_data = {"key": "value"}
    
    # Act
    response = api_client.post("/endpoint", data=form_data)
    
    # Assert
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

## Dependency Management

### Package Manager
- **uv**: Primary package manager (not pip)
- **Commands**: `uv pip install <package>`
- **Lock files**: Both `uv.lock` and `requirements.txt` maintained

### Dependency Updates
1. Modify `pyproject.toml`
2. Run `./scripts/generate_requirements.sh`
3. Rebuild Docker images if needed