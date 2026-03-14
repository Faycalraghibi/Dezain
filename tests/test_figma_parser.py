# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from dezain.figma.parser import parse_figma_file, parse_figma_node
from dezain.figma.types import FigmaFile, FigmaNode
from dezain.ir import LayoutMode, NodeType


class TestParseFigmaNode:
    """Tests for single node parsing."""

    def test_parses_frame_type(self, sample_figma_node: FigmaNode) -> None:
        """Should map FRAME to NodeType.FRAME."""
        ir = parse_figma_node(sample_figma_node)
        assert ir.type == NodeType.FRAME

    def test_preserves_name(self, sample_figma_node: FigmaNode) -> None:
        """Should preserve the node name."""
        ir = parse_figma_node(sample_figma_node)
        assert ir.name == "Button"

    def test_preserves_id(self, sample_figma_node: FigmaNode) -> None:
        """Should preserve the node ID."""
        ir = parse_figma_node(sample_figma_node)
        assert ir.id == "1:2"

    def test_extracts_children(self, sample_figma_node: FigmaNode) -> None:
        """Should recursively parse children."""
        ir = parse_figma_node(sample_figma_node)
        assert len(ir.children) == 1
        assert ir.children[0].type == NodeType.TEXT
        assert ir.children[0].text_content == "Click Me"

    def test_extracts_background_color(self, sample_figma_node: FigmaNode) -> None:
        """Should extract background from fills."""
        ir = parse_figma_node(sample_figma_node)
        assert ir.styles.background is not None
        assert abs(ir.styles.background.r - 0.39) < 0.01

    def test_extracts_layout_mode(self, sample_figma_node: FigmaNode) -> None:
        """Should extract horizontal auto-layout."""
        ir = parse_figma_node(sample_figma_node)
        assert ir.layout.mode == LayoutMode.HORIZONTAL
        assert ir.layout.gap == 8

    def test_extracts_padding(self, sample_figma_node: FigmaNode) -> None:
        """Should extract padding from Figma padding props."""
        ir = parse_figma_node(sample_figma_node)
        assert ir.styles.padding.top == 12
        assert ir.styles.padding.right == 24

    def test_extracts_border_radius(self, sample_figma_node: FigmaNode) -> None:
        """Should extract corner radius as border radius."""
        ir = parse_figma_node(sample_figma_node)
        assert ir.styles.border.radius == 8

    def test_extracts_size(self, sample_figma_node: FigmaNode) -> None:
        """Should extract width and height from bounding box."""
        ir = parse_figma_node(sample_figma_node)
        assert ir.size.width == 200
        assert ir.size.height == 48

    def test_hidden_node_becomes_unknown(self) -> None:
        """Should mark invisible nodes as UNKNOWN."""
        hidden_node = FigmaNode(id="x", name="Hidden", type="FRAME", visible=False)
        ir = parse_figma_node(hidden_node)
        assert ir.type == NodeType.UNKNOWN
        assert ir.metadata.get("hidden") is True

    def test_text_node_extracts_font(self, sample_figma_node: FigmaNode) -> None:
        """Should extract font properties from text nodes."""
        ir = parse_figma_node(sample_figma_node)
        text_node = ir.children[0]
        assert text_node.styles.font is not None
        assert text_node.styles.font.family == "Inter"
        assert text_node.styles.font.size == 16
        assert text_node.styles.font.weight == 600


class TestParseFigmaFile:
    """Tests for full file parsing."""

    def test_parses_file_name(self, sample_figma_file: FigmaFile) -> None:
        """Should extract file name."""
        design = parse_figma_file(sample_figma_file)
        assert design.name == "Test Design"

    def test_parses_page_name(self, sample_figma_file: FigmaFile) -> None:
        """Should extract page name from first canvas."""
        design = parse_figma_file(sample_figma_file)
        assert design.page_name == "Page 1"

    def test_parses_nodes(self, sample_figma_file: FigmaFile) -> None:
        """Should parse top-level nodes from the canvas."""
        design = parse_figma_file(sample_figma_file)
        assert len(design.nodes) == 1
        assert design.nodes[0].name == "Button"

    def test_extracts_tokens(self, sample_figma_file: FigmaFile) -> None:
        """Should extract design tokens from file styles."""
        design = parse_figma_file(sample_figma_file)
        assert len(design.tokens) == 2
        categories = {t.category for t in design.tokens}
        assert "color" in categories
        assert "font" in categories

    def test_parses_file_with_frame_ids(self) -> None:
        """Should filter and parse only requested frame IDs."""
        node1 = FigmaNode(id="1:1", name="Frame 1", type="FRAME")
        node2 = FigmaNode(id="2:2", name="Frame 2", type="FRAME")
        node3 = FigmaNode(
            id="3:3",
            name="Frame 3",
            type="FRAME",
            children=[FigmaNode(id="3:4", name="Inner", type="RECTANGLE")],
        )
        canvas = FigmaNode(id="0:0", name="Canvas", type="CANVAS", children=[node1, node2, node3])
        doc = FigmaNode(id="doc", name="Doc", type="DOCUMENT", children=[canvas])
        figma_file = FigmaFile(name="Test", document=doc, components={}, styles={})

        # Only request 2:2 and 3:4 (a nested node)
        design = parse_figma_file(figma_file, frame_ids=["2:2", "3:4"])

        assert len(design.nodes) == 2
        # Check that we found exactly the requested nodes
        names = {n.name for n in design.nodes}
        assert "Frame 2" in names
        assert "Inner" in names
        assert "Frame 1" not in names
