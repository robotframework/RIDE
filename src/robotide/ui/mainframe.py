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

import builtins
import os

import wx
import wx.lib.agw.aui as aui
from wx import Colour
from wx.adv import TaskBarIcon, TBI_DOCK, EVT_TASKBAR_LEFT_DOWN
from multiprocessing import shared_memory

from .actiontriggers import (MenuBar, ToolBarButton, ShortcutRegistry, _RideSearchMenuItem)
from .filedialogs import (NewProjectDialog, InitFileFormatDialog)
from .fileexplorerplugin import FileExplorer
from .notebook import NoteBook
from .pluginmanager import PluginManager
from .progress import LoadProgressObserver
from .review import ReviewDialog
from .treeplugin import Tree
from ..action import action_info_collection, action_factory, SeparatorInfo
from ..action.shortcut import localize_shortcuts
from ..context import get_about_ride, SHORTCUT_KEYS
from ..controller.ctrlcommands import SaveFile, SaveAll
from ..editor import customsourceeditor
from ..preferences import PreferenceEditor
from ..publish import (RideSaveAll, RideClosing, RideSaved, PUBLISHER, RideInputValidationError, RideTreeSelection,
                       RideModificationPrevented, RideBeforeSaving, RideSettingsChanged)
from ..ui.filedialogs import RobotFilePathDialog
from ..ui.tagdialogs import ViewAllTagsDialog
from ..utils import RideFSWatcherHandler
from ..widgets import RIDEDialog, ImageProvider, HtmlWindow

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

ID_CustomizeToolbar = wx.ID_HIGHEST + 1
ID_SampleItem = ID_CustomizeToolbar + 1
MAINFRAME_POSITION = 'mainframe position'
MAINFRAME_MAXIMIZED = 'mainframe maximized'


def get_menudata():
    # Menus to translate
    file_0 = _("[File]\n")
    file_1 = _("!&New Project | Create a new top level suite | Ctrlcmd-N | ART_NEW\n")
    separator = "---\n"
    file_2 = _("!&Open Test Suite | Open file containing tests | Ctrlcmd-O | ART_FILE_OPEN\n")
    file_3 = _("!Open &Directory | Open directory containing datafiles | Shift-Ctrlcmd-O | ART_FOLDER_OPEN\n")
    file_4 = _("!Open External File | Open file in Code Editor | | ART_NORMAL_FILE\n")
    file_5 = _("!&Save | Save selected datafile | Ctrlcmd-S | ART_FILE_SAVE\n")
    file_6 = _("!Save &All | Save all changes | Ctrlcmd-Shift-S | ART_FILE_SAVE_AS\n")
    file_7 = _("!E&xit | Exit RIDE | Ctrlcmd-Q\n")
    tool_0 = _("[Tools]\n")
    tool_1 = _("!Search Unused Keywords | | | | POSITION-54\n")
    tool_2 = _("!Manage Plugins | | | | POSITION-81\n")
    tool_3 = _("!View All Tags | | F7 | | POSITION-82\n")
    tool_4 = _("!Preferences | | | | POSITION-99\n")
    help_0 = _("[Help]\n")
    help_1 = _("!Shortcut keys | RIDE shortcut keys\n")
    help_2 = _("!User Guide | Robot Framework User Guide\n")
    help_3 = _("!Wiki | RIDE User Guide (Wiki)\n")
    help_4 = _("!Report a Problem | Open browser to SEARCH on the RIDE issue tracker\n")
    help_6 = _("!About | Information about RIDE\n")
    help_7 = _("!Check for Upgrade | Looks at PyPi for new released version\n")
    
    return (file_0 + file_1 + separator + file_2 + file_3 + file_4 + separator + file_5 + file_6 + separator +
            file_7 + '\n' + tool_0 + tool_1 + tool_2 + tool_3 + tool_4 + '\n' + help_0 + help_1 + help_2 +
            help_3 + help_4 + help_6 + help_7)


class RideFrame(wx.Frame):

    _menudata_nt = """[File]
    !&New Project | Create a new top level suite | Ctrlcmd-N | ART_NEW
    ---
    !&Open Test Suite | Open file containing tests | Ctrlcmd-O | ART_FILE_OPEN
    !Open &Directory | Open directory containing datafiles | Shift-Ctrlcmd-O | ART_FOLDER_OPEN
    !Open External File | Open file in Code Editor | | ART_NORMAL_FILE
    ---
    !&Save | Save selected datafile | Ctrlcmd-S | ART_FILE_SAVE
    !Save &All | Save all changes | Ctrlcmd-Shift-S | ART_FILE_SAVE_AS
    ---
    !E&xit | Exit RIDE | Ctrlcmd-Q

    [Tools]
    !Search Unused Keywords | | | | POSITION-54
    !Manage Plugins | | | | POSITION-81
    !View All Tags | | F7 | | POSITION-82
    !Preferences | | | | POSITION-99

    [Help]
    !Shortcut keys | RIDE shortcut keys
    !User Guide | Robot Framework User Guide
    !Wiki | RIDE User Guide (Wiki)
    !Report a Problem | Open browser to SEARCH on the RIDE issue tracker
    !About | Information about RIDE
    !Check for Upgrade | Looks at PyPi for new released version
    """

    def __init__(self, application, controller):
        size = application.settings.get('mainframe size', (1100, 700))
        # DEBUG self.general_settings = application.settings['General']
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY, title='RIDE',
                          pos=application.settings.get(MAINFRAME_POSITION, (50, 30)),
                          size=size, style=wx.DEFAULT_FRAME_STYLE | wx.SUNKEN_BORDER | wx.BORDER_THEME)

        # Shared memory to store language definition
        try:
            self.sharemem = shared_memory.ShareableList(['en'], name="language")
        except FileExistsError:  # Other instance created file
            self.sharemem = shared_memory.ShareableList(name="language")
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        # self.SetLayoutDirection(wx.Layout_RightToLeft)

        self.fontinfo = application.fontinfo
        self.SetFont(wx.Font(self.fontinfo))

        self.aui_mgr = aui.AuiManager(self)

        # tell AuiManager to manage this frame
        self.aui_mgr.SetManagedWindow(self)

        self.SetMinSize(wx.Size(400, 300))

        self.ensure_on_screen()
        if application.settings.get(MAINFRAME_MAXIMIZED, False):
            self.Maximize()
        self._application = application
        self.controller = controller
        self._image_provider = ImageProvider()
        self.reformat = application.settings.get('reformat', False)
        self.tasks = application.settings.get('tasks', False)
        self.doc_language = application.settings.get('doc language', '')
        self._notebook_theme = application.settings.get('notebook theme', 0)
        self.general_settings = application.settings['General']  # .get_without_default('General')
        self.color_background_help = self.general_settings.get('background help', (240, 242, 80))
        self.color_foreground_text = self.general_settings.get('foreground text', (7, 0, 70))
        self.color_background = self.general_settings.get_without_default('background')
        self.color_foreground = self.general_settings.get_without_default('foreground')
        self.font_face = self.general_settings.get('font face', '')
        self.font_size = self.general_settings.get('font size', 11)
        self.ui_language = self.general_settings.get('ui language', 'English')
        self.main_menu = None
        self._init_ui()
        self._task_bar_icon = RIDETaskBarIcon(self, self._image_provider)
        self._plugin_manager = PluginManager(self.notebook)
        self._review_dialog = None
        self._view_all_tags_dialog = None
        self._current_external_dir = None
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_MOVE, self.on_move)
        self.Bind(wx.EVT_MAXIMIZE, self.on_maximize)
        self.Bind(wx.EVT_DIRCTRL_FILEACTIVATED, self.on_open_file)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_menu_open_file)
        self._subscribe_messages()
        wx.CallAfter(self.actions.register_tools)  # DEBUG
        # DEBUG wx.CallAfter(self.OnSettingsChanged, self.general_settings)

    def _subscribe_messages(self):
        for listener, topic in [
            (lambda message: self.SetStatusText(_('Saved %s') % message.path), RideSaved),
            (lambda message: self.SetStatusText(_('Saved all files')), RideSaveAll),
            (self._set_label, RideTreeSelection),
            (self._show_validation_error, RideInputValidationError),
            (self._show_modification_prevented_error, RideModificationPrevented),
            (self.on_ui_language_changed, RideSettingsChanged)
        ]:
            PUBLISHER.subscribe(listener, topic)

    def _set_label(self, message):
        self.SetTitle(self._create_title(message))

    @staticmethod
    def _create_title(message):
        title = 'RIDE'
        if message:
            item = message.item
            title += ' - ' + item.datafile.name
            if not item.is_modifiable():
                title += _(' (READ ONLY)')
        return title

    @staticmethod
    def _show_validation_error(message):
        wx.MessageBox(message.message, _('Validation Error'), style=wx.ICON_ERROR)

    @staticmethod
    def _show_modification_prevented_error(message):
        wx.MessageBox(_("\"%s\" is read only") % message.controller.datafile_controller.filename,
                      _("Modification prevented"), style=wx.ICON_ERROR)

    def _init_ui(self):
        """ DEBUG:
            self.aui_mgr.AddPane(wx.Panel(self), aui.AuiPaneInfo().CenterPane())
            self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        """
        if not self.main_menu:
            new_ui = True
        else:
            new_ui = False
        if new_ui:  # Only when creating UI we add panes
            self.aui_mgr.AddPane(wx.Panel(self), aui.AuiPaneInfo().Name("right_pane").Right())
            # set up default notebook style
            self._notebook_style = (aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | aui.AUI_NB_TAB_FLOAT |
                                    aui.AUI_NB_TAB_EXTERNAL_MOVE | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS)
            self._notebook_style ^= aui.AUI_NB_TAB_FIXED_WIDTH
            # DEBUG: self._notebook_theme = 0 (allow to select themes for notebooks)
            # DEBUG:self.notebook = NoteBook(self.splitter, self._application, self._notebook_style)
            self.notebook = NoteBook(self, self._application, self._notebook_style)
            self.notebook.SetFont(wx.Font(self.fontinfo))
            self.notebook.SetBackgroundColour(Colour(self.color_background))
            self.notebook.SetForegroundColour(Colour(self.color_foreground))
            self.aui_mgr.AddPane(self.notebook, aui.AuiPaneInfo().Name("notebook_editors").
                                 CenterPane().PaneBorder(True))
        # we need to remake Menu if language changes
        if self.main_menu:
            del self.main_menu
            pane = self.aui_mgr.GetPaneByName("maintoolbar")
            self.aui_mgr.DetachPane(pane)
            pane.DestroyOnClose(True)
            self.aui_mgr.ClosePane(pane)
            del pane
            # DEBUG: del self.toolbar

        _menudata = get_menudata()

        self.main_menu = MenuBar(self)
        self.main_menu.take_menu_bar_into_use()
        self.toolbar = ToolBar(self)
        self.toolbar.SetMinSize(wx.Size(100, 60))
        self.toolbar.SetBackgroundColour(Colour(self.color_background))
        self.toolbar.SetForegroundColour(Colour(self.color_foreground))
        # self.SetToolBar(self.toolbar.GetToolBar())
        self.main_menu._mb.SetFont(wx.Font(self.fontinfo))
        self.main_menu.m_frame.SetFont(wx.Font(self.fontinfo))
        self.main_menu.m_frame.SetBackgroundColour(Colour(self.color_background))
        self.main_menu.m_frame.SetForegroundColour(Colour(self.color_foreground))

        self.aui_mgr.AddPane(self.toolbar, aui.AuiPaneInfo().Name("maintoolbar").ToolbarPane().Top())
        self.actions = ActionRegisterer(self.aui_mgr, self.main_menu, self.toolbar, ShortcutRegistry(self))
        """
        ##### Test
        tb3 = self.testToolbar()

        self.aui_mgr.AddPane(tb3,
                          aui.AuiPaneInfo().Name("tb3").Caption("Toolbar 3").
                          ToolbarPane().Top().Row(1).Position(1))

        ##### End Test
        """
        # DEBUG: self.leftpanel = wx.Panel(self, name="left_panel", size = (275, 250))
        if new_ui:  # Only when creating UI we add panes
            # Tree is always created here
            self.tree = Tree(self, self.actions, self._application.settings)
            self.tree.SetMinSize(wx.Size(275, 250))
            self.tree.SetFont(wx.Font(self.fontinfo))
            # self.leftpanel.Bind(wx.EVT_SIZE, self.tree.OnSize)
            # self.aui_mgr.AddPane(self.leftpanel, aui.AuiPaneInfo().Name("left_panel").Caption("left_panel").Left())
            # DEBUG: Next was already called from application.py
            self.aui_mgr.AddPane(self.tree,
                                 aui.AuiPaneInfo().Name("tree_content").Caption(_("Test Suites")).CloseButton(False).
                                 LeftDockable())  # DEBUG: remove .CloseButton(False) when restore is fixed
            # DEBUG: self.aui_mgr.GetPane(self.tree).DestroyOnClose()
            # TreePlugin will manage showing the Tree
        self.actions.register_actions(action_info_collection(_menudata, self, data_nt=self._menudata_nt,
                                                             container=self.tree))
        if new_ui:  # Only when creating UI we add panes
            # ##### File explorer panel is always created here
            self.filemgr = FileExplorer(self, self.controller)
            self.filemgr.SetFont(wx.Font(self.fontinfo))
            self.filemgr.SetMinSize(wx.Size(275, 250))
            # DEBUG: Next was already called from application.py
            self.aui_mgr.AddPane(self.filemgr, aui.AuiPaneInfo().Name("file_manager").LeftDockable())

        # self.main_menu.take_menu_bar_into_use()
        if new_ui:  # Only when creating UI we add panes
            self.CreateStatusBar(name="StatusBar")
            self._status_bar = self.FindWindowByName("StatusBar", self)
            if self._status_bar:
                self._status_bar.SetFont(wx.Font(self.fontinfo))
                self._status_bar.SetBackgroundColour(Colour(self.color_background))
                self._status_bar.SetForegroundColour(Colour(self.color_foreground))
            # set main frame icon
            self.SetIcons(self._image_provider.PROGICONS)
        # change notebook theme
        self.set_notebook_theme()
        # tell the manager to "commit" all the changes just made
        self.aui_mgr.Update()
        # wx.CallLater(2000, RideSettingsChanged(keys=("General", ''), old='', new='').publish)

    def set_notebook_theme(self):
        if not self.notebook:
            return
        try:
            self._notebook_theme = int(self._notebook_theme)
        except ValueError:
            self._notebook_theme = 0
        if self._notebook_theme == 1:
            self.notebook.SetArtProvider(aui.AuiSimpleTabArt())
        elif self._notebook_theme == 2:
            self.notebook.SetArtProvider(aui.VC71TabArt())
        elif self._notebook_theme == 3:
            self.notebook.SetArtProvider(aui.FF2TabArt())
        elif self._notebook_theme == 4:
            self.notebook.SetArtProvider(aui.VC8TabArt())
        elif self._notebook_theme == 5:
            self.notebook.SetArtProvider(aui.ChromeTabArt())
        else:
            self.notebook.SetArtProvider(aui.AuiDefaultTabArt())

    def get_selected_datafile(self):
        return self.tree.get_selected_datafile()

    def get_selected_datafile_controller(self):
        return self.tree.get_selected_datafile_controller()

    def on_close(self, event):
        if self._allowed_to_exit():
            try:
                perspective = self.aui_mgr.SavePerspective()
                self._application.settings.set('AUI Perspective', perspective)
                # deinitialize the frame manager
                self.aui_mgr.UnInit()
                del self.aui_mgr
            except AttributeError:
                pass
            try:
                nb_perspective = self.notebook.SavePerspective()
                self._application.settings.set('AUI NB Perspective', nb_perspective)
            except AttributeError:
                pass
            PUBLISHER.unsubscribe(self._set_label, RideTreeSelection)
            RideClosing().publish()
            # DEBUG: Wrap in try/except for RunTime error
            try:
                self._task_bar_icon.RemoveIcon()
                self._task_bar_icon.Destroy()
            except RuntimeError:
                pass
            try:
                PUBLISHER.unsubscribe_all()
                self.Destroy()
                wx.Exit()
            except RuntimeError:
                pass
            app = wx.GetApp()
            if app is not self._application:
                # other wx app instance created unexpectedly
                # this will cause RIDE app instance cannot invoke ExitMainLoop properly
                self._application.ExitMainLoop()
            wx.Exit()
        else:
            wx.CloseEvent.Veto(event)

    def on_size(self, event):
        if wx.VERSION >= (4, 1, 0):
            size = self.DoGetSize()
        else:
            size = tuple(self.GetSize())
        is_full_screen_mode = size == wx.DisplaySize()
        self._application.settings[MAINFRAME_MAXIMIZED] = self.IsMaximized() or is_full_screen_mode
        if not is_full_screen_mode:
            self._application.settings['mainframe size'] = size
        if wx.VERSION >= (4, 1, 0):
            self._application.settings[MAINFRAME_POSITION] = self.DoGetPosition()
        else:
            self._application.settings[MAINFRAME_POSITION] = tuple(self.GetPosition())
        event.Skip()

    def on_move(self, event):
        # When the window is Iconized, a move event is also raised, but we
        # don't want to update the position in the settings file
        if not self.IsIconized() and not self.IsMaximized():
            if wx.VERSION >= (4, 1, 0):
                self._application.settings[MAINFRAME_POSITION] = self.DoGetPosition()
            else:
                self._application.settings[MAINFRAME_POSITION] = tuple(self.GetPosition())
        event.Skip()

    def on_maximize(self, event):
        self._application.settings[MAINFRAME_MAXIMIZED] = True
        event.Skip()

    def _allowed_to_exit(self):
        if self.has_unsaved_changes():
            ret = wx.MessageBox(_("There are unsaved modifications.\n"
                                  "Do you want to save your changes before "
                                  "exiting?"), _("Warning"), wx.ICON_WARNING | wx.CANCEL | wx.YES_NO)
            if ret == wx.CANCEL:
                return False
            if ret == wx.YES:
                self.save()
        return True

    def has_unsaved_changes(self):
        return self.controller.is_dirty()

    def on_new_project(self, event):
        __ = event
        if not self.check_unsaved_modifications():
            return
        NewProjectDialog(self.controller).execute()
        self._populate_tree()

    def _populate_tree(self):
        self.tree.populate(self.controller)
        self.filemgr.update_tree()

    def on_open_file(self, event):
        __ = event
        if not self.filemgr:
            return
        # EVT_DIRCTRL_FILEACTIVATED
        from os.path import splitext
        robottypes = self._application.settings.get('robot types', ['robot',
                                                                    'resource',
                                                                    'txt',
                                                                    'tsv'])  # Removed 'html'
        path = self.filemgr.GetFilePath()
        ext = ''
        if len(path) > 0:
            ext = splitext(path)
            ext = ext[1].replace('.', '')
            # print("DEBUG: path %s ext %s" % (path, ext))
        if len(ext) > 0 and ext in robottypes:
            if not self.check_unsaved_modifications():
                return
            if self.open_suite(path):
                return
        customsourceeditor.main(path)

    def on_menu_open_file(self, event):
        if not self.filemgr:
            return
        # DEBUG: Use widgets/popupmenu tools
        path = self.filemgr.GetFilePath()
        if len(path) > 0:
            self.on_open_file(event)
        else:
            path = self.filemgr.GetPath()
            if not self.check_unsaved_modifications():
                return
            self.open_suite(path)  # It is a directory, do not edit
        event.Skip()

    def on_open_external_file(self, event):
        __ = event
        if not self._current_external_dir:
            curdir = self.controller.default_dir
        else:
            curdir = self._current_external_dir
        fdlg = wx.FileDialog(self, defaultDir=curdir, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if fdlg.ShowModal() == wx.ID_CANCEL:
            return
        path = fdlg.GetPath()
        try:
            self._current_external_dir = os.path.dirname(path)
            customsourceeditor.main(path)
        except IOError:
            wx.LogError(f"Cannot open file {path}")

    def on_open_test_suite(self, event):
        __ = event
        if not self.check_unsaved_modifications():
            return
        path = RobotFilePathDialog(
            self, self.controller, self._application.settings).execute()
        if path:
            if self.open_suite(path):
                return
            customsourceeditor.main(path)

    def check_unsaved_modifications(self):
        if self.has_unsaved_changes():
            ret = wx.MessageBox(_("There are unsaved modifications.\n"
                                  "Do you want to proceed without saving?"), _("Warning"), wx.ICON_WARNING | wx.YES_NO)
            return ret == wx.YES
        return True

    def open_suite(self, path):
        self.controller.update_default_dir(path)
        # self._controller.default_dir will only save dir path
        # need to save path to self._application.workspace_path too
        self._application.workspace_path = path
        from ..lib.compat.parsing.language import check_file_language
        self.controller.file_language = check_file_language(path)
        set_lang = []
        set_lang.append('en')
        try:
            set_lang = shared_memory.ShareableList(name="language")
        except FileNotFoundError:
            set_lang[0] = 'en'
        if self.controller.file_language:
            set_lang[0] = self.controller.file_language[0]
            # print(f"DEBUG: project.py Project load_data file_language = {self.controller.file_language}\n"
            #       f"sharedmem={set_lang}")
        else:
            set_lang[0] = 'en'
        try:
            err = self.controller.load_datafile(path, LoadProgressObserver(self))
            if isinstance(err, UserWarning):
                # DEBUG: raise err  # Just leave message in Parser Log
                return False
        except UserWarning:
            return False
        self._populate_tree()
        return True

    def refresh_datafile(self, item, event):
        self.tree.refresh_datafile(item, event)
        if self.filemgr:
            self.filemgr.ReCreateTree()

    def on_open_directory(self, event):
        __ = event
        if self.check_unsaved_modifications():
            path = wx.DirSelector(message=_("Choose a directory containing Robot files"),
                                  default_path=self.controller.default_dir)
            if path:
                self.open_suite(path)

    def on_save(self, event):
        __ = event
        RideBeforeSaving().publish()
        self.save()

    def on_save_all(self, event):
        __ = event
        RideBeforeSaving().publish()
        self.save_all()

    def save_all(self):
        self._show_dialog_for_files_without_format()
        self.controller.execute(SaveAll(self.reformat))

    def save(self, controller=None):
        if controller is None:
            controller = self.get_selected_datafile_controller()
        if controller is not None:
            if not controller.has_format():
                self._show_dialog_for_files_without_format(controller)
            else:
                controller.execute(SaveFile(self.reformat))

    def _show_dialog_for_files_without_format(self, controller=None):
        files_without_format = self.controller.get_files_without_format(
            controller)
        for f in files_without_format:
            self._show_format_dialog_for(f)

    @staticmethod
    def _show_format_dialog_for(file_controller_without_format):
        InitFileFormatDialog(file_controller_without_format).execute()

    def on_exit(self, event):
        __ = event
        try:
            self.sharemem.shm.close()
            self.sharemem.shm.unlink()
        except FileNotFoundError:
            pass
        self.Close()

    def on_manage_plugins(self, event):
        __ = event
        self._plugin_manager.show(self._application.get_plugins())

    def on_view_all_tags(self, event):
        __ = event
        if self._view_all_tags_dialog is None:
            self._view_all_tags_dialog = ViewAllTagsDialog(self.controller, self)
        self._view_all_tags_dialog.show_dialog()

    def on_search_unused_keywords(self, event):
        __ = event
        if self._review_dialog is None:
            self._review_dialog = ReviewDialog(self.controller, self)
        self._review_dialog.show_dialog()

    def on_preferences(self, event):
        __ = event
        dlg = PreferenceEditor(self, _("RIDE - Preferences"),
                               self._application.preferences, style='tree')
        # Changed to non-modal, original comment follows:
        # I would prefer that this not be modal, but making it non-modal
        # opens up a can of worms. We don't want to have to deal
        # with settings getting changed out from under us while the
        # dialog is open.
        dlg.Show()

    @staticmethod
    def on_about(event):
        __ = event
        dlg = AboutDialog()
        dlg.ShowModal()
        dlg.Destroy()

    def on_check_for_upgrade(self, event):
        __ = event
        from ..application.updatenotifier import UpdateNotifierController, UpdateDialog
        wx.CallAfter(UpdateNotifierController(self.general_settings, self.notebook).notify_update_if_needed,
                     UpdateDialog, ignore_check_condition=True, show_no_update=True)

    @staticmethod
    def on_shortcut_keys(event):
        __ = event
        dialog = ShortcutKeysDialog()
        """ DEBUG:
            self.aui_mgr.AddPane(dialog.GetContentWindow(),aui.AuiPaneInfo().Name("shortcuts").Caption("Shortcuts Keys")
                                 .CloseButton(True).RightDockable().Floatable().Float(), self.notebook)
            self.aui_mgr.Update()
        """
        dialog.Show()

    @staticmethod
    def on_report_a_problem(event):
        __ = event
        wx.LaunchDefaultBrowser("https://github.com/robotframework/RIDE/issues"
                                "?utf8=%E2%9C%93&q=is%3Aissue+%22search"
                                "%20your%20problem%22"
                                )

    @staticmethod
    def on_user_guide(event):
        __ = event
        wx.LaunchDefaultBrowser("https://robotframework.org/robotframework/#user-guide")

    @staticmethod
    def on_wiki(event):
        __ = event
        wx.LaunchDefaultBrowser("https://github.com/robotframework/RIDE/wiki")

    def _has_data(self):
        return self.controller.data is not None

    def _refresh(self):
        self.controller.update_namespace()

    # This code is copied from http://wiki.wxpython.org/EnsureFrameIsOnScreen,
    # and adapted to fit our code style.
    def ensure_on_screen(self):
        try:
            display_id = wx.Display.GetFromWindow(self)
        except NotImplementedError:
            display_id = 0
        if display_id == -1:
            display_id = 0
        geometry = wx.Display(display_id).GetGeometry()
        position = self.GetPosition()
        if position.x < geometry.x:
            position.x = geometry.x
        if position.y < geometry.y:
            position.y = geometry.y
        size = self.GetSize()
        if size.width > geometry.width:
            size.width = geometry.width
            position.x = geometry.x
        elif position.x + size.width > geometry.x + geometry.width:
            position.x = geometry.x + geometry.width - size.width
        if size.height > geometry.height:
            size.height = geometry.height
            position.y = geometry.y
        elif position.y + size.height > geometry.y + geometry.height:
            position.y = geometry.y + geometry.height - size.height
        self.SetPosition(position)
        self.SetSize(size)

    def show_confirm_reload_dlg(self, event):
        msg = [_('Workspace modifications detected on the file system.'),
               _('Do you want to reload the workspace?')]
        if self.controller.is_dirty():
            msg += [_('Answering <Yes> will discard unsaved changes.'),
                    _('Answering <No> will ignore the changes on disk.')]
        ret = wx.MessageBox('\n'.join(msg), _('Files Changed On Disk'),
                            style=wx.YES_NO | wx.ICON_WARNING)
        confirmed = ret == wx.YES
        if confirmed:
            # workspace_path should update after open directory/suite
            # There are two scenarios:
            # 1. path is a directory
            # 2. path is a suite file
            new_path = RideFSWatcherHandler.get_workspace_new_path()
            if new_path and os.path.exists(new_path):
                wx.CallAfter(self.open_suite, new_path)
            else:
                # in case workspace is totally removed
                # ask user to open new directory
                # DEBUG: add some notification msg to users
                wx.CallAfter(self.on_open_directory, event)

    def on_ui_language_changed(self, message):
        if message.keys[0] != "General":
            return
        self.ui_language = self.general_settings.get('ui language', 'English')
        # print(f"DEBUG: mainframe.py on_ui_language_changed message.items={message.keys}, menudata={get_menudata}\n"
        #       f"language={self.ui_language} Translated Warning={_('Warning')} ")
        # DANGER!!! # The below refresh works, but we lose TestRunner buttons in taskbar and Edit menu is broken
        # wx.CallLater(1000, self._init_ui)  # Let the change happen at application


# Code moved from actiontriggers
class ToolBar(aui.AuiToolBar):

    def __init__(self, frame):
        aui.AuiToolBar.__init__(self, frame)
        # prepare a few custom overflow elements for the toolbars' overflow buttons
        prepend_items, append_items = [], []
        item = aui.AuiToolBarItem()

        item.SetKind(wx.ITEM_SEPARATOR)
        append_items.append(item)

        item = aui.AuiToolBarItem()
        item.SetKind(wx.ITEM_NORMAL)
        item.SetId(ID_CustomizeToolbar)
        item.SetLabel(_("Customize..."))
        append_items.append(item)

        self._frame = frame
        # DEBUG If we attach to frame it won't be detachable, and overlaps
        # If self, buttons are not shown
        self.tb = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                                 agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self.tb.SetToolBitmapSize(wx.Size(16, 16))
        self._buttons = []
        self._search_handlers = {}
        self._current_description = None
        self.SetMinSize(wx.Size(100, 60))
        self.tb.SetCustomOverflowItems(prepend_items, append_items)
        self.tb.Realize()

    def register(self, action):
        if action.has_icon():
            button = self._get_existing_button(action)
            if not button:
                button = self._create_button(action)
            button.register(action)

    def _get_existing_button(self, action):
        for button in self._buttons:
            if button.icon == action.icon:
                return button
        return None

    def enabled_status_changed(self, idd, action):
        self.EnableTool(idd, action.is_active())

    def _create_button(self, action):
        button = ToolBarButton(self._frame, self, action)
        name = self._format_button_tooltip(action)
        self.AddTool(button.id, name, action.icon, wx.NullBitmap,
                     wx.ITEM_NORMAL, name, action.doc)
        self.Realize()
        self._buttons.append(button)
        return button

    @staticmethod
    def _format_button_tooltip(action):
        tooltip = action.name.replace('&', '')
        if action.shortcut and action.shortcut.value:
            tooltip = '%s    (%s)' % (tooltip, action.shortcut.value)
        return tooltip

    def remove_toolbar_button(self, button):
        self._buttons.remove(button)
        self.DeleteTool(button.id)
        self.Realize()

    def register_search_handler(self, description, handler, icon,
                                default=False):
        if default:
            self._current_description = description
        self._search_handlers[description] = _RideSearchMenuItem(handler, icon)


class ActionRegisterer(object):

    def __init__(self, aui_mgr, menubar, toolbar, shortcut_registry):
        self._aui_mgr = aui_mgr
        self._menubar = menubar
        self._toolbar = toolbar
        self._shortcut_registry = shortcut_registry
        self._tools_items = dict()

    def register_action(self, action_info, update_aui=True):
        menubar_can_be_registered = True
        action = action_factory(action_info)
        self._shortcut_registry.register(action)
        if hasattr(action_info, "menu_name"):
            # print(f"DEBUG: mainframe.py ActionRegister register_action menu_name={action_info.menu_name}")
            if action_info.menu_name == _("Tools"):
                self._tools_items[action_info.position] = action
                menubar_can_be_registered = False
        if menubar_can_be_registered:
            self._menubar.register(action)
        self._toolbar.register(action)
        if update_aui:
            # tell the manager to "commit" all the changes just made
            self._aui_mgr.Update()
        return action

    def register_tools(self):
        separator_action = action_factory(SeparatorInfo(_("Tools")))
        add_separator_after = [_("stop test run"), _("search unused keywords"),
                               _("preview"), _("view ride log")]
        # for key in sorted(self._tools_items.iterkeys()):
        # print("DEBUG: at register_tools, tools: %s" % self._tools_items)
        for key in sorted(self._tools_items.keys()):  # DEBUG Python3
            self._menubar.register(self._tools_items[key])
            # print("DEBUG: key=%s name=%s" % (key, self._tools_items[key].name.lower()))
            if self._tools_items[key].name.lower() in add_separator_after:
                self._menubar.register(separator_action)

    def register_actions(self, actions):
        for action in actions:
            if not isinstance(action, SeparatorInfo):  # DEBUG
                # print("DEBUG: action=%s" % action.name)
                self.register_action(action, update_aui=False)
        # tell the manager to "commit" all the changes just made
        self._aui_mgr.Update()

    def register_shortcut(self, action_info):
        action = action_factory(action_info)
        self._shortcut_registry.register(action)
        return action


class AboutDialog(RIDEDialog):

    def __init__(self):
        RIDEDialog.__init__(self, title='RIDE')
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        sizer = wx.BoxSizer(wx.VERTICAL)
        content = get_about_ride()
        sizer.Add(HtmlWindow(self, (650, 350), content), 1, flag=wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def on_key(self, *args):
        """ Just ignore keystrokes """
        pass


class ShortcutKeysDialog(RIDEDialog):

    def __init__(self):
        RIDEDialog.__init__(self, title=_("Shortcut keys for RIDE"))
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(HtmlWindow(self, (350, 400),
                             self._get_platform_specific_shortcut_keys()), 1,
                  flag=wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def on_key(self, *args):
        """ Just ignore keystrokes """
        pass

    @staticmethod
    def _get_platform_specific_shortcut_keys():
        return localize_shortcuts(SHORTCUT_KEYS)


class RIDETaskBarIcon(TaskBarIcon):

    def __init__(self, frame, img_provider):
        TaskBarIcon.__init__(self, TBI_DOCK)
        self.frame = frame
        self._img_provider = img_provider
        self.SetIcon(wx.Icon(self._img_provider.RIDE_ICON), "RIDE")
        self.Bind(EVT_TASKBAR_LEFT_DOWN, self.on_click)
        self.Bind(wx.EVT_MENU, self.on_task_bar_activate, id=1)
        self.Bind(wx.EVT_MENU, self.on_task_bar_deactivate, id=2)
        self.Bind(wx.EVT_MENU, self.on_task_bar_close, id=3)

    def on_click(self, event):
        __ = event
        self.frame.Raise()
        self.frame.Restore()
        self.frame.Show(True)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(1, _('Show'))
        menu.Append(2, _('Hide'))
        menu.Append(3, _('Close'))
        return menu

    def on_task_bar_close(self, event):
        __ = event
        self.frame.Close()

    def on_task_bar_activate(self, event):
        __ = event
        if not self.frame.IsShown():
            self.frame.Show()
            self.frame.Restore()

    def on_task_bar_deactivate(self, event):
        __ = event
        if self.frame.IsShown():
            self.frame.Hide()
