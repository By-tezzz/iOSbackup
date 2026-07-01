# pymobiledevice3 Extractor Framework

This branch adds an acquisition and plugin layer on top of the existing `iOSbackup` encrypted-backup reader.

## Baseline

The existing project already handles local iTunes/Finder-style backup parsing, including `Manifest.db` access and decrypted file copies. The new framework keeps that code intact and wraps it with:

- a `pymobiledevice3` acquisition command wrapper,
- a stable backup adapter for plugins,
- a plugin discovery and execution system,
- reusable SQLite and plist parser utilities,
- JSON reporting,
- initial artifact plugins for KnowledgeC, device messages, call history, Biome candidates, and plist artifacts.

## CLI

```bash
# List connected devices visible to pymobiledevice3
ios-backup-extractor devices

# Acquire a backup from a trusted, paired device
ios-backup-extractor acquire \
  --udid <DEVICE_UDID> \
  --output ./case-backups \
  --password '<BACKUP_PASSWORD>'

# Run all built-in plugins against an existing backup
ios-backup-extractor extract \
  --udid <DEVICE_UDID> \
  --backup-root ./case-backups \
  --output ./case-output \
  --password '<BACKUP_PASSWORD>'

# Acquire and extract in one run
ios-backup-extractor run \
  --udid <DEVICE_UDID> \
  --backup-output ./case-backups \
  --extract-output ./case-output \
  --password '<BACKUP_PASSWORD>'
```

## Parser utilities

### SQLite

`ios_backup_extractor.parsers.SQLiteParser` provides:

- read-only SQLite connections,
- table discovery,
- schema inspection,
- safe table export to JSON and CSV,
- SELECT-only query helper,
- byte normalization to hexadecimal strings.

Artifact-specific helpers currently include:

- `parse_call_history()`
- `parse_messages()`
- `parse_knowledgec()`

These helpers export raw tables and create best-effort normalized JSON outputs when the expected tables exist.

### Plist

`ios_backup_extractor.parsers.PlistParser` provides:

- XML and binary plist parsing through `plistlib`,
- normalized JSON export,
- ISO-formatted date values,
- hexadecimal byte values.

The `plists` plugin extracts plist candidates and writes parsed JSON copies under plugin output.

## Plugin contract

Each plugin exposes a `Plugin` class with:

```python
name = "artifact_name"
description = "What this plugin does."

def supports(self, backup) -> bool:
    ...

def process(self, backup, output_dir):
    ...
```

Plugins return `PluginResult` objects so future report writers can consume the same normalized result shape.

## Future integration points

- ALEAPP/iLEAPP handoff
- MVT handoff
- SQLite timeline normalization
- gzip/NSKeyedArchive helpers
- WAL and freelist recovery modules
- richer Biome decoders
- case metadata and chain-of-custody report fields
- GUI/API front end
