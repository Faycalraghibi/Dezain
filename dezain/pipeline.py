# Copyright © 2026 Dezain. All rights reserved.


from __future__ import annotations

import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from dezain.config import DezainConfig, load_config
from dezain.design_system.registry import ComponentRegistry
from dezain.figma.client import FigmaClient, load_sample_file
from dezain.figma.parser import parse_figma_file
from dezain.generator.orchestrator import LLMOrchestrator
from dezain.generator.types import GenerationResult
from dezain.generator.writer import generate_summary_report, write_generated_files
from dezain.validation.validator import validate_generated_code

logger = logging.getLogger(__name__)
console = Console()


def run_pipeline(
    config: DezainConfig | None = None,
    sample_mode: bool = False,
    file_url: str | None = None,
    frame_ids: list[str] | None = None,
    output_dir: Path | None = None,
    preview: bool = False,
) -> GenerationResult:
    """Run the full design-to-code pipeline.

    Args:
        config: Pipeline configuration. Loaded from defaults if None.
        sample_mode: If True, use sample data instead of Figma API.
        file_url: Override Figma file URL.
        frame_ids: Specific frame IDs to generate (optional).
        output_dir: Override output directory.
        preview: If True, scaffolds and launches a Vite preview server.

    Returns:
        GenerationResult with all generated files and status.
    """
    if config is None:
        overrides = {}
        if file_url:
            overrides["figma"] = {"file_url": file_url}
        if output_dir:
            overrides["output"] = {"directory": str(output_dir)}
        config = load_config(overrides=overrides if overrides else None)

    effective_output_dir = output_dir or config.output.directory

    console.print(Panel("🎨 [bold cyan]Dezain[/] — Design to Code", expand=False))

    console.print("\n[bold]Step 1:[/] Fetching design data...")
    if sample_mode:
        console.print("  → Using sample data (demo mode)")
        figma_file = load_sample_file()
    else:
        if not config.figma.token:
            console.print("[red]Error:[/] FIGMA_TOKEN not set. Use --sample for demo mode.")
            return GenerationResult(errors=["FIGMA_TOKEN not configured"])
        url = file_url or config.figma.file_url
        if not url:
            console.print("[red]Error:[/] No Figma file URL provided.")
            return GenerationResult(errors=["No Figma file URL"])
        client = FigmaClient(config.figma.token)
        file_key = FigmaClient.parse_file_url(url)
        figma_file = client.get_file(file_key)

    console.print(f"  ✓ Loaded design: [green]{figma_file.name}[/]")

    console.print("\n[bold]Step 2:[/] Parsing design to intermediate representation...")
    ir_design = parse_figma_file(figma_file, frame_ids=frame_ids)
    console.print(
        f"  ✓ Parsed [green]{len(ir_design.nodes)}[/] nodes, "
        f"[green]{len(ir_design.tokens)}[/] tokens"
    )

    console.print("\n[bold]Step 3:[/] Configuring design system...")
    registry = ComponentRegistry(config.component_mappings)
    console.print(f"  ✓ Registered [green]{len(config.component_mappings)}[/] component mappings")

    console.print("\n[bold]Step 4:[/] Generating React + TypeScript components...")
    orchestrator = LLMOrchestrator(config.llm, registry, console=console)
    result = orchestrator.generate_from_design(ir_design)
    console.print(
        f"  ✓ Generated [green]{len(result.files)}[/] files ({result.tokens_used} tokens used)"
    )

    if result.warnings:
        for w in result.warnings:
            console.print(f"  ⚠ {w}")

    if result.errors:
        for e in result.errors:
            console.print(f"  [red]✗ {e}[/]")
        return result

    console.print(f"\n[bold]Step 5:[/] Writing files to {effective_output_dir}...")
    written = write_generated_files(result.files, Path(effective_output_dir))
    console.print(f"  ✓ Wrote [green]{len(written)}[/] files")

    console.print("\n[bold]Step 6:[/] Validating generated code...")
    validation = validate_generated_code(Path(effective_output_dir))
    if validation.passed:
        console.print("  ✓ [green]All checks passed[/]")
    else:
        console.print(f"  ✗ [red]{validation.total_errors} errors found[/]")
        for err in validation.typescript_errors[:5]:
            console.print(f"    [red]{err}[/]")
        for err in validation.lint_errors[:5]:
            console.print(f"    [red]{err}[/]")

    report = generate_summary_report(
        result.files, result.warnings, result.errors, result.tokens_used, Path(effective_output_dir)
    )
    report_path = Path(effective_output_dir) / "GENERATION_REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    console.print(f"\n📋 Report saved to [cyan]{report_path}[/]")

    console.print(Panel("✅ [bold green]Generation complete![/]", expand=False))

    if preview:
        console.print("\n[bold]Step 7:[/] Launching preview server...")
        try:
            from dezain.preview.scaffold import create_preview_scaffold
            from dezain.preview.server import launch_preview

            preview_dir = create_preview_scaffold(Path(effective_output_dir), result.files)
            launch_preview(preview_dir, console)
        except Exception as e:
            console.print(f"[red]✗ Failed to launch preview server: {e}[/]")

    return result
