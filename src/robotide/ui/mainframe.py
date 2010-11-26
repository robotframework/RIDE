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

from robotide.controller import NewDatafile
from robotide.action import ActionInfoCollection, Action
from robotide.publish import RideSaveAll, RideClosing, RideSaved, PUBLISHER
from robotide.utils import RideEventHandler, RideHtmlWindow
from robotide.context import SETTINGS, ABOUT_RIDE
from robotide.widgets import Dialog

from actiontriggers import MenuBar, ToolBar, ShortcutRegistry
from filedialogs import NewProjectDialog, NewResourceDialog, ChangeFormatDialog
from pluginmanager import PluginManager
from tree import Tree
from notebook import NoteBook
from progress import LoadProgressObserver
from robotide.controller.commands import SaveFile, SaveAll


_menudata = """
[File]
!&Open | Open file containing tests | Ctrlcmd-O | ART_FILE_OPEN
!Open &Directory | Open directory containing datafiles | Shift-Ctrlcmd-O | ART_FOLDER_OPEN
!Open &Resource | Open a resource file | Ctrlcmd-R
---
!&New Project | Create a new top level suite | Ctrlcmd-N
!N&ew Resource | Create New Resource File | Ctrlcmd-Shift-N
---
&Save | Save selected datafile | Ctrlcmd-S | ART_FILE_SAVE
!Save &All | Save all changes | Ctrlcmd-Shift-S | ART_FILE_SAVE_AS
---
!E&xit | Exit RIDE | Ctrlcmd-Q

[Tools]
!Manage Plugins

[Help]
!About | Information about RIDE
"""


class RideFrame(wx.Frame, RideEventHandler):
    _default_dir = property(lambda self: os.path.abspath(SETTINGS['default directory']),
                            lambda self, path: SETTINGS.set('default directory', path))


    def __init__(self, application, controller):
        wx.Frame.__init__(self, parent=None, title='RIDE',
                          pos=SETTINGS['mainframe position'],
                          size=SETTINGS['mainframe size'])
        self._application = application
        self._controller = controller
        self._init_ui()
        self._plugin_manager = PluginManager(self.notebook)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self._subscribe_messages()
        self.ensure_on_screen()
        self.Show()

    def _subscribe_messages(self):
        for listener, topic in [(lambda msg: self.SetStatusText('Saved %s' % msg.path), RideSaved),
                                (lambda msg: self.SetStatusText('Saved all files'), RideSaveAll)]:
            PUBLISHER.subscribe(listener, topic)

    def _init_ui(self):
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        splitter.SetMinimumPaneSize(200)
        self.notebook = NoteBook(splitter, self._application)
        self.actions = ActionRegisterer(MenuBar(self), ToolBar(self),
                                        ShortcutRegistry(self))
        self.tree = Tree(splitter, self.actions)
        self.actions.register_actions(ActionInfoCollection(_menudata, self,
                                                           self.tree))
        splitter.SplitVertically(self.tree, self.notebook, 300)
        self.CreateStatusBar()

    def get_selected_datafile(self):
        return self.tree.get_selected_datafile()

    def get_selected_datafile_controller(self):
        return self.tree.get_selected_datafile_controller()

    def OnClose(self, event):
        SETTINGS['mainframe size'] = self.GetSizeTuple()
        SETTINGS['mainframe position'] = self.GetPositionTuple()
        if self._allowed_to_exit():
            RideClosing().publish()
            self.Destroy()
        else:
            wx.CloseEvent.Veto(event)

    def _allowed_to_exit(self):
        if self._controller.is_dirty():
            ret = wx.MessageBox('There are unsaved modifications.\n'
                                'Do you want to save your changes before exiting?',
                                'Warning', wx.ICON_WARNING|wx.CANCEL|wx.YES_NO)
            if ret == wx.CANCEL:
                return False
            if ret == wx.YES:
                self.save()
        return True

    def OnNewProject(self, event):
        if not self._check_unsaved_modifications():
            return
        dlg = NewProjectDialog(self._default_dir)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.get_path()
            self._default_dir = os.path.dirname(path)
            data = NewDatafile(path, dlg.is_dir_type())
            self._controller.new_datafile(data)
            self.tree.populate(self._controller)
        dlg.Destroy()

    def OnNewResource(self, event):
        dlg = NewResourceDialog(self._default_dir)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.get_path()
            self._default_dir = os.path.dirname(path)
            self._controller.new_resource(path)
        dlg.Destroy()

    def OnOpen(self, event):
        self._check_unsaved_modifications()
        path = self._get_path()
        if path:
            self.open_suite(path)

    def _check_unsaved_modifications(self):
        if self._controller.is_dirty():
            ret = wx.MessageBox('There are unsaved modifications.\n'
                                'Do you want to proceed without saving?',
                                'Warning', wx.ICON_WARNING|wx.YES_NO)
            return ret == wx.YES
        return True

    def OnOpenResource(self, event):
        path = self._get_path()
        if path:
            self._controller.load_resource(path, LoadProgressObserver(self))

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
        self._controller.load_datafile(path, LoadProgressObserver(self))
        self.tree.populate(self._controller)

    def refresh_datafile(self, item, event):
        self.tree.refresh_datafile(item, event)

    def OnOpenDirectory(self, event):
        if self._check_unsaved_modifications():
            path = wx.DirSelector(message='Choose a directory containing Robot files',
                                  defaultPath=self._default_dir)
            if path:
                self._default_dir = path
                self.open_suite(path)

    def OnSave(self, event):
        self.save()

    def OnSaveAll(self, event):
        self._show_dialog_for_files_without_format()
        self._controller.execute(SaveAll())

    def save(self, controller=None):
        if controller is None : 
            controller = self.get_selected_datafile_controller()
        self._show_dialog_for_files_without_format(controller)
        controller.execute(SaveFile())

    def _show_dialog_for_files_without_format(self, controller=None):
        files_without_format = self._controller.get_files_without_format(controller)
        for f in files_without_format:
            self._show_format_dialog_for(f)

    def _show_format_dialog_for(self, file_controller_without_format):
        help = 'Please provide format of initialization file for directory suite\n"%s".' %\
                file_controller_without_format.directory
        dlg = ChangeFormatDialog('TXT', help_text=help)
        if dlg.ShowModal() == wx.ID_OK:
            file_controller_without_format.set_format(dlg.get_format())
        dlg.Destroy()

    def OnExit(self, event):
        self.Close()

    def OnManagePlugins(self, event):
        self._plugin_manager.show(self._application.get_plugins())

    def OnAbout(self, event):
        dlg = AboutDialog()
        dlg.ShowModal()
        dlg.Destroy()

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

    def register_action(self, action_info):
        action = Action(action_info)
        self._shortcut_registry.register(action)
        self._menubar.register(action)
        self._toolbar.register(action)
        return action

    def register_actions(self, actions):
        for action in actions:
            self.register_action(action)


class AboutDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self, title='RIDE')
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(RideHtmlWindow(self, (450, 200), ABOUT_RIDE))
        self.SetSizerAndFit(sizer)
