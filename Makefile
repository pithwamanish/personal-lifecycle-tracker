.PHONY: dev build test test-backend test-frontend lint down clean logs ps

dev:
	docker compose up --build

up:
	docker compose up -d --build

build:
	docker compose build

test: test-backend test-frontend

test-backend:
	docker compose run --rm backend pytest

test-frontend:
	docker compose run --rm frontend npm test

lint:
	docker compose run --rm frontend npm run lint

ps:
	docker compose ps

db-shell:
	docker compose exec db psql -U postgres -d lifecycle

test-postgres:
	docker compose run --rm -e DATABASE_URL=postgresql://postgres:postgres@db:5432/lifecycle backend pytest

logs:
	docker compose logs -f

down:
	docker compose down -v

clean:
	docker compose down -v --rmi local --remove-orphans
