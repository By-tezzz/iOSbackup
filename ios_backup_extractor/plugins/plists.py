"""Property-list extraction and JSON parsing plugin."""

from __future__ import annotations

from pathlib import Path

from ios_backup_extractor.parsers.plist_parser import PlistParser

from .base import PluginResult


class Plugin:
    name = "plists"
    description = "Discover plist artifacts and export parsed JSON copies."

    CANDIDATES = (
        "Info.plist",
        "Manifest.plist",
        "Status.plist",
    )

    def supports(self, backup) -> bool:
        if any(backup.find_files(relative_path=path) for path in self.CANDIDATES):
            return True
        return bool(backup.find_files(contains=".plist"))

    def process(self, backup, output_dir: Path) -> PluginResult:
        artifacts: list[Path] = []
        parsed: list[dict] = []
        seen: set[tuple[str, str]] = set()

        records = []
        for path in self.CANDIDATES:
            records.extend(backup.find_files(relative_path=path))
        records.extend(backup.find_files(contains=".plist"))

        for record in records:
            key = (record.domain, record.relative_path)
            if key in seen:
                continue
            seen.add(key)

            safe_name = f"{record.domain}__{record.relative_path}".replace("/", "__")
            extracted = backup.extract_file(
                relative_path=record.relative_path,
                domain=record.domain,
                output_dir=output_dir / "raw",
                output_name=safe_name,
            )
            if not extracted:
                continue

            artifacts.append(extracted)
            try:
                result = PlistParser(extracted).export_json(output_dir / "parsed", output_name=f"{safe_name}.json")
                if result.json_path:
                    artifacts.append(result.json_path)
                parsed.append(
                    {
                        "source": str(extracted),
                        "json_path": str(result.json_path) if result.json_path else None,
                        "root_type": result.root_type,
                        "keys": result.keys,
                    }
                )
            except Exception as exc:
                parsed.append(
                    {
                        "source": str(extracted),
                        "error": str(exc),
                    }
                )

        return PluginResult(
            plugin=self.name,
            status="ok" if artifacts else "skipped",
            summary=f"Extracted {len(seen)} plist candidate(s), parsed {sum(1 for item in parsed if 'error' not in item)} JSON output(s).",
            artifacts=artifacts,
            metadata={"parsed": parsed},
        )
