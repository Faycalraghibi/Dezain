# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class FigmaNodeType(StrEnum):
    """Figma node type identifiers."""

    DOCUMENT = "DOCUMENT"
    CANVAS = "CANVAS"
    FRAME = "FRAME"
    GROUP = "GROUP"
    COMPONENT = "COMPONENT"
    COMPONENT_SET = "COMPONENT_SET"
    INSTANCE = "INSTANCE"
    TEXT = "TEXT"
    RECTANGLE = "RECTANGLE"
    ELLIPSE = "ELLIPSE"
    VECTOR = "VECTOR"
    LINE = "LINE"
    BOOLEAN_OPERATION = "BOOLEAN_OPERATION"
    SECTION = "SECTION"
    STAR = "STAR"
    REGULAR_POLYGON = "REGULAR_POLYGON"


class FigmaColor(BaseModel):
    """Figma RGBA color."""

    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    a: float = 1.0


class FigmaPaint(BaseModel):
    """Figma paint (fill or stroke)."""

    type: str = "SOLID"
    color: FigmaColor | None = None
    opacity: float = 1.0
    visible: bool = True


class FigmaTypeStyle(BaseModel):
    """Figma text style properties."""

    fontFamily: str = "Inter"  # noqa: N815
    fontSize: float = 16.0  # noqa: N815
    fontWeight: int = 400  # noqa: N815
    lineHeightPx: float | None = None  # noqa: N815
    letterSpacing: float | None = None  # noqa: N815
    textAlignHorizontal: str = "LEFT"  # noqa: N815


class FigmaLayoutMode(StrEnum):
    """Figma auto-layout mode."""

    NONE = "NONE"
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"


class FigmaEffect(BaseModel):
    """Figma visual effect (shadow, blur, etc.)."""

    type: str = "DROP_SHADOW"
    visible: bool = True
    color: FigmaColor = Field(default_factory=FigmaColor)
    offset: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    radius: float = 0.0
    spread: float = 0.0


class FigmaNode(BaseModel):
    """A node in the Figma document tree."""

    id: str
    name: str
    type: str
    children: list[FigmaNode] = Field(default_factory=list)

    fills: list[FigmaPaint] = Field(default_factory=list)
    strokes: list[FigmaPaint] = Field(default_factory=list)
    effects: list[FigmaEffect] = Field(default_factory=list)
    opacity: float = 1.0
    visible: bool = True
    clipsContent: bool = False  # noqa: N815

    absoluteBoundingBox: dict[str, float] | None = None  # noqa: N815
    size: dict[str, float] | None = None

    layoutMode: str | None = None  # noqa: N815
    primaryAxisAlignItems: str | None = None  # noqa: N815
    counterAxisAlignItems: str | None = None  # noqa: N815
    itemSpacing: float | None = None  # noqa: N815
    paddingTop: float = 0  # noqa: N815
    paddingRight: float = 0  # noqa: N815
    paddingBottom: float = 0  # noqa: N815
    paddingLeft: float = 0  # noqa: N815

    characters: str | None = None
    style: FigmaTypeStyle | None = None

    componentId: str | None = None  # noqa: N815

    cornerRadius: float | None = None  # noqa: N815

    strokeWeight: float | None = None  # noqa: N815

    extraData: dict[str, Any] = Field(default_factory=dict)  # noqa: N815


class FigmaFile(BaseModel):
    """Top-level Figma file response."""

    name: str
    document: FigmaNode
    components: dict[str, Any] = Field(default_factory=dict)
    styles: dict[str, Any] = Field(default_factory=dict)
