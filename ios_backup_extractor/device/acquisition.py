"""Device backup acquisition helpers.

The implementation prefers pymobiledevice3's public Python APIs when available
and falls back to its CLI. The fallback keeps this framework usable while
pymobiledevice3 internals continue to evolve.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
from typing import Iterable, Optional


class AcquisitionError(RuntimeError):
    """Raised when a device acquisition step fails."""


@dataclass(frozen=True)
class DeviceSummary:
    """Minimal connected-device metadata used by the CLI and reports."""

    udid: str
    name: Optional[str] = None
    product_type: Optional[str] = None
    product_version: Optional[str] = None
    serial_number: Optional[str] = None


class Pymobiledevice3Acquirer:
    """Acquire iOS backups using pymobiledevice3.

    Parameters
    ----------
    pymobiledevice3_bin:
        Optional explicit path to the pymobiledevice3 CLI executable.
    """

    def __init__(self, pymobiledevice3_bin: str = "pymobiledevice3") -> None:
        self.pymobiledevice3_bin = pymobiledevice3_bin

    def assert_available(self) -> None:
        """Validate that pymobiledevice3 is installed and callable."""

        if shutil.which(self.pymobiledevice3_bin) is None:
            raise AcquisitionError(
                f"{self.pymobiledevice3_bin!r} was not found on PATH. "
                "Install pymobiledevice3 or pass an explicit executable path."
            )

    def list_devices(self) -> list[DeviceSummary]:
        """Return connected devices.

        This uses the CLI because pymobiledevice3 has changed Python API entry
        points across releases. Output formats are intentionally parsed
        conservatively; richer discovery can be added as a future integration.
        """

        self.assert_available()
        result = self._run(["usbmux", "list"], check=False)
        devices: list[DeviceSummary] = []

        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or "udid" in line.lower() or line.startswith("-"):
                continue
            parts = line.replace("|", " ").split()
            udid = next((part for part in parts if len(part) >= 24 and "-" in part), None)
            if udid:
                devices.append(DeviceSummary(udid=udid))

        return devices

    def backup(
        self,
        output_dir: Path | str,
        *,
        udid: Optional[str] = None,
        encrypted: bool = True,
        password: Optional[str] = None,
        force_full: bool = False,
    ) -> Path:
        """Create an iOS backup and return the output directory.

        The command is intentionally explicit and minimally destructive. It does
        not attempt passcode bypass, lock-state bypass, or any unauthorized
        acquisition path. The connected device must already be paired/trusted.
        """

        self.assert_available()
        output_path = Path(output_dir).expanduser().resolve()
        output_path.mkdir(parents=True, exist_ok=True)

        args = [self.pymobiledevice3_bin]
        if udid:
            args.extend(["--udid", udid])
        args.extend(["backup2", "backup", str(output_path)])

        if encrypted:
            args.append("--encrypt")
            if password:
                args.extend(["--password", password])
        if force_full:
            args.append("--full")

        self._run(args, check=True, already_prefixed=True)
        return output_path

    def _run(
        self,
        args: Iterable[str],
        *,
        check: bool,
        already_prefixed: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        command = list(args) if already_prefixed else [self.pymobiledevice3_bin, *args]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if check and result.returncode != 0:
            raise AcquisitionError(
                "Command failed: "
                + " ".join(command)
                + f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result
