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

import builtins
import wx
from wx import Colour
from wx.lib.mixins.listctrl import TextEditMixin

from ..editor.listeditor import AutoWidthColumnList, ListEditorBase
from ..widgets import RIDEDialog, HelpLabel, ButtonWithHandler

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

_CONFIG_HELP = _("""The specified command string will be split from whitespaces into a command
and its arguments. If either the command or any of the arguments require
internal spaces, they must be written as '<SPACE>'.\n
The command will be executed in the system directly without opening a shell.
This means that shell commands and extensions are not available. For example,
in Windows batch files to execute must contain the '.bat' extension and 'dir'
command does not work.\n
Examples:
    robot.bat --include smoke C:\\my_tests
    svn update /home/robot
    C:\\Program<SPACE>Files\\App\\prg.exe argument<SPACE>with<SPACE>space,
Run configurations are stored in the RIDE settings file.
""")


class ConfigManagerDialog(RIDEDialog):

    def __init__(self, configs, plugin):
        RIDEDialog.__init__(self, title=_('Manage Run Configurations'))
        # set Left to Right direction (while we don't have localization)

        self.SetBackgroundColour(Colour(self.color_background))
        # self.SetOwnBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        # self.SetOwnForegroundColour(Colour(self.color_foreground))

        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.plugin = plugin
        self._create_ui(configs)

    def _create_ui(self, configs):
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._editor = self._create_editor(configs)
        self._create_help()
        self._create_line()
        self._create_buttons()
        self.SetSize((750, 500))

    def _create_editor(self, configs):
        editor = _ConfigListEditor(self, configs)
        self.Sizer.Add(editor, flag=wx.GROW, proportion=1)
        return editor

    def _create_help(self):
        hhelp = HelpLabel(self, label=_CONFIG_HELP)
        hhelp.Wrap(700)
        self.Sizer.Add(hhelp, border=5, flag=wx.TOP)

    def _create_line(self):
        line = wx.StaticLine(self, size=(20, -1), style=wx.LI_HORIZONTAL)
        if wx.VERSION < (4, 1, 0):
            self.Sizer.Add(line, border=5, flag=wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP)
        else:
            self.Sizer.Add(line, border=5, flag=wx.GROW | wx.RIGHT | wx.TOP)

    def _create_buttons(self, sizer=None):
        buttons = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        for item in self.GetChildren():
            if isinstance(item, (wx.Button, wx.BitmapButton, ButtonWithHandler)):
                item.SetBackgroundColour(Colour(self.color_secondary_background))
                # item.SetOwnBackgroundColour(Colour(self.color_secondary_background))
                item.SetForegroundColour(Colour(self.color_secondary_foreground))
                # item.SetOwnForegroundColour(Colour(self.color_secondary_foreground))
        self.Sizer.Add(buttons, flag=wx.ALIGN_CENTER | wx.ALL, border=5)

    def get_data(self):
        return self._editor.get_data()


class _ConfigListEditor(ListEditorBase):
    _buttons = [_('New'), _('Remove')]
    _buttons_nt = ['New', 'Remove']  # Non-translated names
    _columns = [_('Name'), _('Command'), _('Documentation')]

    def __init__(self, parent, configs):
        self._editor_open = False
        ListEditorBase.__init__(self, parent, self._columns, configs)

    def _create_list(self, columns, data):
        return _TextEditListCtrl(self, columns, color_foreground=self.color_secondary_foreground,
                                 color_background=self.color_secondary_background, data=data)

    @staticmethod
    def get_column_values(config):
        return config.name, config.command, config.doc

    def get_data(self):
        return self._list.get_data()

    def on_edit(self, event):
        self._list.open_editor(self._selection)

    def on_new(self, event):
        __ = event
        self._list.new_item()

    def on_remove(self, event):
        self.on_delete(event)

    def new_config(self, data):
        self._controller.add(*data)

    def edit_config(self, index, data):
        self._controller.edit(index, *data)

    def on_delete(self, event):
        if not self._editor_open:
            ListEditorBase.on_delete(self, event)

    def editor_open(self):
        self._editor_open = True

    def editor_closed(self):
        self._editor_open = False


class _TextEditListCtrl(AutoWidthColumnList, TextEditMixin):
    last_index = property(lambda self: self.ItemCount - 1)

    def __init__(self, parent, columns, color_foreground, color_background, data):
        AutoWidthColumnList.__init__(self, parent, columns, color_foreground=color_foreground,
                                     color_background=color_background, data=data)
        TextEditMixin.__init__(self)

        self.SetBackgroundColour(Colour(color_background))
        self.SetForegroundColour(Colour(color_foreground))

        self._set_command_column_width()
        self.col_locs = self._calculate_col_locs()
        self._new_item_creation = False

    def _set_command_column_width(self):
        self.SetColumnWidth(1, 250)

    def _calculate_col_locs(self):
        """Calculates and returns initial locations of colums.

        This is needed so that TextEditMixin can work from context menu,
        without selecting the row first.
        """
        locations = [0]
        loc = 0
        for n in range(self.GetColumnCount()):
            loc = loc + self.GetColumnWidth(n)
            locations.append(loc)
        return locations

    def open_editor(self, row):
        self.OpenEditor(0, row)

    def OpenEditor(self, col, row):
        self._parent.editor_open()
        TextEditMixin.OpenEditor(self, col, row)

    def new_item(self):
        self._new_item_creation = True
        self.InsertItem(self.ItemCount, '')
        self.Select(self.ItemCount-1, True)
        self.open_editor(self.last_index)

    def get_data(self):
        return [self._get_row(row) for row in range(self.ItemCount)]

    def _get_row(self, row):
        return [self.GetItem(row, col).GetText() for col in range(3)]

    def CloseEditor(self, event=None):
        TextEditMixin.CloseEditor(self, event)
        # It seems that this is called twice per editing action and in the
        # first time the value may be empty.
        # End new item creation only when there really is a value
        lastrow = self._get_row(self.last_index)
        if self._new_item_creation:
            if any(lastrow):
                self._new_item_creation = False
                self.Parent.new_config(lastrow)
        else:
            self.Parent.edit_config(self.curRow, self._get_row(self.curRow))
            self.Select(self.curRow)
        self._parent.editor_closed()
