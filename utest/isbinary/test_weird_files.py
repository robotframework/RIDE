
import re
from pathlib import Path

import pytest

from robotide.lib.isbinary import is_binary_file


def test_nonexistent_file(tmp_path: Path) -> None:
    file_path = tmp_path / "nonexistent"

    errmsg = re.escape("No such file or directory: ")
    with pytest.raises(FileNotFoundError, match=errmsg):
        is_binary_file(file_path)


def test_broken_symlink(tmp_path: Path) -> None:
    symlink_file = tmp_path / "symlink-file"
    symlink_file.symlink_to(tmp_path / "non-existent-file")

    assert is_binary_file(symlink_file) is True
