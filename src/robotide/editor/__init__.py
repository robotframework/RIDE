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

from robotide.publish.messages import RideDataFileRemoved
from robotide.pluginapi import (
    Plugin, ActionInfoCollection, TreeAwarePluginMixin)
from robotide.publish import (
    RideTreeSelection, RideNotebookTabChanging, RideNotebookTabChanged,
    RideSaving)
from robotide.utils import overrides
from robotide.widgets import PopupCreator
from .editorcreator import EditorCreator


_EDIT = """
[Edit]
&Undo | Undo last modification | Ctrlcmd-Z
&Redo | Redo modification | Ctrlcmd-Y
---
Cu&t | Cut | Ctrlcmd-X
&Copy | Copy | Ctrlcmd-C
&Paste | Paste | Ctrlcmd-V
&Insert | Insert | Shift-Ctrl-V
&Delete | Delete  | Del
---
Comment | Comment selected rows | Ctrlcmd-3
Uncomment | Uncomment selected rows | Ctrlcmd-4
---
Insert Cells | Insert Cells | Shift-Ctrl-I
Delete Cells | Delete Cells | Shift-Ctrl-D
Insert Rows | Insert Rows | Ctrlcmd-I
Delete Rows | Delete Rows | Ctrlcmd-D
[Tools]
Content Assistance (Ctrl-Space or Ctrl-Alt-Space) | Show possible keyword and variable completions | | | POSITION-70
"""


class EditorPlugin(Plugin, TreeAwarePluginMixin):
    """The default editor plugin.

    This plugin implements editors for the various items of Robot Framework
    test data.
    """
    def __init__(self, application):
        Plugin.__init__(self, application)
        self._tab = None
        self._grid_popup_creator = PopupCreator()
        self._creator = EditorCreator(self.register_editor)
        self._editor = None

    def enable(self):
        self._creator.register_editors()
        self._show_editor()
        self.register_actions(
            ActionInfoCollection(_EDIT, self._tab, self._tab))
        self.subscribe(self.OnTreeItemSelected, RideTreeSelection)
        self.subscribe(self.OnTabChanged, RideNotebookTabChanged)
        self.subscribe(self.OnTabChanging, RideNotebookTabChanging)
        self.subscribe(self.OnSaveToModel, RideSaving)
        self.subscribe(self.OnFileDeleted, RideDataFileRemoved)
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
        self._grid_popup_creator.add_hook(hook)

    def unregister_context_menu_hook_to_grid(self, hook):
        self._grid_popup_creator.remove_hook(hook)

    def _show_editor(self):
        if not self._tab:
            self._tab = _EditorTab(self)
            self.add_tab(self._tab, 'Edit', allow_closing=False)
        if self.is_focused():
            self._editor = self._create_editor()
            self._tab.show_editor(self._editor)

    def _create_editor(self):
        return self._creator.editor_for(self, self._tab, self.tree)

    def OnTreeItemSelected(self, message=None):
        self._show_editor()
        if not self.is_focused() and \
           not self.is_focus_on_tree_aware_plugin() and \
           (not message or not message.silent):
            self._editor = self._create_editor()
            self._tab.show_editor(self._editor)
            self.show()
        if self._editor:
            self._editor.tree_item_selected(message.item)

    @overrides(Plugin)
    def get_selected_datafile(self):
        if self._editor and self._editor.controller:
            return self._editor.controller.datafile
        return Plugin.get_selected_datafile(self)

    def OnOpenEditor(self, event):
        self._show_editor()

    def OnTabChanged(self, event):
        self._show_editor()

    def OnTabChanging(self, message):
        if 'Edit' in message.oldtab:
            self._tab.save()

    def OnSaveToModel(self, message):
        if self._tab:
            self._tab.save()

    def OnFileDeleted(self, message):
        self._create_editor()


class _EditorTab(wx.Panel):

    def __init__(self, plugin):
        wx.Panel.__init__(self, plugin.notebook, style=wx.SUNKEN_BORDER)
        self.plugin = plugin
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
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

    def OnSave(self, event):
        self.plugin.save_selected_datafile()

    def OnUndo(self, event):
        self.editor.undo()

    def OnRedo(self, event):
        self.editor.redo()

    def OnCut(self, event):
        self.editor.cut()

    def OnCopy(self, event):
        self.editor.copy()

    def OnPaste(self, event):
        self.editor.paste()

    def OnInsert(self, event):
        self.editor.insert()

    def OnInsertCells(self, event):
        self.editor.insert_cells()

    def OnDeleteCells(self, event):
        # print("DEBUG init delete cells call")
        self.editor.delete_cells()

    def OnInsertRows(self, event):
        self.editor.insert_rows()

    def OnDeleteRows(self, event):
        wx.CallAfter(self.editor.delete_rows)

    def OnDelete(self, event):
        self.editor.delete()

    def OnComment(self, event):
        self.editor.comment()

    def OnUncomment(self, event):
        self.editor.uncomment()

    def OnContentAssistance(self, event):
        self.editor.show_content_assist()

    def save(self, message=None):
        if self.editor:
            self.editor.save()

    def OnKey(self, *args):
        pass
