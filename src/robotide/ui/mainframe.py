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

import os

import wx
import wx.lib.agw.aui as aui
from wx import Colour
from wx.adv import TaskBarIcon, TBI_DOCK

from .actiontriggers import (MenuBar, ToolBarButton, ShortcutRegistry, _RideSearchMenuItem)
from .filedialogs import (NewProjectDialog, InitFileFormatDialog)
from .fileexplorerplugin import FileExplorer
from .notebook import NoteBook
from .pluginmanager import PluginManager
from .progress import LoadProgressObserver
from .review import ReviewDialog
from .treeplugin import Tree
from ..action import ActionInfoCollection, ActionFactory, SeparatorInfo
from ..action.shortcut import localize_shortcuts
from ..context import ABOUT_RIDE, SHORTCUT_KEYS, IS_MAC
from ..controller.ctrlcommands import SaveFile, SaveAll
from ..editor import customsourceeditor
from ..preferences import PreferenceEditor
from ..preferences.settings import RideSettings, _Section
from ..publish import (RideSaveAll, RideClosing, RideSaved, PUBLISHER, RideInputValidationError, RideTreeSelection,
                       RideModificationPrevented, RideBeforeSaving, RideSettingsChanged)
from ..ui.filedialogs import RobotFilePathDialog
from ..ui.tagdialogs import ViewAllTagsDialog
from ..utils import RideFSWatcherHandler
from ..widgets import RIDEDialog, ImageProvider, HtmlWindow

_menudata = """
[File]
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
!Release notes | Shows release notes
!About | Information about RIDE
"""

ID_CustomizeToolbar = wx.ID_HIGHEST + 1
ID_SampleItem = ID_CustomizeToolbar + 1


"""

# -- DEBUG some testing
# -- SizeReportCtrl --
# (a utility control that always reports it's client size)


class SizeReportCtrl(wx.Control):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, mgr=None):

        wx.Control.__init__(self, parent, id, pos, size, style=wx.NO_BORDER)
        self._mgr = mgr

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, event):

        dc = wx.PaintDC(self)
        size = self.GetClientSize()

        s = "Size: %d x %d" % (size.x, size.y)

        dc.SetFont(wx.NORMAL_FONT)
        w, height = dc.GetTextExtent(s)
        height += 3
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.WHITE_PEN)
        dc.DrawRectangle(0, 0, size.x, size.y)
        dc.SetPen(wx.LIGHT_GREY_PEN)
        dc.DrawLine(0, 0, size.x, size.y)
        dc.DrawLine(0, size.y, size.x, 0)
        dc.DrawText(s, (size.x-w)/2, (size.y-height*5)/2)

        if self._mgr:

            pi = self._mgr.GetPane(self)

            s = "Layer: %d" % pi.dock_layer
            w, h = dc.GetTextExtent(s)
            dc.DrawText(s, (size.x-w)/2, ((size.y-(height*5))/2)+(height*1))

            s = "Dock: %d Row: %d" % (pi.dock_direction, pi.dock_row)
            w, h = dc.GetTextExtent(s)
            dc.DrawText(s, (size.x-w)/2, ((size.y-(height*5))/2)+(height*2))

            s = "Position: %d" % pi.dock_pos
            w, h = dc.GetTextExtent(s)
            dc.DrawText(s, (size.x-w)/2, ((size.y-(height*5))/2)+(height*3))

            s = "Proportion: %d" % pi.dock_proportion
            w, h = dc.GetTextExtent(s)
            dc.DrawText(s, (size.x-w)/2, ((size.y-(height*5))/2)+(height*4))

    def OnEraseBackground(self, event):
        pass

    def OnSize(self, event):
        self.Refresh()
"""


class RideFrame(wx.Frame):

    def __init__(self, application, controller):
        size = application.settings.get('mainframe size', (1100, 700))
        # DEBUG self.general_settings = application.settings['General']
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY, title='RIDE',
                          pos=application.settings.get('mainframe position', (50, 30)),
                          size=size, style=wx.DEFAULT_FRAME_STYLE | wx.SUNKEN_BORDER | wx.BORDER_THEME)

        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        # self.SetLayoutDirection(wx.Layout_RightToLeft)

        self._mgr = aui.AuiManager()

        # tell AuiManager to manage this frame
        self._mgr.SetManagedWindow(self)

        self.SetMinSize(wx.Size(400, 300))

        self.ensure_on_screen()
        if application.settings.get('mainframe maximized', False):
            self.Maximize()
        self._application = application
        self._controller = controller
        self._image_provider = ImageProvider()
        self.reformat = application.settings.get('reformat', False)
        self.general_settings = application.settings['General']  #.get_without_default('General')
        self.color_background_help = self.general_settings.get('background help', (240, 242, 80))
        self.color_foreground_text = self.general_settings.get('foreground text', (7, 0, 70))
        self.color_background = self.general_settings.get_without_default('background')
        self.color_foreground = self.general_settings.get_without_default('foreground')
        self.font_face = self.general_settings.get('font face', '')
        self.font_size = self.general_settings.get('font size', 11)
        self._init_ui()
        self._task_bar_icon = RIDETaskBarIcon(self._image_provider)
        self._plugin_manager = PluginManager(self.notebook)
        self._review_dialog = None
        self._view_all_tags_dialog = None
        self._current_external_dir = None
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_MAXIMIZE, self.OnMaximize)
        self.Bind(wx.EVT_DIRCTRL_FILEACTIVATED, self.OnOpenFile)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnMenuOpenFile)
        self._subscribe_messages()
        wx.CallAfter(self.actions.register_tools)  # DEBUG
        # DEBUG wx.CallAfter(self.OnSettingsChanged, self.general_settings)

    def _subscribe_messages(self):
        for listener, topic in [
            (lambda message: self.SetStatusText('Saved %s' % message.path), RideSaved),
            (lambda message: self.SetStatusText('Saved all files'), RideSaveAll),
            (self._set_label, RideTreeSelection),
            (self._show_validation_error, RideInputValidationError),
            (self._show_modification_prevented_error, RideModificationPrevented),
            # (self.OnSettingsChanged, RideSettingsChanged)
        ]:
            PUBLISHER.subscribe(listener, topic)

    def _set_label(self, message):
        self.SetTitle(self._create_title(message))

    def _create_title(self, message):
        title = 'RIDE'
        if message:
            item = message.item
            title += ' - ' + item.datafile.name
            if not item.is_modifiable():
                title += ' (READ ONLY)'
        return title

    def _show_validation_error(self, message):
        wx.MessageBox(message.message, 'Validation Error', style=wx.ICON_ERROR)

    def _show_modification_prevented_error(self, message):
        wx.MessageBox("\"%s\" is read only" % message.controller.datafile_controller.filename, "Modification prevented",
                      style=wx.ICON_ERROR)

    def _init_ui(self):
        # self._mgr.AddPane(wx.Panel(self), aui.AuiPaneInfo().CenterPane())
        # #### self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        # self._mgr.AddPane(wx.Panel(self), aui.AuiPaneInfo().CenterPane())
        # set up default notebook style
        self._notebook_style = aui.AUI_NB_DEFAULT_STYLE | aui.AUI_NB_WINDOWLIST_BUTTON | \
                               aui.AUI_NB_TAB_EXTERNAL_MOVE | aui.AUI_NB_SUB_NOTEBOOK | aui.AUI_NB_SMART_TABS  #| wx.NO_BORDER
        # TODO self._notebook_theme = 0 (allow to select themes for notebooks)
        # self.notebook = NoteBook(self.splitter, self._application,
        #                         self._notebook_style)
        self.notebook = NoteBook(self, self._application,
                                 self._notebook_style)
        self.notebook.SetBackgroundColour(Colour(self.color_background))
        self.notebook.SetForegroundColour(Colour(self.color_foreground))
        self._mgr.AddPane(self.notebook,
                          aui.AuiPaneInfo().Name("notebook_editors").
                          CenterPane().PaneBorder(False))
        # ############### Test
        # self._mgr.AddPane(self.CreateTextCtrl(),
        #                   aui.AuiPaneInfo().Name("text_content").
        #                   CenterPane().Hide().MinimizeButton(True))
        #
        # self._mgr.AddPane(self.CreateHTMLCtrl(),
        #                   aui.AuiPaneInfo().Name("html_content").
        #                   CenterPane().Hide().MinimizeButton(True))
        #
        # self._mgr.AddPane(self.CreateNotebook(),
        #                   aui.AuiPaneInfo().Name("notebook_content").
        #                   CenterPane().PaneBorder(False))
        # ###################
        # self._mgr.AddPane(self.CreateSizeReportCtrl(), aui.AuiPaneInfo().
        #                   Name("test1").Caption(
        #     "Pane Caption").Top().MinimizeButton(True))

        mb = MenuBar(self)
        self.toolbar = ToolBar(self)
        self.toolbar.SetMinSize(wx.Size(100, 60))
        self.toolbar.SetBackgroundColour(Colour(self.color_background))
        self.toolbar.SetForegroundColour(Colour(self.color_foreground))
        # self.SetToolBar(self.toolbar.GetToolBar())
        mb._frame.SetBackgroundColour(Colour(self.color_background))
        mb._frame.SetForegroundColour(Colour(self.color_foreground))
        self._mgr.AddPane(self.toolbar, aui.AuiPaneInfo().Name("maintoolbar").
                          ToolbarPane().Top())
        self.actions = ActionRegisterer(self._mgr, mb, self.toolbar,
                                        ShortcutRegistry(self))
        """
        ##### Test
        tb3 = self.testToolbar()

        self._mgr.AddPane(tb3,
                          aui.AuiPaneInfo().Name("tb3").Caption("Toolbar 3").
                          ToolbarPane().Top().Row(1).Position(1))
        
        ##### End Test
        """
        # self.leftpanel = wx.Panel(self, name="left_panel", size = (275, 250))
        # Tree is always created here
        self.tree = Tree(self, self.actions, self._application.settings)
        self.tree.SetMinSize(wx.Size(275, 250))
        # self.leftpanel.Bind(wx.EVT_SIZE, self.tree.OnSize)
        # self._mgr.AddPane(self.leftpanel, aui.AuiPaneInfo().Name("left_panel").Caption("left_panel").Left())
        # DEBUG: Next was already called from application.py
        self._mgr.AddPane(self.tree,
                          aui.AuiPaneInfo().Name("tree_content").Caption("Test Suites").CloseButton(False).
                          LeftDockable())  # TODO: remove .CloseButton(False) when restore is fixed
        #### self._mgr.GetPane(self.tree).DestroyOnClose()
        # TreePlugin will manage showing the Tree
        self.actions.register_actions(ActionInfoCollection(_menudata, self, self.tree))
        # ##### File explorer panel is always created here
        self.filemgr = FileExplorer(self, self._controller)
        self.filemgr.SetMinSize(wx.Size(275, 250))
        # DEBUG: Next was already called from application.py
        self._mgr.AddPane(self.filemgr,
                          aui.AuiPaneInfo().Name("file_manager").
                          LeftDockable())

        mb.take_menu_bar_into_use()
        self.CreateStatusBar(name="StatusBar")
        self._status_bar = self.FindWindowByName("StatusBar", self)
        if self._status_bar:
            self._status_bar.SetBackgroundColour(Colour(self.color_background))
            self._status_bar.SetForegroundColour(Colour(self.color_foreground))
        # set main frame icon
        self.SetIcons(self._image_provider.PROGICONS)
        # tell the manager to "commit" all the changes just made
        self._mgr.Update()
        # wx.CallLater(2000, RideSettingsChanged(keys=("General", ''), old='', new='').publish)

    """
    def testToolbar(self):

        # ### More testing
        prepend_items, append_items = [], []
        item = aui.AuiToolBarItem()

        item.SetKind(wx.ITEM_SEPARATOR)
        append_items.append(item)

        item = aui.AuiToolBarItem()
        item.SetKind(wx.ITEM_NORMAL)
        item.SetId(ID_CustomizeToolbar)
        item.SetLabel("Customize...")
        append_items.append(item)

        tb3 = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                             agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        tb3.SetToolBitmapSize(wx.Size(16, 16))
        tb3_bmp1 = wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER,
                                            wx.Size(16, 16))
        tb3.AddSimpleTool(ID_SampleItem + 16, "Check 1", tb3_bmp1, "Check 1",
                          aui.ITEM_CHECK)
        tb3.AddSimpleTool(ID_SampleItem + 17, "Check 2", tb3_bmp1, "Check 2",
                          aui.ITEM_CHECK)
        tb3.AddSimpleTool(ID_SampleItem + 18, "Check 3", tb3_bmp1, "Check 3",
                          aui.ITEM_CHECK)
        tb3.AddSimpleTool(ID_SampleItem + 19, "Check 4", tb3_bmp1, "Check 4",
                          aui.ITEM_CHECK)
        tb3.AddSeparator()
        tb3.AddSimpleTool(ID_SampleItem + 20, "Radio 1", tb3_bmp1, "Radio 1",
                          aui.ITEM_RADIO)
        tb3.AddSimpleTool(ID_SampleItem + 21, "Radio 2", tb3_bmp1, "Radio 2",
                          aui.ITEM_RADIO)
        tb3.AddSimpleTool(ID_SampleItem + 22, "Radio 3", tb3_bmp1, "Radio 3",
                          aui.ITEM_RADIO)
        tb3.AddSeparator()
        tb3.AddSimpleTool(ID_SampleItem + 23, "Radio 1 (Group 2)", tb3_bmp1,
                          "Radio 1 (Group 2)", aui.ITEM_RADIO)
        tb3.AddSimpleTool(ID_SampleItem + 24, "Radio 2 (Group 2)", tb3_bmp1,
                          "Radio 2 (Group 2)", aui.ITEM_RADIO)
        tb3.AddSimpleTool(ID_SampleItem + 25, "Radio 3 (Group 2)", tb3_bmp1,
                          "Radio 3 (Group 2)", aui.ITEM_RADIO)

        tb3.SetCustomOverflowItems(prepend_items, append_items)
        tb3.Realize()
        return tb3
    """

    def get_selected_datafile(self):
        return self.tree.get_selected_datafile()

    def get_selected_datafile_controller(self):
        return self.tree.get_selected_datafile_controller()

    def OnClose(self, event):
        if self._allowed_to_exit():
            try:
                perspective = self._mgr.SavePerspective()
                self._application.settings.set('AUI Perspective', perspective)
                # deinitialize the frame manager
                self._mgr.UnInit()
                del self._mgr
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
            self._task_bar_icon.Destroy()
            self.Destroy()
            app = wx.GetApp()
            if app is not self._application:
                # other wx app instance created unexpectedly
                # this will cause RIDE app instance cannot invoke ExitMainLoop properly
                self._application.ExitMainLoop()
            wx.Exit()
        else:
            wx.CloseEvent.Veto(event)

    def OnSize(self, event):
        if wx.VERSION >= (4, 1, 0):
            size = self.DoGetSize()
        else:
            size = tuple(self.GetSize())
        is_full_screen_mode = size == wx.DisplaySize()
        self._application.settings['mainframe maximized'] = self.IsMaximized() or is_full_screen_mode
        if not is_full_screen_mode:
            self._application.settings['mainframe size'] = size
        if wx.VERSION >= (4, 1, 0):
            self._application.settings['mainframe position'] = self.DoGetPosition()
        else:
            self._application.settings['mainframe position'] = tuple(self.GetPosition())
        event.Skip()

    def OnMove(self, event):
        # When the window is Iconized, a move event is also raised, but we
        # don't want to update the position in the settings file
        if not self.IsIconized() and not self.IsMaximized():
            if wx.VERSION >= (4, 1, 0):
                self._application.settings['mainframe position'] = self.DoGetPosition()
            else:
                self._application.settings['mainframe position'] = tuple(self.GetPosition())
        event.Skip()

    def OnMaximize(self, event):
        self._application.settings['mainframe maximized'] = True
        event.Skip()

    def OnReleasenotes(self, event):
        pass

    def _allowed_to_exit(self):
        if self.has_unsaved_changes():
            ret = wx.MessageBox("There are unsaved modifications.\n"
                                "Do you want to save your changes before "
                                "exiting?", "Warning",
                                wx.ICON_WARNING | wx.CANCEL | wx.YES_NO)
            if ret == wx.CANCEL:
                return False
            if ret == wx.YES:
                self.save()
        return True

    def has_unsaved_changes(self):
        return self._controller.is_dirty()

    def OnNewProject(self, event):
        if not self.check_unsaved_modifications():
            return
        NewProjectDialog(self._controller).execute()
        self._populate_tree()

    def _populate_tree(self):
        self.tree.populate(self._controller)
        self.filemgr.update_tree()

    def OnOpenFile(self, event):
        if not self.filemgr:
            return
        # EVT_DIRCTRL_FILEACTIVATED
        from os.path import splitext
        robottypes = self._application.settings.get('robot types', ['robot',
                                                                    'resource',
                                                                    'txt',
                                                                    'tsv',
                                                                    'html'])
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

    def OnMenuOpenFile(self, event):
        if not self.filemgr:
            return
        # TODO: Use widgets/popupmenu tools
        path = self.filemgr.GetFilePath()
        if len(path) > 0:
            self.OnOpenFile(event)
        else:
            path = self.filemgr.GetPath()
            if not self.check_unsaved_modifications():
                return
            self.open_suite(path)  # It is a directory, do not edit
        event.Skip()

    def OnOpenExternalFile(self, event):
        if not self._current_external_dir:
            curdir = self._controller.default_dir
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

    def OnOpenTestSuite(self, event):
        if not self.check_unsaved_modifications():
            return
        path = RobotFilePathDialog(
            self, self._controller, self._application.settings).execute()
        if path:
            if self.open_suite(path):
                return
            customsourceeditor.main(path)

    def check_unsaved_modifications(self):
        if self.has_unsaved_changes():
            ret = wx.MessageBox("There are unsaved modifications.\n"
                                "Do you want to proceed without saving?",
                                "Warning", wx.ICON_WARNING | wx.YES_NO)
            return ret == wx.YES
        return True

    def open_suite(self, path):
        self._controller.update_default_dir(path)
        # self._controller.default_dir will only save dir path
        # need to save path to self._application.workspace_path too
        self._application.workspace_path = path
        err = None
        try:
            err = self._controller.load_datafile(path, LoadProgressObserver(self))
        finally:
            if isinstance(err, UserWarning):
                # raise err  # Just leave message in Parser Log
                return False
        self._populate_tree()
        return True

    def refresh_datafile(self, item, event):
        self.tree.refresh_datafile(item, event)
        if self.filemgr:
            self.filemgr.ReCreateTree()

    def OnOpenDirectory(self, event):
        if self.check_unsaved_modifications():
            path = wx.DirSelector(message="Choose a directory containing Robot"
                                          " files",
                                  default_path=self._controller.default_dir)
            if path:
                self.open_suite(path)

    def OnSave(self, event):
        RideBeforeSaving().publish()
        self.save()

    def OnSaveAll(self, event):
        RideBeforeSaving().publish()
        self.save_all()

    def save_all(self):
        self._show_dialog_for_files_without_format()
        self._controller.execute(SaveAll(self.reformat))

    def save(self, controller=None):
        if controller is None:
            controller = self.get_selected_datafile_controller()
        if controller is not None:
            if not controller.has_format():
                self._show_dialog_for_files_without_format(controller)
            else:
                controller.execute(SaveFile(self.reformat))

    def _show_dialog_for_files_without_format(self, controller=None):
        files_without_format = self._controller.get_files_without_format(
            controller)
        for f in files_without_format:
            self._show_format_dialog_for(f)

    def _show_format_dialog_for(self, file_controller_without_format):
        InitFileFormatDialog(file_controller_without_format).execute()

    def OnExit(self, event):
        self.Close()

    def OnManagePlugins(self, event):
        self._plugin_manager.show(self._application.get_plugins())

    def OnViewAllTags(self, event):
        if self._view_all_tags_dialog is None:
            self._view_all_tags_dialog = ViewAllTagsDialog(self._controller, self)
        self._view_all_tags_dialog.show_dialog()

    def OnSearchUnusedKeywords(self, event):
        if self._review_dialog is None:
            self._review_dialog = ReviewDialog(self._controller, self)
        self._review_dialog.show_dialog()

    def OnPreferences(self, event):
        dlg = PreferenceEditor(self, "RIDE - Preferences",
                               self._application.preferences, style='tree')
        # Changed to non-modal, original comment follows:
        # I would prefer that this not be modal, but making it non-
        # modal opens up a can of worms. We don't want to have to deal
        # with settings getting changed out from under us while the
        # dialog is open.
        dlg.Show()

    @staticmethod
    def OnAbout(event):
        dlg = AboutDialog()
        dlg.ShowModal()
        dlg.Destroy()

    @staticmethod
    def OnShortcutkeys(event):
        dialog = ShortcutKeysDialog()
        dialog.Show()

    @staticmethod
    def OnReportaProblem(event):
        wx.LaunchDefaultBrowser("https://github.com/robotframework/RIDE/issues"
                                "?utf8=%E2%9C%93&q=is%3Aissue+%22search"
                                "%20your%20problem%22"
                                )

    @staticmethod
    def OnUserGuide(event):
        wx.LaunchDefaultBrowser("http://robotframework.org/robotframework/"
                                "#user-guide")

    @staticmethod
    def OnWiki(event):
        wx.LaunchDefaultBrowser("https://github.com/robotframework/RIDE/wiki")

    def _has_data(self):
        return self._controller.data is not None

    def _refresh(self):
        self._controller.update_namespace()

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

    # DEBUG just some testing
    """
    def CreateSizeReportCtrl(self, width=80, height=80):

        ctrl = SizeReportCtrl(self, -1, wx.DefaultPosition, wx.Size(width, height), self._mgr)
        return ctrl
    """

    def show_confirm_reload_dlg(self, event):
        msg = ['Workspace modifications detected on the file system.',
               'Do you want to reload the workspace?',
               'Answering <No> will overwrite the changes on disk.']
        if self._controller.is_dirty():
            msg.insert(2, 'Answering <Yes> will discard unsaved changes.')
        ret = wx.MessageBox('\n'.join(msg), 'Files Changed On Disk',
                            style=wx.YES_NO | wx.ICON_WARNING)
        confirmed = ret == wx.YES
        if confirmed:
            # workspace_path should update after open directory/suite
            # There're two scenarios:
            # 1. path is a directory
            # 2. path is a suite file
            new_path = RideFSWatcherHandler.get_workspace_new_path()
            if new_path and os.path.exists(new_path):
                wx.CallAfter(self.open_suite, new_path)
            else:
                # in case workspace is totally removed
                # ask user to open new directory
                # TODO add some notification msg to users
                wx.CallAfter(self.OnOpenDirectory, event)
        else:
            for _ in self._controller.datafiles:
                if _.has_been_modified_on_disk() or _.has_been_removed_from_disk():
                    if not os.path.exists(_.directory):
                        # sub folder is removed, create new one before saving
                        os.makedirs(_.directory)
                    _.mark_dirty()
            self.save_all()
"""
    def OnSettingsChanged(self, message):
        #TODO: change to doc Redraw the colors if the color settings are modified
        # section, setting = data.keys
        #print(f"DEBUG: OnSettingsChanged enter {repr(message)}")
        if isinstance(message, _Section):
            ndata= message
            # print(f"DEBUG: OnSettingsChanged in Section {type(ndata)}")
            for key, value in message:
                # print(f"DEBUG: OnSettingsChanged in key {key} value {value}")
            background = message.get_without_default('background')
            foreground = message.get_without_default('foreground')
            # print(f"DEBUG: OnSettings section: {message._is_section('General')} background {background}"
                  f" foreground {foreground}")
            if message._is_section('General'):
                internal_settings = RideSettings()
                _general_settings = internal_settings['General']
                children = self.GetChildren()
                for child in children:
                    child.SetBackgroundColour(Colour(_general_settings['background']))
                    child.SetOwnBackgroundColour(Colour(_general_settings['background']))
                    child.SetForegroundColour(Colour(_general_settings['foreground']))
                    child.SetOwnForegroundColour(Colour(_general_settings['foreground']))
                    font = child.GetFont()
                    font.SetFaceName(_general_settings['font face'])
                    font.SetPointSize(_general_settings['font size'])
                    child.SetFont(font)
                    child.Refresh(True)
                    # print(f"DEBUG: OnSettingsChanged child {type(child)}")
            # print(f"DEBUG: OnSettingsChanged not General")
"""


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
        item.SetLabel("Customize...")
        append_items.append(item)

        self._frame = frame
        # DEBUG If we attach to frame it won't be detachable, and overlaps
        # If self, buttons are not shown
        self.tb = aui.AuiToolBar(self, -1, wx.DefaultPosition,
                            wx.DefaultSize,
                            agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self.tb.SetToolBitmapSize(wx.Size(16, 16))
        self._buttons = []
        self._search_handlers = {}
        self._current_description = None
        self.SetMinSize(wx.Size(100, 60))
        # self.tb.SetBackgroundColour(Colour(self._frame.color_background))
        # self.tb.SetForegroundColour(Colour(self._frame.color_foreground))
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

    def enabled_status_changed(self, id, action):
        self.EnableTool(id, action.is_active())

    def _create_button(self, action):
        button = ToolBarButton(self._frame, self, action)
        name = self._format_button_tooltip(action)
        self.AddTool(button.id, name, action.icon, wx.NullBitmap,
                     wx.ITEM_NORMAL, name, action.doc)
        self.Realize()
        self._buttons.append(button)
        return button

    def _format_button_tooltip(self, action):
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
        action = ActionFactory(action_info)
        self._shortcut_registry.register(action)
        if hasattr(action_info, "menu_name"):
            if action_info.menu_name == "Tools":
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
        separator_action = ActionFactory(SeparatorInfo("Tools"))
        add_separator_after = ["stop test run", "search unused keywords",
                               "preview", "view ride log"]
        #for key in sorted(self._tools_items.iterkeys()):
        # print("DEBUG: at register_tools, tools: %s" % self._tools_items)
        for key in sorted(self._tools_items.keys()):  #DEBUG Python3
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
        action = ActionFactory(action_info)
        self._shortcut_registry.register(action)
        return action


class AboutDialog(RIDEDialog):

    def __init__(self):
        RIDEDialog.__init__(self, title='RIDE')
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(HtmlWindow(self, (650, 200), ABOUT_RIDE), 1, flag=wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def OnKey(self, *args):
        pass


class ShortcutKeysDialog(RIDEDialog):

    def __init__(self):
        RIDEDialog.__init__(self, title="Shortcut keys for RIDE")
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(HtmlWindow(self, (350, 400),
                             self._get_platform_specific_shortcut_keys()), 1,
                  flag=wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def OnKey(self, *args):
        pass

    def _get_platform_specific_shortcut_keys(self):
        return localize_shortcuts(SHORTCUT_KEYS)


class RIDETaskBarIcon(TaskBarIcon):

    def __init__(self, img_provider):
        TaskBarIcon.__init__(self, TBI_DOCK)
        self._img_provider = img_provider
        # if IS_MAC:
        #    # only use in mac to display RIDE app icon in dock
        self.SetIcon(wx.Icon(self._img_provider.RIDE_ICON), "RIDE")
