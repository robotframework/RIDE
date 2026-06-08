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

from enum import Enum, auto
from ..action.shortcut import localize_shortcuts
from ..utils import highlightmatcher, html_escape

CTRL_LABEL = localize_shortcuts('CtrlCmd')


class PrivateError(Enum):
    no_error = auto()
    invalid = auto()


class CellInfo(object):

    def __init__(self, cell_content, cell_position, for_loop=False):
        self._cell_content = cell_content
        self._cell_position = cell_position
        self.for_loop = for_loop
        self._error_state = PrivateError.no_error

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
    def private(self):
        return self._cell_content.private

    @property
    def arg_name(self):
        return self._cell_position.argument_name

    @property
    def value(self):
        return self._cell_content.value

    def has_error(self):
        return self.argument_missing() or self.too_many_arguments() or self._error_state == PrivateError.invalid

    def set_or_clear_error(self, mode=False):
        if mode:
            self._error_state = PrivateError.invalid
        else:
            self._error_state = PrivateError.no_error

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


def tip_message(cell):
    if not cell:
        return ''
    tip = _TooltipMessage(cell)  # if not cell.for_loop else _ForLoopTooltipMessage(cell)
    return html_escape(str(tip)).replace('\n', '<br />')


class _TooltipMessage(object):

    TOO_MANY_ARGUMENTS = "Too many arguments"
    KEYWORD_NOT_FOUND = \
        "Keyword not found! For possible corrections press <%s>" % CTRL_LABEL
    VARIABLE_ASSIGMENT = "Variable assignment"
    UNKNOWN_VARIABLE = "\n\nUnknown variable"

    ARGUMENT = "Argument:  %s"
    OPTIONAL_ARGUMENT = "Optional argument:  %s"
    MISSING_ARGUMENT = "Missing argument:  %s"

    KEYWORD = "Keyword from:  %s\n\n" + ("Press <%s> for details" % CTRL_LABEL)
    CONTROL_MARKER = "Control Marker from:  %s\n\n" + ("Press <%s> for details" % CTRL_LABEL)

    def __init__(self, cell):
        self.message = self._get_message(cell)

    def _get_message(self, cell):
        message = '' if cell.content_type != ContentType.UNKNOWN_VARIABLE \
            else self.UNKNOWN_VARIABLE
        handlers = {
            CellType.ASSIGN: self._assign,
            CellType.KEYWORD: self._keyword,
            CellType.CONTROL_MARKER: self._control_marker,
            CellType.MANDATORY: self._mandatory,
            CellType.OPTIONAL: self._optional,
            CellType.MUST_BE_EMPTY: self._must_be_empty,
            CellType.UNKNOWN: self._unknown,
            CellType.AND: self._control_marker,
            CellType.BREAK: self._control_marker,
            CellType.CONTINUE: self._control_marker,
            CellType.ELSE: self._control_marker,
            CellType.ELSEIF: self._control_marker,
            CellType.END: self._control_marker,
            CellType.EXCEPT: self._control_marker,
            CellType.FINALLY: self._control_marker,
            CellType.FOR: self._control_marker,
            CellType.GROUP: self._control_marker,
            CellType.IF: self._control_marker,
            CellType.IN: self._control_marker,
            CellType.INENUMERATE: self._control_marker,
            CellType.INRANGE: self._control_marker,
            CellType.INZIP: self._control_marker,
            CellType.RETURN: self._control_marker,
            CellType.TRY: self._control_marker,
            CellType.VAR: self._assign,
            CellType.WHILE: self._control_marker
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

    def _control_marker(self, cell):
        if cell.content_type == ContentType.STRING:
            return self.KEYWORD_NOT_FOUND
        if cell.value in ContentType.CONTROL_MARKERS:
            return self.CONTROL_MARKER % cell.source
        return ''

    def _assign(self, cell):
        _ = cell
        return self.VARIABLE_ASSIGMENT

    @staticmethod
    def _unknown(cell):
        _ = cell
        return ''

    def __nonzero__(self):
        return bool(self.message)

    def __str__(self):
        return self.message


class CellContent(object):

    def __init__(self, ctype, value, source=None, private=False):
        self.type = ctype
        self.value = value
        self.source = source
        self.private = private


class CellPosition(object):

    def __init__(self, ctype, argument_name):
        self.type = ctype
        self.argument_name = argument_name


class ContentType:
    USER_KEYWORD = 'USER_KEYWORD'
    LIBRARY_KEYWORD = 'LIBRARY_KEYWORD'
    CONTROL_MARKER = 'CONTROL_MARKER'
    AND = 'AND'
    BREAK = 'BREAK'
    CONTINUE = 'CONTINUE'
    ELSE = 'ELSE'
    ELSEIF = 'ELSE IF'
    END = 'END'
    EXCEPT = 'EXCEPT'
    FINALLY = 'FINALLY'
    FOR = 'FOR'
    GROUP = 'GROUP'
    IF = 'IF'
    IN = 'IN'
    INENUMERATE = 'IN ENUMERATE'
    INRANGE = 'IN RANGE'
    INZIP = 'IN ZIP'
    RETURN = 'RETURN'
    TRY = 'TRY'
    VAR = 'VAR'
    WHILE = 'WHILE'
    KEYWORDS = (USER_KEYWORD, LIBRARY_KEYWORD)
    CONTROL_MARKERS = (AND, BREAK, CONTINUE, ELSE, ELSEIF, END, EXCEPT, FINALLY, FOR,
                       GROUP, IF, IN, INENUMERATE, INRANGE, INZIP, RETURN, TRY, VAR, WHILE)
    VARIABLE = 'VARIABLE'
    UNKNOWN_VARIABLE = 'UNKNOWN_VARIABLE'
    COMMENTED = 'COMMENTED'
    STRING = 'STRING'
    EMPTY = 'EMPTY'


class CellType:
    ASSIGN = 'ASSIGN'
    KEYWORD = 'KEYWORD'
    CONTROL_MARKER = 'CONTROL_MARKER'
    MANDATORY = 'MANDATORY'
    OPTIONAL = 'OPTIONAL'
    MUST_BE_EMPTY = 'MUST_BE_EMPTY'
    UNKNOWN = 'UNKNOWN'
    AND = 'CONTROL_MARKER'
    BREAK = 'CONTROL_MARKER'
    CONTINUE = 'CONTROL_MARKER'
    ELSE = 'CONTROL_MARKER'
    ELSEIF = 'CONTROL_MARKER'
    END = 'CONTROL_MARKER'
    EXCEPT = 'CONTROL_MARKER'
    FINALLY = 'CONTROL_MARKER'
    FOR = 'CONTROL_MARKER'
    GROUP = 'CONTROL_MARKER'
    IF = 'CONTROL_MARKER'
    IN = 'CONTROL_MARKER'
    INENUMERATE = 'CONTROL_MARKER'
    INRANGE = 'CONTROL_MARKER'
    INZIP = 'CONTROL_MARKER'
    RETURN = 'CONTROL_MARKER'
    TRY = 'CONTROL_MARKER'
    VAR = 'ASSIGN'
    WHILE = 'CONTROL_MARKER'


CONTROL_MARKERS = [ContentType.AND, ContentType.BREAK, ContentType.CONTINUE, ContentType.ELSE,
                   ContentType.ELSEIF, ContentType.END, ContentType.EXCEPT, ContentType.FINALLY,
                   ContentType.FOR, ContentType.GROUP, ContentType.IF, ContentType.IN,
                   ContentType.INENUMERATE, ContentType.INRANGE, ContentType.INZIP, ContentType.RETURN,
                   ContentType.TRY, ContentType.VAR, ContentType.WHILE]
