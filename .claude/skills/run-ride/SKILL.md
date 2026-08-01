---
name: run-ride
description: Run, launch, start, screenshot or GUI-test RIDE from source on a headless machine. Drives the real wxPython app (docking panes, tree, menus) via a driver script and asserts what actually rendered. Use for any change to ui/, editor/, or anything wxPython/AUI that unit tests cannot cover.
---

# Running RIDE

RIDE is a wxPython desktop GUI. It has no in-process automation API, so it is driven
from outside: a private Xvfb display, a window manager, XTEST input via `xdotool`,
and screenshots for observation. All of that is wrapped by
`.claude/skills/run-ride/driver.py`.

Paths below are relative to the repo root. Everything here was executed on Fedora 42,
Python 3.13, wxPython 4.2.x.

## Prerequisites

The driver needs these on `PATH` (all were already installed here):

```bash
for t in Xvfb xdotool import xdpyinfo wmctrl xfwm4 convert; do printf "%-10s %s\n" "$t" "$(command -v $t || echo MISSING)"; done
```

On Fedora these come from `xorg-x11-server-Xvfb`, `xdotool`, `ImageMagick`,
`xorg-x11-utils`, `wmctrl`, `xfwm4`. A window manager is **required**, not optional —
see Gotchas.

No build step: RIDE runs straight from `src/`.

## Run (agent path)

```bash
python .claude/skills/run-ride/driver.py up          # Xvfb + xfwm4 + RIDE, waits until ready
python .claude/skills/run-ride/driver.py shot /tmp/ride.png
python .claude/skills/run-ride/driver.py down        # stops everything, restores settings.cfg
```

`up` opens `rtest/testdir` by default; pass another path as an argument. It normalises the
main window to `0,0 1400x900` (so all gesture coordinates are reproducible) and parks the
floating Files pane out of the way.

Commands:

| Command | What it does |
|---|---|
| `up [suite]` | start display, WM and RIDE; wait for the main window |
| `down` | stop RIDE/WM/Xvfb, restore `~/.robotframework/ride/settings.cfg` |
| `shot [path]` | screenshot the whole display |
| `windows` | list top-level windows (a floating pane is its own window) |
| `dock-tree` | drag the floating Test Suites pane onto the left dock guide (retries 3x) |
| `float-tree` | drag the docked pane back out into a floating mini-frame |
| `check-tree` | assert the tree actually painted; exit 0 = RENDERED, 1 = BLANK |
| `toggle-tree` | hide/show the tree via the View menu |
| `click X Y` / `key KEY` | raw input |
| `park` / `normalize` | re-park floating panes / re-apply the known window rect |
| `log` | RIDE's stdout+stderr for this run |

Verified interaction — selecting a node updates the window title:

```bash
python .claude/skills/run-ride/driver.py click 85 165
python .claude/skills/run-ride/driver.py windows | head -1
```

```
0x00400094  0 localhost.localdomain RIDE - Suite
```

### check-tree: the assertion that matters

`check-tree` counts unique colours in the tree pane. A painted tree has hundreds; a blank
pane has ~2. This is the machine-checkable form of "the panel went blank", which is a real
recurring bug class here (fixed in `a75aa8ebd`; wxGTK stops sending paint events to a
reparented `ScrolledWindow`).

**Always run `dock-tree` immediately before `check-tree`.** Pixels cannot distinguish a
blank pane from a hidden one — with the pane hidden, the region shows the editor
underneath and reads as RENDERED.

### A/B a GUI regression across commits

`RIDE_SRC` points the driver at another checkout, so you can run an old commit with today's
driver. This is how the docking fix was verified:

```bash
git worktree add /tmp/ride-ctrl HEAD~1
cp -r src/robotide/preferences/configobj/. /tmp/ride-ctrl/src/robotide/preferences/configobj/
RIDE_SRC=/tmp/ride-ctrl/src python .claude/skills/run-ride/driver.py up
RIDE_SRC=/tmp/ride-ctrl/src python .claude/skills/run-ride/driver.py dock-tree
RIDE_SRC=/tmp/ride-ctrl/src python .claude/skills/run-ride/driver.py check-tree
```

Before the fix vs after, same driver, same gesture:

```
tree (docked TREE_REGION) unique colours: 2 -> BLANK        # HEAD~1, exit 1
tree (docked TREE_REGION) unique colours: 585 -> RENDERED   # HEAD,   exit 0
```

Clean up with `git worktree remove --force /tmp/ride-ctrl`.

## Test suite

```bash
timeout 300 xvfb-run -a python -m pytest utest/ui/ -q
```

81 tests, ~50s. `utest/ui/` is the relevant subset for UI work. Note that **no unit test
covers docking, painting or pane layout** — that is exactly why this driver exists.

## Run (human path)

`invoke devel` runs RIDE from source on your own display. Useless headless, and it does not
give you a programmatic handle on the app — prefer the driver above.

## Gotchas

- **`PYTHONPATH` must point at `src/`.** Plain `python -m robotide.__init__` imports the
  *installed* package from site-packages, so you silently test released code instead of your
  edits. The driver sets it and logs the resolved path — check it with `driver.py log | head -1`.
- **A window manager is required.** Without one, AUI floating mini-frames misbehave and
  `ClientToScreen` warnings flood the log. The driver starts `xfwm4`.
- **`xdotool key --window <id>` does nothing.** It sends a synthetic XSendEvent that GTK
  ignores. Only XTEST (plain `xdotool key`, i.e. `driver.py key`) works.
- **The F12 accelerator is unreliable** even via XTEST. Use `toggle-tree` (View menu), which
  is deterministic.
- **RIDE captures stdout**, so `print()` added inside the app does not reach the terminal.
  Write debug output to a file instead.
- **Runs rewrite `~/.robotframework/ride/settings.cfg`** (pane perspective, `opened`,
  `docked`). `up` backs it up and `down` restores it — always finish with `down`, or the
  user's layout silently changes.
- **Docking needs a genuine stepped drag.** AUI only raises its docking guides after a
  stream of motion events, and the drop must land *on* the guide (~(34, 478) at this window
  size). Twenty pixels off and the pane just moves instead of docking. `dock-tree` retries
  three times because the first drag does sometimes miss.
- **The floating Files pane overlaps the tree region.** Left in place it leaks colours into
  `check-tree` and a blank tree reads as RENDERED. `up` and `check-tree` park it.
- **A new `git worktree` has an empty `configobj` submodule**; copy it from the main
  checkout as shown above or RIDE will not import.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `no RIDE window after 90s` | `driver.py log` — usually an import error from a wrong `RIDE_SRC`. |
| `check-tree` says RENDERED but the screenshot looks empty | The pane is hidden or floating, so the region measured something else. Run `dock-tree` first. |
| `dock-tree` prints `still floating` after 3 attempts | Window geometry drifted; run `normalize`, then retry. |
| Stale `Xvfb` blocks startup | `driver.py down`, then remove `/tmp/.X99-lock`. |
| Want a second instance | `RIDE_DISPLAY=:98 python .claude/skills/run-ride/driver.py up`. |
