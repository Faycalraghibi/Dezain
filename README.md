<div align="center">
  <h1>🎨 Dezain</h1>
  <p><strong>AI-powered frontend code generator translating Figma designs into production-ready React + TypeScript + TailwindCSS components.</strong></p>

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![CI Status](https://github.com/faycalraghibi/Dezain/actions/workflows/ci.yml/badge.svg)](https://github.com/faycalraghibi/Dezain/actions)
  [![Coverage](https://img.shields.io/badge/Coverage-92%25-brightgreen.svg)](#testing)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

---

**Dezain** is designed for modern TDD frontend teams, utilizing **LangChain / OpenAI / Ollama** for intelligent code generation. Dezain integrates seamlessly into your CI/CD pipelines, enforcing strict type-safety, robust testing (92% Coverage), and automated code validation.

## ✨ Key Features

- **🔌 Figma Integration** — Connects directly to the Figma API to extract frames, vector hierarchies, and layout geometry.
- **🧠 AI-Driven Code Generation** — Employs Large Language Models (LLMs) to natively author functional React & TypeScript UI components.
- **📚 Design System Awareness** — Cross-references your existing local components (e.g., `<Button>`, `<Card>`) and dynamically integrates them into generated templates.
- **🎨 Tailwind Extraction** — Converts extracted Design Tokens (colors, fonts, borders, paddings) natively into TailwindCSS utility classes.
- **🔍 Automated Code Validation** — Scaffolds generated ASTs and validates output instantly against `tsc` (TypeScript compiler) to ensure absolute syntax safety.
- **🌍 Pluggable LLM Backends** — Fully supports cloud inference via **OpenAI**, or self-hosted, secure local generation via **Ollama**.
- **⚡ Live Dev Preview Server** — Natively launches a high-speed Vite server displaying your generated code visually in your browser immediately post-generation.
- **📦 Multi-Frame Processing** — Accepts targeted `--frame` array selections, enabling extraction of multiple specific nested components per operation. 

---

## 🏗️ Architecture Visualization

```mermaid
graph LR
    subgraph Input Phase
        A[Figma API] -->|document node| B[Figma Client]
    end
    
    subgraph Transformation
        B --> C[Design Parser]
        C -->|Type-Safe Pydantic| D[Intermediate Representation (IR)]
    end
    
    subgraph Execution Pipeline
        D --> E[LLM Orchestrator]
        F[Design System Registry] -->|Component context| E
        E -->|React AST String| G[Generated .tsx Files]
    end
    
    subgraph Output Validation
        G --> H[TSC Validator]
        H -->|Validation OK| I[Output Directory]
    end
```

---

## 🚀 Quick Start

### 1. Installation

Clone the repository and structure the virtual environment:
```bash
git clone https://github.com/Faycalraghibi/Dezain.git
cd Dezain

python -m venv desain-venv
source desain-venv/bin/activate    # Linux/MacOS
# desain-venv\Scripts\activate     # Windows

pip install -e ".[dev]"
```

### 2. Initialization & Configuration
Scaffold the system config (`dezain.config.yaml`):
```bash
dezain init
```
*Note: Use the `.yaml` config to explicitly define known component directories and custom mappings.*

### 3. Usage

#### Demo Mode
Dezain provides a bundled offline sample file so you can generate components without needing Figma tokens immediately:
```bash
dezain generate --sample --preview
```

#### Authentic Generation Workflows
Copy over the environment file and set your `FIGMA_TOKEN` and `OPENAI_API_KEY`:
```bash
cp .env.example .env
```
Execute generation with an active Figma document URL:
```bash
dezain generate --file-url "https://figma.com/file/XXXXX/Design"
```

#### Targeting Specific Frames (Multi-Frame)
Filter your document by targeting nested nodes using consecutive `--frame` flags:
```bash
dezain generate --file-url "..." --frame "1:2" --frame "3:4"
```

---

## 🐳 Docker Support

If you prefer completely isolated execution, Dezain includes `docker-compose` routing for both isolated API generation and Local-LLM hosting workflows:

```bash
# Utilizing external cloud LLM inputs (OpenAI)
docker compose up dezain

# Utilizing a self-hosted isolated LLM (Ollama Sidecar)
docker compose --profile local-llm up
```

---

## 🛠️ Development & Testing

We uphold severe Code Quality gates. The project requires passing lint (`Ruff`), format (`Ruff`), and type-checking (`Mypy`) tests to merge workflows. 

```bash
# Execute local unit suite (100+ tests, 92% Local Coverage minimum)
pytest tests/ --cov=dezain

# Check format adherence
ruff check dezain/ tests/
ruff format --check dezain/ tests/

# Statically analyze types
mypy dezain/ tests/
```

> **Tip!** Install the git-hooks automatically to guard commits:
> `pre-commit install`

---

## 📜 License
Provided under the standard **MIT License**.