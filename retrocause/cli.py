"""Command-line entry point."""

from __future__ import annotations

import sys

from retrocause.app.demo_data import topic_aware_demo_result
from retrocause.formatter import ReportFormatter


def _format_local_notice(query: str) -> str:
    result = topic_aware_demo_result(query)
    formatted = ReportFormatter().format(result)
    return f"[local OSS] Showing topic-matched demo output from the keyless OSS path.\n\n{formatted}"


def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Why did dinosaurs go extinct?"
    print(_format_local_notice(query))


if __name__ == "__main__":
    main()
