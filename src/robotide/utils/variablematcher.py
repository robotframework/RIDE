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

from .. import utils

_VAR_BODY = r"([^\}]|\\\})*"
_SCALAR_VARIABLE_MATCHER = re.compile(r"\$\{" + _VAR_BODY + "}")
_SCALAR_VARIABLE_LINE_MATCHER = re.compile(r"^(\$\{" + _VAR_BODY + "}) *=?$")
_LIST_VARIABLE_MATCHER = re.compile(r"^(@\{" + _VAR_BODY + r"})( ?=?|\[\d*])$")
_DICT_VARIABLE_MATCHER = re.compile(r"^(&\{" + _VAR_BODY + r"})( ?=?|\[[a-zA-Z_]*])$")
_LIST_VARIABLE_SUBITEM_END_MATCHER = re.compile(r"\[\d+]$")
_DICT_VARIABLE_SUBITEM_END_MATCHER = re.compile(r"\[[a-zA-Z_]+]$")


def is_variable(value):
    return is_scalar_variable(value) or is_list_variable(value) or \
        is_dict_variable(value)


def is_scalar_variable(value):
    return _SCALAR_VARIABLE_LINE_MATCHER.match(value.strip())


def is_list_variable(value):
    return _LIST_VARIABLE_MATCHER.match(value.strip())


def is_dict_variable(value):
    return _DICT_VARIABLE_MATCHER.match(value.strip())


def is_list_variable_subitem(value):
    return is_list_variable(value) and \
        _LIST_VARIABLE_SUBITEM_END_MATCHER.search(value)


def is_dict_var_access(value):
    return is_dict_variable(value) and \
        _DICT_VARIABLE_SUBITEM_END_MATCHER.search(value)


def get_variable(value):
    """Returns variables name without equal sign '=' and indexing '[2]'
    or None
    """
    match = is_variable(value)
    return match.groups()[0] if match else None


def get_variable_basename(value):
    """Return variable without extended variable syntax part"""
    if is_list_variable(value) or is_dict_variable(value):
        return get_variable(value)
    match = re.match(r"\${(.+?)[^\s\w-]+.*}?", value)
    if not match:
        return None
    return '${%s}' % (match.groups()[0].strip())


def find_variable_basenames(value):
    return [get_variable_basename(var)
            for var in re.findall('[@$&]{[^}]*}', value)]


def contains_scalar_variable(value):
    return bool(_SCALAR_VARIABLE_MATCHER.findall(value))


def value_contains_variable(value, varname):
    return utils.Matcher("*%s*" % varname).match(value)


def find_unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]
