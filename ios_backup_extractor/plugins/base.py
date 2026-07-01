"""Plugin contracts for artifact extraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class PluginResult:
    """Structured result returned by an artifact plugin."""

    plugin: str
    status: str
    summary: str
    artifacts: list[Path] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class ArtifactPlugin(Protocol):
    """Protocol every artifact plugin should implement."""

    name: str
    description: str

    def supports(self, backup: Any) -> bool:
        """Return True when this plugin can process the supplied backup."""

    def process(self, backup: Any, output_dir: Path) -> PluginResult:
        """Process the backup and write plugin output under output_dir."""
