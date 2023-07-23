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

import wx

from ..controller.ctrlcommands import DeleteResourceAndImports, DeleteFile, DeleteFolder, DeleteFolderAndImports
from ..usages.commands import FindResourceUsages, FindTestFolderUsages
from ..usages.usagesdialog import ResourceImportListModel, RecursiveResourceImportListModel
from ..widgets import RIDEDialog, VirtualList, VerticalSizer, Label


class _UsageDialog(RIDEDialog):
    _width = 650
    _height = 250

    def __init__(self, usages, title, checkbox_label, model=ResourceImportListModel):
        RIDEDialog.__init__(self, title, size=(self._width, self._height))
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self._sizer = VerticalSizer()
        self._create_controls(usages, checkbox_label, model)
        self._create_horizontal_line(self._sizer)
        self._create_buttons(self._sizer)
        self.SetSizer(self._sizer)

    def _create_controls(self, usages, checkbox_label, model):
        self._sizer.add_with_padding(Label(self, label="Usages:"))
        model = model(usages)
        self._sizer.add_expanding(VirtualList(self, model.headers, model))
        self._add_usages_modifying_help(usages)
        self._checkbox = wx.CheckBox(self, label=checkbox_label)
        self._checkbox.SetValue(True)
        self._sizer.add_with_padding(self._checkbox)

    def _add_usages_modifying_help(self, usages):
        if any(u for u in usages if not u.can_be_renamed):
            hhelp = Label(self,
                          label='Highlighted imports are not modified because they contain variables in resource file'
                                ' name.')
            hhelp.Wrap(self._width)
            hhelp.SetForegroundColour('red')
            self._sizer.add_with_padding(hhelp)

    def show(self):
        confirmed = self.ShowModal() == wx.ID_OK
        return confirmed, self._checkbox.IsChecked()


class _FolderUsageDialog(_UsageDialog):

    def __init__(self, usages, title, checkbox_label):
        _UsageDialog.__init__(self, usages, title, checkbox_label)


class ResourceRenameDialog(object):
    def __init__(self, controller):
        self._rename_confirmed = True
        self._rename_usage = False
        title = 'Rename resource'
        checkbox_label = 'Also update resource imports'

        usages = list(controller.execute(FindResourceUsages()))
        if usages:
            self._rename_confirmed, self._rename_usage = _UsageDialog(usages, title, checkbox_label).show()

    def execute(self):
        return self._rename_confirmed and self._rename_usage


class ResourceDeleteDialog(object):
    def __init__(self, controller):
        self._delete_confirmed = False
        self._delete_usage = False
        self._controller = controller
        title = 'Delete resource'
        checkbox_label = 'Also delete resource imports'

        usages = list(controller.execute(FindResourceUsages()))
        self._delete_confirmed, self._delete_usage = _UsageDialog(usages, title, checkbox_label).show()

    def execute(self):
        if self._delete_confirmed:
            if self._delete_usage:
                self._controller.execute(DeleteResourceAndImports())
            else:
                self._controller.execute(DeleteFile())


class FolderDeleteDialog(object):
    def __init__(self, controller):
        self._delete_confirmed = False
        self._delete_usage = False
        self._controller = controller
        title = 'Delete test data folder'
        checkbox_label = 'Also delete resource imports'

        usages = list(controller.execute(FindTestFolderUsages()))
        self._delete_confirmed, self._delete_usage = _UsageDialog(usages, title, checkbox_label,
                                                                  RecursiveResourceImportListModel).show()

    def execute(self):
        if self._delete_confirmed:
            if self._delete_usage:
                self._controller.execute(DeleteFolderAndImports())
            else:
                self._controller.execute(DeleteFolder())
