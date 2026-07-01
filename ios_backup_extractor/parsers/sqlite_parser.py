"""SQLite parsing and export helpers.

These utilities are intentionally generic: artifact-specific plugins can use the
same code to inspect schema, export full tables, and run known-safe SELECT
queries into JSON/CSV outputs.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable, Mapping, Sequence


@dataclass
class SQLiteTableExport:
    """Metadata for a table export operation."""

    table: str
    row_count: int
    json_path: Path | None = None
    csv_path: Path | None = None
    columns: list[str] = field(default_factory=list)


class SQLiteParser:
    """Read-only SQLite parser/exporter for forensic artifacts."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(self.db_path)

    def connect(self) -> sqlite3.Connection:
        uri = f"file:{self.db_path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def tables(self) -> list[str]:
        """Return user-created table names."""

        with self.connect() as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        return [row["name"] for row in rows]

    def columns(self, table: str) -> list[str]:
        """Return column names for a table."""

        self._validate_identifier(table)
        with self.connect() as conn:
            rows = conn.execute(f"PRAGMA table_info({self._quote_identifier(table)})").fetchall()
        return [row["name"] for row in rows]

    def query(self, sql: str, parameters: Sequence[Any] | Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        """Run a read-only SELECT query and return JSON-serializable rows."""

        if not sql.lstrip().lower().startswith("select"):
            raise ValueError("Only SELECT queries are supported by SQLiteParser.query().")
        with self.connect() as conn:
            rows = conn.execute(sql, parameters or ()).fetchall()
        return [self._normalize_row(row) for row in rows]

    def export_table(
        self,
        table: str,
        output_dir: Path | str,
        *,
        formats: Iterable[str] = ("json", "csv"),
        limit: int | None = None,
    ) -> SQLiteTableExport:
        """Export a table to JSON and/or CSV."""

        self._validate_identifier(table)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        quoted = self._quote_identifier(table)
        limit_clause = "" if limit is None else f" LIMIT {int(limit)}"
        rows = self.query(f"SELECT * FROM {quoted}{limit_clause}")
        columns = list(rows[0].keys()) if rows else self.columns(table)

        export = SQLiteTableExport(table=table, row_count=len(rows), columns=columns)
        selected_formats = {fmt.lower() for fmt in formats}

        if "json" in selected_formats:
            export.json_path = output_path / f"{table}.json"
            export.json_path.write_text(json.dumps(rows, indent=2, sort_keys=True, default=str), encoding="utf-8")

        if "csv" in selected_formats:
            export.csv_path = output_path / f"{table}.csv"
            with export.csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns)
                writer.writeheader()
                for row in rows:
                    writer.writerow({key: row.get(key) for key in columns})

        return export

    def export_all_tables(
        self,
        output_dir: Path | str,
        *,
        formats: Iterable[str] = ("json", "csv"),
        limit: int | None = None,
    ) -> list[SQLiteTableExport]:
        """Export every user-created table in the database."""

        return [self.export_table(table, output_dir, formats=formats, limit=limit) for table in self.tables()]

    def schema(self) -> dict[str, list[str]]:
        """Return a table-to-columns mapping."""

        return {table: self.columns(table) for table in self.tables()}

    @staticmethod
    def _normalize_row(row: sqlite3.Row) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key in row.keys():
            value = row[key]
            if isinstance(value, bytes):
                normalized[key] = value.hex()
            else:
                normalized[key] = value
        return normalized

    @staticmethod
    def _validate_identifier(identifier: str) -> None:
        if not identifier or "\x00" in identifier or '"' in identifier:
            raise ValueError(f"Unsafe SQLite identifier: {identifier!r}")

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        SQLiteParser._validate_identifier(identifier)
        return f'"{identifier}"'
