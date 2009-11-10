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
#  See the License for the specific language governing permissions and
#  limitations under the License.

import wx

from robotide.editors import Editor
from robotide.ui.dialogs import AboutDialog
from robotide import utils
from robotide.publish import RideTreeSelection, RideNotebookTabchange,\
                           RideSavingDatafile
from plugin import Plugin


class EditorPlugin(Plugin):

    def __init__(self, application):
        Plugin.__init__(self, application, initially_active=True)
        self._tab = None
        self._item = None
        self.subscribe(self.OnTreeItemSelected, RideTreeSelection)

    def activate(self):
        self.add_to_menu('Tools', 'Editor', -1, self.OnOpen,
                         'Opens suite/resource editor')
        #FIXME: Should we add the menu item?
        #('Keyword Completion', 'Show available keywords','', 'Ctrl-Space')
        self.subscribe(self.SaveToModel, RideNotebookTabchange)
        self.subscribe(self.SaveToModel, RideSavingDatafile)
        self._create_editor_tab()

    def deactivate(self):
        self.remove_added_menu_items()
        self.delete_page(self._tab)
        self.unsubscribe(self.SaveToModel, RideNotebookTabchange)
        self.unsubscribe(self.SaveToModel, RideSavingDatafile)
        self._tab = None

    def OnTreeItemSelected(self, message):
        self._item = message.item
        if self._tab:
            self._create_editor_tab()

    def OnOpen(self, event):
        if self._tab:
            self._create_editor_tab()

    def SaveToModel(self, message):
        if self._tab:
            self._tab.save()

    def _create_editor_tab(self):
        self._tab = self._create_tab(self._tab)
        if self._item:
            editor = Editor(self._item, self._tab)
        else:
            editor = self._get_welcome_editor(self._tab)
        self._tab.set_editor(editor)

    def _create_tab(self, panel):
        if not panel:
            notebook = self.get_notebook()
            panel = _EditorPanel(notebook)
            self._bind_keys(panel)
            notebook.AddPage(panel, 'Edit    ')
        return panel

    def _get_welcome_editor(self, tab):
        sizer = wx.BoxSizer()
        sizer.Add(tab, 1, wx.EXPAND)
        return utils.RideHtmlWindow(tab, wx.DefaultSize, AboutDialog.TEXT)

    def _bind_keys(self, panel):
        id = wx.NewId()
        panel.Bind(wx.EVT_MENU, self.OnKeywordCompletion, id=id )
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL,  ord(' '), id )])
        panel.SetAcceleratorTable(accel_tbl)

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

    def handle_event(self, action):
        if hasattr(self.editor, 'kweditor'):
            getattr(self.editor.kweditor, action)()
