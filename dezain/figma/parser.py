# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from dezain.figma.types import (
    FigmaFile,
    FigmaNode,
    FigmaNodeType,
)
from dezain.ir import (
    IRBorder,
    IRColor,
    IRDesign,
    IRFont,
    IRLayout,
    IRNode,
    IRShadow,
    IRSize,
    IRSpacing,
    IRStyles,
    IRToken,
    LayoutMode,
    NodeType,
)

# Mapping from Figma node types to IR node types
_NODE_TYPE_MAP: dict[str, NodeType] = {
    FigmaNodeType.FRAME.value: NodeType.FRAME,
    FigmaNodeType.GROUP.value: NodeType.GROUP,
    FigmaNodeType.COMPONENT.value: NodeType.COMPONENT,
    FigmaNodeType.COMPONENT_SET.value: NodeType.COMPONENT,
    FigmaNodeType.INSTANCE.value: NodeType.INSTANCE,
    FigmaNodeType.TEXT.value: NodeType.TEXT,
    FigmaNodeType.RECTANGLE.value: NodeType.RECTANGLE,
    FigmaNodeType.ELLIPSE.value: NodeType.ELLIPSE,
    FigmaNodeType.VECTOR.value: NodeType.VECTOR,
    FigmaNodeType.LINE.value: NodeType.VECTOR,
    FigmaNodeType.STAR.value: NodeType.VECTOR,
    FigmaNodeType.REGULAR_POLYGON.value: NodeType.VECTOR,
    FigmaNodeType.BOOLEAN_OPERATION.value: NodeType.VECTOR,
    FigmaNodeType.SECTION.value: NodeType.FRAME,
}


def parse_figma_file(figma_file: FigmaFile) -> IRDesign:
    """Parse a full Figma file into an IRDesign.

    Args:
        figma_file: Parsed Figma file response.

    Returns:
        Normalized IRDesign with all nodes and extracted tokens.
    """
    tokens: list[IRToken] = []
    nodes: list[IRNode] = []

    # The document root contains canvas (page) children
    for canvas in figma_file.document.children:
        for child in canvas.children:
            ir_node = _convert_node(child)
            nodes.append(ir_node)

    # Extract tokens from file styles
    tokens.extend(_extract_tokens_from_file(figma_file))

    return IRDesign(
        name=figma_file.name,
        page_name=figma_file.document.children[0].name if figma_file.document.children else "",
        nodes=nodes,
        tokens=tokens,
    )


def parse_figma_node(figma_node: FigmaNode) -> IRNode:
    """Parse a single Figma node into an IRNode.

    Args:
        figma_node: A Figma node.

    Returns:
        Normalized IRNode.
    """
    return _convert_node(figma_node)


def _convert_node(node: FigmaNode) -> IRNode:
    """Recursively convert a FigmaNode to an IRNode."""
    if not node.visible:
        return IRNode(
            id=node.id,
            name=node.name,
            type=NodeType.UNKNOWN,
            metadata={"hidden": True},
        )

    ir_type = _NODE_TYPE_MAP.get(node.type, NodeType.UNKNOWN)

    children = [_convert_node(child) for child in node.children]

    return IRNode(
        id=node.id,
        name=node.name,
        type=ir_type,
        children=children,
        styles=_extract_styles(node),
        layout=_extract_layout(node),
        size=_extract_size(node),
        text_content=node.characters,
        component_name=node.name if ir_type in (NodeType.COMPONENT, NodeType.INSTANCE) else None,
    )


def _extract_styles(node: FigmaNode) -> IRStyles:
    """Extract visual styles from a Figma node."""
    background: IRColor | None = None
    foreground: IRColor | None = None

    # Background from fills
    for fill in node.fills:
        if fill.visible and fill.color:
            background = IRColor(
                r=fill.color.r,
                g=fill.color.g,
                b=fill.color.b,
                a=fill.color.a * fill.opacity,
            )
            break  # Use first visible fill

    # Foreground (text color) from style
    if node.style and node.fills:
        for fill in node.fills:
            if fill.visible and fill.color:
                foreground = IRColor(
                    r=fill.color.r,
                    g=fill.color.g,
                    b=fill.color.b,
                    a=fill.color.a * fill.opacity,
                )
                break

    # Font
    font: IRFont | None = None
    if node.style:
        s = node.style
        font = IRFont(
            family=s.fontFamily,
            size=s.fontSize,
            weight=s.fontWeight,
            line_height=s.lineHeightPx,
            letter_spacing=s.letterSpacing,
            text_align=s.textAlignHorizontal.lower(),
        )

    # Padding
    padding = IRSpacing(
        top=node.paddingTop,
        right=node.paddingRight,
        bottom=node.paddingBottom,
        left=node.paddingLeft,
    )

    # Border
    border_color: IRColor | None = None
    for stroke in node.strokes:
        if stroke.visible and stroke.color:
            border_color = IRColor(
                r=stroke.color.r,
                g=stroke.color.g,
                b=stroke.color.b,
                a=stroke.color.a * stroke.opacity,
            )
            break

    border = IRBorder(
        width=node.strokeWeight or 0,
        color=border_color,
        radius=node.cornerRadius or 0,
    )

    # Shadows
    shadows: list[IRShadow] = []
    for effect in node.effects:
        if effect.visible and effect.type == "DROP_SHADOW":
            shadows.append(
                IRShadow(
                    offset_x=effect.offset.get("x", 0),
                    offset_y=effect.offset.get("y", 0),
                    blur=effect.radius,
                    spread=effect.spread,
                    color=IRColor(
                        r=effect.color.r,
                        g=effect.color.g,
                        b=effect.color.b,
                        a=effect.color.a,
                    ),
                )
            )

    return IRStyles(
        background=background,
        foreground=foreground,
        font=font,
        padding=padding,
        border=border,
        shadows=shadows,
        opacity=node.opacity,
        overflow_hidden=node.clipsContent,
    )


def _extract_layout(node: FigmaNode) -> IRLayout:
    """Extract layout properties from a Figma node."""
    mode = LayoutMode.NONE
    if node.layoutMode:
        mode_map = {
            "HORIZONTAL": LayoutMode.HORIZONTAL,
            "VERTICAL": LayoutMode.VERTICAL,
        }
        mode = mode_map.get(node.layoutMode, LayoutMode.NONE)

    align_items = "start"
    if node.counterAxisAlignItems:
        align_map = {"MIN": "start", "CENTER": "center", "MAX": "end"}
        align_items = align_map.get(node.counterAxisAlignItems, "start")

    justify_content = "start"
    if node.primaryAxisAlignItems:
        justify_map = {
            "MIN": "start",
            "CENTER": "center",
            "MAX": "end",
            "SPACE_BETWEEN": "space-between",
        }
        justify_content = justify_map.get(node.primaryAxisAlignItems, "start")

    return IRLayout(
        mode=mode,
        gap=node.itemSpacing or 0,
        align_items=align_items,
        justify_content=justify_content,
    )


def _extract_size(node: FigmaNode) -> IRSize:
    """Extract size from a Figma node."""
    width: float | None = None
    height: float | None = None

    if node.absoluteBoundingBox:
        width = node.absoluteBoundingBox.get("width")
        height = node.absoluteBoundingBox.get("height")
    elif node.size:
        width = node.size.get("x") or node.size.get("width")
        height = node.size.get("y") or node.size.get("height")

    return IRSize(width=width, height=height)


def _extract_tokens_from_file(figma_file: FigmaFile) -> list[IRToken]:
    """Extract design tokens from file-level styles."""
    tokens: list[IRToken] = []

    for style_id, style_info in figma_file.styles.items():
        style_type = style_info.get("styleType", "")
        name = style_info.get("name", style_id)

        if style_type == "FILL":
            tokens.append(
                IRToken(name=name, category="color", value=style_id, description=f"Color: {name}")
            )
        elif style_type == "TEXT":
            tokens.append(
                IRToken(
                    name=name, category="font", value=style_id, description=f"Typography: {name}"
                )
            )
        elif style_type == "EFFECT":
            tokens.append(
                IRToken(name=name, category="shadow", value=style_id, description=f"Effect: {name}")
            )

    return tokens
