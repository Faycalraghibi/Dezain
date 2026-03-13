# Copyright © 2026 Dezain. All rights reserved.


from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

_ENV_LOADED = False


def _ensure_env() -> None:
    """Load .env file once."""
    global _ENV_LOADED  # noqa: PLW0603
    if not _ENV_LOADED:
        load_dotenv()
        _ENV_LOADED = True


class FigmaConfig(BaseModel):
    """Figma API connection settings."""

    token: str = ""
    file_url: str = ""


class LLMConfig(BaseModel):
    """LLM provider settings."""

    provider: str = "openai"  # "openai" or "ollama"
    openai_api_key: str = ""
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "codellama"


class OutputConfig(BaseModel):
    """Output generation settings."""

    directory: Path = Path("./generated")
    tailwind_version: int = 3


class ComponentMapping(BaseModel):
    """Maps a Figma component name to a React component import."""

    figma_name: str
    react_import: str
    react_component: str
    props_mapping: dict[str, str] = Field(default_factory=dict)


class DezainConfig(BaseModel):
    """Root configuration for the Dezain pipeline."""

    figma: FigmaConfig = Field(default_factory=FigmaConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    component_mappings: list[ComponentMapping] = Field(default_factory=list)
    design_tokens_overrides: dict[str, Any] = Field(default_factory=dict)


def load_config(
    config_path: Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> DezainConfig:
    """Load configuration from .env + YAML + overrides.

    Priority (highest to lowest):
    1. CLI/runtime overrides
    2. dezain.config.yaml
    3. .env environment variables
    4. Defaults
    """
    import os

    _ensure_env()

    # Start with env-based defaults
    config_data: dict[str, Any] = {
        "figma": {
            "token": os.getenv("FIGMA_TOKEN", ""),
            "file_url": os.getenv("FIGMA_FILE_URL", ""),
        },
        "llm": {
            "provider": os.getenv("LLM_PROVIDER", "openai"),
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "openai_base_url": os.getenv("OPENAI_BASE_URL"),
            "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o"),
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "ollama_model": os.getenv("OLLAMA_MODEL", "codellama"),
        },
        "output": {
            "directory": os.getenv("OUTPUT_DIR", "./generated"),
        },
    }

    # Merge YAML config if available
    yaml_path = config_path or Path("dezain.config.yaml")
    if yaml_path.exists():
        with open(yaml_path) as f:
            yaml_data = yaml.safe_load(f) or {}
        config_data = _deep_merge(config_data, yaml_data)

    # Apply runtime overrides
    if overrides:
        config_data = _deep_merge(config_data, overrides)

    return DezainConfig(**config_data)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override dict into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
