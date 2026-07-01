"""Artifact plugin framework."""

from .base import ArtifactPlugin, PluginResult
from .manager import PluginManager

__all__ = ["ArtifactPlugin", "PluginManager", "PluginResult"]
