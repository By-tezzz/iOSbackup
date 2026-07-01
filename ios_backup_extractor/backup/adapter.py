"""Adapter over the legacy iOSbackup class.

The adapter gives new plugins a small stable interface while preserving the
underlying project API for encrypted backup handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

from iOSbackup import iOSbackup


@dataclass(frozen=True)
class BackupFileRecord:
    """A file record from Manifest.db."""

    backup_file: str
    domain: str
    relative_path: str
    name: str | None = None
    size: int | None = None
    flags: int | None = None


class IOSBackupAdapter:
    """Stable facade consumed by plugins and report generators."""

    def __init__(
        self,
        *,
        udid: str,
        backup_root: Path | str | None = None,
        password: str | None = None,
        derived_key: str | bytes | None = None,
    ) -> None:
        self.udid = udid
        self.backup_root = Path(backup_root).expanduser() if backup_root else None
        self._backup = iOSbackup(
            udid=udid,
            cleartextpassword=password,
            derivedkey=derived_key,
            backuproot=str(self.backup_root) if self.backup_root else None,
        )

    @property
    def raw(self) -> iOSbackup:
        """Return the underlying legacy iOSbackup object."""

        return self._backup

    @property
    def info(self) -> dict[str, Any]:
        return getattr(self._backup, "info", {})

    @property
    def manifest(self) -> dict[str, Any]:
        return getattr(self._backup, "manifest", {})

    @property
    def manifest_db_path(self) -> Path:
        return Path(self._backup.manifestDB)

    def iter_files(self) -> Iterable[BackupFileRecord]:
        """Yield backup file records from Manifest.db."""

        for item in self._backup.getBackupFilesList():
            yield BackupFileRecord(
                backup_file=item.get("backupFile", ""),
                domain=item.get("domain", ""),
                relative_path=item.get("relativePath") or item.get("name", ""),
                name=item.get("name"),
                size=item.get("size"),
                flags=item.get("flags"),
            )

    def find_files(
        self,
        *,
        relative_path: str | None = None,
        domain: str | None = None,
        contains: str | None = None,
    ) -> list[BackupFileRecord]:
        """Find files by path/domain with optional substring matching."""

        results: list[BackupFileRecord] = []
        for record in self.iter_files():
            if domain and record.domain != domain:
                continue
            if relative_path and record.relative_path != relative_path:
                continue
            if contains and contains.lower() not in record.relative_path.lower():
                continue
            results.append(record)
        return results

    def extract_file(
        self,
        *,
        relative_path: str,
        output_dir: Path | str,
        domain: str | None = None,
        output_name: Optional[str] = None,
    ) -> Path | None:
        """Extract and decrypt a single file when present."""

        output_path = Path(output_dir).expanduser().resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        kwargs: dict[str, Any] = {
            "relativePath": relative_path,
            "targetFolder": str(output_path),
        }
        if domain:
            kwargs["domain"] = domain
        if output_name:
            kwargs["targetName"] = output_name

        result = self._backup.getFileDecryptedCopy(**kwargs)
        decrypted = result.get("decryptedFilePath") if result else None
        return Path(decrypted) if decrypted else None

    def close(self) -> None:
        self._backup.close()
