"""Biome artifact discovery plugin.

This first pass only discovers and exports matching files. Decoders can be added
under this plugin without changing acquisition or backup extraction code.
"""

from __future__ import annotations

from pathlib import Path

from .base import PluginResult


class Plugin:
    name = "biome"
    description = "Discover and extract Biome files for later parser integrations."

    NEEDLE = "Biome"

    def supports(self, backup) -> bool:
        return bool(backup.find_files(contains=self.NEEDLE))

    def process(self, backup, output_dir: Path) -> PluginResult:
        artifacts: list[Path] = []
        for record in backup.find_files(contains=self.NEEDLE):
            safe_name = f"{record.domain}__{record.relative_path}".replace("/", "__")
            extracted = backup.extract_file(
                relative_path=record.relative_path,
                domain=record.domain,
                output_dir=output_dir,
                output_name=safe_name,
            )
            if extracted:
                artifacts.append(extracted)

        return PluginResult(
            plugin=self.name,
            status="ok" if artifacts else "skipped",
            summary=f"Extracted {len(artifacts)} Biome candidate file(s).",
            artifacts=artifacts,
        )
