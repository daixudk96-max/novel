from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

_AI_CLICHE_PATTERNS = (
    r"\bas an ai language model\b",
    r"\bit is important to note\b",
    r"\bin conclusion\b",
    r"\bdelve into\b",
)
_TIME_MARKER_PATTERN = re.compile(r"\b(?:Day\s+\d+|Morning|Afternoon|Evening|Night)\b")
_TITLE_CASE_PATTERN = re.compile(r"(?<!\w)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?!\w)")
_IGNORE_TITLE_CASE = frozenset(
    {
        "A",
        "An",
        "The",
        "And",
        "But",
        "Or",
        "If",
        "Then",
        "When",
        "While",
        "Before",
        "After",
        "At",
        "In",
        "On",
        "To",
        "From",
        "Of",
        "For",
        "By",
        "With",
        "Without",
        "He",
        "She",
        "They",
        "We",
        "I",
        "It",
        "His",
        "Her",
        "Their",
        "Our",
        "My",
        "Day",
        "Morning",
        "Afternoon",
        "Evening",
        "Night",
    }
)
_KNOWN_TIME_KEYS = ("time_marker", "time", "day")


@dataclass(frozen=True, slots=True)
class PostcheckIssue:
    rule: str
    severity: str
    message: str
    location: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PostcheckResult:
    passed: bool
    issues: list[PostcheckIssue]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class PostcheckRunner:
    def run(self, state, chapter_number: int, chapter_text: str) -> PostcheckResult:
        if type(chapter_number) is not int:
            raise ValueError("chapter_number must be an integer")
        if not isinstance(chapter_text, str):
            raise ValueError("chapter_text must be a string")

        issues: list[PostcheckIssue] = []
        world_entities = self._world_entities(state)

        if not world_entities:
            issues.append(
                self._make_issue(
                    rule="world-model-missing",
                    severity="minor",
                    message="world model is empty; entity-based checks were skipped",
                    start=0,
                    end=0,
                    excerpt="",
                )
            )
        else:
            issues.extend(self._detect_hidden_entities(world_entities, chapter_text))
            issues.extend(self._detect_unregistered_names(world_entities, chapter_text))

        issues.extend(self._detect_timeline_jump(state, chapter_number, chapter_text))
        issues.extend(self._detect_ai_cliches(chapter_text))
        ordered_issues = sorted(issues, key=self._issue_sort_key)
        return PostcheckResult(
            passed=all(issue.severity == "minor" for issue in ordered_issues),
            issues=ordered_issues,
        )

    def _world_entities(self, state) -> list[dict]:
        data = getattr(state, "data", state)
        if not isinstance(data, dict):
            return []
        world = data.get("world")
        if not isinstance(world, dict):
            return []
        entities = world.get("entities")
        if not isinstance(entities, list):
            return []
        return [entity for entity in entities if isinstance(entity, dict)]

    def _detect_hidden_entities(
        self, entities: list[dict], chapter_text: str
    ) -> list[PostcheckIssue]:
        issues: list[PostcheckIssue] = []
        for entity in entities:
            if entity.get("visibility") != "hidden":
                continue
            match = self._find_entity_match(chapter_text, entity.get("name"))
            if match is None:
                continue
            issues.append(
                self._make_issue(
                    rule="hidden-entity-appearance",
                    severity="blocker",
                    message=f"hidden entity '{entity['name']}' appears in chapter text",
                    start=match.start(),
                    end=match.end(),
                    excerpt=match.group(0),
                )
            )
        return issues

    def _detect_unregistered_names(
        self, entities: list[dict], chapter_text: str
    ) -> list[PostcheckIssue]:
        registered_names = {
            entity["name"]
            for entity in entities
            if entity.get("type") in {"character", "location"}
            and isinstance(entity.get("name"), str)
        }
        known_names = {name.casefold() for name in registered_names}
        issues: list[PostcheckIssue] = []
        seen: set[str] = set()

        for match in _TITLE_CASE_PATTERN.finditer(chapter_text):
            candidate = match.group(1).strip()
            if self._is_sentence_initial_single_word(match, candidate, chapter_text):
                continue
            if candidate in _IGNORE_TITLE_CASE:
                continue
            if candidate.casefold() in known_names:
                continue
            if candidate.casefold() in seen:
                continue
            seen.add(candidate.casefold())
            issues.append(
                self._make_issue(
                    rule="unregistered-name",
                    severity="blocker",
                    message=f"unregistered character or location '{candidate}' found in chapter text",
                    start=match.start(1),
                    end=match.end(1),
                    excerpt=candidate,
                )
            )
        return issues

    def _detect_timeline_jump(
        self, state, chapter_number: int, chapter_text: str
    ) -> list[PostcheckIssue]:
        timeline_markers = self._chapter_timeline_markers(state, chapter_number)
        if not timeline_markers:
            return []

        issues: list[PostcheckIssue] = []
        expected = {marker.casefold() for marker in timeline_markers}
        seen: set[str] = set()
        for match in _TIME_MARKER_PATTERN.finditer(chapter_text):
            marker = match.group(0)
            folded = marker.casefold()
            if folded in expected or folded in seen:
                continue
            seen.add(folded)
            issues.append(
                self._make_issue(
                    rule="timeline-jump",
                    severity="major",
                    message=f"chapter time marker '{marker}' conflicts with timeline marker '{timeline_markers[0]}'",
                    start=match.start(),
                    end=match.end(),
                    excerpt=marker,
                )
            )
        return issues

    def _chapter_timeline_markers(self, state, chapter_number: int) -> list[str]:
        data = getattr(state, "data", state)
        if not isinstance(data, dict):
            return []
        timeline = data.get("timeline")
        if not isinstance(timeline, dict):
            return []
        events = timeline.get("events")
        if not isinstance(events, list):
            return []

        markers: list[str] = []
        for event in events:
            if not isinstance(event, dict):
                continue
            if event.get("chapter") != chapter_number:
                continue
            for key in _KNOWN_TIME_KEYS:
                value = event.get(key)
                if isinstance(value, str) and value.strip():
                    markers.append(value.strip())
                    break
                if type(value) is int:
                    markers.append(f"Day {value}")
                    break
        return markers

    def _detect_ai_cliches(self, chapter_text: str) -> list[PostcheckIssue]:
        issues: list[PostcheckIssue] = []
        for pattern in _AI_CLICHE_PATTERNS:
            match = re.search(pattern, chapter_text, flags=re.IGNORECASE)
            if match is None:
                continue
            issues.append(
                self._make_issue(
                    rule="ai-cliche",
                    severity="minor",
                    message=f"AI-style stock phrase detected: '{match.group(0)}'",
                    start=match.start(),
                    end=match.end(),
                    excerpt=match.group(0),
                )
            )
            break
        return issues

    def _find_entity_match(self, chapter_text: str, entity_name: object):
        if not isinstance(entity_name, str) or not entity_name.strip():
            return None
        pattern = rf"(?<!\w){re.escape(entity_name.strip())}(?!\w)"
        return re.search(pattern, chapter_text, flags=re.IGNORECASE)

    def _is_sentence_initial_single_word(
        self, match: re.Match[str], candidate: str, chapter_text: str
    ) -> bool:
        if " " in candidate:
            return False
        start = match.start(1)
        if start == 0:
            return True
        prefix = chapter_text[:start].rstrip()
        return prefix.endswith((".", "!", "?"))

    def _make_issue(
        self,
        *,
        rule: str,
        severity: str,
        message: str,
        start: int,
        end: int,
        excerpt: str,
    ) -> PostcheckIssue:
        return PostcheckIssue(
            rule=rule,
            severity=severity,
            message=message,
            location={
                "line": 1,
                "start": start,
                "end": end,
                "excerpt": excerpt,
            },
        )

    def _issue_sort_key(self, issue: PostcheckIssue) -> tuple[int, int, str, str]:
        return (
            issue.location["start"],
            issue.location["end"],
            issue.rule,
            issue.severity,
        )


__all__ = ["PostcheckIssue", "PostcheckResult", "PostcheckRunner"]
