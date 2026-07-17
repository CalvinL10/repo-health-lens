import unittest

from repo_health_lens.cli import build_parser


class CliTests(unittest.TestCase):
    def test_snapshot_option_accepts_a_history_path(self):
        args = build_parser().parse_args(["owner/repo", "--snapshot", "history.json"])

        self.assertEqual(args.snapshot, "history.json")

    def test_format_option_accepts_html(self):
        args = build_parser().parse_args(["owner/repo", "--format", "html"])

        self.assertEqual(args.format, "html")


if __name__ == "__main__":
    unittest.main()
