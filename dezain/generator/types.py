# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

from pydantic import BaseModel, Field


class GeneratedFile(BaseModel):
    """A single generated code file."""

    path: str
    content: str
    description: str = ""


class GenerationResult(BaseModel):
    """Result of a code generation run."""

    files: list[GeneratedFile] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    tokens_used: int = 0

    @property
    def success(self) -> bool:
        """Whether generation completed without errors."""
        return len(self.errors) == 0
