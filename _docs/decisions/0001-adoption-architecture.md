# ADR 0001: Technology Stack and Container Architecture Selection

**Status:** Accepted  
**Date:** 2026-10-10  
**Deciders:** Core Engineering Team & AI Orchestrator

## Context

The Personal Lifecycle Tracker requires high availability, zero host runtime coupling, deterministic API synchronization, and multi-tenant data persistence across dev and prod environments.

## Decision

1. Adopt FastAPI (Python 3.11) with Pydantic v2 and SQLAlchemy for backend services.
2. Adopt React 19 + TypeScript + Vite 8 + Tailwind CSS for frontend.
3. Freeze OpenAPI 3.0.3 specification in `contracts/openapi.yaml` prior to backend implementation.
4. Orchestrate all local dependencies via Docker Compose with healthchecks.
5. Deploy production gateway via Caddy 2 reverse proxy.
6. Provide dual cloud implementations across Render (PaaS) and AWS (EC2 Compose + Serverless).

## Consequences

- Full environment parity between local development and cloud deployments.
- Zero host tool dependency requirements.
- Strong compile-time and runtime type safety across tiers.
