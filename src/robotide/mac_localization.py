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

CMD_CHAR = u'\u2318'
SHIFT_CHAR = u'\u21E7'
OPTION_CHAR = u'\u2325'
CTRL_CHAR = u'\u2303'
SPACE_CHAR = u'\u2423'
LEFT_CHAR = u'\u2190'
RIGHT_CHAR = u'\u2192'
DEL_CHAR = u'\u232B'

REPLACE = {'Cmd': CMD_CHAR,
           'Shift': SHIFT_CHAR,
           'Alt': OPTION_CHAR,
           'Ctrl': CTRL_CHAR,
           'Space': SPACE_CHAR,
           'Left': LEFT_CHAR,
           'Right': RIGHT_CHAR,
           'Delete': DEL_CHAR,
           '-': ''}

def replace_chars_in_mac(shortcut):
    if not is_mac() or not shortcut:
        return shortcut
    for key, value in REPLACE.items():
        shortcut = shortcut.replace(key, value)
    return shortcut


def is_mac():
    return sys.platform == 'darwin'

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