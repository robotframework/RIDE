import os
from os.path import join, isdir, isfile
import csv
import re
import shutil
import tempfile
from urllib2 import urlopen
from string import Template
from StringIO import StringIO
import urllib2
from paver.easy import *
from paver.setuputils import setup, find_package_data


ROOT_DIR = path(__file__).dirname()
SOURCE_DIR = ROOT_DIR/'src'
TEST_DIR = ROOT_DIR/'utest'
DIST_DIR = ROOT_DIR/'dist'
BUILD_DIR = ROOT_DIR/'build'
ROBOTIDE_PACKAGE = ROOT_DIR/'src'/'robotide'
LIB_TARGET = ROBOTIDE_PACKAGE/'lib'
LIB_SOURCE = ROOT_DIR/'lib'
MANIFEST = ROOT_DIR/'MANIFEST.in'

VERSION = open(ROOT_DIR/'VERSION.txt').read().strip()
FINAL_RELEASE = bool(re.match('^(\d*\.){1,2}\d*$', VERSION))

TEST_PROJECT_DIR = 'theproject'
TEST_LIBS_GENERATED = 10

def find_packages(where):
    def is_package(path):
        return isdir(path) and isfile(join(path ,'__init__.py'))
    pkgs = []
    for dirpath, dirs, _ in os.walk(where):
        for dirname in dirs:
            pkg_path = join(dirpath, dirname)
            if is_package(pkg_path):
                pkgs.append('.'.join((pkg_path.split(os.sep)[1:])))
    return pkgs


setup(name         = 'robotframework-ride',
      version      = VERSION,
      description  = 'RIDE :: Robot Framework Test Data Editor',
      long_description ="""
Robot Framework is a generic test automation framework for acceptance
level testing. RIDE is a lightweight and intuitive editor for Robot
Framework test data.
          """.strip(),
      license      = 'Apache License 2.0',
      keywords     = 'robotframework testing testautomation',
      platforms    = 'any',
      classifiers  = """
Development Status :: 5 - Production/Stable
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Testing
          """.strip().splitlines(),
      author       = 'Robot Framework Developers',
      author_email = 'robotframework-devel@googlegroups,com',
      url          = 'https://github.com/robotframework/RIDE/',
      download_url = 'https://github.com/robotframework/RIDE/downloads/',
      package_dir  = {'' : str(SOURCE_DIR)},
      packages     = find_packages(str(SOURCE_DIR)) + \
                        ['robotide.lib.%s' % str(name) for name
                         in find_packages(str(LIB_SOURCE))],
      package_data = find_package_data(str(SOURCE_DIR)),
      # Robot Framework package data is not included, but RIDE does not need it.
      # # Always install everything, since we may be switching between versions
      options      = { 'install': { 'force' : True } },
      scripts      = ['src/bin/ride.py', 'ride_postinstall.py'],
      install_requires = ['Pygments']
      )

@task
@consume_args
def run(args):
    """Start development version of RIDE"""
    _set_development_path()
    from robotide import main
    main(*args)

@task
@consume_args
def test(args):
    """Run unit tests (requires nose and mock)"""
    _remove_bytecode_files()
    assert _run_nose(args) is True

options(
    generate_big_project = Bunch(
        dir = "theproject",
        libs = 5,
        keywords=10,
        suites = 1,
        tests=10,
        resourcefiles=1,
        resources=30,
        testdepth=3,
        validity=1,
        upgrade=False
    )
)
@task
@consume_args
@no_help
def generate_big_project(args):
    _remove_bytecode_files()
    if "--upgrade" in args or '--install' in args:
        rfgen_url = "https://raw.github.com/robotframework/Generator/master/rfgen.py"
        print "Installing/upgrading rfgen.py from github."
        f = open('rfgen.py','wb')
        f.write(urllib2.urlopen(rfgen_url).read())
        f.close()
        print "Done."
        sys.exit(0)

    _set_development_path()
    sys.path.insert(0, '.')

    try:
        from rfgen import main
        assert main(args)
    except ImportError:
        print "Error: Did not find 'rfgen' script or installation"
        print "Use 'paver generate_big_project --install'"
        sys.exit(0)


@task
def random_test():
    """Use rtest go_find_bugs.py to randomly test RIDE api"""
    _remove_bytecode_files()
    _set_development_path()
    sys.path.insert(0, '.')
    from rtest.go_find_some_bugs import main
    dir = tempfile.mkdtemp()
    try:
        assert main(dir)
    finally:
        shutil.rmtree(dir, ignore_errors=True)

@task
def test_parallel():
    """Run tests with --processes 4"""
    _remove_bytecode_files()
    excluded_packages = ['^ui', '^settings', '^editor']
    excluded_files = [os.path.join('utest', 'controller', 'test_resource_import'),
                      os.path.join('utest', 'controller', 'test_filecontrollers'),
                      os.path.join('utest', 'plugin', 'test_plugin_settings')]
    args = ['--processes', '4']
    for name in excluded_packages + excluded_files:
        args.extend(['--exclude', os.path.basename(name)])
    success = _run_nose(args)
    args = ['--tests']
    for pkg in excluded_packages:
        args.append(os.path.join('utest', pkg[1:]))
    args.extend(['%s.py' % name for name in excluded_files])
    assert _run_nose(args) and success is True

@task
@needs('_prepare_build', 'setuptools.command.install')
def install():
    """Installs development version and dependencies"""
    try:
        import wxversion
    except ImportError:
        print "No wxPython installation detected!"
        print ""
        print "Please ensure that you have wxPython installed before running RIDE."
        print "You can obtain wxPython 2.8.12.1 from http://sourceforge.net/projects/wxpython/files/wxPython/2.8.12.1/"

@task
@needs('_prepare_build', 'setuptools.command.register')
def register():
    """Register current version to Python package index"""
    pass

@task
@consume_args
def set_version(args):
    with open('VERSION.txt', 'w') as version_file:
        version_file.write(args[0])

@task
@needs('clean', '_prepare_build', '_release_notes', 'generate_setup', 'minilib',
       'setuptools.command.sdist')
def sdist():
    """Creates source distribution with bundled dependencies"""
    _after_distribution()

@task
@needs('_windows', 'clean', '_prepare_build',
       'setuptools.command.bdist_wininst')
def wininst():
    """Creates Windows installer with bundled dependencies"""
    _after_distribution()

@task
def _windows():
    if os.sep != '\\':
        sys.exit('Windows installers may only be created in Windows')

@task
def _prepare_build():
    _update_version()
    if not LIB_TARGET.exists():
        LIB_SOURCE.copytree(LIB_TARGET)

@task
def _release_notes():
    if FINAL_RELEASE:
        changes = _download_and_format_issues()
        _update_release_notes_plugin(changes)

@task
def clean():
    _clean()

def _clean(keep_dist=False):
    if not keep_dist and DIST_DIR.exists():
        DIST_DIR.rmtree()
    if BUILD_DIR.exists():
        BUILD_DIR.rmtree()
    if LIB_TARGET.exists():
        LIB_TARGET.rmtree()
    for name in 'paver-minilib.zip', 'setup.py':
        p = path(name)
        if p.exists():
            p.remove()

def _remove_bytecode_files():
    for d in LIB_SOURCE, SOURCE_DIR, TEST_DIR:
        for pyc in d.walkfiles(pattern='*.pyc'):
            os.remove(pyc)
        for clazz in d.walkfiles(pattern='*$py.class'):
            os.remove(clazz)

def _run_nose(args):
    from nose import run as noserun
    _set_development_path()
    return noserun(defaultTest=TEST_DIR,
                   argv=['', '--m=^test_'] + args)

def _update_version():
    _log('Using version %s from VERSION.txt' % VERSION)
    with (path(ROBOTIDE_PACKAGE)/'version.py').open('w') as version_file:
        version_file.write("""# Automatically generated by `pavement.py`.
VERSION = '%s'
""" % VERSION)

def _set_development_path():
    sys.path.insert(0, LIB_SOURCE)
    sys.path.insert(0, SOURCE_DIR)

def _after_distribution():
    _announce()
    _clean(keep_dist=True)

def _download_and_format_issues():
    try:
        from robot.utils import HtmlWriter, html_format
    except ImportError:
        sys.exit('creating release requires Robot Framework to be installed.')
    URL = Template('http://code.google.com/p/robotframework-ride/issues/csv?'
                   'sort=priority+type&colspec=ID%20Type%20Priority%20Summary'
                   '&q=target%3A${version}&can=1')
    reader = csv.reader(urlopen(URL.substitute({'version': VERSION})))
    total_issues = 0
    writer = HtmlWriter(StringIO())
    writer.element('h2', 'Release notes for %s' % VERSION)
    writer.start('table', attrs={'border': '1'})
    for row in reader:
        if not row or row[1] == 'Task':
            continue
        row = row[:4]
        writer.start('tr')
        if reader.line_num == 1:
            row = [ '*%s*' % cell for cell in row ]
        else:
            row[0] = '<a href="http://code.google.com/p/robotframework-ride/'\
                     'issues/detail?id=%s">Issue %s</a>' % (row[0], row[0])
            total_issues += 1
        for cell in row:
            if reader.line_num == 1:
                cell = html_format(cell)
            writer.element('td', cell, escape=False)
        writer.end('tr')
    writer.end('table')
    writer.element('p', 'Altogether %d issues.' % total_issues)
    return writer.output.getvalue()

def _update_release_notes_plugin(changes):
    plugin_path = os.path.join(ROBOTIDE_PACKAGE, 'application', 'releasenotes.py')
    content = open(plugin_path).read().rsplit('RELEASE_NOTES =', 1)[0]
    content += 'RELEASE_NOTES = """\n%s"""\n' % changes
    open(plugin_path, 'w').write(content)

def _announce():
    _log('Created:')
    for path in os.listdir(DIST_DIR):
        _log(os.path.abspath(os.path.join(DIST_DIR, path)))

def _log(msg):
    print msg
