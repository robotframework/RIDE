
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def file_fixtures_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "files"


@pytest.fixture
def binfile_fixtures_dir(fixtures_dir: Path) -> Path:
    return fixtures_dir / "isBinaryFile"
