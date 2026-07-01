"""Call history database extraction and parsing plugin."""

from __future__ import annotations

from pathlib import Path

from ios_backup_extractor.parsers.artifact_sqlite import parse_call_history

from .base import PluginResult


class Plugin:
    name = "callhistory"
    description = "Extract and parse CallHistory.storedata."

    CALL_HISTORY = "Library/CallHistoryDB/CallHistory.storedata"

    def supports(self, backup) -> bool:
        return bool(backup.find_files(relative_path=self.CALL_HISTORY))

    def process(self, backup, output_dir: Path) -> PluginResult:
        artifact = backup.extract_file(relative_path=self.CALL_HISTORY, output_dir=output_dir)
        if not artifact:
            return PluginResult(
                plugin=self.name,
                status="skipped",
                summary="Call history database not present in backup.",
            )

        parsed = parse_call_history(artifact, output_dir / "parsed")
        artifacts = [artifact]
        for table in parsed.get("tables", []):
            for key in ("json_path", "csv_path"):
                if table.get(key):
                    artifacts.append(Path(table[key]))
        normalized = output_dir / "parsed" / "calls_normalized.json"
        if normalized.exists():
            artifacts.append(normalized)

        return PluginResult(
            plugin=self.name,
            status="ok",
            summary=f"Extracted call history database and parsed {parsed['normalized_records']} normalized record(s).",
            artifacts=artifacts,
            metadata=parsed,
        )
