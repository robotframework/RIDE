#  Copyright 2020-     Robot Framework Foundation
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
import wx
import wx.lib.agw.aui as aui
from wx import Colour
from wx.lib.agw.aui import GetManager

from ..controller.filecontrollers import start_filemanager
from ..controller.project import Project
from ..pluginapi import Plugin
from ..pluginapi.plugin import ActionInfo
from ..preferences import PreferenceEditor
from ..publish import RideSettingsChanged, PUBLISHER
from ..widgets import PopupCreator, PopupMenuItems, VerticalSizer, HorizontalSizer, ButtonWithHandler, RIDEDialog

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

FILE_MANAGER = 'file manager'
LABEL_OPEN = 'Open'
LABEL_OPEN_FOLDER = 'Open Containing Folder'
PLUGIN_NAME = 'File Explorer'


class FileExplorerPlugin(Plugin):
    __doc__ = _("""Provides a tree view for Files and Folders. Opens selected item with mouse right-click.""")

    datafile = property(lambda self: self.get_selected_datafile())
    defaults = {"opened": True,
                "docked": True,
                "own colors": False,
                "file manager": None,
                "system file explorer": True
                }

    def __init__(self, application, controller=None):
        Plugin.__init__(self, application, default_settings=self.defaults)
        self.app = application
        self.settings = self.app.settings.config_obj['Plugins']['File Explorer']
        # self._parent = self.app.GetTopWindow()  # self._parent = self.frame wx.App.Get()
        # self._parent = self.app.frame
        self._parent = None
        self._mgr = None
        # self._mgr = GetManager(self._parent)
        # print(f"DEBUG: FileExplorerPlugin INIT parent={self._parent} mgr={self._mgr}")
        self._controller = controller
        self.general_settings = self.global_settings.config_obj['General']
        self.html_font_size = self.general_settings.get('font size', 11)
        # if self.file_explorer is None:
        ## self.file_explorer = FileExplorer(self._parent, plugin=self, controller=self._controller)
        # self.file_explorer = self.app.frame.filemgr
        self.file_explorer = None
        # self.__setattr__('file_explorer', self.file_explorer)
        # else:
        # self.file_explorer = self.file_explorer
        # self.file_explorer.SetThemeEnabled(True)
        # self._mgr = GetManager(self.file_explorer)
        self._pane = None
        self._filetreectrl = None
        self.config_dlg = None
        self.opened = self.settings['opened']
        # self.font = self.file_explorer.GetFont()
        self.font = None
        self._popup_creator = PopupCreator()
        self._actions = [
            _('Open'),
            '---',
            _('Open Containing Folder')
        ]
        self._actions_nt = [
            LABEL_OPEN,
            '---',
            LABEL_OPEN_FOLDER
        ]

    def register_frame(self, parent=None):
        if parent:
            self._parent = parent
            self._mgr = GetManager(self._parent)
            # self._mgr = self.frame.aui_mgr
            self.file_explorer = self._parent.filemgr
            self.file_explorer.SetThemeEnabled(True)
            self.font = self.file_explorer.GetFont()
            # print(f"DEBUG: FileExplorerPlugin INIT parent={self._parent} mgr={self._mgr}")
            if self._mgr.GetPane("file_manager") in self._mgr._panes:
                register = self._mgr.InsertPane
            else:
                register = self._mgr.AddPane

            register(self.file_explorer, wx.lib.agw.aui.AuiPaneInfo().Name("file_manager").
                     Caption(_("Files")).LeftDockable(True).CloseButton(False))

            self._mgr.Update()

    def enable(self):
        self.register_action(ActionInfo(_('View'), _('View File Explorer'), self.toggle_view,
                                        shortcut='F11',
                                        doc=_('Show File Explorer panel'),
                                        position=1))
        if self.file_explorer:
            self.show_file_explorer()
        # if not self.opened:
        #     self.close_tree()

    def close_tree(self):
        # self.save_setting('opened', False)
        self.opened = False
        self._mgr = GetManager(self.app.frame)
        if not self._mgr:
            return
        # self._mgr = self.app.frame.aui_mgr
        if not self.file_explorer:
            self.file_explorer = self.frame.filemgr
        # print(f"DEBUG: FileExplorerPlugin ENTER close_tree file_explorer={self.file_explorer}")
        # self._mgr.DetachPane(self.file_explorer) DestroyOnClose()
        pane_info = self._mgr.GetPane("file_manager")
        if pane_info.IsOk():
            if pane_info.IsFloating():
                pane_info.DestroyOnClose()
                self._mgr.DetachPane(self.file_explorer)
                self.save_setting('docked', False)
            else:
                self._mgr.ClosePane(pane_info.Hide())
                self.save_setting('docked', True)
        # perspective = self._mgr.SavePaneInfo(pane_info)
        # print(f"DEBUG: FileExplorerPlugin call close_tree perspective={perspective}")
        # self.save_setting('perspective', perspective)
        self.save_setting('opened', False)
        self._mgr.Update()

    def is_focused(self):
        return self.file_explorer.HasFocus()

    def toggle_view(self, event):
        __ = event
        self.save_setting('opened', not self.opened)
        # if not self._mgr:
        #     self._mgr = self.app.frame.aui_mgr
        # pane_info = self._mgr.GetPane("file_manager")
        # perspective = self._mgr.SavePaneInfo(pane_info)
        # print(f"DEBUG: FileExplorerPlugin call toggle_view perspective={perspective}")
        # self.save_setting('perspective', perspective)
        if not self.opened:
            self.opened = True
            self.show_file_explorer()
        else:
            self.close_tree()

    def show_file_explorer(self):
        if not self._parent:
            self._parent = self.frame
        if not self.file_explorer:
            self.file_explorer = self.app.frame.filemgr
        self._mgr = GetManager(self.app.frame)
        apply_global = self.general_settings['apply to panels']
        use_own = self.settings['own colors']
        if apply_global and not use_own:
            html_background = self.general_settings.get('background help', (240, 242, 80))
            html_foreground = self.general_settings.get('foreground text', (7, 0, 70))
        else:
            html_background = self.settings.get('background', (240, 242, 80))
            html_foreground = self.settings.get('foreground', (7, 0, 70))
        html_font_face = self.general_settings.get('font face', '')
        html_font_size = self.general_settings.get('font size', 11)
        self.html_font_face = self.settings.get('font face', html_font_face)
        self.html_font_size = self.settings.get('font size', html_font_size)
        self._filetreectrl = self.file_explorer.tree_ctrl.GetTreeCtrl()
        self.file_explorer.Show(True)
        # self.file_explorer.Raise()
        self.file_explorer.SetMinSize(wx.Size(200, 225))
        self.file_explorer.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
        self.file_explorer.SetBackgroundColour(html_background)
        self.file_explorer.SetForegroundColour(html_foreground)
        self.font = self.file_explorer.GetFont()
        self.font.SetFaceName(self.html_font_face)
        self.font.SetPointSize(self.html_font_size)
        self.file_explorer.SetFont(self.font)
        self.file_explorer.Refresh()
        self._filetreectrl.SetBackgroundColour(html_background)
        self._filetreectrl.SetForegroundColour(html_foreground)
        self._filetreectrl.SetFont(self.font)
        self._filetreectrl.Fit()
        self._filetreectrl.Refresh()
        self.file_explorer.Raise()
        if not self._controller:
            self._controller = self.app._controller  # Ugly but better than nothing
        if self._controller:
            self._pane = self._mgr.GetPane("file_manager")
            if not self._pane.IsOk():
                self._mgr.DetachPane("file_manager")
                if not self.__getattr__('docked'):
                    self._mgr.AddPane(self.file_explorer, wx.lib.agw.aui.AuiPaneInfo().Name("file_manager").
                                      Caption(_("Files")).LeftDockable(True).CloseButton(False).Float())
                else:
                    self._mgr.AddPane(self.file_explorer, wx.lib.agw.aui.AuiPaneInfo().Name("file_manager").
                                      Caption(_("Files")).LeftDockable(True).CloseButton(False).Dock())
                self._pane = self._mgr.GetPane("file_manager")
        if self._pane:
            self._pane.Show(True)
            if not self.__getattr__('docked'):
                self._pane.Float()
            else:
                self._pane.Dock()
            self._mgr.RestorePane(self._pane)
            """
            try:
                perspective = self.settings['perspective']
            except AttributeError:
                perspective = None
            if perspective:  # Values are being saved empty
                print(f"DEBUG: FileExplorer show_file_explorer LoadPaneInfo PANE perspective={perspective} "
                      f"type={type(perspective)}")
                self._mgr.LoadPaneInfo("file_manager", perspective)
            """
        self._mgr.Update()
        self.update_tree()

    def update_tree(self):
        if not self.file_explorer:
            return
        self.file_explorer.update_tree()

    def show_popup(self):
        self._popup_creator.show(self.file_explorer, PopupMenuItems(self, self._actions, self._actions_nt), self._controller)

    def on_open(self, event):
        # __ = event
        print(f"DEBUG: FileExplorerPlugin call on_open_file={event}\n"
              f"{self.file_explorer.current_path}")
        self._parent.on_open_file(event)

    def on_open_containing_folder(self, event):
        __ = event
        print(f"DEBUG: FileExplorerPlugin call on_open_containing_folder={event}")
        try:
            use_sys_file_explorer = self.settings['system file explorer']
            own_file_manager = self.settings[FILE_MANAGER]
            if not use_sys_file_explorer and own_file_manager:
                file_manager = self.settings[FILE_MANAGER]
            else:
                file_manager = self.global_settings[FILE_MANAGER]
        except KeyError:
            file_manager = None
        #  self._controller.execute(
        #  ctrlcommands.OpenContainingFolder(file_manager, self.file_explorer.current_path)
        print(f"DEBUG: FileExplorerPlugin call file manager={file_manager}")
        start_filemanager(self.file_explorer.current_path, file_manager)

    def on_config_panel(self):
        if not self.config_dlg:
            self.config_dlg = self.config_panel(self.frame)
        self.config_dlg.Show(True)

    def config_panel(self, parent):
        __ = parent
        _parent = wx.GetTopLevelWindows()
        dlg = PreferenceEditor(_parent[0], _("RIDE - Preferences"),
                               self.app.preferences, style='single', index=7)
        dlg.Show(False)
        return dlg


class FileExplorer(wx.Panel):  # wx.GenericDirCtrl,

    def __init__(self, parent, plugin, controller=None):
        wx.Panel.__init__(self, parent)
        self.name = 'files_explorer'
        self.parent = parent
        self._plugin = plugin
        self._controller = controller
        self.dlg = RIDEDialog()
        self.SetBackgroundColour(Colour(self.dlg.color_background))
        self.SetForegroundColour(Colour(self.dlg.color_foreground))
        # self.sizer = VerticalSizer()
        self.sizer = wx.FlexGridSizer(cols=1, hgap=5, vgap=5)
        print(f"DEBUG: FileExplorer INIT sizer={self.sizer}")
        self.SetSizer(self.sizer)
        self._create_pane_toolbar()
        self.tree_ctrl = wx.GenericDirCtrl(parent=self, id=-1, style=wx.DIRCTRL_3D_INTERNAL)
        # wx.BORDER_NONE   size=(200, 205),
        # wx.GenericDirCtrl.__init__(self, parent=self, id=-1, size=(200, 225), style=wx.DIRCTRL_3D_INTERNAL)
        tsizer = VerticalSizer()
        tsizer.Add(self.tree_ctrl, proportion=1, flag=wx.EXPAND)
        self.sizer.Add(wx.Size(35, 35))
        self.sizer.Add(tsizer, proportion=1, flag=wx.EXPAND)
        self._right_click = False
        self.current_path = None
        self._apply_settings()
        self.Bind(wx.EVT_CLOSE, self.on_close)
        # self.Bind(wx.EVT_SIZE, self.on_size)  # DEBUG With this activated, the "toolbar" is hidden
        self.Bind(wx.EVT_MOVE, self.on_size)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.on_right_click)
        PUBLISHER.subscribe(self.on_settings_changed, RideSettingsChanged)
        self.SetThemeEnabled(True)
        self.SetAutoLayout(True)
        self.Refresh()

    def update_tree(self):
        print(f"DEBUG: FileExplorer update_tree ENTER {self._controller}\n")
        if isinstance(self._controller, Project):
            if self._controller.data and len(self._controller.data.directory) > 1:
                # wnd_list = wx.GetTopLevelParent(self.parent)
                # wnd_txt_file_explorer = [ wnd for wnd in wnd_list if wnd.name == 'File Explorer']
                # wnd_txt_file_explorer = wx.FindWindowByName(self.parent, name='File Explorer')
                # txt_field = wx.TextCtrl.FindWindowByName('file_manager', wnd_txt_file_explorer)
                # txt_field = [txt_field for txt_field in wnd_txt_file_explorer if txt_field.name == 'file_manager']
                # if len(txt_field) == 1:
                #     txt_field = txt_field[0]
                self._apply_settings()
                print(f"DEBUG: FileExplorer update_tree VALID {self._controller.data.directory}\n")
                """
                      f"wnd_txt_file_explorer={wnd_txt_file_explorer}  txt_field={txt_field}")
                if self._plugin.settings['system file explorer']:
                    txt_field.SetEditable(False)
                    txt_field.Disable()
                else:
                    txt_field.Enable()
                    txt_field.SetEditable(True)
                """
                self.tree_ctrl.SelectPath(self._controller.data.source)
                try:
                    self.tree_ctrl.ExpandPath(self._controller.data.source)
                    self.tree_ctrl.TreeCtrl.EnsureVisible(self.tree_ctrl.TreeCtrl.GetSelection())
                except Exception:
                    pass
                # self.on_size(None)
                self.Refresh()
                self.Update()
                self.tree_ctrl.Update()

    def _apply_settings(self):
        apply_to_panels = self._plugin.general_settings['apply to panels']
        own_colors = self._plugin.settings['own colors']
        tc = self.tree_ctrl.GetTreeCtrl()
        if not own_colors:
            if apply_to_panels:  # Missing toolbar colors
                self.SetBackgroundColour(Colour(self._plugin.general_settings['background help']))
                self.SetForegroundColour(Colour(self._plugin.general_settings['foreground text']))
                self.tree_ctrl.SetBackgroundColour(Colour(self._plugin.general_settings['background help']))
                self.tree_ctrl.SetForegroundColour(Colour(self._plugin.general_settings['foreground text']))
                tc.SetBackgroundColour(Colour(self._plugin.general_settings['background help']))
                tc.SetForegroundColour(Colour(self._plugin.general_settings['foreground text']))
            else:
                self.SetBackgroundColour(Colour(self._plugin.general_settings['background']))
                self.SetForegroundColour(Colour(self._plugin.general_settings['foreground']))
                self.tree_ctrl.SetBackgroundColour(Colour(self._plugin.general_settings['background']))
                self.tree_ctrl.SetForegroundColour(Colour(self._plugin.general_settings['foreground']))
                tc.SetBackgroundColour(Colour(self._plugin.general_settings['background']))
                tc.SetForegroundColour(Colour(self._plugin.general_settings['foreground']))
            self.tool_bar_txt.SetBackgroundColour(Colour(self._plugin.general_settings['secondary background']))
            self.tool_bar_txt.SetForegroundColour(Colour(self._plugin.general_settings['secondary foreground']))
        else:
            self.SetBackgroundColour(Colour(self._plugin.settings['background']))
            self.SetForegroundColour(Colour(self._plugin.settings['foreground']))
            self.tree_ctrl.SetBackgroundColour(Colour(self._plugin.settings['background']))
            self.tree_ctrl.SetForegroundColour(Colour(self._plugin.settings['foreground']))
            tc.SetBackgroundColour(Colour(self._plugin.settings['background']))
            tc.SetForegroundColour(Colour(self._plugin.settings['foreground']))
            self.tool_bar_txt.SetBackgroundColour(Colour(self._plugin.settings['secondary background']))
            self.tool_bar_txt.SetForegroundColour(Colour(self._plugin.settings['secondary foreground']))
        self.font = self.GetFont()
        self.font.SetFaceName(self._plugin.settings['font face'])
        self.font.SetPointSize(self._plugin.settings['font size'])
        self.SetFont(self.font)
        tc.Fit()
        tc.Refresh()
        tc.Update()
        self.tree_ctrl.SetFont(self.font)
        self.tree_ctrl.Fit()
        self.tool_bar_txt.SetFont(self.font)
        self.tree_ctrl.Refresh()

    def on_close(self, event):
        __ = event
        print("DEBUG: FileExplorer OnClose hidding")
        self._plugin.close_tree()

    def on_size(self, event):
        __ = event
        self.update_tree()
        sz = self.GetSize()  # + wx.Size(-5, -5)
        print(f"DEBUG: FileExplorer On size refreshing. sz={sz}")
        tc = self.tree_ctrl.GetTreeCtrl()
        tc.SetSize(sz)
        tc.Fit()
        tc.Refresh()
        self.tree_ctrl.Fit()
        self.tree_ctrl.Refresh()
        self.tree_ctrl.Update()

    def on_right_click(self, event):
        # __ = event
        # event.Skip()
        print(f"DEBUG: FileExplorer mouse RightClick event={event} controller={self._controller}")
        if not self._right_click:
            self._right_click = True
        handler = None
        # item = self.HitTest(self.ScreenToClient(wx.GetMousePosition()))  #  wx.TREE_HITTEST_ONITEMLABEL)
        tc = self.tree_ctrl.GetTreeCtrl()
        # item, _ = tc.HitTest(self.ScreenToClient(wx.GetMousePosition()))
        item = tc.GetSelection()
        if item:
            print(f"DEBUG: FileExplorer mouse RightClick item={item} type={type(item)}")
            # id=self.GetPopupMenuSelectionFromUser()
            handler = self.tree_ctrl.GetPath(item)  # self.GetItemData(item)
        if handler:
            # handler.show_popup()
            self.current_path = handler
            print(f"DEBUG: FileExplorer PATH={handler}")
            if self._plugin:
                self._plugin.show_popup()
            self._right_click = False

    def on_settings_changed(self, message):
        """Redraw the colors if the color settings are modified"""
        if message.keys[0] == "General":
            print(f"DEBUG: FileExplorer on_settings_changed GENERAL={message.keys}\n"
                  f"settings={self._plugin.general_settings}")
            if message.keys[-1] == "apply to panels":
                self.update_tree()
            return
        section, _ = message.keys
        if section == PLUGIN_NAME:
            print(f"DEBUG: FileExplorer on_settings_changed SECTION={message.keys}\n"
                  f"settings={self._plugin.settings}")
            self.update_tree()
            """
            self.editor.autocomplete = self.settings[PLUGIN_NAME].get(AUTO_SUGGESTIONS, False)
            caret_colour = self.settings[PLUGIN_NAME].get('setting', 'black')
            caret_colour = self.editor.get_visible_color(caret_colour)
            self.editor.SetCaretForeground(Colour(caret_colour))
            caret_style = self.settings[PLUGIN_NAME].get('caret style', 'block')
            caret_style = stc.STC_CARETSTYLE_BLOCK if caret_style.lower() == 'block' else stc.STC_CARETSTYLE_LINE
            self.editor.SetCaretStyle(caret_style)
            """

    def general_font_size(self) -> int:
        fsize = self.dlg.font_size
        print(f"DEBUG: FileExplorer return general_font_size fsize={fsize}")
        return fsize

    def _create_pane_toolbar(self):
        # needs extra container, since we might add helper
        # text about syntax colorization
        self.pane_toolbar = HorizontalSizer()
        default_components = HorizontalSizer()
        self.tool_bar_txt = wx.StaticText(self, label="Add Tool Here")  # DEBUG To use later if needed
        self.tool_bar_txt.SetBackgroundColour(Colour(self.dlg.color_secondary_background))
        self.tool_bar_txt.SetForegroundColour(Colour(self.dlg.color_secondary_foreground))
        self.config_button = ButtonWithHandler(self, _('Settings'), bitmap='wrench.png', fsize=self._plugin.html_font_size,
                                          handler=lambda e: self._plugin.on_config_panel())
        self.config_button.SetBackgroundColour(Colour(self.dlg.color_background))
        self.config_button.SetOwnBackgroundColour(Colour(self.dlg.color_background))
        self.config_button.SetForegroundColour(Colour(self.dlg.color_foreground))
        default_components.add_with_padding(self.tool_bar_txt)
        # self._create_search(default_components)
        self.pane_toolbar.add_expanding(default_components)
        self.pane_toolbar.AddStretchSpacer()
        self.pane_toolbar.add_with_padding(self.config_button)
        # self.sizer.add_expanding(self.pane_toolbar, propotion=0)
        self.sizer.Add(self.pane_toolbar, proportion=0)
