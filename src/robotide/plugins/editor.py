#  Copyright 2008-2009 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the 'License');
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an 'AS IS' BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  S    ee the License for the specific language governing permissions and
#  limitations under the License.

import wx

from robotide.editors import Editor
from robotide.ui import MenuEntries
from robotide.publish import RideTreeSelection, RideNotebookTabchange,\
                           RideSavingDatafile

from plugin import Plugin


edit_actions ="""
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
!Open &Editor | Opens suite/resource editor
"""


class EditorPlugin(Plugin):

    def __init__(self, application):
        Plugin.__init__(self, application, initially_active=True)
        self._tab = None
        self.subscribe(self.OnTreeItemSelected, RideTreeSelection)

    def activate(self):
        self._show_editor()
        self.register_menu_entries(MenuEntries(edit_actions, self, self._tab))
        self.subscribe(self.SaveToModel, RideNotebookTabchange)
        self.subscribe(self.SaveToModel, RideSavingDatafile)

    def _show_editor(self, item=None):
        if not self._tab:
            self._tab = self._create_tab()
        self._tab.set_editor(Editor(item, self._tab))

    def _create_tab(self):
        panel = _EditorPanel(self.notebook)
        self._bind_keys(panel)
        self.notebook.AddPage(panel, 'Edit    ')
        return panel

    def deactivate(self):
        self.unergister_menu_entries()
        self.delete_page(self._tab)
        self.unsubscribe(self.SaveToModel, RideNotebookTabchange)
        self.unsubscribe(self.SaveToModel, RideSavingDatafile)
        self._tab = None

    def OnTreeItemSelected(self, message):
        self._show_editor(message.item)

    def OnOpenEditor(self, event):
        self._show_editor()

    def OnUndo(self, event):
        self._tab.editor.undo()

    def OnCut(self, event):
        self._tab.editor.cut()

    def OnCopy(self, event):
        self._tab.editor.copy()

    def OnPaste(self, event):
        self._tab.editor.paste()

    def OnDelete(self, event):
        self._tab.editor.delete()

    def OnComment(self, event):
        self._tab.editor.comment()

    def OnUncomment(self, event):
        self._tab.editor.uncomment()

    def SaveToModel(self, message):
        if self._tab:
            self._tab.save()

    def _bind_keys(self, panel):
        id = wx.NewId()
        panel.Bind(wx.EVT_MENU, self.OnKeywordCompletion, id=id)
        panel.SetAcceleratorTable(wx.AcceleratorTable([(wx.ACCEL_CTRL, 
                                                        wx.WXK_SPACE, id)]))

    def OnKeywordCompletion(self, event):
        self._tab.show_keyword_completion()


class _EditorPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.editor = None

    def set_editor(self, editor):
        if self.editor:
            self.editor.close()
            self.sizer.Clear()
        editor.Show(True)
        self.sizer.Add(editor, 1, wx.ALL|wx.EXPAND)
        self.Layout()
        self.editor = editor

    def save(self, message=None):
        if hasattr(self.editor, 'save'):
            self.editor.save()

    def show_keyword_completion(self):
        if hasattr(self.editor, 'kweditor'):
            kwe = self.editor.kweditor
            if kwe.IsCellEditControlShown():
                kwe.show_content_assist()
            return
        wx.MessageBox('To use Keyword Completion, type the beginning of the keyword '
                      'name into a cell and then choose this option.', 'Hint')
