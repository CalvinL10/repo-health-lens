from datetime import datetime, timezone
import unittest

from repo_health_lens.analysis import analyze_repository
from repo_health_lens.models import CheckTrend, RepositorySnapshot, ScoreTrend
from repo_health_lens.render import render_html, render_markdown


class RenderTests(unittest.TestCase):
    def test_markdown_report_contains_score_and_recommendations(self):
        report = analyze_repository(
            RepositorySnapshot(
                full_name="owner/repo",
                description=None,
                default_branch="main",
                archived=False,
                fork=False,
                stars=0,
                forks=0,
                open_issues=0,
                pushed_at="2026-01-01T00:00:00Z",
                created_at="2026-01-01T00:00:00Z",
                license_name=None,
                topics=(),
                has_wiki=False,
                files=frozenset(),
            ),
            now=datetime(2026, 7, 14, tzinfo=timezone.utc),
        )
        markdown = render_markdown(report)
        self.assertIn("Repository health: owner/repo", markdown)
        self.assertIn("Issue and pull-request responsiveness", markdown)
        self.assertIn("No issue or pull-request activity", markdown)
        self.assertIn("Recommended next steps", markdown)

    def test_markdown_report_contains_score_trend(self):
        report = analyze_repository(
            RepositorySnapshot(
                full_name="owner/repo",
                description=None,
                default_branch="main",
                archived=False,
                fork=False,
                stars=0,
                forks=0,
                open_issues=0,
                pushed_at="2026-07-10T00:00:00Z",
                created_at="2026-01-01T00:00:00Z",
                license_name=None,
                topics=(),
                has_wiki=False,
                files=frozenset(),
            )
        )
        report = report.__class__(
            repository=report.repository,
            score=report.score,
            grade=report.grade,
            checks=report.checks,
            trend=ScoreTrend(
                previous_captured_at="2026-07-14T00:00:00Z",
                previous_score=40,
                current_score=report.score,
                delta=4,
                checks=(
                    CheckTrend(
                        key="activity",
                        label="Recent activity",
                        previous_score=5,
                        current_score=9,
                        delta=4,
                    ),
                ),
            ),
        )

        markdown = render_markdown(report)

        self.assertIn("Trend: +4 points vs previous snapshot", markdown)
        self.assertIn("Recent activity: +4", markdown)

    def test_html_report_is_standalone_and_escapes_dynamic_content(self):
        report = analyze_repository(
            RepositorySnapshot(
                full_name="owner/<script>alert(1)</script>",
                description=None,
                default_branch="main",
                archived=False,
                fork=False,
                stars=0,
                forks=0,
                open_issues=0,
                pushed_at="2026-01-01T00:00:00Z",
                created_at="2026-01-01T00:00:00Z",
                license_name=None,
                topics=(),
                has_wiki=False,
                files=frozenset(),
            ),
            now=datetime(2026, 7, 14, tzinfo=timezone.utc),
        )

        html = render_html(report)

        self.assertTrue(html.startswith("<!doctype html>"))
        self.assertIn("<style>", html)
        self.assertIn("Repository health", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("Recommended next steps", html)
