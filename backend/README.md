# Personal Lifecycle Tracker - FastAPI Backend

FastAPI backend implementing the `openapi.yaml` specification for Personal Lifecycle Tracker.

## Module Structure

The backend code is modularized as follows:
- **`app/models.py`**: Pydantic schemas and models matching `openapi.yaml` definitions (items, groups, auth, users, reminders, and digest).
- **`app/database.py`**: Database connection management, dialect handling, and session factories. Configured via `DATABASE_URL` (with fallback to `DB_URL` or default `sqlite:///./lifecycle.db`).
- **`app/db_models.py`**: Declarative SQLAlchemy ORM models (`UserModel`, `GroupModel`, `GroupMemberModel`, `LifecycleItemModel`, `DailyDigestConfigModel`, `DailyDigestHistoryModel`).
- **`app/auth.py`**: Authentication logic using PBKDF2-HMAC-SHA256 password hashing, JWT bearer token generation/decoding, and FastAPI authentication dependencies (`get_current_user` and `get_current_user_optional`).
- **`app/store.py`**: Database-agnostic persistent store (`DatabaseStore`) powered by SQLAlchemy, supporting SQLite and future relational databases (such as PostgreSQL). Pre-seeds initial users, groups, and 12 sample lifecycle items when empty. Implements cascade deletion rules per MVP specifications.
- **`app/routers/`**:
  - `auth.py`: Signup (`/api/v1/auth/signup`), Login (`/api/v1/auth/login`), Current User (`/api/v1/auth/me`), Logout (`/api/v1/auth/logout`)
  - `users.py`: User list (`/api/v1/users`), Account deletion (`/api/v1/users/{userId}`)
  - `items.py`: Lifecycle items CRUD (`/api/v1/items`), filters, search, and completion toggle (`/api/v1/items/{id}/complete`)
  - `groups.py`: Shared groups CRUD (`/api/v1/groups`), member invitations and removal
  - `reminders.py`: Active alerts summary (`/api/v1/reminders/summary`), daily digest configuration & generation (`/api/v1/reminders/digest/*`)
  - `dev.py`: Dev seed reset (`/api/v1/dev/seed`)
  - `health.py`: Service healthcheck (`/health`)
- **`app/main.py` & `main.py`**: Application factory, CORS middleware, global exception handlers mapping errors to `ErrorResponse`, and router registration.
- **`tests/`**: Comprehensive pytest test suite covering all routers, authentication, permissions, filtering, and edge cases.

## Seed Accounts

The store comes pre-seeded with:
- `alex@example.com` (password: `password123`) - Default user
- `sarah@example.com` (password: `password123`)
- `jordan@example.com` (password: `password123`)

## Running the Backend

### In Docker
```bash
docker build -t lifecycle-backend backend
docker run -p 8000:8000 lifecycle-backend
```

### Running Tests
```bash
docker run --rm -v $(pwd)/backend:/app -w /app lifecycle-backend pytest -v
```
