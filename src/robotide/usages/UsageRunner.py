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

from robotide.usages.commands import FindUsages, FindResourceUsages, FindVariableUsages
from robotide.usages.usagesdialog import UsagesDialog, UsagesDialogWithUserKwNavigation, ResourceImportUsageDialog
from threading import Thread
import wx
import time

class Usages(object):

    def __init__(self, controller, highlight, name=None, kw_info=None):
        self._name = name or controller.name
        self._kw_info = kw_info
        self._controller = controller
        self._highlight = highlight
        self._dlg = self._usages_dialog()
        self._worker = Thread(target=self._run)
        self._dialog_closed = False

    def _usages_dialog(self):
        if self._controller.name == self._name:
            return UsagesDialogWithUserKwNavigation(self._name, self._highlight, self._controller)
        return UsagesDialog(self._name)

    def show(self):
        self._dlg.add_selection_listener(self._highlight)
        self._dlg.Bind(wx.EVT_CLOSE, self._stop)
        self._dlg.Show()
        self._worker.start()

    def _run(self):
        wx.CallAfter(self._begin_search)
        for usage in self._find_usages():
            time.sleep(0) # GIVE SPACE TO OTHER THREADS -- Thread.yield in Java
            if self._dialog_closed: return
            wx.CallAfter(self._add_usage, usage)
        wx.CallAfter(self._end_search)

    def _find_usages(self):
        return self._controller.execute(FindUsages(self._name, self._kw_info))

    def _begin_search(self):
        if not self._dialog_closed:
            self._dlg.begin_searching()

    def _add_usage(self, usage):
        if not self._dialog_closed:
            self._dlg.add_usage(usage)

    def _end_search(self):
        if not self._dialog_closed:
            self._dlg.end_searching()

    def _stop(self, event):
        self._dialog_closed = True
        event.Skip()


class ResourceFileUsages(Usages):

    def __init__(self, controller, highlight):
        Usages.__init__(self, controller, highlight)

    def _usages_dialog(self):
        return ResourceImportUsageDialog(self._controller.display_name,
                                         self._highlight,
                                         self._controller)

    def _find_usages(self):
        return self._controller.execute(FindResourceUsages())


class VariableUsages(Usages):

    def _find_usages(self):
        return self._controller.execute(FindVariableUsages(self._name))
