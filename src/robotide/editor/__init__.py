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

from .editorcreator import EditorCreator
from ..pluginapi import (Plugin, action_info_collection, TreeAwarePluginMixin)
from ..publish import (RideTreeSelection, RideNotebookTabChanging, RideNotebookTabChanged, RideSaving)
from ..publish.messages import RideDataFileRemoved
from ..widgets import PopupCreator

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


def get_menudata():
    # Menus to translate
    edit_0 = _("[Edit]\n")
    edit_1 = _("&Undo | Undo last modification | Ctrlcmd-Z\n")
    edit_2 = _("&Redo | Redo modification | Ctrlcmd-Y\n")
    SEPARATOR = "---\n"
    edit_3 = _("Cu&t | Cut | Ctrlcmd-X\n")
    edit_4 = _("&Copy | Copy | Ctrlcmd-C\n")
    edit_5 = _("&Paste | Paste | Ctrlcmd-V\n")
    edit_6 = _("&Insert | Insert | Shift-Ctrl-V\n")
    edit_7 = _("&Delete | Delete  | Del\n")
    edit_8 = _("Comment Rows | Comment selected rows | Ctrlcmd-3\n")
    edit_9 = _("Comment Cells | Comment cells with # | Ctrlcmd-Shift-3\n")
    edit_10 = _("Uncomment Rows | Uncomment selected rows | Ctrlcmd-4\n")
    edit_11 = _("Uncomment Cells | Uncomment cells with # | Ctrlcmd-Shift-4\n")
    edit_12 = _("Insert Cells | Insert Cells | Ctrlcmd-Shift-I\n")
    edit_13 = _("Delete Cells | Delete Cells | Ctrlcmd-Shift-D\n")
    edit_14 = _("Insert Rows | Insert Rows | Ctrlcmd-I\n")
    edit_15 = _("Delete Rows | Delete Rows | Ctrlcmd-D\n")
    edit_16 = _("Move Rows Up | Move Rows Up | Alt-Up\n")
    edit_17 = _("Move Rows Down | Move Rows Down | Alt-Down\n")
    tools_0 = _("[Tools]\n")
    tools_1 = _("Content Assistance (Ctrl-Space or Ctrl-Alt-Space) | Show possible keyword and variable completions"
                " | | | POSITION-70\n")

    return (edit_0 + edit_1 + edit_2 + SEPARATOR + edit_3 + edit_4 + edit_5 + edit_6 + edit_7 + SEPARATOR +
            edit_8 + edit_9 + edit_10 + edit_11 + SEPARATOR + edit_12 + edit_13 + edit_14 + edit_15 + edit_16 +
            edit_17 + tools_0 + tools_1)


_EDIT_nt = """[Edit]
&Undo | Undo last modification | Ctrlcmd-Z
&Redo | Redo modification | Ctrlcmd-Y
---
Cu&t | Cut | Ctrlcmd-X
&Copy | Copy | Ctrlcmd-C
&Paste | Paste | Ctrlcmd-V
&Insert | Insert | Shift-Ctrl-V
&Delete | Delete  | Del
---
Comment Rows | Comment selected rows | Ctrlcmd-3
Comment Cells | Comment cells with # | Ctrlcmd-Shift-3
Uncomment Rows | Uncomment selected rows | Ctrlcmd-4
Uncomment Cells | Uncomment cells with # | Ctrlcmd-Shift-4
---
Insert Cells | Insert Cells | Ctrlcmd-Shift-I
Delete Cells | Delete Cells | Ctrlcmd-Shift-D
Insert Rows | Insert Rows | Ctrlcmd-I
Delete Rows | Delete Rows | Ctrlcmd-D
Move Rows Up | Move Rows Up | Alt-Up
Move Rows Down | Move Rows Down | Alt-Down
[Tools]
Content Assistance (Ctrl-Space or Ctrl-Alt-Space) | Show possible keyword and variable completions | | | POSITION-70
"""


class EditorPlugin(Plugin, TreeAwarePluginMixin):

    def __init__(self, application):
        self.__doc__ = _("""The default editor plugin. Also known as Grid or Cell Editor.

    This plugin implements editors for the various items of Robot Framework
    test data.
    """)
        Plugin.__init__(self, application, name='Editor')
        self._tab = None
        self.name = _('Editor')
        self.grid_popup_creator = PopupCreator()
        self._creator = EditorCreator(self.register_editor)
        self._editor = None

    def enable(self):
        self._creator.register_editors()
        self._show_editor()
        _menudata = get_menudata()
        self.register_actions(action_info_collection(_menudata, self._tab, data_nt=_EDIT_nt, container=self._tab))
        self.subscribe(self.on_tree_item_selected, RideTreeSelection)
        self.subscribe(self.on_tab_changed, RideNotebookTabChanged)
        self.subscribe(self.on_tab_changing, RideNotebookTabChanging)
        self.subscribe(self.on_save_to_model, RideSaving)
        self.subscribe(self.on_file_deleted, RideDataFileRemoved)
        self.add_self_as_tree_aware_plugin()

    def disable(self):
        self.remove_self_from_tree_aware_plugins()
        self.unsubscribe_all()
        self.delete_tab(self._tab)
        wx.CallLater(500, self.unregister_actions())
        self._tab = None
        self._editor = None

    def is_focused(self):
        return self.tab_is_visible(self._tab)

    def highlight_cell(self, obj, row, column):
        self.show()
        self._editor.highlight_cell(obj, row, column)

    def highlight(self, text):
        self.show()
        self._editor.highlight(text)

    def show(self):
        self.show_tab(self._tab)

    def register_context_menu_hook_to_grid(self, hook):
        """ Used to register own items to grid's right click context menu

        hook is called with current selection (list of list containing
        values) and it is expected to return list of PopupMenuItem.
        If user selects one of the returned PopupMenuItem, related function
        is called with one argument, the wx event.
        """
        self.grid_popup_creator.add_hook(hook)

    def unregister_context_menu_hook_to_grid(self, hook):
        self.grid_popup_creator.remove_hook(hook)

    def _show_editor(self):
        if not self._tab:
            self._tab = _EditorTab(self)
            self.add_tab(self._tab, self._tab.plugin.name, allow_closing=False)
        if self.is_focused():
            self._editor = self._create_editor()
            self._tab.show_editor(self._editor)

    def _create_editor(self):
        return self._creator.editor_for(self, self._tab, self.tree)

    def on_tree_item_selected(self, message):
        self._show_editor()
        if not self.is_focused() and \
           not self.is_focus_on_tree_aware_plugin() and \
           (not message or not message.silent):
            self._editor = self._create_editor()
            self._tab.show_editor(self._editor)
            self.show()
        if self._editor:
            self._editor.tree_item_selected(message.item)

    def get_selected_datafile(self):
        if self._editor and self._editor.controller:
            return self._editor.controller.datafile
        return Plugin.get_selected_datafile(self)

    def on_open_editor(self, event):
        __ = event
        self._show_editor()

    def on_tab_changed(self, message):
        __ = message
        self._show_editor()

    def on_tab_changing(self, message):
        if 'Editor' in message.oldtab:
            self._tab.save()

    def on_save_to_model(self, message):
        __ = message
        if self._tab:
            self._tab.save()

    def on_file_deleted(self, message):
        __ = message
        self._create_editor()


class _EditorTab(wx.Panel):

    def __init__(self, plugin):
        wx.Panel.__init__(self, plugin.notebook, style=wx.SUNKEN_BORDER)
        self.plugin = plugin
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        """
        self.SetBackgroundColour(Colour(200, 222, 40))
        self.SetOwnBackgroundColour(Colour(200, 222, 40))
        self.SetForegroundColour(Colour(7, 0, 70))
        self.SetOwnForegroundColour(Colour(7, 0, 70))
        """
        self.Refresh(True)
        self.editor = None

    def show_editor(self, editor):
        if editor is None:
            return
        if editor is self.editor:
            self.Show(True)
            return
        self.sizer.Clear()
        self.editor = editor
        self.sizer.Add(self.editor, 1, wx.ALL | wx.EXPAND)
        self.Layout()
        self.Show(True)

    def hide_editor(self):
        self.Show(False)

    def on_save(self, event):
        __ = event
        self.plugin.save_selected_datafile()

    def on_undo(self, event):
        __ = event
        self.editor.undo()

    def on_redo(self, event):
        __ = event
        self.editor.redo()

    def on_cut(self, event):
        __ = event
        self.editor.cut()

    def on_copy(self, event):
        __ = event
        self.editor.copy()

    def on_paste(self, event):
        __ = event
        self.editor.paste()

    def on_insert(self, event):
        __ = event
        self.editor.insert()

    def on_insert_cells(self, event):
        __ = event
        self.editor.insert_cells()

    def on_delete_cells(self, event):
        __ = event
        # print("DEBUG init delete cells call")
        self.editor.delete_cells()

    def on_insert_rows(self, event):
        __ = event
        self.editor.insert_rows()

    def on_delete_rows(self, event):
        __ = event
        wx.CallAfter(self.editor.delete_rows)

    def on_move_rows_up(self, event):
        __ = event
        self.editor.on_move_rows_up()

    def on_move_rows_down(self, event):
        __ = event
        self.editor.on_move_rows_down()

    def on_delete(self, event):
        __ = event
        self.editor.delete()

    def on_comment_rows(self, event):
        __ = event
        self.editor.comment_rows()

    def on_uncomment_rows(self, event):
        __ = event
        self.editor.uncomment_rows()

    def on_sharp_comment_rows(self, event):
        __ = event
        self.editor.sharp_comment_rows()

    def on_sharp_uncomment_rows(self, event):
        __ = event
        self.editor.sharp_uncomment_rows()

    def on_comment_cells(self, event):
        __ = event
        self.editor.comment_cells()

    def on_uncomment_cells(self, event):
        __ = event
        self.editor.uncomment_cells()

    def on_content_assistance(self, event):
        __ = event
        self.editor.show_content_assist()

    def save(self, message=None):
        __ = message
        if self.editor:
            self.editor.save()

    def on_key(self, *args):
        """ Intentional override """
        pass
