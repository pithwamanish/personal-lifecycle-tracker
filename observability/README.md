# Observability Infrastructure — Personal Lifecycle Tracker

A decoupled, production-grade observability stack containing **OpenTelemetry Collector**, **Prometheus**, **Loki**, **Tempo**, and **Grafana** (LGTM + OTel).

---

## 1. Architecture & Design Principles

```
                              ┌──────────────────────────────────────────┐
                              │            Application Stack             │
                              │  (FastAPI Backend / React Vite Frontend) │
                              └────────────────────┬─────────────────────┘
                                                   │
                              OTLP Traces / Metrics / Logs (HTTP 4328 / gRPC 4327)
                                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              Observability Compose Stack                               │
│                                                                                        │
│                         ┌────────────────────────────────────┐                         │
│                         │   OpenTelemetry Collector Contrib  │                         │
│                         │   (receivers: OTLP gRPC/HTTP)      │                         │
│                         └───────┬────────────┬───────────┬───┘                         │
│                                 │            │           │                             │
│                     Traces      │    Metrics │           │ Logs                        │
│                     (OTLP)      │   (Scrape) │           │ (Loki push)                 │
│                                 ▼            ▼           ▼                             │
│                           ┌───────────┐ ┌──────────┐ ┌──────────┐                      │
│                           │   Tempo   │ │Prometheus│ │   Loki   │                      │
│                           │  (Traces) │ │(Metrics) │ │  (Logs)  │                      │
│                           └─────┬─────┘ └────┬─────┘ └────┬─────┘                      │
│                                 │            │            │                            │
│                                 └────────────┼────────────┘                            │
│                                              ▼                                         │
│                                       ┌──────────────┐                                 │
│                                       │   Grafana    │                                 │
│                                       │ (Dashboards) │                                 │
│                                       └──────────────┘                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Decoupled Lifecycle**: The observability stack runs as an independent Docker Compose project (`personal-lifecycle-observability`). Application reloads, restarts, or crashes never disrupt telemetry collection or wipe dashboard history.
- **Cross-Pillar Correlation**: Pre-provisioned Grafana datasources link traces directly to relevant logs (Tempo $\to$ Loki), logs directly to traces (Loki $\to$ Tempo via `TraceID`), and metrics to traces (Tempo $\to$ Prometheus).
- **Collision-Resistant Ports**: Configured with non-colliding default ports to operate smoothly alongside other services and stacks on the machine.

---

## 2. Service Endpoints & Port Map

| Component | Service Name | Container Port | Host Port (Configurable) | Description |
|---|---|---|---|---|
| **OpenTelemetry Collector** | `otel-collector` | `4317` | `4327` (`${OTEL_GRPC_PORT:-4327}`) | OTLP gRPC Receiver |
| **OpenTelemetry Collector** | `otel-collector` | `4318` | `4328` (`${OTEL_HTTP_PORT:-4328}`) | OTLP HTTP Receiver |
| **OpenTelemetry Collector** | `otel-collector` | `8889` | `8899` (`${OTEL_METRICS_PORT:-8899}`) | Collector Prometheus Metrics Exporter |
| **OpenTelemetry Collector** | `otel-collector` | `8888` | *Internal* | Collector Internal Health & Pipeline Telemetry |
| **Prometheus** | `prometheus` | `9090` | `9091` (`${PROMETHEUS_PORT:-9091}`) | Metrics Storage & Query Engine |
| **Loki** | `loki` | `3100` | `3101` (`${LOKI_PORT:-3101}`) | Log Aggregation Engine |
| **Tempo** | `tempo` | `3200` | `3201` (`${TEMPO_PORT:-3201}`) | Distributed Tracing Storage |
| **Grafana** | `grafana` | `3000` | `3004` (`${GRAFANA_PORT:-3004}`) | Unified Dashboard & Explorer UI |

> **Default Grafana Credentials**: `admin` / `admin`

---

## 3. Directory Layout

```
observability/
├── docker-compose.yaml                 # Standalone Compose project definition
├── .env.example                        # Configurable port & container name overrides
├── otel-collector-config.yaml          # Collector pipelines routing traces, metrics & logs
├── prometheus.yml                      # Prometheus scrape targets
├── loki-config.yaml                    # Loki filesystem & TSDB config
├── tempo-config.yaml                   # Tempo local trace storage & OTLP ingestion
└── grafana/
    ├── dashboards/
    │   └── lifecycle-tracker-overview.json # Golden Signals overview dashboard
    └── provisioning/
        ├── dashboards/
        │   └── dashboards.yaml         # Auto-provisioning provider for dashboards
        └── datasources/
            └── datasources.yaml        # Correlated Prometheus, Loki & Tempo datasources
```

---

## 4. How to Run

### Start the Observability Stack
```bash
# Using root Makefile
make obs-up

# Or directly with Docker Compose
docker compose -f observability/docker-compose.yaml up -d
```

### Check Status & Health
```bash
make obs-ps
# or
docker compose -f observability/docker-compose.yaml ps
```

### View Live Logs
```bash
make obs-logs
# Or specific component:
docker compose -f observability/docker-compose.yaml logs -f otel-collector
```

### Tear Down
```bash
make obs-down
# or
docker compose -f observability/docker-compose.yaml down -v
```

---

## 5. Verification Traffic Test

To verify that the OpenTelemetry Collector and pipelines are actively processing telemetry:

```bash
# Send test log payload to Collector via OTLP HTTP
NOW_NANO=$(date +%s000000000)
curl -i -X POST http://localhost:4328/v1/logs \
  -H "Content-Type: application/json" \
  -d '{
    "resourceLogs": [{
      "resource": {
        "attributes": [
          {"key": "service.name", "value": {"stringValue": "verification-test"}},
          {"key": "deployment.environment", "value": {"stringValue": "development"}},
          {"key": "service.version", "value": {"stringValue": "dev-latest"}}
        ]
      },
      "scopeLogs": [{
        "scope": {"name": "test-logger"},
        "logRecords": [{
          "timeUnixNano": "'"${NOW_NANO}"'",
          "severityNumber": 9,
          "severityText": "INFO",
          "body": {"stringValue": "OpenTelemetry Collector verification test log"}
        }]
      }]
    }]
  }'
```

Check Collector logs to confirm receipt:
```bash
docker compose -f observability/docker-compose.yaml logs otel-collector
```

---

## 6. Connecting Applications

### From the Host (Development / Hot-Reloading)
Configure application environment variables:
```ini
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4328
OTEL_SERVICE_NAME=api-backend
OTEL_RESOURCE_ATTRIBUTES=service.name=api-backend,deployment.environment=development,service.version=dev-latest
```

### From Docker Compose Application Stack
Attach the application services to the `personal-lifecycle-observability-net` network:
```yaml
services:
  backend:
    environment:
      OTEL_EXPORTER_OTLP_ENDPOINT: http://personal-lifecycle-otel-collector:4318
    networks:
      - default
      - observability-net

networks:
  default:
  observability-net:
    external: true
    name: personal-lifecycle-observability-net
```
