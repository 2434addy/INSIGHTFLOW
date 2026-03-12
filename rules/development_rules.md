# InsightFlow — Development Rules

## Non-Negotiable Rules

These rules apply to ALL code in the InsightFlow codebase. No exceptions without explicit CTO approval.

### Security Rules

1. **NEVER commit secrets** — No API keys, tokens, passwords, or credentials in source code. Use environment variables + Secrets Manager.

2. **ALWAYS scope database queries to workspace_id** — Every query that touches tenant data MUST include `workspace_id` filtering. No exceptions.

3. **ALWAYS validate user input** — Use Pydantic (backend) and Zod (frontend) for all inputs. Never trust client-sent data.

4. **NEVER use raw SQL with user input** — Always use parameterized queries via SQLAlchemy ORM. No string interpolation in queries.

5. **ALWAYS check permissions** — Every API endpoint must verify the user has the required role/permission for the action.

6. **NEVER log sensitive data** — No passwords, tokens, PII, or full request bodies in logs.

7. **ALWAYS encrypt sensitive fields** — OAuth tokens and API keys stored with application-level encryption (AES-256-GCM).

8. **NEVER disable security headers** — CSP, HSTS, X-Frame-Options must be present on all responses.

### Code Quality Rules

9. **ALWAYS write tests for new endpoints** — Every API endpoint requires at least one happy-path test and one auth/permission test.

10. **NEVER skip tenant isolation tests** — Any PR touching data access must include a test proving cross-tenant access is blocked.

11. **ALWAYS use type hints (Python) / TypeScript (frontend)** — No `Any` types except with explicit justification.

12. **NEVER introduce N+1 queries** — Use `selectinload` or `joinedload` for relationships. CI will flag N+1 patterns.

13. **ALWAYS handle errors explicitly** — No bare `except:` or empty `catch {}` blocks.

14. **NEVER push directly to main** — All changes go through PR with at least 1 approval.

### Architecture Rules

15. **Service layer handles business logic** — Routers parse requests and return responses. Services contain logic. Models define data.

16. **One concern per module** — Don't mix auth logic in the reports module, or DB queries in route handlers.

17. **Async by default** — Use `async/await` for all I/O operations. Sync calls block the event loop.

18. **Celery for long-running tasks** — Any operation > 5 seconds should be a background task (data sync, report generation, PDF export).

### Frontend Rules

19. **Server Components by default** — Only add `"use client"` when you need interactivity, hooks, or browser APIs.

20. **No inline styles** — Use Tailwind CSS utility classes. No `style={{ }}` props.

21. **Accessible by default** — All interactive elements must be keyboard navigable with appropriate ARIA labels.

22. **No `any` types in TypeScript** — Use `unknown` if the type is truly unknown, then narrow it.
