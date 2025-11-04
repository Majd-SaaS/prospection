"""Utilities for automating LinkedIn company follow actions.

This module provides building blocks that are reused by both the CLI script
and the test-suite.  The utilities are intentionally written so that the core
decision making logic (e.g. determining whether a button represents the
"Follow" or "Following" state) can be unit-tested without launching a browser.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Set

try:  # pragma: no cover - fallback used only when Selenium is absent (unit tests)
    from selenium.webdriver.common.by import By
except ModuleNotFoundError:  # pragma: no cover
    class _FallbackBy:
        TAG_NAME = "tag name"

    By = _FallbackBy()


# LinkedIn's English UI primarily toggles between "Follow" and "Following".
# Some company pages use "Follow company" as the call-to-action.  The sets
# below are normalised to lowercase to simplify comparisons.
FOLLOW_KEYWORDS: Set[str] = {"follow", "follow company"}
FOLLOWING_KEYWORDS: Set[str] = {"following"}


@dataclass(frozen=True)
class ButtonSnapshot:
    """A serialisable snapshot of a follow button's visible state."""

    texts: Set[str]
    aria_label: str
    aria_pressed: str
    disabled: bool


def normalise_company_url(url: str) -> str:
    """Ensure that a LinkedIn company URL always includes a protocol."""

    if not url:
        raise ValueError("The URL provided for a company page is empty.")

    trimmed = url.strip()
    if not trimmed:
        raise ValueError("The URL provided for a company page contains only whitespace.")

    if trimmed.startswith(("http://", "https://")):
        return trimmed

    # LinkedIn company pages only support HTTPS, so default to https:// when the
    # caller omits the protocol.
    return f"https://{trimmed.lstrip('/')}"


def collect_button_texts(button) -> Set[str]:  # type: ignore[no-untyped-def]
    """Collect visible texts for a Selenium WebElement button.

    Selenium's WebElement exposes ``text`` for the element as well as nested
    children.  We inspect both the button and its ``span`` descendants to ensure
    that we capture text rendered in nested wrappers.
    """

    texts: Set[str] = set()

    def _normalise(text: Optional[str]) -> Optional[str]:
        if not text:
            return None
        cleaned = text.strip().lower()
        return cleaned or None

    primary_text = _normalise(getattr(button, "text", None))
    if primary_text:
        texts.add(primary_text)

    try:
        for span in button.find_elements(By.TAG_NAME, "span"):
            span_text = _normalise(getattr(span, "text", None))
            if span_text:
                texts.add(span_text)
    except Exception:  # pragma: no cover - Selenium errors are tolerated here.
        pass

    return texts


def snapshot_button(button) -> ButtonSnapshot:  # type: ignore[no-untyped-def]
    """Create a :class:`ButtonSnapshot` from a Selenium WebElement."""

    texts = collect_button_texts(button)
    aria_label = (button.get_attribute("aria-label") or "").strip().lower()
    aria_pressed = (button.get_attribute("aria-pressed") or "").strip().lower()

    # ``disabled`` can be represented either as a boolean attribute or a string
    # equal to "true".  ``get_attribute`` normalises boolean attributes to the
    # string ``"true"`` when present.
    disabled_attribute = button.get_attribute("disabled")
    disabled = bool(disabled_attribute and disabled_attribute != "false")

    return ButtonSnapshot(
        texts=texts,
        aria_label=aria_label,
        aria_pressed=aria_pressed,
        disabled=disabled,
    )


def evaluate_button_state(snapshot: ButtonSnapshot) -> str:
    """Classify the snapshot as ``follow``, ``already followed`` or ``unknown``.

    The caller can use the resulting label to decide whether to click the button
    or to skip it.  ``unknown`` indicates that the element does not match the
    expected LinkedIn semantics and should be treated as an error.
    """

    if snapshot.disabled:
        return "unknown"

    if snapshot.aria_pressed == "true":
        return "already followed"

    if any(keyword in snapshot.aria_label for keyword in FOLLOWING_KEYWORDS):
        return "already followed"

    if any(keyword in snapshot.texts for keyword in FOLLOWING_KEYWORDS):
        return "already followed"

    has_follow_keyword = any(keyword in snapshot.texts for keyword in FOLLOW_KEYWORDS)
    has_follow_label = any(keyword in snapshot.aria_label for keyword in FOLLOW_KEYWORDS)

    aria_false = snapshot.aria_pressed in {"", "false"}

    if (has_follow_keyword or has_follow_label) and aria_false:
        return "follow"

    # LinkedIn sometimes omits the aria attributes but keeps the correct button
    # text.  When that happens we still consider the button actionable.
    if has_follow_keyword:
        return "follow"

    return "unknown"


def merge_unique_urls(sequences: Sequence[Iterable[str]]) -> Sequence[str]:
    """Merge URLs from several iterables while keeping the first occurrence order."""

    seen: Set[str] = set()
    ordered: list[str] = []

    for sequence in sequences:
        for raw_url in sequence:
            url = raw_url.strip()
            if not url or url in seen:
                continue
            ordered.append(url)
            seen.add(url)

    return ordered

