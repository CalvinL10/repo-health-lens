from __future__ import annotations

from .models import AnalysisReport


def render_markdown(report: AnalysisReport) -> str:
    lines = [
        f"# Repository health: {report.repository}",
        "",
        f"**Score: {report.score}/100 · Grade: {report.grade}**",
        "",
        "| Check | Score | Evidence |",
        "|---|---:|---|",
    ]
    for check in report.checks:
        evidence = check.evidence.replace("|", "\\|")
        lines.append(
            f"| {check.label} | {check.score}/{check.max_score} | {evidence} |"
        )
    recommendations = [
        check.recommendation for check in report.checks if check.recommendation
    ]
    if recommendations:
        lines.extend(["", "## Recommended next steps", ""])
        lines.extend(f"- {item}" for item in recommendations)
    lines.append("")
    return "\n".join(lines)

