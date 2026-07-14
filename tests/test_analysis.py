from datetime import datetime, timezone
import unittest

from repo_health_lens.analysis import analyze_repository
from repo_health_lens.models import RepositorySnapshot


NOW = datetime(2026, 7, 14, tzinfo=timezone.utc)


def snapshot(**overrides):
    values = {
        "full_name": "calvin/example",
        "description": "A useful project",
        "default_branch": "main",
        "archived": False,
        "fork": False,
        "stars": 10,
        "forks": 2,
        "open_issues": 1,
        "pushed_at": "2026-07-10T00:00:00Z",
        "created_at": "2026-01-01T00:00:00Z",
        "license_name": "MIT",
        "topics": ("github",),
        "has_wiki": True,
        "files": frozenset(
            {
                "readme.md",
                "contributing.md",
                "code_of_conduct.md",
                "security.md",
                "tests",
                ".github",
            }
        ),
        "workflow_files": ("ci.yml",),
    }
    values.update(overrides)
    return RepositorySnapshot(**values)


class AnalysisTests(unittest.TestCase):
    def test_complete_repository_scores_100(self):
        report = analyze_repository(snapshot(), now=NOW)
        self.assertEqual(report.score, 100)
        self.assertEqual(report.grade, "A")
        self.assertFalse(any(check.recommendation for check in report.checks))

    def test_archived_bare_fork_has_actionable_recommendations(self):
        report = analyze_repository(
            snapshot(
                archived=True,
                fork=True,
                description=None,
                license_name=None,
                topics=(),
                has_wiki=False,
                files=frozenset(),
                workflow_files=(),
            ),
            now=NOW,
        )
        self.assertEqual(report.score, 0)
        self.assertEqual(report.grade, "F")
        self.assertTrue(all(check.recommendation for check in report.checks))

    def test_activity_score_decays_over_time(self):
        recent = analyze_repository(snapshot(), now=NOW)
        stale = analyze_repository(
            snapshot(pushed_at="2024-01-01T00:00:00Z"), now=NOW
        )
        self.assertGreater(recent.score, stale.score)

    def test_github_directory_without_workflow_does_not_count_as_ci(self):
        report = analyze_repository(
            snapshot(files=frozenset({".github", "tests"}), workflow_files=()),
            now=NOW,
        )

        engineering = next(
            check for check in report.checks if check.key == "engineering"
        )
        self.assertEqual(engineering.score, 10)
        self.assertIn("workflow files=0", engineering.evidence)
