# Copyright © 2026 Dezain. All rights reserved.

from pathlib import Path
from unittest.mock import patch

from dezain.config import _deep_merge, load_config


def test_deep_merge() -> None:
    # Test simple merge
    d1 = {"a": 1, "b": {"c": 2}}
    d2 = {"b": {"d": 3}, "e": 4}

    result = _deep_merge(d1, d2)
    assert result == {"a": 1, "b": {"c": 2, "d": 3}, "e": 4}

    # Test completely overwriting a non-dict value
    d3 = {"a": {"nested": True}}
    result2 = _deep_merge(d1, d3)
    assert result2 == {"a": {"nested": True}, "b": {"c": 2}}


@patch.dict("os.environ", {"FIGMA_TOKEN": "env_token"})
def test_load_config_yaml(tmp_path: Path) -> None:
    yaml_content = """
figma:
  token: "yaml_token"
output:
  tailwind_version: 4
"""
    yaml_file = tmp_path / "dezain.config.yaml"
    yaml_file.write_text(yaml_content)

    config = load_config(config_path=yaml_file)

    # YAML takes precedence over ENV variables based on _deep_merge logic
    assert config.figma.token == "yaml_token"
    assert config.output.tailwind_version == 4


@patch.dict("os.environ", {"FIGMA_TOKEN": "env_token"})
def test_load_config_overrides(tmp_path: Path) -> None:
    yaml_file = tmp_path / "not_exist.yaml"

    overrides = {"figma": {"token": "override_token"}, "output": {"directory": "./test_dir"}}

    config = load_config(config_path=yaml_file, overrides=overrides)

    # Overrides > YAML > ENV
    assert config.figma.token == "override_token"
    assert config.output.directory == Path("./test_dir")
