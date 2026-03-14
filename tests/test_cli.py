# Copyright © 2026 Dezain. All rights reserved.

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from dezain.cli import app

runner = CliRunner()


@patch("dezain.pipeline.run_pipeline")
def test_cli_generate_success(mock_run_pipeline: MagicMock, tmp_path: Path) -> None:
    # Setup mock
    mock_result = MagicMock()
    mock_result.success = True
    mock_run_pipeline.return_value = mock_result

    out_dir = tmp_path / "out"

    result = runner.invoke(app, ["generate", "--sample", "--preview", "-o", str(out_dir)])

    # Assert
    assert result.exit_code == 0
    mock_run_pipeline.assert_called_once()

    call_kwargs = mock_run_pipeline.call_args.kwargs
    assert call_kwargs["sample_mode"] is True
    assert call_kwargs["preview"] is True
    assert call_kwargs["output_dir"] == out_dir


@patch("dezain.pipeline.run_pipeline")
def test_cli_generate_failure(mock_run_pipeline: MagicMock) -> None:
    mock_result = MagicMock()
    mock_result.success = False
    mock_run_pipeline.return_value = mock_result

    result = runner.invoke(app, ["generate", "--sample"])

    # Assert CLI exits with 1 if pipeline fails
    assert result.exit_code == 1


def test_cli_init_success(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "-o", str(tmp_path)])

    assert result.exit_code == 0
    assert "Created config" in result.stdout
    assert (tmp_path / "dezain.config.yaml").exists()


def test_cli_init_exists(tmp_path: Path) -> None:
    # Pre-create config
    config_path = tmp_path / "dezain.config.yaml"
    config_path.write_text("existing", encoding="utf-8")

    result = runner.invoke(app, ["init", "-o", str(tmp_path)])

    # Assert it fails because config already exists
    assert result.exit_code == 1
    assert "Config already exists" in result.stdout
