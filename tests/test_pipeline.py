# Copyright © 2026 Dezain. All rights reserved.

from pathlib import Path
from unittest.mock import MagicMock, patch

from dezain.config import DezainConfig
from dezain.generator.types import GeneratedFile
from dezain.pipeline import run_pipeline


@patch("dezain.pipeline.generate_summary_report")
@patch("dezain.pipeline.validate_generated_code")
@patch("dezain.pipeline.write_generated_files")
@patch("dezain.pipeline.LLMOrchestrator")
@patch("dezain.pipeline.ComponentRegistry")
@patch("dezain.pipeline.parse_figma_file")
@patch("dezain.pipeline.load_sample_file")
def test_run_pipeline_sample_mode(
    mock_load_sample: MagicMock,
    mock_parse: MagicMock,
    mock_registry_cls: MagicMock,
    mock_orch_cls: MagicMock,
    mock_write: MagicMock,
    mock_validate: MagicMock,
    mock_report: MagicMock,
    tmp_path: Path,
) -> None:
    # Setup happy path mocks
    mock_figma_file = MagicMock()
    mock_figma_file.name = "Test File"
    mock_load_sample.return_value = mock_figma_file

    mock_ir_design = MagicMock()
    mock_ir_design.nodes = []
    mock_ir_design.tokens = []
    mock_parse.return_value = mock_ir_design

    mock_orch_instance = MagicMock()
    mock_gen_result = MagicMock()
    mock_gen_result.success = True
    mock_gen_result.files = [GeneratedFile(path="a.tsx", content="a")]
    mock_gen_result.warnings = []
    mock_gen_result.errors = []
    mock_gen_result.tokens_used = 100
    mock_orch_instance.generate_from_design.return_value = mock_gen_result
    mock_orch_cls.return_value = mock_orch_instance

    mock_write.return_value = [Path("a.tsx")]

    mock_val_result = MagicMock()
    mock_val_result.passed = True
    mock_validate.return_value = mock_val_result

    mock_report.return_value = "Test Report"

    # Execution
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    result = run_pipeline(sample_mode=True, output_dir=out_dir)

    # Assert basic flow
    assert result == mock_gen_result
    mock_load_sample.assert_called_once()
    mock_parse.assert_called_once_with(mock_figma_file, frame_ids=None)
    mock_orch_instance.generate_from_design.assert_called_once_with(mock_ir_design)
    mock_write.assert_called_once_with(mock_gen_result.files, out_dir)
    mock_validate.assert_called_once_with(out_dir)
    mock_report.assert_called_once()

    # Assert report was written
    assert (out_dir / "GENERATION_REPORT.md").exists()
    assert (out_dir / "GENERATION_REPORT.md").read_text() == "Test Report"


@patch("dezain.pipeline.generate_summary_report")
@patch("dezain.pipeline.validate_generated_code")
@patch("dezain.pipeline.write_generated_files")
@patch("dezain.pipeline.LLMOrchestrator")
@patch("dezain.pipeline.ComponentRegistry")
@patch("dezain.pipeline.parse_figma_file")
@patch("dezain.pipeline.FigmaClient")
def test_run_pipeline_figma_url(
    mock_client_cls: MagicMock,
    mock_parse: MagicMock,
    mock_registry_cls: MagicMock,
    mock_orch_cls: MagicMock,
    mock_write: MagicMock,
    mock_validate: MagicMock,
    mock_report: MagicMock,
    tmp_path: Path,
) -> None:
    # Setup happy path Figma mock
    mock_client_instance = MagicMock()
    mock_figma_file = MagicMock()
    mock_client_instance.get_file.return_value = mock_figma_file
    mock_client_cls.return_value = mock_client_instance
    mock_client_cls.parse_file_url.return_value = "file_key123"

    mock_orch_instance = MagicMock()
    mock_gen_result = MagicMock()
    mock_gen_result.warnings = ["Test warning"]
    mock_gen_result.errors = []
    mock_orch_instance.generate_from_design.return_value = mock_gen_result
    mock_orch_cls.return_value = mock_orch_instance

    mock_val_result = MagicMock()
    mock_val_result.passed = False
    mock_val_result.total_errors = 1
    mock_val_result.typescript_errors = ["ts error"]
    mock_val_result.lint_errors = ["lint error"]
    mock_validate.return_value = mock_val_result

    mock_report.return_value = "Test Report"
    tmp_path.mkdir(parents=True, exist_ok=True)

    # Provide a minimal config with token
    config = DezainConfig()
    config.figma.token = "fake_token"

    result = run_pipeline(
        config=config, sample_mode=False, file_url="https://figma.com/file/key", output_dir=tmp_path
    )

    assert result == mock_gen_result
    mock_client_cls.assert_called_once_with("fake_token")
    mock_client_instance.get_file.assert_called_once_with("file_key123")


def test_run_pipeline_missing_token() -> None:
    config = DezainConfig()
    config.figma.token = ""  # Missing token

    result = run_pipeline(config=config, sample_mode=False)

    assert not result.success
    assert "FIGMA_TOKEN not configured" in result.errors[0]


def test_run_pipeline_missing_url() -> None:
    config = DezainConfig()
    config.figma.token = "valid_token"
    config.figma.file_url = ""  # Missing url

    result = run_pipeline(config=config, sample_mode=False, file_url=None)

    assert not result.success
    assert "No Figma file URL" in result.errors[0]


@patch("dezain.pipeline.generate_summary_report")
@patch("dezain.pipeline.validate_generated_code")
@patch("dezain.pipeline.write_generated_files")
@patch("dezain.pipeline.LLMOrchestrator")
@patch("dezain.pipeline.parse_figma_file")
@patch("dezain.pipeline.load_sample_file")
@patch("dezain.preview.scaffold.create_preview_scaffold")
@patch("dezain.preview.server.launch_preview")
def test_run_pipeline_preview_flag(
    mock_launch: MagicMock,
    mock_scaffold: MagicMock,
    mock_load: MagicMock,
    mock_parse: MagicMock,
    mock_orch_cls: MagicMock,
    mock_write: MagicMock,
    mock_validate: MagicMock,
    mock_report: MagicMock,
    tmp_path: Path,
) -> None:
    # Setup mock success path
    mock_orch_instance = MagicMock()
    mock_gen_result = MagicMock()
    mock_gen_result.errors = []
    mock_orch_instance.generate_from_design.return_value = mock_gen_result
    mock_orch_cls.return_value = mock_orch_instance

    mock_preview_dir = Path("/mock/preview")
    mock_scaffold.return_value = mock_preview_dir

    mock_report.return_value = "Test Report"
    tmp_path.mkdir(parents=True, exist_ok=True)

    run_pipeline(sample_mode=True, output_dir=tmp_path, preview=True)

    # Assert preview logic was triggered
    mock_scaffold.assert_called_once()
    mock_launch.assert_called_once()
    assert mock_launch.call_args[0][0] == mock_preview_dir


@patch("dezain.pipeline.generate_summary_report")
@patch("dezain.pipeline.validate_generated_code")
@patch("dezain.pipeline.write_generated_files")
@patch("dezain.pipeline.LLMOrchestrator")
@patch("dezain.pipeline.parse_figma_file")
@patch("dezain.pipeline.load_sample_file")
def test_run_pipeline_llm_fails(
    mock_load: MagicMock,
    mock_parse: MagicMock,
    mock_orch_cls: MagicMock,
    mock_write: MagicMock,
    mock_validate: MagicMock,
    mock_report: MagicMock,
    tmp_path: Path,
) -> None:
    # Setup mock failure path
    mock_orch_instance = MagicMock()
    mock_gen_result = MagicMock()
    mock_gen_result.errors = ["LLM error"]
    mock_orch_instance.generate_from_design.return_value = mock_gen_result
    mock_orch_cls.return_value = mock_orch_instance

    result = run_pipeline(sample_mode=True, output_dir=tmp_path)

    # Assert it stops early if generated files throws error
    assert result == mock_gen_result
    mock_write.assert_not_called()
    mock_validate.assert_not_called()
    mock_report.assert_not_called()
