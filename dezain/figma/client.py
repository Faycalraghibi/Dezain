# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

from dezain.figma.types import FigmaFile

FIGMA_API_BASE = "https://api.figma.com/v1"


class FigmaClientError(Exception):
    """Raised when a Figma API call fails."""


class FigmaClient:
    """Client for the Figma REST API."""

    def __init__(self, token: str) -> None:
        self._token = token
        self._session = requests.Session()
        self._session.headers.update({"X-Figma-Token": token})

    def get_file(self, file_key: str) -> FigmaFile:
        """Fetch a full Figma file by its key.

        Args:
            file_key: The Figma file key (from the URL).

        Returns:
            Parsed FigmaFile model.
        """
        url = f"{FIGMA_API_BASE}/files/{file_key}"
        response = self._session.get(url)

        if response.status_code != 200:
            raise FigmaClientError(f"Figma API returned {response.status_code}: {response.text}")

        data = response.json()
        return FigmaFile(**data)

    def get_node(self, file_key: str, node_id: str) -> dict[str, Any]:
        """Fetch a specific node from a Figma file.

        Args:
            file_key: The Figma file key.
            node_id: The node ID to fetch.

        Returns:
            Raw node data dict.
        """
        url = f"{FIGMA_API_BASE}/files/{file_key}/nodes"
        params = {"ids": node_id}
        response = self._session.get(url, params=params)

        if response.status_code != 200:
            raise FigmaClientError(f"Figma API returned {response.status_code}: {response.text}")

        data = response.json()
        nodes = data.get("nodes", {})
        node_data = nodes.get(node_id, {}).get("document")

        if node_data is None:
            raise FigmaClientError(f"Node {node_id} not found in file {file_key}")

        return node_data  # type: ignore[no-any-return]

    @staticmethod
    def parse_file_url(url: str) -> str:
        """Extract the file key from a Figma URL.

        Args:
            url: Full Figma file URL.

        Returns:
            The file key string.

        Raises:
            ValueError: If URL format is not recognized.
        """
        # URL format: https://www.figma.com/file/FILE_KEY/...
        # or: https://www.figma.com/design/FILE_KEY/...
        parts = url.rstrip("/").split("/")
        for i, part in enumerate(parts):
            if part in ("file", "design") and i + 1 < len(parts):
                return parts[i + 1]

        raise ValueError(f"Could not extract file key from URL: {url}")


def load_sample_file(sample_path: Path | None = None) -> FigmaFile:
    """Load a sample Figma response from a JSON file (demo mode).

    Args:
        sample_path: Path to the sample JSON. Defaults to samples/sample-figma-response.json

    Returns:
        Parsed FigmaFile model.
    """
    if sample_path is None:
        sample_path = Path("samples/sample-figma-response.json")

    if not sample_path.exists():
        raise FileNotFoundError(f"Sample file not found: {sample_path}")

    with open(sample_path) as f:
        data = json.load(f)

    return FigmaFile(**data)
