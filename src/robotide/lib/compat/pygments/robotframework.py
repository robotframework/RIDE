"""
    pygments.lexers.robotframework
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Lexer for Robot Framework.

    :copyright: Copyright 2006-2023 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import annotations

#  Copyright 2012 Nokia Siemens Networks Oyj
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

#  Copyright 2012-2015 Nokia Networks
#  Copyright 2023-     Robot Framework Foundation
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
#
# This is a modified copy from Pygments 2.17.0, by Hélio Guilherme 2023-12-09
# The changes in this file were done with the purpose to add colorization
# support for test suites using languages other than English and supported
# by Robot Framework 6.0 or higher (at the time, version is 6.1.1)


import re

from pygments.lexer import Lexer
from pygments.token import Token
from multiprocessing import shared_memory
from robotide.lib.compat.parsing.language import Language
from robotide.utils import normalize_lc, normalize_dict, normalize_pipe_list

if not Language:  # Let's import original
    raise ImportError

__all__ = ['RobotFrameworkLexer']


HEADING = Token.Generic.Heading
SETTING = Token.Keyword.Namespace
IMPORT = Token.Name.Namespace
TC_KW_NAME = Token.Generic.Subheading
KEYWORD = Token.Name.Function
CONTROL = Token.Name.Function.Magic
ARGUMENT = Token.String
VARIABLE = Token.Name.Variable
COMMENT = Token.Comment
SEPARATOR = Token.Punctuation
SYNTAX = Token.Punctuation
GHERKIN = Token.Generic.Emph
ERROR = Token.Error

FORSEP = ('IN', 'IN ENUMERATE', 'IN RANGE', 'IN ZIP')
CONTROLS = ('AND', 'BREAK', 'CONTINUE', 'ELSE', 'ELSE IF', 'END', 'EXCEPT',
            'FINALLY', 'FOR', 'GROUP', 'IF', FORSEP[:], 'RETURN', 'TRY', 'VAR', 'WHILE')

def get_key_by_value(table: dict, value: str) -> str:
    for k, v in table.items():
        if v == value:
            return k
    return value  # Returns original if not in dict, deprecated/old labels

def normalize(string, remove='', strip=True):
    string = string.lower()
    for char in remove + ' ':
        if char in string:
            string = string.replace(char, '')
    return string if not strip else string.strip()

def is_control(value):
    return value in CONTROLS  # and value not in FORSEP

class RobotFrameworkLexer(Lexer):
    """
    For `Robot Framework <http://robotframework.org>`_ test data.

    Supports both space and pipe separated plain text formats.

    ... versionadded:: 1.6
    """
    name = 'RobotFramework'
    url = 'http://robotframework.org'
    aliases = ['robotframework']
    filenames = ['*.robot', '*.resource']
    mimetypes = ['text/x-robotframework']

    def __init__(self, **options):
        options['tabsize'] = 2
        options['encoding'] = 'UTF-8'
        Lexer.__init__(self, **options)
        self.language = options.get('doc language', None)
        try:
            set_lang = shared_memory.ShareableList(name="language")
        except FileNotFoundError:
            set_lang = ['']
        if not self.language:
            # DEBUG self.new_lang = Language.from_name('en')
            shared_lang = set_lang[0].replace('_', '-') or 'en'
            self.new_lang = Language.from_name(shared_lang)
        else:
            self.new_lang = Language.from_name(self.language[0].replace('_', '-'))  # DEBUG: We consider a single language
        # print(f"DEBUG: robotframework.py after RobotFrameworkLexer _init_ mimetypes={self.mimetypes}\n"
        #      f"options['doc language']={options['doc language']}\n"
        #      f"self.new_lang={self.new_lang.code.replace('-','_')}")

    def get_tokens_unprocessed(self, text):
        row_tokenizer = RowTokenizer(self.new_lang)
        var_tokenizer = VariableTokenizer()
        index = 0
        for row in text.splitlines():
            for value, token in row_tokenizer.tokenize(row):
                for value, token in var_tokenizer.tokenize(value, token):
                    if value:
                        yield index, token, str(value)
                        index += len(value)


class VariableTokenizer:

    def tokenize(self, string, token):
        var = VariableSplitter(string, identifiers='$@%&')
        if var.start < 0 or token in (COMMENT, ERROR):
            yield string, token
            return
        for value, token in self._tokenize(var, string, token):
            if value:
                yield value, token

    def _tokenize(self, var, string, orig_token):
        before = string[:var.start]
        yield before, orig_token
        yield var.identifier + '{', SYNTAX
        yield from self.tokenize(var.base, VARIABLE)
        yield '}', SYNTAX
        for item in var.items:
            yield '[', SYNTAX
            yield from self.tokenize(item, VARIABLE)
            yield ']', SYNTAX
        yield from self.tokenize(string[var.end:], orig_token)


class RowTokenizer:
    new_lang = None

    def __init__(self, new_lang):
        if self.new_lang is None:
            if new_lang is None:
                set_lang = shared_memory.ShareableList(name="language")
                self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
            else:
                self.new_lang = new_lang
        self._table = UnknownTable()
        self._splitter = RowSplitter()
        testcases = TestCaseTable(new_lang=self.new_lang)
        settings = SettingTable(testcases.set_default_template, new_lang=self.new_lang)
        variables = VariableTable(new_lang=self.new_lang)
        keywords = KeywordTable(new_lang=self.new_lang)
        comments = CommentsTable(new_lang=self.new_lang)
        normalized_headers = normalize_dict(self.new_lang.headers)
        self._tables = {get_key_by_value(normalized_headers, 'settings'): settings,
                        get_key_by_value(normalized_headers, 'metadata'): settings,
                        get_key_by_value(normalized_headers, 'variables'): variables,
                        get_key_by_value(normalized_headers, 'testcases'): testcases,
                        get_key_by_value(normalized_headers, 'tasks'): testcases,
                        get_key_by_value(normalized_headers, 'keywords'): keywords,
                        get_key_by_value(normalized_headers, 'comments'): comments}

    def tokenize(self, row):
        commented = False
        heading = False
        for index, value in enumerate(self._splitter.split(row)):
            # First value, and every second after that, is a separator.
            index, separator = divmod(index-1, 2)
            if value.startswith('#'):
                commented = True
            elif index == 0 and value.startswith('*'):
                self._table = self._start_table(value)
                # print(f"DEBUG: robotframework.py RowTokenizer tokenize HEADING value={value}\n"
                #       f"self._table={self._table} lang={self.new_lang}\n")
                heading = True
            yield from self._tokenize(value, index, commented,
                                      separator, heading)
        self._table.end_row()

    def _start_table(self, header):
        name = normalize_lc(header, remove='*')
        return self._tables.get(name, UnknownTable())

    def _tokenize(self, value, index, commented, separator, heading):
        # print(f"DEBUG: robotframework.py RowTokenizer _tokenize lang={self.new_lang}\n"
        #       f"{value=}, {index=}, {commented=}, {separator=}, {heading=}")
        if commented:
            yield value, COMMENT
        elif separator:
            yield value, SEPARATOR
        elif heading:
            token = HEADING if self._in_valid_table() else ERROR
            yield value, token
        elif is_control(value):
            yield value, CONTROL
        else:
            yield from self._table.tokenize(value, index)

    def _in_valid_table(self):
        return not isinstance(self._table, UnknownTable)

class RowSplitter:
    _space_splitter = re.compile('( {2,})')
    _pipe_splitter = re.compile(r'((?:^| +)\|(?: +|$))')

    def split(self, row):
        splitter = (row.startswith('| ') and self._split_from_pipes
                    or self._split_from_spaces)
        yield from splitter(row)
        yield '\n'

    def _split_from_spaces(self, row):
        yield ''  # Start with (pseudo)separator similarly as with pipes
        yield from self._space_splitter.split(row)

    def _split_from_pipes(self, row):
        _, separator, rest = self._pipe_splitter.split(row, 1)
        yield separator
        while self._pipe_splitter.search(rest):
            cell, separator, rest = self._pipe_splitter.split(rest, 1)
            yield cell
            yield separator
        yield rest


class Tokenizer:
    _tokens = None
    new_lang = None

    def __init__(self, new_lang=None):
        if self.new_lang is None:
            if new_lang is None:
                try:
                    set_lang = shared_memory.ShareableList(name="language")
                    self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
                except (ValueError, FileNotFoundError):
                    self.new_lang = ['En']
            else:
                self.new_lang = new_lang
        self._index = 0
        # print(f"DEBUG: robotframework.py Tokenizer __init__ language={self.new_lang}")

    def tokenize(self, value):
        values_and_tokens = self._tokenize(value, self._index)
        self._index += 1
        if isinstance(values_and_tokens, type(Token)):
            values_and_tokens = [(value, values_and_tokens)]
        return values_and_tokens

    def _tokenize(self, value, index):
        _ = value
        index = min(index, len(self._tokens) - 1)
        return self._tokens[index]

    @staticmethod
    def _is_assign(value):
        if value.endswith('='):
            value = value[:-1].strip()
        var = VariableSplitter(value, identifiers='$@&')
        return var.start == 0 and var.end == len(value)


class Comment(Tokenizer):
    _tokens = (COMMENT,)
    new_lang = None


class Setting(Tokenizer):
    _tokens = (SETTING, ARGUMENT)
    _keyword_settings = ('suitesetup', 'suiteteardown',
                         'arguments', 'teardown', 'testsetup', 'tasksetup',
                         'testteardown','taskteardown', 'testtemplate', 'tasktemplate', 'setup', 'template')
    _import_settings = ('library', 'resource', 'variables')
    _other_settings = ('documentation', 'metadata', 'testtags', 'tasktags', 'tags', 'forcetags', 'defaulttags',
                       'testtimeout','tasktimeout', 'timeout')
    _custom_tokenizer = None
    new_lang = None

    def __init__(self, template_setter=None, new_lang=None):
        Tokenizer.__init__(self)
        self._template_setter = template_setter
        if self.new_lang is None:
            if new_lang is None:
                try:
                    set_lang = shared_memory.ShareableList(name="language")
                    self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
                except (ValueError, FileNotFoundError):
                    pass
            else:
                self.new_lang = new_lang
        if self.new_lang is None or isinstance(self.new_lang, list) :
            self.new_lang = Language.from_name('En')
        # print(f"DEBUG: robotframework.py Setting self.new_lang={self.new_lang}\n"
        #       f"type of self.new_lang={type(self.new_lang)} ")
        self.normalized_settings = normalize_dict(self.new_lang.settings)
        self._keyword_settings = (get_key_by_value(self.normalized_settings,'suitesetup'),
                                  get_key_by_value(self.normalized_settings, 'suiteprecondition'),
                                  get_key_by_value(self.normalized_settings, 'suiteteardown'),
                                  get_key_by_value(self.normalized_settings, 'suitepostcondition'),
                                  # get_key_by_value(self.normalized_settings, 'documentation'),
                                  get_key_by_value(self.normalized_settings, 'arguments'),  # Keyword setting
                                  get_key_by_value(self.normalized_settings,'teardown'),  # Keyword setting
                                  get_key_by_value(self.normalized_settings,'testsetup'),
                                  get_key_by_value(self.normalized_settings,'tasksetup'),
                                  get_key_by_value(self.normalized_settings, 'testprecondition'),
                                  get_key_by_value(self.normalized_settings,'testteardown'),
                                  get_key_by_value(self.normalized_settings,'taskteardown'),
                                  get_key_by_value(self.normalized_settings, 'testpostcondition'),
                                  get_key_by_value(self.normalized_settings, 'testtemplate'),
                                  get_key_by_value(self.normalized_settings,'tasktemplate'),
                                  get_key_by_value(self.normalized_settings, 'setup'),
                                  get_key_by_value(self.normalized_settings, 'precondition'),  # obsolete
                                  get_key_by_value(self.normalized_settings, 'postcondition'),  # obsolete
                                  get_key_by_value(self.normalized_settings, 'template'))
        self._import_settings = (get_key_by_value(self.normalized_settings,'library'),
                                 get_key_by_value(self.normalized_settings,'resource'),
                                 get_key_by_value(self.normalized_settings,'variables'))
        self._other_settings = (get_key_by_value(self.normalized_settings,'documentation'),
                                get_key_by_value(self.normalized_settings, 'metadata'),
                                get_key_by_value(self.normalized_settings, 'keywordtags'),  # New
                                get_key_by_value(self.normalized_settings, 'testtags'),  # New
                                get_key_by_value(self.normalized_settings,'tasktags'),  # New
                                get_key_by_value(self.normalized_settings, 'tags'),  # New
                                get_key_by_value(self.normalized_settings,'forcetags'),  # Non-existing
                                get_key_by_value(self.normalized_settings,'defaulttags'),  # Non-existing
                                get_key_by_value(self.normalized_settings, 'testtimeout'),
                                get_key_by_value(self.normalized_settings, 'tasktimeout'),
                                get_key_by_value(self.normalized_settings, 'timeout'))
        Tokenizer.__init__(self, new_lang=self.new_lang)
        # print(f"DEBUG: robotframework.py Setting self.normalized_settings={self.normalized_settings}\n"
        #       f"self._keyword_settings={self._keyword_settings}\n"
        #       f"self._import_settings={self._import_settings}\n"
        #      f"self._other_settings={self._other_settings}\n")

    def _tokenize(self, value, index):
        if index == 1 and self._template_setter:
            self._template_setter(value)
        if index == 0:
            normalized = normalize_lc(value)
            if normalized in self._keyword_settings:
                # print(f"DEBUG: robotframework.py Setting call KeywordCall in _tokenize value={value}")
                self._custom_tokenizer = KeywordCall(support_assign=False)
            elif normalized in self._import_settings:
                self._custom_tokenizer = ImportSetting()
                return IMPORT
            elif normalized not in self._other_settings:
                return ERROR
        elif self._custom_tokenizer:
            return self._custom_tokenizer.tokenize(value)
        return Tokenizer._tokenize(self, value, index)


class ImportSetting(Tokenizer):
    _tokens = (IMPORT, ARGUMENT)
    new_lang = None

    def __init__(self, new_lang=None):
        if self.new_lang is None:
            if new_lang is None:
                try:
                    set_lang = shared_memory.ShareableList(name="language")
                    self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
                except (ValueError, FileNotFoundError):
                    self.new_lang = None
            else:
                self.new_lang = new_lang
        if self.new_lang is None:
            self.new_lang = Language.from_name('En')
        self.normalized_settings = normalize_dict(self.new_lang.settings)
        self._import_settings = (get_key_by_value(self.normalized_settings, 'library'),
                                 get_key_by_value(self.normalized_settings, 'resource'),
                                 get_key_by_value(self.normalized_settings, 'variables'))
        Tokenizer.__init__(self, new_lang=self.new_lang)


class TestCaseSetting(Setting):
    _keyword_settings = ('setup', 'teardown', 'template')
    _import_settings = ()
    _other_settings = ('documentation', 'tags', 'timeout')

    def __init__(self, template_setter=None, new_lang=None):
        if self.new_lang is None:
            if new_lang is None:
                set_lang = shared_memory.ShareableList(name="language")
                try:
                    self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
                except ValueError:
                    self.new_lang = None
            else:
                self.new_lang = new_lang
        if self.new_lang is None:
            self.new_lang = Language.from_name('En')
        self.normalized_settings = normalize_dict(self.new_lang.settings)
        self._keyword_settings = (get_key_by_value(self.normalized_settings, 'setup'),
                                  get_key_by_value(self.normalized_settings, 'precondition'),  # obsolete
                                  get_key_by_value(self.normalized_settings, 'testsetup'),
                                  get_key_by_value(self.normalized_settings, 'teardown'),
                                  # get_key_by_value(self.normalized_settings, 'documentation'),
                                  get_key_by_value(self.normalized_settings, 'postcondition'),  # obsolete
                                  get_key_by_value(self.normalized_settings, 'template'))
        # DEBUG self._import_settings = ()
        self._other_settings = (get_key_by_value(self.normalized_settings, 'documentation'),
                                get_key_by_value(self.normalized_settings, 'timeout'),
                                get_key_by_value(self.normalized_settings, 'keywordtags'),  # New
                                get_key_by_value(self.normalized_settings, 'tags'))
        Setting.__init__(self, template_setter=template_setter, new_lang=new_lang)
        # print(f"DEBUG: robotframework.py TestCaseSetting \n"
        #       f"self._keyword_settings={self._keyword_settings}\n"
        #       f"self._import_settings={self._import_settings}\n"
        #       f"self._other_settings={self._other_settings}\n")

    def _tokenize(self, value, index):
        # print(f"DEBUG: robotframework.py TestCaseSetting _tokenize self.new_lang={self.new_lang} value={value}\n")
        normalized = normalize_lc(value)
        if normalized in self._keyword_settings:
            self._custom_tokenizer = KeywordCall(support_assign=False)
        if index == 0:
            stype = Setting(new_lang=self.new_lang)._tokenize(value[1:-1], index)
            return [('[', SYNTAX), (value[1:-1], stype), (']', SYNTAX)]
        elif self._custom_tokenizer:
            return self._custom_tokenizer.tokenize(value)
        return Setting(new_lang=self.new_lang)._tokenize(value, index)


class KeywordSetting(TestCaseSetting):
    _keyword_settings = ('setup', 'testsetup', 'teardown', 'template')
    _other_settings = ('documentation', 'arguments', 'return', 'timeout', 'tags')

    def __init__(self, template_setter=None, new_lang=None):
        if self.new_lang is None:
            if new_lang is None:
                set_lang = shared_memory.ShareableList(name="language")
                try:
                    self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
                except ValueError:
                    self.new_lang = None
            else:
                self.new_lang = new_lang
        if self.new_lang is None:
            self.new_lang = Language.from_name('En')
        self.normalized_settings = normalize_dict(self.new_lang.settings)
        self._keyword_settings = (get_key_by_value(self.normalized_settings, 'setup'),
                                  get_key_by_value(self.normalized_settings, 'precondition'),  # obsolete
                                  get_key_by_value(self.normalized_settings, 'testsetup'),
                                  get_key_by_value(self.normalized_settings, 'teardown'),
                                  get_key_by_value(self.normalized_settings, 'return'),  # Non-existing
                                  get_key_by_value(self.normalized_settings, 'postcondition'),  # obsolete
                                  get_key_by_value(self.normalized_settings, 'template'))
        self._other_settings = (get_key_by_value(self.normalized_settings, 'documentation'),
                                get_key_by_value(self.normalized_settings, 'timeout'),
                                get_key_by_value(self.normalized_settings, 'keywordtags'),  # New
                                get_key_by_value(self.normalized_settings, 'tags'))
        TestCaseSetting.__init__(self, template_setter=template_setter, new_lang=new_lang)


class Variable(Tokenizer):
    _tokens = (SYNTAX, ARGUMENT)
    new_lang = None

    def _tokenize(self, value, index):
        if index == 0 and not self._is_assign(value):
            return ERROR
        return Tokenizer._tokenize(self, value, index)


class KeywordCall(Tokenizer):
    _tokens = (KEYWORD, ARGUMENT)
    new_lang = None

    def __init__(self, support_assign=True, new_lang=None):
        if self.new_lang is None:
            if new_lang is None:
                try:
                    set_lang = shared_memory.ShareableList(name="language")
                    self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
                except (ValueError, FileNotFoundError):
                    self.new_lang = None
            else:
                self.new_lang = new_lang
        if self.new_lang is None:
            self.new_lang = Language.from_name('En')
        # print(f"DEBUG: robotframework.py KeywordCall __init__ lang={self.new_lang}")
        Tokenizer.__init__(self, new_lang=self.new_lang)
        self._keyword_found = not support_assign
        self._control_found = False
        self._assigns = 0

    def _tokenize(self, value, index):
        # print(f"DEBUG: robotframework.py KeywordCall _tokenize ENTER value={value} index={index}\n")
        if not self._keyword_found and self._is_assign(value):
            self._assigns += 1
            return SYNTAX  # VariableTokenizer tokenizes this later.
        if self._keyword_found or self._control_found:
            if not is_control(value):
                self._tokens = (KEYWORD, ARGUMENT)
            else:
                self._tokens = (CONTROL, ARGUMENT)
            return Tokenizer._tokenize(self, value, index - self._assigns)
        self._control_found = is_control(value) or value in FORSEP
        if self._control_found:
            self._tokens = (CONTROL, ARGUMENT)
        self._keyword_found = not self._control_found
        return GherkinTokenizer().tokenize(value, self._tokens[0])


class GherkinTokenizer:
    # _gherkin_prefix = re.compile('^(Given|When|Then|And|But) ', re.IGNORECASE)
    new_lang = None

    def __init__(self, new_lang=None):
        if self.new_lang is None:
            if new_lang is None:
                set_lang = shared_memory.ShareableList(name="language")
                try:
                    self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
                except ValueError:
                    self.new_lang = None
            else:
                self.new_lang = new_lang
        if self.new_lang is None:
            self.new_lang = Language.from_name('En')
        # Sort prefixes by descending length so that the longest ones are matched first
        prefixes = sorted(self.new_lang.bdd_prefixes, key=len, reverse=True)
        self.normalized_bdd_prefixes = normalize_pipe_list(list(prefixes), spaces=False)
        # print(f"DEBUG: robotframework.py GherkinTokenizer _tokenize DEFINITION GHERKIN"
        #       f" BDDPREFIXES={self.new_lang.bdd_prefixes}\n"
        #       f"PATTERN='^({self.normalized_bdd_prefixes}) '"
        #       f"new_lang={self.new_lang}")
        self._gherkin_prefix = re.compile(fr'^({self.normalized_bdd_prefixes}) ', re.IGNORECASE)

    def tokenize(self, value, token):
        # print(f"DEBUG: robotframework.py GherkinTokenizer tokenize ENTER self._gherkin_prefix={self._gherkin_prefix}:"
        #       f"\nvalue={value} token={token}")
        match = self._gherkin_prefix.match(value)
        if not match:
            # print(f"DEBUG: robotframework.py GherkinTokenizer tokenize NO MATCH value={value} token={token}")
            return [(value, token)]
        end = match.end()
        # print(f"DEBUG: robotframework.py GherkinTokenizer tokenize RETURN MATCH GHERKIN value={value[:end]}
        # rest={value[end:]}")
        return [(value[:end], GHERKIN), (value[end:], token)]


class TemplatedKeywordCall(Tokenizer):
    _tokens = (ARGUMENT,)
    new_lang = None


class ForLoop(Tokenizer):
    new_lang = None

    def __init__(self, new_lang=None):
        if self.new_lang is None:
            if new_lang is None:
                set_lang = shared_memory.ShareableList(name="language")
                try:
                    self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
                except ValueError:
                    self.new_lang = None
            else:
                self.new_lang = new_lang
        if self.new_lang is None:
            self.new_lang = Language.from_name('En')
        Tokenizer.__init__(self, new_lang=self.new_lang)
        self._in_arguments = False

    def _tokenize(self, value, index):
        token = self._in_arguments and ARGUMENT or SYNTAX
        if value in ('FOR', 'IN', 'IN ENUMERATE', 'IN RANGE', 'IN ZIP'):  # value must be in all caps
            self._in_arguments = value != 'FOR'
            token = CONTROL
        elif (index == 0 and value in (': FOR', 'for') or
              index > 1 and value in ('in', 'in enumerate', 'in range', 'in zip')):
            self._in_arguments = True
            token = ERROR
        elif index >= 1 and not self._in_arguments:
            var = list(VariableTokenizer().tokenize(value, ARGUMENT))
            if len(var) > 1  and var[1][1] == VARIABLE:
                token = SYNTAX
            elif var[0][1] == ARGUMENT:
                token = ERROR
            else:
                token = ARGUMENT
        return token


class _Table:
    _tokenizer_class = None
    new_lang = None

    def __init__(self, prev_tokenizer=None, new_lang=None):
        if self.new_lang is None:
            if new_lang is None:
                try:
                    set_lang = shared_memory.ShareableList(name="language")
                except  FileNotFoundError:
                    set_lang = ['En']
                try:
                    self.new_lang = Language.from_name(set_lang[0].replace('_','-'))
                except ValueError:
                    self.new_lang = None
            else:
                self.new_lang = new_lang
        if self.new_lang is None:
            self.new_lang = Language.from_name('En')
        self._tokenizer = self._tokenizer_class()
        self._prev_tokenizer = prev_tokenizer
        self._prev_values_on_row = []

    def tokenize(self, value, index):
        if self._continues(value, index):
            self._tokenizer = self._prev_tokenizer
            yield value, SYNTAX
        else:
            yield from self._tokenize(value, index)
        self._prev_values_on_row.append(value)

    def _continues(self, value, index):
        _ = index
        return value == '...' and all(self._is_empty(t) for t in self._prev_values_on_row)

    @staticmethod
    def _is_empty(value):
        return value in ('', '\\')

    def _tokenize(self, value, index):
        _ = index
        return self._tokenizer.tokenize(value)

    def end_row(self):
        self.__init__(prev_tokenizer=self._tokenizer)


class CommentsTable(_Table):
    _tokenizer_class = Comment

    def _continues(self, value, index):
        return False


class UnknownTable(_Table):
    _tokenizer_class = Comment

    def _continues(self, value, index):
        return False


class VariableTable(_Table):
    _tokenizer_class = Variable


class SettingTable(_Table):
    _tokenizer_class = Setting
    new_lang = None

    def __init__(self, template_setter, prev_tokenizer=None, new_lang=None):
        _Table.__init__(self, prev_tokenizer)
        self._template_setter = template_setter
        if self.new_lang is None:
            if new_lang is None:
                set_lang = shared_memory.ShareableList(name="language")
                try:
                    self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
                except ValueError:
                    self.new_lang = None
            else:
                self.new_lang = new_lang
        if self.new_lang is None:
            self.new_lang = Language.from_name('En')
        self.normalized_settings = normalize_dict(self.new_lang.settings)
        _Table.__init__(self, prev_tokenizer, new_lang=self.new_lang)
        # print(f"DEBUG: robotframework.py SettingTable self.normalized_settings={self.normalized_settings}")

    def _tokenize(self, value, index):
        # print(f"DEBUG: robotframework.py SettingTable ENTER _tokenize "
        #       f"self.normalized_settings={self.normalized_settings}\n"
        #       f"value={value} new_lang={self.new_lang}")
        if index == 0 and normalize_lc(value) in (
                get_key_by_value(self.normalized_settings, 'metadata'),  # DEBUG
                get_key_by_value(self.normalized_settings, 'template'),
                get_key_by_value(self.normalized_settings, 'documentation'),
                get_key_by_value(self.normalized_settings, 'suitesetup'),
                get_key_by_value(self.normalized_settings, 'suiteteardown'),
                get_key_by_value(self.normalized_settings,'testsetup'),
                get_key_by_value(self.normalized_settings,'tasksetup'),
                get_key_by_value(self.normalized_settings,'testteardown'),
                get_key_by_value(self.normalized_settings,'taskteardown'),
                get_key_by_value(self.normalized_settings, 'library'),
                get_key_by_value(self.normalized_settings, 'resource'),
                get_key_by_value(self.normalized_settings, 'variables'),
                get_key_by_value(self.normalized_settings, 'testtemplate'),
                get_key_by_value(self.normalized_settings, 'tasktemplate')):
            self._tokenizer = Setting(template_setter=self._template_setter, new_lang=self.new_lang)
        return _Table._tokenize(self, value, index)

    def end_row(self):
        self.__init__(self._template_setter, prev_tokenizer=self._tokenizer, new_lang=self.new_lang)


class TestCaseTable(_Table):
    _setting_class = TestCaseSetting
    _test_template = None
    _default_template = None
    new_lang = None

    def __init__(self, prev_tokenizer=None, new_lang=None):
        if self.new_lang is None:
            if new_lang is None:
                set_lang = shared_memory.ShareableList(name="language")
                try:
                    self.new_lang = Language.from_name(set_lang[0].replace('_', '-'))
                except ValueError:
                    self.new_lang = None
            else:
                self.new_lang = new_lang
        if self.new_lang is None:
            self.new_lang = Language.from_name('En')
        # print(f"DEBUG: robotframework.py TestCaseTable __init__ self.new_lang={self.new_lang}")
        self.normalized_settings = normalize_dict(self.new_lang.settings)
        _Table.__init__(self, prev_tokenizer)
        # print(f"DEBUG: robotframework.py TestCaseTable self.normalized_settings={self.normalized_settings}")

    @property
    def _tokenizer_class(self):
        if self._test_template or (self._default_template and self._test_template is not False):
            return TemplatedKeywordCall
        return KeywordCall

    def _continues(self, value, index):
        return index > 0 and _Table._continues(self, value, index)

    def _tokenize(self, value, index):
        if index == 2 and self._test_template and self._is_template_set(value):
            return KeywordCall(new_lang=self.new_lang).tokenize(value)
        if index == 0:
            if value:
                self._test_template = None
            return GherkinTokenizer(new_lang=self.new_lang).tokenize(value, TC_KW_NAME)
        if index == 1 and self._is_setting(value):
            if self._is_template(value):
                self._test_template = False
                self._tokenizer = self._setting_class(template_setter=self.set_test_template, new_lang=self.new_lang)
            else:
                self._test_template = None
                self._tokenizer = self._setting_class(new_lang=self.new_lang)
        if self._is_for_loop(value):
            self._tokenizer = ForLoop()
        if index == 1 and self._is_empty(value):
            return [(value, SYNTAX)]
        if index == 1 and not self._is_setting(value):
            test_gherkin = GherkinTokenizer(new_lang=self.new_lang).tokenize(value, KEYWORD)
            if test_gherkin[0][1] in (GHERKIN, KEYWORD):
                return test_gherkin
        return _Table._tokenize(self, value, index)

    @staticmethod
    def _is_setting(value):
        return value.startswith('[') and value.endswith(']')

    def _is_template(self, value):
        return normalize_lc(value) in (f"[{get_key_by_value(self.normalized_settings, 'template')}]",
                                       f"[{get_key_by_value(self.normalized_settings, 'testsetup')}]",
                                       f"[{get_key_by_value(self.normalized_settings, 'tasksetup')}]",
                                       f"[{get_key_by_value(self.normalized_settings, 'testteardown')}]",
                                       f"[{get_key_by_value(self.normalized_settings, 'taskteardown')}]",
                                       f"[{get_key_by_value(self.normalized_settings, 'testtemplate')}]",
                                       f"[{get_key_by_value(self.normalized_settings, 'tasktemplate')}]",
                                       f"[{get_key_by_value(self.normalized_settings, 'setup')}]",
                                       f"[{get_key_by_value(self.normalized_settings, 'teardown')}]")

    @staticmethod
    def _is_for_loop(value):
        return (value.startswith(':') and normalize_lc(value, remove=':') == 'for') or value == 'FOR'

    def set_test_template(self, template):
        self._test_template = self._is_template_set(template)

    def set_default_template(self, template):
        self._default_template = self._is_template_set(template)

    @staticmethod
    def _is_template_set(template):
        return normalize_lc(template) not in ('', '\\', 'none', '${empty}')


class KeywordTable(TestCaseTable):
    _tokenizer_class = KeywordCall
    _setting_class = KeywordSetting

    def _is_template(self, value):
        return False


# Following code copied from Robot Framework 3.1.1.

class VariableSplitter:

    def __init__(self, string, identifiers='$@%&*'):
        self.identifier = None
        self.base = None
        self.items = []
        self.start = -1
        self.end = -1
        self._identifiers = identifiers
        self._may_have_internal_variables = False
        self._max_end = len(string)
        if self._split(string):
            self._finalize()

    def get_replaced_variable(self, replacer):
        if self._may_have_internal_variables:
            base = replacer.replace_string(self.base)
        else:
            base = self.base
        # This omits possible variable items.
        return '%s{%s}' % (self.identifier, base)

    def is_variable(self):
        return bool(self.identifier and self.base and
                    self.start == 0 and self.end == self._max_end)

    def is_list_variable(self):
        return bool(self.identifier == '@' and self.base and
                    self.start == 0 and self.end == self._max_end and
                    not self.items)

    def is_dict_variable(self):
        return bool(self.identifier == '&' and self.base and
                    self.start == 0 and self.end == self._max_end and
                    not self.items)

    def _finalize(self):
        self.identifier = self._variable_chars[0]
        self.base = ''.join(self._variable_chars[2:-1])
        self.end = self.start + len(self._variable_chars)
        if self.items:
            self.end += len(''.join(self.items)) + 2 * len(self.items)

    def _split(self, string):
        start_index, max_index = self._find_variable(string)
        if start_index == -1:
            return False
        self.start = start_index
        self._open_curly = 1
        self._state = self._variable_state
        self._variable_chars = [string[start_index], '{']
        self._item_chars = []
        self._string = string
        start_index += 2
        for index, char in enumerate(string[start_index:], start=start_index):
            try:
                self._state(char, index)
            except StopIteration:
                break
            if index == max_index and not self._scanning_item():
                break
        return True

    def _scanning_item(self):
        return self._state in (self._waiting_item_state, self._item_state)

    def _find_variable(self, string):
        max_end_index = string.rfind('}')
        if max_end_index == -1:
            return -1, -1
        if self._is_escaped(string, max_end_index):
            return self._find_variable(string[:max_end_index])
        start_index = self._find_start_index(string, 1, max_end_index)
        if start_index == -1:
            return -1, -1
        return start_index, max_end_index

    def _find_start_index(self, string, start, end):
        while True:
            index = string.find('{', start, end) - 1
            if index < 0:
                return -1
            if self._start_index_is_ok(string, index):
                return index
            start = index + 2

    def _start_index_is_ok(self, string, index):
        return (string[index] in self._identifiers
                and not self._is_escaped(string, index))

    @staticmethod
    def _is_escaped(string, index):
        escaped = False
        while index > 0 and string[index-1] == '\\':
            index -= 1
            escaped = not escaped
        return escaped

    def _variable_state(self, char, index):
        self._variable_chars.append(char)
        if char == '}' and not self._is_escaped(self._string, index):
            self._open_curly -= 1
            if self._open_curly == 0:
                if not self._can_have_item():
                    raise StopIteration
                self._state = self._waiting_item_state
        elif char in self._identifiers:
            self._state = self._internal_variable_start_state

    def _can_have_item(self):
        return self._variable_chars[0] in '$@&'

    def _internal_variable_start_state(self, char, index):
        self._state = self._variable_state
        if char == '{':
            self._variable_chars.append(char)
            self._open_curly += 1
            self._may_have_internal_variables = True
        else:
            self._variable_state(char, index)

    def _waiting_item_state(self, char, index):
        if char != '[':
            raise StopIteration
        self._state = self._item_state

    def _item_state(self, char, index):
        if char != ']':
            self._item_chars.append(char)
            return
        self.items.append(''.join(self._item_chars))
        self._item_chars = []
        # Don't support nested item access with olf @ and & syntax.
        # In RF 3.2 old syntax is to be deprecated and in RF 3.3 it
        # will be reassigned to mean using variable in list/dict context.
        if self._variable_chars[0] in '@&':
            raise StopIteration
        self._state = self._waiting_item_state
