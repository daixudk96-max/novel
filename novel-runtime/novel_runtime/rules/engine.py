from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOWED_SEVERITIES = frozenset({"blocker", "major", "minor"})
BUILTIN_UNIVERSAL_RULES = [
    {
        "id": "abrupt-shift",
        "name": "Abrupt transition detector",
        "pattern": r"\bsuddenly\b",
        "severity": "minor",
        "message": "Watch for abrupt transitions such as 'suddenly'.",
    },
    {
        "id": "filter-phrase",
        "name": "Filter phrase detector",
        "pattern": r"\b(she|he|they) (saw|heard|felt|noticed)\b",
        "severity": "minor",
        "message": "Filter phrases can weaken immediacy.",
    },
    {
        "id": "cliche-breath",
        "name": "Breath cliché detector",
        "pattern": r"\blet out a breath\b",
        "severity": "minor",
        "message": "Review stock body-language phrasing.",
    },
    {
        "id": "shrug-cliche",
        "name": "Shrug cliché detector",
        "pattern": r"\bshrugged\b",
        "severity": "minor",
        "message": "Check whether shrugging is overused.",
    },
    {
        "id": "soft-dialogue-tag",
        "name": "Soft dialogue tag detector",
        "pattern": r"\bsaid softly\b",
        "severity": "minor",
        "message": "Prefer stronger beats over soft dialogue tags.",
    },
]


class InvalidRuleError(ValueError):
    pass


@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    pattern: str
    severity: str
    message: str


@dataclass(frozen=True)
class RuleViolation:
    rule_id: str
    name: str
    severity: str
    message: str
    pattern: str


class RulesEngine:
    def __init__(self) -> None:
        self.rules: list[Rule] = []

    def load_rules(
        self,
        universal_path: str | Path | None,
        genre_path: str | Path | None = None,
        book_path: str | Path | None = None,
    ) -> list[Rule]:
        merged_rules = self._merge_rules(
            self._parse_rules(
                BUILTIN_UNIVERSAL_RULES, source="builtin universal rules"
            ),
            self._load_rules_file(universal_path, required=False),
            self._load_rules_file(genre_path, required=False),
            self._load_rules_file(book_path, required=False),
        )
        self.rules = list(merged_rules.values())
        return self.rules

    def evaluate(self, state: dict[str, Any], chapter_text: str) -> list[RuleViolation]:
        if not isinstance(state, dict):
            raise TypeError("state must be a dict")
        if not isinstance(chapter_text, str):
            raise TypeError("chapter_text must be a string")
        if not self.rules:
            self.load_rules(None)

        violations: list[RuleViolation] = []
        for rule in self.rules:
            if re.search(rule.pattern, chapter_text, flags=re.IGNORECASE):
                violations.append(
                    RuleViolation(
                        rule_id=rule.id,
                        name=rule.name,
                        severity=rule.severity,
                        message=rule.message,
                        pattern=rule.pattern,
                    )
                )
        return violations

    def _load_rules_file(
        self, path: str | Path | None, *, required: bool = False
    ) -> list[Rule]:
        if path is None:
            return []

        rule_path = Path(path)
        if not rule_path.exists():
            if required:
                raise InvalidRuleError(f"rule file not found: {rule_path}")
            return []

        try:
            payload = json.loads(rule_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise InvalidRuleError(
                f"invalid rule JSON in {rule_path}: {exc.msg}"
            ) from exc

        return self._parse_rules(payload, source=str(rule_path))

    def _parse_rules(self, payload: object, *, source: str) -> list[Rule]:
        if not isinstance(payload, list):
            raise InvalidRuleError(f"rules in {source} must be a list")

        parsed_rules: list[Rule] = []
        for index, entry in enumerate(payload):
            path = f"{source}[{index}]"
            if not isinstance(entry, dict):
                raise InvalidRuleError(f"rule {path} must be an object")

            missing_fields = [
                field
                for field in ("id", "name", "pattern", "severity", "message")
                if field not in entry
            ]
            if missing_fields:
                raise InvalidRuleError(
                    f"rule {path} missing required field(s): {', '.join(missing_fields)}"
                )

            for field in ("id", "name", "pattern", "severity", "message"):
                if not isinstance(entry[field], str) or not entry[field].strip():
                    raise InvalidRuleError(
                        f"rule {path}.{field} must be a non-empty string"
                    )

            if entry["severity"] not in ALLOWED_SEVERITIES:
                allowed = ", ".join(sorted(ALLOWED_SEVERITIES))
                raise InvalidRuleError(
                    f"rule {path}.severity must be one of: {allowed}"
                )

            try:
                re.compile(entry["pattern"])
            except re.error as exc:
                raise InvalidRuleError(
                    f"rule {path}.pattern is invalid regex: {exc}"
                ) from exc

            parsed_rules.append(
                Rule(
                    id=entry["id"],
                    name=entry["name"],
                    pattern=entry["pattern"],
                    severity=entry["severity"],
                    message=entry["message"],
                )
            )
        return parsed_rules

    def _merge_rules(self, *rule_layers: list[Rule]) -> dict[str, Rule]:
        merged_rules: dict[str, Rule] = {}
        for layer in rule_layers:
            for rule in layer:
                merged_rules[rule.id] = rule
        return merged_rules
