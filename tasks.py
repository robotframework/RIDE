#!/usr/bin/env python

#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

import sys
import os
from os.path import join, exists
import re
import shutil
import tempfile

try:
    from pathlib import Path
    from rellu import ReleaseNotesGenerator, Version
    assert Path.cwd().resolve() == Path(__file__).resolve().parent
except ImportError:  # We are at Python 2.7
    Path = os.path.normpath
    pass

sys.path.insert(0, 'src')


REPOSITORY = 'robotframework/RIDE'
VERSION_PATH = Path('src/robotide/version.py')
VERSION_PATTERN = "VERSION = '(.*)'"
RELEASE_NOTES_PATH = Path('doc/releasenotes/ride-{version}.rst')
RELEASE_NOTES_TITLE = 'Robot Framework IDE {version}'
RELEASE_NOTES_INTRO = '''
`RIDE (Robot Framework IDE)`_ {version} is a new release with major enhancements
and bug fixes. This version {version} includes fixes for installer, Font Type selection, Text Editor improvements and new File explorer.
The reference for valid arguments is `Robot Framework`_ version 3.1.2.
**MORE intro stuff...**

* This is the **last version supporting Python 2.7**.
* A new File Explorer allows to open supported file types in RIDE, or other types in a basic code editor. To open a file you must double-click on it (project folders open with right-click after being highlighted with left-click). If it is a supported file format but not with the correct structure (for example a resource file), an error message is shown, and then opens in code editor.
* On Grid Editor, the cells can be autoajusting with wordwrap. There is a new checkbox in `Tools>Preferences>Grid Editor`.
* Font Type selection is available for all Editors and Run panels.
* Zoom in and zoom out is possible on Text Editor and Run panels.
* Pressing the Ctrl on the Grid Editor, when over a keyword it will show its documentation (that can be detached with mouse click).
* There are some important changes, or known issues:

  - On MacOS to call autocomplete in Grid and Text Editors, you have to use Alt-Space (not Command-Space)

  - On Linux and Windows to call autocomplete in Grid and Text Editors, you have to use Ctrl-Space

  - On Text Editor the TAB key adds the defined number of spaces. With Shift moves to the left, and together with Control selects text.

  - On Text Editor the **: FOR** loop structure must use Robot Framework 3.1.2 syntax, i.e. **FOR** and **END**. The only solution to disable this, is to disable Text Editor Plugin.

**THIS IS THE LAST RELEASE SUPPORTING PYTHON 2.7**

**wxPython will be updated to current version 4.0.7post2**

*Linux users are advised to install first wxPython from .whl package at* `wxPython.org`_.


**REMOVE reference to tracker if release notes contain all issues.**
All issues targeted for RIDE {version.milestone} can be found
from the `issue tracker milestone`_.

Questions and comments related to the release can be sent to the
`robotframework-users`_ mailing list or to the channel #ride on 
`Robot Framework Slack`_, and possible bugs submitted to the `issue tracker`_.

**REMOVE ``--pre`` from the next command with final releases.**
If you have pip_ installed, just run

::

   pip install --upgrade robotframework-ride==1.7.4rc1

to install this **RELEASE CANDIDATE** release, and for the **final** release use

::

   pip install --upgrade robotframework-ride

::

   pip install robotframework-ride=={version}

to install exactly the **final** version. Alternatively you can download the source
distribution from PyPI_ and install it manually. For more details and other
installation approaches, see the `installation instructions`_.
See the `FAQ`_ for important info about `: FOR` changes.

A possible way to start RIDE is:

::

    python -m robotide.__init__

You can then go to `Tools>Create RIDE Desktop Shortcut`, or run the shortcut creation script with:

::

    python -m robotide.postinstall -install

RIDE {version} was released on {date}.

.. _RIDE (Robot Framework IDE): https://github.com/robotframework/RIDE/
.. _Robot Framework: http://robotframework.org
.. _pip: http://pip-installer.org
.. _PyPI: https://pypi.python.org/pypi/robotframework-ride
.. _issue tracker milestone: https://github.com/robotframework/RIDE/issues?q=milestone%3A{version.milestone}
.. _issue tracker: https://github.com/robotframework/RIDE/issues
.. _robotframework-users: http://groups.google.com/group/robotframework-users
.. _Robot Framework Slack: https://robotframework-slack-invite.herokuapp.com
.. _installation instructions: ../../INSTALL.rst
.. _wxPython.org: https://extras.wxpython.org/wxPython4/extras/linux/gtk3/
.. _FAQ: https://github.com/robotframework/RIDE/wiki/F.A.Q.
'''


try:
    from StringIO import StringIO
    PY3 = False
except ImportError:  # py3
    from io import StringIO
    PY3 = True
try:
    import urllib2
except ImportError:  # py3
    import urllib as urllib2

try:
    from invoke import task, run, __version_info__ as invoke_version
    if invoke_version < (0, 13):
        raise ImportError
except ImportError:
    sys.exit('invoke 0.13 or newer required. See BUILD.rest for details.')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = join(ROOT_DIR, 'src')
TEST_DIR = join(ROOT_DIR, 'utest')
DIST_DIR = join(ROOT_DIR, 'dist')
BUILD_DIR = join(ROOT_DIR, 'build')
ROBOTIDE_PACKAGE = join(ROOT_DIR, 'src', 'robotide')
BUNDLED_ROBOT_DIR = join(ROBOTIDE_PACKAGE, 'lib', 'robot')
# MANIFEST = ROOT_DIR/'MANIFEST.in'

TEST_PROJECT_DIR = 'theproject'
TEST_LIBS_GENERATED = 10
# Set VERSION global variable
# execfile('src/robotide/version.py')
with open("src/robotide/version.py") as f:
    code = compile(f.read(), "version.py", 'exec')
    exec(code)

FINAL_RELEASE = bool(re.match('^(\d*\.){1,2}\d*$', VERSION))
wxPythonDownloadUrl = \
    "https://wxpython.org/"


# Developemnt tasks
@task
def devel(ctx, args=''):
    """Start development version of RIDE."""
    _set_development_path()
    from robotide import main
    main(*args.split(','))


@task
def test(ctx, test_filter=''):
    """Run unit tests."""
    _remove_bytecode_files()
    from nose import run as noserun
    _set_development_path()
    additional_args = []
    if test_filter:
        additional_args.append(test_filter)
    result = noserun(defaultTest=TEST_DIR,
                     argv=['', '--m=^test_'] + additional_args)
    assert result is True


@task
def deps(ctx, upgrade=False):
    """Fetch and install development dependencies."""
    cmd = 'pip install -r requirements-dev.txt'
    if upgrade:
        ctx.run('{} --upgrade'.format(cmd))
    else:
        ctx.run(cmd)


@task
def clean(ctx):
    """Clean bytecode files and remove `dist` and `build` directories."""
    _clean()


@task
def update_robot(ctx, version=''):
    """Update robot framework to specified commit or tag.

    By default, update to current master.
    This task also repackages RF under `robotide.robot` to avoid
    accidentally importing system installation.

    `git`, `grep` and `sed` must be installed
    """
    target = version if version else 'master'
    ctx.run('(cd ../robotframework && git fetch && git checkout {})'.format(target))
    rf_commit_hash = ctx.run('(cd ../robotframework && git rev-parse HEAD)').stdout
    ctx.run('rm -rf {}'.format(BUNDLED_ROBOT_DIR))
    ctx.run('cp -r ../robotframework/src/robot src/robotide/lib/')
    # Prevent .pyc matching grep expressions
    _clean()
    # `import robot` -> `from robotide.lib import robot`
    # Removed in v3.0.3 
    #_run_sed_on_matching_files(ctx, 
    #    'import robot',
    #    's/import robot/from robotide.lib import robot/')

    # `from robot.pkg import stuff` -> `from robotide.lib.robot.pkg import stuff`
    _run_sed_on_matching_files(ctx, 
        'from robot\..* import',
        's/from robot\./from robotide.lib.robot./')
    # `from robot import stuff` -> `from robotide.lib.robot import stuff`
    # Reintroduced in v3.1a1
    _run_sed_on_matching_files(ctx, 
        'from robot import',
        's/from robot import/from robotide.lib.robot import/')
    with open(join(ROBOTIDE_PACKAGE, 'lib', 'robot-commit'), 'w') as rf_version_file:
        rf_version_file.write('{}\n'.format(rf_commit_hash))
    _log('Updated bundled Robot Framework to version {}/{}'.format(
        target, rf_commit_hash))


@task
def generate_big_project(ctx, install=False, upgrade=False, args=''):
    """Generate big test data project to help perf testing."""
    _remove_bytecode_files()
    if install or upgrade:
        rfgen_url = \
            "https://raw.github.com/robotframework/Generator/master/rfgen.py"
        _log("Installing/upgrading rfgen.py from github.")
        f = open('rfgen.py', 'wb')
        f.write(urllib2.urlopen(rfgen_url).read())
        f.close()
        _log("Done.")

    _set_development_path()
    sys.path.insert(0, '.')

    try:
        import rfgen
        assert rfgen.main(args.split(','))
    except ImportError:
        _log("Error: Did not find 'rfgen' script or installation")
        _log("Use 'invoke generate_big_project --install'")


@task
def random_test(ctx):
    """Use rtest go_find_bugs.py to randomly test RIDE API."""
    _remove_bytecode_files()
    _set_development_path()
    sys.path.insert(0, '.')
    from rtest.go_find_some_bugs import main
    dir = tempfile.mkdtemp()
    try:
        assert main(dir)
    finally:
        shutil.rmtree(dir, ignore_errors=True)


# Installation and distribution tasks
@task
def version(ctx, version):
    """Set `version.py` to given version."""
    with open(join(ROBOTIDE_PACKAGE, 'version.py'), 'w') as version_file:
        version_file.write("""#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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
#
# Automatically generated by `tasks.py`.
VERSION = '%s'
""" % version)
    _log('Set version to %s' % version)


@task
def register(ctx):
    """Register current version to Python package index."""
    _run_setup(ctx, 'register')


@task
def install(ctx):
    """Install development version and dependencies."""
    try:
        from wx import VERSION
    except ImportError:
        _log("""No wxPython installation detected!

Please install wxPython before running RIDE.
You can download wxPython from {}
or
You can install with 'pip install wxPython'.
""".format(wxPythonDownloadUrl))
    _run_setup(ctx, 'install')


def _run_setup(ctx, cmd):
    ctx.run('python setup.py {}'.format(cmd))


def release_notes_plugin(ctx):
    changes = _download_and_format_issues()
    plugin_path = os.path.join(
        ROBOTIDE_PACKAGE, 'application', 'releasenotes.py')
    content = ctx.open(plugin_path).read().rsplit('RELEASE_NOTES =', 1)[0]
    content += 'RELEASE_NOTES = """\n%s"""\n' % changes
    ctx.open(plugin_path, 'w').write(content)


@task(pre=[clean],
      help={
          'release-notes': 'If enabled, release notes plugin will be updated'})
def sdist(ctx, release_notes=True, upload=False):
    """Creates source distribution with bundled dependencies."""
    if release_notes:
        release_notes_plugin(ctx)
    _run_setup(ctx, 'sdist{}'.format('' if not upload else ' upload'))
    _after_distribution()


@task(pre=[clean])
def wininst(ctx):
    """Creates Windows installer with bundled dependencies."""
    if os.sep != '\\':
        sys.exit('Windows installers may only be created in Windows')

    _run_setup(ctx, 'bdist_wininst')
    _after_distribution()

'''
@task
def release_notes(ctx):
    """Download and format issues in markdown format."""
    issues = _get_issues()
    _log("""ID  | Type | Priority | Summary
--- | ---- | -------- | ------- """)
    for i in issues:
        parts = ('#{}'.format(i.number), _find_type(i), _find_priority(i),
                 i.title)
        _log(' | '.join(parts))
'''

@task
def release_notes(ctx, version=None, username=None, password=None, write=False):
    """Generate release notes based on issues in the issue tracker.

    Args:
        version:  Generate release notes for this version. If not given,
                  generated them for the current version.
        username: GitHub username.
        password: GitHub password.
        write:    When set to True, write release notes to a file overwriting
                  possible existing file. Otherwise just print them to the
                  terminal.

    Username and password can also be specified using ``GITHUB_USERNAME`` and
    ``GITHUB_PASSWORD`` environment variable, respectively. If they aren't
    specified at all, communication with GitHub is anonymous and typically
    pretty slow.
    """
    if not PY3:
        raise NotImplementedError('This task depends on "rellu" with Python 3')
    version = Version(version, VERSION_PATH, VERSION_PATTERN)
    file = RELEASE_NOTES_PATH if write else sys.stdout
    generator = ReleaseNotesGenerator(REPOSITORY, RELEASE_NOTES_TITLE,
                                      RELEASE_NOTES_INTRO)
    generator.generate(version, username, password, file)


@task
def tags_test(ctx):
    """Runs the main section of src/robotide/editor/tags.py."""
    _set_development_path()
    try:
        import subprocess
        p = subprocess.Popen(["/usr/bin/python", "/home/helio/github/RIDE/src/robotide/editor/tags.py"])
        p.communicate('')
    finally:
        pass


# Helper functions

def _clean(keep_dist=False):
    _remove_bytecode_files()
    if not keep_dist and exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    if exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)


def _remove_bytecode_files():
    for d in SOURCE_DIR, TEST_DIR:
        _remove_files_matching(d, '.*\.pyc')


def _remove_files_matching(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for file in filter(lambda x: re.match(pattern, x), files):
            os.remove(join(root, file))


def _set_development_path():
    sys.path.insert(0, TEST_DIR)
    sys.path.insert(0, SOURCE_DIR)


def _run_sed_on_matching_files(ctx, pattern, sed_expression):
    try:
        ctx.run("grep -lr '{}' {} | xargs sed -i '' -e '{}'".format(
            pattern, BUNDLED_ROBOT_DIR, sed_expression))
    except Exception:
        pass


def _after_distribution():
    _log('Created:')
    for path in os.listdir(DIST_DIR):
        _log(os.path.abspath(os.path.join(DIST_DIR, path)))
    _clean(keep_dist=True)


def _download_and_format_issues():
    try:
        from robot.utils import HtmlWriter, html_format
    except ImportError:
        sys.exit('creating release requires Robot Framework to be installed.')
    writer = HtmlWriter(StringIO())
    writer.element('h2', 'Release notes for %s' % VERSION)
    writer.start('table', attrs={'border': '1'})
    writer.start('tr')
    for header in ['ID', 'Type', 'Priority', 'Summary']:
        writer.element(
            'td', html_format('*{}*'.format(header)), escape=False)
    writer.end('tr')
    issues = _get_issues()
    base_url = 'http://github.com/robotframework/RIDE/issues/'
    for issue in issues:
        writer.start('tr')
        link_tmpl = '<a href="{}{}">Issue {}</a>'
        row = [link_tmpl.format(base_url, issue.number, issue.number),
               _find_type(issue),
               _find_priority(issue),
               issue.title]
        for cell in row:
            writer.element('td', cell, escape=False)
        writer.end('tr')
    writer.end('table')
    writer.element('p', 'Altogether %d issues.' % len(issues))
    return writer.output.getvalue()


def _get_issues():
    import getpass
    from github3 import login
    milestone = re.split('[ab-]', VERSION)[0]
    if not PY3:
        username = raw_input('Enter GitHub username for downloading issues: ')
    else:
        username = input('Enter GitHub username for downloading issues: ')
    password = getpass.getpass(
        'Github password for {user}: '.format(user=username))
    gh = login(username, password=password)
    repo = gh.repository('robotframework', 'RIDE')
    milestone_number = _get_milestone(repo, milestone)
    if milestone_number is None:
        _log('milestone not found')
        sys.exit(1)
    issues = list(repo.issues(milestone=milestone_number, state='closed'))
    # issues.sort(cmp=_issue_sorter)
    return issues

def _issue_sorter(i1, i2):
    prio_mapping = {
        'critical': 0,
        'high': 1,
        'medium': 2,
        'low': 3,
        'none':50
    }
    prio1, prio2 = _find_priority(i1), _find_priority(i2)
    return cmp(prio_mapping[prio1], prio_mapping[prio2])


def _find_type(issue):
    type_labels = [l.name for l in issue.labels()
                   if l.name in ['enhancement', 'bug', 'task', 'none']]
    return type_labels[0] if type_labels else 'none'  # 'Unknown type'


def _find_priority(issue):
    prio_labels = [l.name for l in issue.labels()
                   if l.name.startswith('prio')]
    return prio_labels[0][5:] if prio_labels else 'Unknown priority'


def _get_milestone(repo, milestone_title):
    existing_milestones = list(repo.milestones())
    milestone = [m for m in existing_milestones if m.title == milestone_title]
    if milestone:
        return milestone[0].number
    return None


def _log(msg):
    print(msg)
