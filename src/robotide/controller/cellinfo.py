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

from robotide.utils import highlightmatcher, html_escape
from robotide.utils import PY3
if PY3:
    from robotide.utils import unicode


class CellInfo(object):

    def __init__(self, cell_content, cell_position, for_loop=False):
        self._cell_content = cell_content
        self._cell_position = cell_position
        self.for_loop = for_loop

    @property
    def content_type(self):
        return self._cell_content.type

    @property
    def cell_type(self):
        return self._cell_position.type

    @property
    def source(self):
        return self._cell_content.source

    @property
    def arg_name(self):
        return self._cell_position.argument_name

    def has_error(self):
        return self.argument_missing() or self.too_many_arguments()

    def argument_missing(self):
        return self.cell_type == CellType.MANDATORY \
            and self.content_type in [ContentType.EMPTY, ContentType.COMMENTED]

    def too_many_arguments(self):
        return self.cell_type == CellType.MUST_BE_EMPTY \
            and self.content_type not in \
            [ContentType.EMPTY, ContentType.COMMENTED]

    def matches(self, value):
        return highlightmatcher.highlight_matcher(value,
                                                  self._cell_content.value)


def TipMessage(cell):
    if not cell:
        return ''
    tip = _TooltipMessage(cell) if not cell.for_loop \
        else _ForLoopTooltipMessage(cell)
    return html_escape(unicode(tip))


class _TooltipMessage(object):

    TOO_MANY_ARGUMENTS = "Too many arguments"
    KEYWORD_NOT_FOUND = \
        "Keyword not found! For possible corrections press <Ctrl-M>"
    VARIABLE_ASSIGMENT = "Variable assignment"
    UNKNOWN_VARIABLE = "\n\nUnknown variable"

    ARGUMENT = "Argument:  %s"
    OPTIONAL_ARGUMENT = "Optional argument:  %s"
    MISSING_ARGUMENT = "Missing argument:  %s"

    KEYWORD = "Keyword from:  %s\n\nPress <Ctrl-M> for details"

    def __init__(self, cell):
        self.message = self._get_message(cell)

    def _get_message(self, cell):
        message = '' if cell.content_type != ContentType.UNKNOWN_VARIABLE \
            else self.UNKNOWN_VARIABLE
        handlers = {
            CellType.ASSIGN: self._assign,
            CellType.KEYWORD: self._keyword,
            CellType.MANDATORY: self._mandatory,
            CellType.OPTIONAL: self._optional,
            CellType.MUST_BE_EMPTY: self._must_be_empty,
            CellType.UNKNOWN: self._unknown,
            CellType.END: self._keyword,
            CellType.FOR: self._keyword
        }
        return (handlers[cell.cell_type](cell) + message).strip()

    def _must_be_empty(self, cell):
        if cell.too_many_arguments():
            return self.TOO_MANY_ARGUMENTS
        return ''

    def _mandatory(self, cell):
        if cell.argument_missing():
            return self.MISSING_ARGUMENT % cell.arg_name
        return self.ARGUMENT % cell.arg_name

    def _optional(self, cell):
        return self.OPTIONAL_ARGUMENT % cell.arg_name

    def _keyword(self, cell):
        if cell.content_type == ContentType.STRING:
            return self.KEYWORD_NOT_FOUND
        if cell.content_type in ContentType.KEYWORDS:
            return self.KEYWORD % cell.source
        return ''

    def _assign(self, cell):
        return self.VARIABLE_ASSIGMENT

    def _unknown(self, cell):
        return ''

    def __nonzero__(self):
        return bool(self.message)

    def __str__(self):
        return self.message


class _ForLoopTooltipMessage(_TooltipMessage):

    TOO_MANY_ARGUMENTS = "Too many parameters in for loop"

    def _get_message(self, cell):
        if cell.too_many_arguments():
            return self.TOO_MANY_ARGUMENTS
        return ''


class CellContent(object):

    def __init__(self, type, value, source=None):
        self.type = type
        self.value = value
        self.source = source


class CellPosition(object):

    def __init__(self, type, argument_name):
        self.type = type
        self.argument_name = argument_name


class ContentType:
    USER_KEYWORD = 'USER_KEYWORD'
    LIBRARY_KEYWORD = 'LIBRARY_KEYWORD'
    END = 'END'
    FOR = 'FOR'
    KEYWORDS = (USER_KEYWORD, LIBRARY_KEYWORD, END, FOR)
    VARIABLE = 'VARIABLE'
    UNKNOWN_VARIABLE = 'UNKNOWN_VARIABLE'
    COMMENTED = 'COMMENTED'
    STRING = 'STRING'
    EMPTY = 'EMPTY'


class CellType:
    ASSIGN = 'ASSIGN'
    KEYWORD = 'KEYWORD'
    MANDATORY = 'MANDATORY'
    OPTIONAL = 'OPTIONAL'
    MUST_BE_EMPTY = 'MUST_BE_EMPTY'
    UNKNOWN = 'UNKNOWN'
    FOR = 'KEYWORD'
    END = 'KEYWORD'
