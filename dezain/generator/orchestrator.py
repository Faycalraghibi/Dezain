# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any

from rich.console import Console

from dezain.config import LLMConfig
from dezain.design_system.registry import ComponentRegistry
from dezain.generator.prompts import (
    SYSTEM_PROMPT,
    build_component_prompt,
    build_page_prompt,
)
from dezain.generator.types import GeneratedFile, GenerationResult
from dezain.ir import IRDesign, IRNode, NodeType

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2.0  # seconds


class LLMOrchestrator:
    """Orchestrates LLM calls to generate React components from IR designs."""

    def __init__(
        self,
        config: LLMConfig,
        registry: ComponentRegistry | None = None,
        *,
        stream: bool = True,
        console: Console | None = None,
    ) -> None:
        self._config = config
        self._registry = registry or ComponentRegistry()
        self._total_tokens = 0
        self._stream = stream
        self._console = console or Console()

    def generate_from_design(self, design: IRDesign) -> GenerationResult:
        """Generate components for a full design.

        For small designs, sends the entire design in one prompt.
        For larger designs, splits into per-component generation tasks.

        Args:
            design: The full IR design.

        Returns:
            GenerationResult with all generated files.
        """
        ds_components = self._registry.list_registered()
        all_files: list[GeneratedFile] = []
        warnings: list[str] = []
        errors: list[str] = []

        # For designs with few top-level nodes, generate as a page
        if len(design.nodes) <= 5:
            prompt = build_page_prompt(design, ds_components)
            result = self._call_llm(prompt)
            files, warns, errs = self._parse_response(result)
            all_files.extend(files)
            warnings.extend(warns)
            errors.extend(errs)
        else:
            # Split into per-component tasks
            for node in design.nodes:
                component_nodes = _extract_component_nodes(node)
                for comp_node in component_nodes:
                    prompt = build_component_prompt(comp_node, ds_components)
                    result = self._call_llm(prompt)
                    files, warns, errs = self._parse_response(result)
                    all_files.extend(files)
                    warnings.extend(warns)
                    errors.extend(errs)

        # Generate barrel file
        if all_files:
            barrel = _generate_barrel_file(all_files)
            all_files.append(barrel)

        return GenerationResult(
            files=all_files,
            warnings=warnings,
            errors=errors,
            tokens_used=self._total_tokens,
        )

    def generate_from_node(self, node: IRNode) -> GenerationResult:
        """Generate a single component from an IR node.

        Args:
            node: The IR node to convert.

        Returns:
            GenerationResult with generated file(s).
        """
        ds_components = self._registry.list_registered()
        prompt = build_component_prompt(node, ds_components)
        result = self._call_llm(prompt)
        files, warnings, errors = self._parse_response(result)

        return GenerationResult(
            files=files,
            warnings=warnings,
            errors=errors,
            tokens_used=self._total_tokens,
        )

    def _call_llm(self, user_prompt: str) -> str:
        """Call the configured LLM provider with retry logic.

        Args:
            user_prompt: The user prompt to send.

        Returns:
            Raw response string from the LLM.
        """
        provider = self._config.provider.lower()

        for attempt in range(MAX_RETRIES):
            try:
                if provider == "openai":
                    return self._call_openai(user_prompt)
                elif provider == "ollama":
                    return self._call_ollama(user_prompt)
                else:
                    raise ValueError(f"Unknown LLM provider: {provider}")
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY_BASE * (2**attempt)
                    logger.warning(
                        "LLM call failed (attempt %d/%d): %s. Retrying in %.1fs...",
                        attempt + 1,
                        MAX_RETRIES,
                        str(e),
                        delay,
                    )
                    time.sleep(delay)
                else:
                    raise

        return ""  # Unreachable but satisfies type checker

    def _print_token(self, token: str) -> None:
        """Print a single streamed token to the console."""
        if self._stream and token:
            sys.stdout.write(token)
            sys.stdout.flush()

    def _end_stream(self) -> None:
        """Print a newline after streaming completes."""
        if self._stream:
            sys.stdout.write("\n")
            sys.stdout.flush()

    def _call_openai(self, user_prompt: str) -> str:
        """Call OpenAI API (or compatible like OpenRouter) with streaming."""
        from openai import OpenAI

        client_kwargs: dict[str, Any] = {"api_key": self._config.openai_api_key}
        if self._config.openai_base_url:
            client_kwargs["base_url"] = self._config.openai_base_url

        client = OpenAI(**client_kwargs)

        if self._stream:
            self._console.print("  [dim]Streaming response...[/]")
            response_stream = client.chat.completions.create(
                model=self._config.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                stream=True,
            )

            collected: list[str] = []
            for chunk in response_stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    self._print_token(delta.content)
                    collected.append(delta.content)

            self._end_stream()
            return "".join(collected)

        # Non-streaming fallback (for tests)
        response = client.chat.completions.create(
            model=self._config.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        usage = response.usage
        if usage:
            self._total_tokens += usage.total_tokens

        content = response.choices[0].message.content
        return content or ""

    def _call_ollama(self, user_prompt: str) -> str:
        """Call Ollama local LLM with streaming."""
        import requests

        url = f"{self._config.ollama_base_url}/api/chat"
        payload: dict[str, Any] = {
            "model": self._config.ollama_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": self._stream,
            "format": "json",
            "options": {"temperature": 0.2},
        }

        if self._stream:
            self._console.print("  [dim]Streaming response...[/]")
            resp = requests.post(url, json=payload, timeout=900, stream=True)
            resp.raise_for_status()

            collected: list[str] = []
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        self._print_token(token)
                        collected.append(token)
                except json.JSONDecodeError:
                    continue

            self._end_stream()
            return "".join(collected)

        # Non-streaming fallback
        resp = requests.post(url, json=payload, timeout=900)
        resp.raise_for_status()
        data = resp.json()
        return str(data.get("message", {}).get("content", ""))

    def _parse_response(self, raw: str) -> tuple[list[GeneratedFile], list[str], list[str]]:
        """Parse LLM response JSON into GeneratedFile objects.

        Returns:
            Tuple of (files, warnings, errors).
        """
        files: list[GeneratedFile] = []
        warnings: list[str] = []
        errors: list[str] = []

        if not raw.strip():
            errors.append("Empty LLM response")
            return files, warnings, errors

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            extracted = _extract_json(raw)
            if extracted is not None:
                parsed = extracted
                warnings.append("Had to extract JSON from non-clean LLM response")
            else:
                errors.append(f"Failed to parse LLM response as JSON: {e}")
                return files, warnings, errors

        # Handle both array and {"files": [...]} formats
        file_list: list[dict[str, Any]]
        if isinstance(parsed, list):
            file_list = parsed
        elif isinstance(parsed, dict) and "files" in parsed:
            file_list = parsed["files"]
        elif isinstance(parsed, dict) and "path" in parsed:
            file_list = [parsed]
        else:
            errors.append(f"Unexpected response format: {type(parsed)}")
            return files, warnings, errors

        for item in file_list:
            if isinstance(item, dict) and "path" in item and "content" in item:
                files.append(
                    GeneratedFile(
                        path=item["path"],
                        content=item["content"],
                        description=item.get("description", ""),
                    )
                )
            else:
                warnings.append(f"Skipping malformed file entry: {item}")

        return files, warnings, errors


def _extract_component_nodes(node: IRNode) -> list[IRNode]:
    """Extract nodes that should be generated as individual components."""
    components: list[IRNode] = []

    if node.type in (NodeType.COMPONENT, NodeType.INSTANCE, NodeType.FRAME):
        components.append(node)
    else:
        for child in node.children:
            components.extend(_extract_component_nodes(child))

    return components if components else [node]


def _generate_barrel_file(files: list[GeneratedFile]) -> GeneratedFile:
    """Generate an index.ts barrel file re-exporting all components."""
    exports: list[str] = []
    for f in files:
        # Extract component name from path
        path = f.path.replace("\\", "/")
        if path.endswith(".tsx") or path.endswith(".ts"):
            module = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            exports.append(f'export * from "./{module}";')

    return GeneratedFile(
        path="src/components/index.ts",
        content="\n".join(sorted(exports)) + "\n",
        description="Barrel file re-exporting all components",
    )


def _extract_json(text: str) -> Any | None:
    """Try to extract a JSON array or object from text with surrounding content."""
    # Try to find JSON array
    start = text.find("[")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    break

    # Try to find JSON object
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    break

    return None
