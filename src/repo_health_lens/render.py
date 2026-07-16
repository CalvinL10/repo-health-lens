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
    if report.trend:
        lines.extend(
            [
                "",
                f"**Trend: {report.trend.delta:+d} points vs previous snapshot**",
            ]
        )
        changed = [item for item in report.trend.checks if item.delta]
        if changed:
            lines.append(
                "Changed checks: "
                + "; ".join(f"{item.label}: {item.delta:+d}" for item in changed)
                + "."
            )
    recommendations = [
        check.recommendation for check in report.checks if check.recommendation
    ]
    if recommendations:
        lines.extend(["", "## Recommended next steps", ""])
        lines.extend(f"- {item}" for item in recommendations)
    lines.append("")
    return "\n".join(lines)

