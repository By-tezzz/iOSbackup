"""Call history database extraction plugin."""

from __future__ import annotations

from pathlib import Path

from .base import PluginResult


class Plugin:
    name = "callhistory"
    description = "Extract CallHistory.storedata for downstream parsing."

    CALL_HISTORY = "Library/CallHistoryDB/CallHistory.storedata"

    def supports(self, backup) -> bool:
        return bool(backup.find_files(relative_path=self.CALL_HISTORY))

    def process(self, backup, output_dir: Path) -> PluginResult:
        artifact = backup.extract_file(relative_path=self.CALL_HISTORY, output_dir=output_dir)
        artifacts = [artifact] if artifact else []
        return PluginResult(
            plugin=self.name,
            status="ok" if artifact else "skipped",
            summary="Extracted call history database." if artifact else "Call history database not present in backup.",
            artifacts=artifacts,
        )
