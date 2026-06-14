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

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, Union

LEXER_NAMES: dict[str, int] = {
    "STC_LEX_CONTAINER":       0,
    "STC_LEX_NULL":            1,
    "STC_LEX_PYTHON":          2,
    "STC_LEX_CPP":             3,
    "STC_LEX_HTML":            4,
    "STC_LEX_XML":             5,
    "STC_LEX_PERL":            6,
    "STC_LEX_SQL":             7,
    "STC_LEX_VB":              8,
    "STC_LEX_PROPERTIES":      9,
    "STC_LEX_ERRORLIST":       10,
    "STC_LEX_MAKEFILE":        11,
    "STC_LEX_BATCH":           12,
    "STC_LEX_XCODE":           13,
    "STC_LEX_LATEX":           14,
    "STC_LEX_LUA":             15,
    "STC_LEX_DIFF":            16,
    "STC_LEX_CONF":            17,
    "STC_LEX_PASCAL":          18,
    "STC_LEX_AVE":             19,
    "STC_LEX_ADA":             20,
    "STC_LEX_LISP":            21,
    "STC_LEX_RUBY":            22,
    "STC_LEX_EIFFEL":          23,
    "STC_LEX_EIFFELKW":        24,
    "STC_LEX_TCL":             25,
    "STC_LEX_NNCRONTAB":       26,
    "STC_LEX_BULLANT":         27,
    "STC_LEX_VBSCRIPT":        28,
    "STC_LEX_BAAN":            31,
    "STC_LEX_MATLAB":          32,
    "STC_LEX_SCRIPTOL":        33,
    "STC_LEX_ASM":             34,
    "STC_LEX_CPPNOCASE":       35,
    "STC_LEX_FORTRAN":         36,
    "STC_LEX_F77":             37,
    "STC_LEX_CSS":             38,
    "STC_LEX_POV":             39,
    "STC_LEX_LOUT":            40,
    "STC_LEX_ESCRIPT":         41,
    "STC_LEX_PS":              42,
    "STC_LEX_NSIS":            43,
    "STC_LEX_MMIXAL":          44,
    "STC_LEX_CLW":             45,
    "STC_LEX_CLWNOCASE":       46,
    "STC_LEX_LOT":             47,
    "STC_LEX_YAML":            48,
    "STC_LEX_TEX":             49,
    "STC_LEX_METAPOST":        50,
    "STC_LEX_POWERBASIC":      51,
    "STC_LEX_FORTH":           52,
    "STC_LEX_ERLANG":          53,
    "STC_LEX_OCTAVE":          54,
    "STC_LEX_MSSQL":           55,
    "STC_LEX_VERILOG":         56,
    "STC_LEX_KIX":             57,
    "STC_LEX_GUI4CLI":         58,
    "STC_LEX_SPECMAN":         59,
    "STC_LEX_AU3":             60,
    "STC_LEX_APDL":            61,
    "STC_LEX_BASH":            62,
    "STC_LEX_ASN1":            63,
    "STC_LEX_VHDL":            64,
    "STC_LEX_CAML":            65,
    "STC_LEX_BLITZBASIC":      66,
    "STC_LEX_PUREBASIC":       67,
    "STC_LEX_HASKELL":         68,
    "STC_LEX_PHPSCRIPT":       69,
    "STC_LEX_TADS3":           70,
    "STC_LEX_REBOL":           71,
    "STC_LEX_SMALLTALK":       72,
    "STC_LEX_FLAGSHIP":        73,
    "STC_LEX_CSOUND":          74,
    "STC_LEX_FREEBASIC":       75,
    "STC_LEX_INNOSETUP":       76,
    "STC_LEX_OPAL":            77,
    "STC_LEX_SPICE":           78,
    "STC_LEX_D":               79,
    "STC_LEX_CMAKE":           80,
    "STC_LEX_GAP":             81,
    "STC_LEX_PLM":             82,
    "STC_LEX_PROGRESS":        83,
    "STC_LEX_ABAQUS":          84,
    "STC_LEX_ASYMPTOTE":       85,
    "STC_LEX_R":               86,
    "STC_LEX_MAGIK":           87,
    "STC_LEX_POWERSHELL":      88,
    "STC_LEX_MYSQL":           89,
    "STC_LEX_PO":              90,
    "STC_LEX_TAL":             91,
    "STC_LEX_COBOL":           92,
    "STC_LEX_TACL":            93,
    "STC_LEX_SORCUS":          94,
    "STC_LEX_POWERPRO":        95,
    "STC_LEX_NIMROD":          96,   # older alias for NIM
    "STC_LEX_SML":             97,
    "STC_LEX_MARKDOWN":        98,
    "STC_LEX_TXT2TAGS":        99,
    "STC_LEX_A68K":            100,
    "STC_LEX_MODULA":          101,
    "STC_LEX_COFFEESCRIPT":    102,
    "STC_LEX_TCMD":            103,
    "STC_LEX_AVS":             104,
    "STC_LEX_ECL":             105,
    "STC_LEX_OSCRIPT":         106,
    "STC_LEX_VISUALPROLOG":    107,
    "STC_LEX_LITERATEHASKELL": 108,
    "STC_LEX_STTXT":           109,
    "STC_LEX_KVIRC":           110,
    "STC_LEX_RUST":            111,
    "STC_LEX_DMAP":            112,
    "STC_LEX_AS":              113,
    "STC_LEX_DMIS":            114,
    "STC_LEX_REGISTRY":        115,
    "STC_LEX_BIBTEX":          116,
    "STC_LEX_SREC":            117,
    "STC_LEX_IHEX":            118,
    "STC_LEX_TEHEX":           119,
    "STC_LEX_JSON":            120,
    "STC_LEX_EDIFACT":         121,
    "STC_LEX_INDENT":          122,
    "STC_LEX_MAXIMA":          123,
    "STC_LEX_STATA":           124,
    "STC_LEX_SAS":             125,
    "STC_LEX_NIM":             126,
    "STC_LEX_CIL":             127,
    "STC_LEX_X12":             128,
    "STC_LEX_DATAFLEX":        129,
    "STC_LEX_HOLLYWOOD":       130,
    "STC_LEX_RAKU":            131,
    "STC_LEX_FSHARP":          132,
    "STC_LEX_JULIA":           133,
    "STC_LEX_ASCIIDOC":        134,
    "STC_LEX_GDSCRIPT":        135,
    "STC_LEX_TOML":            136,
    "STC_LEX_TROFF":           137,
    "STC_LEX_DART":            138,
    "STC_LEX_ZIG":             139,
    "STC_LEX_NIX":             140,
    "STC_LEX_SINEX":           141,
    "STC_LEX_AUTOMATIC":       1000,
}

# ---------------------------------------------------------------------------
# Extension → lexer  (lowercase extension without leading dot → STC_LEX_*)
# ---------------------------------------------------------------------------

_EXT_MAP: dict[str, str] = {
    # Python
    "py":      "STC_LEX_PYTHON",
    "pyw":     "STC_LEX_PYTHON",
    "pyi":     "STC_LEX_PYTHON",
    "pyx":     "STC_LEX_PYTHON",   # Cython
    "pxd":     "STC_LEX_PYTHON",

    # C / C++ / ObjC  (all share the CPP lexer)
    "c":       "STC_LEX_CPP",
    "cc":      "STC_LEX_CPP",
    "cpp":     "STC_LEX_CPP",
    "cxx":     "STC_LEX_CPP",
    "c++":     "STC_LEX_CPP",
    "h":       "STC_LEX_CPP",
    "hh":      "STC_LEX_CPP",
    "hpp":     "STC_LEX_CPP",
    "hxx":     "STC_LEX_CPP",
    "h++":     "STC_LEX_CPP",
    "m":       "STC_LEX_CPP",      # Objective-C
    "mm":      "STC_LEX_CPP",      # Objective-C++
    "cs":      "STC_LEX_CPP",      # C#
    "java":    "STC_LEX_CPP",
    "js":      "STC_LEX_CPP",
    "mjs":     "STC_LEX_CPP",
    "cjs":     "STC_LEX_CPP",
    "jsx":     "STC_LEX_CPP",
    "ts":      "STC_LEX_CPP",      # TypeScript
    "tsx":     "STC_LEX_CPP",
    "kt":      "STC_LEX_CPP",      # Kotlin
    "kts":     "STC_LEX_CPP",
    "swift":   "STC_LEX_CPP",
    "go":      "STC_LEX_CPP",
    "sc":      "STC_LEX_CPP",      # Scala script
    "scala":   "STC_LEX_CPP",
    "groovy":  "STC_LEX_CPP",
    "ino":     "STC_LEX_CPP",      # Arduino

    # HTML / web
    "html":    "STC_LEX_HTML",
    "htm":     "STC_LEX_HTML",
    "shtml":   "STC_LEX_HTML",
    "xhtml":   "STC_LEX_HTML",
    "php":     "STC_LEX_HTML",     # PHP embedded in HTML
    "php3":    "STC_LEX_HTML",
    "php4":    "STC_LEX_HTML",
    "php5":    "STC_LEX_HTML",
    "phtml":   "STC_LEX_HTML",
    "asp":     "STC_LEX_HTML",
    "aspx":    "STC_LEX_HTML",
    "vue":     "STC_LEX_HTML",
    "svelte":  "STC_LEX_HTML",

    # XML family
    "xml":     "STC_LEX_XML",
    "xsl":     "STC_LEX_XML",
    "xslt":    "STC_LEX_XML",
    "xsd":     "STC_LEX_XML",
    "wsdl":    "STC_LEX_XML",
    "svg":     "STC_LEX_XML",
    "kml":     "STC_LEX_XML",
    "gpx":     "STC_LEX_XML",
    "rss":     "STC_LEX_XML",
    "atom":    "STC_LEX_XML",
    "plist":   "STC_LEX_XML",
    "xaml":    "STC_LEX_XML",
    "resx":    "STC_LEX_XML",
    "csproj":  "STC_LEX_XML",
    "vbproj":  "STC_LEX_XML",
    "vcxproj": "STC_LEX_XML",
    "props":   "STC_LEX_XML",      # MSBuild .props
    "targets": "STC_LEX_XML",

    # Perl
    "pl":      "STC_LEX_PERL",
    "pm":      "STC_LEX_PERL",
    "pod":     "STC_LEX_PERL",
    "t":       "STC_LEX_PERL",     # Perl test files

    # SQL
    "sql":     "STC_LEX_SQL",
    "ddl":     "STC_LEX_SQL",
    "dml":     "STC_LEX_SQL",

    # VB / VBA / VBScript
    "vb":      "STC_LEX_VB",
    "vba":     "STC_LEX_VB",
    "bas":     "STC_LEX_VB",
    "frm":     "STC_LEX_VB",
    # "cls":     "STC_LEX_VB",
    "vbs":     "STC_LEX_VBSCRIPT",

    # .properties / .ini  →  PROPERTIES lexer
    "properties": "STC_LEX_PROPERTIES",
    "ini":        "STC_LEX_PROPERTIES",
    "inf":        "STC_LEX_PROPERTIES",
    "cfg":        "STC_LEX_CONF",      # Apache-style
    "conf":       "STC_LEX_CONF",
    "cnf":        "STC_LEX_CONF",

    # Makefile / build
    "mk":      "STC_LEX_MAKEFILE",
    "mak":     "STC_LEX_MAKEFILE",

    # Batch / shell
    "bat":     "STC_LEX_BATCH",
    "cmd":     "STC_LEX_BATCH",
    "btm":     "STC_LEX_BATCH",
    "sh":      "STC_LEX_BASH",
    "bash":    "STC_LEX_BASH",
    "zsh":     "STC_LEX_BASH",
    "ksh":     "STC_LEX_BASH",
    "fish":    "STC_LEX_BASH",
    "csh":     "STC_LEX_BASH",
    "tcsh":    "STC_LEX_BASH",
    "ps1":     "STC_LEX_POWERSHELL",
    "psm1":    "STC_LEX_POWERSHELL",
    "psd1":    "STC_LEX_POWERSHELL",

    # LaTeX / TeX
    "tex":     "STC_LEX_LATEX",
    "ltx":     "STC_LEX_LATEX",
    "sty":     "STC_LEX_LATEX",
    "cls":     "STC_LEX_LATEX",    # also VB but tex wins for .cls
    "bib":     "STC_LEX_BIBTEX",
    "mp":      "STC_LEX_METAPOST",

    # Lua
    "lua":     "STC_LEX_LUA",

    # Diff / patch
    "diff":    "STC_LEX_DIFF",
    "patch":   "STC_LEX_DIFF",

    # Pascal / Delphi
    "pas":     "STC_LEX_PASCAL",
    "pp":      "STC_LEX_PASCAL",
    "dpr":     "STC_LEX_PASCAL",
    "inc":     "STC_LEX_PASCAL",

    # Ada
    "ads":     "STC_LEX_ADA",
    "adb":     "STC_LEX_ADA",

    # Lisp / Scheme / Clojure
    "lisp":    "STC_LEX_LISP",
    "lsp":     "STC_LEX_LISP",
    "scm":     "STC_LEX_LISP",
    "ss":      "STC_LEX_LISP",
    "el":      "STC_LEX_LISP",     # Emacs Lisp
    "clj":     "STC_LEX_LISP",
    "cljs":    "STC_LEX_LISP",
    "cljc":    "STC_LEX_LISP",

    # Ruby
    "rb":      "STC_LEX_RUBY",
    "rbw":     "STC_LEX_RUBY",
    "rake":    "STC_LEX_RUBY",
    "gemspec": "STC_LEX_RUBY",
    "ru":      "STC_LEX_RUBY",     # Rack config

    # TCL
    "tcl":     "STC_LEX_TCL",
    "tk":      "STC_LEX_TCL",

    # YAML
    "yaml":    "STC_LEX_YAML",
    "yml":     "STC_LEX_YAML",

    # Matlab / Octave
    "m":       "STC_LEX_MATLAB",   # also ObjC — context determines it
    "octave":  "STC_LEX_OCTAVE",

    # Assembly
    "asm":     "STC_LEX_ASM",
    "s":       "STC_LEX_ASM",
    "nasm":    "STC_LEX_ASM",

    # Fortran
    "f":       "STC_LEX_FORTRAN",
    "for":     "STC_LEX_FORTRAN",
    "f90":     "STC_LEX_FORTRAN",
    "f95":     "STC_LEX_FORTRAN",
    "f03":     "STC_LEX_FORTRAN",
    "f08":     "STC_LEX_FORTRAN",
    "f77":     "STC_LEX_F77",

    # CSS
    "css":     "STC_LEX_CSS",
    "scss":    "STC_LEX_CSS",
    "sass":    "STC_LEX_CSS",
    "less":    "STC_LEX_CSS",

    # PostScript
    "ps":      "STC_LEX_PS",
    "eps":     "STC_LEX_PS",

    # NSIS installer script
    "nsi":     "STC_LEX_NSIS",
    "nsh":     "STC_LEX_NSIS",

    # YAML → already covered; LOT
    "lot":     "STC_LEX_LOT",

    # Haskell
    "hs":      "STC_LEX_HASKELL",
    "lhs":     "STC_LEX_LITERATEHASKELL",

    # Erlang
    "erl":     "STC_LEX_ERLANG",
    "hrl":     "STC_LEX_ERLANG",

    # PHP (pure PHP, no HTML)
    "phps":    "STC_LEX_PHPSCRIPT",

    # Verilog / VHDL
    "v":       "STC_LEX_VERILOG",
    "sv":      "STC_LEX_VERILOG",
    "svh":     "STC_LEX_VERILOG",
    "vhd":     "STC_LEX_VHDL",
    "vhdl":    "STC_LEX_VHDL",

    # OCaml / SML / F#
    "ml":      "STC_LEX_CAML",
    "mli":     "STC_LEX_CAML",
    "sml":     "STC_LEX_SML",
    "sig":     "STC_LEX_SML",
    "fs":      "STC_LEX_FSHARP",
    "fsi":     "STC_LEX_FSHARP",
    "fsx":     "STC_LEX_FSHARP",
    "fsproj":  "STC_LEX_XML",

    # Markdown
    "md":      "STC_LEX_MARKDOWN",
    "markdown":"STC_LEX_MARKDOWN",
    "mdown":   "STC_LEX_MARKDOWN",
    "mkd":     "STC_LEX_MARKDOWN",

    # AsciiDoc
    "adoc":    "STC_LEX_ASCIIDOC",
    "asciidoc":"STC_LEX_ASCIIDOC",

    # D language
    "d":       "STC_LEX_D",
    "di":      "STC_LEX_D",

    # CMake
    "cmake":   "STC_LEX_CMAKE",

    # R language
    "r":       "STC_LEX_R",
    "rmd":     "STC_LEX_R",

    # PowerShell already covered above

    # MySQL / MS-SQL specific
    # (generic .sql already → SQL; specific drivers use same ext)

    # COBOL
    "cbl":     "STC_LEX_COBOL",
    "cob":     "STC_LEX_COBOL",
    "pco":     "STC_LEX_COBOL",

    # Nim
    "nim":     "STC_LEX_NIM",
    "nims":    "STC_LEX_NIM",
    "nimble":  "STC_LEX_NIM",

    # CoffeeScript
    "coffee":  "STC_LEX_COFFEESCRIPT",
    "litcoffee":"STC_LEX_COFFEESCRIPT",

    # Rust
    "rs":      "STC_LEX_RUST",

    # JSON / JSONC / JSONL
    "json":    "STC_LEX_JSON",
    "jsonc":   "STC_LEX_JSON",
    "jsonl":   "STC_LEX_JSON",
    "geojson": "STC_LEX_JSON",
    "json5":   "STC_LEX_JSON",

    # TOML
    "toml":    "STC_LEX_TOML",

    # Julia
    "jl":      "STC_LEX_JULIA",

    # GDScript (Godot)
    "gd":      "STC_LEX_GDSCRIPT",

    # Dart
    "dart":    "STC_LEX_DART",

    # Zig
    "zig":     "STC_LEX_ZIG",

    # Nix expression language
    "nix":     "STC_LEX_NIX",

    # Raku (Perl 6)
    "raku":    "STC_LEX_RAKU",
    "rakumod": "STC_LEX_RAKU",
    "rakutest":"STC_LEX_RAKU",
    "p6":      "STC_LEX_RAKU",
    "pm6":     "STC_LEX_RAKU",

    # Windows registry
    "reg":     "STC_LEX_REGISTRY",

    # Smalltalk
    "st":      "STC_LEX_SMALLTALK",

    # PO / gettext
    "po":      "STC_LEX_PO",
    "pot":     "STC_LEX_PO",

    # Tcmd (4NT / Take Command batch)
    "btm":     "STC_LEX_TCMD",    # also BATCH; prefer TCMD

    # AVS (AviSynth / VapourSynth)
    "avs":     "STC_LEX_AVS",
    "avsi":    "STC_LEX_AVS",

    # SPICE netlist
    "spi":     "STC_LEX_SPICE",
    "sp":      "STC_LEX_SPICE",

    # SAS
    "sas":     "STC_LEX_SAS",

    # Stata
    "do":      "STC_LEX_STATA",
    "ado":     "STC_LEX_STATA",

    # KiviRC script
    "kvs":     "STC_LEX_KVIRC",

    # ASN.1
    "asn":     "STC_LEX_ASN1",
    "asn1":    "STC_LEX_ASN1",

    # SREC / Intel HEX  (text-based firmware formats)
    "srec":    "STC_LEX_SREC",
    "mot":     "STC_LEX_SREC",
    "s19":     "STC_LEX_SREC",
    "s28":     "STC_LEX_SREC",
    "s37":     "STC_LEX_SREC",
    "hex":     "STC_LEX_IHEX",
    "ihex":    "STC_LEX_IHEX",

    # Forth
    "fth":     "STC_LEX_FORTH",
    "forth":   "STC_LEX_FORTH",

    # Visual Prolog
    "pro":     "STC_LEX_VISUALPROLOG",

    # Troff / nroff / groff
    "roff":    "STC_LEX_TROFF",
    "1":       "STC_LEX_TROFF",   # man pages
    "2":       "STC_LEX_TROFF",
    "3":       "STC_LEX_TROFF",
    "4":       "STC_LEX_TROFF",
    "5":       "STC_LEX_TROFF",
    "6":       "STC_LEX_TROFF",
    "7":       "STC_LEX_TROFF",
    "8":       "STC_LEX_TROFF",
    "me":      "STC_LEX_TROFF",
    "ms":      "STC_LEX_TROFF",
    "mm":      "STC_LEX_TROFF",

    # Eiffel
    "e":       "STC_LEX_EIFFEL",

    # Rebol
    "r":       "STC_LEX_REBOL",   # also R; shebang/content resolves
    "reb":     "STC_LEX_REBOL",

    # AutoIt3
    "au3":     "STC_LEX_AU3",
}

# ---------------------------------------------------------------------------
# Basename → lexer  (exact filename matches, case-insensitive)
# ---------------------------------------------------------------------------

_BASENAME_MAP: dict[str, str] = {
    "makefile":        "STC_LEX_MAKEFILE",
    "gnumakefile":     "STC_LEX_MAKEFILE",
    "bsdmakefile":     "STC_LEX_MAKEFILE",
    "cmakelists.txt":  "STC_LEX_CMAKE",
    "dockerfile":      "STC_LEX_BASH",    # shell-like syntax
    ".bashrc":         "STC_LEX_BASH",
    ".bash_profile":   "STC_LEX_BASH",
    ".bash_aliases":   "STC_LEX_BASH",
    ".zshrc":          "STC_LEX_BASH",
    ".zshenv":         "STC_LEX_BASH",
    ".profile":        "STC_LEX_BASH",
    ".bash_history":   "STC_LEX_BASH",
    "gemfile":         "STC_LEX_RUBY",
    "rakefile":        "STC_LEX_RUBY",
    "vagrantfile":     "STC_LEX_RUBY",
    "podfile":         "STC_LEX_RUBY",
    ".htaccess":       "STC_LEX_CONF",
    "nginx.conf":      "STC_LEX_CONF",
    "httpd.conf":      "STC_LEX_CONF",
    "package.json":    "STC_LEX_JSON",
    "tsconfig.json":   "STC_LEX_JSON",
    ".eslintrc":       "STC_LEX_JSON",
    "cargo.toml":      "STC_LEX_TOML",
    "pyproject.toml":  "STC_LEX_TOML",
    ".gitignore":      "STC_LEX_CONF",
    ".gitattributes":  "STC_LEX_CONF",
    "requirements.txt":"STC_LEX_CONF",
}

# ---------------------------------------------------------------------------
# Shebang / content patterns
# ---------------------------------------------------------------------------

# Ordered list of (regex_pattern, lexer_name).  Checked against the first
# line (or first ~512 bytes decoded as UTF-8/latin-1) of the file.
_SHEBANG_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"python[23]?", re.I),       "STC_LEX_PYTHON"),
    (re.compile(r"\bperl\b", re.I),          "STC_LEX_PERL"),
    (re.compile(r"\bruby\b", re.I),          "STC_LEX_RUBY"),
    (re.compile(r"\blua\b", re.I),           "STC_LEX_LUA"),
    (re.compile(r"\b(bash|sh|zsh|ksh|csh|dash|fish)\b", re.I), "STC_LEX_BASH"),
    (re.compile(r"\bnode\b", re.I),          "STC_LEX_CPP"),
    (re.compile(r"\btcl(sh)?\b", re.I),      "STC_LEX_TCL"),
    (re.compile(r"\bphp\b", re.I),           "STC_LEX_HTML"),
    (re.compile(r"\bawk\b", re.I),           "STC_LEX_CPP"),
    (re.compile(r"\braku\b|\bperl6\b", re.I),"STC_LEX_RAKU"),
    (re.compile(r"\br\b", re.I),             "STC_LEX_R"),
]

# XML / HTML declaration heuristics (match at start of content)
_CONTENT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^\s*<\?xml\b", re.I),      "STC_LEX_XML"),
    (re.compile(r"^\s*<!DOCTYPE\s+html\b", re.I), "STC_LEX_HTML"),
    (re.compile(r"^\s*<html\b", re.I),       "STC_LEX_HTML"),
    (re.compile(r"^\s*\{", re.I),            "STC_LEX_JSON"),  # weak signal only
    (re.compile(r"^---\s*$", re.M),          "STC_LEX_YAML"),  # YAML front-matter
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_text(content: Union[str, bytes, None], limit: int = 512) -> Optional[str]:
    """Return up to *limit* bytes/chars as a str, or None."""
    if content is None:
        return None
    if isinstance(content, bytes):
        try:
            return content[:limit].decode("utf-8", errors="replace")
        except Exception:
            return None
    return content[:limit]


def _detect_by_shebang(first_line: str) -> Optional[str]:
    """Return lexer name if *first_line* is a shebang we recognise."""
    if not first_line.startswith("#!"):
        return None
    for pattern, name in _SHEBANG_PATTERNS:
        if pattern.search(first_line):
            return name
    return None


def _detect_by_content(text: str) -> Optional[str]:
    """Apply content heuristics other than shebang."""
    for pattern, name in _CONTENT_PATTERNS:
        if pattern.search(text):
            return name
    return None


def stc_lex_code(text: str) -> int:
    from wx import stc
    if not text.startswith("STC_LEX_"):
        return stc.STC_LEX_NULL
    try:
        lex_code = eval(f"stc.{text}")
    except Exception:
        lex_code = stc.STC_LEX_NULL
    return lex_code


def detect(
    filename: Union[str, "os.PathLike[str]"],
    content: Union[str, bytes, None] = None,
) -> int:
    """
    Detect the ``STC_LEX_*`` type for a text-mode file.

    Detection order
    ---------------
    1. Exact basename match (e.g. ``Makefile``, ``Dockerfile``).
    2. File extension lookup (e.g. ``.py`` → ``STC_LEX_PYTHON``).
    3. Shebang line in content (``#!/usr/bin/env python3``).
    4. Broader content heuristics (XML declaration, HTML tag, …).
    5. Fall back to ``STC_LEX_NULL``.

    Parameters
    ----------
    filename:
        Path or bare filename; only the basename/extension is inspected.
    content:
        Optional raw content of the file (str or bytes).  When provided,
        shebang and content-pattern detection are also applied.

    Returns
    -------
    int
        A ``STC_LEX_*`` constant.
    """
    path = Path(os.fspath(filename))
    basename = path.name.lower()
    ext = path.suffix.lstrip(".").lower()  # e.g. "py", "cpp", ""

    # 1. Basename map
    if basename in _BASENAME_MAP:
        return stc_lex_code(_BASENAME_MAP[basename])

    # 2. Extension map
    if ext and ext in _EXT_MAP:
        ext_result = _EXT_MAP[ext]
    else:
        ext_result = None

    # 3 + 4. Content-based detection
    text = _to_text(content)
    if text:
        first_line = text.splitlines()[0] if text.splitlines() else ""

        shebang_result = _detect_by_shebang(first_line)
        if shebang_result:
            return stc_lex_code(shebang_result)

        content_result = _detect_by_content(text)
        if content_result:
            # Prefer content signal for ambiguous extensions
            if ext_result is None:
                return stc_lex_code(content_result)
            # Content XML/HTML beats a vague extension
            if content_result in ("STC_LEX_XML", "STC_LEX_HTML"):
                return stc_lex_code(content_result)

    # 5. Extension result or NULL
    return stc_lex_code(ext_result or "STC_LEX_NULL")


def detect_from_file(path: Union[str, "os.PathLike[str]"]) -> int:
    """
    Convenience wrapper: open *path*, read the first 512 bytes, and return
    the detected ``STC_LEX_*`` constant.

    Parameters
    ----------
    path:
        Path to the file on disk.

    Returns
    -------
    int
        A ``STC_LEX_*`` constant.
    """
    p = Path(os.fspath(path))
    try:
        with p.open("rb") as fh:
            raw = fh.read(512)
    except OSError:
        raw = b""
    return detect(p, raw)
