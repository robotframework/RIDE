# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

RIDE is a desktop GUI IDE for editing Robot Framework test/task data, built with **wxPython**. The
package lives under `src/robotide/`, is installed as `robotframework-ride`, and ships a bundled
(vendored) copy of Robot Framework's core under `src/robotide/lib/robot` — not a pip dependency.
Supported Python range is 3.9–3.14 (see `pyproject.toml`).

## Setup

This repo has a git submodule (`src/robotide/preferences/configobj`, vendored `configobj` library).
After cloning or pulling, run:

```bash
git submodule init
git submodule update
```

Install dev dependencies with `pip install -U -r requirements-dev.txt` (this also pulls in
`requirements.txt`, which lists runtime deps: wxPython, robotframework, Pygments, PyPubSub, psutil...).

RIDE is a GUI app requiring wxPython, which in turn requires a display. On headless Linux (CI), tests
run under Xvfb (`Xvfb & ; export DISPLAY=:0`). Many unit tests import `wx` at module scope and will
fail to collect without a working display/wx install.

## Common commands

This project uses **Invoke** (`tasks.py`) as its task runner, not raw pytest/setuptools, for most flows.

```bash
invoke --list          # list all available tasks
invoke devel           # run RIDE from source (no install)
invoke devel -a --debugconsole   # run with wx inspection tool + Python debug console
invoke test             # run the full unit test suite (utest/) via pytest
invoke test-ci          # run tests with coverage, split across 3 batches, generate html/xml reports
invoke clean            # remove bytecode, build/, dist/
invoke version 2.2.5    # rewrite src/robotide/version.py (auto-generated, don't hand-edit)
```

Because `pytest.ini` sets `pythonpath = src src/robotide/preferences/configobj/src`, you can also
invoke pytest directly for a subset of tests without going through `invoke`:

```bash
pytest utest/namespace/test_namespace.py           # single test file
pytest utest/namespace/test_namespace.py::test_foo # single test
pytest utest/some_dir -k "pattern"                 # filter by name
```

`invoke test` always runs `utest/application/test_app_main.py` as its own pytest process first
(it does low-level `wx` import-failure simulation and must not share process state with the rest of
the suite), then runs the rest of `utest/` separately.

There's also a customizable helper script `./test_all.sh utest/namespace` that runs a directory of
tests stopping on first failure (requires local customization).

Type checking: an in-progress `ty check` (Astral `ty`) workflow exists (`.github/workflows/ty.yml`);
run `ty check` locally if diagnosing type issues flagged in CI.

Linting: `.pylintrc` (pylint) and `pycodestyle` (`setup.cfg`, `max_line_length=90`) are configured;
CONTRIBUTING.adoc states a 100-character line-length guideline for hand-written code.

## Architecture

Not strict MVC, but a clear separation between a data/domain layer, a wx UI layer, and a plugin
system tying them together.

**Startup chain**: `robotide/__init__.py:main()` → `_run()` → instantiates `robotide.application.RIDE`
(a `wx.App` subclass, `application/application.py`) → `RIDE.OnInit()` creates a `Namespace`, then a
`Project` controller, then the main frame (`ui/mainframe.py:RideFrame`), then loads plugins, restores
the AUI layout, and calls `ride.MainLoop()`.

**Key directories**:
- `controller/` — the model/domain layer: `Project`, file controllers (suite/resource), test case /
  keyword / step controllers, setting controllers. Implements undoable, observable edits over the
  parsed test data via a command pattern (`ctrlcommands.py`), decoupled from the UI.
- `namespace/` — resolves what keywords/libraries/resources/variables are visible/importable at a
  given point (backed by a library cache); drives content-assist/autocomplete. Distinct from
  `controller/`: controller = "what's in this suite", namespace = "what's resolvable/suggestable here".
- `spec/` — library/resource spec discovery and caching (`iteminfo.py` keyword/variable info objects
  feed `namespace/` and `editor/contentassist.py`).
- `ui/` — the wx shell: `RideFrame` (main frame with an AUI manager docking the tree, file explorer,
  and a central `NoteBook` tab container), dialogs, tree view.
- `editor/` — grid editor and text editor for test cases/keywords/settings, packaged as plugins
  (`EditorPlugin`, `TextEditorPlugin`) that dock into `RideFrame`'s notebook.
- `application/` — composition root: the `RIDE` wx.App, `PluginLoader` (discovers/loads plugin
  classes from install dir + user plugin dirs), `PluginConnector` (per-plugin enable/settings state).
- `pluginapi/` — the public plugin API: `Plugin` base class (provides `subscribe()` for pub-sub and
  `add_tab()` to dock a panel into the notebook) that both core and third-party plugins subclass.
  Core plugins are enumerated in `context/coreplugins.py`.
- `publish/` — an internal pub-sub event bus wrapping **PyPubSub**. A singleton `PUBLISHER` is used
  everywhere to decouple model changes from UI updates; typed `RideMessage` subclasses in
  `publish/messages.py` map to topic strings, published via `SomeMessage(...).publish()` and consumed
  via `PUBLISHER.subscribe(handler, MessageClass)` or `Plugin.subscribe(...)`.
- `lib/robot` — vendored Robot Framework core (parsing, running, result, output, model, etc.), kept
  in sync via `invoke update_robot` (checks out a robotframework repo, copies `src/robot` in, and
  rewrites `from robot.` imports to `from robotide.lib.robot.`). Treat this as third-party/vendored
  code, not first-party RIDE code.
- `preferences/` — preferences dialogs + persisted settings (`configobj`-based `RideSettings`); has
  its own settings-migration mechanism (`SettingsMigrator`) for upgrading old user config files
  across RIDE versions — see "Settings migration" in `BUILD.rest` before changing settings schemas.
- `run/`, `log/`, `parserlog/`, `recentfiles/`, `searchtests/`, `usages/` — individual feature plugins
  (test execution tab, log/report viewer, parse-error viewer, recent files, search, find-usages).
- `action/`, `widgets/`, `utils/`, `validators/` — menu/toolbar/shortcut wiring, reusable wx widget
  wrappers, generic helpers, and field validators, respectively.

## Coding conventions (from CONTRIBUTING.adoc)

- Method names: `lowercase_with_underscore`, except when overriding wx methods (`AllCapitalized`,
  e.g. `OnInit`) and event handlers, which follow `OnEventName` (e.g. `OnMouseClick`).
- No blank lines inside functions; no blank lines between a class declaration and its attributes or
  between attributes; indentation with spaces only; no trailing whitespace; files must end with a
  newline and have no extra trailing blank lines.
- Docstrings on public APIs only (PEP-257 style); not expected in internal code.
- Code targets Python 3.9+ but some Python-2-era conditioning may still linger due to legacy dual
  support and the vendored Robot Framework code — don't be surprised by it, but don't propagate it
  in new code.
