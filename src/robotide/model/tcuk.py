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

import copy

from robotide.spec import VariableSpec

from datalist import RobotDataList
from keywords import Keyword, KeywordData
from settings import Setup, Teardown, Timeout, Tags, Arguments, ReturnValue,\
    Documentation


class _TcUkBase(object):
    doc = property(lambda self: self.settings.doc.get_str_value())

    def __init__(self, datafile, data=None, name=None):
        self.datafile = datafile
        self.name = name or data.name
        self.longname = self._get_longname()
        keywords = data and data.keywords or []
        self.keywords = KeywordList(datafile, keywords)

    def copy(self, name):
        ret = copy.deepcopy(self)
        ret.name = name
        self._mark_dirty()
        return ret

    def rename(self, new_name):
        self.name = new_name
        self.longname = self._get_longname()
        self._mark_dirty()

    def show_add_suite_dialog(self, tree):
        self.datafile.show_add_suite_dialog(tree)

    def content_assist_values(self):
        return self.datafile.content_assist_values()

    def get_own_keywords(self, *args):
        return []

    def _serialize(self, serializer):
        self.settings.serialize_before_kws(serializer)
        for kw in self.keywords:
            serializer.keyword(kw)
        self.settings.serialize_after_kws(serializer)

    def _get_longname(self):
        return '%s.%s' % (self.datafile.longname, self.name)

    def _mark_dirty(self):
        self.datafile.dirty = True


class TestCase(_TcUkBase):
    datalist = property(lambda self: self.datafile.tests)

    def __init__(self, datafile, data=None, name=None):
        _TcUkBase.__init__(self, datafile, data, name)
        self.settings = TestCaseSettings(datafile, data)

    def delete(self):
        self.datafile.tests.remove(self)
        self._mark_dirty()

    def serialize(self, serializer):
        serializer.start_testcase(self)
        self._serialize(serializer)
        serializer.end_testcase()


class UserKeyword(_TcUkBase):
    datalist = property(lambda self: self.datafile.keywords)

    def __init__(self, datafile, data=None, name=None):
        _TcUkBase.__init__(self, datafile, data, name)
        self.settings = UserKeywordSettings(datafile, data)
        self.source = datafile.name
        self.imports = datafile.imports

    shortdoc = property(lambda self: self.doc.split('\n')[0])

    def delete(self):
        self.datafile.keywords.remove(self)
        self._mark_dirty()

    def get_own_variables(self):
        return [ VariableSpec('<argument>', var) for var
                 in self.settings.get_args() ]

    def serialize(self, serializer):
        serializer.start_keyword(self)
        self._serialize(serializer)
        serializer.end_keyword()


class TestCaseSettings(object):

    def __init__(self, datafile, data):
        self.doc = Documentation(datafile, data)
        self.setup = Setup(datafile, data)
        self.teardown = Teardown(datafile, data)
        self.tags = Tags(datafile, data)
        self.timeout = Timeout(datafile, data)

    def serialize_before_kws(self, serializer):
        for setting in [self.doc, self.tags, self.timeout, self.setup]:
            setting.serialize(serializer)

    def serialize_after_kws(self, serializer):
        self.teardown.serialize(serializer)

    def __iter__(self):
        return iter([self.doc, self.setup, self.teardown, self.tags, self.timeout])


class UserKeywordSettings(object):

    def __init__(self, datafile, data):
        self.doc = Documentation(datafile, data)
        self.args = Arguments(datafile, data)
        self.timeout = Timeout(datafile, data)
        self.return_value = ReturnValue(datafile, data)

    def get_args(self):
        return self.args.value

    def serialize_before_kws(self, serializer):
        for setting in [self.args, self.doc, self.timeout]:
            setting.serialize(serializer)

    def serialize_after_kws(self, serializer):
        self.return_value.serialize(serializer)

    def __iter__(self):
        return iter([self.doc, self.args, self.timeout, self.return_value])


class KeywordList(RobotDataList):

    def _parse_data(self, kwdata):
        for kw in kwdata:
            kw = Keyword(kw)
            if isinstance(kw, list):
                self.extend(kw)
            else:
                self.append(kw)

    def parse_keywords_from_grid(self, griddata):
        self.__init__(self.datafile, [KeywordData(row) for row in griddata])

    def copy(self):
        copy = KeywordList(self.datafile)
        for item in self:
            copy.append(item)
        return copy
