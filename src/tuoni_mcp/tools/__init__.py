from __future__ import annotations

from collections.abc import Callable
from types import ModuleType
from typing import Any

from tuoni_mcp.config import Profile, Settings
from tuoni_mcp.registry import ToolRegistry, collect_decorated_module
from tuoni_mcp.tools import (
    agents,
    aliases,
    api_spec,
    command_history,
    commands,
    diagnostics,
    discovery,
    events,
    files,
    jobs,
    listeners,
    payloads,
    plugins,
    raw,
    settings as settings_tools,
    users,
)

# The default agent-ops profile uses explicit ToolSpec providers.
FIRST_PARTY_PROVIDERS = (agents, commands, command_history, events, diagnostics, api_spec)

# Optional profiles declare decorated handlers, which the collector converts
# directly into ToolSpecs without retaining FastMCP Tool objects.
DECORATED_PROFILE_MODULES: tuple[
    tuple[ModuleType, frozenset[Profile], frozenset[str]], ...
] = (
    (listeners, frozenset({Profile.ACCESS}), frozenset()),
    (payloads, frozenset({Profile.ACCESS}), frozenset()),
    (files, frozenset({Profile.ARTIFACTS}), frozenset()),
    (discovery, frozenset({Profile.DISCOVERY}), frozenset()),
    (users, frozenset({Profile.ADMINISTRATION}), frozenset()),
    (jobs, frozenset({Profile.ADMINISTRATION}), frozenset()),
    (settings_tools, frozenset({Profile.ADMINISTRATION}), frozenset()),
    (plugins, frozenset({Profile.AUTHORING}), frozenset()),
    (aliases, frozenset({Profile.AUTHORING}), frozenset()),
    # A method-dependent raw request cannot truthfully be annotated read-only.
    # Treat the entire escape hatch as mutating so read-only mode removes it.
    (raw, frozenset({Profile.RAW}), frozenset({"tuoni_raw_request"})),
)


def _register_provider(module: ModuleType, registry: ToolRegistry, cfg: Settings) -> None:
    provider: Callable[[ToolRegistry, Settings], Any] | None = getattr(
        module, "register_specs", None
    )
    if provider is not None:
        provider(registry, cfg)


def build_registry(cfg: Settings) -> ToolRegistry:
    registry = ToolRegistry()
    for module in FIRST_PARTY_PROVIDERS:
        _register_provider(module, registry, cfg)
    for module, profiles, force_mutating in DECORATED_PROFILE_MODULES:
        collect_decorated_module(
            registry,
            module,
            cfg,
            profiles=profiles,
            force_mutating=force_mutating,
        )
    return registry
