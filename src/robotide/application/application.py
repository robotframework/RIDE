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
import subprocess
import sys

import wx

from contextlib import contextmanager
from pathlib import Path

from ..namespace import Namespace
from ..context import SETTINGS_DIRECTORY
from ..controller import Project
from ..spec import librarydatabase
from ..ui import LoadProgressObserver
from ..ui.mainframe import RideFrame
from .. import publish
from .. import context, contrib
from ..preferences import Preferences, RideSettings
from ..application.pluginloader import PluginLoader
from ..application.editorprovider import EditorProvider
from ..application.releasenotes import ReleaseNotes
from ..application.updatenotifier import UpdateNotifierController, UpdateDialog
from ..ui.mainframe import ToolBar
from ..ui.fileexplorerplugin import FileExplorerPlugin
from ..utils import RideFSWatcherHandler, run_python_command
from ..lib.robot.utils.encodingsniffer import get_system_encoding
from ..publish import PUBLISHER
from ..publish.messages import RideSettingsChanged
from ..widgets.button import ButtonWithHandler
from wx.lib.agw.aui import AuiDefaultToolBarArt
from wx.lib.agw.aui.auibar import AuiToolBar
from wx.lib.agw.aui.auibook import AuiTabCtrl, TabFrame
try:
    from robot.conf import languages
except ImportError:
    languages = None

# add translation macro to builtin similar to what gettext does
# generated pot with: /usr/bin/python /usr/bin/pygettext.py -a -d RIDE -o RIDE.pot -p ./localization ../robotide
_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

BACKGROUND_HELP = 'background help'
FOREGROUND_TEXT = 'foreground text'
FONT_SIZE = 'font size'
FONT_FACE = 'font face'
SPC = "  "
FIVE_SPC = SPC*5


def restart_ride(args:list):
    script = os.path.abspath(os.path.dirname(__file__) + '/../__init__.py')  # This is probably a different signature
    python = sys.executable
    arguments = [python, script]
    for a in args:
        if a:
            arguments.append(a)
    # print(f"DEBUG: Application.py restart_RIDE arguments={arguments}\n")
    """DEBUG
    try:
        process = psutil.Process(os.getpid())
        # process.terminate()
        for handler in process.open_files() + process.connections():
            os.close(handler.fd)
    except Exception as e:
        pass
    """
    str_args = " ".join(arguments)
    subprocess.Popen(str_args, shell=True)


class UnthemableWidgetError(Exception):
    def __init__(self):
        Exception.__init__(self, 'HELP! I have no clue how to theme this.')


class RIDE(wx.App):
    _controller = None
    _editor_provider = None
    _locale = None
    _plugin_loader = None
    editor = None
    fileexplorerplugin = None
    fontinfo = None
    frame = None
    namespace = None
    preferences = None
    robot_version = None
    settings = None
    treeplugin = None

    def __init__(self, path=None, updatecheck=True, settingspath=None):
        self._updatecheck = updatecheck
        self.workspace_path = path
        self.changed_workspace = False
        self.preferences = None
        self.settings_path = settingspath
        context.APP = self
        # print(f"DEBUG: Application.py RIDE __init__ path={self.workspace_path}\n")
        wx.App.__init__(self, redirect=False)

    def OnInit(self):  # Overrides wx method
        # DEBUG To test RTL
        # self._initial_locale = wx.Locale(wx.LANGUAGE_ARABIC)
        self._locale = wx.Locale(wx.LANGUAGE_ENGLISH_US)  # LANGUAGE_PORTUGUESE
        # Needed for SetToolTipString to work
        wx.HelpProvider.Set(wx.SimpleHelpProvider())  # DEBUG: adjust to wx versions
        # Use Project settings if available
        from ..recentfiles import RecentFilesPlugin
        self.settings = RideSettings(self.settings_path)  # We need this to know the available plugins
        self._plugin_loader = PluginLoader(self, self._get_plugin_dirs(), [RecentFilesPlugin],
                                           silent=True)
            # print(f"DEBUG: Application.py RIDE OnInit path={self.workspace_path}\n")
        self.workspace_path = self.workspace_path or self._get_latest_path()
        # print(f"DEBUG: Application.py RIDE OnInit AFTER _get_latest_path() path={self.workspace_path}")
        if not self.settings_path:
            self.settings_path = self.initialize_project_settings(self.workspace_path)
        self.settings = RideSettings(self.settings_path)

        class Message:
            keys = ['General']

        self.change_locale(Message)  # This was done here to have menus translated, but not working
        # print(f"DEBUG: application.py RIDE OnInit after changing localization {self._locale.GetCanonicalName()=}")
        # Importing libraries after setting language
        from ..context import coreplugins, SETTINGS_DIRECTORY
        from ..ui.treeplugin import TreePlugin
        librarydatabase.initialize_database()
        self.reload_preferences(Message)
        self.namespace = Namespace(self.settings)
        self._controller = Project(self.namespace, self.settings)
        # print(f"DEBUG: application.py RIDE OnInit after defining controller= {self._controller}")
        # Try to get FontInfo as soon as possible
        font_size = self.settings['General'].get('font size', 12)
        font_face = self.settings['General'].get('font face', 'Helvetica')
        self.fontinfo = wx.FontInfo(font_size).FaceName(font_face).Bold(False)
        self.fileexplorerplugin = FileExplorerPlugin(self, self._controller)
        self.frame = RideFrame(self, self._controller)
        # DEBUG  self.frame.Show()
        self._editor_provider = EditorProvider()
        self._plugin_loader = PluginLoader(self, self._get_plugin_dirs(), coreplugins.get_core_plugins())
        self._plugin_loader.enable_plugins()
        perspective = self.settings.get('AUI Perspective', None)
        if perspective:
            self.frame.aui_mgr.LoadPerspective(perspective, True)
        try:
            nb_perspective = self.settings.get('AUI NB Perspective', None)
            if nb_perspective:
                self.frame.notebook.LoadPerspective(nb_perspective)
        except Exception as e:
            print(f"RIDE: There was a problem loading panels position."
                  f" Please delete the definition 'AUI NB Perspective' in "
                  f"{self.settings_path or os.path.join(SETTINGS_DIRECTORY, 'settings.cfg')}")
            if not isinstance(e, IndexError):  # If is with all notebooks disabled, continue
                raise e

        self.treeplugin = TreePlugin(self)
        if self.treeplugin.settings['_enabled']:
            self.treeplugin.register_frame(self.frame)
        if not self.treeplugin.opened:
            self.treeplugin.close_tree()
        if self.fileexplorerplugin.settings['_enabled']:
            self.fileexplorerplugin.register_frame(self.frame)
        if not self.fileexplorerplugin.opened:
            self.fileexplorerplugin.close_tree()
        self.editor = self._get_editor()
        self.robot_version = self._find_robot_installation()
        self._load_data()
        self.treeplugin.populate(self.model)
        self.treeplugin.set_editor(self.editor)
        self._publish_system_info()
        self.frame.Show()    # ###### DEBUG DANGER ZONE
        self.SetTopWindow(self.frame)
        self.frame.aui_mgr.Update()
        if self._updatecheck:
            wx.CallAfter(UpdateNotifierController(self.settings, self.frame.notebook).notify_update_if_needed,
                         UpdateDialog)
        self.Bind(wx.EVT_ACTIVATE_APP, self.on_app_activate)
        PUBLISHER.subscribe(self.SetGlobalColour, RideSettingsChanged)
        PUBLISHER.subscribe(self.update_excludes, RideSettingsChanged)
        RideSettingsChanged(keys=('Excludes', 'init'), old=None, new=None).publish()
        PUBLISHER.subscribe(self.change_locale, RideSettingsChanged)
        RideSettingsChanged(keys=('General', 'ui language'), old=None, new=None).publish()
        PUBLISHER.subscribe(self.reload_preferences, RideSettingsChanged)
        wx.CallLater(600, ReleaseNotes(self).bring_to_front)
        return True

    def OnExit(self):
        PUBLISHER.unsubscribe_all()
        self.frame.on_exit(None)
        self.Destroy()
        wx.Exit()
        return True

    def reload_preferences(self, message):
        if message.keys[0] != "General":
            return
        NORMAL_SETTINGS = _('Global Settings')
        NORMAL_SETTINGS_DETECTED = _('Global Settings Detected')
        PROJECT_SETTINGS = _('Project Settings')
        PROJECT_SETTINGS_DETECTED = _('Project Settings Detected')
        if self.preferences:
           del self.preferences
        if self.settings_path:
            self.settings = RideSettings(self.settings_path)
        self.preferences = Preferences(self.settings, self.settings_path)
        try:
            if message.keys[1] in ["reload", "restore"]:
                # reload plugins (was the original idea)
                if message.keys[1] == "reload":
                    project_or_normal = PROJECT_SETTINGS
                    project_or_normal_detected = PROJECT_SETTINGS_DETECTED
                else:
                    project_or_normal = NORMAL_SETTINGS
                    project_or_normal_detected = NORMAL_SETTINGS_DETECTED

                from .updatenotifier import _askyesno
                if not _askyesno(_("Restart RIDE?"),
                                 f"{FIVE_SPC}{FIVE_SPC}{FIVE_SPC}{FIVE_SPC}{FIVE_SPC}"
                                 f"{project_or_normal_detected}{FIVE_SPC}\n\n"
                                 f"{FIVE_SPC}{_('RIDE must be restarted to fully use these ')}{project_or_normal}"
                                 f"{FIVE_SPC}\n\n\n{FIVE_SPC}{FIVE_SPC}{FIVE_SPC}{FIVE_SPC}{FIVE_SPC}"
                                 f"{_('Click OK to Restart RIDE!')}{FIVE_SPC}{FIVE_SPC}{FIVE_SPC}{FIVE_SPC}{FIVE_SPC}"
                                 f"\n\n", wx.GetActiveWindow(), no_default=False):
                    return False
                args = [f"{'--noupdatecheck' if not self._updatecheck else ''}",
                        f"--settingspath {message.keys[2]}", f"{message.keys[3]}"]
                restart_ride(args)
                wx.CallLater(1000, self.OnExit)
                # The next block was an attempt to reload plugins, in particular Test Runner to
                # load the Arguments for the project. This did not work because the plugins are
                # loaded at creation of ui/mainframe. For now, we open a new instance of RIDE
                # with the test suite/project argument.
                """
                # print("DEBUG: application.py RELOAD PLUGINS HERE!")
                from time import sleep
                for plu in self._plugin_loader.plugins:
                    # print(f"DEBUG: Application RIDE plugin: {plu} {plu.name}\n"
                    #       f"Plugin object={plu.conn_plugin}")
                    if plu.name == 'Editor':
                        plu.conn_plugin._show_editor()
                    if plu.name == 'Test Runner':
                        plu.disable()
                        sleep(2)
                        plu.enable()
                        # plu.conn_plugin._show_notebook_tab()
                """
        except IndexError:
            pass

    @staticmethod
    def _ApplyThemeToWidget(widget, fore_color=wx.BLUE, back_color=wx.LIGHT_GREY, theme: (None, dict) = None):
        if theme is None:
            theme = {'background': back_color, 'foreground': fore_color, 'secondary background': back_color,
                     'secondary foreground': fore_color}
        background = theme['background']
        foreground = theme['foreground']
        secondary_background = theme['secondary background']
        secondary_foreground = theme['secondary foreground']
        background_help = theme[BACKGROUND_HELP]
        foreground_text = theme[FOREGROUND_TEXT]
        if isinstance(widget, AuiToolBar) or isinstance(widget, ToolBar):
            aui_default_tool_bar_art = AuiDefaultToolBarArt()
            aui_default_tool_bar_art.SetDefaultColours(wx.GREEN)
            widget.SetBackgroundColour(background)
            widget.SetForegroundColour(foreground)
        elif isinstance(widget, wx.Control):
            if not isinstance(widget, (wx.Button, wx.BitmapButton, ButtonWithHandler)):
                widget.SetForegroundColour(foreground)
                widget.SetBackgroundColour(background)
            else:
                widget.SetForegroundColour(secondary_foreground)
                widget.SetBackgroundColour(secondary_background)
        elif isinstance(widget, (wx.TextCtrl, TabFrame, AuiTabCtrl)):
            widget.SetForegroundColour(foreground_text)  # or fore_color
            widget.SetBackgroundColour(background_help)  # or back_color
        elif isinstance(widget, (RideFrame, wx.Panel)):
            widget.SetForegroundColour(foreground)  # or fore_color
            widget.SetBackgroundColour(background)  # or fore_color
        elif isinstance(widget, wx.MenuItem):
            widget.SetTextColour(foreground)
            widget.SetBackgroundColour(background)
        else:
            widget.SetBackgroundColour(background)
            widget.SetForegroundColour(foreground)

    def _WalkWidgets(self, widget, indent=0, indent_level=4, theme=None):
        if theme is None:
            theme = {}
        widget.Freeze()
        self._ApplyThemeToWidget(widget=widget, theme=theme)
        for child in widget.GetChildren():
            if not child.IsTopLevel():  # or isinstance(child, wx.PopupWindow)):
                indent += indent_level
                self._WalkWidgets(child, indent, indent_level, theme)
            indent -= indent_level
        widget.Thaw()

    def SetGlobalColour(self, message):
        if message.keys[0] != "General":
            return
        app = wx.App.Get()
        _root = app.GetTopWindow()
        theme = self.settings.get_without_default('General')
        font_size = theme[FONT_SIZE]
        font_face = theme[FONT_FACE]
        font = _root.GetFont()
        font.SetFaceName(font_face)
        font.SetPointSize(font_size)
        _root.SetFont(font)
        self._WalkWidgets(_root, theme=theme)
        if self.fileexplorerplugin.settings['_enabled']:
            if theme['apply to panels'] and not self.fileexplorerplugin.settings['own colors']:
                self.fileexplorerplugin.settings['background'] = theme['background']
                self.fileexplorerplugin.settings['foreground'] = theme['foreground']
                self.fileexplorerplugin.settings[FOREGROUND_TEXT] = theme[FOREGROUND_TEXT]
                self.fileexplorerplugin.settings[BACKGROUND_HELP] = theme[BACKGROUND_HELP]
                self.fileexplorerplugin.settings[FONT_SIZE] = theme[FONT_SIZE]
                self.fileexplorerplugin.settings[FONT_FACE] = theme[FONT_FACE]
                if self.fileexplorerplugin.settings['opened']:
                    self.fileexplorerplugin.show_file_explorer()
            else:
                self.fileexplorerplugin.update_tree()
        if theme['apply to panels'] and self.treeplugin.settings['_enabled']:
            self.treeplugin.settings['background'] = theme['background']
            self.treeplugin.settings['foreground'] = theme['foreground']
            self.treeplugin.settings[FOREGROUND_TEXT] = theme[FOREGROUND_TEXT]
            self.treeplugin.settings[BACKGROUND_HELP] = theme[BACKGROUND_HELP]
            self.treeplugin.settings[FONT_SIZE] = theme[FONT_SIZE]
            self.treeplugin.settings[FONT_FACE] = theme[FONT_FACE]
            if self.treeplugin.settings['opened']:
                self.treeplugin.on_show_tree(None)

    def change_locale(self, message):
        if message.keys[0] != "General":
            return
        initial_locale = self._locale.GetName()
        try:
            code = self._get_language_code()
        except AttributeError:
            code = wx.LANGUAGE_ENGLISH_WORLD
        del self._locale
        self._locale = wx.Locale(code)
        if not self._locale.IsOk():
            self._locale = wx.Locale(wx.LANGUAGE_ENGLISH_WORLD)
        lpath = Path(__file__).parent.absolute()
        lpath = str(Path(Path.joinpath(lpath.parent, 'localization')).absolute())
        wx.Locale.AddCatalogLookupPathPrefix(lpath)
        self._locale.AddCatalog('RIDE')
        if len(message.keys) > 1:  # Avoid initial setting
            new_locale = self._locale.GetName()
            # print(f"DEBUG: application.py RIDE change_locale from {initial_locale} to {new_locale}")
            if initial_locale != new_locale:
                #if restart_dialog():  # DEBUG: See the in implementation why we don't restart
                # Shared memory to store language definition
                self._manage_shared_lang()

    @staticmethod
    def _manage_shared_lang():
        from multiprocessing import shared_memory
        from .restartutil import do_restart
        try:
            sharemem = shared_memory.ShareableList(['en'], name="language")
        except FileExistsError:  # Other instance created file
            sharemem = shared_memory.ShareableList(name="language")
        result = do_restart()
        if result:
            try:
                sharemem.shm.close()
                sharemem.shm.unlink()
            except FileNotFoundError:
                pass

    def _get_language_code(self):  #  -> Union[str, int]
        if languages:
            from ..preferences import Languages
            names = Languages.names
        else:
            names = [('English', 'en', wx.LANGUAGE_ENGLISH)]
        general = self.settings.get_without_default('General')
        language = general.get('ui language', 'English')
        try:
            idx = [lang[0] for lang in names].index(language)
            code = names[idx][2]
        except (IndexError, ValueError):
            print(f"DEBUG: application.py RIDE change_locale ERROR: Could not find {language=}")
            code = wx.LANGUAGE_ENGLISH_WORLD
        return code

    @staticmethod
    def update_excludes(message):
        if message.keys[0] != "Excludes":
            return
        from ..preferences.excludes_class import Excludes
        from ..context import SETTINGS_DIRECTORY
        excludes = Excludes(SETTINGS_DIRECTORY)
        paths = excludes.get_excludes().split()
        if paths:
            RideFSWatcherHandler.exclude_listening(paths)

    @staticmethod
    def _publish_system_info():
        from ..context import SYSTEM_INFO
        publish.RideLogMessage(SYSTEM_INFO).publish()

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
            maybe_editor = pl.conn_plugin
            if (isinstance(maybe_editor, EditorPlugin) or isinstance(maybe_editor, TextEditorPlugin)) and\
                    maybe_editor.__getattr__("_enabled"):
                return maybe_editor

    def _load_data(self):
        self.workspace_path = self.workspace_path or self._get_latest_path()
        if self.workspace_path:
            self._controller.update_default_dir(self.workspace_path)
            theme = self.settings.get_without_default('General')
            background = theme['background']
            foreground = theme['foreground']
            observer = LoadProgressObserver(self.frame, background=background, foreground=foreground)
            self._controller.load_data(self.workspace_path, observer)

    @staticmethod
    def _find_robot_installation():
        output = run_python_command(
            ['import robot; print(robot.__file__ + \", \" + robot.__version__)'])
        robot_found = b"ModuleNotFoundError" not in output and output
        system_encoding = get_system_encoding()
        if not robot_found:
            rf_info = subprocess.run(['robot', '--version'], capture_output=True)
            print(f"DEBUG: application-py RIDE _find_robot_installation command VERSION={rf_info.stdout}")
            if b"Robot Framework" in rf_info.stdout:
                rf_version = rf_info.stdout.replace(b"Robot Framework", b"").strip(b" ").split(b" ")[0]
                publish.RideLogMessage(_("Found Robot Framework version %s from %s.") % (
                    str(rf_version, system_encoding), "PATH")).publish()
                return rf_version
        if robot_found:
            rf_file, rf_version = output.strip().split(b", ")
            publish.RideLogMessage(_("Found Robot Framework version %s from %s.") % (
                str(rf_version, system_encoding), str(os.path.dirname(rf_file), system_encoding))).publish()
            return rf_version
        else:
            publish.RideLogMessage(publish.get_html_message('no_robot'), notify_user=True).publish()
            return None

    def _get_latest_path(self):
        last_file = None
        last_file_path = os.path.join(SETTINGS_DIRECTORY, 'last_file.txt')
        if os.path.isfile(last_file_path):
            with open(last_file_path, 'r', encoding='utf-8') as fp:
                last_file = fp.read()
        recent = self._get_recentfiles_plugin()
        if not recent or not recent.recent_files:
            if last_file:
                return last_file
            else:
                return None
        return last_file if last_file and last_file != recent.recent_files[0] else recent.recent_files[0]

    def _get_recentfiles_plugin(self):
        from ..recentfiles import RecentFilesPlugin
        for pl in self.get_plugins():
            try:
                plugin = pl.conn_plugin
                if plugin and isinstance(plugin, RecentFilesPlugin):
                    return plugin
            except AttributeError:
                pass

    def get_plugins(self):
        return self._plugin_loader.plugins

    def initialize_project_settings(self, path):
        """ Detects if exists a directory named .robot at project root, and creates ride_settings.cfg
            if not exists, or returns the path to existing file.
        """
        from ..preferences import initialize_settings
        if path:
            default_dir = path if os.path.isdir(path) else os.path.dirname(path)
            local_settings_dir = os.path.join(default_dir, '.robot')
        else:
            local_settings_dir = None
        old_settings_dir = self.settings_path
        # print(f"DEBUG: Project.py Project initialize_project_settings ENTER: path={local_settings_dir}")
        if local_settings_dir and os.path.isdir(local_settings_dir):
            local_settings = os.path.join(local_settings_dir, 'ride_settings.cfg')
            self.settings_path = local_settings
            if os.path.isfile(local_settings):
                os.environ['RIDESETTINGS'] = local_settings
                self.settings = RideSettings(local_settings)
            else:
                default = RideSettings()
                settings_path = default.user_path
                new_path = initialize_settings(path=settings_path, dest_file_name=local_settings)
                self.settings = RideSettings(new_path)
        else:
            os.environ['RIDESETTINGS'] = ''
        if self.settings_path != old_settings_dir:
            RideSettingsChanged(keys=('General', ), old=None, new=None).publish()
        return self.settings_path

    def dump_settings(self):
        keys = []
        for items in self.settings:
            keys.append(items)
        values = [f"{val}={self.settings[val]}" for val in keys]
        return values

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

    def OnEventLoopEnter(self, loop):  # Overrides wx method
        if loop and wx.EventLoopBase.IsMain(loop):
            RideFSWatcherHandler.create_fs_watcher(self.workspace_path)

    def on_app_activate(self, event):
        if self.workspace_path is not None and RideFSWatcherHandler.is_watcher_created():
            if event.GetActive():
                if not self.changed_workspace and RideFSWatcherHandler.is_workspace_dirty():
                    self.frame.show_confirm_reload_dlg(event)
                RideFSWatcherHandler.stop_listening()
            else:
                RideFSWatcherHandler.start_listening(self.workspace_path)
        event.Skip()
