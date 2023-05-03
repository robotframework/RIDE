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
import github3

from pathlib import Path
assert Path.cwd().resolve() == Path(__file__).resolve().parent

sys.path.insert(0, 'src')


REPOSITORY = 'robotframework/RIDE'
VERSION_PATH = Path('src/robotide/version.py')
VERSION_PATTERN = "VERSION = '(.*)'"
RELEASE_NOTES_PATH = Path('doc/releasenotes/ride-{version}.rst')
RELEASE_NOTES_TITLE = 'Robot Framework IDE {version}'
RELEASE_NOTES_INTRO = """
<div class="document">


<p><a class="reference external" href="https://github.com/robotframework/RIDE/">RIDE (Robot Framework IDE)</a> {version} is a new release with major enhancements
and bug fixes. This version {version} includes removal of Python 2.7 support.
The reference for valid arguments is <a class="reference external" href="http://robotframework.org">Robot Framework</a> installed version, which is at this moment 6.0.2. However, internal library is based on version 3.1.2, to keep compatibility with old formats.</p>
<!-- <strong>MORE intro stuff...</strong>-->
</p>
<ul class="simple">
<li>This is the <strong>first version without support for Python 2.7</strong>.</li>
<li>The last version with support for Python 2.7 was <strong>1.7.4.2</strong>.</li>
<li>Support for Python 3.6 up to 3.10 (current version on this date).</li>
<li>There are some important changes, or known issues:
<ul>
<li>On MacOS to call autocomplete in Grid and Text Editors, you have to use Alt-Space (not Command-Space).</li>
<li>On Linux and Windows to call autocomplete in Grid and Text Editors, you have to use Ctrl-Space.</li>
<li>On Text Editor the TAB key adds the defined number of spaces. With Shift moves to the left, and together with Control selects text.</li>
<li>On Text Editor the <strong>: FOR</strong> loop structure must use Robot Framework 3.1.2 syntax, i.e. <strong>FOR</strong> and <strong>END</strong>.</li>
<li>On Grid Editor and Linux the auto enclose is only working on cell selection, but not on cell content edit.</li>
</ul>
</li>
</ul>
<p><strong>New Features and Fixes Highlights</strong></p>
<ul class="simple">
<li>Auto enclose text in &#123;&#125;, [], &quot;&quot;, ''</li>
<li>Auto indent in Text Editor on new lines</li>
<li>Block indent in Text Editor (TAB on block of selected text)</li>
<li>Ctrl-number with number, 1-5 also working on Text Editor:<ol class="arabic">
<li>create scalar variable</li>
<li>create list variable</li>
<li>Comment line (with Shift comment content with #)</li>
<li>Uncomment line (with Shift uncomment content with #)</li>
<li>create dictionary variable</li>
</ol>
</li>
<li>Persistence of the position and state of detached panels, File Explorer and Test Suites</li>
<li>File Explorer and Test Suites panels are now Plugins and can be disabled or enabled and made Visible with F11 ( Test Suites with F12, but disabled for now)</li>
<li>File Explorer now shows selected file when RIDE starts</li>
<li>Block comment and uncomment on both Grid and Text editors</li>
<li>Extensive color customization of panel elements via <cite>Tools&gt;Preferences</cite></li>
<li>Color use on Console and Messages Log panels on Test Run tab</li>
</ul>
<p>Please note, that the features and fixes are not yet closed. This pre-release is being done because it has important fixes.
</p>
<p><strong>wxPython will be updated to version 4.2.0</strong></p>
<p><em>Linux users are advised to install first wxPython from .whl package at</em> <a class="reference external" href="https://extras.wxpython.org/wxPython4/extras/linux/gtk3/">wxPython.org</a>.</p>
<!-- <p><strong>REMOVE reference to tracker if release notes contain all issues.</strong></p>-->

<p>All issues targeted for RIDE {milestone} can be found
from the <a class="reference external" href="https://github.com/robotframework/RIDE/issues?q=milestone%3A{milestone}">issue tracker milestone</a>.</p>
<p>Questions and comments related to the release can be sent to the
<a class="reference external" href="http://groups.google.com/group/robotframework-users">robotframework-users</a> mailing list or to the channel #ride on
<a class="reference external" href="https://robotframework-slack-invite.herokuapp.com">Robot Framework Slack</a>, and possible bugs submitted to the <a class="reference external" href="https://github.com/robotframework/RIDE/issues">issue tracker</a>.
<!-- <p><strong>REMOVE ``--pre`` from the next command with final releases.</strong> -->
You should see <a class="reference external" href="https://forum.robotframework.org/c/tools/ride/">Robot Framework Forum</a> if your problem is already known.</p>
<p>If you have <a class="reference external" href="http://pip-installer.org">pip</a> installed, just run</p>
<pre class="literal-block">
pip install --pre --upgrade robotframework-ride==2.0b3
</pre>
<p>to install this <strong>BETA</strong> release, and for the <strong>final</strong> release use</p>
<pre class="literal-block">
pip install --upgrade robotframework-ride
</pre>
<pre class="literal-block">
pip install robotframework-ride=={version}
</pre>
<p>to install exactly the <strong>final</strong> version. Alternatively you can download the source
distribution from <a class="reference external" href="https://pypi.python.org/pypi/robotframework-ride">PyPI</a> and install it manually. For more details and other
installation approaches, see the <a class="reference external" href="https://github.com/robotframework/RIDE/wiki/Installation-Instructions">installation instructions</a>.
If you want to help in the development of RIDE, by reporting issues in current development version, you can install with:</p>
<pre class="literal-block">
pip install -U https://github.com/robotframework/RIDE/archive/master.zip
</pre>
<p>Important document for helping with development is the <a class="reference external" href="https://github.com/robotframework/RIDE/blob/master/CONTRIBUTING.adoc">CONTRIBUTING</a>.</p>
<p>See the <a class="reference external" href="https://github.com/robotframework/RIDE/wiki/F.A.Q.">FAQ</a> for important info about <cite>: FOR</cite> changes and other known issues and workarounds.</p>
<p>A possible way to start RIDE is:</p>
<pre class="literal-block">
python -m robotide.__init__
</pre>
<p>You can then go to <cite>Tools&gt;Create RIDE Desktop Shortcut</cite>, or run the shortcut creation script with:</p>
<pre class="literal-block">
python -m robotide.postinstall -install
</pre>
<p>RIDE {version} was released on {date}.</p>
</div>
"""

from io import StringIO
import urllib

from invoke import task, run

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
    # from nose import run as noserun
    from pytest import main as pytestrun
    _set_development_path()
    additional_args = []
    if test_filter:
        additional_args.append(test_filter)
    result = pytestrun(args=[TEST_DIR] + additional_args)
    assert result == 0 


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
    _run_sed_on_matching_files(ctx, 
        'from robot\..* import',
        's/from robot\./from robotide.lib.robot./')
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
        f.write(urllib.urlopen(rfgen_url).read())
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
    with open(plugin_path, 'r') as ctx.f:
        content = ctx.f.read().rsplit('RELEASE_NOTES =', 1)[0]
    content += 'RELEASE_NOTES = f"""\n%s\n%s"""\n' % (RELEASE_NOTES_INTRO, changes)
    with open(plugin_path, 'w') as ctx.f:
        ctx.f.write(content)
    _log(f"Created {plugin_path}")


@task(pre=[clean],
      help={
          'release-notes': 'If enabled, release notes plugin will be updated'})
def sdist(ctx, release_notes=False, upload=False):
    """Creates source distribution with bundled dependencies."""
    if release_notes:
        release_notes_plugin(ctx)
    _run_setup(ctx, 'sdist{}'.format('' if not upload else ' upload'))
    _after_distribution()


@task
def release_notes(ctx):
    """Generate release notes based on issues in the issue tracker.

    You must have defined a ``GITHUB_TOKEN`` environment variable, created on GitHub
    repository with the proper permissions (read mode).
    """
    token = os.getenv('GITHUB_TOKEN')
    if token:
        release_notes_plugin(ctx)
    else:
        _log(release_notes.__doc__)
        sys.exit(1)


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

@task
def sonar(ctx, test_filter=''):
    """Run unit tests and coverage and send to SonarCloud"""
    
    _set_development_path()

    try:
        import subprocess
        c = subprocess.Popen(["coverage", "run" , "-m", "pytest", "--cov-config=.coveragerc", "-k test_", "-v", TEST_DIR])
        c.communicate('')
        r = subprocess.Popen(["coverage", "report"])
        r.communicate('')
        x = subprocess.Popen(["coverage", "xml"])
        x.communicate('')
        h = subprocess.Popen(["coverage", "html"])
        h.communicate('')
        s = subprocess.Popen(["sonar-scanner", "-D", "sonar.projectVersion='v"+VERSION+"'"])
        s.communicate('')
    finally:
        pass

@task
def test_ci(ctx, test_filter=''):
    """Run unit tests and coverage"""
    
    _set_development_path()

    try:
        import subprocess
        c = subprocess.Popen(["coverage", "run" , "-m", "pytest", "--cov-config=.coveragerc", "-k test_", "-v", TEST_DIR])
        c.communicate('')
        r = subprocess.Popen(["coverage", "report"])
        r.communicate('')
        x = subprocess.Popen(["coverage", "xml"])
        x.communicate('')
        h = subprocess.Popen(["coverage", "html"])
        h.communicate('')
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
        _remove_files_matching(d, r'.*\.pyc')


def _remove_files_matching(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for file in filter(lambda x: re.match(pattern, x), files):
            os.remove(join(root, file))


def _set_development_path():
    sys.path.insert(0, TEST_DIR+"/controller")
    sys.path.insert(0, TEST_DIR)
    sys.path.insert(0, SOURCE_DIR)
    pythonpath = os.getenv('PYTHONPATH')
    if not pythonpath:
           pythonpath = ""
    pythonpath = ':' + pythonpath
    os.environ['PYTHONPATH'] = SOURCE_DIR + ':' + TEST_DIR + pythonpath


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
    print(f"{str(issues)}")
    base_url = 'http://github.com/robotframework/RIDE/issues/'
    for issue in issues:
        writer.start('tr')
        link_tmpl = '<a href="{}{}">Issue {}</a>'
        row = [link_tmpl.format(base_url, issue.number, issue.number),
               _find_type(issue),
               _find_priority(issue),
               issue.title.replace('{','{{').replace('}', '}}')]
        for cell in row:
            writer.element('td', cell, escape=False)
        writer.end('tr')
    writer.end('table')
    writer.element('p', 'Altogether %d issues.' % len(issues))
    return writer.output.getvalue()


def _my_two_factor_function():
    code = ''
    while not code:
        # The user could accidentally press Enter before being ready,
        # let's protect them from doing that.
        code = input('Enter 2FA code: ')
    return code
       

def _get_issues():
    
    milestone = re.split('[ab-]', VERSION)[0]
    # gh = github3.login(os.getenv('GITHUB_USERNAME'), os.getenv('GITHUB_PASSWORD'),
    #              two_factor_callback=_my_two_factor_function)
    gh = github3.login(token=os.getenv('GITHUB_TOKEN'))
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
    print(f"{str(existing_milestones)}")
    milestone = [m for m in existing_milestones if m.title == milestone_title]
    if milestone:
        return milestone[0].number
    return None


def _log(msg):
    print(msg)
