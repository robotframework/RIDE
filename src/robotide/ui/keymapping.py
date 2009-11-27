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


def parse_shortcut(shortcut):
    keys = shortcut.replace('+', '-').split('-')
    if len(keys) == 1:
        flags = wx.ACCEL_NORMAL
    else:
        flags = sum(_get_wx_key_constant('ACCEL', key) for key in keys[:-1])
    return flags, _get_key(keys[-1])

def _get_key(key):
    if len(key) == 1:
        return ord(key.upper())
    key = {'Del': 'Delete', 'Ins': 'Insert',
           'Enter': 'Return', 'Esc':'Escape'}.get(key.title(), key)
    return _get_wx_key_constant('WXK', key)

def _get_wx_key_constant(prefix, name):
    attr = '%s_%s' % (prefix, name.upper().replace(' ', ''))
    try:
        return getattr(wx, attr)
    except AttributeError:
        raise ValueError('Invalid shortcut key: %s' % name)
