from datetime import datetime, timezone
import unittest

from repo_health_lens.analysis import analyze_repository
from repo_health_lens.models import RepositorySnapshot
from repo_health_lens.render import render_markdown


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
