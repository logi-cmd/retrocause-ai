from __future__ import annotations

from retrocause.api.schemas import RetrievalTraceItemV2
from retrocause.evidence_access import describe_source_name


def trace_value(item: object, key: str, default: object = None) -> object:
    if isinstance(item, dict):
        return item.get(key, default)
    if key == "source":
        return getattr(item, "source", getattr(item, "name", default))
    return getattr(item, key, default)


def coerce_optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def coerce_result_count(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def retrieval_status_from_trace(item: object) -> str:
    explicit = str(trace_value(item, "status", "") or "").strip()
    if explicit:
        return explicit
    if bool(trace_value(item, "cache_hit", False)):
        return "cached"
    if trace_value(item, "error"):
        return "source_error"
    return "ok"


def build_retrieval_trace_item_v2(item: object) -> RetrievalTraceItemV2:
    source = str(trace_value(item, "source", "") or "")
    source_metadata = describe_source_name(source)
    return RetrievalTraceItemV2(
        source=source,
        source_label=str(
            trace_value(item, "source_label", "")
            or source_metadata.get("source_label", "")
        ),
        source_kind=str(
            trace_value(item, "source_kind", "")
            or source_metadata.get("source_kind", "unknown")
        ),
        stability=str(
            trace_value(item, "stability", "")
            or source_metadata.get("stability", "unknown")
        ),
        cache_policy=str(
            trace_value(item, "cache_policy", "")
            or source_metadata.get("cache_policy", "no_cache_policy")
        ),
        query=str(trace_value(item, "query", "") or ""),
        result_count=coerce_result_count(trace_value(item, "result_count", 0)),
        cache_hit=bool(trace_value(item, "cache_hit", False)),
        error=trace_value(item, "error"),
        status=retrieval_status_from_trace(item),
        retry_after_seconds=coerce_optional_int(
            trace_value(item, "retry_after_seconds", None)
        ),
    )
