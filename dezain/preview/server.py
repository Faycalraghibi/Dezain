# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

import logging
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

logger = logging.getLogger(__name__)


def launch_preview(preview_dir: Path, console: Console) -> None:
    """Install dependencies and launch the Vite dev server.

    Blocks until the server exits or is interrupted by the user.
    """
    console.print("  [dim]Installing npm dependencies (this may take a minute)...[/]")

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    try:
        subprocess.run(
            [npm_cmd, "install"],
            cwd=preview_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        console.print("[red]✗ npm install failed[/]")
        logger.error("npm install failed:\n%s\n%s", e.stdout, e.stderr)
        return
        console.print(
            "[red]✗ node/npm not found. Please install Node.js to use the preview server.[/]"
        )
        return

    console.print("  ✓ Dependencies installed")
    console.print("  [dim]Starting Vite dev server...[/]")

    try:
        # Launch dev server. Vite's --open will launch the browser automatically.
        server_process = subprocess.Popen(
            [npm_cmd, "run", "dev", "--", "--port", "5174", "--open"],
            cwd=preview_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Give it a moment to fail if port is in use or fast crash
        time.sleep(1.5)

        if server_process.poll() is None:
            console.print(
                Panel(
                    "[bold green]Preview server running![/]\n"
                    "[dim]Check your browser. Press Ctrl+C in this terminal "
                    "to stop the preview.[/]",
                    expand=False,
                )
            )

            # Block until user stops it
            server_process.wait()
        else:
            console.print("[red]✗ Failed to start dev server[/]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping preview server...[/]")
        if "server_process" in locals() and server_process.poll() is None:
            server_process.terminate()
            server_process.wait()
