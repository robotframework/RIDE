#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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

from robotide.controller.commands import DeleteResourceAndImports, DeleteFile
from robotide.usages.commands import FindResourceUsages
from robotide.usages.usagesdialog import ResourceImportListModel
from robotide.widgets import Dialog, VirtualList, VerticalSizer, Label


class _ConfirmationWithCheckbox(Dialog):
    _width = 650
    _height = 250

    def __init__(self, controller):
        Dialog.__init__(self, self._title, size=(self._width, self._height))
        self._controller = controller
        self._sizer = VerticalSizer()
        self._create_controls()
        self._create_horizontal_line(self._sizer)
        self._create_buttons(self._sizer)
        self.SetSizer(self._sizer)

    def _create_controls(self):
        self._show_usages()
        self._checkbox = wx.CheckBox(self, label=self._checkbox_label)
        self._checkbox.SetValue(True)
        self._sizer.add_with_padding(self._checkbox)

    def _show_usages(self):
        usages = list(self._controller.execute(FindResourceUsages()))
        if usages:
            self._sizer.add_with_padding(Label(self, label="Usages:"))
            model = ResourceImportListModel(usages)
            self._sizer.add_expanding(VirtualList(self, model.headers, model))
            self._add_usages_modifying_help(usages)

    def _add_usages_modifying_help(self, usages):
        if any(u for u in usages if not u.can_be_renamed):
            help = Label(self,
                label='Highlighted imports are not modified because they '
                      'contain variables in resource file name.')
            help.Wrap(self._width)
            help.SetForegroundColour('red')
            self._sizer.add_with_padding(help)


class ResourceRenameDialog(_ConfirmationWithCheckbox):
    _title = 'Rename resource'
    _checkbox_label = 'Also update resource imports'

    def __init__(self, controller):
        _ConfirmationWithCheckbox.__init__(self, controller)

    def _execute(self):
        return self._checkbox.IsChecked()


class ResourceDeleteDialog(_ConfirmationWithCheckbox):
    _title = 'Delete resource'
    _checkbox_label = 'Also delete resource imports'

    def __init__(self, controller):
        _ConfirmationWithCheckbox.__init__(self, controller)

    def _execute(self):
        if self._checkbox.IsChecked():
            self._controller.execute(DeleteResourceAndImports())
        else:
            self._controller.execute(DeleteFile())
