# Copyright © 2026 Dezain. All rights reserved.

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from dezain.generator.types import GeneratedFile

logger = logging.getLogger(__name__)

PACKAGE_JSON = """{
  "name": "dezain-preview",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.2.2",
    "vite": "^5.2.0"
  }
}"""

VITE_CONFIG = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})"""

TAILWIND_CONFIG = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}"""

POSTCSS_CONFIG = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}"""

INDEX_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Dezain Preview</title>
  </head>
  <body class="bg-gray-50 text-gray-900">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>"""

MAIN_TSX = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)"""

INDEX_CSS = """@tailwind base;
@tailwind components;
@tailwind utilities;"""


def _generate_app_tsx(files: list[GeneratedFile]) -> str:
    imports = []
    components = []

    for f in files:
        path = f.path.replace("\\", "/")
        if not path.endswith(".tsx") or path.endswith("index.tsx") or path.endswith("index.ts"):
            continue

        module_name = path.rsplit("/", 1)[-1].replace(".tsx", "")
        # Assuming component name matches file name and is exported
        import_path = path.replace("src/", "./").replace(".tsx", "")
        imports.append(f"import {{ {module_name} }} from '{import_path}'")
        components.append(module_name)

    lines = [
        "import React from 'react'",
        *imports,
        "",
        "export default function App() {",
        "  return (",
        '    <div className="min-h-screen p-8">',
        '      <header className="mb-8">',
        '        <h1 className="text-3xl font-bold">🎨 Dezain Preview</h1>',
        '        <p className="text-gray-500 mt-2">Generated React Components</p>',
        "      </header>",
        '      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">',
    ]

    if not components:
        lines.append(
            '        <div className="col-span-full p-8 text-center text-gray-500 '
            'border-2 border-dashed rounded-xl">No React components generated.</div>'
        )

    for comp in components:
        lines.extend(
            [
                '        <div className="bg-white p-6 rounded-xl shadow-sm border '
                'border-gray-100 flex flex-col items-center justify-center min-h-[300px]">',
                '          <div className="w-full flex-1 flex items-center justify-center p-4">',
                f"            <{comp} />",
                "          </div>",
                '          <h2 className="text-xs font-mono text-gray-400 mt-4 pt-2 '
                f'border-t w-full text-center">{comp}</h2>',
                "        </div>",
            ]
        )

    lines.extend(
        [
            "      </div>",
            "    </div>",
            "  )",
            "}",
        ]
    )

    return "\n".join(lines)


def create_preview_scaffold(output_dir: Path, files: list[GeneratedFile]) -> Path:
    """Create a Vite project scaffolding for previewing the generated components.

    Args:
        output_dir: The original output directory.
        files: List of generated files to import.

    Returns:
        Path to the preview project directory.
    """
    preview_dir = output_dir.with_name(f"{output_dir.name}-preview")

    # Clean previous if exists
    if preview_dir.exists():
        shutil.rmtree(preview_dir)

    preview_dir.mkdir(parents=True)

    # Write config files
    (preview_dir / "package.json").write_text(PACKAGE_JSON, encoding="utf-8")
    (preview_dir / "vite.config.ts").write_text(VITE_CONFIG, encoding="utf-8")
    (preview_dir / "tailwind.config.js").write_text(TAILWIND_CONFIG, encoding="utf-8")
    (preview_dir / "postcss.config.js").write_text(POSTCSS_CONFIG, encoding="utf-8")
    (preview_dir / "index.html").write_text(INDEX_HTML, encoding="utf-8")

    # Setup src directory
    src_dir = preview_dir / "src"
    src_dir.mkdir()

    (src_dir / "main.tsx").write_text(MAIN_TSX, encoding="utf-8")
    (src_dir / "index.css").write_text(INDEX_CSS, encoding="utf-8")
    (src_dir / "App.tsx").write_text(_generate_app_tsx(files), encoding="utf-8")

    # Copy components
    components_src = output_dir / "src" / "components"
    if components_src.exists():
        shutil.copytree(components_src, src_dir / "components", dirs_exist_ok=True)

    return preview_dir
