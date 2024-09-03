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

from multiprocessing import shared_memory
from robotide.lib.robot.utils import is_string, unicode
from robotide.lib.compat.parsing.language import get_localized_setting

from .comments import Comment
from ..version import ALIAS_MARKER


class Setting(object):
    language = None

    def __init__(self, setting_name, parent=None, comment=None):
        self.parent = parent
        try:
            self.language = parent.language
            if not self.language:
                set_lang = shared_memory.ShareableList(name="language")
                self.language = [set_lang[0]]
        except (AttributeError, FileNotFoundError):
            self.language = ['en']
        # DEBUG Starts
        # from robotide.lib.robot.parsing.model import TestCaseFileSettingTable, InitFileSettingTable
        # if isinstance(parent, TestCaseFileSettingTable) or isinstance(parent, InitFileSettingTable):
        #     print(f"DEBUG: settings.py Setting __init__ BEFORE setting_name= {setting_name} "
        #           f"lang={self.language} parent has tasks={hasattr(parent, 'tasks')} parent type={type(parent)}")
        # DEBUG Ends
        self.setting_name = get_localized_setting(self.language, setting_name)
        self._set_initial_value()
        self._set_comment(comment)
        self._populated = False

    def _set_initial_value(self):
        self.value = []

    def _set_comment(self, comment):
        self.comment = Comment(comment)

    def reset(self):
        self.__init__(self.setting_name, self.parent)

    @property
    def source(self):
        return self.parent.source if self.parent is not None else None

    @property
    def directory(self):
        return self.parent.directory if self.parent is not None else None

    def populate(self, value, comment=None):
        """Mainly used at parsing time, later attributes can be set directly."""
        try:
            start_continuation = value[0].lstrip().startswith('\\n...') or value[0].lstrip().startswith('...')
        except IndexError:
            start_continuation = False
        if not self._populated or start_continuation:
            if start_continuation:
                value[0] = value[0].replace('...', '\\n').replace('\\n\\n', '\\n')
            self._populate(value)
            self._set_comment(comment)
            self._populated = True
            # print(f"DEBUG: settings.py populate new or continuation value={value} {comment=}")
            return
        if self._populated and not start_continuation:
            # DEBUG
            # print(f"DEBUG: settings.py populate at branch that would clear data value={value}")
            # self._populate(value)
            # self._set_comment(comment)
            # return
            # DEBUG END
            self._set_initial_value()
            self._set_comment(None)
            self.report_invalid_syntax("Setting '%s' used multiple times."
                                       % self.setting_name, 'ERROR')

    def _populate(self, value):
        # self.value.append(self._string_value(value))
        if value and isinstance(value, list):
            value = [x.strip() for x in value if x != '' and x != '...']  # Remove ... from list
        self.value = value

    def is_set(self):
        return bool(self.value)

    @staticmethod
    def is_for_loop():
        return False

    def report_invalid_syntax(self, message, level='ERROR'):
        self.parent.report_invalid_syntax(message, level)

    def _string_value(self, value):
        if value and isinstance(value, list):
            value = [x.strip() for x in value if x != '']
        return value.strip() if is_string(value) else ' '.join(value)

    def _concat_string_with_value(self, string, value):
        if string:
            return string.strip() + ' ' + self._string_value(value)
        return self._string_value(value)

    def as_list(self):
        return self._data_as_list() + self.comment.as_list()

    def _data_as_list(self):
        ret = [self.setting_name]
        if self.value:
            ret.extend(self.value)
        return ret

    def __nonzero__(self):
        return self.is_set()

    def __iter__(self):
        return iter(self.value or ())

    def __unicode__(self):
        return unicode(self.value or '')


class StringValueJoiner(object):

    def __init__(self, separator):
        self._separator = separator

    def join_string_with_value(self, string, value):
        if string:
            return string.strip() + self._separator + self.string_value(value)
        return self.string_value(value)

    def string_value(self, value):
        if is_string(value):
            return value.strip()
        if value and isinstance(value, list):
            value = [x.strip() for x in value if x != '']
        return self._separator.join(value)


class Documentation(Setting):

    def _set_initial_value(self):
        self.value = ''

    def _populate(self, value):
        self.value = self._concat_string_with_value(self.value, value)

    def _string_value(self, value):
        if value and isinstance(value, list):
            value = [x.strip() for x in value if x != '']
        return value.strip() if is_string(value) else ''.join(value)

    def _data_as_list(self):
        return [self.setting_name, self.value]


class Template(Setting):

    def _set_initial_value(self):
        self.value = None

    def _populate(self, value):
        self.value = self._concat_string_with_value(self.value, value)

    def is_set(self):
        return self.value is not None

    def is_active(self):
        return self.value and self.value.upper() != 'NONE'

    def _data_as_list(self):
        ret = [self.setting_name]
        if self.value:
            ret.append(self.value)
        return ret


class Fixture(Setting):

    # `keyword`, `is_comment` and `assign` make the API compatible with Step.

    @property
    def keyword(self):
        return self.name or ''

    @staticmethod
    def is_comment():
        return False

    def _set_initial_value(self):
        self.name = None
        self.args = []
        self.assign = ()

    def _populate(self, value):
        if value and isinstance(value, list):
            value = [x.strip() for x in value if x != '' and x != '...']  # Remove ... from list
        if not self.name:
            self.name = value[0] if value else ''
            value = value[1:]
        self.args.extend(value)

    def is_set(self):
        return self.name is not None

    def is_active(self):
        return self.name and self.name.upper() != 'NONE'

    def _data_as_list(self):
        ret = [self.setting_name]
        if self.name or self.args:
            ret.append(self.name or '')
        if self.args:
            ret.extend(self.args)
        return ret


class Timeout(Setting):

    def _set_initial_value(self):
        self.value = None
        self.message = ''

    def _populate(self, value):
        if value and isinstance(value, list):
            value = [x.strip() for x in value if x != '']
        if not self.value:
            self.value = value[0] if value else ''
            value = value[1:]
        self.message = self._concat_string_with_value(self.message, value)
        # DEBUG: Remove custom timeout message support in RF 3.2.
        if value and self.parent:
            self.parent.report_invalid_syntax(
                'Using custom timeout messages is deprecated since Robot '
                'Framework 3.0.1 and will be removed in future versions. '
                "Message that was used is '%s'." % self.message, level='WARN')

    def is_set(self):
        return self.value is not None

    def _data_as_list(self):
        ret = [self.setting_name]
        if self.value or self.message:
            ret.append(self.value or '')
        if self.message:
            ret.append(self.message)
        return ret


class Tags(Setting):

    def _set_initial_value(self):
        self.value = None

    def _populate(self, value):
        if value and isinstance(value, list):
            value = [x.strip() for x in value if x != '']
        self.value = (self.value or []) + value

    def is_set(self):
        return self.value is not None

    def __add__(self, other):
        if not isinstance(other, Tags):
            raise TypeError('Tags can only be added with tags')
        tags = Tags('Tags')
        tags.value = (self.value or []) + (other.value or [])
        return tags


class Arguments(Setting):
    pass


class Return(Setting):
    pass


class Metadata(Setting):
    setting_name = 'Metadata'

    def __init__(self, parent, name, value, comment=None, joined=False):
        self.parent = parent
        self.setting_name = get_localized_setting(parent.language, 'Metadata')
        Setting.__init__(self, setting_name=self.setting_name, parent=parent, comment=comment)
        if value and isinstance(value, list):
            value = [x.strip() for x in value if x != '']
        if not name.strip():
            if value and not value[1:]:
                value = value[0].split('  ')
                value = [x.strip() for x in value if x != '']
            name = value[0]
            value = value[1:]
        self.name = name
        joiner = StringValueJoiner('' if joined else ' ')
        self.value = joiner.join_string_with_value('', value)
        self._set_comment(comment)

    def reset(self):
        """ Just overriding """
        pass

    def is_set(self):
        return True

    def _data_as_list(self):
        return [self.setting_name, self.name, self.value]


class ImportSetting(Setting):
    setting_name = None

    def __init__(self, parent, name, args=None, alias=None, comment=None):
        self.parent = parent
        if parent:
            self.setting_name = get_localized_setting(parent.language, self.setting_name)
        else:
            self.setting_name = self.type
        self.name = name.strip()
        Setting.__init__(self, setting_name=self.setting_name, parent=parent, comment=comment)
        if args:
            self.args = [x.strip() for x in args if x != '']
        else:
            self.args = []
        self.alias = alias
        self._set_comment(comment)

    def reset(self):
        """ Just overriding """
        pass

    @property
    def type(self):
        return type(self).__name__

    def is_set(self):
        return True

    def _data_as_list(self):
        # Special case when only comment is set
        comment = self.comment.as_list()
        if not self.name:
            data = [] if len(comment) > 0 else ['\n']
            return data
        return [self.setting_name, self.name] + self.args

    def report_invalid_syntax(self, message, level='ERROR', parent=None):
        parent = parent or getattr(self, 'parent', None)
        if parent:
            parent.report_invalid_syntax(message, level)
        else:
            from robotide.lib.robot.api import logger
            logger.write(message, level)


class Library(ImportSetting):

    def __init__(self, parent, name, args=None, alias=None, comment=None):
        if args:
            args = [x.strip() for x in args if x != '']
        else:
            args = []
        if not name and args:
            name = args.pop(0)
        if args and not alias:
            args, alias = self._split_possible_alias(args)
        self.setting_name = get_localized_setting(parent.language, 'Library')
        # print(f"DEBUG: settings.py Library {self.setting_name=}")
        ImportSetting.__init__(self, parent, name, args, alias, comment)

    @staticmethod
    def _split_possible_alias(args):
        if len(args) > 1 and (args[-2] == ALIAS_MARKER or args[-2] == 'WITH NAME'):
            return args[:-2], args[-1]
        return args, None

    def _data_as_list(self):
        # Special case when only comment is set
        comment = self.comment.as_list()
        if not self.name:
            data = [] if len(comment) > 0 else ['\n']
            return data
        data = [self.setting_name, self.name] + self.args
        if self.alias:
            data += [ALIAS_MARKER, self.alias]
        return data


class Resource(ImportSetting):

    def __init__(self, parent, name, invalid_args=None, comment=None):
        if invalid_args:
            name += ' ' + ' '.join(invalid_args)
        try:
            self.setting_name = get_localized_setting(parent.language, 'Resource')
        except AttributeError:  # Unit tests were failing here
            self.setting_name = get_localized_setting(None, 'Resource')
        # print(f"DEBUG: settings.py Resource {self.setting_name=}")
        ImportSetting.__init__(self, parent, name, comment=comment)


class Variables(ImportSetting):

    def __init__(self, parent, name, args=None, comment=None):
        # print(f"DEBUG: RFLib settings.py Variables __init__ {name=}, {args=}")
        if args and isinstance(args, list):
            args = [x.strip() for x in args if x != ''] or []
        if args and not name:
            name = args.pop(0)
        self.setting_name = get_localized_setting(parent.language, 'Variables')
        # print(f"DEBUG: settings.py Variables {self.setting_name=}")
        ImportSetting.__init__(self, parent, name, args, comment=comment)


class _DataList(object):

    def __init__(self, parent):
        self._parent = parent
        self.data = []

    def add(self, meta):
        self._add(meta)

    def _add(self, meta):
        self.data.append(meta)

    @staticmethod
    def _parse_name_and_value(value):
        if value:
            value = [x.strip() for x in value if x != '']
        else:
            return '', []  # The case when we just want the comment or empty row
        name = value[0] if value else ''
        return name, value[1:]

    def __getitem__(self, index):
        return self.data[index]

    def __setitem__(self, index, item):
        self.data[index] = item

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)


class ImportList(_DataList):

    def populate_library(self, data, comment):
        self._populate(Library, data, comment)

    def populate_resource(self, data, comment):
        self._populate(Resource, data, comment)

    def populate_variables(self, data, comment):
        self._populate(Variables, data, comment)

    def _populate(self, item_class, data, comment):
        name, value = self._parse_name_and_value(data)
        self._add(item_class(self._parent, name, value, comment=comment))


class MetadataList(_DataList):

    def populate(self, name, value, comment=''):
        self._add(Metadata(self._parent, name, value, comment, joined=True))
