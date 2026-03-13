# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from dezain.config import ComponentMapping
from dezain.design_system.registry import ComponentRegistry


class TestComponentRegistry:
    """Tests for ComponentRegistry."""

    def test_exact_match(self) -> None:
        """Should resolve exact case-insensitive match."""
        registry = ComponentRegistry(
            [
                ComponentMapping(
                    figma_name="Button",
                    react_import="@/components/Button",
                    react_component="Button",
                )
            ]
        )
        result = registry.resolve("Button")
        assert result.react_component == "Button"
        assert result.react_import == "@/components/Button"
        assert result.is_fallback is False

    def test_case_insensitive_match(self) -> None:
        """Should match regardless of case."""
        registry = ComponentRegistry(
            [
                ComponentMapping(
                    figma_name="Button",
                    react_import="@/components/Button",
                    react_component="Button",
                )
            ]
        )
        result = registry.resolve("button")
        assert result.react_component == "Button"
        assert result.is_fallback is False

    def test_partial_match(self) -> None:
        """Should match when registered name is contained in query."""
        registry = ComponentRegistry(
            [
                ComponentMapping(
                    figma_name="Button",
                    react_import="@/components/Button",
                    react_component="Button",
                )
            ]
        )
        result = registry.resolve("Primary Button Large")
        assert result.react_component == "Button"
        assert result.is_fallback is False

    def test_fallback_for_unknown(self) -> None:
        """Should return fallback with PascalCase name for unregistered components."""
        registry = ComponentRegistry()
        result = registry.resolve("fancy-card")
        assert result.react_component == "FancyCard"
        assert result.is_fallback is True
        assert result.react_import == ""

    def test_register_and_resolve(self) -> None:
        """Should resolve components added via register()."""
        registry = ComponentRegistry()
        registry.register(
            ComponentMapping(
                figma_name="Modal",
                react_import="@/components/Modal",
                react_component="Modal",
            )
        )
        result = registry.resolve("Modal")
        assert result.react_component == "Modal"
        assert result.is_fallback is False

    def test_list_registered(self) -> None:
        """Should list all registered Figma component names."""
        registry = ComponentRegistry(
            [
                ComponentMapping(
                    figma_name="Button",
                    react_import="",
                    react_component="Button",
                ),
                ComponentMapping(
                    figma_name="Card",
                    react_import="",
                    react_component="Card",
                ),
            ]
        )
        names = registry.list_registered()
        assert "Button" in names
        assert "Card" in names

    def test_props_mapping_preserved(self) -> None:
        """Should preserve props mapping from config."""
        registry = ComponentRegistry(
            [
                ComponentMapping(
                    figma_name="Button",
                    react_import="@/components/Button",
                    react_component="Button",
                    props_mapping={"label": "children"},
                )
            ]
        )
        result = registry.resolve("Button")
        assert result.props_mapping == {"label": "children"}
