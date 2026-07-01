"""Artifact-specific SQLite parsers.

These functions intentionally stay defensive. They inspect available columns and
only run queries when the expected tables exist, allowing them to survive iOS
schema drift across versions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .sqlite_parser import SQLiteParser, SQLiteTableExport


def parse_call_history(db_path: Path | str, output_dir: Path | str) -> dict[str, Any]:
    """Export call-history tables and a best-effort normalized calls JSON."""

    parser = SQLiteParser(db_path)
    output_path = Path(output_dir)
    exports = parser.export_all_tables(output_path / "tables")
    normalized: list[dict[str, Any]] = []

    if "ZCALLRECORD" in parser.tables():
        normalized = parser.query(
            """
            SELECT
                Z_PK AS id,
                ZADDRESS AS address,
                ZDATE AS apple_date,
                ZDURATION AS duration_seconds,
                ZCALLTYPE AS call_type,
                ZORIGINATED AS originated,
                ZANSWERED AS answered
            FROM ZCALLRECORD
            ORDER BY ZDATE DESC
            """
        )
        (output_path / "calls_normalized.json").write_text(
            _json_dumps(normalized), encoding="utf-8"
        )

    return {
        "tables": [_export_to_dict(export) for export in exports],
        "normalized_records": len(normalized),
    }


def parse_messages(db_path: Path | str, output_dir: Path | str) -> dict[str, Any]:
    """Export message tables and a best-effort normalized messages JSON."""

    parser = SQLiteParser(db_path)
    output_path = Path(output_dir)
    tables = set(parser.tables())
    important = [table for table in ("message", "handle", "chat", "attachment") if table in tables]
    exports = [parser.export_table(table, output_path / "tables") for table in important]
    normalized: list[dict[str, Any]] = []

    if "message" in tables:
        normalized = parser.query(
            """
            SELECT
                message.ROWID AS id,
                message.guid AS guid,
                message.date AS apple_date,
                message.date_read AS apple_date_read,
                message.date_delivered AS apple_date_delivered,
                message.is_from_me AS is_from_me,
                message.service AS service,
                message.text AS text,
                handle.id AS handle_id
            FROM message
            LEFT JOIN handle ON message.handle_id = handle.ROWID
            ORDER BY message.date DESC
            """
        )
        (output_path / "messages_normalized.json").write_text(
            _json_dumps(normalized), encoding="utf-8"
        )

    return {
        "tables": [_export_to_dict(export) for export in exports],
        "normalized_records": len(normalized),
    }


def parse_knowledgec(db_path: Path | str, output_dir: Path | str) -> dict[str, Any]:
    """Export KnowledgeC tables and normalized object/activity rows when available."""

    parser = SQLiteParser(db_path)
    output_path = Path(output_dir)
    tables = set(parser.tables())
    exports = parser.export_all_tables(output_path / "tables")
    normalized: list[dict[str, Any]] = []

    if "ZOBJECT" in tables:
        columns = set(parser.columns("ZOBJECT"))
        select_parts = ["Z_PK AS id"]
        for candidate in ("ZSTREAMNAME", "ZVALUESTRING", "ZSTARTDATE", "ZENDDATE", "ZCREATIONDATE"):
            if candidate in columns:
                select_parts.append(f"{candidate} AS {candidate.lower()}")
        normalized = parser.query(f"SELECT {', '.join(select_parts)} FROM ZOBJECT ORDER BY Z_PK DESC")
        (output_path / "knowledgec_objects_normalized.json").write_text(
            _json_dumps(normalized), encoding="utf-8"
        )

    return {
        "tables": [_export_to_dict(export) for export in exports],
        "normalized_records": len(normalized),
    }


def _export_to_dict(export: SQLiteTableExport) -> dict[str, Any]:
    return {
        "table": export.table,
        "row_count": export.row_count,
        "columns": export.columns,
        "json_path": str(export.json_path) if export.json_path else None,
        "csv_path": str(export.csv_path) if export.csv_path else None,
    }


def _json_dumps(value: Any) -> str:
    import json

    return json.dumps(value, indent=2, sort_keys=True, default=str)
