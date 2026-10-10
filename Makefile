.PHONY: dev build test test-backend test-frontend test-integration test-e2e lint down clean logs ps

dev:
	docker compose up --build

up:
	docker compose up -d --build

build:
	docker compose build

test: test-backend test-frontend test-integration test-e2e

test-backend:
	docker compose run --rm backend pytest tests -m "not integration"

test-integration:
	docker compose run --rm backend pytest tests/integration -v

test-frontend:
	docker compose run --rm frontend npm test

test-e2e:
	docker compose run --rm e2e

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

# Production Stack (Local or VM)
prod-up:
	docker compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.prod.yml down -v

prod-ps:
	docker compose -f docker-compose.prod.yml ps

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f

# Infrastructure as Code (IaC) - Zero Host Dependencies via Docker Containers
TF_IMAGE ?= hashicorp/terraform:1.7.5
AWS_CLI_IMAGE ?= amazon/aws-cli:latest

tf-fmt:
	docker run --rm -v $$(PWD):/workspace -w /workspace $(TF_IMAGE) fmt -recursive terraform/

tf-init-aws:
	docker run --rm -v $$(PWD)/terraform/aws:/workspace -w /workspace $(TF_IMAGE) init

tf-validate-aws:
	docker run --rm -v $$(PWD)/terraform/aws:/workspace -w /workspace $(TF_IMAGE) validate

tf-plan-aws:
	docker run --rm -v $$(PWD)/terraform/aws:/workspace -w /workspace -v $$HOME/.aws:/root/.aws:ro -e AWS_PROFILE $(TF_IMAGE) plan

tf-apply-aws:
	docker run --rm -it -v $$(PWD)/terraform/aws:/workspace -w /workspace -v $$HOME/.aws:/root/.aws:ro -e AWS_PROFILE $(TF_IMAGE) apply

tf-init-render:
	docker run --rm -v $$(PWD)/terraform/render:/workspace -w /workspace $(TF_IMAGE) init

tf-validate-render:
	docker run --rm -v $$(PWD)/terraform/render:/workspace -w /workspace $(TF_IMAGE) validate

tf-plan-render:
	docker run --rm -v $$(PWD)/terraform/render:/workspace -w /workspace -e RENDER_API_KEY $(TF_IMAGE) plan

cf-validate:
	docker run --rm -v $$(PWD)/cloudformation:/cf $(AWS_CLI_IMAGE) cloudformation validate-template --template-body file:///cf/aws-ec2-compose.yaml

