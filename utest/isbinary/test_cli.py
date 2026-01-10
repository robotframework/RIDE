
from pathlib import Path

import pytest

from robotide.lib.isbinary.cli import main


def test_main_with_binary(capsys: pytest.CaptureFixture[str], file_fixtures_dir: Path) -> None:
    binary_file = file_fixtures_dir / "logo.png"

    main((str(binary_file),))

    captured = capsys.readouterr()
    assert captured.out == "true\n"
    assert captured.err == ""


def test_main_with_not_binary(capsys: pytest.CaptureFixture[str], file_fixtures_dir: Path) -> None:
    not_binary_file = file_fixtures_dir / "robots.txt"

    main((str(not_binary_file),))

    captured = capsys.readouterr()
    assert captured.out == "false\n"
    assert captured.err == ""


def test_main_with_empty(capsys: pytest.CaptureFixture[str], file_fixtures_dir: Path) -> None:
    empty_file = file_fixtures_dir / "empty.txt"

    main((str(empty_file),))

    captured = capsys.readouterr()
    assert captured.out == "false\n"
    assert captured.err == ""
