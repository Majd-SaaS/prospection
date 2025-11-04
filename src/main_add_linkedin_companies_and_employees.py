"""CLI tool to follow LinkedIn company pages via Selenium.

The script accepts a list of LinkedIn company URLs (via command line arguments,
an input file, or standard input), opens each page in Chrome, and attempts to
click the "Follow" button when it is not already active.  The resulting status
for each URL is printed either as JSON or as a simple table so that the caller
can capture the output when running the script over SSH.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement

from src.linkedin_company_follow import (
    ButtonSnapshot,
    evaluate_button_state,
    merge_unique_urls,
    normalise_company_url,
    snapshot_button,
)


BUTTON_SELECTORS = (
    "button.follow",
    "button[data-control-name='follow']",
    "button[data-test-id='follow-button']",
    "button[data-test-follow-button]",
    "button[aria-label*='Follow']",
)


@dataclass
class FollowResult:
    url: str
    status: str
    reason: Optional[str] = None

    def as_dict(self) -> dict:
        payload = {"url": self.url, "status": self.status}
        if self.reason:
            payload["reason"] = self.reason
        return payload


def build_driver(args: argparse.Namespace) -> webdriver.Chrome:
    options = Options()

    if args.chrome_binary:
        options.binary_location = args.chrome_binary

    if args.user_data_dir:
        options.add_argument(f"--user-data-dir={args.user_data_dir}")

    if args.profile_directory:
        options.add_argument(f"--profile-directory={args.profile_directory}")

    if args.headless:
        options.add_argument("--headless=new")

    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    try:
        return webdriver.Chrome(options=options)
    except WebDriverException as exc:  # pragma: no cover - requires Chrome runtime
        raise SystemExit(
            "Unable to start Chrome. Ensure that chromedriver is installed and "
            "compatible with the Chrome build present on the VM."
        ) from exc


def wait_for_page_ready(driver: webdriver.Chrome, timeout: int) -> None:
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def find_follow_button(driver: webdriver.Chrome) -> Optional[tuple[WebElement, ButtonSnapshot]]:
    for selector in BUTTON_SELECTORS:
        try:
            button = driver.find_element(By.CSS_SELECTOR, selector)
            snapshot = snapshot_button(button)
            if evaluate_button_state(snapshot) != "unknown":
                return button, snapshot
        except NoSuchElementException:
            continue
        except Exception:
            continue

    try:
        buttons = driver.find_elements(By.TAG_NAME, "button")
    except Exception:
        return None

    for button in buttons:
        try:
            snapshot = snapshot_button(button)
        except Exception:
            continue
        if evaluate_button_state(snapshot) != "unknown":
            return button, snapshot

    return None


def click_follow_button(driver: webdriver.Chrome, timeout: int) -> str:
    end_time = time.time() + timeout

    while time.time() < end_time:
        located = find_follow_button(driver)
        if located is None:
            time.sleep(0.5)
            continue

        button, snapshot = located
        state = evaluate_button_state(snapshot)
        if state == "already followed":
            return "already followed"

        if state != "follow":
            time.sleep(0.5)
            continue

        try:
            button.click()
        except Exception:
            time.sleep(0.5)
            continue

        # Wait for the button state to flip to "Following" after the click.
        try:
            def _followed(_driver: webdriver.Chrome) -> bool:
                located = find_follow_button(_driver)
                return bool(located and evaluate_button_state(located[1]) == "already followed")

            WebDriverWait(driver, 10).until(_followed)
            return "follow"
        except TimeoutException:
            pass

    return "error"


def process_url(driver: webdriver.Chrome, url: str, args: argparse.Namespace) -> FollowResult:
    try:
        normalised_url = normalise_company_url(url)
    except ValueError as exc:
        return FollowResult(url=url, status="error", reason=str(exc))

    try:
        driver.get(normalised_url)
        wait_for_page_ready(driver, args.page_load_timeout)
    except TimeoutException:
        return FollowResult(url=normalised_url, status="error", reason="Page load timeout")
    except WebDriverException as exc:
        return FollowResult(url=normalised_url, status="error", reason=str(exc))

    located = find_follow_button(driver)
    if located is None:
        return FollowResult(url=normalised_url, status="error", reason="Follow button not found")

    _, snapshot = located
    state = evaluate_button_state(snapshot)
    if state == "already followed":
        return FollowResult(url=normalised_url, status="already followed")

    if state != "follow":
        return FollowResult(url=normalised_url, status="error", reason="Unexpected button state")

    outcome = click_follow_button(driver, args.follow_timeout)
    if outcome == "follow":
        return FollowResult(url=normalised_url, status="follow")
    if outcome == "already followed":
        return FollowResult(url=normalised_url, status="already followed")
    return FollowResult(url=normalised_url, status="error", reason="Unable to confirm follow action")


def parse_urls(args: argparse.Namespace) -> List[str]:
    sources: list[Iterable[str]] = []

    if args.input_file:
        try:
            with open(args.input_file, "r", encoding="utf-8") as handle:
                sources.append(handle.readlines())
        except OSError as exc:
            raise SystemExit(f"Unable to read input file: {exc}") from exc

    if args.urls:
        sources.append(args.urls)

    if not sys.stdin.isatty():
        sources.append(line for line in sys.stdin)

    urls = merge_unique_urls(sources)

    if not urls:
        raise SystemExit("No company URLs were provided. Supply them as arguments, via --input-file, or through stdin.")

    return list(urls)


def render_results(results: List[FollowResult], output_format: str) -> None:
    if output_format == "json":
        payload = [result.as_dict() for result in results]
        print(json.dumps(payload, indent=2))
        return

    header = f"{'URL':<80} | STATUS | REASON"
    print(header)
    print("-" * len(header))
    for result in results:
        reason = result.reason or ""
        print(f"{result.url:<80} | {result.status:<14} | {reason}")


def parse_arguments(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Follow LinkedIn company pages using a logged-in Chrome session.",
    )

    parser.add_argument("urls", nargs="*", help="LinkedIn company URLs to follow")
    parser.add_argument("--input-file", help="Path to a file containing company URLs (one per line)")
    parser.add_argument("--user-data-dir", help="Chrome user data directory with an authenticated LinkedIn session")
    parser.add_argument("--profile-directory", help="Chrome profile directory to use (e.g. 'Default')")
    parser.add_argument("--chrome-binary", help="Path to the Chrome/Chromium binary to use")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode (Chrome 109+)")
    parser.add_argument("--page-load-timeout", type=int, default=30, help="Seconds to wait for a page to load")
    parser.add_argument("--follow-timeout", type=int, default=20, help="Seconds to wait when attempting to follow a company")
    parser.add_argument("--delay-between", type=float, default=1.5, help="Delay between URL navigations in seconds")
    parser.add_argument("--output-format", choices=("table", "json"), default="table", help="Output results as a table or JSON array")

    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_arguments(argv)
    urls = parse_urls(args)

    driver = build_driver(args)

    results: List[FollowResult] = []

    try:
        for index, url in enumerate(urls, start=1):
            if index > 1 and args.delay_between > 0:
                time.sleep(args.delay_between)

            result = process_url(driver, url, args)
            results.append(result)
    finally:
        driver.quit()

    render_results(results, args.output_format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

