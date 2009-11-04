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
from plugin import Plugin


class EditorPlugin(Plugin):

    def __init__(self, application):
        Plugin.__init__(self, application, initially_active=True)
        self._panel = None
        self._item = None
        self._editor = None

    def activate(self):
        self.add_to_menu('Tools', 'Editor', -1, self.OnOpen,
                         'Opens suite/resource editor')
        self.subscribe(self.OnTreeItemSelected,('core','tree','selection'))
        self.subscribe(self.OnSave, ('core', 'notebook', 'tabchange'))
        self._create_editor_panel()

    def deactivate(self):
        self.remove_added_menu_items()
        self.delete_page(self._panel)
        self._panel = None
        self.unsubscribe(self.OnTreeItemSelected,('core','tree','selection'))

    def OnTreeItemSelected(self, message):
        self._item = message.data['item']
        self._panel = None
        self._create_editor_panel()

    def OnOpen(self, event):
        self._create_editor_panel()

    def OnSave(self, message):
        if self._panel:
            self._panel.save()

    def _create_editor_panel(self):
        if not self._panel:
            notebook = self.get_notebook()
            self._panel = _EditorPanel(notebook)
            notebook.AddPage(self._panel, 'Edit    ')
            if self._item:
                self._editor = Editor(self._item, self._panel)
                self._panel.set_editor(self._editor)
            else:
                sizer = wx.BoxSizer()
                sizer.Add(self._panel, 1, wx.EXPAND)
                self._editor = utils.RideHtmlWindow(self._panel, wx.DefaultSize,
                                                    AboutDialog.TEXT)
                self._panel.set_editor(self._editor)


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
