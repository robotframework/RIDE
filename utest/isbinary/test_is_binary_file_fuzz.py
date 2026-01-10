
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis.strategies import binary

from robotide.lib.isbinary import is_binary_file


@pytest.fixture
def tmp_file(tmp_path: Path) -> Path:
    return tmp_path / "tmpfile"


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(binary_data=binary(max_size=10 * 1024))
def test_never_crashes(tmp_file: Path, binary_data: bytes) -> None:
    tmp_file.write_bytes(binary_data)
    try:
        assert isinstance(is_binary_file(tmp_file), bool)
    finally:
        tmp_file.unlink()
