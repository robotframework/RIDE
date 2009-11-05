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

import wx.html
from StringIO import StringIO
try:
    from wx.lib.agw import flatnotebook as fnb
except ImportError:
    from wx.lib import flatnotebook as fnb

from robotide.writer.writer import HtmlFileWriter, TxtFileWriter
from robotide.model.tcuk import TestCase, UserKeyword
from robotide.errors import SerializationError
from robotide.event import RideTreeSelection, RideNotebookTabchange

from plugin import Plugin


class InMemoryHtmlWriter(HtmlFileWriter):

    def _write_empty_row(self):
        self._write_data(['&nbsp;'])

    def close(self):
        HtmlFileWriter.close(self, close_output=False)


class InMemoryTxtWriter(TxtFileWriter):

    def close(self):
        TxtFileWriter.close(self, close_output=False)


class PreviewPlugin(Plugin):
    """Provides preview of the test data in HTML and TXT formats."""

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._panel = None
        self._item = None

    def activate(self):
        self.add_to_menu('Tools','Preview', -1, self.OnShowPreview,
                         'Show preview of the current file')
        self.subscribe(self._create_preview_if_item_changed, RideTreeSelection)
        self.subscribe(self._create_preview_if_self_selected, 
                       RideNotebookTabchange)

    def deactivate(self):
        self.unsubscribe_all_events()
        self.remove_added_menu_items()
        self.delete_page(self._panel)
        self._panel = None

    def OnShowPreview(self, event):
        self._create_ui()
        if self._create_preview_if_item_is_selected():
            self.show_page(self._panel)

    def _create_preview_if_item_is_selected(self):
        item = self._get_item()
        if not item:
            return False
        self._create_preview(item)
        return True

    def _create_preview_if_item_changed(self, event):
        item = self._get_item()
        if not (item and self._panel):
            return
        if item is self._item:
            self._panel.scroll_to_subitem(event.item)
        else:
            self._item = item
            self._create_preview(item)

    def _create_preview_if_self_selected(self, event):
        if event.newtab == self.name:
            self._create_preview_if_item_is_selected()

    def _get_item(self):
        return self.get_frame()._get_active_item()

    def _create_preview(self, item):
        if not self._panel:
            return
        self._panel.preview(item)

    def _create_ui(self):
        if not self._panel:
            notebook = self.get_notebook()
            self._panel = PreviewPanel(self, notebook)


class PreviewPanel(wx.Panel):

    def __init__(self, parent, notebook):
        wx.Panel.__init__(self, notebook)
        self._parent = parent
        self._datafile = None
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._create_chooser()
        self._set_format('Text')
        notebook.AddPage(self, "Preview")

    def _create_chooser(self):
        chooser = wx.RadioBox(self, label='Format', choices=['Text', 'HTML'])
        self.Bind(wx.EVT_RADIOBOX, self.OnTypeChanged, chooser)
        self.Sizer.Add(chooser)

    def preview(self, datafile):
        self._datafile = datafile
        content = datafile and self._get_content(datafile) or ''
        self._view.set_content(content.decode('UTF-8'))

    def _get_content(self, datafile):
        output = StringIO()
        writer = {'HTML': InMemoryHtmlWriter,
                  'Text': InMemoryTxtWriter}[self._format](output)
        try:
            # TODO: might need a public way to do this
            datafile._serialize(writer)
        except SerializationError, e:
            return "Creating preview of '%s' failed: %s" % (datafile.name, e)
        else:
            return output.getvalue()

    def scroll_to_subitem(self, item):
        self._view.scroll_to_subitem(self._get_anchor(item))

    def _get_anchor(self, item):
        if isinstance(item, TestCase):
            return 'test_%s' % item.name
        if isinstance(item, UserKeyword):
            return 'keyword_%s' % item.name
        return ''

    def OnTypeChanged(self, event):
        self._set_format(event.GetString())
        self.preview(self._datafile)

    def _set_format(self, format):
        self._format = format
        if hasattr(self, '_view'):
            self.Sizer.Remove(self._view)
            self._view.Destroy()
        if format == 'HTML':
            self._view = HtmlView(self)
        else:
            self._view = TxtView(self)
        self.Sizer.Add(self._view, 1, wx.EXPAND|wx.ALL, border=8)
        self.Sizer.Layout()


class HtmlView(wx.html.HtmlWindow):

    def __init__(self, parent):
        wx.html.HtmlWindow.__init__(self, parent)
        self.SetStandardFonts()

    def set_content(self, content):
        self.SetPage(content)

    def scroll_to_subitem(self, anchor):
        if self.HasAnchor(anchor):
            self.ScrollToAnchor(anchor)
            self.ScrollLines(-1)
        else:
            self.Scroll(0,0)


class TxtView(wx.TextCtrl):

    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, style=wx.TE_MULTILINE)
        self.SetEditable(False)
        self.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL))

    def set_content(self, content):
        self.SetValue(content)

    def scroll_to_subitem(self, item):
        pass
