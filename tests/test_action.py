import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from repo_health_lens.models import RepositorySnapshot


def complete_snapshot() -> RepositorySnapshot:
    return RepositorySnapshot(
        full_name="owner/repo",
        description="Example",
        default_branch="main",
        archived=False,
        fork=False,
        stars=1,
        forks=1,
        open_issues=0,
        pushed_at="2026-07-10T00:00:00Z",
        created_at="2026-01-01T00:00:00Z",
        license_name="MIT",
        topics=("github",),
        has_wiki=True,
        files=frozenset(
            {
                "readme.md",
                "contributing.md",
                "code_of_conduct.md",
                "security.md",
                "tests",
            }
        ),
        workflow_files=("ci.yml",),
    )


class ActionTests(unittest.TestCase):
    def test_runner_writes_report_and_action_outputs(self):
        runner_path = Path("scripts/run_action.py")
        if not runner_path.exists():
            self.fail("scripts/run_action.py has not been created")
        from scripts import run_action

        class FakeClient:
            def __init__(self, token=None):
                self.token = token

            def snapshot(self, owner, repo):
                self.repository = (owner, repo)
                return complete_snapshot()

        with TemporaryDirectory() as directory:
            directory_path = Path(directory)
            report_path = directory_path / "report.json"
            output_path = directory_path / "github-output"
            with patch.object(run_action, "GitHubClient", FakeClient), patch.dict(
                os.environ, {"GITHUB_OUTPUT": str(output_path)}, clear=False
            ):
                exit_code = run_action.main(
                    [
                        "--repository",
                        "owner/repo",
                        "--format",
                        "json",
                        "--output",
                        str(report_path),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(report_path.read_text())["score"], 90)
            outputs = output_path.read_text()
            self.assertIn("score<<", outputs)
            self.assertIn("\n90\n", outputs)
            self.assertIn("grade<<", outputs)
            self.assertIn("\nA\n", outputs)
            self.assertIn("report-path<<", outputs)
            self.assertIn(f"\n{report_path}\n", outputs)

    def test_action_outputs_keep_multiline_values_as_one_output(self):
        from scripts import run_action

        with TemporaryDirectory() as directory:
            output_path = Path(directory) / "github-output"
            malicious_value = "report.md\nattacker=unexpected"
            with patch.dict(
                os.environ, {"GITHUB_OUTPUT": str(output_path)}, clear=False
            ):
                run_action._set_output("report-path", malicious_value)

            output = output_path.read_text()
            lines = output.splitlines()
            self.assertTrue(lines[0].startswith("report-path<<"))
            delimiter = lines[0].split("<<", 1)[1]
            self.assertEqual(lines[1], "report.md")
            self.assertEqual(lines[2], "attacker=unexpected")
            self.assertEqual(lines[3], delimiter)

    def test_action_manifest_exposes_reusable_report_inputs_and_outputs(self):
        manifest_path = Path("action.yml")
        if not manifest_path.exists():
            self.fail("action.yml has not been created")
        manifest = manifest_path.read_text(encoding="utf-8")

        for name in ("repository", "format", "snapshot", "output", "token"):
            self.assertIn(f"  {name}:", manifest)
        for name in ("score", "grade", "report-path"):
            self.assertIn(f"  {name}:", manifest)
        self.assertIn("using: composite", manifest)
        self.assertIn("scripts/run_action.py", manifest)


if __name__ == "__main__":
    unittest.main()
