# Contributing Guidelines

## Project
**Autonomous Campus Operating System (ACOS)**

**Version:** 1.0

**Document Type:** Contribution Guide

---

# 1. Introduction

Thank you for your interest in contributing to the Autonomous Campus Operating System (ACOS).

This project is being developed as a research-based Final Year Project (FYP) focused on Agentic AI, Multi-Agent Systems, and Zero-Trust Security for higher education environments.

These guidelines define the development standards, coding practices, documentation requirements, and Git workflow to ensure the project remains organized, maintainable, and consistent.

---

# 2. Contribution Goals

Every contribution should aim to:

- Maintain high code quality.
- Follow project architecture.
- Keep documentation up to date.
- Ensure security best practices.
- Write readable and maintainable code.
- Preserve consistency throughout the project.

---

# 3. Repository Structure

```
frontend/
backend/
ai/
database/
docs/
scripts/
tests/
```

Each directory has a specific responsibility and should only contain files related to its purpose.

---

# 4. Branch Strategy

The project follows a feature-based branching model.

```
main
│
├── develop
│
├── feature/frontend
├── feature/backend
├── feature/database
├── feature/langgraph
├── feature/security
├── feature/documentation
└── feature/testing
```

### Branch Descriptions

| Branch | Purpose |
|---------|---------|
| main | Stable production-ready code |
| develop | Integration branch for ongoing development |
| feature/* | Development of individual features |
| hotfix/* | Critical bug fixes |
| docs/* | Documentation updates |

---

# 5. Git Workflow

Follow the development workflow below.

```
Clone Repository

↓

Create Feature Branch

↓

Develop Feature

↓

Test Changes

↓

Update Documentation

↓

Commit Changes

↓

Push Branch

↓

Create Pull Request

↓

Review

↓

Merge
```

---

# 6. Commit Message Convention

Write clear and meaningful commit messages.

### Examples

```
feat: Add student management API

feat: Implement LangGraph workflow

fix: Resolve authentication issue

docs: Update architecture documentation

refactor: Improve database schema

test: Add unit tests for API

style: Format source code
```

Avoid vague messages such as:

```
update

changes

fixed

work

test
```

---

# 7. Coding Standards

### Python

- Follow PEP 8 style guidelines.
- Use meaningful variable names.
- Keep functions focused on a single responsibility.
- Write descriptive docstrings.
- Use type hints where appropriate.

Example:

```python
def get_student(student_id: int):
    """Retrieve a student record by ID."""
```

---

### HTML

- Use semantic HTML elements.
- Maintain proper indentation.
- Keep components modular.

---

### CSS

- Organize styles logically.
- Use reusable class names.
- Avoid unnecessary duplication.

---

### JavaScript

- Use descriptive function names.
- Prefer modern JavaScript (ES6+).
- Avoid global variables.

---

# 8. Documentation Standards

Every major feature should include documentation updates.

Documentation should include:

- Purpose
- Architecture changes
- API updates
- Database changes
- Screenshots (if applicable)

Markdown formatting should remain consistent throughout the repository.

---

# 9. Testing Requirements

Before submitting changes, verify that:

- The application starts successfully.
- API endpoints work as expected.
- Database operations execute correctly.
- AI agents perform as intended.
- Existing functionality is not affected.

Testing should include:

- Unit Tests
- Integration Tests
- API Tests

---

# 10. Code Review Checklist

Before creating a Pull Request, ensure:

- Code follows project standards.
- No unnecessary files are included.
- Documentation is updated.
- No sensitive information is committed.
- Code has been tested.
- No obvious warnings or errors remain.

---

# 11. Security Guidelines

Contributors must never commit:

- `.env`
- API keys
- Passwords
- Authentication tokens
- Private certificates
- Database files containing sensitive data

Always use `.env.example` for configuration examples.

---

# 12. Dependency Management

When adding a new dependency:

1. Verify it is actively maintained.
2. Ensure it is compatible with the project.
3. Update `requirements.txt`.
4. Document why it was added.

Avoid unnecessary libraries.

---

# 13. Issue Reporting

When reporting an issue, include:

- Description
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment information
- Screenshots (if applicable)

---

# 14. Pull Request Guidelines

Each Pull Request should include:

- Clear title
- Description of changes
- Related issue (if any)
- Testing summary
- Updated documentation

Small, focused Pull Requests are preferred over large changes.

---

# 15. Documentation Update Policy

Whenever a major change is introduced, update the relevant documentation.

Examples include:

- README.md
- ARCHITECTURE.md
- SETUP.md
- API_DESIGN.md
- Database documentation
- Weekly progress reports

Documentation should evolve alongside the codebase.

---

# 16. Development Principles

The project follows these principles:

- Modularity
- Scalability
- Maintainability
- Security by Design
- Separation of Concerns
- Reusability
- Consistent Documentation
- Clean Architecture

---

# 17. Communication

Development discussions should focus on:

- Technical decisions
- Research findings
- Architecture improvements
- Security considerations
- AI workflow enhancements

Major architectural changes should be documented before implementation.

---

# 18. Future Contributors

As the project grows, additional contributors should:

- Read the project documentation.
- Understand the architecture.
- Follow the established coding standards.
- Respect the branching strategy.
- Keep changes focused and well-documented.

---

# 19. Conclusion

Following these contribution guidelines helps maintain a consistent, secure, and well-organized codebase. Adhering to the documented workflow and development standards ensures that the Autonomous Campus Operating System remains scalable, maintainable, and aligned with its research objectives throughout the development lifecycle.