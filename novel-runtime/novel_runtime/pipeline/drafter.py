from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from novel_runtime.llm.resilience import (
    ROUTE_A_PROVIDER_MAX_ATTEMPTS,
    classify_route_a_provider_error,
    is_route_a_retryable_provider_error,
    run_with_route_a_provider_resilience,
)
from novel_runtime.llm.provider import RouteAProvider, build_route_a_provider
from novel_runtime.llm.temperature import (
    DEFAULT_DRAFT_TEMPERATURE,
    normalize_draft_temperature,
)
from novel_runtime.state.canonical import CanonicalState


@dataclass(frozen=True, slots=True)
class ChapterDraft:
    chapter: int
    title: str
    status: str
    summary: str
    content: str


class ChapterDrafter:
    def __init__(
        self,
        *,
        provider: RouteAProvider | None = None,
        provider_factory: Callable[[], RouteAProvider] = build_route_a_provider,
        temperature: object = DEFAULT_DRAFT_TEMPERATURE,
    ) -> None:
        self._provider = provider
        self._provider_factory = provider_factory
        self._temperature = normalize_draft_temperature(temperature)

    def draft(self, state: CanonicalState, chapter_number: int) -> ChapterDraft:
        if type(chapter_number) is not int:
            raise ValueError("chapter_number must be an integer")

        entity = self._first_active_world_entity(state)
        if entity is None:
            raise ValueError(
                f"chapter {chapter_number} draft requires at least one active world entity"
            )

        title = f"Chapter {chapter_number}"
        summary = f"{entity['name']} takes the next step."
        content = self._draft_content(
            chapter_number=chapter_number,
            entity_name=entity["name"],
            summary=summary,
        )
        return ChapterDraft(
            chapter=chapter_number,
            title=title,
            status="draft",
            summary=summary,
            content=content,
        )

    def _draft_content(
        self,
        *,
        chapter_number: int,
        entity_name: str,
        summary: str,
    ) -> str:
        prompt = (
            f"Draft Chapter {chapter_number} about {entity_name}. Summary: {summary}"
        )
        provider = self._resolve_provider()

        try:
            content = run_with_route_a_provider_resilience(
                lambda: provider.draft(
                    prompt=prompt,
                    temperature=self._temperature,
                )
            )
        except Exception as exc:
            if is_route_a_retryable_provider_error(exc):
                raise ValueError(
                    f"chapter draft failed after {ROUTE_A_PROVIDER_MAX_ATTEMPTS} attempts: {exc}"
                ) from exc
            decision = classify_route_a_provider_error(exc)
            if decision.reason == "invalid_request":
                raise ValueError(str(exc)) from exc
            raise ValueError(
                f"chapter {chapter_number} draft provider failed: {exc}"
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise ValueError(
                f"chapter {chapter_number} draft provider returned empty content"
            )

        return content

    def _resolve_provider(self) -> RouteAProvider:
        if self._provider is None:
            self._provider = self._provider_factory()
        return self._provider

    def _first_active_world_entity(self, state: CanonicalState) -> dict | None:
        for entity in state.data["world"]["entities"]:
            if not isinstance(entity, dict):
                continue
            if entity.get("visibility") != "active":
                continue
            if not isinstance(entity.get("name"), str) or not entity["name"].strip():
                continue
            return entity
        return None


__all__ = ["ChapterDraft", "ChapterDrafter"]
