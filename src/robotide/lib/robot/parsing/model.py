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

import os
import copy
import re
import warnings

from robotide.lib.robot.errors import DataError
from robotide.lib.robot.variables import is_var
from robotide.lib.robot.output import LOGGER
from robotide.lib.robot.writer import DataFileWriter
from robotide.lib.robot.utils import abspath, is_string, normalize, py2to3, NormalizedDict

from .comments import Comment
from .populators import FromFilePopulator, FromDirectoryPopulator, NoTestsFound
from .settings import (Documentation, Fixture, Timeout, Tags, Metadata,
                       Library, Resource, Variables, Arguments, Return,
                       Template, MetadataList, ImportList)

re_set_var = re.compile(r"(?i)^set[ ](\S.*)+variable$")


def TestData(parent=None, source=None, include_suites=None,
             warn_on_skipped='DEPRECATED', extensions=None, settings=None):
    """Parses a file or directory to a corresponding model object.

    :param parent: Optional parent to be used in creation of the model object.
    :param source: Path where test data is read from.
    :param warn_on_skipped: Deprecated.
    :param extensions: List/set of extensions to parse. If None, all files
        supported by Robot Framework are parsed when searching test cases.
    :returns: :class:`~.model.TestDataDirectory`  if `source` is a directory,
        :class:`~.model.TestCaseFile` otherwise.
    """
    # TODO: Remove in RF 3.2.
    if warn_on_skipped != 'DEPRECATED':
        warnings.warn("Option 'warn_on_skipped' is deprecated and has no "
                      "effect.", DeprecationWarning)
    if os.path.isdir(source):
        return TestDataDirectory(parent, source, settings).populate(include_suites,
                                                          extensions)
    return TestCaseFile(parent, source, settings).populate()


class _TestData(object):
    _setting_table_names = 'Setting', 'Settings'
    _variable_table_names = 'Variable', 'Variables'
    _testcase_table_names = 'Test Case', 'Test Cases', 'Task', 'Tasks'
    _keyword_table_names = 'Keyword', 'Keywords'
    # remove Comments section, because we want to keep them as they are in files
    _comment_table_names = 'Comment', 'Comments'

    def __init__(self, parent=None, source=None):
        self.parent = parent
        self.source = abspath(source) if source else None
        self.children = []
        self._preamble = []
        self._tables = dict(self._get_tables())

    def _get_tables(self):
        for names, table in [(self._setting_table_names, self.setting_table),
                             (self._variable_table_names, self.variable_table),
                             (self._testcase_table_names, self.testcase_table),
                             (self._keyword_table_names, self.keyword_table),
                             (self._comment_table_names, None)]:
            # remove Comments section, because we want to keep them as they are in files
            # , (self._comment_table_names, None)]:
            for name in names:
                yield name, table

    def start_table(self, header_row):
        table = self._find_table(header_row)
        if table is None or not self._table_is_allowed(table):
            return None
        table.set_header(header_row)
        return table

    def has_preamble(self):
        return len(self.preamble) > 0

    def add_preamble(self, row):
        self._preamble.append(row)

    @property
    def preamble(self):
        return self._preamble

    @preamble.setter
    def preamble(self, row):
        self.add_preamble(row)

    def _find_table(self, header_row):
        name = header_row[0] if header_row else ''
        title = name.title()
        if title not in self._tables:
            title = self._resolve_deprecated_table(name)
            if title is None:
                self._report_unrecognized_table(name)
                return None
        return self._tables[title]

    def _resolve_deprecated_table(self, used_name):
        normalized = normalize(used_name)
        for name in (self._setting_table_names + self._variable_table_names +
                     self._testcase_table_names + self._keyword_table_names):
            # remove Comments section, because we want to keep them as they are in files
            # + self._comment_table_names):
            if normalize(name) == normalized:
                self._report_deprecated_table(used_name, name)
                return name
        return None

    def _report_deprecated_table(self, deprecated, name):
        self.report_invalid_syntax(
            "Section name '%s' is deprecated. Use '%s' instead."
            % (deprecated, name), level='WARN'
        )

    def _report_unrecognized_table(self, name):
        self.report_invalid_syntax(
            "Unrecognized table header '%s'. Available headers for data: "
            "'Setting(s)', 'Variable(s)', 'Test Case(s)', 'Task(s)' and "
            "'Keyword(s)'. Use 'Comment(s)' to embedded additional data."
            % name
        )

    def _table_is_allowed(self, table):
        return True

    @property
    def name(self):
        return self._format_name(self._get_basename()) if self.source else None

    @property
    def rawname(self):
        return self._get_basename() if self.source else None
        # To be used on resource prefixed suggestions

    def _get_basename(self):
        return os.path.splitext(os.path.basename(self.source))[0]

    def _format_name(self, name):
        name = self._strip_possible_prefix_from_name(name)
        name = name.replace('_', ' ').strip()
        return name.title() if name.islower() else name

    def _strip_possible_prefix_from_name(self, name):
        return name.split('__', 1)[-1]

    @property
    def keywords(self):
        return self.keyword_table.keywords

    @property
    def imports(self):
        return self.setting_table.imports

    def report_invalid_syntax(self, message, level='ERROR'):
        initfile = getattr(self, 'initfile', None)
        path = os.path.join(self.source, initfile) if initfile else self.source
        LOGGER.write("Error in file '%s': %s" % (path, message), level)

    def save(self, **options):
        """Writes this datafile to disk.

        :param options: Configuration for writing. These are passed to
            :py:class:`~robot.writer.datafilewriter.WritingContext` as
            keyword arguments.

        See also :py:class:`robot.writer.datafilewriter.DataFileWriter`
        """
        return DataFileWriter(**options).write(self)


@py2to3
class TestCaseFile(_TestData):
    """The parsed test case file object.

    :param parent: parent object to be used in creation of the model object.
    :param source: path where test data is read from.
    """
    __test__ = False

    def __init__(self, parent=None, source=None, settings=None):
        self.directory = os.path.dirname(source) if source else None
        self.setting_table = TestCaseFileSettingTable(self)
        self.variable_table = VariableTable(self)
        self.testcase_table = TestCaseTable(self)
        self.keyword_table = KeywordTable(self)
        self._settings = settings
        self._tab_size = self._settings.get('txt number of spaces', 2) if self._settings else 2
        _TestData.__init__(self, parent, source)

    def populate(self):
        FromFilePopulator(self, self._tab_size).populate(self.source)
        self._validate()
        return self

    def _validate(self):
        if not self.testcase_table.is_started():
            # print(f"DEBUG: Model TestCaseFile _validate this is where there are no tests")
            raise NoTestsFound('File has no tests or tasks.')

    def has_tests(self):
        return True

    def __iter__(self):
        for table in [self.setting_table, self.variable_table,
                      self.testcase_table, self.keyword_table]:
            yield table

    def __nonzero__(self):
        return any(table for table in self)


class ResourceFile(_TestData):
    """The parsed resource file object.

    :param source: path where resource file is read from.
    """

    def __init__(self, source=None, settings=None):
        self.directory = os.path.dirname(source) if source else None
        self.setting_table = ResourceFileSettingTable(self)
        self.variable_table = VariableTable(self)
        self.testcase_table = TestCaseTable(self)
        self.keyword_table = KeywordTable(self)
        self.settings = settings
        self._tab_size = self.settings.get('txt number of spaces', 2) if self.settings else 2
        _TestData.__init__(self, source=source)

    def populate(self):
        FromFilePopulator(self, self._tab_size).populate(self.source, resource=True)
        self._report_status()
        return self

    def _report_status(self):
        if self.setting_table or self.variable_table or self.keyword_table:
            LOGGER.info("Imported resource file '%s' (%d keywords)."
                        % (self.source, len(self.keyword_table.keywords)))
        else:
            LOGGER.warn("Imported resource file '%s' is empty." % self.source)

    def _table_is_allowed(self, table):
        if table is self.testcase_table:
            raise DataError("Resource file '%s' cannot contain tests or "
                            "tasks." % self.source)
        return True

    def __iter__(self):
        for table in [self.setting_table, self.variable_table, self.keyword_table]:
            yield table


class TestDataDirectory(_TestData):
    """The parsed test data directory object. Contains hiearchical structure
    of other :py:class:`.TestDataDirectory` and :py:class:`.TestCaseFile`
    objects.

    :param parent: parent object to be used in creation of the model object.
    :param source: path where test data is read from.
    """
    __test__ = False

    def __init__(self, parent=None, source=None, settings=None):
        self.directory = source
        self.initfile = None
        self.setting_table = InitFileSettingTable(self)
        self.variable_table = VariableTable(self)
        self.testcase_table = TestCaseTable(self)
        self.keyword_table = KeywordTable(self)
        self._settings = settings
        self._tab_size = self._settings.get('txt number of spaces', 2) if self._settings else 2
        _TestData.__init__(self, parent, source)

    def populate(self, include_suites=None, extensions=None, recurse=True):
        FromDirectoryPopulator().populate(self.source, self, include_suites,
                                          extensions, recurse, self._tab_size)
        self.children = [ch for ch in self.children if ch.has_tests()]
        return self

    def _get_basename(self):
        return os.path.basename(self.source)

    def _table_is_allowed(self, table):
        if table is self.testcase_table:
            LOGGER.error("Test suite initialization file in '%s' cannot "
                         "contain tests or tasks." % self.source)
            return False
        return True

    def add_child(self, path, include_suites, extensions=None):
        self.children.append(TestData(parent=self,
                                      source=path,
                                      include_suites=include_suites,
                                      extensions=extensions, settings=self._settings))

    def has_tests(self):
        return any(ch.has_tests() for ch in self.children)

    def __iter__(self):
        for table in [self.setting_table, self.variable_table, self.keyword_table]:
            yield table


@py2to3
class _Table(object):

    def __init__(self, parent):
        self.parent = parent
        self._header = None

    def set_header(self, header):
        self._header = self._prune_old_style_headers(header)

    def _prune_old_style_headers(self, header):
        if len(header) < 3:
            return header
        if self._old_header_matcher.match(header):
            return [header[0]]
        return header

    @property
    def header(self):
        return self._header or [self.type.title() + 's']

    @property
    def name(self):
        return self.header[0]

    @property
    def source(self):
        return self.parent.source

    @property
    def directory(self):
        return self.parent.directory

    def report_invalid_syntax(self, message, level='ERROR'):
        self.parent.report_invalid_syntax(message, level)

    def __nonzero__(self):
        return bool(self._header or len(self))

    def __len__(self):
        return sum(1 for item in self)


class _WithSettings(object):
    _setters = {}
    _aliases = {}

    def get_setter(self, name):
        if name[-1:] == ':':
            name = name[:-1]
        setter = self._get_setter(name)
        if setter is not None:
            return setter
        setter = self._get_deprecated_setter(name)
        if setter is not None:
            return setter
        self.report_invalid_syntax("Non-existing setting '%s'." % name)
        return None

    def _get_setter(self, name):
        title = name.title()
        if title in self._aliases:
            title = self._aliases[name]
        if title in self._setters:
            return self._setters[title](self)
        return None

    def _get_deprecated_setter(self, name):
        normalized = normalize(name)
        for setting in list(self._setters) + list(self._aliases):
            if normalize(setting) == normalized:
                self._report_deprecated_setting(name, setting)
                return self._get_setter(setting)
        return None

    def _report_deprecated_setting(self, deprecated, correct):
        self.report_invalid_syntax(
            "Setting '%s' is deprecated. Use '%s' instead."
            % (deprecated, correct), level='WARN'
        )

    def report_invalid_syntax(self, message, level='ERROR'):
        raise NotImplementedError


class _SettingTable(_Table, _WithSettings):
    type = 'setting'

    def __init__(self, parent):
        _Table.__init__(self, parent)
        self.doc = Documentation('Documentation', self)
        self.suite_setup = Fixture('Suite Setup', self)
        self.suite_teardown = Fixture('Suite Teardown', self)
        self.test_setup = Fixture('Test Setup', self)
        self.test_teardown = Fixture('Test Teardown', self)
        self.force_tags = Tags('Force Tags', self)
        self.default_tags = Tags('Default Tags', self)
        self.test_template = Template('Test Template', self)
        self.test_timeout = Timeout('Test Timeout', self)
        self.metadata = MetadataList(self)
        self.imports = ImportList(self)

    @property
    def _old_header_matcher(self):
        return OldStyleSettingAndVariableTableHeaderMatcher()

    def add_metadata(self, name, value='', comment=None):
        self.metadata.add(Metadata(self, name, value, comment))
        return self.metadata[-1]

    def add_library(self, name, args=None, comment=None):
        self.imports.add(Library(self, name, args, comment=comment))
        return self.imports[-1]

    def add_resource(self, name, invalid_args=None, comment=None):
        self.imports.add(Resource(self, name, invalid_args, comment=comment))
        return self.imports[-1]

    def add_variables(self, name, args=None, comment=None):
        self.imports.add(Variables(self, name, args, comment=comment))
        return self.imports[-1]

    def __len__(self):
        return sum(1 for setting in self if setting.is_set())


class TestCaseFileSettingTable(_SettingTable):
    __test__ = False
    _setters = {'Documentation': lambda s: s.doc.populate,
                'Suite Setup': lambda s: s.suite_setup.populate,
                'Suite Teardown': lambda s: s.suite_teardown.populate,
                'Test Setup': lambda s: s.test_setup.populate,
                'Test Teardown': lambda s: s.test_teardown.populate,
                'Force Tags': lambda s: s.force_tags.populate,
                'Default Tags': lambda s: s.default_tags.populate,
                'Test Template': lambda s: s.test_template.populate,
                'Test Timeout': lambda s: s.test_timeout.populate,
                'Library': lambda s: s.imports.populate_library,
                'Resource': lambda s: s.imports.populate_resource,
                'Variables': lambda s: s.imports.populate_variables,
                'Metadata': lambda s: s.metadata.populate}
    _aliases = {'Task Setup': 'Test Setup',
                'Task Teardown': 'Test Teardown',
                'Task Template': 'Test Template',
                'Task Timeout': 'Test Timeout'}

    def __iter__(self):
        for setting in [self.doc, self.suite_setup, self.suite_teardown,
                        self.test_setup, self.test_teardown, self.force_tags,
                        self.default_tags, self.test_template, self.test_timeout] \
                        + self.metadata.data + self.imports.data:
            yield setting


class ResourceFileSettingTable(_SettingTable):
    _setters = {'Documentation': lambda s: s.doc.populate,
                'Library': lambda s: s.imports.populate_library,
                'Resource': lambda s: s.imports.populate_resource,
                'Variables': lambda s: s.imports.populate_variables}

    def __iter__(self):
        for setting in [self.doc] + self.imports.data:
            yield setting


class InitFileSettingTable(_SettingTable):
    _setters = {'Documentation': lambda s: s.doc.populate,
                'Suite Setup': lambda s: s.suite_setup.populate,
                'Suite Teardown': lambda s: s.suite_teardown.populate,
                'Test Setup': lambda s: s.test_setup.populate,
                'Test Teardown': lambda s: s.test_teardown.populate,
                'Test Timeout': lambda s: s.test_timeout.populate,
                'Force Tags': lambda s: s.force_tags.populate,
                'Library': lambda s: s.imports.populate_library,
                'Resource': lambda s: s.imports.populate_resource,
                'Variables': lambda s: s.imports.populate_variables,
                'Metadata': lambda s: s.metadata.populate}

    def __iter__(self):
        for setting in [self.doc, self.suite_setup, self.suite_teardown,
                        self.test_setup, self.test_teardown, self.force_tags,
                        self.test_timeout] + self.metadata.data + self.imports.data:
            yield setting


class VariableTable(_Table):
    type = 'variable'

    def __init__(self, parent):
        _Table.__init__(self, parent)
        self.variables = []

    @property
    def _old_header_matcher(self):
        return OldStyleSettingAndVariableTableHeaderMatcher()

    def add(self, name, value, comment=None):
        self.variables.append(Variable(self, name, value, comment))

    def __iter__(self):
        return iter(self.variables)


class TestCaseTable(_Table):
    __test__ = False
    type = 'test case'

    def __init__(self, parent):
        _Table.__init__(self, parent)
        self.tests = []

    def set_header(self, header):
        if self._header and header:
            self._validate_mode(self._header[0], header[0])
        _Table.set_header(self, header)

    def _validate_mode(self, name1, name2):
        tasks1 = normalize(name1) in ('task', 'tasks')
        tasks2 = normalize(name2) in ('task', 'tasks')
        if tasks1 is not tasks2:
            raise DataError('One file cannot have both tests and tasks.')

    @property
    def _old_header_matcher(self):
        return OldStyleTestAndKeywordTableHeaderMatcher()

    def add(self, name):
        self.tests.append(TestCase(self, name))
        return self.tests[-1]

    def __iter__(self):
        return iter(self.tests)

    def is_started(self):
        return bool(self._header)


class KeywordTable(_Table):
    type = 'keyword'

    def __init__(self, parent):
        _Table.__init__(self, parent)
        self.keywords = []

    @property
    def _old_header_matcher(self):
        return OldStyleTestAndKeywordTableHeaderMatcher()

    def add(self, name):
        self.keywords.append(UserKeyword(self, name))
        return self.keywords[-1]

    def __iter__(self):
        return iter(self.keywords)


@py2to3
class Variable(object):

    def __init__(self, parent, name, value, comment=None):
        self.parent = parent
        self.name = name.rstrip('= ')
        if name.startswith('$') and value == []:
            value = ''
        if is_string(value):
            value = [value]
        self.value = value
        self.comment = Comment(comment)

    def as_list(self):
        if self.has_data():
            return [self.name] + self.value + self.comment.as_list()
        return self.comment.as_list()

    def is_set(self):
        return True

    def is_for_loop(self):
        return False

    def has_data(self):
        return bool(self.name or ''.join(self.value))

    def __nonzero__(self):
        return self.has_data()

    def report_invalid_syntax(self, message, level='ERROR'):
        self.parent.report_invalid_syntax("Setting variable '%s' failed: %s"
                                          % (self.name, message), level)


class _WithSteps(object):

    def add_step(self, content, comment=None):
        # print(f"DEBUG: model.py Enter _WithSteps content={content[:]} comment={comment}")
        self.steps.append(Step(content, comment))
        return self.steps[-1]

    def copy(self, name):
        new = copy.deepcopy(self)
        new.name = name
        self._add_to_parent(new)
        return new


class TestCase(_WithSteps, _WithSettings):
    __test__ = False

    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.doc = Documentation('[Documentation]', self)
        self.template = Template('[Template]', self)
        self.tags = Tags('[Tags]', self)
        self.setup = Fixture('[Setup]', self)
        self.teardown = Fixture('[Teardown]', self)
        self.timeout = Timeout('[Timeout]', self)
        self.steps = []
        if name == '...':
            self.report_invalid_syntax(
                "Using '...' as test case name is deprecated. It will be "
                "considered line continuation in Robot Framework 3.2.",
                level='WARN'
            )

    _setters = {'Documentation': lambda s: s.doc.populate,
                'Template': lambda s: s.template.populate,
                'Setup': lambda s: s.setup.populate,
                'Teardown': lambda s: s.teardown.populate,
                'Tags': lambda s: s.tags.populate,
                'Timeout': lambda s: s.timeout.populate}

    @property
    def source(self):
        return self.parent.source

    @property
    def directory(self):
        return self.parent.directory

    def add_for_loop(self, declaration, comment=None):
        # DEBUG
        #self.steps.append(ForLoop(self, ['FOR'] + declaration, comment=comment))
        # print(f"DEBUG: Model add_for_loop init={['FOR'] + declaration} comment:{comment}")
        self.steps.append(Step(['FOR'] + declaration, comment))
        # : Model add_for_loop return steps:{self.steps[-1].as_list()} comment:{comment}")
        return self.steps[-1]

    def end_for_loop(self):
        loop, steps = self._find_last_empty_for_and_steps_after()
        if not loop:
            return False
        loop.steps.extend(steps)
        self.steps[-len(steps):] = []
        return True

    def _find_last_empty_for_and_steps_after(self):
        steps = []
        for step in reversed(self.steps):
            if isinstance(step, ForLoop):
                if not step.steps:
                    steps.reverse()
                    return step, steps
                break
            steps.append(step)
        return None, []

    def report_invalid_syntax(self, message, level='ERROR'):
        type_ = 'test case' if type(self) is TestCase else 'keyword'
        message = "Invalid syntax in %s '%s': %s" % (type_, self.name, message)
        self.parent.report_invalid_syntax(message, level)

    def _add_to_parent(self, test):
        self.parent.tests.append(test)

    @property
    def settings(self):
        return [self.doc, self.tags, self.setup, self.template, self.timeout,
                self.teardown]

    def __iter__(self):
        for element in [self.doc, self.tags, self.setup,
                        self.template, self.timeout] \
                        + self.steps + [self.teardown]:
            yield element


class UserKeyword(TestCase):

    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.doc = Documentation('[Documentation]', self)
        self.args = Arguments('[Arguments]', self)
        self.return_ = Return('[Return]', self)
        self.timeout = Timeout('[Timeout]', self)
        self.teardown = Fixture('[Teardown]', self)
        self.tags = Tags('[Tags]', self)
        self.steps = []
        if name == '...':
            self.report_invalid_syntax(
                "Using '...' as keyword name is deprecated. It will be "
                "considered line continuation in Robot Framework 3.2.",
                level='WARN'
            )

    _setters = {'Documentation': lambda s: s.doc.populate,
                'Arguments': lambda s: s.args.populate,
                'Return': lambda s: s.return_.populate,
                'Timeout': lambda s: s.timeout.populate,
                'Teardown': lambda s: s.teardown.populate,
                'Tags': lambda s: s.tags.populate}

    def _add_to_parent(self, test):
        self.parent.keywords.append(test)

    @property
    def settings(self):
        return [self.args, self.doc, self.tags, self.timeout, self.teardown, self.return_]

    def __iter__(self):
        for element in [self.args, self.doc, self.tags, self.timeout] \
                        + self.steps + [self.teardown, self.return_]:
            yield element


class ForLoop(_WithSteps):
    """The parsed representation of a for-loop.

    :param list declaration: The literal cell values that declare the loop
                             (excluding ":FOR").
    :param str comment: A comment, default None.
    :ivar str flavor: The value of the 'IN' item, uppercased.
                      Typically 'IN', 'IN RANGE', 'IN ZIP', or 'IN ENUMERATE'.
    :ivar list vars: Variables set per-iteration by this loop.
    :ivar list items: Loop values that come after the 'IN' item.
    :ivar str comment: A comment, or None.
    :ivar list steps: A list of steps in the loop.
    """
    flavors = {'IN', 'IN RANGE', 'IN ZIP', 'IN ENUMERATE'}
    normalized_flavors = NormalizedDict((f, f) for f in flavors)
    inner_kw_pos = None

    def __init__(self, parent, declaration, indentation=[], comment=None):
        self.parent = parent
        self.indent = indentation if isinstance(indentation, list) else [indentation]
        isize = idx = 0
        print(f"\nDEBUG: ForLoop init ENTER declaration={declaration[:]}")
        if declaration[0] == '':
            declaration.pop(0)
        for idx in range(0, len(declaration)):
            if declaration[idx] == '':
                if idx >= 0:
                    isize = self.increase_indent()
            else:
                self.first_kw = declaration[idx]
                break
        self.inner_kw_pos = idx
        print(f"\nDEBUG: ForLoop init indent {isize} self.inner_kw_pos={self.inner_kw_pos}\ndeclaration={declaration[:]}")
        # compensation for double FOR
        if declaration[self.inner_kw_pos+1] == declaration[self.inner_kw_pos] == 'FOR':
            declaration.pop(self.inner_kw_pos+1)
        self.flavor, index = self._get_flavor_and_index(declaration)
        self.vars = declaration[self.inner_kw_pos+1:index]
        self.items = declaration[index+1:]
        self.comment = Comment(comment)
        self.steps = []
        self.args = []

    def _get_flavor_and_index(self, declaration):
        for index, item in enumerate(declaration):
            if item in self.flavors:
                return item, index
            if item in self.normalized_flavors:
                correct = self.normalized_flavors[item]
                self._report_deprecated_flavor_syntax(item, correct)
                return correct, index
            if normalize(item).startswith('in'):
                return item.upper(), index
        return 'IN', len(declaration)

    def _report_deprecated_flavor_syntax(self, deprecated, correct):
        self.parent.report_invalid_syntax(
            "Using '%s' as a FOR loop separator is deprecated. "
            "Use '%s' instead." % (deprecated, correct), level='WARN'
        )

    def is_comment(self):
        return False

    def is_for_loop(self):
        return True

    def as_list(self, indent=True, include_comment=True):
        comments = self.comment.as_list() if include_comment else []
        # print(f"DEBUG: Model ForLoop as_list: indent={self.indent[:]} self.first_kw={self.first_kw}\n"
        #       f"{self.vars} + {self.flavor} + {self.items} + {comments}")
        return self.indent + [self.first_kw] + self.vars + [self.flavor] + self.items + comments

    def __iter__(self):
        return iter(self.steps)

    def is_set(self):
        return True

    def increase_indent(self):
        self.indent.append('')
        return len(self.indent)

    def decrease_indent(self):
        self.indent = self.indent[:-1] if len(self.indent) > 0 else []
        return len(self.indent)


class Step(object):

    inner_kw_pos = None
    name = None
    indent = []
    assign = []
    args = []
    comment = []
    normal_assign = None
    cells = []

    def __init__(self, content, comment=None):
        if isinstance(content, Step):
            size = len(content)
            self.cells = content.cells  # .as_list()
        elif isinstance(content, list):
            size = len(content)
            self.cells = content
        else:
            size = len(self.cells)  # size = len(self)
            # cells = self.as_list()
        if comment:
            if isinstance(comment, list):
                self.cells.extend(comment)
            elif isinstance(comment, str):
                self.cells.append(comment)
        index = self.first_non_empty_cell(content)  # Called first to set self.inner_kw_pos
        self.inner_kw_pos = index
        self.normal_assign = None
        self.assign = self._get_assign()  # self._get_assign(content)
        # print(f"DEBUG: RFLib Model enter init Step: 1st cell content={content} comment={comment} index={index}"
        #       f" assign={self.assign} self.normal_assign={self.normal_assign}")
        self.indent = []
        self.args = []
        self.name = None
        self.comment = Comment(comment)
        if index < 0:  # This is redundant because index is >= 0
            return
        for _ in range(0, index):
            self.indent.append('')
        # print(f"DEBUG: RFLib Model init Step: index={index} inner_kw_pos = {self.inner_kw_pos} indent={self.indent[:]} \ncontent {content}")
        self.args = content[index + 1:] if content and index <= len(content) - 1 else []
        # print(f"DEBUG: RFLib Model init Step: 1st cell len(content)={len(content)} index {index} indent={self.indent[:]}")  # 1st cell: {content[index]}")
        # TODO: Create setters for Step.name and Step.args, see stepcontrollers.py replace_keyword
        if index < len(content):
            self.name = content[index] if content else None
        else:
            self.name = None
        # if self.assign:
        #     print(f"DEBUG RFLib init Step: self.assign {self.assign}")

    @staticmethod
    def is_kind_of_comment(content):
        return content.lower() in ['comment', 'builtin.comment'] or content.startswith('#')

    def _get_assign(self):
        assign = []
        idx = 0
        positional = True
        cells = self.cells.copy()
        if cells and cells != ['']:
            index = self.inner_kw_pos  # DEBUG avoiding calling self.first_non_empty_cell(content)
            if index < len(cells) and is_var(cells[index].rstrip('=')):
                self.normal_assign = True
            if 0 <= index < len(cells) and self.is_kind_of_comment(cells[index]):  # Special case for commented content
                return []
                # print(f"DEBUG: RFLib Model _get_assign VAR NORMAL (index={index}) inner_kw_pos={self.inner_kw_pos} content={content[:]}")
            # first handle non FOR cases
            idx = 0
            try:
                if cells[self.inner_kw_pos] != 'FOR':
                    while idx < len(cells):
                        if is_var(cells[idx].rstrip('=')):
                            assign.append(cells.pop(idx))
                            # if idx < self.inner_kw_pos:
                            idx -= 1
                        else:
                            break
                        idx += 1
                    # print(f"DEBUG: RFLib Model _get_assign RETURN assign={assign} size of content={len(content)}")
                    return assign
            except IndexError:
                pass
            idx = index
            while idx < len(cells) and positional:
                if idx <= self.inner_kw_pos:
                    positional = True
                else:
                    positional = False
                if not positional and self.inner_kw_pos < idx <= self.inner_kw_pos + 3 < len(cells) and cells[self.inner_kw_pos] == 'FOR':
                    # print(f"DEBUG: RFLib Model _get_assign idx={idx} +1{self.inner_kw_pos + 1}:{idx+1} +2{self.inner_kw_pos + 2}:{idx+2}"
                    #      f"FOR content1={content[self.inner_kw_pos + 1]}"
                    #      f" content2={content[self.inner_kw_pos + 2]} size of content={len(content)}")
                    if idx + 2 < len(cells):  # idx < self.inner_kw_pos + 3 and
                        # print(f"DEBUG: RFLib Model _get_assign FOR idx={idx} second IN ENUMERATE"
                        #      f" content[idx + 1]={content[idx + 1]} content[idx + 2]={content[idx + 2]}")
                        if cells[idx + 1] == 'IN ENUMERATE' or cells[idx + 2] == 'IN ENUMERATE':
                            positional = True
                            self.normal_assign = False
                            # print(f"DEBUG: RFLib Model _get_assign FOR idx={idx} second IN ENUMERATE"
                            #      f" size of content={len(content)} VALUE={content[idx]}")
                    if idx == self.inner_kw_pos + 1:
                        positional = True
                        self.normal_assign = False
                        # print(f"DEBUG: RFLib Model _get_assign FOR idx={idx} first loop var")
                    # else:
                    #    positional = False
                if not positional and self.inner_kw_pos < idx <= self.inner_kw_pos + 1 < len(cells) and re_set_var.match(cells[self.inner_kw_pos]):
                    positional = True
                    self.normal_assign = False
                if is_var(cells[idx].rstrip('=')) and positional:  # and self.normal_assign:
                    assign.append(cells.pop(idx))
                    idx -= 1  # We need to recheck var in case of IN ENUMERATE
                idx += 1
        # print(f"DEBUG: RFLib Model _get_assign idx={idx} size of content={len(content)}")
        return assign

    def is_comment(self):
        return self.name.lower() == 'comment' or not (self.assign or self.name or self.args)

    def is_for_loop(self):
        # TODO: remove steps ForLoop: return self.name == 'FOR'
        return False

    def is_set(self):
        return True

    def as_list(self, indent=False, include_comment=True):
        """
        import inspect
        stack = inspect.stack()
        the_class = stack[1][0].f_locals["self"].__class__.__name__
        the_method = stack[1][0].f_code.co_name
        print("DEBUG: RFLib Model Step called by {}.{}()".format(the_class, the_method))
        """
        # print(f"DEBUG RFLib Model Step: as_list() ENTER assign={self.assign}\n"
        #       f"cells={self.cells[:]}")
        _ = include_comment
        if indent:
            return [''] + self.cells[:]
        return self.cells[:]

    def first_non_empty_cell(self, content=None):
        _ = content
        size = len(self.cells)
        index = 0
        while index < size and self.cells[index] == '':
            index += 1
        if 0 <= index < size:
            return index
        elif index - 1 > 0:
            return index - 1
        else:
            return 0

    def first_empty_cell(self):
        index = self.inner_kw_pos
        if index > 0:
            return index - 1
        return None

    def increase_indent(self):
        self.indent.append('')
        self.cells.insert(0, '')
        return len(self.indent)

    def decrease_indent(self):
        self.indent = self.indent[:-1] if len(self.indent) > 0 else []
        self.cells = self.cells[1:] if len(self.cells) >= 1 and self.cells[0] == '' else self.cells
        return len(self.indent)

    def add_step(self, content, comment=None):
        self.__init__(content, comment)
        return self

    def __len__(self):
        kw = [self.name] if self.name is not None and self.name[0] != '#' else []
        cells_len = len(self.cells)
        if self.name == 'FOR':
            seglen = len(self.indent) + len(kw) + len(self.args) + len(self.comment)
        else:
            seglen = len(self.indent) + len(self.assign) + len(kw) + len(self.args) + len(self.comment)
        # Compensation for args==comment
        if self.args and self.comment and self.args[-1] == self.comment.as_list()[-1]:
            seglen -= 1  # len(self.args[:-1])
        elif len(self.comment) > 1 and self.args == self.comment.as_list()[1:]:
            seglen -= len(self.comment)
        # Compensation for assign==kw
        if self.assign and kw and self.assign[0] == kw[0]:
            seglen -= len(self.assign)  # len assign because assign may also be in args
        # Compensation for kw==comment
        if kw and self.comment and kw == self.comment.as_list():
            seglen -= 1
        return cells_len


class OldStyleSettingAndVariableTableHeaderMatcher(object):

    def match(self, header):
        return all(value.lower() == 'value' for value in header[1:])


class OldStyleTestAndKeywordTableHeaderMatcher(object):

    def match(self, header):
        if header[1].lower() != 'action':
            return False
        for arg in header[2:]:
            if not arg.lower().startswith('arg'):
                return False
        return True
