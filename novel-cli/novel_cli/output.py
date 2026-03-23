from __future__ import annotations

import json
from collections.abc import Mapping, Sequence


class OutputFormatter:
    def format(self, data: object, mode: str = "plain") -> str:
        if mode == "json":
            return json.dumps(data, ensure_ascii=False, sort_keys=True)
        if mode == "table":
            return self._format_table(data)
        return self._format_plain(data)

    def error_format(self, error: object, mode: str) -> str:
        payload = self._error_payload(error)
        if mode == "json":
            return self.format(payload, mode="json")
        return f"Error: {payload['error']}"

    def _format_plain(self, data: object) -> str:
        if isinstance(data, Mapping):
            return "\n".join(f"{key}: {self._plain_scalar(data[key])}" for key in data)
        if isinstance(data, Sequence) and not isinstance(data, (str, bytes, bytearray)):
            return "\n".join(self._plain_scalar(item) for item in data)
        return self._plain_scalar(data)

    def _format_table(self, data: object) -> str:
        if not isinstance(data, Sequence) or isinstance(data, (str, bytes, bytearray)):
            return self._format_plain(data)
        rows = [item for item in data if isinstance(item, Mapping)]
        if not rows:
            return self._format_plain(data)
        columns = [str(key) for key in rows[0]]
        lines = [" | ".join(columns)]
        lines.extend(
            " | ".join(self._plain_scalar(row.get(column)) for column in columns)
            for row in rows
        )
        return "\n".join(lines)

    def _plain_scalar(self, value: object) -> str:
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        if value is None:
            return "null"
        return str(value)

    def _error_payload(self, error: object) -> dict[str, object]:
        if isinstance(error, Mapping):
            message = str(error.get("error", "unknown error"))
            code = int(error.get("code", 1))
            nested = self._decode_json_error(message)
            if nested is not None:
                nested.setdefault("code", code)
                return nested
            return {"error": message, "code": code}

        message = str(error)
        code = getattr(error, "exit_code", getattr(error, "code", 1))
        nested = self._decode_json_error(message)
        if nested is not None:
            nested.setdefault("code", int(code))
            return nested
        return {"error": message, "code": int(code)}

    def _decode_json_error(self, message: str) -> dict[str, object] | None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return None

        if not isinstance(payload, Mapping) or "error" not in payload:
            return None

        code = payload.get("code", 1)
        return {"error": str(payload["error"]), "code": int(code)}


__all__ = ["OutputFormatter"]
