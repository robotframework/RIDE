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

from functools import total_ordering

import wx

from ..context import IS_MAC

CMD_CHAR = u'\u2318'
SHIFT_CHAR = u'\u21E7'
OPTION_CHAR = u'\u2325'
CTRL_CHAR = u'\u2303'
SPACE_CHAR = u'\u2423'
LEFT_CHAR = u'\u2190'
RIGHT_CHAR = u'\u2192'
DEL_CHAR = u'\u2326'
ENTER_CHAR = u'\u2324'
RETURN_CHAR = u'\u21A9'
ESC_CHAR = u'\u238B'
UP_CHAR = u'\u2191'
DOWN_CHAR = u'\u2193'

_REPLACE = {
    'Cmd': CMD_CHAR,
    'Shift': SHIFT_CHAR,
    'Alt': OPTION_CHAR,
    'Ctrl': CTRL_CHAR,
    'Space': SPACE_CHAR,
    'Left': LEFT_CHAR,
    'Right': RIGHT_CHAR,
    'Delete': DEL_CHAR,
    'Enter': ENTER_CHAR,
    'Return': RETURN_CHAR,
    'Escape': ESC_CHAR,
    '-': '',
    'Up': UP_CHAR,
    'Down': DOWN_CHAR
}


def localize_shortcuts(string):
    if IS_MAC:
        string = string.replace('CtrlCmd', 'Cmd')
    else:
        string = string.replace('CtrlCmd', 'Ctrl')
    return _replace_mac_chars(string)


def _replace_mac_chars(string):
    if not IS_MAC or not string:
        return string
    for key, value in _REPLACE.items():
        string = string.replace(key, value)
    return string


@total_ordering
class Shortcut(object):

    def __init__(self, shortcut):
        self.value = self._normalize(shortcut)
        self.printable = self._get_printable(self.value)

    def _get_printable(self, value):
        return self._replace_chars_in_mac(value)

    def _replace_chars_in_mac(self, shortcut):
        return _replace_mac_chars(shortcut)

    def __nonzero__(self):
        return bool(self.value)

    def _normalize(self, shortcut):
        if not shortcut:
            return None
        order = ['Shift', 'Ctrl', 'Cmd', 'Alt']
        keys = [self._normalize_key(key) for key in self._split(shortcut)]
        try:  # DEBUG only in python3 ??
            keys.index('')
            keys.pop()
            return None
        except ValueError:
            pass
        keys.sort(key=lambda t: t in order and order.index(t) or 42)
        return '-'.join(keys)

    def _split(self, shortcut):
        try:
            m_str=shortcut.replace('+', '-').split('-')
            # print("DEBUG: Shortcut %s" % m_str)
            return m_str
        except AttributeError:  # DEBUG On python 3 there are NoneType
            pass
        return ''

    def _normalize_key(self, key):
        key = key.title()
        key = self._handle_ctrlcmd(key)
        return {'Del': 'Delete', 'Ins': 'Insert',
                'Enter': 'Return', 'Esc':'Escape'}.get(key, key)

    def _handle_ctrlcmd(self, key):
        if key != 'Ctrlcmd':
            return key
        if IS_MAC:
            return 'Cmd'
        return 'Ctrl'

    def parse(self):
        keys = self._split(self.value)
        if keys:
            # print("DEBUG: parser %s" % keys)
            if len(keys) == 1:
                flags = wx.ACCEL_NORMAL
            else:
                flags = sum(self._get_wx_key_constant('ACCEL', key)
                            for key in keys[:-1])
            return flags, self._get_key(keys[-1])

    def _get_wx_key_constant(self, prefix, name):
        attr = '%s_%s' % (prefix, name.upper().replace(' ', ''))
        try:
            return getattr(wx, attr)
        except AttributeError:
            raise ValueError('Invalid shortcut key: %s' % name)

    def _get_key(self, key):
        if len(key) == 1:
            return ord(key.upper())
        return self._get_wx_key_constant('WXK', self._normalize_key(key))

    def __eq__(self, other):
        return self.name.lower() == other.name.lower()

    def __hash__(self):
        return hash(repr(self))

    def __lt__(self, other):
        return self.name.lower() < other.name.lower()

    def __repr__(self):
        return self.printable
