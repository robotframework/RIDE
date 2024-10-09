#  Copyright 2024-     Robot Framework Foundation
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
import builtins
import subprocess
import sys

import psutil
import wx

from .updatenotifier import _askyesno

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

SPC = "  "


def restart_dialog():
    if not _askyesno(_("Re-open RIDE for Language Change"),
            f"{SPC}{_('Language change will only be correct after re-opening RIDE.')}"
            f"{SPC}\n{SPC}{_('Do you want to CLOSE RIDE now?')}\n{SPC}"
            # f"{_('After restarting RIDE you will see another dialog informing to close this RIDE instance.')}"
            f"{SPC}\n", wx.GetTopLevelWindows()[0], no_default=True):
        return False
    else:
        # do_restart()
        return True


def do_restart():
    my_pid = psutil.Process()
    # DEBUG: The starting of new RIDE instance with subsequent closing of this instance,
    # makes problems in editing the current file, and even opening new file. Because of
    # this, the restarting was disabled, until someone finds a good way to clean-up memory.
    command = sys.executable + " -m robotide.__init__ --noupdatecheck"
    wx.CallLater(500, subprocess.Popen, command.split(' '), start_new_session=True)
    result = _askyesno(_("Completed Language Change"),
                       f"\n{SPC}{_('You should close this RIDE (Process ID = ')}{my_pid.pid}){SPC}"
                       f"\n{SPC}{_('Do you want to CLOSE RIDE now?')}\n{SPC}",
                       wx.GetActiveWindow())
    if result:
        wx.CallLater(1000, wx.App.Get().GetTopWindow().Close)
        return True
