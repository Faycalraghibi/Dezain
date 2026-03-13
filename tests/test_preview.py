# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from rich.console import Console

from dezain.generator.types import GeneratedFile
from dezain.preview.scaffold import create_preview_scaffold
from dezain.preview.server import launch_preview


def test_create_preview_scaffold(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated"
    output_dir.mkdir()

    files = [
        GeneratedFile(
            path="src/components/Button.tsx",
            content="export const Button = () => <button/>",
        ),
        GeneratedFile(
            path="src/components/Card.tsx",
            content="export const Card = () => <div/>",
        ),
        # Should ignore an index file
        GeneratedFile(path="src/components/index.ts", content="export * from './Button'"),
    ]

    preview_dir = create_preview_scaffold(output_dir, files)

    # Check directory was created at the right place
    assert preview_dir.name == "generated-preview"
    assert preview_dir.parent == tmp_path

    # Check essential files
    assert (preview_dir / "package.json").exists()
    assert (preview_dir / "vite.config.ts").exists()
    assert (preview_dir / "tailwind.config.js").exists()

    # Check App.tsx imports
    app_tsx = (preview_dir / "src" / "App.tsx").read_text(encoding="utf-8")
    assert "import { Button } from './components/Button'" in app_tsx
    assert "import { Card } from './components/Card'" in app_tsx
    assert "<Button />" in app_tsx
    assert "<Card />" in app_tsx
    assert "import { index } from" not in app_tsx  # Should have skipped index.ts


@patch("dezain.preview.server.subprocess.Popen")
@patch("dezain.preview.server.subprocess.run")
@patch("dezain.preview.server.time")
def test_launch_preview(mock_time: MagicMock, mock_run: MagicMock, mock_popen: MagicMock) -> None:
    console = Console(force_terminal=False)
    preview_dir = Path("/mock/preview")

    mock_process = MagicMock()
    mock_process.poll.return_value = None  # Process is running
    mock_popen.return_value = mock_process

    launch_preview(preview_dir, console)

    # Should perform npm install
    mock_run.assert_called_once()
    run_args = mock_run.call_args[0][0]
    assert "install" in run_args
    assert mock_run.call_args[1]["cwd"] == preview_dir

    # Should launch dev server
    mock_popen.assert_called_once()
    popen_args = mock_popen.call_args[0][0]
    assert "run" in popen_args
    assert "dev" in popen_args
    assert mock_popen.call_args[1]["cwd"] == preview_dir

    # Should block waiting for process to end
    mock_process.wait.assert_called_once()


@patch("dezain.preview.server.subprocess.Popen")
@patch("dezain.preview.server.subprocess.run")
def test_launch_preview_install_fails(mock_run: MagicMock, mock_popen: MagicMock) -> None:
    console = Console(force_terminal=False)
    preview_dir = Path("/mock/preview")

    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=["npm", "install"], stderr="error"
    )

    launch_preview(preview_dir, console)

    # Popen should not be called if install fails
    mock_popen.assert_not_called()
