"""KnowledgeC artifact extraction and parsing plugin."""

from __future__ import annotations

from pathlib import Path

from ios_backup_extractor.parsers.artifact_sqlite import parse_knowledgec

from .base import PluginResult


class Plugin:
    name = "knowledgec"
    description = "Locate, extract, and parse KnowledgeC/CoreDuet activity databases."

    CANDIDATES = (
        "Library/Application Support/Knowledge/knowledgeC.db",
        "Library/Application Support/com.apple.spotlight/knowledgeC.db",
    )

    def supports(self, backup) -> bool:
        return any(backup.find_files(relative_path=path) for path in self.CANDIDATES)

    def process(self, backup, output_dir: Path) -> PluginResult:
        artifacts: list[Path] = []
        parsed_outputs: list[dict] = []
        missing: list[str] = []

        for path in self.CANDIDATES:
            extracted = backup.extract_file(relative_path=path, output_dir=output_dir)
            if not extracted:
                missing.append(path)
                continue

            artifacts.append(extracted)
            parsed_dir = output_dir / "parsed" / extracted.stem
            parsed = parse_knowledgec(extracted, parsed_dir)
            parsed_outputs.append({"source": str(extracted), **parsed})
            for table in parsed.get("tables", []):
                for key in ("json_path", "csv_path"):
                    if table.get(key):
                        artifacts.append(Path(table[key]))
            normalized = parsed_dir / "knowledgec_objects_normalized.json"
            if normalized.exists():
                artifacts.append(normalized)

        normalized_records = sum(item.get("normalized_records", 0) for item in parsed_outputs)
        return PluginResult(
            plugin=self.name,
            status="ok" if artifacts else "skipped",
            summary=f"Extracted {len(parsed_outputs)} KnowledgeC candidate file(s) and parsed {normalized_records} normalized record(s).",
            artifacts=artifacts,
            metadata={"missing_candidates": missing, "parsed": parsed_outputs},
        )
