#  Copyright 2008-2015 Nokia Solutions and Networks
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
import wx

IS_WINDOWS = os.sep == '\\'
IS_MAC = sys.platform == 'darwin'
WX_VERSION = wx.VERSION_STRING


def ctrl_or_cmd():
    if IS_MAC:
        return wx.ACCEL_CMD
    return wx.ACCEL_CTRL

def bind_keys_to_evt_menu(target, actions):
    accelrators = []
    for accel, keycode, handler in actions:
        id = wx.NewId()
        target.Bind(wx.EVT_MENU, handler, id=id)
        accelrators.append((accel, keycode, id))
    target.SetAcceleratorTable(wx.AcceleratorTable(accelrators))
