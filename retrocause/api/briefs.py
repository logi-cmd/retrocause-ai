from __future__ import annotations

from typing import Any


def humanize_identifier(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("_", " ").replace("-", " ")
    text = " ".join(text.split())
    if not text:
        return ""
    return text[:1].upper() + text[1:]


def format_source_label(value: object) -> str:
    raw = str(value or "").strip()
    if raw.startswith("EvidenceType."):
        raw = raw.split(".", 1)[1]
    labels = {
        "NEWS": "News",
        "PAPER": "Paper",
        "OFFICIAL": "Official",
        "WEB": "Web",
        "OTHER": "Other",
    }
    return labels.get(raw.upper(), humanize_identifier(raw) or "Unknown")


def challenge_check_phrase(refuting_count: int) -> str:
    if refuting_count:
        return f"challenge evidence found: {refuting_count}"
    return "no challenge evidence found"


def source_trace_status_label(status: str) -> str:
    labels = {
        "ok": "ok",
        "recovered": "recovered",
        "empty": "no-hits",
        "stale_filtered": "stale-filtered",
        "cached": "cached",
        "source_limited": "source-limited",
        "rate_limited": "rate-limited",
        "forbidden": "forbidden",
        "timeout": "timeout",
        "source_error": "source-error",
    }
    return labels.get(status, status.replace("_", "-") if status else "unknown")


def markdown_bullet(text: str) -> str:
    normalized = " ".join(str(text).split())
    return f"- {normalized}" if normalized else "- "


def build_markdown_research_brief(response: Any) -> str:
    title = (
        response.production_brief.title
        if response.production_brief
        else "RetroCause Research Brief"
    )
    lines: list[str] = [
        f"# {title}",
        "",
        "## Question",
        response.query or "(empty query)",
        "",
        "## Run Status",
        markdown_bullet(f"Mode: {response.analysis_mode}"),
        markdown_bullet(f"Freshness: {response.freshness_status}"),
    ]
    if response.time_range:
        lines.append(markdown_bullet(f"Time range: {response.time_range}"))
    if response.partial_live_reasons:
        lines.append(markdown_bullet(f"Limits: {'; '.join(response.partial_live_reasons)}"))

    brief = response.analysis_brief
    lines.extend(["", "## Likely Explanation"])
    if brief:
        lines.append(brief.answer)
        lines.append(markdown_bullet(f"Confidence signal: {brief.confidence:.0%}"))
    else:
        lines.append("No analysis brief was produced for this run.")

    lines.extend(["", "## Top Reasons"])
    if brief and brief.top_reasons:
        lines.extend(markdown_bullet(reason) for reason in brief.top_reasons)
    else:
        lines.append("- No reason list is available.")

    if response.production_brief:
        lines.extend(["", "## Production Brief", "", response.production_brief.executive_summary])
        for section in response.production_brief.sections:
            lines.extend(["", f"### {section.title}"])
            for item in section.items:
                evidence_note = (
                    ", ".join(item.evidence_ids)
                    if item.evidence_ids
                    else "verification needed"
                )
                lines.append(markdown_bullet(f"{item.summary} Evidence: {evidence_note}."))

        lines.extend(["", "## Next Verification Steps"])
        if response.production_brief.next_verification_steps:
            lines.extend(
                markdown_bullet(step)
                for step in response.production_brief.next_verification_steps
            )
        else:
            lines.append("- No production verification steps were generated.")

        lines.extend(["", "## Production Limits"])
        if response.production_brief.limits:
            lines.extend(markdown_bullet(limit) for limit in response.production_brief.limits)
        else:
            lines.append("- No additional production limits were generated.")

    lines.extend(["", "## Challenge Coverage"])
    if brief and brief.challenge_summary:
        lines.append(markdown_bullet(brief.challenge_summary))
    if response.challenge_checks:
        for check in response.challenge_checks[:5]:
            lines.append(
                markdown_bullet(
                    f"{humanize_identifier(check.source)} -> "
                    f"{humanize_identifier(check.target)}: "
                    f"{check.status}, {challenge_check_phrase(check.refuting_count)}, "
                    f"{check.context_count} context, {check.result_count} retrieved"
                )
            )
    elif not brief or not brief.challenge_summary:
        lines.append("- Challenge retrieval was not checked.")

    lines.extend(["", "## Gaps And Caveats"])
    if brief and brief.missing_evidence:
        lines.extend(markdown_bullet(item) for item in brief.missing_evidence)
    else:
        lines.append("- No explicit gap list was produced.")

    lines.extend(["", "## Evidence"])
    if response.evidences:
        for item in response.evidences[:8]:
            stance = "Challenges" if item.stance == "refuting" or not item.is_supporting else "Supports"
            content = " ".join(item.content.split())
            lines.append(
                markdown_bullet(
                    f"[{item.id}] {stance}. Source: {format_source_label(item.source)}. "
                    f"Reliability: {item.reliability}. {content}"
                )
            )
    else:
        lines.append("- No evidence items are attached.")

    lines.extend(["", "## Source Trace"])
    if response.retrieval_trace:
        for item in response.retrieval_trace[:8]:
            label = item.source_label or item.source
            cache_note = "cache hit" if item.cache_hit else "fresh query"
            status_note = f"status: {source_trace_status_label(item.status)}"
            retry_note = (
                f", retry after {item.retry_after_seconds}s"
                if item.retry_after_seconds is not None
                else ""
            )
            lines.append(
                markdown_bullet(
                    f"{label}: {item.result_count} result(s), {status_note}{retry_note}, "
                    f"{cache_note}, source kind: {item.source_kind}, "
                    f"stability: {item.stability}, cache policy: {item.cache_policy}. "
                    f"Query: {item.query}"
                )
            )
    else:
        lines.append("- No retrieval trace is attached.")

    lines.extend(
        [
            "",
            "## Use Note",
            "This brief is evidence-grounded product output, not verified causal truth. Review source quality, challenge coverage, and missing evidence before relying on it.",
        ]
    )
    return "\n".join(lines)
