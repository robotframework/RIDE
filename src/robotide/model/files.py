#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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
import operator
import copy

from robotide import utils
from robotide.spec import UserKeywordContent
from robotide.errors import NoRideError, DataError, SerializationError
from robotide.robotapi import TestSuiteData, ResourceFileData, InitFileData
from robotide.writer import FileWriter

from tables import InitFileSettingTable, SuiteSettingTable, ResourceSettingTable,\
    VariableTable, TestCaseTable, UserKeywordTable
from cache import LIBRARYCACHE, VARIABLEFILECACHE, RESOURCEFILECACHE
from tcuk import UserKeyword


def TestSuiteFactory(path):
    if not os.path.exists(path):
        if '__init__' in path:
            return _TestSuiteFactory(_EmptyInitFile(path))
        return _TestSuiteFactory(_EmptyTestSuite(path))
    if _is_empty_dir(path):
        return _TestSuiteFactory(_EmptyInitFile(path))
    if _is_empty_file(path):
        return _TestSuiteFactory(_EmptyTestSuite(path))
    return _TestSuiteFactory(TestSuiteData(path))

def _is_empty_dir(path):
    return os.path.isdir(path) and not os.listdir(path)

def _is_empty_file(path):
    return os.path.isfile(path) and os.path.getsize(path) == 0

def _TestSuiteFactory(data, parent=None):
    if hasattr(data, 'initfile'):
        return InitFile(data, parent)
    return TestCaseFile(data, parent)


def ResourceFileFactory(path, create_empty=True):
    if path and os.path.isfile(path):
        data = ResourceFileData(path)
    elif create_empty:
        data = _EmptyResourceFile(path)
    else:
        return None
    return ResourceFile(data)


class _AbstractDataFile(object):
    is_directory_suite = False

    def __init__(self, data):
        self.source = data.source.decode('UTF-8')
        self._stat = self._get_stat(self.source)
        self.variables = VariableTable(self, data.variables)
        self.keywords = UserKeywordTable(self, data.user_keywords)
        self.dirty = False
        self.suites = []

    def _get_stat(self, path):
        if os.path.isfile(path):
            stat = os.stat(path)
            return (stat.st_mtime, stat.st_size) 
        return (0, 0)

    def get_resources(self):
        resources = []
        for name in self.get_resource_imports():
            #TODO: Extract variable resolving
            name = self.variables.replace_scalar(name)
            for res in resources:
                name = res.variables.replace_scalar(name)
            resource = RESOURCEFILECACHE.get_resource_file(self.source, name)
            if resource:
                resources.append(resource)
        return resources

    def set_dirty(self):
        self.dirty = True

    def get_user_keyword(self, name):
        kws = self._filter(self.keywords + self.get_user_keywords(), name)
        return kws and kws[0] or None 

    def get_user_keywords(self):
        kws = copy.copy(self.keywords)
        for res in self.get_resources():
            kws.extend(res.get_user_keywords())
        return kws

    def get_keywords(self, library_keywords=True):
        kws = self._get_own_keywords() + self._get_resource_keywords(library_keywords) 
        if library_keywords:
            kws += self._get_library_keywords()
        return kws

    def get_keywords_for_content_assist(self, relative=True, name=None):
        own_kws = self._get_own_keywords(relative=relative) 
        resource_keywords = []
        for res in self.get_resources():
            resource_keywords.extend(res.get_keywords_for_content_assist(relative=False))
        kws = own_kws + self._get_library_keywords() + resource_keywords
        kws = self._remove_duplicates(self._filter(kws, name))
        kws.sort(key=operator.attrgetter('name'))
        return kws

    def _get_own_keywords(self, relative=False):
        source = relative and '<this file>' or self.name
        return [ UserKeywordContent(kw, source, self.type) for kw in self.keywords ]

    def _filter(self, keywords, name):
        if name is not None:
            keywords = [ kw for kw in keywords if utils.eq(kw.name, name) or
                                                  utils.eq(kw.longname, name) ]
        return keywords

    def _remove_duplicates(self, keywords):
        filtered = {}
        for kw in keywords:
            if kw.name not in filtered:
                filtered[kw.name] = kw
        return filtered.values()

    def _get_library_keywords(self):
        keywords = []
        for lib_import in self.get_library_imports():
            name = self.replace_variables(lib_import.name)
            keywords.extend(LIBRARYCACHE.get_library_keywords(name, lib_import.args))
        keywords.extend(LIBRARYCACHE.get_default_keywords())
        return keywords

    def _get_resource_keywords(self, library_keywords=True):
        keywords = []
        for resource in self.get_resources():
            keywords.extend(resource.get_keywords(library_keywords=library_keywords))
        return keywords

    def replace_variables(self, value):
        value = self.variables.replace_scalar(value)
        for res in self.get_resources():
            value = res.replace_variables(value)
        for vars in self._get_variable_files():
            try:
                value = vars.replace_scalar(value)
            except DataError:
                pass
        return value

    def get_variables(self):
        return [ _VariableSpec(self.name, var) for var in self.variables ] + \
                self._get_resource_variables() + self._get_variable_file_variables()

    def validate_keyword_name(self, value):
        return self.keywords.validate_name(value)

    def _get_resource_variables(self):
        vars = []
        for resource in self.get_resources():
            vars.extend(resource.get_variables())
        return vars

    def _get_variable_file_variables(self):
        vars = []
        for varfile in self._get_variable_files():
            vars.extend([_VariableSpec(varfile.source, var) for var in varfile.keys()])
        return vars

    def _get_variable_files(self):
        varfiles = []
        for var_settings in self.get_variable_imports():
            # TODO: There is need for namespace object which could be used for 
            # all variable replacing
            name = self.variables.replace_scalar(var_settings.name)
            args = self.variables.replace_list(var_settings.args)
            varfile = VARIABLEFILECACHE.get_varfile(self.source, name, args)
            if varfile:
                varfiles.append(varfile)
        return varfiles

    def get_resource_imports(self):
        return self.settings.imports.get_resource_imports() 

    def get_library_imports(self):
        return self.settings.imports.get_library_imports()

    def get_variable_imports(self):
        return self.settings.imports.get_variable_imports()

    def get_datafile(self):
        return self

    def has_been_modified_on_disk(self):
        return self._get_stat(self.source) != self._stat

    def new_keyword(self, name):
        self.dirty = True
        return self.keywords.new_keyword(name)

    def add_test_or_user_keyword(self, item):
        item.longname = '%s.%s' %(self.longname, item.name)
        item.datafile = self
        if isinstance(item, UserKeyword):
            self.keywords.append(item)
        else:
            self.tests.append(item)
        self.dirty = True

    def has_format(self):
        return True

    def get_format(self):
        format = os.path.splitext(self.source)[1][1:].upper()
        if format in ['HTML', 'HTM', 'XHTML']:
            return 'HTML'
        return format

    def serialize(self, force=False, format=None, recursive=False):
        if recursive:
            for s in self.suites:
                s.serialize(force, format, recursive)
        old_source = self._change_format_if_needed(format)
        if not (self.dirty or force):
            return
        self._validate_serialization()
        try:
            self._serialize(FileWriter(self.source))
        except EnvironmentError, e:
            raise SerializationError(e.strerror)
        self._stat = self._get_stat(self.source)
        self.dirty = False
        if old_source and os.path.isfile(old_source):
            os.remove(old_source)

    def _change_format_if_needed(self, format):
        if format in [None, self.get_format()]:
            return None
        old = self.source
        self.source = '%s.%s' % (os.path.splitext(old)[0], format.lower())
        self.dirty = True
        return old

    def _validate_serialization(self):
        pass

    def _serialize(self, serializer):
        self.settings.serialize(serializer)
        self.variables.serialize(serializer)
        self._serialize_tests(serializer)
        self.keywords.serialize(serializer)
        serializer.close()

    def _serialize_tests(self, serializer):
        pass


class _TestSuite(_AbstractDataFile):
    type = 'test suite'

    def __init__(self, data, parent=None):
        self._check_ride_suitability(data)
        self.name = data.name.decode('UTF-8')
        self.longname = parent and '%s.%s' % (parent.longname, self.name) or self.name
        _AbstractDataFile.__init__(self, data)
        self._parent = parent
        self.tests = TestCaseTable(self, data.tests)
        self.suites = [ _TestSuiteFactory(suite, self)
                        for suite in data.suites ]

    def _check_ride_suitability(self, data):
        for meta in data.metadata:
            if meta.lower() == 'no ride':
                raise NoRideError("Test data file '%s' is not supposed to be "
                                  "edited with RIDE." % data.source)

    def set_source(self, path, parent=False):
        """Used to set new source when Save As is used."""
        self.dirty = True
        self._set_source(path, parent)

    def add_suite(self, path):
        if not os.path.exists(os.path.dirname(path)):
            os.mkdir(os.path.dirname(path))
        suite = TestSuiteFactory(path)
        self.suites.append(suite)
        return suite

    def get_test_or_user_keyword(self, longname):
        test = self.tests.get_test(longname)
        return test or self.keywords.get_keyword(longname)

    def get_dir_path(self):
        if os.path.isfile(self.source):
            return os.path.dirname(self.source)
        return self.source


class TestCaseFile(_TestSuite):

    def __init__(self, data, parent=None):
        self.settings = SuiteSettingTable(self, data)
        _TestSuite.__init__(self, data, parent)

    def new_test(self, name):
        self.dirty = True
        return self.tests.new_test(name)

    def validate_test_name(self, value):
        return self.tests.validate_name(value)

    def get_directory_suite(self):
        return self._parent

    def reload_from_disk(self):
        self.__init__(TestSuiteData(self.source))

    def _set_source(self, path, parent):
        if not parent:
            self.source = path
            self.name = utils.printable_name_from_path(self.source)
        else:
            self.source = os.path.join(path, os.path.basename(self.source))

    def _validate_serialization(self):
        if not self.tests:
            raise SerializationError('File suite contains no test cases and '
                                     'cannot be properly serialized.')

    def _serialize_tests(self, serializer):
        self.tests.serialize(serializer)


class InitFile(_TestSuite):
    is_directory_suite = True

    def __init__(self, data, parent=None):
        self.settings = InitFileSettingTable(self, data)
        _TestSuite.__init__(self, data, parent)
        if data.initfile is not None:
            self.source = data.initfile
        else:
            self.source = os.path.join(data.source)
        self._stat = self._get_stat(self.source)

    def set_format(self, format):
        self.source = os.path.join(self.source, '__init__.' + format.lower())

    def has_format(self):
        return bool(os.path.splitext(self.source)[1])

    def get_directory_suite(self):
        return self

    def reload_from_disk(self):
        self.__init__(InitFileData(os.path.dirname(self.source)))

    def _set_source(self, path, parent):
        path = path.replace('__init__.html', '').replace('__init__.tsv', '')
        if parent:
            owndir = os.path.split(os.path.dirname(self.source))[1]
            path = os.path.join(path, owndir)
        os.mkdir(path)
        self.source = os.path.join(path, os.path.basename(self.source))
        self.name = utils.printable_name_from_path(path)
        for suite in self.suites:
            suite.set_source(path, parent=True)


class ResourceFile(_AbstractDataFile):
    type = 'resource file'

    def __init__(self, data):
        self.name = self.longname = os.path.basename(data.source)
        self.settings = ResourceSettingTable(self, data)
        _AbstractDataFile.__init__(self, data)

    def reload_from_disk(self):
        data = ResourceFileData(self.source)
        self.__init__(data)


class _EmptyResourceFile(object):

    def __init__(self, source):
        self.source = os.path.normpath(os.path.abspath(source))
        self.name = source is not None and utils.printable_name_from_path(source) or None
        self.doc = None
        self.imports = []
        self.variables = VariableTable(self, [])
        self.user_keywords = UserKeywordTable(self, [])


class _EmptyTestSuite(_EmptyResourceFile):

    def __init__(self, source):
        _EmptyResourceFile.__init__(self, source)
        self.force_tags = self.default_tags = self.suite_setup = self.test_setup = \
        self.suite_teardown = self.test_teardown = self.test_timeout = None
        self.metadata = {}
        self.suites = []
        self.tests = TestCaseTable(self, [])


class _EmptyInitFile(_EmptyTestSuite):

    def __init__(self, source):
        _EmptyTestSuite.__init__(self, source)
        self.name = self._get_name(self.source)
        self.initfile = self.source

    def _get_name(self, source):
        if '__init__' in self.source:
            source = os.path.split(self.source)[0]
        return utils.printable_name_from_path(source)


class _VariableSpec(object):

    def __init__(self, parent, name):
        self.parent = parent
        self.name = name

    def get_details(self):
        return ''
