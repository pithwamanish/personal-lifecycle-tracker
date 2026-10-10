.PHONY: dev build test test-backend test-frontend test-integration test-e2e lint down clean logs ps ci-validate promote-validate obs-up obs-down obs-ps obs-logs

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

# Observability Stack (Decoupled Compose Project: OTel Collector, Prometheus, Loki, Tempo, Grafana)
obs-up:
	docker compose -f observability/docker-compose.yaml up -d

obs-down:
	docker compose -f observability/docker-compose.yaml down -v

obs-ps:
	docker compose -f observability/docker-compose.yaml ps

obs-logs:
	docker compose -f observability/docker-compose.yaml logs -f

# Registry (ECR) Image Stages & Pattern Tagging (YYYYMMDD-HHMMSS-shortsha)
IMAGE_TAG ?= $(shell date -u +'%Y%m%d-%H%M%S')-$(shell git rev-parse --short=7 HEAD 2>/dev/null || echo "latest")
ECR_REGISTRY ?= localhost:5000
BACKEND_REPO ?= personal-lifecycle-tracker-backend
FRONTEND_REPO ?= personal-lifecycle-tracker-frontend

ecr-tag:
	@echo $(IMAGE_TAG)

build-images:
	docker build --target base -t $(ECR_REGISTRY)/$(BACKEND_REPO):$(IMAGE_TAG) -t $(ECR_REGISTRY)/$(BACKEND_REPO):latest ./backend
	docker build --target prod -t $(ECR_REGISTRY)/$(FRONTEND_REPO):$(IMAGE_TAG) -t $(ECR_REGISTRY)/$(FRONTEND_REPO):latest ./frontend

push-images:
	docker push $(ECR_REGISTRY)/$(BACKEND_REPO):$(IMAGE_TAG)
	docker push $(ECR_REGISTRY)/$(BACKEND_REPO):latest
	docker push $(ECR_REGISTRY)/$(FRONTEND_REPO):$(IMAGE_TAG)
	docker push $(ECR_REGISTRY)/$(FRONTEND_REPO):latest

pull-images:
	docker pull $(ECR_REGISTRY)/$(BACKEND_REPO):$(IMAGE_TAG)
	docker pull $(ECR_REGISTRY)/$(FRONTEND_REPO):$(IMAGE_TAG)

prod-serve:
	BACKEND_IMAGE=$(ECR_REGISTRY)/$(BACKEND_REPO):$(IMAGE_TAG) FRONTEND_IMAGE=$(ECR_REGISTRY)/$(FRONTEND_REPO):$(IMAGE_TAG) docker compose -f docker-compose.prod.yml up -d --no-build


# Infrastructure as Code (IaC) - Zero Host Dependencies via Docker Containers
TF_IMAGE ?= hashicorp/terraform:1.7.5
AWS_CLI_IMAGE ?= amazon/aws-cli:latest

tf-fmt:
	docker run --rm -v $(CURDIR):/workspace -w /workspace $(TF_IMAGE) fmt -recursive terraform/

# AWS Terraform - Dev Environment
tf-init-aws:
	docker run --rm -v $(CURDIR)/terraform/aws:/workspace -w /workspace $(TF_IMAGE) init

tf-validate-aws:
	docker run --rm -v $(CURDIR)/terraform/aws:/workspace -w /workspace $(TF_IMAGE) validate

tf-plan-aws:
	docker run --rm -v $(CURDIR)/terraform/aws:/workspace -w /workspace -v $$HOME/.aws:/root/.aws:ro -e AWS_PROFILE $(TF_IMAGE) plan -var-file=terraform.tfvars.dev

tf-apply-aws:
	docker run --rm -it -v $(CURDIR)/terraform/aws:/workspace -w /workspace -v $$HOME/.aws:/root/.aws:ro -e AWS_PROFILE $(TF_IMAGE) apply -var-file=terraform.tfvars.dev

# AWS Terraform - Production Environment Copy
tf-init-aws-prod:
	docker run --rm -v $(CURDIR)/terraform/aws-prod:/workspace -w /workspace $(TF_IMAGE) init

tf-validate-aws-prod:
	docker run --rm -v $(CURDIR)/terraform/aws-prod:/workspace -w /workspace $(TF_IMAGE) validate

tf-plan-aws-prod:
	docker run --rm -v $(CURDIR)/terraform/aws-prod:/workspace -w /workspace -v $$HOME/.aws:/root/.aws:ro -e AWS_PROFILE $(TF_IMAGE) plan -var-file=terraform.tfvars.prod

tf-apply-aws-prod:
	docker run --rm -it -v $(CURDIR)/terraform/aws-prod:/workspace -w /workspace -v $$HOME/.aws:/root/.aws:ro -e AWS_PROFILE $(TF_IMAGE) apply -var-file=terraform.tfvars.prod

# Render Terraform - Dev Environment
tf-init-render:
	docker run --rm -v $(CURDIR)/terraform/render:/workspace -w /workspace $(TF_IMAGE) init

tf-validate-render:
	docker run --rm -v $(CURDIR)/terraform/render:/workspace -w /workspace $(TF_IMAGE) validate

tf-plan-render:
	docker run --rm -v $(CURDIR)/terraform/render:/workspace -w /workspace -e RENDER_API_KEY $(TF_IMAGE) plan -var-file=terraform.tfvars.dev

# Render Terraform - Production Environment Copy
tf-init-render-prod:
	docker run --rm -v $(CURDIR)/terraform/render-prod:/workspace -w /workspace $(TF_IMAGE) init

tf-validate-render-prod:
	docker run --rm -v $(CURDIR)/terraform/render-prod:/workspace -w /workspace $(TF_IMAGE) validate

tf-plan-render-prod:
	docker run --rm -v $(CURDIR)/terraform/render-prod:/workspace -w /workspace -e RENDER_API_KEY $(TF_IMAGE) plan -var-file=terraform.tfvars.prod

# Validate All Terraform Environments
tf-validate: tf-validate-aws tf-validate-aws-prod tf-validate-render tf-validate-render-prod

# CloudFormation Validation
cf-validate-dev:
	docker run --rm -v $(CURDIR)/cloudformation:/cf -v $$HOME/.aws:/root/.aws:ro -e AWS_DEFAULT_REGION=us-east-1 $(AWS_CLI_IMAGE) cloudformation validate-template --template-body file:///cf/aws-ec2-compose.yaml

cf-validate-prod:
	docker run --rm -v $(CURDIR)/cloudformation:/cf -v $$HOME/.aws:/root/.aws:ro -e AWS_DEFAULT_REGION=us-east-1 $(AWS_CLI_IMAGE) cloudformation validate-template --template-body file:///cf/aws-ec2-compose-prod.yaml

cf-validate: cf-validate-dev cf-validate-prod

ci-validate:
	act -n -W .github/workflows/ci.yml

promote-validate:
	act -n -W .github/workflows/promote-dev-to-prod.yml

# On-Call Engineer & Autonomous Incident Response
on-call-poll:
	python3 on-call-engineer/poll-alerts.py

on-call-verify:
	bash on-call-engineer/scripts/verify

on-call-simulate-cloud:
	bash on-call-engineer/cloud-simulator/scripts/run-cloud-simulation
