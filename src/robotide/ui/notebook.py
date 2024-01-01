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

try:
    import wx.lib.agw.aui.auibook as aui
except ImportError:
    import wx.lib.agw.aui as aui

from ..publish import RideNotebookTabChanging, RideNotebookTabChanged


class NoteBook(aui.AuiNotebook):

    def __init__(self, parent, app, style):
        self.app = app
        self._notebook_style = style
        # style = fnb.FNB_NODRAG|fnb.FNB_HIDE_ON_SINGLE_TAB|fnb.FNB_VC8
        # fnb.FlatNotebook.__init__(self, parent, style=style)
        # default style=0, experiment others
        aui.AuiNotebook.__init__(self, parent, style=3, agwStyle=self._notebook_style)
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_tab_closing)
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGING, self.on_tab_changing)
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_tab_changed)
        self._tab_closing = False
        self._tab_state = None
        self._uncloseable = []

    def add_tab(self, tab, title, allow_closing=True):
        if not allow_closing:
            self._uncloseable.append(tab)
        self.AddPage(tab, title.strip())

    def show_tab(self, tab):
        """Shows the notebook page that contains the given tab."""
        if not self.tab_is_visible(tab):
            page = self.GetPageIndex(tab)
            if page >= 0:
                self.SetSelection(page)

    def delete_tab(self, tab):
        if tab in self._uncloseable:
            self._uncloseable.remove(tab)
        page = self.GetPageIndex(tab)
        self.DeletePage(page)

    def rename_tab(self, tab, new_name):
        self.SetPageText(self.GetPageIndex(tab), new_name)

    def allow_closing(self, tab):
        if tab in self._uncloseable:
            self._uncloseable.remove(tab)

    def disallow_closing(self, tab):
        if tab not in self._uncloseable:
            self._uncloseable.append(tab)

    def tab_is_visible(self, tab):
        return tab == self.GetCurrentPage()

    @property
    def current_page_title(self):
        return self.GetPageText(self.GetSelection())

    def on_tab_closing(self, event):
        if self.GetPage(event.GetSelection()) in self._uncloseable:
            event.Veto()
            return
        self._tab_closing = True

    def on_tab_changing(self, event):
        if not self._tab_changed():
            return
        oldselect = event.GetOldSelection()
        try:
            oldtitle = self.GetPageText(oldselect)
        except Exception:
            oldtitle = ""
        newindex = event.GetSelection()
        newtitle = self.GetPageText(event.GetSelection())
        if self._tab_state is not None:
            if self._tab_state == oldtitle + newtitle + str(newindex):
                return
            else:
                self._tab_state = oldtitle + newtitle + str(newindex)
        else:
            self._tab_state = newtitle + str(newindex)
        self.GetPage(event.GetSelection()).SetFocus()
        RideNotebookTabChanging(oldtab=oldtitle, newtab=newtitle).publish()
        event.Skip()

    def on_tab_changed(self, event):
        __ = event
        if not self._tab_changed():
            self._tab_closing = False
            return
        RideNotebookTabChanged().publish()

    def _tab_changed(self):
        """Change event is sent even when no tab available or tab is closed"""
        if not self.GetPageCount() or self._tab_closing:
            return False
        return True
