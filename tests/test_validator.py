# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from pathlib import Path

from dezain.validation.validator import validate_generated_code


class TestValidateGeneratedCode:
    """Tests for file-level validation."""

    def test_valid_tsx_passes(self, tmp_path: Path) -> None:
        """Should pass for valid .tsx files with exports."""
        comp_dir = tmp_path / "src" / "components"
        comp_dir.mkdir(parents=True)
        (comp_dir / "Button.tsx").write_text(
            'import React from "react";\n\n'
            "interface ButtonProps {\n"
            "  children: React.ReactNode;\n"
            "}\n\n"
            "export const Button: React.FC<ButtonProps> = ({ children }) => (\n"
            '  <button className="px-4 py-2 bg-blue-500">{children}</button>\n'
            ");\n"
        )
        result = validate_generated_code(tmp_path)
        assert result.passed is True
        assert result.total_errors == 0

    def test_empty_file_fails(self, tmp_path: Path) -> None:
        """Should fail for empty .tsx files."""
        (tmp_path / "Empty.tsx").write_text("")
        result = validate_generated_code(tmp_path)
        assert result.passed is False
        assert any("empty" in e.lower() for e in result.lint_errors)

    def test_missing_export_fails(self, tmp_path: Path) -> None:
        """Should warn about files with no exports."""
        (tmp_path / "NoExport.tsx").write_text("const Internal = () => <div>Hello</div>;\n")
        result = validate_generated_code(tmp_path)
        assert result.passed is False
        assert any("export" in e.lower() for e in result.lint_errors)

    def test_any_type_detected(self, tmp_path: Path) -> None:
        """Should flag usage of 'any' type."""
        (tmp_path / "BadTypes.tsx").write_text(
            "export const Foo = (props: any) => <div>{props.x}</div>;\n"
        )
        result = validate_generated_code(tmp_path)
        assert any("any" in e.lower() for e in result.lint_errors)

    def test_no_ts_files_warns(self, tmp_path: Path) -> None:
        """Should warn when output dir has no TypeScript files."""
        (tmp_path / "readme.md").write_text("# Hello")
        result = validate_generated_code(tmp_path)
        assert result.passed is True  # Not a failure, just a warning
        assert len(result.warnings) > 0
