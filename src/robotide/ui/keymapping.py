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

import wx
from robotide.robotapi import NormalizedDict


KEY_MAPPINGS = NormalizedDict({'DEL': wx.WXK_DELETE,
                'INS': wx.WXK_INSERT,
                'ENTER': wx.WXK_RETURN,
                'PGUP': wx.WXK_PAGEUP,
                'PGDN': wx.WXK_PAGEDOWN,
                'ESC': wx.WXK_ESCAPE,
                })

CTRL_KEY_MAPPINGS = NormalizedDict({
                    'Ctrl': wx.ACCEL_CTRL,
                    'Shift': wx.ACCEL_SHIFT,
                    'Cmd': wx.ACCEL_CMD,
                    'Alt': wx.ACCEL_ALT})

def parse_shortcut(shortcut):
    keys = shortcut.split('-')
    if len(keys) == 1:
        flags = wx.ACCEL_NORMAL
    else:
        flags = sum(CTRL_KEY_MAPPINGS[key] for key in keys[:-1])
    return flags, _get_key(keys[-1])

def _get_key(key):
    if key in KEY_MAPPINGS:
        return KEY_MAPPINGS[key]
    name = 'WXK_%s' % (key.upper())
    if hasattr(wx, name):
        return getattr(wx, name)
    if len(key) == 1:
        return ord(key)
    raise AttributeError("Invalid key '%s'" % (key))
