from __future__ import annotations

from dataclasses import dataclass

from novel_runtime.state.canonical import CanonicalState


@dataclass(frozen=True, slots=True)
class ChapterDraft:
    chapter: int
    title: str
    status: str
    summary: str
    content: str


class ChapterDrafter:
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
        return ChapterDraft(
            chapter=chapter_number,
            title=title,
            status="draft",
            summary=summary,
            content=f"# {title}\n\n{summary}\n",
        )

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
