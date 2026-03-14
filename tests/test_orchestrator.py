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
        orch = LLMOrchestrator(config, stream=False)
        files, warnings, errors = orch._parse_response(SAMPLE_LLM_RESPONSE)
        assert len(files) == 1
        assert files[0].path == "src/components/PrimaryButton.tsx"
        assert len(errors) == 0

    def test_parse_json_object_with_files_key(self) -> None:
        """Should parse {files: [...]} format."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config, stream=False)
        response = json.dumps(
            {"files": [{"path": "src/A.tsx", "content": "export const A = () => null;"}]}
        )
        files, warnings, errors = orch._parse_response(response)
        assert len(files) == 1
        assert files[0].path == "src/A.tsx"

    def test_parse_single_object(self) -> None:
        """Should handle a single file object (not in array)."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config, stream=False)
        response = json.dumps({"path": "src/B.tsx", "content": "export const B = () => null;"})
        files, warnings, errors = orch._parse_response(response)
        assert len(files) == 1

    def test_parse_empty_response(self) -> None:
        """Should return error for empty response."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config, stream=False)
        files, warnings, errors = orch._parse_response("")
        assert len(errors) == 1
        assert "Empty" in errors[0]

    def test_parse_malformed_json(self) -> None:
        """Should return error for completely invalid JSON."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config, stream=False)
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
        orch = LLMOrchestrator(config, stream=False)
        result = orch.generate_from_node(sample_ir_node)
        assert result.success
        assert len(result.files) >= 1
        mock_llm.assert_called_once()

    @patch.object(LLMOrchestrator, "_call_llm", return_value=SAMPLE_LLM_RESPONSE)
    def test_generate_from_design(self, mock_llm: MagicMock, sample_ir_design: IRDesign) -> None:
        """Should generate files from a full design."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config, stream=False)
        result = orch.generate_from_design(sample_ir_design)
        assert result.success
        # Should include barrel file
        paths = [f.path for f in result.files]
        assert any("index.ts" in p for p in paths)

    @patch.object(
        LLMOrchestrator,
        "_call_llm",
        return_value='{"files": [{"path": "dummy.tsx", "content": ""}]}',
    )
    def test_generate_sequential_fallback_many_children(self, mock_llm: MagicMock) -> None:
        """Should fall back to sequential generation if design has more than 5 nodes."""
        config = LLMConfig(provider="openai", openai_api_key="test")
        orch = LLMOrchestrator(config, stream=False)

        # 6 top-level nodes
        nodes = [IRNode(id=f"1:{i}", name=f"Component{i}", type="component") for i in range(6)]
        design = IRDesign(name="Test", nodes=nodes, tokens=[])

        result = orch.generate_from_design(design)

        assert result.success
        assert mock_llm.call_count == 6


class TestOpenAIStreaming:
    """Tests for OpenAI streaming accumulation."""

    @patch("openai.OpenAI")
    def test_openai_streaming_accumulates(self, mock_openai_cls: MagicMock) -> None:
        """Should accumulate all streamed chunks into the final response."""
        # Build mock chunks
        chunks = []
        for token in ['{"files', '": [{"path":', ' "a.tsx",', ' "content": "x"}]}']:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta = MagicMock()
            chunk.choices[0].delta.content = token
            chunks.append(chunk)

        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = iter(chunks)

        config = LLMConfig(provider="openai", openai_api_key="test-key")
        orch = LLMOrchestrator(config, stream=True)
        result = orch._call_openai("generate a button")

        expected = '{"files": [{"path": "a.tsx", "content": "x"}]}'
        assert result == expected
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs.kwargs.get("stream") is True

    @patch("openai.OpenAI")
    def test_openai_non_streaming(self, mock_openai_cls: MagicMock) -> None:
        """Should handle OpenAI non-streaming successfully."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"files": [{"path": "a.tsx", "content": "x"}]}'
        mock_response.usage.total_tokens = 42
        mock_client.chat.completions.create.return_value = mock_response

        config = LLMConfig(provider="openai", openai_api_key="test-key")
        orch = LLMOrchestrator(config, stream=False)
        result = orch._call_openai("generate a button")

        assert result == '{"files": [{"path": "a.tsx", "content": "x"}]}'
        mock_client.chat.completions.create.assert_called_once()


class TestOllamaStreaming:
    """Tests for Ollama streaming accumulation."""

    @patch("requests.post")
    def test_ollama_streaming_accumulates(self, mock_post: MagicMock) -> None:
        """Should accumulate all streamed JSON lines into the final response."""
        lines = [
            json.dumps({"message": {"content": '{"files'}}),
            json.dumps({"message": {"content": '": [{"path":'}}),
            json.dumps({"message": {"content": ' "b.tsx", "content": "y"}]}'}}),
        ]

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.iter_lines.return_value = iter(lines)
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        config = LLMConfig(
            provider="ollama",
            ollama_base_url="http://localhost:11434",
            ollama_model="test",
        )
        orch = LLMOrchestrator(config, stream=True)
        result = orch._call_ollama("generate a card")

        expected = '{"files": [{"path": "b.tsx", "content": "y"}]}'
        assert result == expected
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs.get("stream") is True

    @patch("requests.post")
    def test_ollama_non_streaming(self, mock_post: MagicMock) -> None:
        """Should handle Ollama non-streaming successfully."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "message": {"content": '{"files": [{"path": "b.tsx", "content": "y"}]}'},
            "prompt_eval_count": 10,
            "eval_count": 20,
        }
        mock_post.return_value = mock_resp

        config = LLMConfig(
            provider="ollama",
            ollama_base_url="http://localhost:11434",
            ollama_model="test",
        )
        orch = LLMOrchestrator(config, stream=False)
        result = orch._call_ollama("generate a card")

        assert result == '{"files": [{"path": "b.tsx", "content": "y"}]}'
        mock_post.assert_called_once()
