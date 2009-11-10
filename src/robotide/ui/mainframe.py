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


import os
import wx
try:
    from wx.lib.agw import flatnotebook as fnb
except ImportError:
    from wx.lib import flatnotebook as fnb

from robotide.editors import RideEventHandler
from robotide.errors import PluginPageNotFoundError
from robotide.publish import RideNotebookTabchange, RideSavingDatafile,\
                           RideSavedDatafiles
from robotide import utils
from robotide import context

from actions import Actions
from dialogs import KeywordSearchDialog, AboutDialog
from filedialogs import NewProjectDialog, NewResourceDialog, ChangeFormatDialog
from pluginmanager import PluginManager
from suitetree import SuiteTree


class RideFrame(wx.Frame, RideEventHandler, utils.OnScreenEnsuringFrame):

    def __init__(self, application, keyword_filter):
        wx.Frame.__init__(self, None, -1, 'RIDE',
                          pos=context.SETTINGS["mainframe position"],
                          size=context.SETTINGS["mainframe size"])
        self._application = application
        self._create_decorations()
        self.ensure_on_screen()
        self._create_containers()
        self._plugin_manager = PluginManager(self.notebook)
        self._kw_search_dialog = KeywordSearchDialog(self, keyword_filter)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Show()

    def _create_containers(self):
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(200)
        # for now, hide the tabs if there's only one. Until there are
        # at least two tabs there's no point in taking up the screen
        # real estate. Eventually this should be a user preference.
        self.notebook = NoteBook(splitter, self._application)
        self.tree = SuiteTree(splitter) #, self._editor_panel)
        splitter.SplitVertically(self.tree, self.notebook, 300)

    def _create_decorations(self):
        # We need to define some standard toolbar buttons. For 
        # now, create an empty toolbar so plugins have a place to
        # put their buttons.
        actions = Actions(self)
        self.SetMenuBar(actions.get_menubar())
        self.SetToolBar(actions.get_toolbar())
        self.CreateStatusBar()

    def populate_tree(self, model):
        self.tree.populate_tree(model)

    def show_page(self, panel):
        """Shows the notebook page that contains the given panel.

        Throws a PluginPageNotFoundError exception if the page can't be found.
        """
        if self.notebook.GetCurrentPage() != panel:
            page = self.notebook.GetPageIndex(panel)
            if page >= 0:
                self.notebook.SetSelection(page)
            else:
                raise PluginPageNotFoundError("unable to find a notebook page for the given panel")

    def delete_page(self, panel):
        page = self.notebook.GetPageIndex(panel)
        self.notebook.DeletePage(page)

    def _get_active_item(self):
        return self.tree.get_active_item()

    def OnClose(self, event):
        self._save_mainframe_size_and_position()
        if self._application.ok_to_exit():
            self.Destroy()
        else:
            wx.CloseEvent.Veto(event)

    def _save_mainframe_size_and_position(self):
        context.SETTINGS["mainframe size"] = self.GetSizeTuple()
        context.SETTINGS["mainframe position"] = self.GetPositionTuple()

    #File Menu

    def OnNewSuite(self, event):
        if not self._application.ok_to_open_new():
            return
        dlg = NewProjectDialog(self, self._default_dir)
        if dlg.ShowModal() == wx.ID_OK:
            dirname = os.path.dirname(dlg.get_path())
            if not os.path.isdir(dirname):
                os.mkdir(dirname)
            self._default_dir = dirname
            self._application.open_suite(dlg.get_path())
            self.tree.populate_tree(self._application.model)
        dlg.Destroy()

    # TODO: Are properties ok in here? Settings are saved when frame is closed.
    def _set_default_dir(self, dirname):
        context.SETTINGS["default directory"] = dirname

    def _get_default_dir(self):
        return os.path.abspath(context.SETTINGS["default directory"])

    _default_dir = property(_get_default_dir, _set_default_dir)

    def OnNewResource(self, event):
        dlg = NewResourceDialog(self, self._default_dir)
        if dlg.ShowModal() == wx.ID_OK:
            self._default_dir = os.path.dirname(dlg.get_path())
            self._application.open_resource(dlg.get_path())
        dlg.Destroy()

    def OnOpen(self, event):
        if not self._application.ok_to_open_new():
            return
        path = self._get_path()
        if path:
            self.open_suite(path)

    def OnOpenResource(self, event):
        path = self._get_path()
        if path:
            self._application.open_resource(path)

    def _get_path(self):
        wildcard = ('All files|*.*|Robot data (*.html)|*.*htm*|'
                    'Robot data (*.tsv)|*.tsv|Robot data (*txt)|*.txt')
        dlg = wx.FileDialog(self, message='Open', wildcard=wildcard,
                            defaultDir=self._default_dir, style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._default_dir = os.path.dirname(path)
        else:
            path = None
        dlg.Destroy()
        return path

    def open_suite(self, path):
        self._application.open_suite(path)
        self.tree.populate_tree(self._application.model)

    def OnOpenDirectory(self, event):
        if not self._application.ok_to_open_new():
            return
        path = wx.DirSelector(message='Choose a directory containing Robot files',
                              defaultPath=self._default_dir)
        if path:
            self._default_dir = os.path.dirname(path)
            self.open_suite(path)
        event.Skip()

    def OnSave(self, event):
        self._save(self._get_active_item())

    def OnSaveAll(self, event):
        self._save()

    def _save(self, datafile=None):
        files_without_format = self._application.get_files_without_format(datafile)
        for f in files_without_format:
            self._show_format_dialog_for(f)
        RideSavingDatafile(datafile=datafile).publish()
        saved = self._application.save(datafile)
        self._report_saved_files(saved)
        self.tree.unset_dirty()

    def _show_format_dialog_for(self, file_without_format):
        help = 'Please provide format of initialization file for directory suite\n"%s".' %\
                file_without_format.source
        dlg = ChangeFormatDialog(self, 'HTML', help_text=help)
        if dlg.ShowModal() == wx.ID_OK:
            file_without_format.set_format(dlg.get_format())
        dlg.Destroy()

    def _report_saved_files(self, saved):
        if not saved:
            return
        RideSavedDatafiles(datafiles=saved).publish()
        s = len(saved) > 1 and 's' or ''
        self.SetStatusText('Wrote file%s: %s' %
                          (s, ', '.join(item.source for item in saved)))

    def OnExit(self, event):
        self.Close()
        event.Skip()

    # Edit Menu
    #FIXME: How these should be handled? We should have one active component 
    #always like tree, tab, etc.. -> plugin interface should have abstract 
    #methods for handling the events.

    def OnCut(self, event):
        self._editor_panel.handle_event('cut')

    def OnCopy(self, event):
        self._editor_panel.handle_event('copy')

    def OnPaste(self, event):
        self._editor_panel.handle_event('paste')

    def OnDelete(self, event):
        self._editor_panel.handle_event('delete')

    def OnUndo(self, event):
        self._editor_panel.handle_event('undo')

    def OnComment(self, event):
        self._editor_panel.handle_event('comment')
        event.Skip()

    def OnUncomment(self, event):
        self._editor_panel.handle_event('uncomment')
        event.Skip()

    # Tools Menu
    
    def OnManagePlugins(self, event):
        self._plugin_manager.show(self._application.get_plugins())

    def OnSearchKeywords(self, event):
        if not self._kw_search_dialog.IsShown():
            self._kw_search_dialog.Show()

    # Navigate Menu

    def OnGoBack(self, event):
        self.tree.go_back()

    def OnGoForward(self, event):
        self.tree.go_forward()

    # About Menu

    def OnAbout(self, event):
        dlg = AboutDialog(self)
        dlg.ShowModal()
        dlg.Destroy()


class NoteBook(fnb.FlatNotebook):

    def __init__(self, parent, app):
        self._app = app
        style = fnb.FNB_NODRAG|fnb.FNB_HIDE_ON_SINGLE_TAB|fnb.FNB_VC8
        fnb.FlatNotebook.__init__(self, parent, style=style)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnPageClosing)
        self._page_closing = False

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
        else:
            newtitle = None
        RideNotebookTabchange(oldtab=oldtitle, newtab=newtitle).publish()

    def _page_changed(self):
        """Change event is send even when no tab available or tab is closed"""
        if not self.GetPageCount() or self._page_closing:
            return False
        return True
