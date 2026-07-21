import io
import json
import unittest
from unittest.mock import patch
import urllib.error

from repo_health_lens.github import GitHubClient, GitHubError
from repo_health_lens.models import IssueSummary


class FakeResponse:
    def __init__(self, payload):
        self.stream = io.BytesIO(json.dumps(payload).encode())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, *args):
        return self.stream.read(*args)


class RawResponse(FakeResponse):
    def __init__(self, payload: bytes):
        self.stream = io.BytesIO(payload)


class GitHubClientTests(unittest.TestCase):
    def test_snapshot_converts_timeout_to_github_error(self):
        with patch("urllib.request.urlopen", side_effect=TimeoutError):
            with self.assertRaisesRegex(GitHubError, "timed out"):
                GitHubClient(timeout=7).snapshot("owner", "repo")

    def test_snapshot_converts_invalid_json_to_github_error(self):
        with patch("urllib.request.urlopen", return_value=RawResponse(b"not json")):
            with self.assertRaisesRegex(GitHubError, "invalid JSON"):
                GitHubClient().snapshot("owner", "repo")

    def test_snapshot_encodes_repository_path_segments(self):
        metadata = {"full_name": "owner/repo", "license": None}

        with patch(
            "urllib.request.urlopen",
            side_effect=[
                FakeResponse(metadata),
                FakeResponse([]),
                FakeResponse([]),
                FakeResponse([]),
            ],
        ) as urlopen:
            GitHubClient().snapshot("owner name", "repo?name")

        urls = [call.args[0].full_url for call in urlopen.call_args_list]
        self.assertTrue(all("/repos/owner%20name/repo%3Fname" in url for url in urls))

    def test_snapshot_rejects_empty_repository_path_segments(self):
        responses = [
            FakeResponse({"full_name": "owner/repo", "license": None}),
            FakeResponse([]),
            FakeResponse([]),
            FakeResponse([]),
        ] * 2
        with patch("urllib.request.urlopen", side_effect=responses) as urlopen:
            with self.assertRaises(ValueError):
                GitHubClient().snapshot("", "repo")
            with self.assertRaises(ValueError):
                GitHubClient().snapshot("owner", "")

        urlopen.assert_not_called()

    def test_snapshot_reads_workflow_files(self):
        metadata = {
            "full_name": "owner/repo",
            "description": "Example",
            "default_branch": "main",
            "archived": False,
            "fork": False,
            "stargazers_count": 0,
            "forks_count": 0,
            "open_issues_count": 0,
            "pushed_at": None,
            "created_at": None,
            "license": None,
            "topics": [],
            "has_wiki": False,
        }
        root_contents = [{"name": ".github", "type": "dir"}]
        workflow_contents = [
            {"name": "ci.yml", "type": "file"},
            {"name": "README.md", "type": "file"},
            {"name": "release.yaml", "type": "file"},
            {"name": "nested", "type": "dir"},
        ]

        with patch(
            "urllib.request.urlopen",
            side_effect=[
                FakeResponse(metadata),
                FakeResponse(root_contents),
                FakeResponse(workflow_contents),
                FakeResponse([]),
            ],
        ):
            snapshot = GitHubClient().snapshot("owner", "repo")

        self.assertEqual(snapshot.workflow_files, ("ci.yml", "release.yaml"))

    def test_snapshot_allows_missing_workflows_directory(self):
        metadata = {
            "full_name": "owner/repo",
            "license": None,
        }
        not_found = urllib.error.HTTPError(
            "https://api.github.com/repos/owner/repo/contents/.github/workflows",
            404,
            "Not Found",
            {},
            io.BytesIO(b'{"message":"Not Found"}'),
        )

        with patch(
            "urllib.request.urlopen",
            side_effect=[
                FakeResponse(metadata),
                FakeResponse([]),
                not_found,
                FakeResponse([]),
            ],
        ):
            snapshot = GitHubClient().snapshot("owner", "repo")

        self.assertEqual(snapshot.workflow_files, ())

    def test_snapshot_reads_issue_and_pull_request_activity(self):
        metadata = {
            "full_name": "owner/repo",
            "license": None,
        }
        issue_activity = [
            {
                "number": 12,
                "state": "open",
                "created_at": "2026-07-01T00:00:00Z",
                "updated_at": "2026-07-10T00:00:00Z",
                "closed_at": None,
                "comments": 3,
            },
            {
                "number": 13,
                "state": "closed",
                "created_at": "2026-06-01T00:00:00Z",
                "updated_at": "2026-07-05T00:00:00Z",
                "closed_at": "2026-07-05T00:00:00Z",
                "comments": 1,
                "pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/13"},
            },
            {"number": "invalid"},
        ]

        with patch(
            "urllib.request.urlopen",
            side_effect=[
                FakeResponse(metadata),
                FakeResponse([]),
                FakeResponse([]),
                FakeResponse(issue_activity),
            ],
        ):
            snapshot = GitHubClient().snapshot("owner", "repo")

        self.assertEqual(
            snapshot.issue_activity,
            (
                IssueSummary(
                    number=12,
                    kind="issue",
                    state="open",
                    created_at="2026-07-01T00:00:00Z",
                    updated_at="2026-07-10T00:00:00Z",
                    closed_at=None,
                    comments=3,
                ),
                IssueSummary(
                    number=13,
                    kind="pull_request",
                    state="closed",
                    created_at="2026-06-01T00:00:00Z",
                    updated_at="2026-07-05T00:00:00Z",
                    closed_at="2026-07-05T00:00:00Z",
                    comments=1,
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
