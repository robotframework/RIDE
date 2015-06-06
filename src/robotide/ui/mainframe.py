#  Copyright 2008-2015 Nokia Solutions and Networks
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

import wx

from robotide.action import ActionInfoCollection, ActionFactory, SeparatorInfo
from robotide.context import ABOUT_RIDE, SHORTCUT_KEYS
from robotide.controller.commands import SaveFile, SaveAll
from robotide.publish import RideSaveAll, RideClosing, RideSaved, PUBLISHER,\
    RideInputValidationError, RideTreeSelection, RideModificationPrevented
from robotide.ui.tagdialogs import ViewAllTagsDialog
from robotide.utils import RideEventHandler
from robotide.widgets import Dialog, ImageProvider, HtmlWindow
from robotide.preferences import PreferenceEditor

from .actiontriggers import MenuBar, ToolBar, ShortcutRegistry
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
!Open &Directory | Open directory containing datafiles | Shift-Ctrlcmd-O | ART_FOLDER_OPEN
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
!User Guide | RIDE User Guide
!Report a Problem | Open browser to the RIDE issue tracker
!Release notes | Shows release notes
!About | Information about RIDE
"""


class RideFrame(wx.Frame, RideEventHandler):

    def __init__(self, application, controller):
        wx.Frame.__init__(self, parent=None, title='RIDE',
                          pos=application.settings['mainframe position'],
                          size=application.settings['mainframe size'])
        self.ensure_on_screen()
        if application.settings['mainframe maximized']:
            self.Maximize()
        self._application = application
        self._controller = controller
        self._init_ui()
        self._plugin_manager = PluginManager(self.notebook)
        self._review_dialog = None
        self._view_all_tags_dialog = None
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_MAXIMIZE, self.OnMaximize)
        self._subscribe_messages()
        self.Show()
        wx.CallLater(100, self.actions.register_tools)

    def _subscribe_messages(self):
        for listener, topic in [
            (lambda msg: self.SetStatusText('Saved %s' % msg.path), RideSaved),
            (lambda msg: self.SetStatusText('Saved all files'), RideSaveAll),
            (self._set_label, RideTreeSelection),
            (self._show_validation_error, RideInputValidationError),
            (self._show_modification_prevented_error, RideModificationPrevented)
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
        wx.MessageBox('"%s" is read only' % message.controller.datafile_controller.filename,
                      'Modification prevented',
                      style=wx.ICON_ERROR)

    def _init_ui(self):
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.notebook = NoteBook(splitter, self._application)
        mb = MenuBar(self)
        self.toolbar = ToolBar(self)
        self.actions = ActionRegisterer(mb, self.toolbar,
                                        ShortcutRegistry(self))
        self.tree = Tree(splitter, self.actions, self._application.settings)
        self.actions.register_actions(
            ActionInfoCollection(_menudata, self, self.tree))
        mb.take_menu_bar_into_use()
        splitter.SetMinimumPaneSize(100)
        splitter.SplitVertically(self.tree, self.notebook, 300)
        self.CreateStatusBar()
        self.SetIcons(ImageProvider().PROGICONS)

    def get_selected_datafile(self):
        return self.tree.get_selected_datafile()

    def get_selected_datafile_controller(self):
        return self.tree.get_selected_datafile_controller()

    def OnClose(self, event):
        if self._allowed_to_exit():
            PUBLISHER.unsubscribe(self._set_label, RideTreeSelection)
            RideClosing().publish()
            self.Destroy()
        else:
            wx.CloseEvent.Veto(event)

    def OnSize(self, event):
        if not self.IsMaximized():
            self._application.settings['mainframe maximized'] = False
            self._application.settings['mainframe size'] = self.GetSizeTuple()
        event.Skip()

    def OnMove(self, event):
        # When the window is Iconized, a move event is also raised, but we
        # don't want to update the position in the settings file
        if not self.IsIconized() and not self.IsMaximized():
            self._application.settings['mainframe position'] = self.GetPositionTuple()
        event.Skip()

    def OnMaximize(self, event):
        self._application.settings['mainframe maximized'] = True
        event.Skip()

    def OnReleasenotes(self, event):
        pass

    def _allowed_to_exit(self):
        if self.has_unsaved_changes():
            ret = wx.MessageBox('There are unsaved modifications.\n'
                                'Do you want to save your changes before exiting?',
                                'Warning', wx.ICON_WARNING|wx.CANCEL|wx.YES_NO)
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

    def OnOpenTestSuite(self, event):
        if not self.check_unsaved_modifications():
            return
        path = self._get_path()
        if path:
            self.open_suite(path)

    def check_unsaved_modifications(self):
        if self.has_unsaved_changes():
            ret = wx.MessageBox('There are unsaved modifications.\n'
                                'Do you want to proceed without saving?',
                                'Warning', wx.ICON_WARNING|wx.YES_NO)
            return ret == wx.YES
        return True

    def _get_path(self):
        wildcard = 'Robot data (*robot)|*.robot|Robot data (*txt)|*.txt|All files|*.*'
        dlg = wx.FileDialog(
            self, message='Open', wildcard=wildcard,
            defaultDir=self._controller.default_dir, style=wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._controller.update_default_dir(path)
        else:
            path = None
        dlg.Destroy()
        return path

    def open_suite(self, path):
        self._controller.update_default_dir(path)
        self._controller.load_datafile(path, LoadProgressObserver(self))
        self._populate_tree()

    def refresh_datafile(self, item, event):
        self.tree.refresh_datafile(item, event)

    def OnOpenDirectory(self, event):
        if self.check_unsaved_modifications():
            path = wx.DirSelector(message='Choose a directory containing Robot files',
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
        if controller is None :
            controller = self.get_selected_datafile_controller()
        if controller is not None:
            if not controller.has_format():
                self._show_dialog_for_files_without_format(controller)
            else:
                controller.execute(SaveFile())

    def _show_dialog_for_files_without_format(self, controller=None):
        files_without_format = self._controller.get_files_without_format(controller)
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
        wx.LaunchDefaultBrowser('http://github.com/robotframework/RIDE/issues')

    def OnUserGuide(self, event):
        wx.LaunchDefaultBrowser('http://robotframework.org/robotframework/#user-guide')

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


class ActionRegisterer(object):

    def __init__(self, menubar, toolbar, shortcut_registry):
        self._menubar = menubar
        self._toolbar = toolbar
        self._shortcut_registry = shortcut_registry
        self._tools_items = {}

    def register_action(self, action_info):
        menubar_can_be_registered = True
        action = ActionFactory(action_info)
        self._shortcut_registry.register(action)
        if hasattr(action_info,"menu_name"):
            if action_info.menu_name == "Tools":
                self._tools_items[action_info.position] = action
                menubar_can_be_registered = False
        if menubar_can_be_registered:
            self._menubar.register(action)
        self._toolbar.register(action)
        return action

    def register_tools(self):
        separator_action = ActionFactory(SeparatorInfo("Tools"))
        add_separator_after = ["stop test run","search unused keywords","preview","view ride log"]
        for key in sorted(self._tools_items.iterkeys()):
            self._menubar.register(self._tools_items[key])
            if self._tools_items[key].name.lower() in add_separator_after:
                self._menubar.register(separator_action)

    def register_actions(self, actions):
        for action in actions:
            self.register_action(action)

    def register_shortcut(self, action_info):
        action = ActionFactory(action_info)
        self._shortcut_registry.register(action)
        return action


class AboutDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self, title='RIDE')
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(HtmlWindow(self, (450, 200), ABOUT_RIDE), 1, flag=wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def OnKey(self, *args):
        pass


class ShortcutKeysDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self, title='Shortcut keys for RIDE')
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(HtmlWindow(self, (350, 400), self._get_platform_specific_shortcut_keys()), 1, flag=wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def OnKey(self, *args):
        pass

    def _get_platform_specific_shortcut_keys(self):
        return localize_shortcuts(SHORTCUT_KEYS)
