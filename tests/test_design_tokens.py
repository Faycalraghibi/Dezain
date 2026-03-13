"""Tests for design token extraction and Tailwind mapping."""

from __future__ import annotations

from dezain.design_system.tokens import (
    color_to_tailwind,
    font_to_tailwind_classes,
    spacing_to_tailwind,
    tokens_to_tailwind_config,
)
from dezain.ir import IRColor, IRFont, IRSpacing, IRToken


class TestColorToTailwind:
    """Tests for color → Tailwind class conversion."""

    def test_solid_color(self) -> None:
        """Should produce hex arbitrary value."""
        color = IRColor(r=1.0, g=0.0, b=0.0)
        result = color_to_tailwind(color)
        assert result == "[#ff0000]"

    def test_color_with_alpha(self) -> None:
        """Should include alpha in hex for transparent colors."""
        color = IRColor(r=0.0, g=0.0, b=0.0, a=0.5)
        result = color_to_tailwind(color)
        assert result == "[#0000007f]"


class TestFontToTailwind:
    """Tests for font → Tailwind classes conversion."""

    def test_standard_size(self) -> None:
        """Should map 16px to text-base."""
        font = IRFont(size=16, weight=400)
        classes = font_to_tailwind_classes(font)
        assert "text-base" in classes

    def test_bold_weight(self) -> None:
        """Should map weight 700 to font-bold."""
        font = IRFont(size=16, weight=700)
        classes = font_to_tailwind_classes(font)
        assert "font-bold" in classes

    def test_custom_size_uses_arbitrary(self) -> None:
        """Should use arbitrary value for non-standard sizes."""
        font = IRFont(size=27, weight=400)
        classes = font_to_tailwind_classes(font)
        assert "text-[27px]" in classes

    def test_center_alignment(self) -> None:
        """Should add text-center for centered text."""
        font = IRFont(size=16, weight=400, text_align="center")
        classes = font_to_tailwind_classes(font)
        assert "text-center" in classes

    def test_left_alignment_omitted(self) -> None:
        """Should not add text-left (it's the default)."""
        font = IRFont(size=16, weight=400, text_align="left")
        classes = font_to_tailwind_classes(font)
        assert "text-left" not in classes


class TestSpacingToTailwind:
    """Tests for spacing → Tailwind padding/margin classes."""

    def test_uniform_padding(self) -> None:
        """Should use p-X for uniform padding."""
        spacing = IRSpacing(top=16, right=16, bottom=16, left=16)
        classes = spacing_to_tailwind(spacing, "p")
        assert classes == ["p-4"]

    def test_symmetric_padding(self) -> None:
        """Should use px/py for symmetric padding."""
        spacing = IRSpacing(top=8, right=16, bottom=8, left=16)
        classes = spacing_to_tailwind(spacing, "p")
        assert "py-2" in classes
        assert "px-4" in classes

    def test_individual_padding(self) -> None:
        """Should use pt/pr/pb/pl for asymmetric padding."""
        spacing = IRSpacing(top=4, right=8, bottom=12, left=16)
        classes = spacing_to_tailwind(spacing, "p")
        assert "pt-1" in classes
        assert "pr-2" in classes
        assert "pb-3" in classes
        assert "pl-4" in classes

    def test_zero_padding_omitted(self) -> None:
        """Should produce empty list for zero padding."""
        spacing = IRSpacing(top=0, right=0, bottom=0, left=0)
        classes = spacing_to_tailwind(spacing, "p")
        assert classes == []


class TestTokensToTailwindConfig:
    """Tests for tokens → Tailwind config extend."""

    def test_color_tokens(self) -> None:
        """Should map color tokens to colors config."""
        tokens = [IRToken(name="Primary", category="color", value="#6366f1")]
        config = tokens_to_tailwind_config(tokens)
        assert "colors" in config
        assert config["colors"]["primary"] == "#6366f1"

    def test_empty_categories_excluded(self) -> None:
        """Should exclude empty categories from config."""
        tokens = [IRToken(name="Primary", category="color", value="#6366f1")]
        config = tokens_to_tailwind_config(tokens)
        assert "spacing" not in config
