#  Copyright 2026-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import unittest

from utest.resources import datafilereader
from wx import stc
from robotide.editor.lex_detect import detect, detect_from_file, stc_lex_code

PLUGIN_NAME = "Text Edit"

tests = [
    # (filename, content, expected)
    ("hello.py",         None,                                    stc.STC_LEX_PYTHON),
    ("app.js",           None,                                    stc.STC_LEX_CPP),
    ("main.cpp",         None,                                    stc.STC_LEX_CPP),
    ("style.css",        None,                                    stc.STC_LEX_CSS),
    ("index.html",       None,                                    stc.STC_LEX_HTML),
    ("config.xml",       None,                                    stc.STC_LEX_XML),
    ("query.sql",        None,                                    stc.STC_LEX_SQL),
    ("build.yaml",       None,                                    stc.STC_LEX_YAML),
    ("data.json",        None,                                    stc.STC_LEX_JSON),
    # ("Cargo.toml",       None,                                    stc.STC_LEX_TOML),
    ("Makefile",         None,                                    stc.STC_LEX_MAKEFILE),
    ("CMakeLists.txt",   None,                                    stc.STC_LEX_CMAKE),
    ("script.sh",        None,                                    stc.STC_LEX_BASH),
    ("install.bat",      None,                                    stc.STC_LEX_BATCH),
    ("module.rs",        None,                                    stc.STC_LEX_RUST),
    ("main.go",          None,                                    stc.STC_LEX_CPP),
    # ("app.dart",         None,                                    stc.STC_LEX_DART),
    # ("main.zig",         None,                                    stc.STC_LEX_ZIG),
    # ("game.gd",          None,                                    stc.STC_LEX_GDSCRIPT),
    ("Main.java",        None,                                    stc.STC_LEX_CPP),
    ("README.md",        None,                                    stc.STC_LEX_MARKDOWN),
    ("thesis.tex",       None,                                    stc.STC_LEX_LATEX),
    ("refs.bib",         None,                                    stc.STC_LEX_BIBTEX),
    ("prog.hs",          None,                                    stc.STC_LEX_HASKELL),
    ("mod.erl",          None,                                    stc.STC_LEX_ERLANG),
    ("script.rb",        None,                                    stc.STC_LEX_RUBY),
    ("code.lua",         None,                                    stc.STC_LEX_LUA),
    # ("prog.nim",         None,                                    stc.STC_LEX_NIM),
    # ("app.jl",           None,                                    stc.STC_LEX_JULIA),
    ("lib.ml",           None,                                    stc.STC_LEX_CAML),
    ("code.d",           None,                                    stc.STC_LEX_D),
    ("script.tcl",       None,                                    stc.STC_LEX_TCL),
    ("unknown.xyz",      None,                                    stc.STC_LEX_NULL),
    # shebang overrides extension-less file
    ("script",           "#!/usr/bin/env python3\nprint('hi')",   stc.STC_LEX_PYTHON),
    ("run",              "#!/bin/bash\necho hello",               stc.STC_LEX_BASH),
    ("unknowncommand",   "#!/bin/clash\necho hello",              stc.STC_LEX_NULL),
    ("runner",           "#!/usr/bin/ruby\nputs 'x'",             stc.STC_LEX_RUBY),
    # content XML declaration overrides unknown ext
    ("data.txt",         "<?xml version='1.0'?><root/>",          stc.STC_LEX_XML),
    ("unknownextension.unkx", "<?xml version='1.0'?><root/>",     stc.STC_LEX_XML),
    ("wrongextension.html", "<?xml version='1.0'?><root/>",       stc.STC_LEX_XML),
    # HTML doctype
    ("page.txt",         "<!DOCTYPE html>\n<html>",               stc.STC_LEX_HTML),
]


class TestLexDetect(unittest.TestCase):

    def test_valid_detections(self):
        passed = failed = 0
        for fname, content, expected in tests:
            got = detect(fname, content)
            ok = got == expected
            status = "OK" if ok else "FAIL"
            if not ok:
                print(f"  [{status}] detect({fname!r}) → {got!r}, expected {expected!r}")
                failed += 1
            else:
                passed += 1

        print(f"\nResults: {passed} passed, {failed} failed out of {len(tests)} tests")
        assert failed == 0

    def test_invalid_detections(self):
        ftests = [ ("Cargo.toml", None),  # stc.STC_LEX_TOML
                  ("app.dart", None),  # stc.STC_LEX_DART
                  ("main.zig", None),  # stc.STC_LEX_ZIG
                  ("game.gd", None),  # stc.STC_LEX_GDSCRIPT
                  ("prog.nim", None),  # stc.STC_LEX_NIM
                  ("app.jl", None),  # stc.STC_LEX_JULIA
                  # ASCIIDOC exists in Scintilla/wxWidgets but not in wxPython
                  ("readme.adoc", None)  # stc.STC_LEX_ASCIIDOC
                  ]
        passed = failed = 0
        for fname, content in ftests:
            got = detect(fname, content)
            ok = got == stc.STC_LEX_NULL
            status = "OK" if ok else "FAIL"
            if not ok:
                print(f"  [{status}] detect({fname!r}) → {got!r}")
                failed += 1
            else:
                passed += 1

        print(f"\nResults: {passed} passed, {failed} failed out of {len(tests)} tests")
        assert failed == 0

    def test_invalid_lex_code(self):
        result = stc_lex_code("STC_LEXICOGRAPHY")
        assert result == stc.STC_LEX_NULL

    def test_invalid_data(self):
        result = detect_from_file(os.path.join(datafilereader.DATAPATH, "bin", "binary.bin"))
        assert result == stc.STC_LEX_NULL

    def test_file_type_detections(self):
        result = detect_from_file(datafilereader.LIBRARY_WITH_SPACES_IN_PATH)
        assert result == stc.STC_LEX_PYTHON

    def test_invalid_file_type_detections(self):
        result = detect_from_file(datafilereader.RESOURCES_DIR + "/nonexisting.jason")
        assert result == stc.STC_LEX_NULL


if __name__ == '__main__':
    unittest.main()
