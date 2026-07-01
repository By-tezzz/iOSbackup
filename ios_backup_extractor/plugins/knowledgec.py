"""KnowledgeC artifact discovery plugin."""

from __future__ import annotations

from pathlib import Path

from .base import PluginResult


class Plugin:
    name = "knowledgec"
    description = "Locate and extract KnowledgeC/CoreDuet activity databases."

    CANDIDATES = (
        "Library/Application Support/Knowledge/knowledgeC.db",
        "Library/Application Support/com.apple.spotlight/knowledgeC.db",
    )

    def supports(self, backup) -> bool:
        return any(backup.find_files(relative_path=path) for path in self.CANDIDATES)

    def process(self, backup, output_dir: Path) -> PluginResult:
        artifacts: list[Path] = []
        missing: list[str] = []
        for path in self.CANDIDATES:
            extracted = backup.extract_file(relative_path=path, output_dir=output_dir)
            if extracted:
                artifacts.append(extracted)
            else:
                missing.append(path)

        return PluginResult(
            plugin=self.name,
            status="ok" if artifacts else "skipped",
            summary=f"Extracted {len(artifacts)} KnowledgeC candidate file(s).",
            artifacts=artifacts,
            metadata={"missing_candidates": missing},
        )
