import io
import json
import unittest
from unittest.mock import patch
import urllib.error

from repo_health_lens.github import GitHubClient


class FakeResponse:
    def __init__(self, payload):
        self.stream = io.BytesIO(json.dumps(payload).encode())

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, *args):
        return self.stream.read(*args)


class GitHubClientTests(unittest.TestCase):
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
            side_effect=[FakeResponse(metadata), FakeResponse([]), not_found],
        ):
            snapshot = GitHubClient().snapshot("owner", "repo")

        self.assertEqual(snapshot.workflow_files, ())


if __name__ == "__main__":
    unittest.main()
