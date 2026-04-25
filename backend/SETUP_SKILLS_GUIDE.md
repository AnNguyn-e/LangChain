# LangChain Backend: AI Skills & Agents Setup Guide

**Completion Date**: April 22, 2026  
**Setup Status**: ✅ Complete

This guide walks you through the Everything Claude Code (ECC) integration for your LangChain backend project.

## What Has Been Installed

### 📁 Directory Structure Created

```
.claude/
├── skills/                           # 10 specialized skills for your project
│   ├── api-design/
│   ├── backend-patterns/
│   ├── claude-api/
│   ├── cost-aware-llm-pipeline/
│   ├── database-migrations/
│   ├── python-patterns/
│   ├── python-testing/
│   ├── search-first/
│   ├── security-review/
│   ├── tdd-workflow/
│   └── verification-loop/

.github/
├── copilot-instructions.md           # Workspace-level instructions
└── agents/                           # Coming: custom agents

AGENTS.md                              # Project-specific agent configuration
.claude-config.md                      # Model and tool configuration
```

### 🎯 Skills Installed (10 Total)

| Skill                       | Purpose                                             | When to Use                     |
| --------------------------- | --------------------------------------------------- | ------------------------------- |
| **api-design**              | REST endpoint patterns, pagination, error responses | Designing new endpoints         |
| **backend-patterns**        | DB transactions, caching, connection pooling        | Architecture decisions          |
| **claude-api**              | Anthropic Claude API patterns for Python            | Integrating Claude in your code |
| **cost-aware-llm-pipeline** | Token budgeting, model routing, cost tracking       | Optimizing LLM spending         |
| **database-migrations**     | Alembic workflows, data integrity, safety           | Database schema changes         |
| **python-patterns**         | Pythonic idioms, decorators, generators             | Writing better Python code      |
| **python-testing**          | pytest, fixtures, parametrization, mocking          | Writing tests                   |
| **search-first**            | Research-before-coding workflow                     | Complex feature design          |
| **security-review**         | OWASP Top 10, input validation, auth                | Security audits                 |
| **tdd-workflow**            | Test-first methodology, RED-GREEN-REFACTOR          | Feature development             |
| **verification-loop**       | Test → lint → typecheck → security checks           | Pre-commit verification         |

## How to Use These Skills

### In Claude Code Chat

Type `/` in Claude Code and search for any skill:

**Example 1: Adding an API endpoint**

```
😊: Use the api-design and python-testing skills to help me
    design a POST /documents/{id}/process endpoint

→ Skill provides:
  - REST design patterns (request/response format)
  - Error handling structure
  - Status code conventions
  - Test structure for the endpoint
```

**Example 2: Optimizing LLM costs**

```
😊: Review my Claude API calls and optimize for cost

→ Skill suggests:
  - Model selection (Sonnet vs Opus)
  - Token budget tracking
  - Prompt caching
  - Batch processing strategies
```

**Example 3: Database migration**

```
😊: Create migration to add document_hash column

→ Skill guides:
  - Alembic revision workflow
  - Data migration patterns
  - Rollback safety
  - Testing the migration
```

### Available Agents (ECC)

The AGENTS.md file lists these delegated specialists:

- `planner` — Break down complex features
- `python-reviewer` — Review Python code for PEP 8, type hints
- `tdd-guide` — Guide test-first development
- `security-reviewer` — Find vulnerabilities
- `architect` — Design system architecture
- `code-reviewer` — General code quality
- `build-error-resolver` — Fix Python/type errors

Use them like this:

```
😊: Review this code for Python best practices
→ python-reviewer provides detailed feedback on:
  - Type hints coverage
  - PEP 8 compliance
  - Docstring style
  - Error handling
  - Performance issues
```

## Daily Workflow Examples

### Adding a New Feature

#### 1️⃣ Plan the Feature

```
😊: I need to add a document classification endpoint
→ planner agent breaks down into:
  - API route design
  - Service logic
  - Database schema changes
  - LLM integration points
  - Required tests
```

#### 2️⃣ Create Database Migration

```
😊: Use database-migrations skill to create Alembic migration for document classification

→ Guides through Alembic workflow and testing
```

#### 3️⃣ Write Tests First

```
😊: Use tdd-workflow skill. Write tests for the classification endpoint

→ Shows:
  - Test structure
  - Fixtures needed
  - Parametrized test cases
  - Mock setup for Claude API
```

#### 4️⃣ Implement the Feature

```
😊: Use claude-api + python-patterns skills to implement classification

→ Guides:
  - Claude API call patterns
  - Error handling (Python idioms)
  - Async/await usage
  - Token tracking
```

#### 5️⃣ Optimize for Cost

```
😊: Use cost-aware-llm-pipeline skill to review for LLM cost optimization

→ Suggests:
  - Prompt caching
  - Model selection (Sonnet vs Opus)
  - Batch processing
  - Token budgeting
```

#### 6️⃣ Review & Verify

```
😊: Review this implementation for Python best practices

→ python-reviewer checks:
  - Type hints (100% coverage)
  - PEP 8 style
  - Docstrings
  - Error handling

😊: Run security review
→ security-reviewer checks:
  - Input validation
  - JWT/auth tokens
  - SQL injection risk
  - Secret exposure

😊: Verify all checks pass
→ verification-loop runs:
  - pytest (80%+ coverage)
  - mypy type checking
  - pylint linting
  - Security audit
```

#### 7️⃣ Commit

```bash
git commit -m "feat(documents): add classification endpoint

- POST /api/documents/{id}/classify endpoint
- Integrates Claude 3.5 Sonnet for smart classification
- Database migration for classification_label column
- 87% test coverage with mocking
- Cost: ~500 tokens per classification

Estimated cost: $0.0008 per request at 2M/4M tier"
```

### Debugging an Issue

```
😊: This API endpoint is timing out - help me debug

→ planner agent:
  - Is it the Claude API call? (1-2s expected)
  - Is it the database query? (should be <100ms)
  - Is it serialization/parsing? (should be <10ms)

😊: Fix the slow database query
→ backend-patterns suggests:
  - Check if query is indexed
  - Look for N+1 queries
  - Consider caching
  - Use pagination

😊: Optimize the Claude API call
→ cost-aware-llm-pipeline suggests:
  - Cache the prompt if reusable
  - Summarize context to reduce tokens
  - Use a smaller model (Haiku) for routing
  - Batch requests if possible
```

### Security Audit

```
😊: Audit this authentication code
→ security-reviewer checks:
  - JWT signature validation
  - Token expiration
  - Rate limiting
  - Password handling
  - Secrets in environment variables

😊: Audit this database code
→ security-reviewer + backend-patterns check:
  - SQL injection risk (should use ORM)
  - SQL escaping patterns
  - Transaction safety
  - Connection pool security
```

## Model Configuration

The project uses **Claude 3.5 Sonnet by default** for cost efficiency:

```json
{
  "model": "claude-3-5-sonnet",
  "env": {
    "MAX_THINKING_TOKENS": "8000",
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "50"
  }
}
```

### Switch to Opus When:

- Designing complex system architecture
- Debugging subtle concurrency bugs
- Making strategic technology decisions

```
😊: /model opus
```

## Next Steps

### 1. Update Your `.env` File

```bash
ANTHROPIC_API_KEY=sk-your-key-here
DATABASE_URL=postgresql://...
JWT_SECRET=your-secret
ENVIRONMENT=development
```

### 2. Configure Your IDE

- Open the workspace in Claude Code
- AGENTS.md and `.github/copilot-instructions.md` will auto-load
- Skills in `.claude/skills/` are now available

### 3. Read Key Documentation

- **skills/tdd-workflow/SKILL.md** — Learn TDD methodology
- **skills/python-patterns/SKILL.md** — Python best practices
- **skills/claude-api/SKILL.md** — Claude API patterns

### 4. Start Using Skills

```
😊: Help me write tests for the auth service
→ python-testing + tdd-workflow
```

## Token Cost Optimization

Your project now includes cost optimization guidance:

**Typical Costs:**

- API endpoint review: 500-1000 tokens (~$0.0015-$0.003)
- Document summarization: 2000-5000 tokens (~$0.006-$0.015)
- Code generation: 1000-3000 tokens (~$0.003-$0.009)

**Free optimizations:**

- Use Sonnet (default) — 60% cheaper than Opus
- Cache prompts — Save 90%+ on repeated requests
- Summarize context — Reduce tokens by 50%+
- Batch requests — Single API call < multiple calls

**Monitor spending:**

```
😊: /cost
```

## Troubleshooting

### Skills Not Showing Up

- Restart Claude Code
- Check `.claude/skills/` directory exists
- Verify folder structure matches: `.claude/skills/skill-name/SKILL.md`

### AGENTS.md Not Loading

- Placed at workspace root: `d:\CODE_TEST\Python\LangChain\backend\AGENTS.md` ✅
- Verify filename is exactly `AGENTS.md` (case-sensitive on Linux/Mac)

### Instructions Not Applied

- `.github/copilot-instructions.md` loads automatically
- Try `/refresh` in Claude Code to reload config

### Models Slow/Expensive

- Use `/model sonnet` (default)
- Use `/clear` between unrelated tasks
- Use `/compact` at logical breakpoints
- Monitor with `/cost`

## Resources

- **Everything Claude Code**: https://github.com/affaan-m/everything-claude-code
- **Claude API Docs**: https://docs.anthropic.com
- **LangChain Docs**: https://python.langchain.com
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org

## Support

If skills aren't working as expected:

1. Check the skill's SKILL.md in `.claude/skills/skill-name/`
2. Review the examples in this setup guide
3. Read the ECC documentation for detailed patterns
4. Check the project's AGENTS.md for specifics

---

**Setup Complete!** 🎉

You're now ready to develop your LangChain backend with AI-assisted skills and agents. Start with `/tdd` to write your first test, then implement using skill guidance.

**Happy coding!**
