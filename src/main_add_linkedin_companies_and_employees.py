"""Queue-based launcher that relies on the Chrome extension for automation.

The script reads company URLs from a queue file (or from standard inputs),
opens each page in the default browser, and waits for the Chrome extension
to report whether the Follow action succeeded.  Results are appended to a CSV
log as they arrive, and completed URLs are removed from the queue file so the
list can be reused between runs.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import uuid
import webbrowser
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable, List, Optional, Sequence
from urllib.parse import parse_qs, quote, urlparse, urlunparse

from src.linkedin_company_follow import merge_unique_urls, normalise_company_url


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


def render_results(
    results: List[FollowResult],
    output_format: str,
    output_path: Optional[str] = None,
) -> str:
    if output_format == "json":
        payload = [result.as_dict() for result in results]
        rendered = json.dumps(payload, indent=2)
    else:
        lines = []
        header = f"{'URL':<80} | STATUS         | REASON"
        lines.append(header)
        lines.append("-" * len(header))
        for result in results:
            reason = result.reason or ""
            lines.append(f"{result.url:<80} | {result.status:<14} | {reason}")
        rendered = "\n".join(lines)

    if output_path:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        text_to_write = rendered if rendered.endswith("\n") else f"{rendered}\n"
        destination.write_text(text_to_write, encoding="utf-8")

    print(rendered)
    return rendered


def compute_exit_code(results: List[FollowResult]) -> int:
    return 0 if all(result.status != "error" for result in results) else 1


def read_queue_file(queue_file: str) -> List[str]:
    path = Path(queue_file)
    if not path.exists():
        raise SystemExit(f"Queue file '{queue_file}' does not exist.")

    with path.open("r", encoding="utf-8") as handle:
        urls = [line.strip() for line in handle if line.strip()]

    if not urls:
        raise SystemExit(f"Queue file '{queue_file}' does not contain any URLs.")

    return urls


def write_queue_file(queue_file: str, remaining_urls: Sequence[str]) -> None:
    path = Path(queue_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for url in remaining_urls:
            handle.write(f"{url}\n")


def append_incremental_result(destination: str, result: FollowResult) -> None:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    header_needed = not path.exists()
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    reason = result.reason or ""

    with path.open("a", encoding="utf-8") as handle:
        if header_needed:
            handle.write("timestamp,url,status,reason\n")
        handle.write(f"{timestamp},{result.url},{result.status},{reason}\n")


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
        raise SystemExit(
            "No company URLs were provided. "
            "Supply them as arguments, via --input-file, --queue-file, or through stdin."
        )

    return list(urls)


class DailyQuotaTracker:
    """Tracks the number of processed URLs per calendar day."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path) if path else Path.home() / ".prospection_daily_quota.json"
        self._load_state()

    def _load_state(self) -> None:
        self.current_date = datetime.now().astimezone().date()
        self.count = 0
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            stored_date = payload.get("date")
            stored_count = payload.get("count", 0)
            if stored_date == self.current_date.isoformat():
                self.count = int(stored_count)
        except Exception:
            self.count = 0

    def _persist(self) -> None:
        data = {"date": self.current_date.isoformat(), "count": self.count}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def remaining(self, limit: int) -> int:
        if limit <= 0:
            return float("inf")
        return max(0, limit - self.count)

    def record(self, limit: int) -> None:
        if limit <= 0:
            return
        self.count += 1
        self._persist()


class ResultStore:
    """Thread-safe store that blocks until the extension reports a result."""

    def __init__(self) -> None:
        self._results: dict[str, dict] = {}
        self._condition = threading.Condition()

    def add_result(self, task_id: str, payload: dict) -> None:
        with self._condition:
            self._results[task_id] = payload
            self._condition.notify_all()

    def wait_for(self, task_id: str, timeout: float) -> Optional[dict]:
        deadline = time.time() + timeout
        with self._condition:
            while task_id not in self._results:
                remaining = deadline - time.time()
                if remaining <= 0:
                    return None
                self._condition.wait(timeout=remaining)
            return self._results.pop(task_id)


class _ResultRequestHandler(BaseHTTPRequestHandler):
    store: ResultStore  # populated dynamically

    def _handle_report(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or "{}")
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid JSON payload")
            return

        missing = [field for field in ("task_id", "url", "status") if field not in payload]
        if missing:
            self.send_error(HTTPStatus.BAD_REQUEST, f"Missing fields: {', '.join(missing)}")
            return

        task_id = str(payload["task_id"])
        self.store.add_result(task_id, payload)
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def _handle_launch(self, query: str, page_duration: float) -> None:
        params = parse_qs(query)
        task_id = params.get("task_id", [""])[0]
        target_url = params.get("url", [""])[0]

        if not task_id or not target_url:
            self.send_error(HTTPStatus.BAD_REQUEST, "task_id and url are required")
            return

        # Basic validation
        parsed = urlparse(target_url)
        if parsed.scheme not in {"http", "https"}:
            self.send_error(HTTPStatus.BAD_REQUEST, "Only http/https targets are supported.")
            return

        payload = json.dumps(
            {
                "task_id": task_id,
                "port": self.server.server_address[1],
                "page_duration": page_duration,
            }
        )
        escaped_payload = payload.replace("</", "<\\/")
        body = f"""<!DOCTYPE html>
<meta charset="utf-8">
<title>LinkedIn Prospection Launcher</title>
<script>
  window.name = 'prospection::{escaped_payload}';
  window.location.replace({json.dumps(target_url)});
</script>
"""
        encoded = body.encode("utf-8")

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        if self.path == "/report":
            self._handle_report()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Unexpected endpoint")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/launch":
            duration = getattr(self.server, "page_duration", 60.0)
            self._handle_launch(parsed.query, duration)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unexpected endpoint")

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - matching BaseHTTPRequestHandler
        return  # Silence the built-in HTTP server logging


def start_result_server(store: ResultStore) -> ThreadingHTTPServer:
    handler_class = type(
        "ResultHandler",
        (_ResultRequestHandler,),
        {"store": store},
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    server.page_duration = 60.0
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def parse_arguments(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch LinkedIn company pages so the Chrome extension can follow them.",
    )

    parser.add_argument("urls", nargs="*", help="LinkedIn company URLs to follow")
    parser.add_argument("--input-file", help="Path to a file containing company URLs (one per line)")
    parser.add_argument("--queue-file", help="Path to a persistent queue file (one URL per line)")
    parser.add_argument("--queue-output", help="CSV file that receives incremental processing results")
    parser.add_argument("--callback-timeout", type=float, default=90, help="Seconds to wait for the extension to report a result")
    parser.add_argument("--delay-between", type=float, default=90, help="Delay between URL launches in seconds")
    parser.add_argument("--page-duration", type=float, default=60, help="Seconds to keep each tab open before the extension is allowed to close it")
    parser.add_argument("--daily-limit", type=int, default=100, help="Maximum number of URLs to process per calendar day (set to 0 to disable)")
    parser.add_argument("--output-format", choices=("table", "json"), default="table", help="Output results as a table or JSON array")
    parser.add_argument("--output-path", help="Optional path to save the rendered results")

    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_arguments(argv)

    if args.queue_file:
        queue_urls = read_queue_file(args.queue_file)
        urls = list(queue_urls)
    else:
        queue_urls = None
        urls = parse_urls(args)

    quota_tracker = DailyQuotaTracker()

    if args.daily_limit > 0:
        allowed = quota_tracker.remaining(args.daily_limit)
        if allowed <= 0:
            print(f"Daily limit of {args.daily_limit} URLs already reached today. Add new URLs tomorrow.")
            return 0
        if len(urls) > allowed:
            print(f"Daily limit allows processing {allowed} more URLs today; remaining entries stay in the queue.")
            if args.queue_file and queue_urls is not None:
                urls = queue_urls[:allowed]
            else:
                urls = urls[:allowed]

    result_store = ResultStore()
    server = start_result_server(result_store)
    server.page_duration = max(float(args.page_duration), 0.0)
    port = server.server_address[1]

    results: List[FollowResult] = []
    task_url_map: dict[str, str] = {}

    try:
        for index, url in enumerate(urls, start=1):
            try:
                normalised_url = normalise_company_url(url)
            except ValueError as exc:
                follow_result = FollowResult(url=url, status="error", reason=str(exc))
                results.append(follow_result)
                if args.queue_output:
                    append_incremental_result(args.queue_output, follow_result)
                continue

            task_id = uuid.uuid4().hex
            task_url_map[task_id] = normalised_url
            launcher_url = (
                f"http://127.0.0.1:{port}/launch?"
                f"task_id={task_id}&url={quote(normalised_url, safe='')}&duration={args.page_duration}"
            )
            webbrowser.open_new_tab(launcher_url)

            payload = result_store.wait_for(task_id, args.callback_timeout)
            if payload is None:
                follow_result = FollowResult(
                    url=normalised_url,
                    status="error",
                    reason="Chrome extension did not report a result within the timeout window.",
                )
            else:
                reason = payload.get("reason") or None
                follow_result = FollowResult(
                    url=normalised_url,
                    status=str(payload.get("status", "error")),
                    reason=reason if reason else None,
                )

            results.append(follow_result)

            if args.queue_output:
                append_incremental_result(args.queue_output, follow_result)

            quota_tracker.record(args.daily_limit)

            if args.queue_file and queue_urls is not None:
                remaining = queue_urls[index:]
                write_queue_file(args.queue_file, remaining)

            if index < len(urls) and args.delay_between > 0:
                time.sleep(args.delay_between)
    finally:
        server.shutdown()
        server.server_close()

    render_results(results, args.output_format, args.output_path)
    return compute_exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
