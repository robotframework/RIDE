#  Copyright 2008-2015 Nokia Solutions and Networks
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

from robotide import utils


class ItemInfo(object):
    """Represents an object that can be displayed by content assistant."""

    def __init__(self, name, source, details):
        """Creates an item info.

        :Parameters:
          name
            Item name. Is shown in the first column of the content assist popup.
          source
            Item source. Is shown in the second column of the content assist popup.
          details
            Detailed information for item that is shown in the additional popup
            besides the list that contains content assist values. Will be
            displayed as HTML.
        """
        self.name = name
        self.source = source
        if details is not None:
            self.details = details
        self._priority = PRIORITIES.get(self.__class__, PRIORITIES[ItemInfo])

    @property
    def longname(self):
        return '%s.%s' % (self.source, self.name)

    def name_begins_with(self, prefix):
        return utils.normalize(self.name).startswith(prefix)

    def longname_begins_with(self, prefix):
        return utils.normalize(self.longname).startswith(prefix)

    def is_library_keyword(self):
        return False

    def is_user_keyword(self):
        return not self.is_library_keyword()

    def __cmp__(self, other):
        if self._priority == other._priority:
            name_cmp = cmp(self.name.upper(), other.name.upper())
            return name_cmp if name_cmp else cmp(self.source, other.source)
        return cmp(self._priority, other._priority)

    def __eq__(self, other):
        return not self.__cmp__(other) if isinstance(other, ItemInfo) else False

    def __hash__(self):
        return hash((self.name, self.source))


class VariableInfo(ItemInfo):

    def __init__(self, name, value, source):
        ItemInfo.__init__(self, name, self._source_name(source), None)
        self._original_source = source
        self._value = value

    def _source_name(self, source):
        return unicode(os.path.basename(source)) if source else ''

    @property
    def details(self):
        value = self._value
        if self.name.startswith('@'):
            if value is None:
                value = '[ ]'
        return ('<table>'
                '<tr><td><i>Name:</i></td><td>%s</td></tr>'
                '<tr><td><i>Source:</i></td><td>%s</td></tr>'
                '<tr><td valign=top><i>Value:</i></td><td>%s</td></tr>'
                '</table>') % (self.name, self._original_source, unicode(value))


class ArgumentInfo(VariableInfo):

    SOURCE = 'Argument'

    def __init__(self, name, value):
        VariableInfo.__init__(self, name, value, self.SOURCE)

class LocalVariableInfo(VariableInfo):

    SOURCE = 'Local variable'

    def __init__(self, name):
        VariableInfo.__init__(self, name, '', self.SOURCE)

class _KeywordInfo(ItemInfo):

    def __init__(self, item):
        self.doc = self._doc(item).strip()
        ItemInfo.__init__(self, self._name(item), self._source(item),
                          None)
        self.shortdoc = self.doc.splitlines()[0] if self.doc else ''
        self.item = item

    @property
    def arguments(self):
        return self._parse_args(self.item)

    @property
    def details(self):
        return ('<table>'
                '<tr><td><i>Name:</i></td><td>%s</td></tr>'
                '<tr><td><i>Source:</i></td><td>%s &lt;%s&gt;</td></tr>'
                '<tr><td><i>Arguments:</i></td><td>%s</td></tr>'
                '</table>'
                '<table>'
                '<tr><td>%s</td></tr>'
                '</table>') % \
                (self._name(self.item), self._source(self.item), self._type,
                 self._format_args(self.arguments),
                 utils.html_format(self.doc))

    def _format_args(self, args):
        return '[ %s ]' % ' | '.join(args)

    def __str__(self):
        return 'KeywordInfo[name: %s, source: %s, doc: %s]' %(self.name,
                                                              self.source,
                                                              self.doc)
    def _name(self, item):
        return item.name


class _XMLKeywordContent(_KeywordInfo):

    def __init__(self, item, source, source_type):
        self._type = source_type
        self._source = lambda x: source
        _KeywordInfo.__init__(self, item)
        self.args = self._format_args(self._parse_args(item))

    def with_alias(self, alias):
        if alias:
            self.source = alias
        return self

    def _name(self, node):
        return node.get('name')

    def _doc(self, node):
        return node.find('doc').text or ''

    def _parse_args(self, node):
        args_node = node.find('arguments')
        return [arg_node.text for arg_node in args_node.findall('arg')]

    def is_library_keyword(self):
        return True


class LibraryKeywordInfo(_KeywordInfo):
    _type = 'test library'
    _library_alias = None
    item = None

    def __init__(self, name, doc, library_name, args):
        self._item_name = name
        self.doc = doc.strip()
        self._item_library_name = library_name
        self._args = args
        ItemInfo.__init__(self, self._item_name, library_name, None)
        self.shortdoc = self.doc.splitlines()[0] if self.doc else ''

    def with_alias(self, alias):
        self._library_alias = alias
        self.source = self._source(self.item)
        return self

    def _source(self, item):
        if self._library_alias:
            return self._library_alias
        return self._item_library_name

    @property
    def arguments(self):
        return self._args

    def is_library_keyword(self):
        return True

    def _name(self, item):
        return self._item_name


class _UserKeywordInfo(_KeywordInfo):

    def _source(self, item):
        return unicode(os.path.basename(item.source)) if item.source else ''

    def _doc(self, item):
        return utils.unescape(item.doc.value)

    def _parse_args(self, uk):
        parsed = []
        for arg in uk.args.value:
            if self._is_scalar(arg):
                parsed.append(self._parse_name_and_default(arg))
            elif self._is_list(arg):
                parsed.append(self._parse_vararg(arg))
        return parsed

    def _is_scalar(self, arg):
        return arg.startswith('$')

    def _parse_name_and_default(self, arg):
        parts = arg.split('=', 1)
        name = self._strip_var_syntax_chars(parts[0])
        if len(parts) == 1:
            return name
        return name + '=' + parts[1]

    def _strip_var_syntax_chars(self, string):
        return string[2:-1]

    def _is_list(self, arg):
        return arg.startswith('@')

    def _parse_vararg(self, arg):
        return '*' + self._strip_var_syntax_chars(arg)


class TestCaseUserKeywordInfo(_UserKeywordInfo):
    _type = 'test case file'

    @property
    def longname(self):
        return self.name


class ResourceUserKeywordInfo(_UserKeywordInfo):
    _type = 'resource file'

    @property
    def longname(self):
        return self.item.parent.parent.name + '.' + self.name


PRIORITIES = {ItemInfo: 50,
              LibraryKeywordInfo: 40,
              ResourceUserKeywordInfo: 30,
              TestCaseUserKeywordInfo: 20,
              VariableInfo: 10,
              ArgumentInfo: 5,
              LocalVariableInfo: 5}
