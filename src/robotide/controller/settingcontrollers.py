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

import re
import sys
from itertools import chain

from robotide.publish.messages import RideImportSettingChanged,\
    RideImportSettingRemoved, RideVariableUpdated, RideItemSettingsChanged, \
    RideImportSettingAdded
from robotide import robotapi, utils
from .tags import Tag, ForcedTag, DefaultTag
from .basecontroller import ControllerWithParent
from robotide.utils import PY2, PY3, overrides, variablematcher
if PY3:
    from robotide.utils import basestring, unicode


class _SettingController(ControllerWithParent):
    def __init__(self, parent_controller, data):
        self._parent = parent_controller
        self._data = data
        self.label = self._label(self._data)
        self._init(self._data)

    def _label(self, data):
        label = data.setting_name
        if label.startswith('['):
            return label[1:-1]
        return label

    @property
    def _value(self):
        return [v.replace('|', '\\|') for v in self.as_list()[1:]]

    @property
    def value(self):
        value = self._value
        if self._data.comment:
            value.pop()
        return ' | '.join(value)

    @property
    def display_value(self):
        return ' | ' .join(self._value)

    def as_list(self):
        return self._data.as_list()

    @property
    def comment(self):
        return self._data.comment

    @property
    def keyword_name(self):
        return ''

    def contains_keyword(self, name):
        if PY2:
            istring = isinstance(name, basestring) or isinstance(name, unicode)
        elif PY3:
            istring = isinstance(name, basestring)
        matcher = name.match if not istring else lambda i: utils.eq(i, name)
        return self._contains_keyword(matcher)

    def _contains_keyword(self, matcher_function):
        return any(matcher_function(item or '') for item in self.as_list())

    def contains_variable(self, name):
        return variablematcher.value_contains_variable(self.value, name)

    @property
    def is_set(self):
        return self._data.is_set()

    def set_from(self, other):
        if other.is_set:
            self.set_value(other.value)
        self.set_comment(other.comment)

    def set_value(self, value):
        if self._changed(value):
            self._set(value)
            self.mark_dirty()
            RideItemSettingsChanged(item=self._parent).publish()

    def set_comment(self, comment):
        if comment != self.comment:
            if not isinstance(comment, robotapi.Comment):
                comment = robotapi.Comment(comment)
            self._data.comment = comment
            self.mark_dirty()

    def notify_value_changed(self):
        self._parent.notify_settings_changed()

    def clear(self):
        self._data.reset()
        self.mark_dirty()

    def _changed(self, value):
        return value != self._data.value

    def _set(self, value):
        self._data.value = value

    def _split_from_separators(self, value):
        return utils.split_value(value)


class DocumentationController(_SettingController):
    newline_regexps = (re.compile(r'(\\+)r\\n'),
                       re.compile(r'(\\+)n'),
                       re.compile(r'(\\+)r'))

    def _init(self, doc):
        self._doc = doc

    @property
    def value(self):
        return self._doc.value

    @overrides(_SettingController)
    def contains_keyword(self, name):
        return False

    def _get_editable_value(self):
        return self._unescape_newlines_and_handle_escapes(self.value)

    def _set_editable_value(self, value):
        self.set_value(self._escape_newlines_and_leading_hash(value))

    editable_value = property(_get_editable_value, _set_editable_value)

    @property
    def visible_value(self):
        return utils.html_format(utils.unescape(self.value))

    def _unescape_newlines_and_handle_escapes(self, item):
        for regexp in self.newline_regexps:
            item = regexp.sub(self._newline_replacer, item)
        return item

    def _newline_replacer(self, match):
        blashes = len(match.group(1))
        if blashes % 2 == 1:
            return '\\' * (blashes - 1) + '\n'
        return match.group()

    def _escape_newlines_and_leading_hash(self, item):
        for newline in ('\r\n', '\n', '\r'):
            item = item.replace(newline, '\\n')
        if item.strip().startswith('#'):
            item = '\\' + item
        return item


class FixtureController(_SettingController):

    def _init(self, fixture):
        self._fixture = fixture

    @property
    def keyword_name(self):
        return self._fixture.name

    def replace_keyword(self, new_name, old_value=None):
        self._fixture.name = new_name
        self.mark_dirty()

    def _changed(self, value):
        name, args = self._parse(value)
        return self._fixture.name != name or self._fixture.args != args

    def _set(self, value):
        name, args = self._parse(value)
        self._fixture.name = name
        self._fixture.args = args

    def _parse(self, value):
        value = self._split_from_separators(value)
        return (value[0], value[1:]) if value else ('', [])


class TagsController(_SettingController):

    def _init(self, tags):
        self._tags = tags

    def empty_tag(self):
        return Tag(None, controller=self)

    def _changed(self, value):
        return self._tags.value != self._split_from_separators(value)

    def set_from(self, other):
        if other.is_set and other._tags.value is not None:
            self.set_value(other.value)
        self.set_comment(other.comment)

    def _set(self, value):
        self._tags.value = self._split_from_separators(value)

    def add(self, tag):
        if self._tags.value is None:
            self._tags.value = []
        tag.set_index(len(self._tags.value))
        self._tags.value.append(tag.name)

    def remove(self, tag):
        if tag in self._tags.value:
            self._tags.value.remove(tag)

    def __iter__(self):
        forced = self._parent.force_tags
        if self._tags.value is None:
            return chain(forced, self._parent.default_tags).__iter__()
        if len(self._tags.value) == 0:
            return chain(forced, [Tag('', controller=self)])
        own_tags = (Tag(t, index, self)
                    for index, t in enumerate(self._tags.value))
        return chain(forced, own_tags).__iter__()

    @property
    def is_set(self):
        return any(self)

    @property
    def display_value(self):
        return ' | ' .join(tag.name.replace('|', '\\|') for tag in self)


class DefaultTagsController(TagsController):

    def empty_tag(self):
        return DefaultTag(None, controller=self)

    def __iter__(self):
        if self._tags.value is None:
            return [].__iter__()
        return (DefaultTag(t, index, self)
                for index, t in enumerate(self._tags.value)).__iter__()


class ForceTagsController(TagsController):

    def empty_tag(self):
        return ForcedTag(None, controller=self)

    def __iter__(self):
        return self._recursive_gather_from(self.parent, []).__iter__()

    def __eq__(self, other):
        if self is other:
            return True
        if other is None:
            return False
        if not isinstance(other, self.__class__):
            return False
        return self._tags == other._tags

    def _recursive_gather_from(self, obj, result):
        if obj is None:
            return result
        force_tags = obj._setting_table.force_tags
        return self._recursive_gather_from(
            obj.parent,
            self._gather_from_data(force_tags, obj.force_tags) + result)

    def _gather_from_data(self, tags, parent):
        if tags.value is None:
            return []
        return [ForcedTag(t, index, parent)
                for index, t in enumerate(tags.value)]


class TimeoutController(_SettingController):

    def _init(self, timeout):
        self._timeout = timeout

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

    def _init(self, template):
        self._template = template

    def _set(self, value):
        _SettingController._set(self, value)
        self._parent.notify_steps_changed()

    def clear(self):
        _SettingController.clear(self)
        self._parent.notify_steps_changed()

    @property
    def keyword_name(self):
        return self._template.value

    def replace_keyword(self, new_name, old_name=None):
        self._template.value = new_name
        self.mark_dirty()


class ArgumentsController(_SettingController):

    def _init(self, args):
        self._args = args

    def _changed(self, value):
        return self._args.value != self._split_from_separators(value)

    def _set(self, value):
        self._args.value = self._split_from_separators(value)
        self._parent.notify_settings_changed()

    def clear(self):
        _SettingController.clear(self)
        self._parent.notify_settings_changed()


class ReturnValueController(_SettingController):

    def _init(self, return_):
        self._return = return_

    def _label(self, data):
        return 'Return Value'

    def _changed(self, value):
        return self._return.value != self._split_from_separators(value)

    def _set(self, value):
        self._return.value = self._split_from_separators(value)


class MetadataController(_SettingController):

    def _init(self, meta):
        self._meta = meta

    @property
    def name(self):
        return self._meta.name

    @property
    def value(self):
        return self._meta.value

    def set_value(self, name, value):
        self._meta.name = name
        self._meta.value = value
        self._parent.mark_dirty()


class VariableController(_SettingController):

    def _init(self, var):
        self._var = var

    def _label(self, data):
        return ''

    def __ne__(self, other):
        return not (self == other)

    @property
    def name(self):
        return self._var.name

    @property
    def value(self):
        return self._var.value

    @property
    def comment(self):
        return self._var.comment

    @property
    def data(self):
        return self._data

    @property
    def index(self):
        return self.parent.index(self)

    def set_value(self, name, value):
        if isinstance(value, basestring) or isinstance(value, unicode):
            value = [value]
        self._var.name = name
        self._var.value = value
        self._parent.mark_dirty()

    def has_data(self):
        return self._data.has_data()

    def delete(self):
        self._parent.remove_var(self)

    def notify_value_changed(self):
        RideVariableUpdated(item=self).publish()

    def notify_variable_added(self):
        self.parent.notify_variable_added(self)

    def validate_name(self, new_name):
        if variablematcher.is_scalar_variable(self.name):
            return self.parent.validate_scalar_variable_name(new_name, self)
        if variablematcher.is_dict_variable(self.name):
            return self.parent.validate_dict_variable_name(new_name, self)
        return self.parent.validate_list_variable_name(new_name, self)

    def __eq__(self, other):
        if self is other:
            return True
        if other.__class__ != self.__class__:
            return False
        return self._var == other._var

    def __hash__(self):
        return hash(self._var) + 1


def ImportController(parent, import_):
    if import_.type == 'Resource':
        return ResourceImportController(parent, import_)
    elif import_.type == 'Library':
        return LibraryImportController(parent, import_)
    return VariablesImportController(parent, import_)


class _ImportController(_SettingController):

    def _init(self, import_):
        self._import = import_
        self.type = self._import.type

    def _label(self, data):
        return data.type

    @property
    def name(self):
        return self._import.name

    @property
    def alias(self):
        return self._import.alias or ''

    @property
    def args(self):
        return self._import.args or []

    @property
    def display_value(self):
        value = self.args + (['WITH NAME', self.alias] if self.alias else [])
        return ' | '.join(value)

    @property
    def dirty(self):
        return self._parent.dirty

    def has_error(self):
        return False

    def get_imported_controller(self):
        return None

    def set_value(self, name, args=None, alias=''):
        self._import.name = name
        self._import.args = utils.split_value(args or [])
        self._import.alias = alias
        self._parent.mark_dirty()
        self.publish_edited()
        self.import_loaded_or_modified()
        return self

    def import_loaded_or_modified(self):
        self._parent.notify_imports_modified()
        if not self.is_resource:
            return
        self._parent.resource_import_modified(self.name)

    def remove(self):
        self.parent.remove_import_data(self._import)

    def publish_added(self):
        RideImportSettingAdded(
            datafile=self.datafile_controller,
            import_controller=self, type=self.type.lower()).publish()

    def publish_edited(self):
        RideImportSettingChanged(
            datafile=self.datafile_controller,
            import_controller=self, type=self.type.lower()).publish()

    def publish_removed(self):
        RideImportSettingRemoved(datafile=self.datafile_controller,
                                 import_controller=self,
                                 type=self.type.lower()).publish()


class ResourceImportController(_ImportController):
    is_resource = True
    _resolved_import = False
    _previous_imported_controller = None

    def set_value(self, name, args=None, alias=''):
        self._previous_imported_controller = self.get_imported_controller()
        self.unresolve()
        _ImportController.set_value(self, name, args, alias)

    def get_imported_controller(self):
        if not self._resolved_import:
            self._imported_resource_controller = \
                self.parent.resource_file_controller_factory.find_with_import(
                    self._import)
            if self._imported_resource_controller:
                self._imported_resource_controller.add_known_import(self)
            self._resolved_import = True
        return self._imported_resource_controller

    @overrides(_ImportController)
    def has_error(self):
        return self.get_imported_controller() is None

    @overrides(_ImportController)
    def publish_added(self):
        # Resolve the import <-> ResourceFileController link
        self.get_imported_controller()
        _ImportController.publish_added(self)

    @overrides(_ImportController)
    def publish_removed(self):
        self._previous_imported_controller = self.get_imported_controller()
        # Unresolve the import <-> ResourceFileController link
        self.unresolve()
        self._prevent_resolve()
        _ImportController.publish_removed(self)

    def _prevent_resolve(self):
        self._resolved_import = True
        self._imported_resource_controller = None

    def get_previous_imported_controller(self):
        return self._previous_imported_controller

    def unresolve(self):
        if self._resolved_import and self._imported_resource_controller:
            self._imported_resource_controller.remove_known_import(self)
        self._resolved_import = False

    def contains_filename(self, filename):
        return self.name.endswith(filename)

    def change_name(self, old_name, new_name):
        if self.contains_filename(old_name):
            self.set_value(self.name[:-len(old_name)] + new_name)
        else:
            # If original result has changed and this import relies on
            # variables, can't know if import is still resolved
            self.unresolve()

    def change_format(self, format):
        if self._has_format():
            self.set_value(utils.replace_extension(self.name, format))
        else:
            self.unresolve()

    def _has_format(self):
        parts = self.name.rsplit('.', 1)
        if len(parts) == 1:
            return False
        return parts[-1].lower() in ['html', 'txt', 'tsv', 'robot', 'resource']


class LibraryImportController(_ImportController):
    is_resource = False

    @overrides(_ImportController)
    def has_error(self):
        return not self.parent.parent.is_library_import_ok(self._data)


class VariablesImportController(_ImportController):
    is_resource = False

    @overrides(_ImportController)
    def has_error(self):
        return not self.parent.parent.is_variables_import_ok(self._data)
