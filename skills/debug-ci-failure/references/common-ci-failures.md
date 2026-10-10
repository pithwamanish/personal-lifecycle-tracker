# Common CI Failures Reference

### 1. Database Readiness Race Condition
- **Symptom**: `ConnectionRefusedError: [Errno 111]`
- **Root Cause**: Web application container starts before PostgreSQL is ready to accept connections.
- **Fix**: Use Docker Compose `condition: service_healthy` or an explicit wait loop (`pg_isready`).

### 2. Missing Environment Variables
- **Symptom**: `KeyError: 'DATABASE_URL'`
- **Root Cause**: Environment variable specified in `.env` is omitted in CI workflow file (`.github/workflows/ci.yml`).
- **Fix**: Declare default fallback in configuration or pass test env vars in CI step.

### 3. Unapplied Database Migrations
- **Symptom**: `UndefinedTable: relation "users" does not exist`
- **Root Cause**: CI runner did not execute migration command prior to test execution.
- **Fix**: Add migration target (`docker compose run --rm backend alembic upgrade head`) to CI pipeline.
