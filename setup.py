import os
from os.path import abspath, join, dirname, isdir, isfile
from distutils.core import setup


def find_packages(where):
    def is_package(path):
        return isdir(path) and isfile(join(path, '__init__.py'))
    pkgs = []
    for dirpath, dirs, _ in os.walk(where):
        for dir_name in dirs:
            pkg_path = join(dirpath, dir_name)
            if is_package(pkg_path):
                pkgs.append('.'.join((pkg_path.split(os.sep)[1:])))
    return pkgs

ROOT_DIR = dirname(abspath(__file__))
SOURCE_DIR = 'src'

execfile(join(ROOT_DIR, 'src', 'robotide', 'version.py'))

package_data = {
    'robotide.preferences': ['settings.cfg'],
    'robotide.widgets': ['*.png', '*.ico'],
    'robotide.messages': ['*.html'],
    'robotide.publish.html': ['no_robot.html']
}

long_description = """
Robot Framework is a generic test automation framework for acceptance
level testing. RIDE is a lightweight and intuitive editor for Robot
Framework test data.
""".strip()

classifiers = """
Development Status :: 5 - Production/Stable
License :: OSI Approved :: Apache Software License
Operating System :: OS Independent
Programming Language :: Python
Topic :: Software Development :: Testing
""".strip().splitlines()

setup(
    name='robotframework-ride',
    version=VERSION,
    description='RIDE :: Robot Framework Test Data Editor',
    long_description=long_description,
    license='Apache License 2.0',
    keywords='robotframework testing testautomation',
    platforms='any',
    classifiers=classifiers,
    author='Robot Framework Developers',
    author_email='robotframework@gmail.com',
    url='https://github.com/robotframework/RIDE/',
    download_url='https://pypi.python.org/pypi/robotframework-ride',
    package_dir={'': SOURCE_DIR},
    packages=find_packages(SOURCE_DIR),
    package_data=package_data,
    # Robot Framework package data is not included, but RIDE does not need it.
    # Always install everything, since we may be switching between versions
    options={'install': {'force': True}},
    scripts=['src/bin/ride.py', 'ride_postinstall.py'],
    requires=['Pygments']
)
