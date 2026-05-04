from pathlib import Path

import pytest

from microsql.config import AppConfig, load_config
from microsql.exceptions import FileSystemException


def test_load_config_returns_safe_defaults_when_file_is_missing(tmp_path: Path) -> None:
    config = load_config(tmp_path / "missing.json")

    assert config == AppConfig.safe_default()


def test_load_config_reads_filter_options(tmp_path: Path) -> None:
    config_file = tmp_path / "microsql.config.json"
    config_file.write_text(
        '{"filter": {"engine": "specification", "enable_not_operator": false, '
        '"case_sensitive_strings": false}}',
        encoding="utf-8",
    )

    config = load_config(config_file)
    parser_options = config.to_parser_options()

    assert parser_options.filter_engine == "specification"
    assert parser_options.enable_not_operator is False
    assert parser_options.case_sensitive_strings is False


def test_load_config_raises_filesystem_exception_for_invalid_json(tmp_path: Path) -> None:
    config_file = tmp_path / "broken.json"
    config_file.write_text("{", encoding="utf-8")

    with pytest.raises(FileSystemException, match="Invalid JSON configuration"):
        load_config(config_file)
