from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from novel_runtime.llm import provider as _provider


_ORIGINAL_BUILD_ROUTE_A_PROVIDER = _provider.build_route_a_provider
_FAKE_PROVIDER_ENV = "NOVEL_REAL_VERIFY_FAKE_PROVIDER"
_DRAFT_TEXT_ENV = "NOVEL_REAL_VERIFY_DRAFT_TEXT_FILE"
_CALL_LOG_ENV = "NOVEL_REAL_VERIFY_PROVIDER_CALL_LOG"


@dataclass(frozen=True, slots=True)
class _FakeRouteAProvider:
    config: _provider.RouteAProviderConfig
    draft_text_file: Path
    call_log_path: Path

    def draft(self, *, prompt: str, temperature: float) -> str:
        self.call_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.call_log_path.write_text(
            json.dumps({"prompt": prompt, "temperature": temperature}, indent=2),
            encoding="utf-8",
        )
        return self.draft_text_file.read_text(encoding="utf-8")


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
    return _FakeRouteAProvider(
        config=config,
        draft_text_file=draft_text_file,
        call_log_path=call_log_path,
    )


def _required_path(source: Mapping[str, str], name: str) -> Path:
    value = source.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} is required when {_FAKE_PROVIDER_ENV}=1")
    return Path(value.strip())


_provider.build_route_a_provider = _patched_build_route_a_provider
