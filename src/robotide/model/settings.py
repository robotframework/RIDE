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
from robotide.errors import DataError


class _Setting(object):
    _initial = []
    _serialized_name = property(lambda self: utils.name_from_class(self))
    _serialized_value = property(lambda self: self.value)

    def __init__(self, datafile, data=None):
        if data:
            self.value = self._get_value(data)
        else:
            self.value = self._initial
        self.datafile = datafile

    def serialize(self, serializer):
        if self.active():
            serializer.setting(self._serialized_name, self._serialized_value)

    def clear(self):
        self.value = self._initial

    def active(self):
        return self.value != self._initial

    def get_str_value(self):
        if self.value is None:
            return ''
        return utils.join_value(self.value)

    def set_str_value(self, value):
        self.value = [ v.strip() for v in utils.split_value(value) ]
        self.datafile.dirty = True


class Documentation(_Setting):
    _serialized_value = property(lambda self:
                                [self.get_str_value().replace('\n', '\\n\n')])

    def _get_value(self, data):
        if data.doc:
            return [data.doc.replace('\n ', '\n').replace('\\n', '\n')]
        return []

    def get_str_value(self):
        return ''.join(self.value)

    def set_str_value(self, doc):
        self.value = doc and [doc] or []
        self.datafile.dirty = True


class ForceTags(_Setting):

    def _get_value(self, data):
        return data.force_tags or []


class DefaultTags(_Setting):

    def _get_value(self, data):
        return data.default_tags or []


class Tags(_Setting):

    _initial = None

    def _get_value(self, data):
        return data.tags


class _Timeout(_Setting):

    def _get_timeout(self, timeout):
        if self._timeout_is_not_set(timeout):
            return self._initial
        if self._timeout_is_empty(timeout):
            return []
        try:
            seconds = utils.secs_to_timestr(utils.timestr_to_secs(timeout[0]))
        except DataError:
            seconds = timeout[0]
        message = ' '.join(timeout[1:])
        return message and [seconds, message] or [seconds]

    def _timeout_is_not_set(self, timeout):
        return timeout is None

    def _timeout_is_empty(self, timeout):
        return not (timeout and timeout[0] != '')


class TestTimeout(_Timeout):

    def _get_value(self, data):
        return self._get_timeout(data.test_timeout)


class Timeout(_Timeout):
    _initial = None

    def _get_value(self, data):
        # Parsed user keyword's timeout is [], even when it's not defined.
        if getattr(data, 'type', None) == 'user' and data.timeout == []:
            return None
        return self._get_timeout(data.timeout)


class _Fixture(_Setting):

    def _get_value(self, data):
        attr = utils.name_from_class(self).replace(' ', '_').lower()
        item = getattr(data, attr)
        if item is None:
            return self._initial
        return item

class SuiteSetup(_Fixture):
    pass

class SuiteTeardown(_Fixture):
    pass

class TestSetup(_Fixture):
    pass

class TestTeardown(_Fixture):
    pass

class Setup(_Fixture):
    _initial = None

class Teardown(_Fixture):
    _initial = None


class Arguments(_Setting):

    def _get_value(self, data):
        parsed = []
        if data.args:
            parsed.extend(list(data.args))
        if data.defaults:
            for i, value in enumerate(data.defaults):
                index = len(data.args) - len(data.defaults) + i
                parsed[index] = parsed[index] + '=' + value
        if data.varargs:
            parsed.append(data.varargs)
        return parsed


class ReturnValue(_Setting):
    _serialized_name = 'Return'

    def _get_value(self, data):
        return data.return_value


class _Import(_Setting):
    name = property(lambda self: self.value[0])
    args = property(lambda self: self.value[1:])

    def _get_value(self, data):
        return data


class ResourceImport(_Import):
    _serialized_name = 'Resource'

    def set_str_value(self, value):
        self.value = [value]
        self.datafile.dirty = True

class LibraryImport(_Import):
    _serialized_name = 'Library'

class VariablesImport(_Import):
    _serialized_name = 'Variables'
