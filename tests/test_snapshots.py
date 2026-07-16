import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from repo_health_lens.models import AnalysisReport, CheckResult
from repo_health_lens.snapshots import SnapshotError, append_report, load_history


def report(score: int, activity_score: int) -> AnalysisReport:
    return AnalysisReport(
        repository="owner/repo",
        score=score,
        grade="A" if score >= 90 else "B",
        checks=(
            CheckResult(
                key="activity",
                label="Recent activity",
                score=activity_score,
                max_score=15,
                evidence=f"Last push score={activity_score}.",
            ),
            CheckResult(
                key="docs",
                label="Documentation",
                score=score - activity_score,
                max_score=85,
                evidence="README is present.",
            ),
        ),
    )


class SnapshotTests(unittest.TestCase):
    def test_appending_reports_returns_score_and_check_trends(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"

            self.assertIsNone(append_report(path, report(80, 10), "2026-07-14T00:00:00Z"))
            trend = append_report(path, report(84, 12), "2026-07-15T00:00:00Z")

            self.assertEqual(trend.previous_score, 80)
            self.assertEqual(trend.current_score, 84)
            self.assertEqual(trend.delta, 4)
            self.assertEqual(trend.checks[0].delta, 2)
            self.assertEqual(trend.checks[1].delta, 2)
            self.assertEqual(len(load_history(path)), 2)

    def test_history_rejects_a_different_repository(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            path.write_text(
                json.dumps({"version": 1, "repository": "other/repo", "snapshots": []}),
                encoding="utf-8",
            )

            with self.assertRaises(SnapshotError):
                append_report(path, report(80, 10), "2026-07-14T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
