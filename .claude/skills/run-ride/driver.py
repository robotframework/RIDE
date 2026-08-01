#!/usr/bin/env python3
"""Headless launcher/driver for RIDE (wxPython GUI).

RIDE has no in-process automation API, so this drives it from outside via XTEST
(xdotool) on a private Xvfb display, and observes it via screenshots.

    python .claude/skills/run-ride/driver.py up
    python .claude/skills/run-ride/driver.py shot /tmp/a.png
    python .claude/skills/run-ride/driver.py dock-tree
    python .claude/skills/run-ride/driver.py check-tree
    python .claude/skills/run-ride/driver.py down

Run `driver.py help` for the full command list.
"""
import os
import shutil
import signal
import subprocess
import sys
import time

DISPLAY = os.environ.get('RIDE_DISPLAY', ':99')
SCREEN_W, SCREEN_H = 1400, 900
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
# Point RIDE_SRC at another checkout (e.g. a `git worktree` of an older commit) to
# run that code with this driver -- how you A/B a GUI regression.
SRC = os.path.abspath(os.environ.get('RIDE_SRC', os.path.join(REPO, 'src')))
RUNDIR = f"/tmp/ride-run{DISPLAY.replace(':', '-')}"
SETTINGS = os.path.expanduser('~/.robotframework/ride/settings.cfg')
SETTINGS_BAK = os.path.join(RUNDIR, 'settings.cfg.bak')
DEFAULT_SUITE = 'rtest/testdir'

# Geometry of the docked tree pane once the main window is normalised to
# 0,0 SCREEN_W x SCREEN_H. Used by check-tree and the dock/float gestures.
TREE_REGION = (2, 100, 270, 760)          # x, y, w, h
LEFT_DOCK_GUIDE = (34, 478)               # AUI left docking guide
DOCKED_CAPTION = (60, 89)                 # "Test Suites" caption when docked


def env():
    e = dict(os.environ)
    e['DISPLAY'] = DISPLAY
    return e


def x(*args, **kw):
    """Run a command on the driver's display."""
    return subprocess.run(args, env=env(), capture_output=True, text=True, **kw)


def xdo(*args):
    return x('xdotool', *args).stdout.strip()


def need(*tools):
    missing = [t for t in tools if not shutil.which(t)]
    if missing:
        sys.exit(f"missing required tools: {' '.join(missing)}\n"
                 f"install with: sudo dnf install {' '.join(missing)}  # or apt-get install")


def pidfile(name):
    return os.path.join(RUNDIR, f'{name}.pid')


def write_pid(name, pid):
    os.makedirs(RUNDIR, exist_ok=True)
    with open(pidfile(name), 'w') as f:
        f.write(str(pid))


def read_pid(name):
    try:
        with open(pidfile(name)) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def kill(name):
    pid = read_pid(name)
    if pid:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.kill(pid, sig)
                time.sleep(1)
            except ProcessLookupError:
                break
        try:
            os.remove(pidfile(name))
        except OSError:
            pass


def display_up():
    return x('xdpyinfo').returncode == 0


def main_window():
    ids = xdo('search', '--name', '^RIDE - ')
    return ids.split('\n')[0] if ids else None


def find_window(pattern):
    ids = xdo('search', '--name', pattern)
    return ids.split('\n')[0] if ids else None


def cmd_up(args):
    """Start Xvfb + window manager + RIDE, and wait until the main window exists."""
    need('Xvfb', 'xfwm4', 'xdotool', 'import', 'xdpyinfo')
    suite = args[0] if args else DEFAULT_SUITE
    os.makedirs(RUNDIR, exist_ok=True)

    # RIDE rewrites settings.cfg (pane perspective, opened/docked). Keep the user's copy.
    if os.path.exists(SETTINGS) and not os.path.exists(SETTINGS_BAK):
        shutil.copy(SETTINGS, SETTINGS_BAK)
        print(f"backed up settings.cfg -> {SETTINGS_BAK}")

    if not display_up():
        lock = f"/tmp/.X{DISPLAY.lstrip(':')}-lock"
        if os.path.exists(lock):
            os.remove(lock)
        p = subprocess.Popen(['Xvfb', DISPLAY, '-screen', '0', f'{SCREEN_W}x{SCREEN_H}x24'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        write_pid('xvfb', p.pid)
        for _ in range(30):
            time.sleep(0.5)
            if display_up():
                break
        else:
            sys.exit("Xvfb failed to start")
        print(f"Xvfb up on {DISPLAY} ({SCREEN_W}x{SCREEN_H})")

    # A window manager is required: without one, AUI floating mini-frames misbehave.
    if not read_pid('wm'):
        p = subprocess.Popen(['xfwm4'], env=env(),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        write_pid('wm', p.pid)
        time.sleep(2)
        print("xfwm4 up")

    # PYTHONPATH is load-bearing: without it, `import robotide` resolves to the
    # installed package in site-packages and you test released code, not this tree.
    e = env()
    e['PYTHONPATH'] = SRC
    log = open(os.path.join(RUNDIR, 'ride.log'), 'w')
    p = subprocess.Popen(
        [sys.executable, '-c',
         'import robotide, sys; sys.stderr.write("robotide from %s\\n" % robotide.__file__); '
         f'from robotide import main; main({suite!r})'],
        cwd=REPO, env=e, stdout=log, stderr=subprocess.STDOUT)
    write_pid('ride', p.pid)
    print(f"launching RIDE (pid {p.pid}) with suite {suite!r} from {SRC}")

    for _ in range(90):
        time.sleep(1)
        if main_window():
            break
        if p.poll() is not None:
            sys.exit(f"RIDE exited early; see {RUNDIR}/ride.log")
    else:
        sys.exit(f"no RIDE window after 90s; see {RUNDIR}/ride.log")
    time.sleep(4)  # let plugins finish loading and the tree populate
    cmd_normalize([])
    park_floaters()
    print("RIDE ready")


def park_floaters():
    """Move floating panes off the tree region.

    The Files pane floats by default and overlaps TREE_REGION; left where it is,
    its contents leak into check-tree and a blank tree reads as RENDERED.
    """
    for name in ('^Files$',):
        w = find_window(name)
        if w:
            xdo('windowmove', w, str(SCREEN_W - 340), str(SCREEN_H - 300))
    time.sleep(1.5)


def cmd_park(args):
    """Move floating panes (e.g. Files) away from the docked tree region."""
    park_floaters()
    print("floating panes parked")


def cmd_normalize(args):
    """Move/resize the main window to a known rect so gesture coords are reproducible."""
    w = main_window()
    if not w:
        sys.exit("no RIDE main window")
    xdo('windowmove', w, '0', '0')
    xdo('windowsize', w, str(SCREEN_W), str(SCREEN_H))
    time.sleep(1.5)
    xdo('windowactivate', '--sync', w)
    print(f"main window normalised to 0,0 {SCREEN_W}x{SCREEN_H}")


def cmd_down(args):
    """Stop RIDE, the WM and Xvfb, and restore the user's settings.cfg."""
    for name in ('ride', 'wm', 'xvfb'):
        kill(name)
    if os.path.exists(SETTINGS_BAK):
        shutil.copy(SETTINGS_BAK, SETTINGS)
        os.remove(SETTINGS_BAK)
        print("restored settings.cfg")
    print("stopped")


def cmd_shot(args):
    path = args[0] if args else '/tmp/ride-shot.png'
    r = x('import', '-window', 'root', path)
    if r.returncode:
        sys.exit(f"screenshot failed: {r.stderr}")
    print(path)


def cmd_windows(args):
    print(x('wmctrl', '-l').stdout.rstrip() or '(none)')


def cmd_click(args):
    px, py = args[0], args[1]
    xdo('mousemove', px, py, 'sleep', '0.3', 'click', '1')
    time.sleep(1)
    print(f"clicked {px},{py}")


def cmd_key(args):
    """Send a key via XTEST. Never use `xdotool key --window` -- GTK ignores it."""
    w = main_window()
    if w:
        xdo('windowactivate', '--sync', w)
        time.sleep(0.5)
    xdo('key', args[0])
    time.sleep(1.5)
    print(f"key {args[0]}")


def _drag(path, settle=1.0):
    sx, sy = path[0]
    xdo('mousemove', str(sx), str(sy), 'sleep', '0.4', 'mousedown', '1', 'sleep', '0.4')
    for px, py in path[1:]:
        # AUI needs a stream of motion events to raise its docking guides.
        xdo('mousemove', str(px), str(py), 'sleep', '0.15')
    time.sleep(settle)
    xdo('mouseup', '1')
    time.sleep(3)


def win_geometry(wid):
    """Return (x, y, w, h) for a window id."""
    out = xdo('getwindowgeometry', '--shell', wid)
    g = dict(line.split('=', 1) for line in out.splitlines() if '=' in line)
    return int(g['X']), int(g['Y']), int(g['WIDTH']), int(g['HEIGHT'])


def cmd_dock_tree(args):
    """Drag the floating Test Suites pane onto the left docking guide."""
    gx, gy = LEFT_DOCK_GUIDE
    for attempt in (1, 2, 3):
        w = find_window('^Test Suites$')
        if not w:
            print("docked")
            return 0
        # Park it somewhere predictable, then grab its AUI-drawn caption bar.
        # The caption is ~12px tall at the top of the mini-frame; compute it from
        # the real geometry rather than assuming a fixed size.
        xdo('windowmove', w, '300', '430')
        time.sleep(1.5)
        wx_, wy_, ww, wh = win_geometry(w)
        cap = (wx_ + ww // 2, wy_ + 6)
        _drag([cap, (cap[0] - 20, 460), (380, 470), (300, 475),
               (200, gy), (120, gy), (60, gy), (gx, gy)])
        if not find_window('^Test Suites$'):
            print(f"docked (attempt {attempt})")
            return 0
        print(f"attempt {attempt}: still floating, retrying")
    print("WARNING: still floating -- the drop missed the guide")
    return 1


def cmd_float_tree(args):
    """Drag the docked Test Suites pane out into a floating mini-frame."""
    if find_window('^Test Suites$'):
        print("already floating")
        return
    cx, cy = DOCKED_CAPTION
    _drag([(cx, cy), (150, 200), (350, 300), (550, 380), (700, 430)])
    print("floating" if find_window('^Test Suites$') else "WARNING: still docked")


VIEW_MENU = (300, 38)                     # "View" in the menu bar
VIEW_MENU_ITEM_1 = (392, 67)              # "View Test Suites Explorer" (first item)


def cmd_toggle_tree(args):
    """Hide/show the tree via View > View Test Suites Explorer.

    Use this rather than `key F12`: the F12 accelerator does not reliably pick up
    synthetic key events here, while the menu path always works.
    """
    w = main_window()
    if w:
        xdo('windowactivate', '--sync', w)
        time.sleep(0.5)
    xdo('mousemove', str(VIEW_MENU[0]), str(VIEW_MENU[1]), 'sleep', '0.4', 'click', '1')
    time.sleep(1.2)
    xdo('mousemove', str(VIEW_MENU_ITEM_1[0]), str(VIEW_MENU_ITEM_1[1]),
        'sleep', '0.4', 'click', '1')
    time.sleep(3)
    print("toggled tree visibility")


def cmd_check_tree(args):
    """Report whether the docked tree pane has rendered content.

    Counts unique colours in the pane's rectangle. A painted tree has many
    (icons, text, selection); a blank pane has a handful. This is the
    assertion for the 'tree goes blank after docking' class of bug.

    When the pane floats, its own window is measured. When it is docked,
    TREE_REGION is measured.

    PRECONDITION when docked: the pane must be *visible*. Pixels cannot tell a
    blank tree pane from a hidden one -- with the pane hidden, TREE_REGION shows
    the editor underneath and reads as RENDERED. Always `dock-tree` immediately
    before `check-tree`; never trust it straight after `toggle-tree`.
    """
    shot = os.path.join(RUNDIR, 'check.png')
    floating = find_window('^Test Suites$')
    if floating:
        where = 'floating pane window'
        r = x('import', '-window', floating, shot)
        if r.returncode:
            sys.exit(f"screenshot failed: {r.stderr}")
        crop = []
    else:
        where = 'docked TREE_REGION'
        park_floaters()
        x('import', '-window', 'root', shot)
        cx, cy, cw, ch = TREE_REGION
        crop = ['-crop', f'{cw}x{ch}+{cx}+{cy}', '+repage']
    r = x('convert', shot, *crop, '-format', '%k', 'info:')
    if r.returncode:
        sys.exit(f"convert failed: {r.stderr}")
    colours = int(r.stdout.strip())
    verdict = 'RENDERED' if colours >= 10 else 'BLANK'
    print(f"tree ({where}) unique colours: {colours} -> {verdict}")
    return 0 if verdict == 'RENDERED' else 1


def cmd_log(args):
    p = os.path.join(RUNDIR, 'ride.log')
    print(open(p).read() if os.path.exists(p) else '(no log)')


def cmd_help(args):
    print(__doc__)
    print("commands:")
    for name, fn in sorted(COMMANDS.items()):
        print(f"  {name:<12} {(fn.__doc__ or '').strip().splitlines()[0] if fn.__doc__ else ''}")


COMMANDS = {
    'up': cmd_up, 'down': cmd_down, 'shot': cmd_shot, 'windows': cmd_windows,
    'click': cmd_click, 'key': cmd_key, 'dock-tree': cmd_dock_tree,
    'float-tree': cmd_float_tree, 'check-tree': cmd_check_tree,
    'normalize': cmd_normalize, 'park': cmd_park, 'toggle-tree': cmd_toggle_tree, 'log': cmd_log, 'help': cmd_help,
}

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        cmd_help([])
        sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] == 'help' else 2)
    sys.exit(COMMANDS[sys.argv[1]](sys.argv[2:]) or 0)
