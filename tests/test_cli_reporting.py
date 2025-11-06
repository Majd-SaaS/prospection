import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.main_add_linkedin_companies_and_employees import (
    FollowResult,
    append_incremental_result,
    compute_exit_code,
    read_queue_file,
    render_results,
    write_queue_file,
)


class RenderResultsTests(unittest.TestCase):
    def setUp(self):
        self.results = [
            FollowResult(url="https://example.com/a", status="follow"),
            FollowResult(url="https://example.com/b", status="already followed"),
            FollowResult(url="https://example.com/c", status="error", reason="Follow button not found"),
        ]

    def test_render_table_and_write_file(self):
        buffer = io.StringIO()
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "results.txt"
            with redirect_stdout(buffer):
                rendered = render_results(self.results, "table", str(destination))

            self.assertIn("already followed", rendered)
            self.assertTrue(destination.exists())
            self.assertEqual(destination.read_text(encoding="utf-8").strip(), rendered.strip())

    def test_render_json(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            rendered = render_results(self.results, "json")

        payload = json.loads(rendered)
        self.assertEqual(len(payload), 3)
        self.assertEqual(payload[2]["reason"], "Follow button not found")


class ComputeExitCodeTests(unittest.TestCase):
    def test_returns_zero_when_no_errors(self):
        results = [
            FollowResult(url="https://example.com/a", status="follow"),
            FollowResult(url="https://example.com/b", status="already followed"),
        ]
        self.assertEqual(compute_exit_code(results), 0)

    def test_returns_one_when_errors_present(self):
        results = [
            FollowResult(url="https://example.com/a", status="follow"),
            FollowResult(url="https://example.com/b", status="error", reason="timeout"),
        ]
        self.assertEqual(compute_exit_code(results), 1)


class QueueFileHelpersTests(unittest.TestCase):
    def test_read_queue_file_rejects_missing(self):
        with self.assertRaises(SystemExit):
            read_queue_file("/tmp/nonexistent-file-for-tests")

    def test_read_and_write_queue_file_cycle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_path = Path(tmpdir) / "queue.txt"
            queue_path.write_text("https://a\n\nhttps://b\n", encoding="utf-8")

            urls = read_queue_file(str(queue_path))
            self.assertEqual(urls, ["https://a", "https://b"])

            write_queue_file(str(queue_path), ["https://b"])
            self.assertEqual(queue_path.read_text(encoding="utf-8"), "https://b\n")

    def test_append_incremental_result_adds_header_once(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "results.csv"

            append_incremental_result(
                str(destination),
                FollowResult(url="https://example.com/a", status="follow"),
            )
            append_incremental_result(
                str(destination),
                FollowResult(url="https://example.com/b", status="error", reason="timeout"),
            )

            contents = destination.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(contents), 3)
            self.assertEqual(contents[0], "timestamp,url,status,reason")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
