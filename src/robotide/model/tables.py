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

from robotide import utils
from robotide.robotapi import RobotVariables

from metadata import Metadata
from importsettings import ImportSettings
from tcuk import TestCase, UserKeyword
from settings import Documentation, SuiteSetup, SuiteTeardown, TestSetup,\
    TestTeardown, ForceTags, DefaultTags, TestTimeout


class ResourceSettingTable(object):
    
    def __init__(self, resource, data):
        self.doc = Documentation(data)
        self.imports = ImportSettings(resource, data.imports)

    def serialize(self, serializer):
        serializer.start_settings()
        for setting in self:
            setting.serialize(serializer)
        if hasattr(self, 'metadata'):
            self.metadata.serialize(serializer)
        self.imports.serialize(serializer)
        serializer.end_settings()

    def __iter__(self):
        return iter([self.doc])


class InitFileSettingTable(ResourceSettingTable):

    def __init__(self, suite, data):
        self.doc = Documentation(data)
        self.suite_setup = SuiteSetup(data)
        self.suite_teardown = SuiteTeardown(data)
        self.force_tags = ForceTags(data)
        self.metadata = Metadata(suite, data.metadata)
        self.imports = ImportSettings(suite, data.imports)

    def __iter__(self):
        return iter([self.doc, self.suite_setup, self.suite_teardown, self.force_tags])


class SuiteSettingTable(InitFileSettingTable):

    def __init__(self, suite, data):
        InitFileSettingTable.__init__(self, suite, data)
        self.test_setup = TestSetup(data)
        self.test_teardown = TestTeardown(data)
        self.default_tags = DefaultTags(data)
        self.test_timeout = TestTimeout(data)

    def __iter__(self):
        return iter([self.doc, self.suite_setup, self.suite_teardown,
                     self.test_setup, self.test_teardown,
                     self.force_tags, self.default_tags, self.test_timeout])


class VariableTable(object):

    def __init__(self, datafile, data=[]):
        self.datafile = datafile
        self._order = []
        self._vars = RobotVariables()
        data = self._escape_variable_values(data)
        self._vars.set_from_variable_table(data)
        for var in data:
            self._order.append(self._remove_possible_equal_sign(var.name))

    def __iter__(self):
        return self._order.__iter__()

    def __len__(self):
        return len(self._order)

    def _escape_variable_values(self, data):
        for item in data:
            item.value = [ elem.replace('\\', '\\\\').replace('$', '\\$')\
                           .replace('@', '\\@').replace('%', '\\%')
                           for elem in item.value ]
        return data

    def _remove_possible_equal_sign(self, name):
        """Parsed data may have '=' at the end of a variable name"""
        return name.rstrip('=').strip()

    def swap(self, index1, index2):
        self._order[index1], self._order[index2] = self._order[index2], self._order[index1]
        
    def value_as_string(self, name):
        value = self._vars[name]
        if isinstance(value, basestring):
            return value
        return ' | '.join(value)

    def replace_scalar(self, value):
        return self._vars.replace_string(value, ignore_errors=True)

    def replace_list(self, values):
        try:
            return self._vars.replace_list(values)
        except:
            return values

    def new_scalar_var(self, name=None, value=None):
        self._create_var(name, value, '${}')

    def new_list_var(self, name=None, value=None):
        self._create_var(name, utils.split_value(value), '@{}')
    
    def _create_var(self, name, value, default_name):
        name = name is not None and name or default_name
        self._vars[name] = value
        self._order.append(name)
        self.datafile.dirty = True

    def pop(self, index):
        del self._vars[utils.normalize(self._order[index], ignore=['_'])]
        self._order.pop(index)
        self.datafile.dirty = True

    def get_name_and_value(self, index):
        key = self._order[index]
        return key, self._format_value(self._vars[key])

    def _format_value(self, value):
        if isinstance(value, basestring):
            return value
        return utils.join_value(value)

    def set_name_and_value(self, index, name, value):
        name = self._remove_possible_equal_sign(name)
        key = self._order[index]
        if key != name:
            del self._vars[utils.normalize(key, ignore=['_'])]
            self._order[index] = name
        if name.startswith('@{'):
            value = utils.split_value(value)
        self._vars[name] = value
        self.datafile.dirty = True

    def serialize(self, serializer):
        if len(self) == 0:
            return
        serializer.start_variables()
        for key in self._order: 
            value = self._vars[key]
            if isinstance(value, basestring):
                value = [value]
            serializer.variable(key, value)
        serializer.end_variables()


class _TcUkTable(utils.RobotDataList):
    _error_msg_duplicate_name = '%s with this name already exists'

    def new_item(self, name):
        item = self._item_class(self.datafile, name=name)
        self.append(item)
        return item

    def validate_name(self, name):
        for item in self:
            if utils.eq(item.name, name):
                return self._error_msg_duplicate_name % self._item_name
        return None

    def copy(self, orig, name):
        item = orig.copy(name)
        self.append(item)
        return item

    def get_item(self, longname):
        for item in self:
            if item.longname == longname:
                return item
        return None

    def _parse_data(self, data):
        for item in data:
            self.append(self._item_class(self.datafile, item))


class TestCaseTable(_TcUkTable):
    _item_class = TestCase
    _item_name = 'Test Case'

    def new_test(self, name):
        return _TcUkTable.new_item(self, name)

    def get_test(self, longname):
        return _TcUkTable.get_item(self, longname)

    def serialize(self, serializer):
        serializer.start_testcases()
        for test in self: 
            test.serialize(serializer)
        serializer.end_testcases()


class UserKeywordTable(_TcUkTable):
    _item_class = UserKeyword
    _item_name = 'User Keyword'

    def new_keyword(self, name):
        return _TcUkTable.new_item(self, name)

    def get_keyword(self, longname):
        return _TcUkTable.get_item(self, longname)

    def serialize(self, serializer):
        if len(self) == 0:
            return
        serializer.start_keywords()
        for kw in self:
            kw.serialize(serializer)
        serializer.end_keywords()
