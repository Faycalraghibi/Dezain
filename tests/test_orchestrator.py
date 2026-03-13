# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from dezain.config import LLMConfig
from dezain.generator.orchestrator import LLMOrchestrator, _extract_json, _generate_barrel_file
from dezain.generator.types import GeneratedFile
from dezain.ir import IRDesign, IRNode

_SAMPLE_CONTENT = (
    'import React from "react";\n\nexport const PrimaryButton = () => <button>Click</button>;'
)
SAMPLE_LLM_RESPONSE = json.dumps(
    [
        {
            "path": "src/components/PrimaryButton.tsx",
            "content": _SAMPLE_CONTENT,
        }
    ]
)


class TestResponseParsing:
    """Tests for LLM response parsing."""

    def test_parse_clean_json_array(self) -> None:
        """Should parse a clean JSON array response."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config)
        files, warnings, errors = orch._parse_response(SAMPLE_LLM_RESPONSE)
        assert len(files) == 1
        assert files[0].path == "src/components/PrimaryButton.tsx"
        assert len(errors) == 0

    def test_parse_json_object_with_files_key(self) -> None:
        """Should parse {files: [...]} format."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config)
        response = json.dumps(
            {"files": [{"path": "src/A.tsx", "content": "export const A = () => null;"}]}
        )
        files, warnings, errors = orch._parse_response(response)
        assert len(files) == 1
        assert files[0].path == "src/A.tsx"

    def test_parse_single_object(self) -> None:
        """Should handle a single file object (not in array)."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config)
        response = json.dumps({"path": "src/B.tsx", "content": "export const B = () => null;"})
        files, warnings, errors = orch._parse_response(response)
        assert len(files) == 1

    def test_parse_empty_response(self) -> None:
        """Should return error for empty response."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config)
        files, warnings, errors = orch._parse_response("")
        assert len(errors) == 1
        assert "Empty" in errors[0]

    def test_parse_malformed_json(self) -> None:
        """Should return error for completely invalid JSON."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config)
        files, warnings, errors = orch._parse_response("not json at all {{{")
        assert len(errors) >= 1


class TestExtractJson:
    """Tests for the _extract_json helper."""

    def test_extract_array_from_text(self) -> None:
        """Should extract JSON array wrapped in text."""
        text = 'Here is the code:\n[{"path": "a.tsx", "content": "x"}]\nDone!'
        result = _extract_json(text)
        assert result is not None
        assert isinstance(result, list)

    def test_extract_object_from_text(self) -> None:
        """Should extract JSON object wrapped in text."""
        text = 'Response: {"path": "a.tsx", "content": "x"} end'
        result = _extract_json(text)
        assert result is not None
        assert isinstance(result, dict)

    def test_returns_none_for_no_json(self) -> None:
        """Should return None when no JSON is found."""
        result = _extract_json("plain text with no json")
        assert result is None


class TestBarrelFile:
    """Tests for barrel file generation."""

    def test_generates_exports(self) -> None:
        """Should create export lines for each file."""
        files = [
            GeneratedFile(path="src/components/Button.tsx", content=""),
            GeneratedFile(path="src/components/Card.tsx", content=""),
        ]
        barrel = _generate_barrel_file(files)
        assert barrel.path == "src/components/index.ts"
        assert 'export * from "./Button"' in barrel.content
        assert 'export * from "./Card"' in barrel.content


class TestOrchestrator:
    """Tests for the full orchestrator flow with mocked LLM."""

    @patch.object(LLMOrchestrator, "_call_llm", return_value=SAMPLE_LLM_RESPONSE)
    def test_generate_from_node(self, mock_llm: MagicMock, sample_ir_node: IRNode) -> None:
        """Should generate files from a single node."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config)
        result = orch.generate_from_node(sample_ir_node)
        assert result.success
        assert len(result.files) >= 1
        mock_llm.assert_called_once()

    @patch.object(LLMOrchestrator, "_call_llm", return_value=SAMPLE_LLM_RESPONSE)
    def test_generate_from_design(self, mock_llm: MagicMock, sample_ir_design: IRDesign) -> None:
        """Should generate files from a full design."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config)
        result = orch.generate_from_design(sample_ir_design)
        assert result.success
        # Should include barrel file
        paths = [f.path for f in result.files]
        assert any("index.ts" in p for p in paths)
