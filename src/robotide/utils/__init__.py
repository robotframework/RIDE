#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
import sys
import inspect

from robot.utils import printable_name, normalize, eq, ET, \
    HtmlWriter, NormalizedDict, timestr_to_secs, secs_to_timestr, normpath,\
    unic, asserts, unescape, html_attr_escape,\
    get_timestamp
from eventhandler import RideEventHandler
from variablematcher import is_variable, is_scalar_variable, is_list_variable, \
    get_variable, get_variable_basename, find_variable_basenames, \
    value_contains_variable
from highlightmatcher import highlight_matcher
from printing import Printing
from htmlutils import html_escape

def name_from_class(item, drop=None):
    cls = inspect.isclass(item) and item or item.__class__
    name = cls.__name__
    if drop and name.endswith(drop):
        name = name[:-len(drop)]
    return printable_name(name, code_style=True)


def split_value(value, sep='|'):
    if not value:
        return []
    return [ v.strip() for v in _split_value(value, sep) ]

def _split_value(value, sep):
    if '\\' not in value:
        return value.split(sep)
    ret = []
    catenate_next = False
    for item in value.split(sep):
        bslash_count = len(item) - len(item.rstrip('\\'))
        escaped = bslash_count % 2 == 1
        if escaped:
            item = item[:-1]
        if catenate_next:
            ret[-1] += sep + item
        else:
            ret.append(item)
        catenate_next = escaped
    return ret


def join_value(value, sep='|', joiner=None):
    if not joiner:
        joiner = ' %s ' % sep
    return joiner.join([ v.replace(sep, '\\'+sep) for v in value ])


def find_from_pythonpath(name):
    for dirpath in sys.path:
        if not os.path.isdir(dirpath):
            continue
        path = os.path.join(dirpath, name)
        if os.path.isfile(path):
            return path
    return None


def replace_extension(path, new_extension):
    base = os.path.splitext(path)[0]
    return '%s.%s' % (base, new_extension.lower())
