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
from  wx.lib.pubsub import Publisher
try:
    from wx.lib.agw import flatnotebook as fnb
except ImportError:
    from wx.lib import flatnotebook as fnb

from filedialogs import NewProjectDialog, NewResourceDialog, SaveAsDialog,\
    ChangeFormatDialog
from dialogs import KeywordSearchDialog, AboutDialog
from robotide.editors import RideEventHandler
from robotide.errors import PluginPageNotFoundError
from suitetree import SuiteTree
from actions import Actions
from robotide import utils
from robotide import context


class RideFrame(wx.Frame, RideEventHandler, utils.OnScreenEnsuringFrame):

    def __init__(self, application):
        wx.Frame.__init__(self, None, -1, 'RIDE',
                          pos=context.SETTINGS["mainframe position"],
                          size=context.SETTINGS["mainframe size"])
        self._application = application
        self._create_decorations()
        self.ensure_on_screen()

    def create_ui(self, keyword_filter):
        """Called by application after it has properly initialized itself."""
        self._create_containers()
        self._kw_search_dialog = KeywordSearchDialog(self, keyword_filter)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnPageClosing)
        self.tree.Bind(wx.EVT_LEFT_DCLICK, self.OnSuiteTreeLeftDClick)
        self.Show()

    def _create_containers(self):
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(200)
        # for now, hide the tabs if there's only one. Until there are
        # at least two tabs there's no point in taking up the screen
        # real estate. Eventually this should be a user preference.
        self.notebook = NoteBook(splitter, self._application)
        self._editor_panel = _EditorPanel(self.notebook)
        self.notebook.AddPage(self._editor_panel, "Edit    ")
        Publisher().subscribe(self._editor_panel.save,
                              ('core', 'notebook', 'tabchange'))
        sizer = wx.BoxSizer()
        sizer.Add(self._editor_panel, 1, wx.EXPAND)
        welcome_page = utils.RideHtmlWindow(self._editor_panel, wx.DefaultSize,
                                            AboutDialog.TEXT)
        self._editor_panel.set_editor(welcome_page)
        self.tree = SuiteTree(splitter, self._editor_panel)
        splitter.SplitVertically(self.tree, self.notebook, 300)

    def OnSuiteTreeLeftDClick(self, event):
        """Make the editor tab visible on double-click in the tree."""
        self.show_page(self._editor_panel)
        event.Skip()

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

    def _get_active_item(self):
        return self.tree.get_active_item()

    def OnPageClosing(self, event):
        """Disallow closing of the edit tab"""
        # Eventually it might be nice to support having multiple editors
        # open at once (for example, a keyword editor and a test editor)
        # but for now we only support one and we can't let that one
        # be deleted.
        page = self.notebook.GetCurrentPage()
        if page == self._editor_panel:
            # Should we print a friendly message in the statusbar or
            # is this Good Enough?
            wx.Bell()
            event.Veto()

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
        self._editor_panel.save()
        files_without_format = self._application.get_files_without_format(datafile)
        for f in files_without_format:
            self._show_format_dialog_for(f)
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
        s = len(saved) > 1 and 's' or ''
        self.SetStatusText('Wrote file%s: %s' %
                          (s, ', '.join(item.source for item in saved)))

    def OnSaveAs(self, event):
        self._editor_panel.save()
        dlg = SaveAsDialog(self, self._application.model.get_suite_path(),
                           self._application.model.is_directory_suite())
        if dlg.ShowModal() == wx.ID_OK:
            self._application.save_as(dlg.get_path())
            self.tree.populate_tree(self._application.model)
        dlg.Destroy()

    def OnExit(self, event):
        self.Close()
        event.Skip()

    # Edit Menu

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

    def OnKeywordCompletion(self, event):
        self._editor_panel.show_keyword_completion()

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


class NoteBook(fnb.FlatNotebook):

    def __init__(self, parent, app):
        self._app = app
        style = fnb.FNB_NODRAG|fnb.FNB_HIDE_ON_SINGLE_TAB|fnb.FNB_VC8
        fnb.FlatNotebook.__init__(self, parent, style=style)
        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING, self.OnPageChanging)

    def OnPageChanging(self, event):
        if not self.GetPageCount():
            return
        oldtitle = self.GetPageText(event.GetOldSelection())
        newindex = event.GetSelection()
        if newindex <= self.GetPageCount() - 1:
            newtitle = self.GetPageText(event.GetSelection())
        else:
            newtitle = None
        Publisher().sendMessage(('core', 'notebook', 'tabchange'),
                                {'oldtab': oldtitle, 'newtab': newtitle})
