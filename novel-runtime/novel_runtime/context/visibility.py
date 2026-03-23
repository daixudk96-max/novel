from __future__ import annotations

from copy import deepcopy

from novel_runtime.state.canonical import CanonicalState
from novel_runtime.state.schema import ALLOWED_VISIBILITIES


class VisibilityError(ValueError):
    pass


class VisibilityGate:
    _ALLOWED_BY_ROLE = {
        "writer": frozenset({"active"}),
        "checker": frozenset({"active", "reference"}),
        "planner": frozenset(ALLOWED_VISIBILITIES),
    }

    def filter_entities(self, entities: list[dict], role: str) -> list[dict]:
        allowed = self._allowed_visibilities(role)
        return deepcopy(
            [entity for entity in entities if entity.get("visibility") in allowed]
        )

    def update_visibility(
        self,
        entity_id: str,
        new_visibility: str,
        state: CanonicalState,
    ) -> dict:
        self._validate_visibility(new_visibility)

        for entity in state.data["world"]["entities"]:
            if entity["id"] == entity_id:
                entity["visibility"] = new_visibility
                return deepcopy(entity)

        raise VisibilityError(f"entity '{entity_id}' not found")

    def get_visible_entities(self, state: CanonicalState, role: str) -> list[dict]:
        return self.filter_entities(state.data["world"]["entities"], role)

    def _allowed_visibilities(self, role: str) -> frozenset[str]:
        allowed = self._ALLOWED_BY_ROLE.get(role)
        if allowed is None:
            supported = ", ".join(sorted(self._ALLOWED_BY_ROLE))
            raise VisibilityError(f"role must be one of: {supported}")
        return allowed

    def _validate_visibility(self, visibility: str) -> None:
        if visibility not in ALLOWED_VISIBILITIES:
            allowed = ", ".join(sorted(ALLOWED_VISIBILITIES))
            raise VisibilityError(f"visibility must be one of: {allowed}")


__all__ = ["VisibilityError", "VisibilityGate"]
