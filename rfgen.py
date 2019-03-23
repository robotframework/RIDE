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
import optparse
import os
import random
import shutil
import sys
import sqlite3
from sqlite3 import OperationalError
import copy
from time import time
try:
    import urllib2
except ImportError:  # py3
    import urllib as urllib2

if sys.version_info[0] == 2:
    print("rfgen: Running under Python 2")  # DEBUG
    PYTHON2 = True
    PYTHON3 = False
elif sys.version_info[0] == 3:
    print("rfgen: Running under Python 3")  # DEBUG
    PYTHON2 = False
    PYTHON3 = True


ROOT = os.path.dirname(__file__)
lib = os.path.join(ROOT, '..', 'lib')
src = os.path.join(ROOT, '..', 'src')

sys.path.insert(0, lib)
sys.path.insert(0, src)


class MyRandomizer:

    def __init__(self, seed=None):
        self.myrandom = random.Random()
        if not seed:
            self.seed = int(time())
        else:
            self.seed = int(seed)
        self.myrandom.seed(self.seed)
        self.len_of_words = len(words)
        self.len_of_verbs = len(verbs)

    def get_seed(self):
        return self.seed

    def choice(self, theArray, capitalize=False, prefix=""):
        chosen = theArray[self.myrandom.randint(0, len(theArray) - 1)]
        if type(chosen) is tuple:
            return chosen
        if capitalize:
            chosen = chosen.capitalize()
        return "%s%s" % (prefix, chosen)

    def get_random_name(self, prefix=""):
        return self.choice(words, capitalize=True, prefix=prefix)

    def get_random_verb(self, prefix=""):
        return self.choice(verbs, capitalize=False, prefix=prefix)

    def get_random_int(self, start, end):
        return self.myrandom.randint(start, end)

    def random(self):
        return self.myrandom.random()


class MyParser(optparse.OptionParser):

    def format_epilog(self, formatter):
        return self.epilog

    def format_help(self, formatter=None):
        if formatter is None:
            formatter = self.formatter
        result = []
        if self.usage:
            result.append(self.get_usage() + "\n")
        if self.description:
            result.append(self.format_description(formatter) + "\n")
        result.append(self.format_option_help(formatter))
        return "".join(result)


class TestResource:

    def __init__(self, path):
        pass


class TestLibrary:

    def __init__(self, path):
        self.lib_path = path
        self.lib_prefix = "CustomLib"
        self.lib_functionality = randomizer.get_random_name()
        self.lib_name = "%s%s" % (self.lib_prefix, self.lib_functionality)
        _sql_execute("INSERT INTO source (path, type) \
        VALUES ('%s', 'CUSTOMLIBRARY')" % self.lib_name)
        self.lib_file = open("%s/%s.py" % (self.lib_path, self.lib_name), "w")
        self.lib_doc = '\t"""Library documentation:\n' + '\t\t%s"""' % \
                                                         self.lib_name
        self.write("import os, time\n\n" + "class %s:\n" % self.lib_name +
                   "\tdef __init__(self):\n" + "\t%s\n" % self.lib_doc)
        self.write("\t\t%s" % _select_functionality() + "\n")
        self.verbs = copy.copy(verbs)
        self.kw_count = 1

    def add_keyword(self):
        if len(self.verbs) > 0:
            kw_name_prefix = self.verbs.pop().capitalize()
        else:
            kw_name_prefix = "KW_%d" % self.kw_count
        self.kw_count += 1
        kw_name = kw_name_prefix + "_" + self.lib_functionality
        _sql_execute("INSERT INTO keywords (name, source) VALUES ('%s', '%s')"
                     % (kw_name, self.lib_name))
        kw_doc = '"""Keyword documentation for %s"""' % kw_name
        self.write("\tdef %s(self):\n" % kw_name + "\t\t%s\n" % kw_doc +
                   "\t\t%s\n" % _select_functionality())

    def write(self, text):
        self.lib_file.write(text)

    def close(self):
        db_connection.commit()
        self.write("myinstance = %s()" % self.lib_name)
        self.lib_file.close()


class TestSuite(object):

    def __init__(self, path, test_index, avg_test_depth, test_validity,
                 test_count):
        self.path = path
        self.test_index = test_index
        self.avg_test_depth = avg_test_depth
        self.test_validity = test_validity
        self.test_count = test_count
        self.libraries_in_use = {}
        self.suite_tag = None
        self.error_count = 0
        self.keywords_txt = self._create_keyword_txt()
        self.settings_txt = ""
        self.variables_txt = ""
        self.test_txt = ""
        self.selected_library = None
        self.library_index = 0
        self.generated_errors = 0
        self.external_resource_used = 0
        self.available_external_resources = _sql_select("SELECT path FROM "
                                                        "source WHERE type ="
                                                        " 'EXT_RESOURCE' ORDER"
                                                        " BY RANDOM()", True)
        self.available_keywords = []
        self.available_libraries = _sql_select("SELECT path FROM source WHERE"
                                               " type = 'CUSTOMLIBRARY'", True)
        self.available_resources = _sql_select("SELECT path FROM source WHERE"
                                               " type = 'RESOURCE' ORDER BY"
                                               " RANDOM()", True)
        self.external_resource_count = len(self.available_external_resources)

    @staticmethod
    def _create_keyword_txt():
        return """\
*** Keywords ***
My Suite Keyword
    [Arguments]    ${something}
    No Operation
"""

    def write(self):
        with open("%s/T%d_CustomTests.txt" % (self.path, self.test_index + 1),
                  "w") as tcfile:
            tcfile.write(self.settings_txt + "\n")
            tcfile.write(self.variables_txt + "\n")
            tcfile.write(self.test_txt)
            tcfile.write(self.keywords_txt)

    def set_settings(self, settings_txt):
        self.settings_txt = settings_txt

    def get_libraries(self):
        return self.libraries_in_use

    def get_external_resource_count(self):
        return self.external_resource_count

    def get_test_validity(self):
        return self.test_validity

    def get_force_tag(self):
        if self.suite_tag:
            return "Force Tags\t%s\n" % self.suite_tag
        return ""

    def get_test_count(self):
        return self.test_count

    def get_test_depth(self):
        return self.avg_test_depth + randomizer.get_random_int(-1, 1)

    def is_error_generated(self):
        if self.test_validity < 1 and randomizer.random() >\
                (self.test_validity * 1.0):
            self.error_count += 1
            return True
        return False

    def is_external_resource_used(self):
        if self.external_resource_used == 0:
            return False
        else:
            return True

    def add_external_keyword(self):
        if self.external_resource_count > 0:
            self.external_resource_used += 1
            return _add_external_keyword()
        return ""

    def select_library(self):
        self.selected_library = randomizer.choice(self.available_libraries)
        self.available_keywords = _sql_select("SELECT * FROM keywords WHERE"
                                              " source IN ('%s', 'BuiltIn', "
                                              "'OperatingSystem', 'String')"
                                              % self.selected_library)
        if self.selected_library not in self.libraries_in_use.values():
            self.add_library_in_use(self.selected_library)

    @property
    def next_free(self):
        self.library_index += 1
        return self.library_index

    def add_library_in_use(self, library_value):
        use_with_name = randomizer.choice([True, False])
        library_key = library_value
        if use_with_name:
            library_key = "Cus%d" % self.next_free
        self.libraries_in_use[library_key] = library_value

    def insert_test_step(self):
        test_txt = ""
        generate_error = self.is_error_generated()
        keyword = randomizer.choice(self.available_keywords)
        kw_library = keyword[2]
        kw_action = keyword[1].replace("_", " ")
        kw_args = keyword[3]
        kw_return = keyword[4]
        if PYTHON2:
            for key, val in self.get_libraries().iteritems():
                if val == kw_library:
                    kw_library = key
        elif PYTHON3:
            for key, val in self.get_libraries().items():
                if val == kw_library:
                    kw_library = key
        if generate_error:
            kw_action += "_X"
            self.generated_errors += 1
        if kw_library in ('BuiltIn', 'OperatingSystem', 'String'):
            kw_total = kw_action
        else:
            kw_total = "%s.%s" % (kw_library, kw_action)
        argument = None
        return_statement = None
        if kw_args == 1:
            argument = randomizer.get_random_name().lower()
        if kw_return == 1:
            return_statement = "${ret}="
        test_txt += "\t\t"
        if return_statement:
            test_txt += return_statement
        test_txt += "\t%s" % kw_total
        if argument:
            if kw_action == "Count Files In Directory":
                test_txt += "\t" + os.path.abspath(os.curdir).replace("\\",
                                                                      "/")
            else:
                test_txt += "\t" + argument
        test_txt += "\n"
        if return_statement:
            test_txt += "\t\tLog\t${ret}\n"
        return test_txt

    def force_one_error_or_not(self, tc):
        if tc == self.get_test_count() - 1 and self.generated_errors == 0 \
                and self.get_test_validity() < 1:
            return "\t\tLogX\t${ret}\n"
        return ""

    @staticmethod
    def tag_test_suite():
        suite_tag = randomizer.choice(common_tags)
        test_tag = randomizer.choice(common_tags)
        if test_tag != suite_tag and randomizer.get_random_int(1, 2) == 1:
            return "\t[Tags]\t%s\n" % test_tag
        return ""

    def _construct_settings(self):
        self.settings_txt += "*** Settings ***\n"
        self.settings_txt += keyword_and_arguments("Documentation", """http://www.google.fi
...\t\t
...\t\tSuite documentation test added from RIDE.
...\t\t
...\t\tThe new *bolded* _underscore_ line.""")
        self.settings_txt += keyword_and_arguments("Suite Setup", "Log",
                                                   "Suite Setup")
        self.settings_txt += keyword_and_arguments("Suite Teardown", "Log",
                                                   "Suite Teardown")
        self.settings_txt += keyword_and_arguments("Test Setup", "Log",
                                                   "Test Setup")
        self.settings_txt += keyword_and_arguments("Test Teardown", "Log",
                                                   "Test Teardown")
        self.settings_txt += keyword_and_arguments("Test Timeout", "1 min")
        self.settings_txt += keyword_and_arguments("Library",
                                                   "OperatingSystem")
        self.settings_txt += keyword_and_arguments("Library", "String")
        self.settings_txt += self.get_force_tag()
        self.settings_txt += keyword_and_arguments("Metadata", "seed", "%d" %
                                                   randomizer.get_seed())

        for x in range(randomizer.get_random_int(0, 2)):
            try:
                selected_resource = self.available_resources.pop()
                self.settings_txt += keyword_and_arguments("Resource",
                                                           selected_resource)
            except IndexError:
                break
                # USE ALL EXTERNAL RESOURCES
        for res in self.available_external_resources:
            self.settings_txt += keyword_and_arguments("Resource", res)

    def _construct_variables(self):
        self.variables_txt += "*** Variables ***\n"
        self.variables_txt += keyword_and_arguments("${suite_scalar_variable}",
                                                    "abcd123")
        self.variables_txt += keyword_and_arguments("@{suite_list_variable}",
                                                    "x", "y", "z")

    def construct(self):
        self._construct_settings()
        self._construct_variables()

        self.test_txt = "*** Test Cases ***\n"
        for tc in range(self.get_test_count()):
            self.select_library()
            tc_name = "Test %s in %s #%d" % (randomizer.get_random_verb(),
                                             self.selected_library.split(
                                                 "CustomLib")[1], tc)
            self.test_txt += "%s\t[Documentation]\t%s\n" % (
                tc_name, "Test %d - %s\\n\\n%s" %
                (tc, "test level documentation",
                 randomizer.get_random_name()))
            self.test_txt += self.tag_test_suite()
            for i in range(self.get_test_depth()):
                if self.external_resource_count > 0 \
                        and not self.is_external_resource_used():
                    self.test_txt += self.add_external_keyword()
                self.test_txt += self.insert_test_step()
            self.test_txt += self.force_one_error_or_not(tc)
            self.test_txt += "\n"

        if PYTHON2:
            for test_lib_key, test_lib_value in \
                    self.get_libraries().iteritems():
                if test_lib_key != test_lib_value:
                    self.settings_txt += keyword_and_arguments("Library",
                                                               "%s.py" %
                                                               test_lib_value,
                                                               "WITH NAME",
                                                               test_lib_key)
                else:
                    self.settings_txt += keyword_and_arguments("Library",
                                                               "%s.py" %
                                                               test_lib_value)
        elif PYTHON3:
            for test_lib_key, test_lib_value in self.get_libraries().items():
                if test_lib_key != test_lib_value:
                    self.settings_txt += keyword_and_arguments("Library",
                                                               "%s.py" %
                                                               test_lib_value,
                                                               "WITH NAME",
                                                               test_lib_key)
                else:
                    self.settings_txt += keyword_and_arguments("Library",
                                                               "%s.py" %
                                                               test_lib_value)


def _select_functionality():
    directory_looper = "for dirname, dirnames, filenames in os.walk('.'):\n" +\
                       "\t\t\tfor subdirname in dirnames:\n" +\
                       "\t\t\t\tprint(os.path.join(dirname, subdirname))\n" +\
                       "\t\t\tfor filename in filenames:\n" +\
                       "\t\t\t\tprint(os.path.join(dirname, filename))\n"
    sleeper = "time.sleep(1)\n"
    return randomizer.choice([directory_looper, sleeper, "pass\n"])


def _sql_execute(sqlString=""):
    db_cursor.execute(sqlString)


def _sql_select(sqlString="", normalize=False):
    result = db_cursor.execute(sqlString).fetchall()
    if not normalize:
        return result
    return [i[0] for i in result]


def _create_test_libraries(dirs, filecount=10, keywords=10):
    path = dirs[0]
    libs = []

    for x in range(filecount):
        lib = TestLibrary(path)
        for y in range(keywords):
            lib.add_keyword()
        lib.close()
        libs.append(lib)


def _add_external_keyword():
    external_kw_not_used = True
    test_txt = ""
    if external_kw_not_used:
        test_txt += "\tMy Super KW\n"
        external_kw_not_used = False
    return test_txt


def _create_test_suites(dirs, filecount=1, test_count=20,
                        avg_test_depth=5, test_validity=1):
    path = dirs[0]

    for test_index in range(filecount):
        suite = TestSuite(path, test_index, avg_test_depth, test_validity,
                          test_count)
        suite.construct()
        suite.write()


def _create_static_resource_files(target_dir,
                                  filename="static_external_resource.txt",
                                  count=1):
    external_info = {}

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    static_external_resource_filename = filename
    static_external_resource = open(os.path.join(
        target_dir, static_external_resource_filename), "w")
    static_external_resource.write(
        "*** Keywords ***\nMy Super KW\n\tNo Operation")
    static_external_resource.close()
    external_info['filepath'] = os.path.join(target_dir,
                                             "ext_R%d_Resource.txt")
    external_info['import_path'] = os.path.join(
        "..", "ext", "ext_R%d_Resource.txt").replace("\\", "/")
    external_info['filename'] = static_external_resource_filename

    return external_info


def _create_resource_file(target_dir, subdir="", id=1):
    res_info = {'filename': "R%d_Resource.txt" % id}
    full_path = os.path.join(target_dir, subdir)
    res_info['import_path'] = res_info['filename'].replace("\\", "/")
    if subdir != "":
        res_info['import_path'] = os.path.join(
            subdir, res_info['filename']).replace("\\", "/")
    if not os.path.exists(full_path):
        os.makedirs(full_path)

    res_info['filepath'] = os.path.join(full_path, res_info['filename'])
    return res_info


def _create_test_resources(dirs, resource_files, resources_in_file,
                           external_resources, subdir=""):
    ext_info = _create_static_resource_files(dirs[1])
    variable_count = int(resources_in_file/2)
    keyword_count = resources_in_file - variable_count

    for resource_index in range(resource_files):
        res_info = _create_resource_file(dirs[0], subdir, resource_index+1)
        resfile_ondisk = open(res_info['filepath'], "w")

        content = "*** Settings ***\n"
        if external_resources > 0:
            content += "Resource\t" + (os.path.join(
                "../", ext_info['import_path']) % (
                randomizer.get_random_int(1, external_resources))) + "\n"

        content += "\n*** Variables ***\n"
        for x in range(variable_count):
            content += "%-25s%10s%d\n" % ("${%s%d}" % (
                randomizer.get_random_name(), x), "",
                                          randomizer.get_random_int(1, 1000))

        content += "\n*** Keywords ***\n"
        for x in range(keyword_count):
            kw_name = "Resource %s User Kw %d" % (
                randomizer.get_random_name(), x + 1)
            content += "%s\n\tNo Operation\n" % kw_name
            _sql_execute("INSERT INTO keywords (name, source) VALUES"
                         " ('%s', '%s')" % (kw_name, res_info['import_path']))
        _sql_execute("INSERT INTO source (path, type) VALUES ('%s',"
                     " 'RESOURCE')" % res_info['import_path'])
        resfile_ondisk.write(content)
        resfile_ondisk.close()

    for resource_index in range(external_resources):
        content = "*** Settings ***\n"
        content += "Resource\t%s\n" % ext_info['filename']
        content += "\n*** Keywords ***\n"
        kw_name = "External User Kw %d" % (resource_index+1)
        content += "%s\n\tNo Operation" % kw_name

        extfile_ondisk = open(ext_info['filepath'] % (resource_index+1), "w")
        extfile_ondisk.write(content)
        extfile_ondisk.close()
        _sql_execute("INSERT INTO keywords (name, source) VALUES ('%s', '%s')"
                     % (kw_name, ext_info['import_path'] % (resource_index+1)))
        _sql_execute("INSERT INTO source (path, type) VALUES ('%s',"
                     " 'EXT_RESOURCE')" % ext_info['import_path'] %
                     (resource_index+1))


def _create_test_project(dirs, testlibs_count=5, keyword_count=10,
                         testsuite_count=5, tests_in_suite=10,
                         resource_count=10, resources_in_file=20,
                         avg_test_depth=5, test_validity=1,
                         external_resources=0):
    print("""Generating test project with following settings
    %d test libraries (option 'l')
    %d keywords per test library (option 'k')
    %d test suites (option 's')
    %d tests per test suite (option 't')
    %d test steps per test case (option 'e')
    %d resource files (option 'f')
    %d external resource files (option 'g')
    %d resources per resource file (option 'r')""" %
          (testlibs_count, keyword_count, testsuite_count,
           tests_in_suite, avg_test_depth, resource_count,
           external_resources, resources_in_file))

    _create_test_libraries(dirs, filecount=testlibs_count,
                           keywords=keyword_count)
    _create_test_resources(dirs, subdir="resources",
                           resource_files=resource_count,
                           resources_in_file=resources_in_file,
                           external_resources=external_resources)
    _create_test_suites(dirs, filecount=testsuite_count,
                        test_count=tests_in_suite,
                        avg_test_depth=avg_test_depth,
                        test_validity=test_validity)

    print("""\

    Seed was %d""" % randomizer.get_seed())

    fo_seed = open(os.path.join(dirs[2], "seed.txt"), "w")
    fo_seed.write("%d" % randomizer.get_seed())
    fo_seed.close()


def create_options_parser():
    desc = """This script generates Robot Framework project structure. The \
structure contains test suites, resource files and test libraries. Test \
suites and tests are randomly marked with tags.

You can define number of test cases in suites, resources in a resource files \
or keywords in a library."""

    parser = MyParser(description=desc)

    group1 = optparse.OptionGroup(parser, 'Test related options')
    group2 = optparse.OptionGroup(parser, 'Common options')

    group1.add_option("-l", "--libs", dest="libs",
                      help="Number of test libraries [default: %default]",
                      default=5)
    group1.add_option("-k", "--keywords", dest="keywords",
                      help="Number of keywords in a test library [default: "
                           "%default]", default=10)
    group1.add_option("-s", "--suites", dest="suites",
                      help="Number of test suites  [default: %default]",
                      default=1)
    group1.add_option("-t", "--tests", dest="tests",
                      help="Number of tests in a suite  [default: %default]",
                      default=10)
    group1.add_option("-f", "--resourcefiles", dest="resourcefiles",
                      help="Number of resource files.  [default: %default]",
                      default=1)
    group1.add_option("-g", "--externalresources", dest="externalresources",
                      help="Number of external resource files.  [default: "
                           "%default]", default=0)
    group1.add_option("-r", "--resources", dest="resources",
                      help="Number of resources in a file.  [default: "
                           "%default]", default=30)
    group1.add_option("-v", "--validity", dest="validity",
                      help="Validity of test cases (1...0). To have ~80% "
                           "passes give 0.8.  [default: %default]", default=1)
    group1.add_option("-e", "--testdepth", dest="testdepth",
                      help="Average number of steps in a test case (2..)  "
                           "[default: %default]", default=3)
    group2.add_option("-d", "--dir", dest="dir", help="Target directory for "
                                                      "the test project "
                                                      "[default: %default]",
                      default=os.path.join(".", "tmp"))
    group2.add_option("", "--seed", dest="seed",
                      help="Give a random seed (integer) to generate specific "
                           "test structure. By default this is randomized.",
                      default=None)
    group2.add_option("-u", "--upgrade", help="Upgrade rfgen.py from the "
                                              "github. Remember 'pip install "
                                              "with --upgrade' if you have pip"
                                              " installation.",
                      action="store_true", dest="upgrade", default=False)

    parser.add_option_group(group1)
    parser.add_option_group(group2)

    return parser


def keyword_and_arguments(kw, *args):
    return "%s\t%s\n" % (kw, "\t".join(args))


def main(options=None):
    global db_connection, db_cursor, words, randomizer

    parser = create_options_parser()
    (options, args) = parser.parse_args()

    if options.upgrade:
        try:
            with open('rfgen.py') as f:
                pass
        except IOError as e:
            print("You probably want to do 'pip install "
                  "git+https://github.com/robotframework/Generator'")
            sys.exit(0)
        rfgen_url = \
            "https://raw.github.com/robotframework/Generator/master/rfgen.py"
        print("Updating rfgen.py from github.")
        f = open('rfgen.py', 'wb')
        f.write(urllib2.urlopen(rfgen_url).read())
        f.close()
        print("Update done.")
        sys.exit(0)

    path = options.dir or sys.exit("Error: No path was defined")
    testlibs_count = int(options.libs) or 5
    keyword_count = int(options.keywords) or 10
    testsuite_count = int(options.suites) or 1
    tests_in_suite = int(options.tests) or 10
    resource_count = int(options.resourcefiles) or 1
    resources_in_file = int(options.resources) or 30
    avg_test_depth = int(options.testdepth) or 3
    test_validity = float(options.validity) or 1
    external_resources = int(options.externalresources) or 0

    randomizer = MyRandomizer(options.seed)

    if avg_test_depth < 2:
        avg_test_depth = 2
    if test_validity > 1:
        test_validity = 1
    elif test_validity < 0:
        test_validity = 0

    project_root_dir = os.path.join(path, "testdir")
    external_resources_dir = os.path.join(path, "ext")
    sys.path.append(project_root_dir)
    shutil.rmtree(project_root_dir, ignore_errors=True)
    shutil.rmtree(external_resources_dir, ignore_errors=True)
    print("Test project is created into directory (option 'd'): %s" %
          project_root_dir)

    if not os.path.exists(project_root_dir):
        os.makedirs(project_root_dir)

    db_connection = sqlite3.connect(os.path.join(project_root_dir,
                                                 "testdata.db"))
    db_cursor = db_connection.cursor()
    try:
        _sql_execute('CREATE TABLE IF NOT EXISTS source (id INTEGER '
                     'PRIMARY KEY, path TEXT, type TEXT)')
        _sql_execute('CREATE TABLE IF NOT EXISTS keywords (id INTEGER PRIMARY '
                     'KEY, name TEXT, source TEXT, arguments INTEGER, '
                     'returns INTEGER)')
        _sql_execute('DELETE FROM source')
        _sql_execute('DELETE FROM keywords')
        libs_to_insert = [("BuiltIn", "LIBRARY"), ("OperatingSystem",
                                                   "LIBRARY"), ("String",
                                                                "LIBRARY")]
        db_cursor.executemany('INSERT INTO source (path, type) VALUES (?, ?)',
                              libs_to_insert)
        keywords_to_insert = [("Log", "BuiltIn", 1, 0), ("No Operation",
                                                         "BuiltIn", 0, 0),
                              ("Get Time", "BuiltIn", 0, 1),
                              ("Count Files In Directory", "OperatingSystem",
                               1, 1), ("Get Environment Variables",
                                       "OperatingSystem", 0, 1),
                              ("Get Time", "BuiltIn", 0, 1)]
        db_cursor.executemany('INSERT INTO keywords (name, source, arguments, '
                              'returns) VALUES (?, ?, ?, ?)',
                              keywords_to_insert)
        db_connection.commit()
    except OperationalError as err:
        print("DB error: ", str(err))

    _create_test_project([project_root_dir, external_resources_dir, path],
                         testlibs_count, keyword_count, testsuite_count,
                         tests_in_suite, resource_count, resources_in_file,
                         avg_test_depth, test_validity, external_resources)
    result = "PASS"
    return result != 'FAIL'


# Global variables
start_time = None
end_time = None

db_connection = None
db_cursor = None

common_tags = ['general', 'feature', 'important', 'regression', 'performance',
               'usability']
verbs = ['do', 'make', 'execute', 'select', 'count', 'process', 'insert',
         'validate', 'verify', 'filter', 'magnify']
words = ['abstraction', 'acetifier', 'acrodont', 'adenographical',
         'advisableness', 'afterbreast', 'agrogeology', 'albuminoscope',
         'alkarsin', 'Alsophila', 'American', 'amphitheatral', 'anapnoic',
         'angiography', 'annulation', 'Anthoxanthum', 'antihelminthic',
         'antisymmetrical', 'apoatropine', 'approximation', 'archgovernor',
         'Arimaspian', 'arthrospore', 'asportation', 'atangle', 'audiometric',
         'autolaryngoscopy', 'awlwort', 'backspierer', 'ballast', 'bargoose',
         'Bathonian', 'becrawl', 'belatedness', 'bepaper', 'Bettina', 'bija',
         'biriba', 'blastopore', 'blunge', 'bony', 'Bourbon', 'brandreth',
         'Britain', 'Bryum', 'bur', 'cabbagewood', 'calciocarnotite',
         'Campodea', 'capitulum', 'careener', 'cask', 'catstitch', 'censual',
         'certify', 'chantey', 'chelydroid', 'chiromantical', 'chopa',
         'Chrysotis', 'circumgyrate', 'clausure', 'clot', 'cocculiferous',
         'cogue', 'coloring', 'companator', 'concordancer', 'conjointment',
         'contemporary', 'coolness', 'cornigerous', 'costopleural',
         'counterscrutiny', 'craniological', 'criniculture', 'cryoscopy',
         'cunye', 'cyclamin', 'cyton', 'dapple', 'debtorship', 'deedbox',
         'delignification', 'denitrator', 'dermatopnagic', 'detinet',
         'dialogue', 'Dielytra', 'dioecious', 'discarnate', 'dishrag',
         'dissertationist', 'dochmiac', 'dopebook', 'drainable', 'dubitant',
         'dynamometer', 'ecostate', 'Eimak', 'elephantoidal', 'Emilia',
         'enderonic', 'Enki', 'entreat', 'epimerite', 'equoidean',
         'esophagoplasty', 'eudiometric', 'Evodia', 'existently',
         'extensional', 'facsimilist', 'fasciculus', 'feminacy', 'fickly',
         'firepower', 'flawful', 'flunkeyize', 'forbiddable', 'fork',
         'frangula', 'frontomaxillary', 'furnishing', 'gallows',
         'Gasterosteidae', 'Gemmingia', 'germanious', 'girdlingly',
         'glossoptosis', 'Goldbird', 'gracelessly', 'greatheart', 'gruelly',
         'gurl', 'Haemogregarinidae', 'handsomeness', 'hause', 'heedfulness',
         'hemianopia', 'heptine', 'heterologous', 'highway', 'hoernesite',
         'homoiothermic', 'horseway', 'humulene', 'hydromaniac',
         'hypercorrection', 'hypogean', 'ichthyal', 'illaudation',
         'impassioned', 'impuberal', 'incomprehension', 'indigitate',
         'infare', 'iniquitously', 'insooth', 'intercombination', 'interpiece',
         'intranatal', 'iodinophilic', 'irritomotile', 'isotomous', 'jaragua',
         'jocundity', 'just', 'janne', 'Kedushshah', 'kiln', 'knowledging',
         'labialization', 'lamboys', 'larkish', 'leadable', 'lenticularis',
         'lexicologist', 'Limnoria', 'lithogenetic', 'logographical',
         'loxotic', 'lycanthropist', 'macrotous', 'malacodermatous',
         'manganeisen', 'Marianolatry', 'matador', 'mecometry',
         'melastomaceous', 'merchantableness', 'Messiah', 'methylotic',
         'microphotoscope', 'milsey', 'Mikko', 'miscompute', 'mistranslation',
         'mollycoddling', 'monolocular', 'mora', 'mountainette',
         'multimillion', 'Mussulwoman', 'myrmecology', 'Napoleonana',
         'necrographer', 'nephrohydrosis', 'newsprint', 'noble', 'nonchalky',
         'nonelemental', 'nonmalignant', 'nonresident', 'nonvolcanic',
         'nubbling', 'obituarist', 'octary', 'oilcan', 'onca', 'opianyl',
         'organizational', 'Ortol', 'Otomi', 'outroar', 'overcasting',
         'overgrow', 'overregister', 'overwrought', 'pachyphyllous',
         'paleface', 'pancyclopedic', 'papion', 'parareka', 'parsonese',
         'patriarchalism', 'pedagogy', 'penetration', 'percolate',
         'peripherically', 'perspiration', 'Phalangerinae', 'philocatholic',
         'photoceramics', 'phyllomorphy', 'picrorhizin', 'pinguid', 'placer',
         'platymesocephalic', 'plouky', 'poditti', 'polyaxial',
         'polysporangium', 'porphyrin', 'postoperative', 'prankle',
         'precoloration', 'predivinity', 'prelusion', 'presalvation',
         'prevaricatory', 'probeer', 'progger', 'proportionality',
         'Protoascales', 'prytanis', 'pseudospherical', 'publican',
         'puppetize', 'pyrazolyl', 'quadruplex', 'quink', 'radiocarbon',
         'Ranquel', 'reaggregation', 'recessively', 'recurve', 'reforestize',
         'reinstruct', 'renderable', 'reprovably', 'respue', 'retrofracted',
         'rhapsodie', 'rictus', 'robustly', 'rosoli', 'ruinator', 'sacciform',
         'Salmon', 'Santos', 'sauqui', 'scatterbrain', 'scirtopodous',
         'scrawler', 'sealant', 'selaginellaceous', 'semiglobe', 'senaite',
         'serin', 'sextuplet', 'sheetwork', 'shortener', 'sighted',
         'Singhalese', 'skelping', 'sleighty', 'Smithsonian', 'soapbush',
         'somacule', 'souper', 'spectator', 'spicular', 'splinder',
         'spumiform', 'stainproof', 'stearin', 'stethoscope', 'stoneworker',
         'strich', 'stylite', 'subequality', 'subprincipal', 'succubine',
         'sulphoterephthalic', 'supereminent', 'superstrong', 'survivalism',
         'swollenly', 'synecdochism', 'tactite', 'tangence', 'Tashnakist',
         'tectibranchiate', 'temporoalar', 'terral', 'Teutomania',
         'theopneusty', 'thiofurane', 'thumblike', 'timbale', 'tobaccoism',
         'topmast', 'toxicemia', 'transconductance', 'treading', 'trichromat',
         'triphammer', 'trophodynamic', 'tubinarine', 'turnsheet',
         'typographical', 'umbonule', 'unappeasedly', 'unbetray',
         'unchangedness', 'unconditional', 'uncurst', 'underfeature',
         'undertie', 'undowny', 'uneviscerated', 'unflaunted', 'ungovernable',
         'unicameralist', 'unintersected', 'unlikelihood', 'unmollifiable',
         'unpanel', 'unprecautioned', 'unreasonable', 'unride',
         'unserviceable', 'unspicy', 'unswept', 'untroubledly',
         'unwillingness', 'upthunder', 'urtication', 'vallancy',
         'vegetation', 'vermiculite', 'victualer', 'visionist', 'voting',
         'wany', 'Wazir', 'wheam', 'whuttering', 'wishedly', 'workbasket',
         'xenium', 'yen', 'zeuglodont', 'zygophoric']


if __name__ == '__main__':
    main()
