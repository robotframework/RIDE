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

from robotide.pluginapi import Plugin, ActionInfoCollection
from robotide.publish import RideTreeSelection, RideNotebookTabChanging,\
    RideNotebookTabChanged, RideSaving

from editors import Editor
from gridcolorizer import Colorizer


_EDIT = """
[File]
&Save | Save current suite or resource | Ctrl-S | ART_FILE_SAVE

[Edit]
&Undo | Undo last modification | Ctrl-Z
---
Cu&t | Cut | Ctrl-X
&Copy | Copy | Ctrl-C
&Paste | Paste | Ctrl-V
&Delete | Delete  | Del
---
Comment | Comment selected rows | Ctrl-3
Uncomment | Uncomment selected rows | Ctrl-4

[Tools]
Content Assistance | Show possible keyword and variable completions | Ctrl-Space 
"""


class EditorPlugin(Plugin):

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._tab = None

    def enable(self):
        self._show_editor()
        self.register_actions(ActionInfoCollection(_EDIT, self._tab, self._tab))
        self.subscribe(self.OnTreeItemSelected, RideTreeSelection)
        self.subscribe(self.OnTabChanged, RideNotebookTabChanged)
        self.subscribe(self.OnSaveToModel, RideNotebookTabChanging)
        self.subscribe(self.OnSaveToModel, RideSaving)

    def _show_editor(self):
        if not self._tab:
            self._tab = _EditorTab(self)
            self.add_tab(self._tab, 'Edit', allow_closing=False)
        if self.tab_is_visible(self._tab):
            self._tab.create_editor(self.get_selected_item(), self.tree)

    def disable(self):
        self.unregister_actions()
        self.unsubscribe_all()
        self.delete_tab(self._tab)
        self._tab = None

    def OnTreeItemSelected(self, message):
        self._show_editor()

    def OnOpenEditor(self, event):
        self._show_editor()

    def OnTabChanged(self, event):
        self._show_editor()

    def OnSaveToModel(self, message):
        if self._tab:
            self._tab.save()


class _EditorTab(wx.Panel):

    def __init__(self, plugin):
        wx.Panel.__init__(self, plugin.notebook, style=wx.SUNKEN_BORDER)
        self._plugin = plugin
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.editor = None

    def create_editor(self, item, tree):
        self.Show(False)
        if self.editor:
            self.editor.close()
            self.editor.Destroy()
            self.sizer.Clear()
        self.editor = Editor(item, self, tree)
        self.sizer.Add(self.editor, 1, wx.ALL|wx.EXPAND)
        self.Layout()
        self.Show()

    def OnSave(self, event):
        self._plugin.save_selected_datafile()

    def OnUndo(self, event):
        self.editor.undo()

    def OnCut(self, event):
        self.editor.cut()

    def OnCopy(self, event):
        self.editor.copy()

    def OnPaste(self, event):
        self.editor.paste()

    def OnDelete(self, event):
        self.editor.delete()

    def OnComment(self, event):
        self.editor.comment()

    def OnUncomment(self, event):
        self.editor.uncomment()

    def OnContentAssistance(self, event):
        self.editor.show_content_assist()

    def save(self, message=None):
        self.editor.save()
