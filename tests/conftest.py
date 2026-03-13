# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from pathlib import Path

import pytest

from dezain.config import ComponentMapping, DezainConfig, FigmaConfig, LLMConfig, OutputConfig
from dezain.figma.types import (
    FigmaColor,
    FigmaFile,
    FigmaNode,
    FigmaPaint,
    FigmaTypeStyle,
)
from dezain.ir import (
    IRColor,
    IRDesign,
    IRFont,
    IRLayout,
    IRNode,
    IRSize,
    IRSpacing,
    IRStyles,
    IRToken,
    LayoutMode,
    NodeType,
)


@pytest.fixture
def sample_ir_node() -> IRNode:
    """A simple IR node representing a styled button."""
    return IRNode(
        id="node-1",
        name="PrimaryButton",
        type=NodeType.COMPONENT,
        children=[
            IRNode(
                id="node-1-text",
                name="Label",
                type=NodeType.TEXT,
                text_content="Click Me",
                styles=IRStyles(
                    foreground=IRColor(r=1.0, g=1.0, b=1.0),
                    font=IRFont(family="Inter", size=16, weight=600),
                ),
            )
        ],
        styles=IRStyles(
            background=IRColor(r=0.39, g=0.4, b=0.95),
            padding=IRSpacing(top=12, right=24, bottom=12, left=24),
        ),
        layout=IRLayout(mode=LayoutMode.HORIZONTAL, gap=8, align_items="center"),
        size=IRSize(width=200, height=48),
        component_name="PrimaryButton",
    )


@pytest.fixture
def sample_ir_design(sample_ir_node: IRNode) -> IRDesign:
    """A simple IR design with one button component."""
    return IRDesign(
        name="Sample Design",
        page_name="Page 1",
        nodes=[sample_ir_node],
        tokens=[
            IRToken(name="Primary", category="color", value="#6366f1"),
            IRToken(name="Body", category="font", value="16px"),
        ],
    )


@pytest.fixture
def sample_figma_node() -> FigmaNode:
    """A Figma node representing a button frame."""
    return FigmaNode(
        id="1:2",
        name="Button",
        type="FRAME",
        fills=[FigmaPaint(type="SOLID", color=FigmaColor(r=0.39, g=0.4, b=0.95))],
        layoutMode="HORIZONTAL",
        itemSpacing=8,
        paddingTop=12,
        paddingRight=24,
        paddingBottom=12,
        paddingLeft=24,
        cornerRadius=8,
        absoluteBoundingBox={"x": 0, "y": 0, "width": 200, "height": 48},
        children=[
            FigmaNode(
                id="1:3",
                name="Label",
                type="TEXT",
                characters="Click Me",
                style=FigmaTypeStyle(
                    fontFamily="Inter",
                    fontSize=16,
                    fontWeight=600,
                ),
                fills=[FigmaPaint(type="SOLID", color=FigmaColor(r=1.0, g=1.0, b=1.0))],
            )
        ],
    )


@pytest.fixture
def sample_figma_file(sample_figma_node: FigmaNode) -> FigmaFile:
    """A minimal Figma file with one page and one button."""
    return FigmaFile(
        name="Test Design",
        document=FigmaNode(
            id="0:0",
            name="Document",
            type="DOCUMENT",
            children=[
                FigmaNode(
                    id="0:1",
                    name="Page 1",
                    type="CANVAS",
                    children=[sample_figma_node],
                )
            ],
        ),
        styles={
            "style-1": {"name": "Primary", "styleType": "FILL"},
            "style-2": {"name": "Heading", "styleType": "TEXT"},
        },
    )


@pytest.fixture
def sample_figma_json(sample_figma_file: FigmaFile) -> str:
    """Sample Figma file as raw JSON string."""
    return sample_figma_file.model_dump_json(indent=2)


@pytest.fixture
def sample_config() -> DezainConfig:
    """A test config with sample values."""
    return DezainConfig(
        figma=FigmaConfig(token="test-token", file_url="https://figma.com/file/ABC/Test"),
        llm=LLMConfig(provider="openai", openai_api_key="test-key"),
        output=OutputConfig(directory=Path("./test-output")),
        component_mappings=[
            ComponentMapping(
                figma_name="Button",
                react_import="@/components/Button",
                react_component="Button",
                props_mapping={"label": "children"},
            ),
            ComponentMapping(
                figma_name="Input",
                react_import="@/components/Input",
                react_component="Input",
            ),
        ],
    )
