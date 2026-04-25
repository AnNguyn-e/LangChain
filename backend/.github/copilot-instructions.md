---
description: "LangChain Backend Project Instructions"
---

# LangChain Backend Development Instructions

## Project Overview

**Stack**: Python 3.11+, LangChain, FastAPI, PostgreSQL, SQLAlchemy, Alembic  
**Purpose**: AI-powered document processing and chat system using Claude API  
**Team**: Backend Development

## Quality Standards

### Code Quality
- **PEP 8 compliant** — Use `pylint`, `black`, `isort`
- **Type hints required** — 100% coverage with `mypy`
- **Docstrings** — Google-style for all public functions/classes
- **Line length** — 120 characters (Python convention)
- **Import ordering** — Standard library → third-party → local

### Testing
- **Test-driven development** — Write tests FIRST
- **Test coverage**: Minimum 80% of app logic
- **Test framework**: pytest with fixtures in `conftest.py`
- **Integration tests**: Use TestClient from FastAPI for API endpoints
- **Database tests**: Use in-memory SQLite or test database fixtures

### Performance
- **Database queries** — Always paginate, use indexes
- **LLM calls** — Log token usage, cache when appropriate
- **API responses** — Keep under 200ms for non-LLM endpoints (1-2s for LLM)
- **Background jobs** — Use async tasks for heavy processing

### Security (CRITICAL)
- **Secrets management** — Environment variables only, never in code
- **SQL injection** — Always use parameterized queries (SQLAlchemy ORM)
- **Input validation** — Validate before processing (Pydantic schemas)
- **Authentication** — Verify JWT tokens on every protected endpoint
- **CORS** — Explicitly define allowed origins
- **Rate limiting** — Enable on all public endpoints

## File Organization

```
├── app/
│   ├── main.py                 # FastAPI app initialization
│   ├── api/                    # API routers
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── documents.py        # Document operations
│   │   └── chat.py             # Chat endpoints
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── user_model.py
│   │   ├── document_model.py
│   │   └── chat_model.py
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py
│   │   ├── document_service.py
│   │   └── chat_service.py
│   ├── database/               # Database configuration
│   │   └── database.py
│   ├── schemas/                # Pydantic request/response models
│   │   └── schemas.py
│   ├── processors/             # Format-specific handlers
│   │   ├── pdf_processor.py
│   │   ├── csv_processor.py
│   │   └── ...
│   └── LLM/                    # LangChain integration
│       └── langchain_ops.py
├── alembic/                    # Database migrations
│   └── versions/
├── tests/                      # Pytest test suite
│   ├── conftest.py            # Shared fixtures
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── requirements.txt            # Python dependencies
└── alembic.ini                # Migration config
```

## Common Development Tasks

### Adding a New API Endpoint

1. **Create test first** (`tests/integration/test_api.py`)
   ```python
   @pytest.mark.asyncio
   async def test_new_endpoint():
       response = await client.get("/api/new")
       assert response.status_code == 200
   ```

2. **Create Pydantic schema** (`app/schemas/schemas.py`)
   ```python
   class NewResponse(BaseModel):
       id: str
       data: dict
   ```

3. **Create service method** (`app/services/service.py`)
   ```python
   async def get_new_data(self) -> NewResponse:
       ...
   ```

4. **Create API route** (`app/api/routes.py`)
   ```python
   @router.get("/new")
   async def get_new(service: NewService = Depends()):
       return await service.get_new_data()
   ```

### Database Schema Changes

**ALWAYS use Alembic migrations** — Never directly modify models without migration:

```bash
# Step 1: Modify app/models/user_model.py
# Step 2: Auto-generate migration
alembic revision --autogenerate -m "add_new_column"

# Step 3: Review migration file (alembic/versions/...)
# Step 4: Apply migration
alembic upgrade head

# Step 5: Write tests for migration
# Step 6: Commit both migration + tests
```

### Integrating LLM Calls

Use the Claude API patterns from the `claude-api` skill:

```python
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def process_with_claude(text: str) -> str:
    message = await client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": text
        }]
    )
    return message.content[0].text
```

**Best practices**:
- Always use environment variable for API key
- Cache prompts and system instructions
- Log token usage for cost tracking
- Use streaming for long responses
- Handle rate limits gracefully

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/integration/test_chat.py

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

### Pre-Commit Checks

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/

# Linting
pylint app/

# Tests with coverage
pytest --cov=app
```

## Debugging Tips

### Common Issues

**"sqlalchemy.exc.IntegrityError: duplicate key"**
- Check for unique constraints violations
- Verify data cleanup in test teardown

**"Unauthorized" on protected endpoint**
- Verify JWT token format and signature
- Check token expiration
- Ensure Authorization header is present

**"LLM rate limit exceeded"**
- Implement exponential backoff retry
- Add request throttling
- Cache responses when appropriate

**Test failures with "AssertionError"**
- Use `pytest -vv` for detailed output
- Check test isolation (use fixtures properly)
- Verify mock setup matches actual behavior

## Git Workflow

### Commit Format
```
<type>(<scope>): <description>

<body>

Fixes #<issue>
```

**Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`

**Example**:
```
feat(auth): add OAuth2 integration

- Implements OAuth2 flow with Google provider
- Adds JWT token generation and validation
- Tests: 85% coverage with mocking

Fixes #42
```

### PR Requirements
- [ ] Tests written and passing
- [ ] Coverage at least 80%
- [ ] Code reviewed
- [ ] Security check passed
- [ ] Documentation updated if needed

## Environment Setup

### .env File (Add to .gitignore)
```
ANTHROPIC_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@localhost/dbname
JWT_SECRET=your-secret-key
ENVIRONMENT=development
```

### Initial Setup
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
alembic upgrade head
pytest
```

## Performance Baselines

- **API endpoints** (non-LLM): <200ms
- **LLM processing**: 1-3 seconds (depends on prompt size)
- **Database queries**: <100ms (with proper indexes)
- **Document upload**: <5 seconds for standard files

## References

- [Claude API Documentation](https://docs.anthropic.com/en/api)
- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Guide](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [pytest Documentation](https://docs.pytest.org/)

---

**Last Updated**: April 22, 2026  
**Automated by**: Claude Code with ECC
