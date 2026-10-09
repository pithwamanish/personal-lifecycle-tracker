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

logs:
	docker compose logs -f

down:
	docker compose down -v

clean:
	docker compose down -v --rmi local --remove-orphans
