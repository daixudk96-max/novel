from __future__ import annotations

import importlib
import math
from typing import Any

import pytest


class _FakeProvider:
    def __init__(self, output: str = "Generated draft body.") -> None:
        self.output = output
        self.calls: list[dict[str, object]] = []

    def draft(self, *, prompt: str, temperature: float) -> str:
        self.calls.append({"prompt": prompt, "temperature": temperature})
        return self.output


class _ExplodingProvider:
    def draft(self, *, prompt: str, temperature: float) -> str:
        raise RuntimeError("provider exploded")


class _FakeOpenAIClient:
    def __init__(self, content: str = "OpenAI-backed chapter body.") -> None:
        self.content = content
        self.calls: list[dict[str, object]] = []
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _FakeCompletionResponse(self.content)


class _FakeCompletionResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeCompletionChoice(content)]


class _FakeCompletionChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeCompletionMessage(content)


class _FakeCompletionMessage:
    def __init__(self, content: str) -> None:
        self.content = content


RateLimitError = type("RateLimitError", (Exception,), {"status_code": 429})
APIConnectionError = type("APIConnectionError", (Exception,), {})
InternalServerError = type("InternalServerError", (Exception,), {"status_code": 503})
AuthenticationError = type("AuthenticationError", (Exception,), {"status_code": 401})
UnsupportedProviderError = type("UnsupportedProviderError", (Exception,), {})


class _FakeProviderOperation:
    def __init__(self, *results: object) -> None:
        self._results = list(results)
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        result = self._results.pop(0)
        if isinstance(result, BaseException):
            raise result
        assert isinstance(result, str)
        return result


def test_draft_returns_structured_chapter_result() -> None:
    drafter_module = _load_drafter_module()
    provider = _FakeProvider("Chapter body from provider.")

    result = drafter_module.ChapterDrafter(provider=provider).draft(_build_state(), 1)

    assert result.chapter == 1
    assert result.title == "Chapter 1"
    assert result.status == "draft"
    assert result.summary == "Mira takes the next step."
    assert result.content == "Chapter body from provider."
    assert provider.calls == [
        {
            "prompt": "Draft Chapter 1 about Mira. Summary: Mira takes the next step.",
            "temperature": 1.0,
        }
    ]


def test_draft_requires_active_world_entity() -> None:
    drafter_module = _load_drafter_module()

    with pytest.raises(
        ValueError, match="chapter 1 draft requires at least one active world entity"
    ):
        drafter_module.ChapterDrafter().draft(
            _load_canonical_state_class().create_empty("Example Novel", "fantasy"),
            1,
        )


def test_draft_failure_requires_integer_chapter_number() -> None:
    drafter_module = _load_drafter_module()

    with pytest.raises(ValueError, match="chapter_number must be an integer"):
        drafter_module.ChapterDrafter().draft(_build_state(), "1")


def test_draft_failure_ignores_active_entities_with_blank_names() -> None:
    drafter_module = _load_drafter_module()
    state = _load_canonical_state_class().create_empty("Example Novel", "fantasy")
    state.data["world"]["entities"].extend(
        [
            {
                "id": "entity-1",
                "name": "   ",
                "type": "character",
                "attributes": {"role": "lead"},
                "visibility": "active",
            },
            {
                "id": "entity-2",
                "name": "Mira",
                "type": "character",
                "attributes": {"role": "lead"},
                "visibility": "hidden",
            },
        ]
    )

    with pytest.raises(
        ValueError, match="chapter 2 draft requires at least one active world entity"
    ):
        drafter_module.ChapterDrafter().draft(state, 2)


def test_draft_loads_route_a_provider_when_not_injected() -> None:
    drafter_module = _load_drafter_module()
    provider = _FakeProvider("Generated from resolved provider.")

    result = drafter_module.ChapterDrafter(
        provider_factory=lambda: provider,
        temperature=0.7,
    ).draft(_build_state(), 3)

    assert result.content == "Generated from resolved provider."
    assert provider.calls == [
        {
            "prompt": "Draft Chapter 3 about Mira. Summary: Mira takes the next step.",
            "temperature": 0.7,
        }
    ]


def test_draft_happy_path_can_use_env_backed_openai_provider_without_network() -> None:
    drafter_module = _load_drafter_module()
    provider_module = _load_provider_module()
    client = _FakeOpenAIClient()

    result = drafter_module.ChapterDrafter(
        provider_factory=lambda: provider_module.build_route_a_provider(
            {
                "NOVEL_LLM_PROVIDER": "openai",
                "NOVEL_LLM_MODEL": "gpt-4o-mini",
                "NOVEL_LLM_API_KEY": "test-key",
            },
            provider_factory=lambda config: provider_module.OpenAIRouteAProvider(
                config,
                client_factory=lambda _: client,
            ),
        )
    ).draft(_build_state(), 4)

    assert result.content == "OpenAI-backed chapter body."
    assert client.calls == [
        {
            "model": "gpt-4o-mini",
            "temperature": 1.0,
            "messages": [
                {
                    "role": "user",
                    "content": "Draft Chapter 4 about Mira. Summary: Mira takes the next step.",
                }
            ],
        }
    ]


def test_draft_failure_rejects_empty_provider_output() -> None:
    drafter_module = _load_drafter_module()

    with pytest.raises(
        ValueError,
        match="chapter 1 draft provider returned empty content",
    ):
        drafter_module.ChapterDrafter(provider=_FakeProvider("   ")).draft(
            _build_state(), 1
        )


def test_draft_failure_wraps_provider_exceptions_deterministically() -> None:
    drafter_module = _load_drafter_module()

    with pytest.raises(
        ValueError,
        match="chapter 1 draft provider failed: provider exploded",
    ):
        drafter_module.ChapterDrafter(provider=_ExplodingProvider()).draft(
            _build_state(), 1
        )


def test_resilience_classifies_retryable_provider_failures() -> None:
    resilience_module = _load_resilience_module()

    assert resilience_module.classify_route_a_provider_error(
        RateLimitError("slow down")
    ) == resilience_module.RouteAResilienceDecision(
        resilience_module.RouteAErrorDisposition.RETRYABLE,
        "RateLimitError",
    )
    assert resilience_module.classify_route_a_provider_error(
        APIConnectionError("reset")
    ) == resilience_module.RouteAResilienceDecision(
        resilience_module.RouteAErrorDisposition.RETRYABLE,
        "APIConnectionError",
    )
    assert resilience_module.classify_route_a_provider_error(
        InternalServerError("overloaded")
    ) == resilience_module.RouteAResilienceDecision(
        resilience_module.RouteAErrorDisposition.RETRYABLE,
        "InternalServerError",
    )


def test_resilience_classifies_fail_fast_provider_failures() -> None:
    resilience_module = _load_resilience_module()

    assert resilience_module.classify_route_a_provider_error(
        ValueError("invalid prompt")
    ) == resilience_module.RouteAResilienceDecision(
        resilience_module.RouteAErrorDisposition.FAIL_FAST,
        "invalid_request",
    )
    assert resilience_module.classify_route_a_provider_error(
        AuthenticationError("bad key")
    ) == resilience_module.RouteAResilienceDecision(
        resilience_module.RouteAErrorDisposition.FAIL_FAST,
        "AuthenticationError",
    )
    assert resilience_module.classify_route_a_provider_error(
        UnsupportedProviderError("unsupported")
    ) == resilience_module.RouteAResilienceDecision(
        resilience_module.RouteAErrorDisposition.FAIL_FAST,
        "UnsupportedProviderError",
    )


def test_resilience_retries_provider_operation_with_deterministic_backoff() -> None:
    resilience_module = _load_resilience_module()
    operation = _FakeProviderOperation(
        RateLimitError("slow down"),
        APIConnectionError("reset"),
        "draft recovered",
    )
    sleeps: list[float] = []

    result = resilience_module.run_with_route_a_provider_resilience(
        operation,
        sleep=sleeps.append,
    )

    assert result == "draft recovered"
    assert operation.calls == 3
    assert sleeps == [0.1, 0.2]


def test_resilience_fails_fast_without_sleeping_for_non_retryable_error() -> None:
    resilience_module = _load_resilience_module()
    operation = _FakeProviderOperation(AuthenticationError("bad key"))
    sleeps: list[float] = []

    with pytest.raises(AuthenticationError, match="bad key"):
        resilience_module.run_with_route_a_provider_resilience(
            operation,
            sleep=sleeps.append,
        )

    assert operation.calls == 1
    assert sleeps == []


def test_resilience_exposes_fixed_provider_retry_contract_for_later_wiring() -> None:
    resilience_module = _load_resilience_module()

    assert resilience_module.ROUTE_A_PROVIDER_MAX_ATTEMPTS == 3
    assert resilience_module.ROUTE_A_PROVIDER_BACKOFF_SECONDS == (0.1, 0.2)
    assert resilience_module.ROUTE_A_PROVIDER_JITTER_ENABLED is False
    assert resilience_module.route_a_provider_sdk_options() == {"max_retries": 0}


def test_draft_requires_supported_route_a_provider_from_env() -> None:
    provider_module = _load_provider_module()

    with pytest.raises(
        ValueError,
        match="unsupported Route A provider 'anthropic'; expected NOVEL_LLM_PROVIDER='openai'",
    ):
        provider_module.build_route_a_provider(
            {
                "NOVEL_LLM_PROVIDER": "anthropic",
                "NOVEL_LLM_MODEL": "claude-3-7-sonnet",
                "NOVEL_LLM_API_KEY": "test-key",
            }
        )


def test_draft_requires_route_a_api_key_when_provider_env_is_set() -> None:
    provider_module = _load_provider_module()

    with pytest.raises(
        ValueError,
        match="NOVEL_LLM_API_KEY is required when NOVEL_LLM_PROVIDER='openai'",
    ):
        provider_module.build_route_a_provider(
            {
                "NOVEL_LLM_PROVIDER": "openai",
                "NOVEL_LLM_MODEL": "gpt-4o-mini",
            }
        )


def test_draft_requires_route_a_model_when_provider_env_is_set() -> None:
    provider_module = _load_provider_module()

    with pytest.raises(
        ValueError,
        match="NOVEL_LLM_MODEL is required when NOVEL_LLM_PROVIDER='openai'",
    ):
        provider_module.resolve_route_a_provider_config(
            {
                "NOVEL_LLM_PROVIDER": "openai",
                "NOVEL_LLM_API_KEY": "test-key",
            }
        )


@pytest.mark.parametrize("temperature", ["warm", math.inf, -0.01, 2.01])
def test_draft_failure_rejects_invalid_temperature_input(temperature: object) -> None:
    drafter_module = _load_drafter_module()

    with pytest.raises(
        ValueError,
        match="draft temperature must be a finite number between 0.0 and 2.0",
    ):
        drafter_module.ChapterDrafter(temperature=temperature).draft(_build_state(), 1)


def _load_drafter_module():
    try:
        return importlib.import_module("novel_runtime.pipeline.drafter")
    except ModuleNotFoundError:
        pytest.fail(
            "novel_runtime.pipeline.drafter module is required for the chapter draft MVP contract"
        )


def _load_provider_module():
    try:
        return importlib.import_module("novel_runtime.llm.provider")
    except ModuleNotFoundError:
        pytest.fail(
            "novel_runtime.llm.provider module is required for the Route A provider contract"
        )


def _load_canonical_state_class() -> type[Any]:
    try:
        return importlib.import_module("novel_runtime.state.canonical").CanonicalState
    except ModuleNotFoundError:
        pytest.fail(
            "novel_runtime.state.canonical module is required for the chapter draft MVP contract"
        )


def _load_resilience_module():
    try:
        return importlib.import_module("novel_runtime.llm.resilience")
    except ModuleNotFoundError:
        pytest.fail(
            "novel_runtime.llm.resilience module is required for the Route A resilience contract"
        )


def _build_state():
    state = _load_canonical_state_class().create_empty("Example Novel", "fantasy")
    state.data["world"]["entities"].append(
        {
            "id": "entity-1",
            "name": "Mira",
            "type": "character",
            "attributes": {"role": "lead"},
            "visibility": "active",
        }
    )
    return state
