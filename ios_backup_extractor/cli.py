"""Command-line interface for the modular iOS backup extractor."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from ios_backup_extractor.backup.adapter import IOSBackupAdapter
from ios_backup_extractor.device.acquisition import Pymobiledevice3Acquirer
from ios_backup_extractor.plugins.manager import PluginManager
from ios_backup_extractor.reports.json_report import write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ios-backup-extractor",
        description="Acquire iOS backups with pymobiledevice3 and run modular artifact plugins.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    devices = subcommands.add_parser("devices", help="List connected devices visible to pymobiledevice3.")
    devices.add_argument("--pymobiledevice3-bin", default="pymobiledevice3")

    acquire = subcommands.add_parser("acquire", help="Create a local device backup using pymobiledevice3.")
    acquire.add_argument("--output", required=True, help="Backup output directory.")
    acquire.add_argument("--udid", help="Target device UDID.")
    acquire.add_argument("--password", help="Backup password for encrypted backups.")
    acquire.add_argument("--unencrypted", action="store_true", help="Request an unencrypted backup.")
    acquire.add_argument("--full", action="store_true", help="Request a full backup when supported.")
    acquire.add_argument("--pymobiledevice3-bin", default="pymobiledevice3")

    extract = subcommands.add_parser("extract", help="Run artifact plugins against an existing backup.")
    extract.add_argument("--udid", required=True, help="Backup UDID/folder name.")
    extract.add_argument("--backup-root", help="Folder containing MobileSync backup folders.")
    extract.add_argument("--output", required=True, help="Extraction output directory.")
    extract.add_argument("--password", help="Cleartext backup password.")
    extract.add_argument("--derived-key", help="Previously derived backup decryption key.")
    extract.add_argument("--plugin", action="append", dest="plugins", help="Plugin name to run. Repeatable.")

    run = subcommands.add_parser("run", help="Acquire then immediately run artifact plugins.")
    run.add_argument("--backup-output", required=True, help="Backup output directory.")
    run.add_argument("--extract-output", required=True, help="Extraction output directory.")
    run.add_argument("--udid", required=True, help="Target device UDID.")
    run.add_argument("--password", help="Backup password for encrypted backups.")
    run.add_argument("--derived-key", help="Previously derived backup decryption key for extraction.")
    run.add_argument("--unencrypted", action="store_true", help="Request an unencrypted backup.")
    run.add_argument("--full", action="store_true", help="Request a full backup when supported.")
    run.add_argument("--plugin", action="append", dest="plugins", help="Plugin name to run. Repeatable.")
    run.add_argument("--pymobiledevice3-bin", default="pymobiledevice3")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "devices":
        acquirer = Pymobiledevice3Acquirer(args.pymobiledevice3_bin)
        for device in acquirer.list_devices():
            print(device.udid)
        return 0

    if args.command == "acquire":
        acquirer = Pymobiledevice3Acquirer(args.pymobiledevice3_bin)
        backup_path = acquirer.backup(
            Path(args.output),
            udid=args.udid,
            encrypted=not args.unencrypted,
            password=args.password,
            force_full=args.full,
        )
        print(f"Backup written to {backup_path}")
        return 0

    if args.command == "extract":
        return _extract(
            udid=args.udid,
            backup_root=args.backup_root,
            output=args.output,
            password=args.password,
            derived_key=args.derived_key,
            plugins=args.plugins,
        )

    if args.command == "run":
        acquirer = Pymobiledevice3Acquirer(args.pymobiledevice3_bin)
        acquirer.backup(
            Path(args.backup_output),
            udid=args.udid,
            encrypted=not args.unencrypted,
            password=args.password,
            force_full=args.full,
        )
        return _extract(
            udid=args.udid,
            backup_root=args.backup_output,
            output=args.extract_output,
            password=args.password,
            derived_key=args.derived_key,
            plugins=args.plugins,
        )

    return 2


def _extract(
    *,
    udid: str,
    backup_root: str | None,
    output: str,
    password: str | None,
    derived_key: str | None,
    plugins: list[str] | None,
) -> int:
    output_path = Path(output).expanduser().resolve()
    backup = IOSBackupAdapter(
        udid=udid,
        backup_root=backup_root,
        password=password,
        derived_key=derived_key,
    )
    try:
        manager = PluginManager()
        manager.discover()
        results = manager.run(backup, output_path / "artifacts", plugins)
        report = write_report(results, output_path)
    finally:
        backup.close()

    print(f"Report written to {report}")
    for result in results:
        print(f"[{result.status}] {result.plugin}: {result.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
