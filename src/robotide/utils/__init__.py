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

import os
import re
import sys
import inspect
import subprocess

import robotide.lib.robot.utils
from robotide.lib.robot.utils.encoding import SYSTEM_ENCODING
from robotide.lib.robot.utils import printable_name, normalize, _normalize, eq, ET, \
    HtmlWriter, NormalizedDict, timestr_to_secs, secs_to_timestr, normpath,\
    unic, asserts, unescape, html_escape, attribute_escape, robottime,\
    get_timestamp, Matcher, is_list_like, is_dict_like, system_decode,\
    ArgumentParser, get_error_details, is_unicode, is_string, py2to3
from .eventhandler import RideFSWatcherHandler
from .printing import Printing


def html_format(text):
    return robotide.lib.robot.utils.html_format(text)


def name_from_class(item, drop=None):
    cls = inspect.isclass(item) and item or item.__class__
    name = cls.__name__
    if drop and name.endswith(drop):
        name = name[:-len(drop)]
    return printable_name(name, code_style=True)


def split_value(value, sep='|'):
    if not value:
        return []
    return [v.strip() for v in _split_value(value, sep)]


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
    return joiner.join([v.replace(sep, '\\' + sep) for v in value])


def find_from_pythonpath(name):
    for dirpath in sys.path:
        if not os.path.isdir(dirpath):
            continue
        path = os.path.join(dirpath, name)
        if os.path.isfile(path):
            return path
    return None


def replace_extension(path, new_extension):
    base = path.rsplit('.', 1)
    return '%s.%s' % (base[0], new_extension.lower())


def overrides(interface_class):
    # type: (object) -> object
    """
    A decorator that can be used to validate method override

    http://stackoverflow.com/questions/1167617/in-python-how-do-i-indicate-im-overriding-a-method/8313042#8313042
    """
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider


def is_same_drive(path1, path2):
    return os.path.splitdrive(path1)[0].lower() == \
        os.path.splitdrive(path2)[0].lower()


def run_python_command(command, mode='c'):
    cmd = [sys.executable, '-{0}'.format(mode)] + command
    # DEBUG: Let the user select which robot to use
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    output, _ = process.communicate()
    return output


def converttypes(data, prefer_str=True):
    """
    Convert all types from Python2 to Python3
    """
    enc = sys.stdout and sys.stdout.encoding or "utf-8"
    data_type = type(data)

    if data_type == bytes:
        if prefer_str:
            return str(data.decode(enc))
        return data.decode(enc)
    if data_type in (str, int):
        return str(data)

    if data_type == dict:
        data = data.items()
    return data_type(map(converttypes, data))


_regexps = (re.compile(r'(\\+)r\\n'),
            re.compile(r'(\\+)n'),
            re.compile(r'(\\+)r'),
            re.compile(r'(\\+) '))


def unescape_newlines_and_whitespaces(item):
    for regexp in _regexps:
        if regexp.pattern.endswith(' '):
            item = regexp.sub(_whitespace_replacer, item)
        else:
            item = regexp.sub(_newline_replacer, item)
    return item


def _whitespace_replacer(match):
    return _replacer(' ', match)


def _newline_replacer(match):
    return _replacer(os.linesep, match)


def _replacer(char, match):
    slashes = len(match.group(1))
    if slashes % 2 == 1:
        return '\\' * (slashes - 1) + char
    return match.group()


def normalize_lc(string, remove='', spaces=True):
    string = string.lower()
    if spaces:
        remove = remove + ' '
    for char in remove:
        if char in string:
            string = string.replace(char, '')
    return string


def normalize_dict(table: dict) -> dict:
    ndict = {}
    for key, value in table.items():
        if key:
            k = normalize_lc(key)
            v = normalize_lc(value)
            ndict[k] = v
    return ndict


def normalize_pipe_list(data: list, spaces: bool = True) -> str:
    pipe_list = "|".join(data)
    return normalize_lc(pipe_list, spaces=spaces)

