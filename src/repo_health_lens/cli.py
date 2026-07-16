from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from .analysis import analyze_repository
from .github import GitHubClient, GitHubError
from .render import render_markdown
from .snapshots import SnapshotError, append_report


def _repository(value: str) -> tuple[str, str]:
    parts = value.strip().strip("/").split("/")
    if len(parts) != 2 or not all(parts):
        raise argparse.ArgumentTypeError("use OWNER/REPOSITORY")
    return parts[0], parts[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repo-health-lens",
        description="Generate an explainable health report for a public GitHub repository.",
    )
    parser.add_argument("repository", type=_repository, help="GitHub OWNER/REPOSITORY")
    parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown"
    )
    parser.add_argument(
        "--snapshot",
        metavar="PATH",
        help="append the report to a JSON snapshot history and show its trend",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    owner, repo = args.repository
    try:
        report = analyze_repository(GitHubClient().snapshot(owner, repo))
        if args.snapshot:
            captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            trend = append_report(Path(args.snapshot), report, captured_at)
            report = replace(report, trend=trend)
    except (GitHubError, SnapshotError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

