# Copyright 2010 Orbitz WorldWide
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''Search plugin for Robot Framework IDE

http://code.google.com/p/robotframework-ride/wiki/SearchPlugin
'''

import sys
import thread
import threading
import time
import wx
from robotide.pluginapi import Plugin, ActionInfo
from robotide.pluginapi import RideLogMessage


SEARCH_KEYWORDS = 0
SEARCH_TAGS = 1
SEARCH_CHOICES = ("Search Test Case Keywords", "Search Tags")

class SearchPlugin(Plugin):
    '''Provides a dialog for searching for strings within tests'''
    def __init__(self, application, initially_active=True):
        defaults = {'match_case':False, 'exact_match':True}
        Plugin.__init__(self, application, default_settings=defaults,
                        name='Search Plugin', initially_enabled=False)
        self.version = "1.0"
        self.id = "com.orbitz.SearchPlugin"
        self.metadata = {"url":"http://code.google.com/p/robotframework-ride/wiki/SearchPlugin"}
        self._application  = application
        self._dialog = None
        self._request_stop_event = threading.Event()
        self._stopped_event = threading.Event()
        self._stopped_event.set()
        self.search_string = ""


    def enable(self):
        '''Enable the plugin'''
        self.active = True
        action = ActionInfo('Tools','Search...',
                            self.OnShowTagSearchDialog,
                            shortcut='F3',
                            doc='Search for strings within tests')
        self.register_action(action)

    def disable(self):
        'disable this plugin'''
        import traceback
        try:
            self.active = False
            self.unregister_actions()
        except Exception, e:
            message = RideLogMessage("SearchPlugin: error while disabling plugin: %s" % str(e))
            message.publish()

    def OnShowTagSearchDialog(self, event, search_string=None):
        '''Display the Tag Search Dialog'''
        if self._dialog is None:
            self._create_dialog()
        self._dialog.clear_results()
        self._dialog.Show(True, search_string)

    def OnSearchStart(self, event):
        '''Start the search thread'''
        self.save_setting('exact_match', self._dialog.exact_match)
        self.save_setting('match_case', self._dialog.match_case)
        self._search(event.search_string)

    def OnSearchCancel(self, event):
        '''Causes the search worker thread to stop'''
        self._request_stop_event.set()

    def OnSearchClose(self, event):
        '''Called when the user closes the dialog window'''
        self._dialog.Show(False)
        self._request_stop_event.set()

    def OnSearchItemSelected(self, event):
        self.highlight_cell(event.tcuk, event.child, event.row, event.col)

    def _create_dialog(self):
        '''Create the dialog window and apply settings'''
        self._dialog = SearchDialog(self.frame, wx.ID_ANY, "Search Test Cases",
                                 style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self._dialog.set_exact_match((self.exact_match))
        self._dialog.set_match_case((self.match_case))
        self._dialog.Bind(SearchDialog.EVT_SEARCH_START, self.OnSearchStart)
        self._dialog.Bind(SearchDialog.EVT_SEARCH_CLOSE, self.OnSearchClose)
        self._dialog.Bind(SearchDialog.EVT_SEARCH_ITEM_SELECTED, self.OnSearchItemSelected)
        self._dialog.Bind(SearchDialog.EVT_SEARCH_CANCEL, self.OnSearchCancel)

    def _search(self, search_string):
        '''Perform housekeeping and start the search worker thread'''

        # wait for the old thread to finish
        self._request_stop_event.set()
        self._stopped_event.wait()

        # do this via CallAfter, because the worker thread
        # may have queued up an insert that hasn't yet been
        # processed. This guarantees that the clear will
        # happen after that, but before any new items are
        # added to the lsit
        wx.CallAfter(self._dialog.clear_results)

        self._dialog.searching(True)
        self.search_string = search_string
        self._request_stop_event.clear()
        self._stopped_event.clear()
        search_type = self._dialog.get_search_type()
        if search_type == SEARCH_KEYWORDS:
            thread.start_new_thread(self._search_keywords_worker_thread, ())
        else:
            thread.start_new_thread(self._search_tags_worker_thread, ())

    def _search_keywords_worker_thread(self):
        '''Perform a search on testcase keywords'''
        search_string = unicode(self.search_string.strip())
        try:
            for tcuk in self.all_testcases():
                ## Search settings
                for setting in tcuk.settings:
                    name, value = setting.label, setting.as_list()
                    if value:
                        for column, field in enumerate(value):
                            if self._request_stop_event.isSet(): return
                            if self._match(search_string, field):
                                setting = getattr(tcuk, name, None)
                                # add one to column to account for the
                                # setting name which isn't part of the data
                                # we have in hand
                                result = KeywordResult(tcuk, setting, -1, column+1)

                                # N.B. CallAfter is necessary so that we only
                                # interact with the GUI in the main thread
                                wx.CallAfter(self._dialog.add_found_item, result)

                # search steps
                for row, step in enumerate(tcuk.steps):
                    for column, field in enumerate(step.as_list()):
                        if self._request_stop_event.isSet(): return
                        if self._match(search_string, field):
                            result = KeywordResult(tcuk, step, row, column)
                            # N.B. CallAfter is necessary so that we only
                            # interact with the GUI in the main thread
                            wx.CallAfter(self._dialog.add_found_item, result)
                        time.sleep(.0001)
        except Exception, e:
            message = RideLogMessage("SearchPlugin: unexpected error in worker thread: %s" % str(e))
            message.publish()

        finally:
            self._stopped_event.set()
            wx.CallAfter(self._dialog.searching, False)

    def _search_tags_worker_thread(self):
        '''Perform a search on testcase tags'''
        search_string = unicode(self.search_string.strip())
        try:
            for test in self.all_testcases():
                for tag in test.tags.as_list():
                    if self._match(search_string, tag):
                        result = TagResult(test, test.tags.as_list()[1:])
                        # N.B. CallAfter is necessary so that we only
                        # interact with the GUI in the main thread
                        wx.CallAfter(self._dialog.add_found_item, result)
        except Exception, e:
            message = RideLogMessage("SearchPlugin: unexpected error in worker thread: %s" % str(e))
            message.publish()

        finally:
            self._stopped_event.set()
            wx.CallAfter(self._dialog.searching, False)

    def _match(self, search_string, value):
        '''Return True if the search string matches the value'''
        if not self.match_case:
            # N.B. match case isn't implemented in the GUI yet...
            search_string = search_string.lower()
            value = value.lower()

        if self.exact_match:
            return search_string == value.strip()
        else:
            return search_string in value.strip()

class CustomListCtrl(wx.ListCtrl):
    '''Adds some methods to make the ListCtrl behave like a ListBox'''
    def __init__(self, *args, **kwargs):
        wx.ListCtrl.__init__(self, *args, **kwargs)
        self._clientData = {}

    def SetSelection(self, index):
        self.SetItemState(index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    def GetSelection(self):
        index = self.GetNextItem(-1, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
        return index

    def SetClientData(self, index, data):
        self._clientData[index] = data

    def GetClientData(self, index):
        return self._clientData.get(index, None)

    def ClearAll(self):
        wx.ListCtrl.ClearAll(self)
        self._clientData.clear()

class StatusCtrl(wx.StatusBar):
    '''Simple class that returns an appropriate string for number of matches'''
    def __init__(self, parent, id, *args, **kwargs):
        self.count = 0
        wx.StatusBar.__init__(self, parent, id, *args, **kwargs)

    def SetStatus(self, string):
        self.SetStatusText(string)

    def Start(self):
        self._running = True

    def Stop(self, found=None):
        self._running = False
        if found is None:
            self.SetStatusText("")
        else:
            if found == 1:
                self.SetStatusText("found only 1 match")
            else:
                self.SetStatusText("found %s matches" % found)

class SearchDialog(wx.Dialog):
    '''A dialog for searching test cases and tags'''
    SearchStartEvent, EVT_SEARCH_START = wx.lib.newevent.NewEvent()
    SearchCloseEvent, EVT_SEARCH_CLOSE = wx.lib.newevent.NewEvent()
    SearchItemSelected, EVT_SEARCH_ITEM_SELECTED = wx.lib.newevent.NewEvent()
    SearchCancelEvent, EVT_SEARCH_CANCEL = wx.lib.newevent.NewEvent()

    ID_SEARCH = wx.NewId()
    ID_CLOSE = wx.NewId()
    ID_EXACT_MATCH = wx.NewId()
    ID_MATCH_CASE = wx.NewId()

    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)

        listbox = CustomListCtrl(self, wx.ID_ANY, size=(500, 200),
                                 style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.LC_SINGLE_SEL)
        search_button = wx.Button(self, self.ID_SEARCH, "Search")
        close_button = wx.Button(self, wx.ID_CLOSE)
        entry = wx.SearchCtrl(self, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        entry.ShowCancelButton(True)
        statusbar = StatusCtrl(self, wx.ID_ANY)
        exact_match_checkbox = wx.CheckBox(self, self.ID_EXACT_MATCH, "Exact Match")
        match_case_checkbox = wx.CheckBox(self, self.ID_MATCH_CASE, "Match Case")
        search_type = wx.Choice(self, wx.ID_ANY, choices=SEARCH_CHOICES)

        top_sizer = wx.GridBagSizer(hgap=5, vgap=5)
        top_sizer.Add(entry,               (0,0), span=(1,2), flag=wx.EXPAND)
        top_sizer.Add(search_button,       (0,2), flag=wx.TOP|wx.LEFT|wx.RIGHT, border=0)
        top_sizer.Add(exact_match_checkbox,(1,0), flag=wx.ALIGN_CENTER_VERTICAL)
        top_sizer.Add(match_case_checkbox, (2,0), flag=wx.ALIGN_CENTER_VERTICAL)
        top_sizer.Add(search_type,         (1,1), span=(1,1), flag=wx.ALIGN_RIGHT)
        top_sizer.AddGrowableCol(1)
        top_sizer.Layout()

        bottom_sizer = wx.GridBagSizer(hgap=5, vgap=5)
        bottom_sizer.Add(close_button, (0,1), border=5, flag=wx.RIGHT)
        bottom_sizer.AddGrowableCol(0)
        bottom_sizer.Layout()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(top_sizer, flag=wx.EXPAND|wx.ALL, border=5)
        sizer.Add(listbox, flag=wx.TOP|wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.GROW, border=5, proportion=100)
        sizer.Add(bottom_sizer, flag=wx.GROW|wx.ALIGN_RIGHT)
        sizer.Add(statusbar, flag=wx.EXPAND)
        self.SetSizerAndFit(sizer)

        close_button.Bind(wx.EVT_BUTTON, self.OnClose)
        exact_match_checkbox.Bind(wx.EVT_CHECKBOX, self.OnExactMatchCheckbox)
        match_case_checkbox.Bind(wx.EVT_CHECKBOX, self.OnMatchCaseCheckbox)
        search_button.Bind(wx.EVT_BUTTON, self.OnSearch)
        entry.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        entry.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        listbox.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListboxSelect)
        search_type.Bind(wx.EVT_CHOICE, self.OnSearchType)
        entry.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)

        entry.SetToolTip(wx.ToolTip("enter a tag to search for"))
        search_type.SetToolTip(wx.ToolTip("Select the type of search to perform"))
        exact_match_checkbox.SetToolTip(wx.ToolTip("Check to search for exact match"))
        close_button.SetToolTip(wx.ToolTip("Click to close this window"))

        self.entry = entry
        self.listbox = listbox
        self.search_button = search_button
        self.statusbar = statusbar
        self.exact_match_checkbox = exact_match_checkbox
        self.match_case_checkbox = match_case_checkbox
        self.search_type = search_type

        self.clear_results()

    def OnCancel(self, event):
        '''Generate a SearchCancelEvent'''
        new_event = self.SearchCancelEvent()
        wx.PostEvent(self, new_event)

    def OnSearchType(self, event):
        '''Called when the user changes the search type'''
        self.clear_results()

    def SetStatus(self, string):
        '''Set the dialog status to the given string'''
        self.statusbar.SetStatus(string)

    def OnMatchCaseCheckbox(self, event):
        '''Called when the user checks/unchecks the 'match case' checkbox'''
        self.match_case = event.IsChecked()

    def OnExactMatchCheckbox(self, event):
        '''Called when the user checks/unchecks the 'exact match' checkbox'''
        self.exact_match = event.IsChecked()

    def OnKeyUp(self, event):
        '''Handles processing of escape key

        This also enables or disables the search button depending
        on whether the search string is non-null
        '''
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnClose(event)
            return
        event.Skip()

    def OnListboxSelect(self, event):
        '''Causes the selected item to be shown in the editor'''
        index = self.listbox.GetSelection()
        data = self.listbox.GetClientData(index)
        new_event = self.SearchItemSelected(tcuk=data["tcuk"],
                                            child=data["child"],
                                            row=data["row"],
                                            col=data["col"])
        wx.PostEvent(self, new_event)

    def OnSearch(self, event):
        '''Starts a new search'''
        new_event = self.SearchStartEvent(search_string=self.entry.GetValue())
        wx.PostEvent(self, new_event)
        self.statusbar.Start()

    def OnClose(self, event):
        '''Closes the dialog box and stops any running search'''
        new_event = self.SearchCloseEvent()
        wx.PostEvent(self, new_event)
        self.statusbar.Stop()

    def Show(self, visible, search_string=None):
        '''Show or hide the dialog

        if the parameter search_string is not None, automatically
        start the search using that string
        '''
        # N.B. this is the dialog class...
        if search_string is not None:
            self.entry.SetValue(search_string)
            new_event = self.SearchStartEvent(search_string=search_string)
            wx.CallAfter(wx.PostEvent, self, new_event)

        wx.Dialog.Show(self, visible)
        self.entry.SetFocus()

    def clear_results(self):
        '''Reset all the search results'''
        self.listbox.ClearAll()
        self.listbox.InsertColumn(0, "Test Case", width=200)
        if self.search_type.GetSelection() == SEARCH_KEYWORDS:
            self.listbox.InsertColumn(1, "Keyword", width=200)
        else:
            self.listbox.InsertColumn(1, "Tags", width=200)

    def set_exact_match(self, value):
        '''Sets the exact_match bit and updates the checkbox'''
        self.exact_match = value
        self.exact_match_checkbox.SetValue(value)

    def set_match_case(self, value):
        '''Sets the match_case bit and updates the checkbox'''
        self.match_case = value
        self.match_case_checkbox.SetValue(value)

    def add_found_item(self, result):
        '''Adds a result to the listbox'''
        index = self.listbox.InsertStringItem(sys.maxint, result.name)
        self.listbox.SetStringItem(index, 1, result.value)
        self.listbox.SetClientData(index, result.data)

        self.SetStatus("searching...%s" % self.listbox.GetItemCount())
        # the wx.LIST_AUTOSIZE feature doesn't seem to work so I
        # need to adjust the width manually.
        width = self._measure_string(self.listbox, result.value)
        if width > self.listbox.GetColumnWidth(1):
            self.listbox.SetColumnWidth(1, width)

    def get_search_type(self):
        '''Returns the currently selected search type

        The return value is an index into the SEARCH_CHOICES list
        '''
        return self.search_type.GetSelection()

    def searching(self, is_searching=True):
        '''Update the dialog to reflect whether a search is happening or not'''
        if is_searching:
            self.statusbar.SetLabel("searching...")
        else:
            self.statusbar.Stop(self.listbox.GetItemCount())

    def _measure_string(self, control, string):
        '''Determines the width of a string'''
        font = control.GetFont()
        dc = wx.WindowDC(control)
        dc.SetFont(font)
        width, height = dc.GetTextExtent(string)
        # add a little fudge factor; it just works better when I do this
        return width + 10

class TagResult:
    '''A result for a search on tags'''
    def __init__(self, tcuk, tags):
        self.tcuk = tcuk
        self.name = tcuk.name
        self.value = ", ".join(tags)
        self.data = {"tcuk":tcuk, "child": tags, "row": None, "col": None}

class KeywordResult:
    '''A result for a search on keywords'''
    def __init__(self, tcuk, child, row, col):
        try:
            self.tcuk = tcuk
            self.name = tcuk.name
            self.data = {"tcuk":tcuk, "child": child, "row": row, "col": col}
            if hasattr(child, "as_list"):
                self.value = " | ".join(child.as_list())
            elif hasattr(child, "value"):
                self.value  = " | ".join(child.value)
            else:
                self.value = str(child)
        except Exception, e:
            message = RideLogMessage("error creating KeywordResult: %s" % str(e))
            message.publish()

