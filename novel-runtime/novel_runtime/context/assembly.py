from __future__ import annotations

import re
from copy import deepcopy


class ContextAssembler:
    def assemble_writer_context(
        self, state, chapter_number: int, token_budget: int
    ) -> dict:
        return self._assemble_context(
            state, chapter_number, token_budget, role="writer"
        )

    def assemble_checker_context(
        self, state, chapter_number: int, token_budget: int
    ) -> dict:
        return self._assemble_context(
            state, chapter_number, token_budget, role="checker"
        )

    def _assemble_context(
        self, state, chapter_number: int, token_budget: int, role: str
    ) -> dict:
        chapter = self._get_chapter(state, chapter_number)
        chapter_context = {
            "number": chapter["number"],
            "title": chapter["title"],
            "summary": chapter["summary"],
        }
        chapter_tokens = self._estimate_tokens(chapter_context["summary"])
        visible_entities = self._visible_entities(state.data["world"]["entities"], role)
        prepared_entities = self._prepare_entities(
            visible_entities, chapter_context["summary"]
        )
        included_entities = self._trim_entities(
            prepared_entities, token_budget - chapter_tokens
        )

        active_entities = [
            entity["context"]
            for entity in included_entities
            if entity["context"]["visibility"] == "active"
        ]
        reference_entities = [
            entity["context"]
            for entity in included_entities
            if entity["context"]["visibility"] == "reference"
        ]

        return {
            "role": role,
            "chapter": chapter_context,
            "active_entities": active_entities,
            "reference_entities": reference_entities,
            "matched_entity_ids": [
                entity["context"]["id"]
                for entity in included_entities
                if entity["matched"]
            ],
            "token_budget": token_budget,
            "token_count": chapter_tokens
            + sum(entity["token_cost"] for entity in included_entities),
        }

    def _get_chapter(self, state, chapter_number: int) -> dict:
        for chapter in state.data["chapters"]:
            if chapter["number"] == chapter_number:
                return chapter
        raise ValueError(f"chapter '{chapter_number}' not found")

    def _visible_entities(self, entities: list[dict], role: str) -> list[dict]:
        allowed = {"active"} if role == "writer" else {"active", "reference"}
        return [entity for entity in entities if entity["visibility"] in allowed]

    def _prepare_entities(self, entities: list[dict], chapter_text: str) -> list[dict]:
        prepared = []
        for index, entity in enumerate(entities):
            context = {
                "id": entity["id"],
                "name": entity["name"],
                "type": entity["type"],
                "visibility": entity["visibility"],
                "attributes": deepcopy(entity["attributes"]),
                "mentioned_in_chapter": self._matches_text(
                    chapter_text, entity["name"]
                ),
            }
            prepared.append(
                {
                    "context": context,
                    "matched": context["mentioned_in_chapter"],
                    "token_cost": self._estimate_entity_tokens(context),
                    "priority": self._priority_tuple(context, index),
                }
            )
        return prepared

    def _trim_entities(self, entities: list[dict], remaining_budget: int) -> list[dict]:
        if not entities or remaining_budget <= 0:
            return []

        included = []
        budget_left = remaining_budget
        for entity in sorted(entities, key=lambda item: item["priority"]):
            if entity["token_cost"] <= budget_left:
                included.append(entity)
                budget_left -= entity["token_cost"]
        return included

    def _priority_tuple(self, entity: dict, index: int) -> tuple[int, int, int]:
        visibility_priority = 0 if entity["visibility"] == "active" else 1
        matched_priority = 0 if entity["mentioned_in_chapter"] else 1
        return (visibility_priority, matched_priority, index)

    def _matches_text(self, text: str, entity_name: str) -> bool:
        normalized = entity_name.strip()
        if not normalized:
            return False
        pattern = rf"(?<!\w){re.escape(normalized)}(?!\w)"
        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    def _estimate_entity_tokens(self, entity: dict) -> int:
        parts = [entity["name"]]
        for key in sorted(entity["attributes"]):
            parts.append(str(entity["attributes"][key]))
        return self._estimate_tokens(" ".join(parts))

    def _estimate_tokens(self, value: str) -> int:
        return len(re.findall(r"\S+", value))


__all__ = ["ContextAssembler"]
