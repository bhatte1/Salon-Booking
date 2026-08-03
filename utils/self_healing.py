from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
except Exception:  # pragma: no cover
    PlaywrightTimeoutError = TimeoutError


LOGGER = logging.getLogger(__name__)


class SelfHealingLocator:
    def __init__(
        self,
        *,
        timeout_ms: int = 3000,
        retry_attempts: int = 2,
        retry_delay_seconds: float = 0.4,
        report_path: str | Path = "reports/self_healing_report.json",
    ) -> None:
        self.timeout_ms = timeout_ms
        self.retry_attempts = retry_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.report_path = Path(report_path)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)

    def find_with_healing(
        self,
        page: "Page",
        primary_locator: str | "Locator",
        element_name: str = "",
    ) -> "Locator":
        locator_name = element_name or self._stringify_locator(primary_locator)
        LOGGER.info("Resolving locator for '%s'", locator_name)

        primary = self._as_locator(page, primary_locator)
        for attempt in range(1, self.retry_attempts + 1):
            try:
                primary.wait_for(state="visible", timeout=self.timeout_ms)
                LOGGER.info(
                    "Primary locator resolved for '%s' on attempt %s",
                    locator_name,
                    attempt,
                )
                return primary
            except PlaywrightTimeoutError:
                LOGGER.warning(
                    "Primary locator failed for '%s' on attempt %s/%s",
                    locator_name,
                    attempt,
                    self.retry_attempts,
                )
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay_seconds)

        locator_candidates = self.generate_fallback_locators(primary_locator)
        healed_locator, healed_selector = self.try_fallback_locators(page, locator_candidates)
        self.log_healing_success(
            old_locator=self._stringify_locator(primary_locator),
            new_locator=healed_selector,
        )
        LOGGER.info(
            "Self-healing succeeded for '%s': '%s' -> '%s'",
            locator_name,
            self._stringify_locator(primary_locator),
            healed_selector,
        )
        return healed_locator

    def generate_fallback_locators(self, primary_locator: str | "Locator") -> list[dict[str, Any]]:
        locator_string = self._stringify_locator(primary_locator)
        metadata = self._extract_locator_metadata(locator_string)
        candidates: list[dict[str, Any]] = []
        seen: set[str] = set()

        def add_candidate(strategy: str, value: str) -> None:
            normalized = f"{strategy}:{value.strip()}"
            if not value.strip() or normalized in seen:
                return
            seen.add(normalized)
            candidates.append({"strategy": strategy, "value": value.strip()})

        for text_value in metadata["texts"]:
            add_candidate("text", text_value)
            add_candidate("role", text_value)
            add_candidate("partial_attribute", text_value)

        for placeholder_value in metadata["placeholders"]:
            add_candidate("placeholder", placeholder_value)
            add_candidate("partial_attribute", placeholder_value)

        for aria_label in metadata["aria_labels"]:
            add_candidate("aria_label", aria_label)
            add_candidate("role", aria_label)
            add_candidate("partial_attribute", aria_label)

        for role_name in metadata["roles"]:
            add_candidate("role_only", role_name)

        for token in metadata["attribute_tokens"]:
            add_candidate("partial_attribute", token)

        for candidate in self._build_dom_similarity_candidates(metadata):
            add_candidate("css", candidate)

        return candidates

    def try_fallback_locators(
        self,
        page: "Page",
        locator_candidates: list[dict[str, Any]],
    ) -> tuple["Locator", str]:
        last_error: Exception | None = None

        for candidate in locator_candidates:
            candidate_locator = self._build_locator_from_candidate(page, candidate)
            candidate_label = self._candidate_to_string(candidate)
            LOGGER.info("Trying fallback locator candidate: %s", candidate_label)

            try:
                candidate_locator.wait_for(state="visible", timeout=self.timeout_ms)
                return candidate_locator, candidate_label
            except PlaywrightTimeoutError as exc:
                last_error = exc
                LOGGER.debug("Fallback candidate timed out: %s", candidate_label)
            except Exception as exc:  # pragma: no cover
                last_error = exc
                LOGGER.debug("Fallback candidate failed: %s", candidate_label)

        raise RuntimeError(
            "Self-healing failed. No fallback locators matched."
        ) from last_error

    def log_healing_success(self, old_locator: str, new_locator: str) -> None:
        entries: list[dict[str, Any]] = []
        if self.report_path.exists():
            try:
                entries = json.loads(self.report_path.read_text(encoding="utf-8"))
                if not isinstance(entries, list):
                    entries = []
            except json.JSONDecodeError:
                entries = []

        entries.append(
            {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "old_locator": old_locator,
                "new_locator": new_locator,
                "status": "healed",
            }
        )
        self.report_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    def _as_locator(self, page: "Page", primary_locator: str | "Locator") -> "Locator":
        if hasattr(primary_locator, "wait_for"):
            return primary_locator  # type: ignore[return-value]
        return page.locator(str(primary_locator)).first

    def _stringify_locator(self, primary_locator: str | "Locator") -> str:
        if isinstance(primary_locator, str):
            return primary_locator
        return str(primary_locator)

    def _candidate_to_string(self, candidate: dict[str, Any]) -> str:
        return f"{candidate['strategy']}={candidate['value']}"

    def _build_locator_from_candidate(self, page: "Page", candidate: dict[str, Any]) -> "Locator":
        strategy = candidate["strategy"]
        value = candidate["value"]

        if strategy == "text":
            return page.get_by_text(value, exact=False).first
        if strategy == "placeholder":
            return page.get_by_placeholder(value, exact=False).first
        if strategy == "aria_label":
            return page.get_by_label(value, exact=False).first
        if strategy == "role":
            return self._role_locator(page, value)
        if strategy == "role_only":
            return self._role_only_locator(page, value)
        if strategy == "partial_attribute":
            return page.locator(
                ",".join(
                    [
                        f'[id*="{value}"]',
                        f'[name*="{value}"]',
                        f'[class*="{value}"]',
                        f'[data-testid*="{value}"]',
                        f'[placeholder*="{value}"]',
                        f'[aria-label*="{value}"]',
                    ]
                )
            ).first
        if strategy == "css":
            return page.locator(value).first
        return page.locator(value).first

    def _role_locator(self, page: "Page", value: str) -> "Locator":
        lowered = value.lower()
        role_pairs = [
            ("button", page.get_by_role("button", name=value, exact=False).first),
            ("link", page.get_by_role("link", name=value, exact=False).first),
            ("textbox", page.get_by_role("textbox", name=value, exact=False).first),
            ("heading", page.get_by_role("heading", name=value, exact=False).first),
            ("checkbox", page.get_by_role("checkbox", name=value, exact=False).first),
            ("combobox", page.get_by_role("combobox", name=value, exact=False).first),
        ]
        for role_name, locator in role_pairs:
            if role_name in lowered:
                return locator
        return page.get_by_role("button", name=value, exact=False).first

    def _role_only_locator(self, page: "Page", value: str) -> "Locator":
        role_name = value.lower()
        supported_roles = {
            "button",
            "link",
            "textbox",
            "heading",
            "checkbox",
            "combobox",
            "dialog",
            "listitem",
        }
        if role_name in supported_roles:
            return page.get_by_role(role_name).first
        return page.locator(role_name).first

    def _extract_locator_metadata(self, locator_string: str) -> dict[str, list[str]]:
        texts: list[str] = []
        placeholders: list[str] = []
        aria_labels: list[str] = []
        roles: list[str] = []
        attribute_tokens: list[str] = []

        quoted_values = re.findall(r'["\']([^"\']{2,})["\']', locator_string)
        for value in quoted_values:
            cleaned = value.strip()
            if cleaned:
                texts.append(cleaned)

        placeholder_matches = re.findall(r"placeholder(?:\*?=|\", name=)([^,\]\)]+)", locator_string)
        aria_matches = re.findall(r"aria-label(?:\*?=|\", name=)([^,\]\)]+)", locator_string)
        role_matches = re.findall(r"get_by_role\((?:\"|')([^\"']+)", locator_string)

        for match in placeholder_matches:
            placeholders.append(match.strip(" '\""))
        for match in aria_matches:
            aria_labels.append(match.strip(" '\""))
        for match in role_matches:
            roles.append(match.strip())

        for token in re.split(r"[^a-zA-Z0-9_-]+", locator_string):
            cleaned = token.strip()
            if len(cleaned) >= 4 and cleaned.lower() not in {
                "page",
                "locator",
                "get_by_text",
                "get_by_role",
                "get_by_label",
                "get_by_placeholder",
                "xpath",
                "css",
            }:
                attribute_tokens.append(cleaned)

        return {
            "texts": self._dedupe(texts),
            "placeholders": self._dedupe(placeholders),
            "aria_labels": self._dedupe(aria_labels),
            "roles": self._dedupe(roles),
            "attribute_tokens": self._dedupe(attribute_tokens),
        }

    def _build_dom_similarity_candidates(self, metadata: dict[str, list[str]]) -> list[str]:
        candidates: list[str] = []
        tokens = metadata["texts"] + metadata["placeholders"] + metadata["aria_labels"] + metadata["attribute_tokens"]

        for token in tokens[:6]:
            safe = token.replace('"', '\\"')
            candidates.extend(
                [
                    f'[data-testid*="{safe}"]',
                    f'[id*="{safe}"]',
                    f'[name*="{safe}"]',
                    f'[class*="{safe}"]',
                    f'[aria-label*="{safe}"]',
                    f'[placeholder*="{safe}"]',
                    f'text={safe}',
                ]
            )

        return self._dedupe(candidates)

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            normalized = value.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped
