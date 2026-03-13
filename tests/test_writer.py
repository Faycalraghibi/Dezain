# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from pathlib import Path

from dezain.generator.types import GeneratedFile
from dezain.generator.writer import generate_summary_report, write_generated_files


class TestWriteGeneratedFiles:
    """Tests for write_generated_files."""

    def test_writes_single_file(self, tmp_path: Path) -> None:
        """Should write a single file to the output directory."""
        files = [
            GeneratedFile(
                path="src/components/Button.tsx",
                content="export const Button = () => <button>Click</button>;\n",
            )
        ]
        written = write_generated_files(files, tmp_path)
        assert len(written) == 1
        assert (tmp_path / "src" / "components" / "Button.tsx").exists()

    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        """Should create parent directories automatically."""
        files = [GeneratedFile(path="deep/nested/dir/File.tsx", content="export default {};")]
        write_generated_files(files, tmp_path)
        assert (tmp_path / "deep" / "nested" / "dir" / "File.tsx").exists()

    def test_skip_existing_when_no_overwrite(self, tmp_path: Path) -> None:
        """Should skip existing files when overwrite is False."""
        # Create existing file
        file_path = tmp_path / "existing.tsx"
        file_path.write_text("original content")

        files = [GeneratedFile(path="existing.tsx", content="new content")]
        written = write_generated_files(files, tmp_path, overwrite=False)

        assert len(written) == 0
        assert file_path.read_text() == "original content"

    def test_overwrites_when_flag_set(self, tmp_path: Path) -> None:
        """Should overwrite existing files when overwrite is True."""
        file_path = tmp_path / "existing.tsx"
        file_path.write_text("original content")

        files = [GeneratedFile(path="existing.tsx", content="new content")]
        written = write_generated_files(files, tmp_path, overwrite=True)

        assert len(written) == 1
        assert file_path.read_text() == "new content"


class TestSummaryReport:
    """Tests for summary report generation."""

    def test_success_report(self) -> None:
        """Should generate a success report."""
        files = [GeneratedFile(path="Button.tsx", content="")]
        report = generate_summary_report(files, [], [], 150, Path("./out"))
        assert "Success" in report
        assert "1" in report  # 1 file
        assert "150" in report  # tokens

    def test_error_report(self) -> None:
        """Should generate a failure report with errors."""
        report = generate_summary_report([], [], ["Something broke"], 0, Path("./out"))
        assert "Failed" in report
        assert "Something broke" in report

    def test_warning_report(self) -> None:
        """Should include warnings in report."""
        files = [GeneratedFile(path="A.tsx", content="")]
        report = generate_summary_report(files, ["Minor issue"], [], 50, Path("./out"))
        assert "Warning" in report
        assert "Minor issue" in report
