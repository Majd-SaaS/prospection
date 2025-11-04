import unittest

from src.linkedin_company_follow import (
    ButtonSnapshot,
    evaluate_button_state,
    merge_unique_urls,
    normalise_company_url,
)


class NormaliseCompanyUrlTests(unittest.TestCase):
    def test_preserves_https(self):
        url = "https://www.linkedin.com/company/example/"
        self.assertEqual(normalise_company_url(url), url)

    def test_adds_protocol(self):
        self.assertEqual(
            normalise_company_url("www.linkedin.com/company/example"),
            "https://www.linkedin.com/company/example",
        )

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            normalise_company_url("")

    def test_rejects_whitespace(self):
        with self.assertRaises(ValueError):
            normalise_company_url("   ")


class EvaluateButtonStateTests(unittest.TestCase):
    def snapshot(self, **kwargs):
        defaults = {
            "texts": set(),
            "aria_label": "",
            "aria_pressed": "",
            "disabled": False,
        }
        defaults.update(kwargs)
        return ButtonSnapshot(**defaults)

    def test_detects_follow_action_by_text(self):
        snapshot = self.snapshot(texts={"follow"})
        self.assertEqual(evaluate_button_state(snapshot), "follow")

    def test_detects_follow_action_by_label(self):
        snapshot = self.snapshot(aria_label="follow company")
        self.assertEqual(evaluate_button_state(snapshot), "follow")

    def test_detects_already_followed_by_text(self):
        snapshot = self.snapshot(texts={"following"})
        self.assertEqual(evaluate_button_state(snapshot), "already followed")

    def test_detects_already_followed_by_aria_pressed(self):
        snapshot = self.snapshot(aria_pressed="true")
        self.assertEqual(evaluate_button_state(snapshot), "already followed")

    def test_unknown_for_disabled_button(self):
        snapshot = self.snapshot(disabled=True, texts={"follow"})
        self.assertEqual(evaluate_button_state(snapshot), "unknown")

    def test_unknown_for_unrelated_button(self):
        snapshot = self.snapshot(texts={"message"})
        self.assertEqual(evaluate_button_state(snapshot), "unknown")


class MergeUniqueUrlsTests(unittest.TestCase):
    def test_merges_and_preserves_order(self):
        merged = merge_unique_urls([
            ["https://a/", "https://b/"],
            ["https://b/", "https://c/"],
            [],
            [" https://d/ "],
        ])
        self.assertEqual(list(merged), [
            "https://a/",
            "https://b/",
            "https://c/",
            "https://d/",
        ])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

