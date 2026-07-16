import unittest

from repo_health_lens.cli import build_parser


class CliTests(unittest.TestCase):
    def test_snapshot_option_accepts_a_history_path(self):
        args = build_parser().parse_args(["owner/repo", "--snapshot", "history.json"])

        self.assertEqual(args.snapshot, "history.json")


if __name__ == "__main__":
    unittest.main()
