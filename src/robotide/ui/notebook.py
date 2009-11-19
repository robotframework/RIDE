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

try:
    from wx.lib.agw import flatnotebook as fnb
except ImportError:
    from wx.lib import flatnotebook as fnb

from robotide.publish import RideNotebookTabChange


class NoteBook(fnb.FlatNotebook):

    def __init__(self, parent, app):
        self._app = app
        style = fnb.FNB_NODRAG|fnb.FNB_HIDE_ON_SINGLE_TAB|fnb.FNB_VC8
        fnb.FlatNotebook.__init__(self, parent, style=style)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnPageClosing)
        self._page_closing = False

    def add_tab(self, tab, title):
        self.AddPage(tab, title.center(10))

    def show_tab(self, tab):
        """Shows the notebook page that contains the given tab."""
        if not self.tab_is_visible(tab):
            page = self.GetPageIndex(tab)
            if page >= 0:
                self.SetSelection(page)

    def delete_tab(self, tab):
        page = self.GetPageIndex(tab)
        self.DeletePage(page)

    def tab_is_visible(self, tab):
        return tab == self.GetCurrentPage()

    def OnPageClosing(self, event):
        self._page_closing = True

    def OnPageChanging(self, event):
        if not self._page_changed():
            self._page_closing = False
            return
        oldtitle = self.GetPageText(event.GetOldSelection())
        newindex = event.GetSelection()
        if newindex <= self.GetPageCount() - 1:
            newtitle = self.GetPageText(event.GetSelection())
            self.GetPage(event.GetSelection()).SetFocus()
        else:
            newtitle = None
        RideNotebookTabChange(oldtab=oldtitle, newtab=newtitle).publish()

    def _page_changed(self):
        """Change event is send even when no tab available or tab is closed"""
        if not self.GetPageCount() or self._page_closing:
            return False
        return True
