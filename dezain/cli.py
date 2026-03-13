# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(
    name="dezain",
    help="🎨 AI-powered Figma design → React + TypeScript code generator",
    add_completion=False,
)
console = Console()


@app.command()
def generate(
    file_url: str | None = typer.Option(  # noqa: UP007
        None,
        "--file-url",
        "-f",
        help="Figma file URL to process",
    ),
    frame: str | None = typer.Option(  # noqa: UP007
        None,
        "--frame",
        help="Specific Figma frame/node ID to generate",
    ),
    output: Path = typer.Option(  # noqa: B008
        Path("./generated"),
        "--output",
        "-o",
        help="Output directory for generated components",
    ),
    sample: bool = typer.Option(
        False,
        "--sample",
        "-s",
        help="Use bundled sample data (demo mode, no Figma token needed)",
    ),
    config_file: Path | None = typer.Option(  # noqa: B008
        None,
        "--config",
        "-c",
        help="Path to dezain.config.yaml",
    ),
) -> None:
    """Generate React + TypeScript components from a Figma design."""
    from dezain.config import load_config
    from dezain.pipeline import run_pipeline

    config = load_config(config_path=config_file)

    result = run_pipeline(
        config=config,
        sample_mode=sample,
        file_url=file_url,
        frame_id=frame,
        output_dir=output,
    )

    if not result.success:
        raise typer.Exit(code=1)


@app.command()
def init(
    output: Path = typer.Option(  # noqa: B008
        Path("."),
        "--output",
        "-o",
        help="Directory to create config file in",
    ),
) -> None:
    """Initialize a dezain.config.yaml configuration file."""
    config_path = output / "dezain.config.yaml"

    if config_path.exists():
        console.print(f"[yellow]Config already exists:[/] {config_path}")
        raise typer.Exit(code=1)

    template = """# Dezain Configuration
# See: https://github.com/Faycal/Dezain

# Component mappings: Figma component name → React component
component_mappings:
  - figma_name: "Button"
    react_import: "@/components/ui/Button"
    react_component: "Button"
    props_mapping:
      label: "children"

  - figma_name: "Input"
    react_import: "@/components/ui/Input"
    react_component: "Input"
    props_mapping:
      placeholder: "placeholder"

# Design token overrides (extend or override extracted tokens)
design_tokens_overrides:
  colors:
    primary: "#6366f1"
    secondary: "#8b5cf6"
  spacing:
    sm: "4px"
    md: "8px"
    lg: "16px"

# Output preferences
output:
  directory: "./generated"
  tailwind_version: 3
"""

    config_path.write_text(template, encoding="utf-8")
    console.print(f"✅ Created config: [cyan]{config_path}[/]")
    console.print("Edit this file to configure your design system mappings.")


if __name__ == "__main__":
    app()
