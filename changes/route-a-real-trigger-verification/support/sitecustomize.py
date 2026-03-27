from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from novel_runtime.llm import provider as _provider


_ORIGINAL_BUILD_ROUTE_A_PROVIDER = _provider.build_route_a_provider
_FAKE_PROVIDER_ENV = "NOVEL_REAL_VERIFY_FAKE_PROVIDER"
_DRAFT_TEXT_ENV = "NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE"
_CALL_LOG_ENV = "NOVEL_REAL_VERIFY_PROVIDER_CALL_LOG"
_RETRY_SEQUENCE_ENV = "NOVEL_REAL_VERIFY_RETRY_SEQUENCE"


class APIConnectionError(Exception):
    pass


class APITimeoutError(Exception):
    pass


class InternalServerError(Exception):
    pass


class RateLimitError(Exception):
    pass


_RETRYABLE_EXCEPTIONS = {
    "APIConnectionError": APIConnectionError,
    "APITimeoutError": APITimeoutError,
    "InternalServerError": InternalServerError,
    "RateLimitError": RateLimitError,
}


@dataclass(slots=True)
class _FakeRouteAProvider:
    config: _provider.RouteAProviderConfig
    draft_text_file: Path
    call_log_path: Path
    retry_sequence: tuple[str, ...] = ()
    attempts: list[dict[str, object]] = field(default_factory=list)

    def draft(self, *, prompt: str, temperature: float) -> str:
        attempt_number = len(self.attempts) + 1
        outcome = (
            self.retry_sequence[attempt_number - 1]
            if attempt_number <= len(self.retry_sequence)
            else "success"
        )
        attempt_record: dict[str, object] = {
            "attempt": attempt_number,
            "outcome": outcome,
        }

        if outcome != "success":
            exc = _build_retryable_exception(outcome, attempt_number)
            attempt_record["raised"] = type(exc).__name__
            attempt_record["message"] = str(exc)
            self.attempts.append(attempt_record)
            self._write_call_log(prompt=prompt, temperature=temperature)
            raise exc

        attempt_record["result"] = "success"
        self.attempts.append(attempt_record)
        self._write_call_log(prompt=prompt, temperature=temperature)
        return self.draft_text_file.read_text(encoding="utf-8")

    def _write_call_log(self, *, prompt: str, temperature: float) -> None:
        self.call_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.call_log_path.write_text(
            json.dumps(
                {
                    "prompt": prompt,
                    "temperature": temperature,
                    "attempt_count": len(self.attempts),
                    "attempts": self.attempts,
                },
                indent=2,
            ),
            encoding="utf-8",
        )


def _patched_build_route_a_provider(
    env: Mapping[str, str] | None = None,
    *,
    provider_factory=_provider.OpenAIRouteAProvider,
):
    source = os.environ if env is None else env
    if source.get(_FAKE_PROVIDER_ENV) != "1":
        return _ORIGINAL_BUILD_ROUTE_A_PROVIDER(env, provider_factory=provider_factory)

    config = _provider.resolve_route_a_provider_config(env)
    draft_text_file = _required_path(source, _DRAFT_TEXT_ENV)
    call_log_path = _required_path(source, _CALL_LOG_ENV)
    retry_sequence = _parse_retry_sequence(source)
    return _FakeRouteAProvider(
        config=config,
        draft_text_file=draft_text_file,
        call_log_path=call_log_path,
        retry_sequence=retry_sequence,
    )


def _required_path(source: Mapping[str, str], name: str) -> Path:
    value = source.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required when {_FAKE_PROVIDER_ENV}=1")
    return Path(value.strip())


def _parse_retry_sequence(source: Mapping[str, str]) -> tuple[str, ...]:
    raw = source.get(_RETRY_SEQUENCE_ENV, "")
    if not isinstance(raw, str) or not raw.strip():
        return ()

    sequence = tuple(token.strip() for token in raw.split(",") if token.strip())
    invalid = [
        token
        for token in sequence
        if token != "success" and token not in _RETRYABLE_EXCEPTIONS
    ]
    if invalid:
        valid = ", ".join(["success", *_RETRYABLE_EXCEPTIONS])
        raise ValueError(
            f"{_RETRY_SEQUENCE_ENV} contains unsupported outcomes: {', '.join(invalid)}; valid values: {valid}"
        )
    return sequence


def _build_retryable_exception(name: str, attempt_number: int) -> Exception:
    exc_type = _RETRYABLE_EXCEPTIONS[name]
    return exc_type(f"simulated {name} on attempt {attempt_number}")


_provider.build_route_a_provider = _patched_build_route_a_provider
