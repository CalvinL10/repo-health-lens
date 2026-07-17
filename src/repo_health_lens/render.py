from __future__ import annotations

from html import escape

from .models import AnalysisReport


def _html(value: object) -> str:
    return escape(str(value), quote=True)


def _score_class(score: int, max_score: int) -> str:
    if max_score and score / max_score >= 0.8:
        return "good"
    if max_score and score / max_score >= 0.5:
        return "watch"
    return "needs-attention"


def render_html(report: AnalysisReport) -> str:
    rows = []
    for check in report.checks:
        recommendation = (
            f'<p class="recommendation"><strong>Next step:</strong> '
            f"{_html(check.recommendation)}</p>"
            if check.recommendation
            else ""
        )
        rows.append(
            "<tr>"
            f'<th scope="row">{_html(check.label)}</th>'
            f'<td><span class="score {_score_class(check.score, check.max_score)}">'
            f"{check.score}/{check.max_score}</span></td>"
            f'<td>{_html(check.evidence)}{recommendation}</td>'
            "</tr>"
        )

    recommendations = [
        check.recommendation for check in report.checks if check.recommendation
    ]
    recommendations_html = ""
    if recommendations:
        recommendations_html = (
            '<section aria-labelledby="recommendations">'
            '<h2 id="recommendations">Recommended next steps</h2>'
            "<ul>"
            + "".join(f"<li>{_html(item)}</li>" for item in recommendations)
            + "</ul></section>"
        )

    trend_html = ""
    if report.trend:
        changed = [item for item in report.trend.checks if item.delta]
        changed_html = ""
        if changed:
            changed_html = (
                "<ul>"
                + "".join(
                    f"<li>{_html(item.label)}: {item.delta:+d}</li>"
                    for item in changed
                )
                + "</ul>"
            )
        trend_html = (
            '<section class="trend" aria-labelledby="trend">'
            f'<h2 id="trend">Trend: {report.trend.delta:+d} points '
            "vs previous snapshot</h2>"
            f"{changed_html}</section>"
        )

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Repository health: %s</title>
<style>
:root { color-scheme: light; font-family: system-ui, sans-serif; color: #172033; background: #f4f7fb; }
body { margin: 0; }
main { max-width: 980px; margin: 0 auto; padding: 3rem 1.25rem; }
.hero, .check-table, .trend, section { background: #fff; border: 1px solid #dbe3ef; border-radius: 14px; box-shadow: 0 8px 24px #17203312; }
.hero { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 1.5rem; }
h1, h2 { margin-top: 0; }
h1 { margin-bottom: .35rem; font-size: clamp(1.5rem, 4vw, 2.4rem); }
.muted { color: #5d6879; }
.score-card { min-width: 8rem; padding: 1rem; border-radius: 12px; text-align: center; background: #edf3ff; }
.score-card strong { display: block; font-size: 2rem; }
.score { display: inline-block; min-width: 3.5rem; padding: .25rem .5rem; border-radius: 999px; text-align: center; font-weight: 700; }
.good { color: #075b3d; background: #d8f5e8; }
.watch { color: #805400; background: #fff0c7; }
.needs-attention { color: #922b2b; background: #ffe0e0; }
.check-table { width: 100%%; margin: 1.5rem 0; border-collapse: separate; border-spacing: 0; overflow: hidden; }
.check-table th, .check-table td { padding: 1rem; border-bottom: 1px solid #e6ebf2; text-align: left; vertical-align: top; }
.check-table th { width: 25%%; }
.check-table tr:last-child th, .check-table tr:last-child td { border-bottom: 0; }
.recommendation { margin: .65rem 0 0; color: #7b3f00; }
section { margin-top: 1.5rem; padding: 1.25rem 1.5rem; }
li + li { margin-top: .45rem; }
@media (max-width: 650px) { .hero { align-items: flex-start; flex-direction: column; } .score-card { width: 100%%; box-sizing: border-box; } .check-table th, .check-table td { display: block; width: auto; } .check-table tr:not(:last-child) td { border-bottom: 0; padding-top: 0; } }
</style>
</head>
<body>
<main>
<header class="hero">
<div><p class="muted">Repo Health Lens report</p><h1>Repository health: %s</h1><p class="muted">Evidence-backed checks for maintainers and contributors.</p></div>
<div class="score-card"><span>Score</span><strong>%d/100</strong><span>Grade %s</span></div>
</header>
<table class="check-table">
<caption class="muted">Health checks and observable evidence</caption>
<thead><tr><th scope="col">Check</th><th scope="col">Score</th><th scope="col">Evidence</th></tr></thead>
<tbody>%s</tbody>
</table>
%s
%s
</main>
</body>
</html>
""" % (
        _html(report.repository),
        _html(report.repository),
        report.score,
        _html(report.grade),
        "".join(rows),
        recommendations_html,
        trend_html,
    )


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

