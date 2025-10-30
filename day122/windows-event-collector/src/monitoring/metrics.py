"""Prometheus metrics setup and helpers for the Windows Event Log Agent."""
from prometheus_client import Counter, Gauge, start_http_server


# Counters for overall system behavior
EVENTS_COLLECTED = Counter(
    "windows_agent_events_collected_total",
    "Total number of Windows events collected by the agent",
)

EVENTS_SENT = Counter(
    "windows_agent_events_sent_total",
    "Total number of Windows events successfully sent by the transport",
)

ERRORS_TOTAL = Counter(
    "windows_agent_errors_total",
    "Total number of errors encountered by the agent",
)


# Gauges for last activity
LAST_COLLECTION_TIMESTAMP = Gauge(
    "windows_agent_last_collection_timestamp_seconds",
    "Unix timestamp of the last event collection",
)


def start_metrics_server(port: int) -> None:
    """Start the Prometheus metrics HTTP server on the given port."""
    # This runs a background thread HTTP server on /metrics
    start_http_server(port)


