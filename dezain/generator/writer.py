# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

import logging
from pathlib import Path

from dezain.generator.types import GeneratedFile

logger = logging.getLogger(__name__)


def write_generated_files(
    files: list[GeneratedFile],
    output_dir: Path,
    overwrite: bool = True,
) -> list[Path]:
    """Write generated files to the output directory.

    Args:
        files: List of generated file objects.
        output_dir: Root output directory.
        overwrite: Whether to overwrite existing files.

    Returns:
        List of paths that were written.
    """
    written: list[Path] = []

    for file in files:
        file_path = output_dir / file.path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists() and not overwrite:
            logger.warning("Skipping existing file: %s", file_path)
            continue

        file_path.write_text(file.content, encoding="utf-8")
        logger.info("Wrote: %s", file_path)
        written.append(file_path)

    return written


def generate_summary_report(
    files: list[GeneratedFile],
    warnings: list[str],
    errors: list[str],
    tokens_used: int,
    output_dir: Path,
) -> str:
    """Generate a human-readable summary report.

    Args:
        files: Generated files.
        warnings: Any warnings from generation.
        errors: Any errors from generation.
        tokens_used: Total LLM tokens consumed.
        output_dir: Where files were written.

    Returns:
        Formatted report string.
    """
    lines = [
        "# Dezain Generation Report",
        "",
        f"**Output directory:** `{output_dir}`",
        f"**Files generated:** {len(files)}",
        f"**LLM tokens used:** {tokens_used}",
        "",
    ]

    if files:
        lines.append("## Generated Files")
        lines.append("")
        for f in files:
            desc = f" — {f.description}" if f.description else ""
            lines.append(f"- `{f.path}`{desc}")
        lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    if errors:
        lines.append("## Errors")
        lines.append("")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")

    if not errors:
        lines.append("## Status: Success")
    else:
        lines.append("## Status: Failed")

    return "\n".join(lines)
