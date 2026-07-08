from __future__ import annotations

from collections import Counter


class SessionCounter:
    def __init__(self):
        self._counts: Counter[str] = Counter()

    def record(self, tool: str) -> None:
        self._counts[tool] += 1

    def stats(self) -> dict:
        return {"total": sum(self._counts.values()),
                "by_tool": dict(self._counts)}

    def reset(self) -> None:
        self._counts.clear()
