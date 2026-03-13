# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dezain.figma.client import FigmaClient, FigmaClientError, load_sample_file
from dezain.figma.types import FigmaFile


class TestFigmaClient:
    """Tests for FigmaClient."""

    def test_parse_file_url_standard(self) -> None:
        """Should extract file key from standard Figma URL."""
        url = "https://www.figma.com/file/ABC123xyz/My-Design"
        assert FigmaClient.parse_file_url(url) == "ABC123xyz"

    def test_parse_file_url_design_format(self) -> None:
        """Should extract file key from /design/ URL format."""
        url = "https://www.figma.com/design/XYZ789/Another-Design"
        assert FigmaClient.parse_file_url(url) == "XYZ789"

    def test_parse_file_url_trailing_slash(self) -> None:
        """Should handle trailing slash."""
        url = "https://www.figma.com/file/ABC123/"
        assert FigmaClient.parse_file_url(url) == "ABC123"

    def test_parse_file_url_invalid(self) -> None:
        """Should raise ValueError for unrecognized URL."""
        with pytest.raises(ValueError, match="Could not extract"):
            FigmaClient.parse_file_url("https://example.com/not-figma")

    @patch("dezain.figma.client.requests.Session")
    def test_get_file_success(self, mock_session_cls: MagicMock) -> None:
        """Should fetch and parse a Figma file."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Test File",
            "document": {"id": "0:0", "name": "Document", "type": "DOCUMENT"},
            "components": {},
            "styles": {},
        }

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_cls.return_value = mock_session

        client = FigmaClient(token="test-token")
        result = client.get_file("ABC123")

        assert isinstance(result, FigmaFile)
        assert result.name == "Test File"

    @patch("dezain.figma.client.requests.Session")
    def test_get_file_error(self, mock_session_cls: MagicMock) -> None:
        """Should raise FigmaClientError on non-200 response."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        mock_session = MagicMock()
        mock_session.get.return_value = mock_response
        mock_session_cls.return_value = mock_session

        client = FigmaClient(token="bad-token")
        with pytest.raises(FigmaClientError, match="403"):
            client.get_file("ABC123")

    def test_load_sample_file_not_found(self) -> None:
        """Should raise FileNotFoundError for missing sample."""
        with pytest.raises(FileNotFoundError):
            load_sample_file(Path("nonexistent.json"))
