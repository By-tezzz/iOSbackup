"""Message database export plugin."""

from __future__ import annotations

from pathlib import Path

from .base import PluginResult


class Plugin:
    name = "messages"
    description = "Extract the device message database for downstream parsing."

    DB_PATH = "Library/SMS/sms.db"

    def supports(self, backup) -> bool:
        return bool(backup.find_files(relative_path=self.DB_PATH))

    def process(self, backup, output_dir: Path) -> PluginResult:
        artifact = backup.extract_file(relative_path=self.DB_PATH, output_dir=output_dir)
        artifacts = [artifact] if artifact else []
        return PluginResult(
            plugin=self.name,
            status="ok" if artifact else "skipped",
            summary="Extracted device message database." if artifact else "Message database not present in backup.",
            artifacts=artifacts,
        )
