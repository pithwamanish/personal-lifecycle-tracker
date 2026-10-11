from __future__ import annotations

import logging
import os
import re
import sys
import time
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logger = logging.getLogger("telemetry")

# Environment & Version Metadata (The Golden Triangle Invariant)
SERVICE_NAME: str = os.getenv("OTEL_SERVICE_NAME", "api-backend")
ENVIRONMENT: str = os.getenv("APP_ENV", os.getenv("DEPLOYMENT_ENVIRONMENT", "development"))
VERSION: str = os.getenv("APP_VERSION", os.getenv("SERVICE_VERSION", "dev-latest"))
OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://personal-lifecycle-otel-collector:4318")

# Prometheus Registry
REGISTRY = CollectorRegistry()

# -----------------------------------------------------------------------------
# Prometheus Metric Instruments
# -----------------------------------------------------------------------------

# Metadata / Build Info metric
APP_INFO = Gauge(
    "app_info",
    "Application metadata containing deployment environment and service version",
    ["deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)
APP_INFO.labels(
    deployment_environment=ENVIRONMENT,
    service_version=VERSION,
    service_name=SERVICE_NAME,
).set(1)

# 1. Golden Signals: HTTP Request Rate, Latency & Errors
HTTP_REQUEST_DURATION = Histogram(
    "app_http_server_duration_milliseconds",
    "HTTP server request execution duration in milliseconds",
    ["http_route", "http_status_code", "http_method", "deployment_environment", "service_version", "service_name"],
    buckets=(5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0),
    registry=REGISTRY,
)

HTTP_REQUESTS_TOTAL = Counter(
    "app_http_requests_total",
    "Total count of HTTP requests processed by the server",
    ["http_route", "http_status_code", "http_method", "deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

# 2. Product Metrics: Lifecycle Items (Renewals, Maintenance, Warranties)
ITEMS_CREATED_TOTAL = Counter(
    "app_items_created_total",
    "Total count of lifecycle items created by users or groups",
    ["lifecycle_type", "deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

ITEM_CREATION_FAILURES_TOTAL = Counter(
    "app_item_creation_failures_total",
    "Total count of lifecycle item creation failures by lifecycle type",
    ["lifecycle_type", "deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

ITEMS_COMPLETED_TOTAL = Counter(
    "app_items_completed_total",
    "Total count of lifecycle items marked as complete",
    ["lifecycle_type", "deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

ITEMS_DELETED_TOTAL = Counter(
    "app_items_deleted_total",
    "Total count of lifecycle items permanently deleted",
    ["lifecycle_type", "deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

LIFECYCLE_ITEMS_CURRENT = Gauge(
    "app_lifecycle_items_current",
    "Instantaneous count of lifecycle items in the database by status and type",
    ["lifecycle_type", "status", "deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

# 3. Product Metrics: Accounts, Authentication & Shared Groups
USER_SIGNUPS_TOTAL = Counter(
    "app_user_signups_total",
    "Total user registration events",
    ["deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

USER_LOGINS_TOTAL = Counter(
    "app_user_logins_total",
    "Total user login attempts by outcome status",
    ["status", "deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

GROUPS_CREATED_TOTAL = Counter(
    "app_groups_created_total",
    "Total shared groups created",
    ["deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

GROUP_MEMBERS_INVITED_TOTAL = Counter(
    "app_group_members_invited_total",
    "Total group members invited or added",
    ["deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

# 4. Product Metrics: Reminders & Daily Morning Email Digests
DIGESTS_GENERATED_TOTAL = Counter(
    "app_digests_generated_total",
    "Total daily morning email digests generated or sent",
    ["status", "deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)

REMINDERS_SUMMARY_REQUESTS_TOTAL = Counter(
    "app_reminders_summary_requests_total",
    "Total in-app reminder summaries requested by users",
    ["deployment_environment", "service_version", "service_name"],
    registry=REGISTRY,
)


def _init_default_series() -> None:
    """Pre-initialize key series so metric queries return series even before first traffic."""
    for l_type in ("renewal", "maintenance", "warranty"):
        ITEMS_CREATED_TOTAL.labels(lifecycle_type=l_type, deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
        ITEMS_COMPLETED_TOTAL.labels(lifecycle_type=l_type, deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
        ITEMS_DELETED_TOTAL.labels(lifecycle_type=l_type, deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
        ITEM_CREATION_FAILURES_TOTAL.labels(lifecycle_type=l_type, deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
        for st in ("active", "completed", "overdue"):
            LIFECYCLE_ITEMS_CURRENT.labels(lifecycle_type=l_type, status=st, deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME).set(0)

    ITEM_CREATION_FAILURES_TOTAL.labels(lifecycle_type="unknown", deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
    USER_SIGNUPS_TOTAL.labels(deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
    USER_LOGINS_TOTAL.labels(status="success", deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
    USER_LOGINS_TOTAL.labels(status="failure", deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
    DIGESTS_GENERATED_TOTAL.labels(status="success", deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
    DIGESTS_GENERATED_TOTAL.labels(status="failure", deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
    REMINDERS_SUMMARY_REQUESTS_TOTAL.labels(deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
    GROUPS_CREATED_TOTAL.labels(deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)
    GROUP_MEMBERS_INVITED_TOTAL.labels(deployment_environment=ENVIRONMENT, service_version=VERSION, service_name=SERVICE_NAME)


_init_default_series()


# -----------------------------------------------------------------------------
# Metric Recording Helper Functions
# -----------------------------------------------------------------------------

def record_http_request(method: str, route: str, status_code: int | str, duration_ms: float) -> None:
    code_str = str(status_code)
    HTTP_REQUEST_DURATION.labels(
        http_route=route,
        http_status_code=code_str,
        http_method=method,
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).observe(duration_ms)

    HTTP_REQUESTS_TOTAL.labels(
        http_route=route,
        http_status_code=code_str,
        http_method=method,
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def record_item_created(lifecycle_type: str) -> None:
    ITEMS_CREATED_TOTAL.labels(
        lifecycle_type=lifecycle_type,
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def record_item_creation_failure(lifecycle_type: str = "unknown") -> None:
    """Record a failed lifecycle item creation attempt."""
    ITEM_CREATION_FAILURES_TOTAL.labels(
        lifecycle_type=lifecycle_type,
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def record_item_completed(lifecycle_type: str) -> None:
    ITEMS_COMPLETED_TOTAL.labels(
        lifecycle_type=lifecycle_type,
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def record_item_deleted(lifecycle_type: str) -> None:
    ITEMS_DELETED_TOTAL.labels(
        lifecycle_type=lifecycle_type,
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def record_user_signup() -> None:
    USER_SIGNUPS_TOTAL.labels(
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def record_user_login(success: bool) -> None:
    USER_LOGINS_TOTAL.labels(
        status="success" if success else "failure",
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def record_group_created() -> None:
    GROUPS_CREATED_TOTAL.labels(
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def record_group_member_invited() -> None:
    GROUP_MEMBERS_INVITED_TOTAL.labels(
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def record_digest_generated(success: bool) -> None:
    DIGESTS_GENERATED_TOTAL.labels(
        status="success" if success else "failure",
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def record_reminders_summary_requested() -> None:
    REMINDERS_SUMMARY_REQUESTS_TOTAL.labels(
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).inc()


def update_lifecycle_items_gauge(lifecycle_type: str, status: str, count: int) -> None:
    LIFECYCLE_ITEMS_CURRENT.labels(
        lifecycle_type=lifecycle_type,
        status=status,
        deployment_environment=ENVIRONMENT,
        service_version=VERSION,
        service_name=SERVICE_NAME,
    ).set(count)


# -----------------------------------------------------------------------------
# OpenTelemetry SDK Integration (Traces & Metrics OTLP Exporter)
# -----------------------------------------------------------------------------

def init_opentelemetry(app: FastAPI) -> None:
    """Initialize OpenTelemetry tracer and meter providers with Golden Triangle resource attributes."""
    is_test_env = "pytest" in sys.modules or os.getenv("TESTING", "").lower() in ("1", "true")
    if is_test_env:
        return

    otlp_endpoint = (os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or "").strip()
    if not otlp_endpoint or (not otlp_endpoint.startswith("http://") and not otlp_endpoint.startswith("https://")):
        logger.info("Remote OTLP exporter skipped (no valid http/https endpoint configured)")
        return

    try:
        from opentelemetry import metrics as otel_metrics
        from opentelemetry import trace as otel_trace
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.semconv.resource import ResourceAttributes

        resource = Resource.create(
            {
                ResourceAttributes.SERVICE_NAME: SERVICE_NAME,
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: ENVIRONMENT,
                ResourceAttributes.SERVICE_VERSION: VERSION,
            }
        )

        # Tracing Setup
        tracer_provider = TracerProvider(resource=resource)
        traces_endpoint = f"{OTLP_ENDPOINT}/v1/traces" if not OTLP_ENDPOINT.endswith("/v1/traces") else OTLP_ENDPOINT
        span_exporter = OTLPSpanExporter(endpoint=traces_endpoint)

        # In AWS Lambda serverless runtime, export spans synchronously to prevent CPU freeze loss
        is_lambda = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("AWS_EXECUTION_ENV"))
        if is_lambda:
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor
            tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
        else:
            tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
        otel_trace.set_tracer_provider(tracer_provider)

        # Metrics Setup
        metrics_endpoint = f"{OTLP_ENDPOINT}/v1/metrics"
        metric_exporter = OTLPMetricExporter(endpoint=metrics_endpoint)
        metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=5000)
        meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        otel_metrics.set_meter_provider(meter_provider)

        logger.info(
            "OpenTelemetry initialized (service=%s, env=%s, ver=%s, otlp=%s)",
            SERVICE_NAME,
            ENVIRONMENT,
            VERSION,
            OTLP_ENDPOINT,
        )
    except Exception as exc:
        logger.warning("OpenTelemetry initialization deferred or optional: %s", exc)


# -----------------------------------------------------------------------------
# Pure ASGI Metrics Middleware & Route Normalization
# -----------------------------------------------------------------------------

UUID_REGEX = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")

EXCLUDED_PATHS = {"/health", "/healthz", "/metrics", "/favicon.ico", "/docs", "/redoc", "/openapi.json"}


def normalize_scope_path(scope: dict) -> str:
    """Extract low-cardinality route template or sanitize dynamic IDs to prevent metric cardinality explosion."""
    raw_path = scope.get("path", "")
    sanitized = UUID_REGEX.sub("{id}", raw_path)
    return sanitized


class MetricsMiddleware:
    """High-performance pure ASGI middleware that records HTTP duration and request counts."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        if path in EXCLUDED_PATHS:
            return await self.app(scope, receive, send)

        start_time = time.perf_counter()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            method = scope.get("method", "GET")
            route_path = normalize_scope_path(scope)
            record_http_request(
                method=method,
                route=route_path,
                status_code=status_code,
                duration_ms=duration_ms,
            )


def setup_telemetry_middleware(app: FastAPI) -> None:
    """Attach HTTP metrics tracking middleware and /metrics scraping endpoint to FastAPI app."""
    app.add_middleware(MetricsMiddleware)

    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint() -> PlainTextResponse:
        return PlainTextResponse(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
