"""Discovery and execution for artifact plugins."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
import pkgutil
from typing import Iterable

from .base import ArtifactPlugin, PluginResult


class PluginManager:
    """Loads built-in plugins and runs selected artifact processors."""

    def __init__(self, package: str = "ios_backup_extractor.plugins") -> None:
        self.package = package
        self._plugins: list[ArtifactPlugin] = []

    @property
    def plugins(self) -> list[ArtifactPlugin]:
        return list(self._plugins)

    def discover(self) -> list[ArtifactPlugin]:
        """Discover built-in plugin modules exposing a ``Plugin`` class."""

        package_module = import_module(self.package)
        package_path = getattr(package_module, "__path__", None)
        if package_path is None:
            return []

        discovered: list[ArtifactPlugin] = []
        for module_info in pkgutil.iter_modules(package_path):
            if module_info.name.startswith("_") or module_info.name in {"base", "manager"}:
                continue
            module = import_module(f"{self.package}.{module_info.name}")
            plugin_cls = getattr(module, "Plugin", None)
            if plugin_cls is not None:
                discovered.append(plugin_cls())

        self._plugins = discovered
        return self.plugins

    def selected(self, names: Iterable[str] | None = None) -> list[ArtifactPlugin]:
        """Return discovered plugins filtered by name."""

        if not self._plugins:
            self.discover()
        if not names:
            return self.plugins
        wanted = {name.lower() for name in names}
        return [plugin for plugin in self._plugins if plugin.name.lower() in wanted]

    def run(self, backup, output_dir: Path, names: Iterable[str] | None = None) -> list[PluginResult]:
        """Run supported plugins and collect results."""

        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[PluginResult] = []
        for plugin in self.selected(names):
            plugin_output = output_dir / plugin.name
            plugin_output.mkdir(parents=True, exist_ok=True)
            try:
                if not plugin.supports(backup):
                    results.append(
                        PluginResult(
                            plugin=plugin.name,
                            status="skipped",
                            summary="Plugin did not find matching source artifacts.",
                        )
                    )
                    continue
                results.append(plugin.process(backup, plugin_output))
            except Exception as exc:  # pragma: no cover - plugin containment
                results.append(
                    PluginResult(
                        plugin=plugin.name,
                        status="error",
                        summary="Plugin failed during processing.",
                        errors=[str(exc)],
                    )
                )
        return results
