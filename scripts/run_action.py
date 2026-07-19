from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from repo_health_lens.analysis import analyze_repository
from repo_health_lens.github import GitHubClient, GitHubError
from repo_health_lens.render import render_html, render_markdown
from repo_health_lens.snapshots import SnapshotError, append_report


def _repository(value: str) -> tuple[str, str]:
    parts = value.strip().strip("/").split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("use OWNER/REPOSITORY")
    return parts[0], parts[1]


def _set_output(name: str, value: object) -> None:
    output_path = os.getenv("GITHUB_OUTPUT")
    if not output_path:
        return
    value_text = str(value)
    delimiter = f"repo-health-lens-{uuid.uuid4().hex}"
    while delimiter in value_text:
        delimiter = f"repo-health-lens-{uuid.uuid4().hex}"
    with Path(output_path).open("a", encoding="utf-8") as output:
        output.write(f"{name}<<{delimiter}\n{value_text}\n{delimiter}\n")


def _render(report, report_format: str) -> str:
    if report_format == "json":
        return json.dumps(report.to_dict(), indent=2) + "\n"
    if report_format == "html":
        return render_html(report)
    return render_markdown(report)


def _build_report(
    repository: str, snapshot_path: str | None, token: str | None
):
    owner, repo = _repository(repository)
    report = analyze_repository(GitHubClient(token=token).snapshot(owner, repo))
    if snapshot_path:
        captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        trend = append_report(Path(snapshot_path), report, captured_at)
        report = replace(report, trend=trend)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Repo Health Lens in GitHub Actions.")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--format", choices=("markdown", "json", "html"), default="markdown")
    parser.add_argument("--snapshot")
    parser.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = _build_report(args.repository, args.snapshot, os.getenv("GITHUB_TOKEN"))
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_render(report, args.format), encoding="utf-8")
        _set_output("score", report.score)
        _set_output("grade", report.grade)
        _set_output("report-path", args.output)
    except (GitHubError, SnapshotError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
