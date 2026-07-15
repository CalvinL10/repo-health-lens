from datetime import datetime, timezone
import unittest

from repo_health_lens.analysis import analyze_repository
from repo_health_lens.models import IssueSummary, RepositorySnapshot


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
        "issue_activity": (
            IssueSummary(
                number=1,
                kind="issue",
                state="open",
                created_at="2026-07-01T00:00:00Z",
                updated_at="2026-07-10T00:00:00Z",
                closed_at=None,
                comments=2,
            ),
            IssueSummary(
                number=2,
                kind="pull_request",
                state="closed",
                created_at="2026-06-01T00:00:00Z",
                updated_at="2026-07-05T00:00:00Z",
                closed_at="2026-07-05T00:00:00Z",
                comments=1,
            ),
        ),
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
                issue_activity=(),
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

    def test_recent_commented_issue_and_pr_score_as_responsive(self):
        report = analyze_repository(snapshot(), now=NOW)

        responsiveness = next(
            check for check in report.checks if check.key == "responsiveness"
        )

        self.assertEqual(responsiveness.score, 10)
        self.assertIsNone(responsiveness.recommendation)
        self.assertIn("comments=2/2", responsiveness.evidence)

    def test_stale_uncommented_open_work_gets_responsiveness_recommendation(self):
        report = analyze_repository(
            snapshot(
                issue_activity=(
                    IssueSummary(
                        number=7,
                        kind="issue",
                        state="open",
                        created_at="2025-01-01T00:00:00Z",
                        updated_at="2025-01-02T00:00:00Z",
                        closed_at=None,
                        comments=0,
                    ),
                )
            ),
            now=NOW,
        )

        responsiveness = next(
            check for check in report.checks if check.key == "responsiveness"
        )

        self.assertLess(responsiveness.score, 10)
        self.assertIsNotNone(responsiveness.recommendation)
        self.assertIn("stale open=1", responsiveness.evidence)

    def test_missing_issue_activity_is_explicitly_unassessed(self):
        report = analyze_repository(
            snapshot(issue_activity=()),
            now=NOW,
        )

        responsiveness = next(
            check for check in report.checks if check.key == "responsiveness"
        )

        self.assertEqual(responsiveness.score, 0)
        self.assertIn("No issue or pull-request activity", responsiveness.evidence)
