# Dezain

AI-powered frontend code generator that translates Figma designs into production-ready **React + TypeScript + TailwindCSS** UI components.

Built in Python, using **LangChain / OpenAI / Ollama** for intelligent code generation, following TDD practices with full CI/CD.

---

## Features

- **Figma Integration** — Connects to the Figma API to pull frames, styles, tokens, and component hierarchies
- **AI-Driven Code Generation** — LLM-powered agent generates React + TypeScript components automatically
- **Design System Awareness** — Uses your existing component library and tokens to produce consistent, reusable code
- **Tailwind Mapping** — Automatically converts design tokens to TailwindCSS utility classes
- **Validation** — Validates generated code for TypeScript correctness and best practices
- **Pluggable LLM** — Supports OpenAI (cloud) and Ollama (local) via config switch
- **Docker-Ready** — Full workflow containerizable with optional Ollama sidecar

---

## Quick Start

```bash
# Clone & setup
git clone https://github.com/Faycal/Dezain.git
cd Dezain
python -m venv desain-venv
desain-venv\Scripts\activate   # Windows
# source desain-venv/bin/activate  # Linux/Mac
pip install -e ".[dev]"

# Initialize config
dezain init
# Edit dezain.config.yaml to define your component mappings

# Demo mode (no Figma token needed)
dezain generate --sample

# With Figma
cp .env.example .env
# Add your FIGMA_TOKEN and OPENAI_API_KEY to .env
dezain generate --file-url "https://figma.com/file/XXXXX/Design"
```

---

## How It Works

1. **Fetch designs** from Figma via the REST API (or use `--sample` for demo mode)
2. **Parse design data** into a normalized Intermediate Representation (Pydantic models)
3. **Resolve design system** — map Figma components to your React component library
4. **Generate React + TypeScript** code via LLM (OpenAI or Ollama)
5. **Validate output** — check for TypeScript errors, missing exports, type safety
6. **Write files** to output directory with generated report

---

## Development

```bash
# Run tests
pytest

# Lint
ruff check dezain/ tests/

# Format
ruff format dezain/ tests/

# Type check
mypy dezain/

# Pre-commit hooks (auto-runs on every commit)
pre-commit install
```

---

## Docker

```bash
# With OpenAI
docker compose up dezain

# With local LLM (Ollama)
docker compose --profile local-llm up
```

---

## Project Structure

```
dezain/
├── figma/           # Figma API client + JSON → IR parser
├── design_system/   # Component registry + Tailwind token mapping
├── generator/       # LLM orchestrator, prompts, file writer
├── validation/      # Post-generation code validation
├── cli.py           # CLI entry point
├── config.py        # Configuration loader
├── ir.py            # Intermediate Representation models
└── pipeline.py      # Main pipeline orchestration

tests/               # 76 tests, 73% coverage
samples/             # Sample Figma data for demo mode
```

---

## License

MIT