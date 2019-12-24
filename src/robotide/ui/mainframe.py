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
from wx import Icon
from wx.lib.agw.aui import aui_switcherdialog as ASD
from robotide.lib.robot.utils.compat import with_metaclass
from robotide.action import ActionInfoCollection, ActionFactory, SeparatorInfo
from robotide.context import ABOUT_RIDE, SHORTCUT_KEYS
from robotide.controller.ctrlcommands import SaveFile, SaveAll
from robotide.publish import RideSaveAll, RideClosing, RideSaved, PUBLISHER,\
    RideInputValidationError, RideTreeSelection, RideModificationPrevented
from robotide.ui.tagdialogs import ViewAllTagsDialog
from robotide.ui.filedialogs import RobotFilePathDialog
from robotide.utils import RideEventHandler, PY2
from robotide.widgets import Dialog, ImageProvider, HtmlWindow
from robotide.preferences import PreferenceEditor

from .actiontriggers import ( MenuBar, ToolBarButton, ShortcutRegistry,
                              _RideSearchMenuItem)
from .filedialogs import (NewProjectDialog, InitFileFormatDialog)
from .review import ReviewDialog
from .pluginmanager import PluginManager
from robotide.action.shortcut import localize_shortcuts
from .tree import Tree
from .notebook import NoteBook
from .progress import LoadProgressObserver


_menudata = """
[File]
!&New Project | Create a new top level suite | Ctrlcmd-N
---
!&Open Test Suite | Open file containing tests | Ctrlcmd-O | ART_FILE_OPEN
!Open &Directory | Open directory containing datafiles | Shift-Ctrlcmd-O | \
ART_FOLDER_OPEN
---
&Save | Save selected datafile | Ctrlcmd-S | ART_FILE_SAVE
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

# Metaclass fix from http://code.activestate.com/recipes/
# 204197-solving-the-metaclass-conflict/
from robotide.utils.noconflict import classmaker

### DEBUG some testing
# -- SizeReportCtrl --
# (a utility control that always reports it's client size)


class SizeReportCtrl(wx.Control):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                size=wx.DefaultSize, mgr=None):

        wx.Control.__init__(self, parent, id, pos, size, style=wx.NO_BORDER)
        self._mgr = mgr

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnPaint(self, event):

        dc = wx.PaintDC(self)
        size = self.GetClientSize()

        s = "Size: %d x %d"%(size.x, size.y)

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

            s = "Layer: %d"%pi.dock_layer
            w, h = dc.GetTextExtent(s)
            dc.DrawText(s, (size.x-w)/2, ((size.y-(height*5))/2)+(height*1))

            s = "Dock: %d Row: %d"%(pi.dock_direction, pi.dock_row)
            w, h = dc.GetTextExtent(s)
            dc.DrawText(s, (size.x-w)/2, ((size.y-(height*5))/2)+(height*2))

            s = "Position: %d"%pi.dock_pos
            w, h = dc.GetTextExtent(s)
            dc.DrawText(s, (size.x-w)/2, ((size.y-(height*5))/2)+(height*3))

            s = "Proportion: %d"%pi.dock_proportion
            w, h = dc.GetTextExtent(s)
            dc.DrawText(s, (size.x-w)/2, ((size.y-(height*5))/2)+(height*4))

    def OnEraseBackground(self, event):

        pass

    def OnSize(self, event):

        self.Refresh()


class RideFrame(with_metaclass(classmaker(), wx.Frame, RideEventHandler)):

    def __init__(self, application, controller):
        size = application.settings.get('mainframe size', (1100, 700))
        wx.Frame.__init__(self, parent=None, id = wx.ID_ANY, title='RIDE',
                          pos=application.settings.get('mainframe position', (50, 30)),
                          size=size,
                          style=wx.DEFAULT_FRAME_STYLE | wx.SUNKEN_BORDER)

        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        # self.SetLayoutDirection(wx.Layout_RightToLeft)

        self._mgr = aui.AuiManager()

        # tell AuiManager to manage this frame
        self._mgr.SetManagedWindow(self)

        # set frame icon
        # self.SetIcon(Icon('widgets/robot.ico')) # Maybe is not needed
        # self.SetMinSize(size)
        self.SetMinSize(wx.Size(400, 300))

        self.ensure_on_screen()
        if application.settings.get('mainframe maximized', False):
            self.Maximize()
        self._application = application
        self._controller = controller
        self.favicon = Icon(os.path.join(os.path.dirname(__file__), "..",
                                         "widgets","robot.ico"),
                            wx.BITMAP_TYPE_ICO, 256, 256)
        self.SetIcon(self.favicon)
        self._init_ui()
        self._plugin_manager = PluginManager(self.notebook)
        self._review_dialog = None
        self._view_all_tags_dialog = None
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_MAXIMIZE, self.OnMaximize)
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            self.Bind(wx.EVT_DIRCTRL_FILEACTIVATED, self.OnOpenFile)
            self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnMenuOpenFile)
        self._subscribe_messages()
        #print("DEBUG: Call register_tools, actions: %s" % self.actions.__repr__())
        if PY2:
            wx.CallLater(100, self.actions.register_tools)  # DEBUG
        else:
            wx.CallAfter(self.actions.register_tools)  # DEBUG

    def _subscribe_messages(self):
        for listener, topic in [
            (lambda msg: self.SetStatusText('Saved %s' % msg.path), RideSaved),
            (lambda msg: self.SetStatusText('Saved all files'), RideSaveAll),
            (self._set_label, RideTreeSelection),
            (self._show_validation_error, RideInputValidationError),
            (self._show_modification_prevented_error,
             RideModificationPrevented)
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
        wx.MessageBox("\"%s\" is read only" %
                      message.controller.datafile_controller.filename,
                      "Modification prevented",
                      style=wx.ICON_ERROR)

    def _init_ui(self):
        # self._mgr.AddPane(wx.Panel(self), aui.AuiPaneInfo().CenterPane())
        ##### self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        # self._mgr.AddPane(wx.Panel(self), aui.AuiPaneInfo().CenterPane())
        # set up default notebook style
        self._notebook_style = aui.AUI_NB_DEFAULT_STYLE | \
                               aui.AUI_NB_TAB_EXTERNAL_MOVE | wx.NO_BORDER
        # TODO self._notebook_theme = 0 (allow to select themes for notebooks)
        # self.notebook = NoteBook(self.splitter, self._application,
        #                         self._notebook_style)
        self.notebook = NoteBook(self, self._application,
                                 self._notebook_style)
        self._mgr.AddPane(self.notebook,
                          aui.AuiPaneInfo().Name("notebook_editors").
                          CenterPane().PaneBorder(False))
        ################ Test
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
        ####################
        # self._mgr.AddPane(self.CreateSizeReportCtrl(), aui.AuiPaneInfo().
        #                   Name("test1").Caption(
        #     "Pane Caption").Top().MinimizeButton(True))

        mb = MenuBar(self)
        self.toolbar = ToolBar(self)
        self.toolbar.SetMinSize(wx.Size(100, 60))
        # self.SetToolBar(self.toolbar.GetToolBar())
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
        # self._mgr.AddPane(self.CreateTreeControl(),
        #                  aui.AuiPaneInfo().Name("tree_content").
        #                  CenterPane().Hide().MinimizeButton(True))
        ###### self.tree = Tree(self.splitter, self.actions, self._application.settings)
        self.tree = Tree(self, self.actions,
                         self._application.settings)
        #self.tree.SetMinSize(wx.Size(100, 200))
        self.tree.SetMinSize(wx.Size(120, 200))
        self._mgr.AddPane(self.tree,
                          aui.AuiPaneInfo().Name("tree_content").
                          Caption("Test Suites").LeftDockable(True).
                          CloseButton(False))
        # MaximizeButton(True).MinimizeButton(True))
        self.actions.register_actions(
            ActionInfoCollection(_menudata, self, self.tree))
        ###### File explorer pane
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            self.filemgr = wx.GenericDirCtrl(self, -1, size=(200, 225),
                                             style=wx.DIRCTRL_3D_INTERNAL)
            self.filemgr.SetMinSize(wx.Size(120, 200))
            # wx.CallAfter(self.filemgr.SetPath(self.tree.get_selected_datafile()))
            self._mgr.AddPane(self.filemgr,
                              aui.AuiPaneInfo().Name("file_manager").
                              Caption("Files").LeftDockable(True).
                              CloseButton(True))

        mb.take_menu_bar_into_use()
        #### self.splitter.SetMinimumPaneSize(100)
        #### self.splitter.SplitVertically(self.tree, self.notebook, 300)
        self.CreateStatusBar()
        self.SetIcons(ImageProvider().PROGICONS)
        # tell the manager to "commit" all the changes just made
        self._mgr.Update()

    def testToolbar(self):

        #### More testing
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

    def get_selected_datafile(self):
        return self.tree.get_selected_datafile()

    def get_selected_datafile_controller(self):
        return self.tree.get_selected_datafile_controller()

    def OnClose(self, event):
        if self._allowed_to_exit():
            PUBLISHER.unsubscribe(self._set_label, RideTreeSelection)
            RideClosing().publish()
            # deinitialize the frame manager
            self._mgr.UnInit()
            self.Destroy()
        else:
            wx.CloseEvent.Veto(event)

    def OnSize(self, event):
        if not self.IsMaximized():
            self._application.settings['mainframe maximized'] = False
            self._application.settings['mainframe size'] = self.MyGetSize()
            # DEBUG wxPhoenix .GetSizeTuple()
        event.Skip()

    def OnMove(self, event):
        # When the window is Iconized, a move event is also raised, but we
        # don't want to update the position in the settings file
        if not self.IsIconized() and not self.IsMaximized():
            # DEBUG wxPhoenix writes wx.Point(50, 30) instead of just (50, 30)
            self._application.settings['mainframe position'] = \
                self.MyGetPosition()
            # DEBUG wxPhoenix self.GetPositionTuple()
        event.Skip()

    def OnMaximize(self, event):
        self._application.settings['mainframe maximized'] = True
        event.Skip()

    def OnReleasenotes(self, event):
        pass

    def MyGetSize(self):
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            return self.DoGetSize()
        else:
            return self.GetSizeTuple()

    def MyGetPosition(self):
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            return self.DoGetPosition()
        else:
            return self.GetPositionTuple()

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
        if len(self._controller.data.directory) > 1:
            self.filemgr.SelectPath(self._controller.data.source)
            try:
                self.filemgr.ExpandPath(self._controller.data.source)
            except Exception:
                pass
            self.filemgr.Update()

    def OnOpenFile(self, event):
        if not self.filemgr:
            return
        # EVT_DIRCTRL_FILEACTIVATED
        from os.path import splitext
        robottypes = self._application.settings.get('robot types', ['robot',
                                                                    'resource'
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
        from robotide.editor import customsourceeditor
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

    def OnOpenTestSuite(self, event):
        if not self.check_unsaved_modifications():
            return
        path = RobotFilePathDialog(
            self, self._controller, self._application.settings).execute()
        if path:
            if self.open_suite(path):
                return
            from robotide.editor import customsourceeditor
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
            if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
                path = wx.DirSelector(message="Choose a directory containing "
                                              "Robot files",
                                      default_path=self._controller.default_dir
                                      )
            else:
                path = wx.DirSelector(message="Choose a directory containing "
                                              "Robot files",
                                      defaultPath=self._controller.default_dir)
            if path:
                self.open_suite(path)

    def OnSave(self, event):
        self.save()

    def OnSaveAll(self, event):
        self.save_all()

    def save_all(self):
        self._show_dialog_for_files_without_format()
        self._controller.execute(SaveAll())

    def save(self, controller=None):
        if controller is None:
            controller = self.get_selected_datafile_controller()
        if controller is not None:
            if not controller.has_format():
                self._show_dialog_for_files_without_format(controller)
            else:
                controller.execute(SaveFile())

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
            self._view_all_tags_dialog = ViewAllTagsDialog(self._controller,
                                                           self)
        self._view_all_tags_dialog.show_dialog()

    def OnSearchUnusedKeywords(self, event):
        if self._review_dialog is None:
            self._review_dialog = ReviewDialog(self._controller, self)
        self._review_dialog.show_dialog()

    def OnPreferences(self, event):
        dlg = PreferenceEditor(self, "RIDE - Preferences",
                               self._application.preferences, style='tree')
        # I would prefer that this not be modal, but making it non-
        # modal opens up a can of worms. We don't want to have to deal
        # with settings getting changed out from under us while the
        # dialog is open.
        dlg.ShowModal()
        dlg.Destroy()

    def OnAbout(self, event):
        dlg = AboutDialog()
        dlg.ShowModal()
        dlg.Destroy()

    def OnShortcutkeys(self, event):
        dialog = ShortcutKeysDialog()
        dialog.Show()

    def OnReportaProblem(self, event):
        wx.LaunchDefaultBrowser("https://github.com/robotframework/RIDE/issues"
                                "?utf8=%E2%9C%93&q=is%3Aissue+%22search"
                                "%20your%20problem%22"
                                )

    def OnUserGuide(self, event):
        wx.LaunchDefaultBrowser("http://robotframework.org/robotframework/"
                                "#user-guide")

    def OnWiki(self, event):
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
    def CreateSizeReportCtrl(self, width=80, height=80):

        ctrl = SizeReportCtrl(self, -1, wx.DefaultPosition, wx.Size(width, height), self._mgr)
        return ctrl


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
        self.MyAddTool(self, button.id, label=name,
                       bitmap=action.icon, shortHelp=name,
                       longHelp=action.doc)
        self.Realize()
        self._buttons.append(button)
        return button

    def MyAddTool(self, obj, toolid, label, bitmap,
                  bmpDisabled=wx.NullBitmap,
                  kind=wx.ITEM_NORMAL, shortHelp="", longHelp=""):
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            obj.AddTool(toolid, label, bitmap, bmpDisabled, kind,
                        shortHelp, longHelp)
        else:  # DEBUG Was AddLabelTool for non AUI version
            obj.AddTool(tool_id=toolid, label=label, bitmap=bitmap,
                        disabled_bitmap=bmpDisabled, kind=wx.ITEM_NORMAL,
                        short_help_string=shortHelp,
                        long_help_string=longHelp, client_data=None)

    def _format_button_tooltip(self, action):
        tooltip = action.name.replace('&', '')
        if action.shortcut and action.shortcut.value:
            tooltip = '%s    (%s)' % (tooltip, action.shortcut.value)
        return tooltip

    def remove_toolbar_button(self, button):
        self._buttons.remove(button)
        # self._wx_toolbar.RemoveTool(button.id)
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


class AboutDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self, title='RIDE')
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(HtmlWindow(self, (650, 200), ABOUT_RIDE), 1, flag=wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def OnKey(self, *args):
        pass


class ShortcutKeysDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self, title="Shortcut keys for RIDE")
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
