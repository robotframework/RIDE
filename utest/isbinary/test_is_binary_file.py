
from pathlib import Path
from typing import Callable

import pytest

from robotide.lib.isbinary import is_binary_file


CheckFunc = Callable[[str], bool]


@pytest.fixture
def check_file_fixture(file_fixtures_dir: Path) -> CheckFunc:
    return lambda filename: is_binary_file(file_fixtures_dir / filename)


@pytest.fixture
def check_binfile_fixture(binfile_fixtures_dir: Path) -> CheckFunc:
    return lambda filename: is_binary_file(binfile_fixtures_dir / filename)


def test_empty(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("empty.txt") is False


def test_triggers_decoding_error(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("decoding-error") is True


def test_triggers_lookup_error(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("lookup-error") is True


def test_ds_store(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture(".DS_Store") is True


def test_txt(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("robots.txt") is False


def test_txt_unicode(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("unicode.txt") is False


def test_binary_pdf2(check_binfile_fixture: CheckFunc) -> None:
    assert check_binfile_fixture("pdf.pdf") is True


def test_text_russian2(check_binfile_fixture: CheckFunc) -> None:
    assert check_binfile_fixture("russian_file.rst") is False


def test_binary_exe2(check_binfile_fixture: CheckFunc) -> None:
    assert check_binfile_fixture("grep") is True


def test_binary_sqlite(check_binfile_fixture: CheckFunc) -> None:
    assert check_binfile_fixture("test.sqlite") is True


@pytest.mark.parametrize("font_format", ("eot", "otf", "ttf", "woff"))
def test_font(check_file_fixture: CheckFunc, font_format: str) -> None:
    assert check_file_fixture(f"glyphiconshalflings-regular.{font_format}") is True


def test_png(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("logo.png") is True


def test_gif(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("lena.gif") is True


def test_jpg(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("lena.jpg") is True


def test_tiff(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("palette-1c-8b.tiff") is True


def test_bmp(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("rgb-3c-8b.bmp") is True


def test_binary_rgb_stream(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("pixelstream.rgb") is True


def test_binary_gif2(check_binfile_fixture: CheckFunc) -> None:
    assert check_binfile_fixture("null_file.gif") is False


def test_binary_gif3(check_binfile_fixture: CheckFunc) -> None:
    assert check_binfile_fixture("trunks.gif") is True


def test_svg(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("glyphiconshalflings-regular.svg") is False


@pytest.mark.parametrize(
    "filename",
    (
        "bom_utf-16",
        "bom_utf-16le",
        "test-utf16be",
        "bom_utf-32le",
        "utf_8",
        "test-gb2",
        "test-kr",
        "test-latin",
        "big5",
        "test-gb",
        "bom_utf-32",
        "bom_utf-8",
        "big5_B",
        "test-shishi",
        "utf8cn",
    ),
)
def test_text_encoding(check_binfile_fixture: CheckFunc, filename: str) -> None:
    assert check_binfile_fixture(f"encodings/{filename}.txt") is False


def test_css(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("bootstrap-glyphicons.css") is False


def test_json(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("cookiecutter.json") is False


def test_text_perl2(check_binfile_fixture: CheckFunc) -> None:
    assert check_binfile_fixture("perl_script") is False


def test_text_js(check_binfile_fixture: CheckFunc) -> None:
    assert check_binfile_fixture("index.js") is False


def test_text_lua(check_binfile_fixture: CheckFunc) -> None:
    assert check_binfile_fixture("no.lua") is False


def test_binary_pyc(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("hello_world.pyc") is True


def test_binary_empty_pyc(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("empty.pyc") is True


def test_binary_troublesome_pyc(check_file_fixture: CheckFunc) -> None:
    assert check_file_fixture("troublesome.pyc") is True
