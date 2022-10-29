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

import locale
import os
import wx
locale.setlocale(locale.LC_ALL, 'C')

from contextlib import contextmanager

from ..namespace import Namespace
from ..controller import Project
from ..spec import librarydatabase
from ..ui import LoadProgressObserver
from ..ui.mainframe import RideFrame
from .. import publish
from .. import context, contrib
from ..context import coreplugins
from ..preferences import Preferences, RideSettings
from ..application.pluginloader import PluginLoader
from ..application.editorprovider import EditorProvider
from ..application.releasenotes import ReleaseNotes
from ..application.updatenotifier import UpdateNotifierController, UpdateDialog
from ..ui.mainframe import ToolBar
from ..ui.treeplugin import TreePlugin
from ..ui.fileexplorerplugin import FileExplorerPlugin
from ..utils import RideFSWatcherHandler, run_python_command
from ..lib.robot.utils.encodingsniffer import get_system_encoding
from ..publish import PUBLISHER
from ..publish.messages import RideSettingsChanged
from ..preferences.settings import _Section
from wx import Colour
from ..widgets.button import ButtonWithHandler


class UnthemableWidgetError(BaseException):
    def __init__(self):
        BaseException.__init__(self, 'HELP! I have no clue how to theme this.')


class RIDE(wx.App):

    def __init__(self, path=None, updatecheck=True):
        self._updatecheck = updatecheck
        self.workspace_path = path
        context.APP = self
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        # DEBUG To test RTL
        # self._initial_locale = wx.Locale(wx.LANGUAGE_ARABIC)
        self._initial_locale = wx.Locale(wx.LANGUAGE_ENGLISH_US)
        # Needed for SetToolTipString to work
        wx.HelpProvider.Set(wx.SimpleHelpProvider())  # TODO adjust to wx versions 
        self.settings = RideSettings()
        librarydatabase.initialize_database()
        self.preferences = Preferences(self.settings)
        self.namespace = Namespace(self.settings)
        self._controller = Project(self.namespace, self.settings)
        self.frame = RideFrame(self, self._controller)
        ##### DEBUG  self.frame.Show()
        self._editor_provider = EditorProvider()
        self._plugin_loader = PluginLoader(self, self._get_plugin_dirs(),
                                           coreplugins.get_core_plugins())
        self._plugin_loader.enable_plugins()
        perspective = self.settings.get('AUI Perspective', None)
        if perspective:
            self.frame._mgr.LoadPerspective(perspective, True)
        try:
            nb_perspective = self.settings.get('AUI NB Perspective', None)
            if nb_perspective:
                self.frame.notebook.LoadPerspective(nb_perspective)
        except Exception as e:
            print(f"RIDE: There was a problem loading panels position."
                  f" Please delete the definition 'AUI NB Perspective' in "
                  f"{os.path.join(context.SETTINGS_DIRECTORY, 'settings.cfg')}")
            if not isinstance(e, IndexError):  # If is with all notebooks disabled, continue
                raise e
        self.treeplugin = TreePlugin(self)
        if self.treeplugin.settings['_enabled']:
            self.treeplugin.register_frame(self.frame)
        self.fileexplorerplugin = FileExplorerPlugin(self, self._controller)
        if self.fileexplorerplugin.settings['_enabled']:
            self.fileexplorerplugin.register_frame(self.frame)
        if not self.treeplugin.opened:
            self.treeplugin.close_tree()
        # else:
        #     wx.CallLater(200, self.treeplugin.populate, self.model)
        if not self.fileexplorerplugin.opened:
            self.fileexplorerplugin.close_tree()
        self.editor = self._get_editor()
        self._load_data()
        self.treeplugin.populate(self.model)
        self.treeplugin.set_editor(self.editor)
        self._find_robot_installation()
        self._publish_system_info()
        self.frame.Show()    ####### DEBUG DANGER ZONE
        self.frame._mgr.Update()
        wx.CallLater(200, ReleaseNotes(self).bring_to_front)
        wx.CallLater(200, self.fileexplorerplugin._update_tree)
        if self._updatecheck:
            wx.CallAfter(UpdateNotifierController(self.settings).notify_update_if_needed, UpdateDialog)
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnAppActivate)
        PUBLISHER.subscribe(self.SetGlobalColour, RideSettingsChanged)
        return True

    def _ApplyThemeToWidget(self, widget,
                            foreColor=wx.BLUE, backColor=wx.LIGHT_GREY, theme={}):
        background = theme['background']
        foreground = theme['foreground']
        secondary_background = theme['secondary background']
        secondary_foreground = theme['secondary foreground']
        background_help = theme['background help']
        foreground_text = theme['foreground text']
        # font_size = theme['font size']
        # font_face = theme['font face']
        if isinstance(widget, wx.lib.agw.aui.auibar.AuiToolBar) or isinstance(widget, ToolBar):
            auiDefaultToolBarArt = wx.lib.agw.aui.AuiDefaultToolBarArt()
            auiDefaultToolBarArt.SetDefaultColours(wx.GREEN)
            widget.SetBackgroundColour(background)
            widget.SetOwnBackgroundColour(background)
            widget.SetForegroundColour(foreground)
            widget.SetOwnForegroundColour(foreground)
            """
            widget.SetBackgroundColour(Colour(200, 222, 40))
            widget.SetOwnBackgroundColour(Colour(200, 222, 40))
            widget.SetForegroundColour(Colour(7, 0, 70))
            widget.SetOwnForegroundColour(Colour(7, 0, 70))
            """
            # or
        elif isinstance(widget, wx.Control):
            if not isinstance(widget, (wx.Button, wx.BitmapButton, ButtonWithHandler)):
                widget.SetForegroundColour(foreground)  #  or foreColor
                widget.SetBackgroundColour(background)  # or backColor
                widget.SetOwnBackgroundColour(background)
                widget.SetOwnForegroundColour(foreground)
            else:
                widget.SetForegroundColour(secondary_foreground)
                widget.SetBackgroundColour(secondary_background)
                widget.SetOwnBackgroundColour(secondary_background)
                widget.SetOwnForegroundColour(secondary_foreground)
        elif isinstance(widget, (wx.TextCtrl, wx.lib.agw.aui.auibook.TabFrame, wx.lib.agw.aui.auibook.AuiTabCtrl)):
            widget.SetForegroundColour(foreground_text)  # or foreColor
            widget.SetBackgroundColour(background_help)  # or backColor
        elif isinstance(widget, (RideFrame, wx.Panel)):
            widget.SetForegroundColour(foreground)  # or foreColor
            widget.SetBackgroundColour(background)  # or foreColor
        elif isinstance(widget, wx.MenuItem):
            widget.SetTextColour(foreground)
            widget.SetBackgroundColour(background)
            # print(f"DEBUG: Application ApplyTheme wx.MenuItem {type(widget)}")
        else:
            widget.SetBackgroundColour(background)
            widget.SetOwnBackgroundColour(background)
            widget.SetForegroundColour(foreground)
            widget.SetOwnForegroundColour(foreground)
            ###### print(f"DEBUG: Application ApplyTheme not specified type(widget) {type(widget)}")
            # pass
            # raise UnthemableWidgetError()

    def _WalkWidgets(self, widget, indent=0, indentLevel=4, theme={}):
        ## print(' ' * indent + widget.__class__.__name__)
        widget.Freeze()
        # print(f"DEBUG Application General : _WalkWidgets background {theme['background']}")
        self._ApplyThemeToWidget(widget=widget, theme=theme)
        for child in widget.GetChildren():
            if (not child.IsTopLevel()):  # or isinstance(child, wx.PopupWindow)):
                indent += indentLevel
                self._WalkWidgets(child, indent, indentLevel, theme)
            indent -= indentLevel
        widget.Thaw()

    def SetGlobalColour(self, message):
        if message.keys[0] != "General":
            return
        # print(f"DEBUG Application General : Enter SetGlobalColour message= {message.keys[0]}")
        app = wx.App.Get()
        _root = app.GetTopWindow()
        theme = self.settings.get('General', None)
        font_size = theme['font size']
        font_face = theme['font face']
        font = _root.GetFont()
        font.SetFaceName(font_face)
        font.SetPointSize(font_size)
        _root.SetFont(font)
        self._WalkWidgets(_root, theme=theme)
        # print(f"DEBUG Application General : SetGlobalColour AppliedWidgets check Filexplorer and Tree")
        if theme['apply to panels'] and self.fileexplorerplugin.settings['_enabled']:
            self.fileexplorerplugin.settings['background'] = theme['background']
            self.fileexplorerplugin.settings['foreground'] = theme['foreground']
            self.fileexplorerplugin.settings['foreground text'] = theme['foreground text']
            self.fileexplorerplugin.settings['background help'] = theme['background help']
            self.fileexplorerplugin.settings['font size'] = theme['font size']
            self.fileexplorerplugin.settings['font face'] = theme['font face']
            if self.fileexplorerplugin.settings['opened']:
                self.fileexplorerplugin.OnShowFileExplorer(None)
        if theme['apply to panels'] and self.treeplugin.settings['_enabled']:
            self.treeplugin.settings['background'] = theme['background']
            self.treeplugin.settings['foreground'] = theme['foreground']
            self.treeplugin.settings['foreground text'] = theme['foreground text']
            self.treeplugin.settings['background help'] = theme['background help']
            self.treeplugin.settings['font size'] = theme['font size']
            self.treeplugin.settings['font face'] = theme['font face']
            if self.treeplugin.settings['opened']:
                self.treeplugin.OnShowTree(None)
        """
        all_windows = list()
        general = self.settings.get('General', None)
        # print(f"DEBUG: Application General {general['background']} Type message {type(message)}")
        # print(f"DEBUG: Application General message keys {message.keys} old {message.old} new {message.new}")
        background = general['background']
        foreground = general['foreground']
        background_help = general['background help']
        foreground_text = general['foreground text']
        font_size = general['font size']
        font_face = general['font face']
        font = _root.GetFont()
        font.SetFaceName(font_face)
        font.SetPointSize(font_size)
        _root.SetFont(font)

        def _iterate_all_windows(root):
            if hasattr(root, 'GetChildren'):
                children = root.GetChildren()
                if children:
                    for c in children:
                        _iterate_all_windows(c)
            all_windows.append(root)

        _iterate_all_windows(_root)

        for w in all_windows:
            if hasattr(w, 'SetHTMLBackgroundColour'):
                w.SetHTMLBackgroundColour(wx.Colour(background_help))
                w.SetForegroundColour(wx.Colour(foreground_text))  # 7, 0, 70))
            elif hasattr(w, 'SetBackgroundColour'):
                w.SetBackgroundColour(wx.Colour(background))  # 44, 134, 179))

                # if hasattr(w, 'SetOwnBackgroundColour'):
                #     w.SetOwnBackgroundColour(wx.Colour(background))  # 44, 134, 179))

                if hasattr(w, 'SetForegroundColour'):
                    w.SetForegroundColour(wx.Colour(foreground))  # 7, 0, 70))

                # if hasattr(w, 'SetOwnForegroundColour'):
                #    w.SetOwnForegroundColour(wx.Colour(foreground))  # 7, 0, 70))

            if hasattr(w, 'SetFont'):
                w.SetFont(font)
            """

    def _publish_system_info(self):
        publish.RideLogMessage(context.SYSTEM_INFO).publish()

    @property
    def model(self):
        return self._controller

    def _get_plugin_dirs(self):
        return [self.settings.get_path('plugins'),
                os.path.join(self.settings['install root'], 'site-plugins'),
                contrib.CONTRIB_PATH]

    def _get_editor(self):
        from ..editor import EditorPlugin
        from ..editor.texteditor import TextEditorPlugin
        for pl in self._plugin_loader.plugins:
            maybe_editor = pl._plugin
            if (isinstance(maybe_editor, EditorPlugin) or
                isinstance(maybe_editor, TextEditorPlugin)) and \
                maybe_editor.__getattr__("_enabled"):
                return maybe_editor

    def _load_data(self):
        self.workspace_path = self.workspace_path or self._get_latest_path()
        if self.workspace_path:
            self._controller.update_default_dir(self.workspace_path)
            observer = LoadProgressObserver(self.frame)
            self._controller.load_data(self.workspace_path, observer)

    def _find_robot_installation(self):
        output = run_python_command(
            ['import robot; print(robot.__file__ + \", \" + robot.__version__)'])
        robot_found = b"ModuleNotFoundError" not in output and output
        if robot_found:
            system_encoding = get_system_encoding()
            rf_file, rf_version = output.strip().split(b", ")
            publish.RideLogMessage("Found Robot Framework version %s from %s." % (
                str(rf_version, system_encoding), str(os.path.dirname(rf_file), system_encoding))).publish()
            return rf_version
        else:
            publish.RideLogMessage(
                publish.get_html_message('no_robot'), notify_user=True
            ).publish()

    def _get_latest_path(self):
        recent = self._get_recentfiles_plugin()
        if not recent or not recent.recent_files:
            return None
        return recent.recent_files[0]

    def _get_recentfiles_plugin(self):
        from ..recentfiles import RecentFilesPlugin
        for pl in self.get_plugins():
            if isinstance(pl._plugin, RecentFilesPlugin):
                return pl._plugin

    def get_plugins(self):
        return self._plugin_loader.plugins

    def register_preference_panel(self, panel_class):
        """Add the given panel class to the list of known preference panels"""
        self.preferences.add(panel_class)

    def unregister_preference_panel(self, panel_class):
        """Remove the given panel class from the known preference panels"""
        self.preferences.remove(panel_class)

    def register_editor(self, object_class, editor_class, activate):
        self._editor_provider.register_editor(object_class, editor_class,
                                              activate)

    def unregister_editor(self, object_class, editor_class):
        self._editor_provider.unregister_editor(object_class, editor_class)

    def activate_editor(self, object_class, editor_class):
        self._editor_provider.set_active_editor(object_class, editor_class)

    def get_editors(self, object_class):
        return self._editor_provider.get_editors(object_class)

    def get_editor(self, object_class):
        return self._editor_provider.get_editor(object_class)

    @contextmanager
    def active_event_loop(self):
        # With wxPython 2.9.1, ProgressBar.Pulse breaks if there's no active
        # event loop.
        # See http://code.google.com/p/robotframework-ride/issues/detail?id=798
        loop = wx.EventLoop()
        wx.EventLoop.SetActive(loop)
        yield
        del loop

    def OnEventLoopEnter(self, loop):
        if loop and wx.EventLoopBase.IsMain(loop):
            RideFSWatcherHandler.create_fs_watcher(self.workspace_path)

    def OnAppActivate(self, event):
        if self.workspace_path is not None and RideFSWatcherHandler.is_watcher_created():
            if event.GetActive():
                # print(f"DEBUG: OnAppActivate event.GetActive  is_project_changed_from_disk = {self._controller.is_project_changed_from_disk()}")
                #print(f"DEBUG: OnAppActivate event.GetActive  is_workspace_dirty = {RideFSWatcherHandler.is_workspace_dirty()}")
                #DEBUG if self._controller.is_project_changed_from_disk() or \
                if RideFSWatcherHandler.is_workspace_dirty():
                    self.frame.show_confirm_reload_dlg(event)
                RideFSWatcherHandler.stop_listening()
            else:
                RideFSWatcherHandler.start_listening(self.workspace_path)
        event.Skip()
