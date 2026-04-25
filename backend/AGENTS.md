# LangChain Backend AI Agent Instructions

This project uses Claude Code with specialized agents and skills for Python/LangChain backend development.

**Version:** 1.0.0  
**Project Stack:** Python 3.11+, LangChain, FastAPI/Flask, PostgreSQL, SQLAlchemy, Alembic  
**Focus Areas:** API development, document processing, LLM integration, vector embeddings, database migrations

## Core Project Principles

1. **LLM-First Design** — Leverage Claude API for intelligent processing
2. **Cost-Aware** — Monitor and optimize LLM token usage
3. **Test-Driven** — Minimum 80% coverage with pytest
4. **Security-First** — Validate all inputs, sanitize outputs, protect API keys
5. **Async-Ready** — Use async/await for I/O operations
6. **Database First** — Use Alembic for all schema changes

## Available Agents (ECC)

| Agent                    | Skill Set                                  | Use Case                                         |
| ------------------------ | ------------------------------------------ | ------------------------------------------------ |
| **planner**              | Break down features, identify dependencies | Complex API features, migration strategies       |
| **python-reviewer**      | PEP 8, type hints, security                | Code review after implementation                 |
| **tdd-guide**            | pytest patterns, fixtures, mocking         | Writing tests first for new features             |
| **security-reviewer**    | SQL injection, API auth, secrets           | Before commits, especially auth code             |
| **code-reviewer**        | General code quality, maintainability      | Post-implementation review                       |
| **architect**            | System design, scalability                 | High-level decisions (monolith vs microservices) |
| **docs-lookup**          | API reference research                     | How to use a library or framework                |
| **build-error-resolver** | Type errors, import issues                 | When Python build/type checking fails            |
| **loop-operator**        | Run autonomous workflows safely            | Monitor long-running migrations, batch jobs      |

## Available Skills (Located in `.claude/skills/`)

### Core Backend Skills

- **`backend-patterns`** — API design, database transactions, caching strategies
- **`api-design`** — REST endpoints, pagination, error responses, versioning
- **`database-migrations`** — Alembic workflows, migration safety, data integrity
- **`verification-loop`** — Test → lint → typecheck → security verify

### Python Development

- **`python-patterns`** — Pythonic idioms, decorators, generators, context managers
- **`python-testing`** — pytest, fixtures, parametrization, coverage tracking
- **`tdd-workflow`** — Test-first methodology, RED-GREEN-REFACTOR cycle

### LangChain & LLM-Specific

- **`claude-api`** — Anthropic Claude API integration patterns (Python)
- **`cost-aware-llm-pipeline`** — Token budgeting, model routing, cost tracking
- **`search-first`** — Research-before-coding workflow (for complex features)

### Security & Quality

- **`security-review`** — OWASP Top 10, input validation, auth patterns
- **`verification-loop`** — Build, test, lint, type-check, security scans

## Project-Specific Conventions

### Architecture

```
app/
├── main.py                 # Entry point (FastAPI/Flask app)
├── api/                    # API routes (by domain: auth, chat, documents)
├── services/               # Business logic (document_service.py, chat_service.py)
├── database/               # SQLAlchemy models & transactions
├── LLM/                    # LangChain operations & prompts
├── processors/             # Document format handlers (PDF, CSV, etc.)
├── schemas/                # Pydantic models for request/response
└── model/                  # SQLAlchemy models (users, documents, chats)

alembic/                    # Database migrations (use for all schema changes!)
tests/                      # pytest tests (mirror app structure)
```

### API Response Format

```python
{
    "success": true,
    "data": {... payload ...},
    "message": "Human-readable message",
    "pagination": {"page": 1, "limit": 10, "total": 100}  # if applicable
}
```

### Testing Requirements

- **Unit tests**: Individual functions, services (in `tests/unit/`)
- **Integration tests**: API endpoints with test DB (in `tests/integration/`)
- **Fixture-based**: Use `conftest.py` for shared fixtures
- **Minimum coverage**: 80% of app logic

### Database Migrations

1. **Always use Alembic** — Never alter `app/model/*.py` then run alembic, use this workflow:
   ```bash
   alembic revision --autogenerate -m "description"
   # Review alembic/versions/HASH_description.py
   # Make manual fixes if needed
   alembic upgrade head
   ```
2. **Test migrations** — Include data migration tests in test suite
3. **Backward compatibility** — Plan for zero-downtime deployments

### LLM Integration

- **Use Claude API directly** when possible (via `claude-api` skill)
- **Monitor token usage** — Track costs per API call (use `cost-aware-llm-pipeline`)
- **Async processing** — Offload heavy LLM calls to jobs/workers
- **Prompt versioning** — Save prompts in version control, not hardcoded
- **Context management** — Summarize conversation history to stay under token limits

### Security Checklist (Before Every Commit)

- [ ] No hardcoded API keys, passwords, or tokens
- [ ] SQL queries use parameterized queries (SQLAlchemy ORM)
- [ ] User inputs validated with Pydantic schemas
- [ ] JWT/auth tokens properly signed and validated
- [ ] Rate limiting on all public endpoints
- [ ] CORS configured correctly (restrictive by default)
- [ ] Secrets rotated if accidentally exposed
- [ ] Error messages don't leak implementation details

## Workflow: Adding a New Feature

### 1. Plan (with `planner` agent)

```
😊: I need to add a document summarization API endpoint
→ planner will:
  - Break down into API route, service, database schema, tests
  - Identify LLM integration points
  - Flag database migration needs
```

### 2. Database Schema (if needed)

```bash
alembic revision --autogenerate -m "add_summary_column_to_documents"
# Review and test migration
alembic upgrade head
```

### 3. Write Tests First (with `tdd-guide`)

```python
# tests/integration/test_summarize_api.py
async def test_summarize_document_success():
    # Arrange: Create test document
    # Act: Call /api/documents/{id}/summarize
    # Assert: Verify response format and summary content
```

### 4. Implement (with `python-patterns` & `claude-api`)

```python
# app/services/document_service.py
async def summarize_document(doc_id: str) -> str:
    doc = await db.get_document(doc_id)
    summary = await claude_client.messages.create(
        model="claude-3-5-sonnet",
        messages=[...doc.content...],
        max_tokens=500
    )
    return summary.content[0].text
```

### 5. API Route

```python
# app/api/documents.py
@router.post("/documents/{doc_id}/summarize")
async def summarize_document(doc_id: str):
    summary = await document_service.summarize_document(doc_id)
    return {"success": True, "data": {"summary": summary}}
```

### 6. Code Review (with `python-reviewer`)

```
😊: Review this implementation for Python best practices
→ python-reviewer checks for type hints, error handling, docstrings
```

### 7. Security Review (for sensitive code)

```
😊: Check this auth logic for vulnerabilities
→ security-reviewer checks OWASP Top 10, crypto usage
```

### 8. Verification Loop (before commit)

Use the `verification-loop` skill:

```bash
pytest tests/ --cov=app --cov-report=term-missing   # 80%+ coverage
pylint app/                                          # Code quality
mypy app/                                            # Type checking
```

### 9. Commit

```bash
git add .
git commit -m "feat: add document summarization API endpoint

- New POST /api/documents/{id}/summarize endpoint
- Integrates Claude API for intelligent summaries
- Added database migration for summary storage
- 92% test coverage with integration tests"
```

## Available Commands (ECC Legacy)

Common slash commands still work while transitioning to skills-first:

- `/plan "description"` — Plan a feature
- `/tdd` — TDD workflow
- `/code-review` — Review code
- `/security-scan` — Security audit
- `/build-fix` — Fix build errors
- `/python-review` — Python-specific review

## Token Optimization Tips

1. **Use Sonnet for most tasks** (60% cheaper than Opus)
2. **Switch to Opus for**: Architecture decisions, debugging complex issues
3. **Compact context** after major milestones (use `/compact` command)
4. **Monitor cost** with `/cost` command

## Project-Specific Agents (Custom)

Coming soon:

- **langchain-specialist** — LangChain patterns, RAG pipelines, vector DB optimization
- **postgres-tuning** — Query optimization, indexing strategy
- **document-processor-expert** — PDF, CSV, DOCX extraction and cleaning

## Getting Help

1. **API questions** → Use `docs-lookup` skill
2. **Python syntax** → Use `python-patterns` skill
3. **Test structure** → Use `tdd-workflow` skill
4. **LLM integration** → Use `claude-api` skill
5. **Cost concerns** → Use `cost-aware-llm-pipeline` skill
6. **General backend** → Use `backend-patterns` skill

## References

- [ECC Documentation](https://github.com/affaan-m/everything-claude-code)
- [Claude API Docs](https://docs.anthropic.com)
- [LangChain Docs](https://python.langchain.com)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org)
- [Alembic Docs](https://alembic.sqlalchemy.org)

---

**Last Updated**: April 22, 2026  
**Maintainer**: Your Team
