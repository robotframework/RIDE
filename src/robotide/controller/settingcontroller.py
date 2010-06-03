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

from robotide.editor.editors import DocumentationEditor, SettingEditor
from robotide import utils


class MetadataController(object):
    def __init__(self, meta):
        self._meta = meta
        self.name = meta.name
        self.value = meta.value

class ImportController(object):
    def __init__(self, import_):
        self._import = import_
        self.type = self._import.type
        self.name = self._import.name
        self.args = self._import.args


class _SettingController(object):

    def __init__(self, parent_controller, data, label=None):
        self._parent = parent_controller
        self._data = data
        self.datafile = data.parent
        if label:
            self.label = label
        self._init(data)

    @property
    def is_set(self):
        return self._data.is_set()

    @property
    def dirty(self):
        return self._parent.dirty


class DocumentationController(_SettingController):
    editor = DocumentationEditor
    label = 'Documentation'

    def _init(self, doc):
        self._doc = doc

    @property
    def value(self):
        return self._doc.value

    def set_value(self, value):
        if value != self._doc.value:
            self._doc.value = value
            self._parent.mark_dirty()


class FixtureController(_SettingController):
    editor = SettingEditor

    def _init(self, fixture):
        self._fixture = fixture

    @property
    def value(self):
        return ' | '.join([self._fixture.name or ''] + self._fixture.args or [])

    def set_value(self, value):
        name, args = self._parse(value)
        if self._changed(name, args):
            self._fixture.name = name
            self._fixture.args = args
            self._parent.mark_dirty()

    def _parse(self, value):
        value = [v.strip() for v in utils.split_value(value)]
        return value[0] if value else '', value[1:] if value else []

    def _changed(self, name, args):
        return self._fixture.name != name or self._fixture.args != args


class TagsController(_SettingController):
    editor = SettingEditor

    def _init(self, tags):
        self._tags = tags

    @property
    def value(self):
        return ' | '.join(self._tags.value)

    def set_value(self, value):
        raise NotImplementedError()


class TimeoutController(_SettingController):
    editor = SettingEditor

    def _init(self, timeout):
        self._timeout = timeout

    @property
    def value(self):
        return ' | '.join([self._timeout.value, self._timeout.message])

    def set_value(self, value):
        raise NotImplementedError()


class TemplateController(_SettingController):
    editor = SettingEditor

    def _init(self, template):
        self._template = template

    @property
    def value(self):
        return self._template.value

    def set_value(self, value):
        raise NotImplementedError()


class ArgumentsController(_SettingController):
    editor = SettingEditor

    def _init(self, args):
        self._args = args

    @property
    def value(self):
        return ' | '.join(self._args.value)

    def set_value(self, value):
        raise NotImplementedError()
