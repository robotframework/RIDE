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

from robotide.utils import html_escape, unescape


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
        self.details = details

    def __cmp__(self, other):
        return cmp(self.name, other.name)


class VariableInfo(ItemInfo):

    def __init__(self, name, value, source):
        ItemInfo.__init__(self, name, source, self._details(name, source, value))

    def _details(self, name, source, value):
        prefix = 'Source: %s<br><br>Value: ' % source
        if name.startswith('$'):
            return prefix  + unicode(value)
        return '%s [ %s ]' % (prefix, ' | '.join(value))


class _KeywordInfo(ItemInfo):

    def __init__(self, item):
        self.doc = self._parse_doc(item.doc).strip()
        ItemInfo.__init__(self, item.name, self._source(item),
                          self._details(item))
        self.shortdoc = self.doc.splitlines()[0] if self.doc else ''
        self.item = item

    def _details(self, item):
        return 'Source: %s &lt;%s&gt;<br><br>Arguments: %s<br><br>%s' % \
                (self._source(item), self._type,
                 self._format_args(self._parse_args(item)),
                 html_escape(self.doc, formatting=True))

    def _format_args(self, args):
        return '[ %s ]' % ' | '.join(args)

    def __str__(self):
        return 'KeywordInfo[name: %s, source: %s, doc: %s]' %(self.name,
                                                              self.source,
                                                              self.doc)

    def __cmp__(self, other):
        name_cmp = cmp(self.name, other.name)
        return name_cmp if name_cmp else cmp(self.source, other.source)

    def __eq__(self, other):
        return not self.__cmp__(other)

    def __hash__(self):
        return hash((self.name, self.source))


class LibraryKeywordInfo(_KeywordInfo):
    _type = 'test library'

    def _source(self, item):
        return item.library.name

    def _parse_doc(self, doc):
        return doc

    def _parse_args(self, handler):
        args = []
        handler_args = handler.arguments
        if handler_args.names:
            args.extend(list(handler_args.names))
        if handler_args.defaults:
            for i, value in enumerate(handler_args.defaults):
                index = len(handler_args.names) - len(handler_args.defaults) + i
                args[index] = args[index] + '=' + str(value)
        if handler_args.varargs:
            args.append('*%s' % handler_args.varargs)
        return args


class _UserKeywordInfo(_KeywordInfo):

    def _source(self, item):
        return os.path.basename(item.source) if item.source else ''

    def _parse_doc(self, doc):
        return unescape(doc.value)

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

class ResourceseUserKeywordInfo(_UserKeywordInfo):
    _type = 'resource file'
