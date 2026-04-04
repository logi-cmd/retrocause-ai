"""CLI 入口"""

from __future__ import annotations
import sys

from retrocause.engine import analyze_and_print


def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "恐龙为什么灭绝？"
    print(analyze_and_print(query))


if __name__ == "__main__":
    main()
