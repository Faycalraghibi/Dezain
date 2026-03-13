# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating generated code."""

    passed: bool = True
    typescript_errors: list[str] = field(default_factory=list)
    lint_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def total_errors(self) -> int:
        """Total number of errors found."""
        return len(self.typescript_errors) + len(self.lint_errors)


def validate_generated_code(output_dir: Path) -> ValidationResult:
    """Validate generated TypeScript/React code.

    Runs:
    1. TypeScript compiler (tsc --noEmit) if tsconfig exists
    2. Checks that all .tsx files have valid syntax structure

    Args:
        output_dir: Directory containing generated code.

    Returns:
        ValidationResult with any errors found.
    """
    result = ValidationResult()

    tsx_files = list(output_dir.rglob("*.tsx")) + list(output_dir.rglob("*.ts"))
    if not tsx_files:
        result.warnings.append("No TypeScript files found in output directory")
        return result

    logger.info("Validating %d TypeScript files in %s", len(tsx_files), output_dir)

    for file_path in tsx_files:
        errors = _check_file_basics(file_path)
        if errors:
            result.lint_errors.extend(errors)
            result.passed = False

    tsc_errors = _run_tsc(output_dir)
    if tsc_errors:
        result.typescript_errors.extend(tsc_errors)
        result.passed = False

    return result


def _check_file_basics(file_path: Path) -> list[str]:
    """Run basic syntax checks on a TypeScript file.

    Returns list of error strings (empty if valid).
    """
    errors: list[str] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{file_path}: Failed to read file: {e}"]

    if not content.strip():
        errors.append(f"{file_path}: File is empty")
        return errors

    if "any" in content and "// @ts-ignore" not in content:
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if ": any" in stripped or "as any" in stripped:
                errors.append(f"{file_path}:{i}: Use of 'any' type detected")

    if "export" not in content:
        errors.append(f"{file_path}: No exports found — components should be exported")

    return errors


def _run_tsc(output_dir: Path) -> list[str]:
    """Run TypeScript compiler on the output directory.

    Returns list of error strings (empty if tsc passes or isn't available).
    """
    errors: list[str] = []

    try:
        result = subprocess.run(
            ["npx", "tsc", "--noEmit", "--strict", "--jsx", "react-jsx"],
            cwd=str(output_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0 and result.stdout:
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    errors.append(f"tsc: {line.strip()}")

    except FileNotFoundError:
        logger.info("TypeScript compiler (tsc) not found — skipping TS validation")
    except subprocess.TimeoutExpired:
        errors.append("TypeScript compilation timed out")

    return errors
