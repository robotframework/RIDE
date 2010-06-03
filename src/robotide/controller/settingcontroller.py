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

    def set_value(self, value):
        if self._changed(value):
            self._set(value)
            self._mark_dirty()

    def _changed(self, value):
        return value != self._data.value

    def _set(self, value):
        self._data.value = value

    def _split_from_separators(self, value):
        return utils.split_value(value)

    def _mark_dirty(self):
        self._parent.mark_dirty()


class DocumentationController(_SettingController):
    editor = DocumentationEditor
    label = 'Documentation'

    def _init(self, doc):
        self._doc = doc

    @property
    def value(self):
        return self._doc.value


class FixtureController(_SettingController):
    editor = SettingEditor

    def _init(self, fixture):
        self._fixture = fixture

    @property
    def value(self):
        return ' | '.join([self._fixture.name or ''] + self._fixture.args or [])

    def _changed(self, value):
        name, args = self._parse(value)
        return self._fixture.name != name or self._fixture.args != args

    def _set(self, value):
        name, args = self._parse(value)
        self._fixture.name = name
        self._fixture.args = args

    def _parse(self, value):
        value = self._split_from_separators(value)
        return value[0] if value else '', value[1:] if value else []


class TagsController(_SettingController):
    editor = SettingEditor

    def _init(self, tags):
        self._tags = tags

    @property
    def value(self):
        return ' | '.join(self._tags.value or [])

    def _changed(self, value):
        return self._tags.value != self._split_from_separators(value)

    def _set(self, value):
        self._tags.value = self._split_from_separators(value) 


class TimeoutController(_SettingController):
    editor = SettingEditor

    def _init(self, timeout):
        self._timeout = timeout

    @property
    def value(self):
        value, msg = self._timeout.value, self._timeout.message
        if not value:
            return ''
        return value if not msg else value + ' | ' + msg

    def _changed(self, value):
        val, msg = self._parse(value)
        return self._timeout.value != val or self._timeout.message != msg

    def _set(self, value):
        value, message = self._parse(value)
        self._timeout.value = value
        self._timeout.message = message

    def _parse(self, value):
        parts = value.split('|', 1)
        val = parts[0].strip() if parts else ''
        msg = parts[1].strip() if len(parts) == 2 else ''
        return val, msg



class TemplateController(_SettingController):
    editor = SettingEditor

    def _init(self, template):
        self._template = template

    @property
    def value(self):
        return self._template.value or ''


class ArgumentsController(_SettingController):
    editor = SettingEditor

    def _init(self, args):
        self._args = args

    @property
    def value(self):
        return ' | '.join(self._args.value or [])

    def _changed(self, value):
        return self._args.value != self._split_from_separators(value)

    def _set(self, value):
        self._args.value = self._split_from_separators(value)
