from __future__ import annotations

from typing import Any


def build_octo_status(octo_metrics: dict[str, Any] | None) -> dict[str, Any]:
    metrics = octo_metrics if isinstance(octo_metrics, dict) else {}
    followup_queues = int(metrics.get("followup_queues", 0) or 0)
    internal_queues = int(metrics.get("internal_queues", 0) or 0)
    followup_tasks = int(metrics.get("followup_tasks", 0) or 0)
    internal_tasks = int(metrics.get("internal_tasks", 0) or 0)
    thinking_count = int(metrics.get("thinking_count", 0) or 0)
    queue_pressure = followup_queues + internal_queues
    busy = thinking_count > 0 or queue_pressure > 0
    state = "thinking" if busy else "idle"

    service_status = "ok"
    service_reason = "idle"
    if queue_pressure >= 20:
        service_status = "critical"
        service_reason = f"queue pressure high ({queue_pressure})"
    elif queue_pressure >= 8:
        service_status = "warning"
        service_reason = f"queue pressure rising ({queue_pressure})"
    elif thinking_count > 0:
        service_reason = "processing tasks"

    return {
        "state": state,
        "busy": busy,
        "label": "Busy" if busy else "Idle",
        "reason": service_reason,
        "service_status": service_status,
        "thinking_count": thinking_count,
        "followup_queues": followup_queues,
        "internal_queues": internal_queues,
        "followup_tasks": followup_tasks,
        "internal_tasks": internal_tasks,
        "queue_pressure": queue_pressure,
        "updated_at": metrics.get("updated_at"),
    }
