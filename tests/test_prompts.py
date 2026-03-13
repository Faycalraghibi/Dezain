# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from dezain.generator.prompts import (
    SYSTEM_PROMPT,
    build_component_prompt,
    build_page_prompt,
)
from dezain.ir import IRDesign, IRNode


class TestSystemPrompt:
    """Tests for the system prompt."""

    def test_mentions_react(self) -> None:
        """System prompt should mention React."""
        assert "React" in SYSTEM_PROMPT

    def test_mentions_typescript(self) -> None:
        """System prompt should mention TypeScript."""
        assert "TypeScript" in SYSTEM_PROMPT

    def test_mentions_tailwind(self) -> None:
        """System prompt should mention TailwindCSS."""
        assert "TailwindCSS" in SYSTEM_PROMPT

    def test_mentions_json_output(self) -> None:
        """System prompt should mention JSON output format."""
        assert "JSON" in SYSTEM_PROMPT


class TestComponentPrompt:
    """Tests for component prompt building."""

    def test_includes_node_data(self, sample_ir_node: IRNode) -> None:
        """Prompt should include the serialized node data."""
        prompt = build_component_prompt(sample_ir_node)
        assert "PrimaryButton" in prompt
        assert "DESIGN NODE" in prompt

    def test_includes_ds_components(self, sample_ir_node: IRNode) -> None:
        """Prompt should list available design system components."""
        prompt = build_component_prompt(sample_ir_node, design_system_components=["Button", "Card"])
        assert "Button" in prompt
        assert "Card" in prompt
        assert "DESIGN SYSTEM COMPONENTS" in prompt

    def test_without_ds_components(self, sample_ir_node: IRNode) -> None:
        """Prompt should work without design system components."""
        prompt = build_component_prompt(sample_ir_node)
        assert "DESIGN SYSTEM COMPONENTS" not in prompt

    def test_includes_parent_context(self, sample_ir_node: IRNode) -> None:
        """Prompt should include parent context when provided."""
        prompt = build_component_prompt(sample_ir_node, parent_context="Inside a Card")
        assert "Inside a Card" in prompt


class TestPagePrompt:
    """Tests for page prompt building."""

    def test_includes_design_name(self, sample_ir_design: IRDesign) -> None:
        """Prompt should include the design name."""
        prompt = build_page_prompt(sample_ir_design)
        assert "Sample Design" in prompt

    def test_includes_tokens(self, sample_ir_design: IRDesign) -> None:
        """Prompt should list design tokens."""
        prompt = build_page_prompt(sample_ir_design)
        assert "Primary" in prompt
        assert "DESIGN TOKENS" in prompt

    def test_asks_for_index_file(self, sample_ir_design: IRDesign) -> None:
        """Prompt should request barrel file generation."""
        prompt = build_page_prompt(sample_ir_design)
        assert "index.ts" in prompt
