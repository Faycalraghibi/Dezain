# Copyright © 2026 Dezain. All rights reserved.


from __future__ import annotations

import logging
from dataclasses import dataclass, field

from dezain.config import ComponentMapping

logger = logging.getLogger(__name__)


@dataclass
class ResolvedComponent:
    """Result of resolving a Figma component name to a React component."""

    react_component: str
    react_import: str
    props_mapping: dict[str, str] = field(default_factory=dict)
    is_fallback: bool = False


class ComponentRegistry:
    """Registry mapping Figma component names → React component info."""

    def __init__(self, mappings: list[ComponentMapping] | None = None) -> None:
        self._mappings: dict[str, ComponentMapping] = {}
        if mappings:
            for m in mappings:
                self._mappings[m.figma_name.lower()] = m

    def register(self, mapping: ComponentMapping) -> None:
        """Register a component mapping."""
        self._mappings[mapping.figma_name.lower()] = mapping

    def resolve(self, figma_name: str) -> ResolvedComponent:
        """Resolve a Figma component name to a React component.

        Lookup order:
        1. Exact match (case-insensitive)
        2. Partial match (Figma name contains or is contained by registered name)
        3. Fallback to generic <div> wrapper with warning

        Args:
            figma_name: The component name from Figma.

        Returns:
            ResolvedComponent with import and component info.
        """
        key = figma_name.lower()

        if key in self._mappings:
            m = self._mappings[key]
            return ResolvedComponent(
                react_component=m.react_component,
                react_import=m.react_import,
                props_mapping=m.props_mapping,
            )

        for registered_name, m in self._mappings.items():
            if registered_name in key or key in registered_name:
                logger.info(
                    "Partial match: '%s' → '%s' (via '%s')",
                    figma_name,
                    m.react_component,
                    m.figma_name,
                )
                return ResolvedComponent(
                    react_component=m.react_component,
                    react_import=m.react_import,
                    props_mapping=m.props_mapping,
                )

        logger.warning("No mapping found for '%s', falling back to generic wrapper", figma_name)
        safe_name = _to_pascal_case(figma_name)
        return ResolvedComponent(
            react_component=safe_name,
            react_import="",
            is_fallback=True,
        )

    def list_registered(self) -> list[str]:
        """Return all registered Figma component names."""
        return [m.figma_name for m in self._mappings.values()]


def _to_pascal_case(name: str) -> str:
    """Convert a string to PascalCase for React component naming."""
    cleaned = name.replace("-", " ").replace("_", " ").replace("/", " ")
    parts = cleaned.split()
    return "".join(word.capitalize() for word in parts) if parts else "UnknownComponent"
