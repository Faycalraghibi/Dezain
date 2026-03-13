"""Intermediate Representation (IR) models.

These Pydantic models bridge Figma design data and code generation.
They provide a normalized, provider-agnostic representation of the design.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class LayoutMode(StrEnum):
    """How child nodes are laid out."""

    NONE = "none"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    GRID = "grid"
    ABSOLUTE = "absolute"


class NodeType(StrEnum):
    """Type of design node."""

    FRAME = "frame"
    GROUP = "group"
    COMPONENT = "component"
    INSTANCE = "instance"
    TEXT = "text"
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    VECTOR = "vector"
    IMAGE = "image"
    UNKNOWN = "unknown"


class IRColor(BaseModel):
    """RGBA color value."""

    r: float = Field(ge=0, le=1)
    g: float = Field(ge=0, le=1)
    b: float = Field(ge=0, le=1)
    a: float = Field(default=1.0, ge=0, le=1)

    def to_hex(self) -> str:
        """Convert to hex string."""
        r = int(self.r * 255)
        g = int(self.g * 255)
        b = int(self.b * 255)
        if self.a < 1.0:
            a = int(self.a * 255)
            return f"#{r:02x}{g:02x}{b:02x}{a:02x}"
        return f"#{r:02x}{g:02x}{b:02x}"


class IRFont(BaseModel):
    """Typography properties."""

    family: str = "Inter"
    size: float = 16.0
    weight: int = 400
    line_height: float | None = None
    letter_spacing: float | None = None
    text_align: str = "left"


class IRSpacing(BaseModel):
    """Padding / margin values."""

    top: float = 0
    right: float = 0
    bottom: float = 0
    left: float = 0


class IRBorder(BaseModel):
    """Border properties."""

    width: float = 0
    color: IRColor | None = None
    radius: float = 0


class IRShadow(BaseModel):
    """Box shadow properties."""

    offset_x: float = 0
    offset_y: float = 0
    blur: float = 0
    spread: float = 0
    color: IRColor = Field(default_factory=lambda: IRColor(r=0, g=0, b=0, a=0.25))


class IRStyles(BaseModel):
    """Visual styles applied to a node."""

    background: IRColor | None = None
    foreground: IRColor | None = None
    font: IRFont | None = None
    padding: IRSpacing = Field(default_factory=IRSpacing)
    border: IRBorder = Field(default_factory=IRBorder)
    shadows: list[IRShadow] = Field(default_factory=list)
    opacity: float = 1.0
    overflow_hidden: bool = False


class IRLayout(BaseModel):
    """Layout properties of a node."""

    mode: LayoutMode = LayoutMode.NONE
    gap: float = 0
    align_items: str = "start"
    justify_content: str = "start"
    wrap: bool = False


class IRSize(BaseModel):
    """Dimensions of a node."""

    width: float | None = None
    height: float | None = None
    min_width: float | None = None
    min_height: float | None = None
    max_width: float | None = None
    max_height: float | None = None


class IRNode(BaseModel):
    """A single node in the design tree."""

    id: str
    name: str
    type: NodeType
    children: list[IRNode] = Field(default_factory=list)
    styles: IRStyles = Field(default_factory=IRStyles)
    layout: IRLayout = Field(default_factory=IRLayout)
    size: IRSize = Field(default_factory=IRSize)
    text_content: str | None = None
    component_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IRToken(BaseModel):
    """A design token (color, spacing, font, etc.)."""

    name: str
    category: str  # "color", "spacing", "font", "shadow", "border-radius"
    value: Any
    description: str = ""


class IRDesign(BaseModel):
    """Top-level design container — the full output of the parser."""

    name: str
    page_name: str = ""
    nodes: list[IRNode] = Field(default_factory=list)
    tokens: list[IRToken] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
