from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol


SUPPORTED_ROUTE_A_PROVIDER = "openai"


@dataclass(frozen=True, slots=True)
class RouteAProviderConfig:
    provider: str
    model: str
    api_key: str


class RouteAProvider(Protocol):
    @property
    def config(self) -> RouteAProviderConfig: ...

    def draft(self, *, prompt: str, temperature: float) -> str: ...


@dataclass(frozen=True, slots=True)
class OpenAIRouteAProvider:
    config: RouteAProviderConfig
    client_factory: Callable[[RouteAProviderConfig], Any] = lambda config: (
        _build_openai_client(config)
    )

    def draft(self, *, prompt: str, temperature: float) -> str:
        response = self.client_factory(self.config).chat.completions.create(
            model=self.config.model,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_openai_message_content(response)


def resolve_route_a_provider_config(
    env: Mapping[str, str] | None = None,
) -> RouteAProviderConfig:
    source = os.environ if env is None else env
    provider = _normalize_provider(source.get("NOVEL_LLM_PROVIDER"))

    if not provider:
        raise ValueError(
            "NOVEL_LLM_PROVIDER is required for Route A provider resolution"
        )

    if provider != SUPPORTED_ROUTE_A_PROVIDER:
        raise ValueError(
            f"unsupported Route A provider '{provider}'; expected NOVEL_LLM_PROVIDER='openai'"
        )

    model = _normalize_value(source.get("NOVEL_LLM_MODEL"))
    if not model:
        raise ValueError("NOVEL_LLM_MODEL is required when NOVEL_LLM_PROVIDER='openai'")

    api_key = _normalize_value(source.get("NOVEL_LLM_API_KEY"))
    if not api_key:
        raise ValueError(
            "NOVEL_LLM_API_KEY is required when NOVEL_LLM_PROVIDER='openai'"
        )

    return RouteAProviderConfig(provider=provider, model=model, api_key=api_key)


def build_route_a_provider(
    env: Mapping[str, str] | None = None,
    *,
    provider_factory: Callable[
        [RouteAProviderConfig], RouteAProvider
    ] = OpenAIRouteAProvider,
) -> RouteAProvider:
    config = resolve_route_a_provider_config(env)
    return provider_factory(config)


def _normalize_provider(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def _normalize_value(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _build_openai_client(config: RouteAProviderConfig):
    from openai import OpenAI

    return OpenAI(api_key=config.api_key)


def _extract_openai_message_content(response: object) -> str:
    choices = getattr(response, "choices", None)
    if not choices:
        return ""

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        text = getattr(item, "text", None)
        if isinstance(text, str):
            parts.append(text)
            continue
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "".join(parts)


__all__ = [
    "OpenAIRouteAProvider",
    "RouteAProvider",
    "RouteAProviderConfig",
    "SUPPORTED_ROUTE_A_PROVIDER",
    "build_route_a_provider",
    "resolve_route_a_provider_config",
]
