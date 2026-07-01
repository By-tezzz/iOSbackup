"""Property list parsing helpers.

Supports XML and binary plist files via Python's standard ``plistlib`` and writes
normalized JSON for report pipelines.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
import plistlib
from typing import Any


@dataclass
class PlistParseResult:
    """Result for a parsed plist artifact."""

    source_path: Path
    json_path: Path | None
    root_type: str
    keys: list[str]


class PlistParser:
    """Read plist files and export normalized JSON."""

    def __init__(self, plist_path: Path | str) -> None:
        self.plist_path = Path(plist_path)
        if not self.plist_path.exists():
            raise FileNotFoundError(self.plist_path)

    def parse(self) -> Any:
        """Return the parsed plist object."""

        with self.plist_path.open("rb") as handle:
            return plistlib.load(handle)

    def export_json(self, output_dir: Path | str, *, output_name: str | None = None) -> PlistParseResult:
        """Parse a plist and write a normalized JSON copy."""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        parsed = self.parse()
        name = output_name or f"{self.plist_path.name}.json"
        json_path = output_path / name
        json_path.write_text(json.dumps(self._normalize(parsed), indent=2, sort_keys=True), encoding="utf-8")
        return PlistParseResult(
            source_path=self.plist_path,
            json_path=json_path,
            root_type=type(parsed).__name__,
            keys=sorted(parsed.keys()) if isinstance(parsed, dict) else [],
        )

    @classmethod
    def parse_to_json(cls, plist_path: Path | str, output_dir: Path | str) -> PlistParseResult:
        """Convenience helper for one-shot plist export."""

        return cls(plist_path).export_json(output_dir)

    @classmethod
    def _normalize(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): cls._normalize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls._normalize(item) for item in value]
        if isinstance(value, tuple):
            return [cls._normalize(item) for item in value]
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, bytes):
            return value.hex()
        return value
