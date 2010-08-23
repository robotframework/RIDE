#  Copyright 2008-2010 Nokia Siemens Networks Oyj
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

import sys
import os
import wx

IS_WINDOWS = os.sep == '\\'
IS_MAC = sys.platform == 'darwin'

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

_REPLACE = {'Cmd': CMD_CHAR,
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
           '-': ''}

def replace_chars_in_mac(shortcut):
    if not IS_MAC or not shortcut:
        return shortcut
    for key, value in _REPLACE.items():
        shortcut = shortcut.replace(key, value)
    return shortcut

def ctrl_or_cmd():
    if IS_MAC:
        return wx.ACCEL_CMD
    return wx.ACCEL_CTRL

def only_once(f):
    '''Decorator that stops event handlers from being 
    called several times in some OSX versions.'''
    _events = set()
    def new(obj, *args):
        id = args[0].Id
        if id in _events:
            return
        _events.add(id)
        return f(obj, *args)
    return new