import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock


# Provide light-weight Selenium stand-ins so this test module can import the CLI
# helpers without requiring the real Selenium dependency. The production code
# still depends on Selenium being installed at runtime.
mock_selenium = MagicMock()
sys.modules.setdefault("selenium", mock_selenium)

webdriver_mock = MagicMock()
sys.modules.setdefault("selenium.webdriver", webdriver_mock)

exceptions_mock = MagicMock()
exceptions_mock.NoSuchElementException = Exception
exceptions_mock.TimeoutException = Exception
exceptions_mock.WebDriverException = Exception
sys.modules.setdefault("selenium.common", MagicMock())
sys.modules.setdefault("selenium.common.exceptions", exceptions_mock)

chrome_options_mock = MagicMock()
chrome_options_mock.Options = MagicMock
sys.modules.setdefault("selenium.webdriver.chrome", MagicMock())
sys.modules.setdefault("selenium.webdriver.chrome.options", chrome_options_mock)

chrome_service_mock = MagicMock()
chrome_service_mock.Service = MagicMock
sys.modules.setdefault("selenium.webdriver.chrome.service", chrome_service_mock)

by_mock = MagicMock()
by_mock.By = MagicMock()
sys.modules.setdefault("selenium.webdriver.common", MagicMock())
sys.modules.setdefault("selenium.webdriver.common.by", by_mock)

support_ui_mock = MagicMock()
support_ui_mock.WebDriverWait = MagicMock
sys.modules.setdefault("selenium.webdriver.support", MagicMock())
sys.modules.setdefault("selenium.webdriver.support.ui", support_ui_mock)

remote_webelement_mock = MagicMock()
remote_webelement_mock.WebElement = MagicMock
sys.modules.setdefault("selenium.webdriver.remote", MagicMock())
sys.modules.setdefault("selenium.webdriver.remote.webelement", remote_webelement_mock)

from src.main_add_linkedin_companies_and_employees import (  # noqa: E402
    FollowResult,
    compute_exit_code,
    render_results,
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


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
