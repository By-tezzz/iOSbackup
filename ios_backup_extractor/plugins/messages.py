"""Message database extraction and parsing plugin."""

from __future__ import annotations

from pathlib import Path

from ios_backup_extractor.parsers.artifact_sqlite import parse_messages

from .base import PluginResult


class Plugin:
    name = "messages"
    description = "Extract and parse the device message database."

    DB_PATH = "Library/SMS/sms.db"

    def supports(self, backup) -> bool:
        return bool(backup.find_files(relative_path=self.DB_PATH))

    def process(self, backup, output_dir: Path) -> PluginResult:
        artifact = backup.extract_file(relative_path=self.DB_PATH, output_dir=output_dir)
        if not artifact:
            return PluginResult(
                plugin=self.name,
                status="skipped",
                summary="Message database not present in backup.",
            )

        parsed = parse_messages(artifact, output_dir / "parsed")
        artifacts = [artifact]
        for table in parsed.get("tables", []):
            for key in ("json_path", "csv_path"):
                if table.get(key):
                    artifacts.append(Path(table[key]))
        normalized = output_dir / "parsed" / "messages_normalized.json"
        if normalized.exists():
            artifacts.append(normalized)

        return PluginResult(
            plugin=self.name,
            status="ok",
            summary=f"Extracted message database and parsed {parsed['normalized_records']} normalized record(s).",
            artifacts=artifacts,
            metadata=parsed,
        )
