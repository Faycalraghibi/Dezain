# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from dezain.ir import (
    IRColor,
    IRFont,
    IRSpacing,
    IRToken,
)


def color_to_tailwind(color: IRColor) -> str:
    """Convert an IR color to closest TailwindCSS color class.

    For exact colors, returns an arbitrary value like `bg-[#hex]`.
    """
    return f"[{color.to_hex()}]"


def font_to_tailwind_classes(font: IRFont) -> list[str]:
    """Convert IR font properties to TailwindCSS utility classes.

    Returns a list of classes for font-size, font-weight, etc.
    """
    classes: list[str] = []
    size_map = {
        12: "text-xs",
        14: "text-sm",
        16: "text-base",
        18: "text-lg",
        20: "text-xl",
        24: "text-2xl",
        30: "text-3xl",
        36: "text-4xl",
        48: "text-5xl",
        60: "text-6xl",
        72: "text-7xl",
        96: "text-8xl",
        128: "text-9xl",
    }
    closest_size = min(size_map.keys(), key=lambda s: abs(s - font.size))
    if abs(closest_size - font.size) <= 2:
        classes.append(size_map[closest_size])
    else:
        size_val = int(font.size) if font.size == int(font.size) else font.size
        classes.append(f"text-[{size_val}px]")

    weight_map = {
        100: "font-thin",
        200: "font-extralight",
        300: "font-light",
        400: "font-normal",
        500: "font-medium",
        600: "font-semibold",
        700: "font-bold",
        800: "font-extrabold",
        900: "font-black",
    }
    classes.append(weight_map.get(font.weight, f"font-[{font.weight}]"))

    align_map = {
        "left": "text-left",
        "center": "text-center",
        "right": "text-right",
        "justified": "text-justify",
    }
    if font.text_align != "left":
        classes.append(align_map.get(font.text_align, "text-left"))

    if font.line_height is not None and font.size > 0:
        ratio = font.line_height / font.size
        if abs(ratio - 1.0) < 0.1:
            classes.append("leading-none")
        elif abs(ratio - 1.25) < 0.1:
            classes.append("leading-tight")
        elif abs(ratio - 1.5) < 0.1:
            classes.append("leading-normal")
        elif abs(ratio - 1.75) < 0.1:
            classes.append("leading-relaxed")
        elif abs(ratio - 2.0) < 0.1:
            classes.append("leading-loose")
        else:
            classes.append(f"leading-[{font.line_height}px]")

    if font.letter_spacing is not None and font.letter_spacing != 0:
        classes.append(f"tracking-[{font.letter_spacing}px]")

    return classes


def spacing_to_tailwind(spacing: IRSpacing, prefix: str = "p") -> list[str]:
    """Convert IR spacing to TailwindCSS padding/margin classes.

    Args:
        spacing: The spacing values.
        prefix: 'p' for padding, 'm' for margin.

    Returns:
        List of Tailwind spacing classes.
    """
    classes: list[str] = []

    def _to_tw(value: float) -> str:
        scale = {0: "0", 4: "1", 8: "2", 12: "3", 16: "4", 20: "5", 24: "6", 32: "8", 40: "10"}
        closest = min(scale.keys(), key=lambda s: abs(s - value))
        if abs(closest - value) <= 1:
            return scale[closest]
        return f"[{value}px]"

    if spacing.top == spacing.right == spacing.bottom == spacing.left:
        if spacing.top > 0:
            classes.append(f"{prefix}-{_to_tw(spacing.top)}")
    elif spacing.top == spacing.bottom and spacing.left == spacing.right:
        if spacing.top > 0:
            classes.append(f"{prefix}y-{_to_tw(spacing.top)}")
        if spacing.left > 0:
            classes.append(f"{prefix}x-{_to_tw(spacing.left)}")
    else:
        if spacing.top > 0:
            classes.append(f"{prefix}t-{_to_tw(spacing.top)}")
        if spacing.right > 0:
            classes.append(f"{prefix}r-{_to_tw(spacing.right)}")
        if spacing.bottom > 0:
            classes.append(f"{prefix}b-{_to_tw(spacing.bottom)}")
        if spacing.left > 0:
            classes.append(f"{prefix}l-{_to_tw(spacing.left)}")

    return classes


def tokens_to_tailwind_config(tokens: list[IRToken]) -> dict[str, dict[str, str]]:
    """Convert IR tokens to a Tailwind config extend block.

    Returns a dict like:
    {
        "colors": {"primary": "#hex", ...},
        "spacing": {"sm": "4px", ...},
    }
    """
    config: dict[str, dict[str, str]] = {"colors": {}, "spacing": {}, "fontSize": {}}

    for token in tokens:
        name_slug = token.name.lower().replace(" ", "-").replace("/", "-")
        if token.category == "color" and isinstance(token.value, str):
            config["colors"][name_slug] = token.value
        elif token.category == "spacing":
            config["spacing"][name_slug] = f"{token.value}px"
        elif token.category == "font":
            config["fontSize"][name_slug] = f"{token.value}px"

    return {k: v for k, v in config.items() if v}
