"""Prompt templates for LLM-based code generation.

Each template takes structured IR data and produces a prompt
that instructs the LLM to generate React + TypeScript + TailwindCSS code.
"""

from __future__ import annotations

from dezain.ir import IRDesign, IRNode

SYSTEM_PROMPT = """You are an expert React + TypeScript frontend developer.
You generate production-ready UI components from design specifications.

RULES:
- Output ONLY valid React + TypeScript (.tsx) code
- Use TailwindCSS utility classes for ALL styling (no inline styles, no CSS files)
- Use semantic HTML elements (<nav>, <main>, <section>, <header>, <footer>, <button>, etc.)
- Add proper accessibility attributes (aria-label, role, alt text, etc.)
- Use React functional components with proper TypeScript typing
- Export components as named exports
- Use descriptive prop interfaces (e.g., `interface ButtonProps`)
- Do NOT use `any` type
- Do NOT include console.log or debug code
- Do NOT invent components not specified in the design system

OUTPUT FORMAT:
Return a JSON array of file objects, each with "path" and "content" keys:
[
  {"path": "src/components/Button.tsx", "content": "...code..."},
  {"path": "src/components/Card.tsx", "content": "...code..."}
]

Return ONLY the JSON array, no markdown fences, no explanation."""


def build_component_prompt(
    node: IRNode,
    design_system_components: list[str] | None = None,
    parent_context: str = "",
) -> str:
    """Build a prompt to generate a single React component from an IR node.

    Args:
        node: The IR node subtree to convert.
        design_system_components: Available DS components to reuse.
        parent_context: Context about the parent component.

    Returns:
        The user prompt string.
    """
    ds_info = ""
    if design_system_components:
        ds_info = (
            "\n\nAVAILABLE DESIGN SYSTEM COMPONENTS (reuse these instead of creating new ones):\n"
            + "\n".join(f"- {c}" for c in design_system_components)
        )

    context = ""
    if parent_context:
        context = f"\n\nPARENT CONTEXT:\n{parent_context}"

    node_json = node.model_dump_json(indent=2)

    return f"""Generate a React + TypeScript component from this design node.

DESIGN NODE:
{node_json}
{ds_info}{context}

Generate a single .tsx file for this component.
The component name should be derived from the node name.
Include proper TypeScript interfaces for props.
Use TailwindCSS classes that match the styles specified in the node.

Return as JSON: [{{"path": "src/components/ComponentName.tsx", "content": "...code..."}}]"""


def build_page_prompt(
    design: IRDesign,
    design_system_components: list[str] | None = None,
) -> str:
    """Build a prompt to generate a full page of components from an IR design.

    Args:
        design: The full IR design to convert.
        design_system_components: Available DS components to reuse.

    Returns:
        The user prompt string.
    """
    ds_info = ""
    if design_system_components:
        ds_info = "\n\nAVAILABLE DESIGN SYSTEM COMPONENTS (reuse these):\n" + "\n".join(
            f"- {c}" for c in design_system_components
        )

    tokens_info = ""
    if design.tokens:
        token_lines = [f"- {t.name} ({t.category}): {t.value}" for t in design.tokens]
        tokens_info = "\n\nDESIGN TOKENS:\n" + "\n".join(token_lines)

    design_json = design.model_dump_json(indent=2)

    return f"""Generate React + TypeScript components for this full page design.

PAGE: {design.name}
{ds_info}{tokens_info}

FULL DESIGN STRUCTURE:
{design_json}

Generate ALL components needed for this page. Each component should be in its own file.
Also generate an index.ts barrel file that re-exports all components.
Use TailwindCSS classes matching the design tokens and styles.

Return as JSON array: [{{"path": "src/components/X.tsx", "content": "..."}}, ...]"""
