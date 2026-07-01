"""JSON report output for acquisition and plugin runs."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Iterable

from ios_backup_extractor.plugins.base import PluginResult


def write_report(results: Iterable[PluginResult], output_dir: Path | str) -> Path:
    """Write a normalized JSON report and return its path."""

    output_path = Path(output_dir).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    report_path = output_path / "extraction_report.json"

    payload = []
    for result in results:
        item = asdict(result)
        item["artifacts"] = [str(path) for path in result.artifacts]
        payload.append(item)

    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return report_path
