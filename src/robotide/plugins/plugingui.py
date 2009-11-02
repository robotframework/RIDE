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

import wx
from plugin import Plugin
from wx.lib.scrolledpanel import ScrolledPanel

from robotide.context import SETTINGS

ID_PLUGIN_MANAGER = wx.NewId()


class PluginManagerPlugin(Plugin):
    """GUI component for managing plugins, implemented as a plugin (!)"""

    def __init__(self, application):
        url = "http://code.google.com/p/robotframework-ride/"
        Plugin.__init__(self, application, metadata={'url': url})
        self.panel = None
        self.settings = SETTINGS.add_section('plugins')

    def activate(self):
        """Make the plugin available"""
        # in the case of this plugin, "active" means there's an item on
        # the tools menu. We don't actually create a notebook page 
        # until the user clicks on the menu item
        self._add_to_menubar()

    def OnShowManager(self, event):
        if not self.panel:
            self._add_to_notebook()
        notebook = self.get_notebook()
        notebook.SetSelection(notebook.GetPageIndex(self.panel))
        self._refresh()

    def _refresh(self):
        """Refresh the list of plugins"""
        plugin_panel_sizer = self.plugin_panel.GetSizer()
        plugin_panel_sizer.Clear(True)
        st1 = wx.StaticText(self.plugin_panel, wx.ID_ANY, "Enabled?")
        st2 = wx.StaticText(self.plugin_panel, wx.ID_ANY, "Plugin")
        boldFont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        boldFont.SetWeight(wx.FONTWEIGHT_BOLD)
        st1.SetFont(boldFont)
        st2.SetFont(boldFont)
        plugin_panel_sizer.Add(st1, 0, wx.BOTTOM, border=8)
        plugin_panel_sizer.Add(st2, 0, wx.BOTTOM|wx.EXPAND, border=8)
        for plugin in self._app._plugins.plugins:
            cb = wx.CheckBox(self.plugin_panel, wx.ID_ANY)
            cb.SetValue(plugin.active)
            p = PluginPanel(self.plugin_panel, wx.ID_ANY, plugin)
            plugin_panel_sizer.Add(cb, 0, wx.ALIGN_CENTER_HORIZONTAL)
            plugin_panel_sizer.Add(p,  0, wx.EXPAND)
            self.plugin_panel.Bind(wx.EVT_CHECKBOX, lambda evt, plugin=plugin: self.OnCheckbox(plugin, evt), cb)
            if plugin.error:
                cb.Enable(False)
        self.panel.Layout()
        self.plugin_panel.Layout()

    def OnCheckbox(self, plugin, evt):
        """Handle checkbox events"""
        if evt.IsChecked():
            plugin.activate()
        else:
            plugin.deactivate()
        # FIXME: saves the wrong settings
        self._save_settings()
        # TODO: move to Plugin
        nb = self.get_notebook()
        nb.SetSelection(nb.GetPageIndex(self.panel))

    def _save_settings(self):
        """Saves the state of the plugins to the settings file"""
        for plugin in self._app._plugins.plugins:
            self.settings[plugin.name] = plugin.active
        self.settings.save()

    def _add_to_notebook(self):
        """Add a tab for this plugin to the notebook if there's not already one"""
        notebook = self.get_notebook()
        self.panel = wx.Panel(notebook)
        notebook.AddPage(self.panel, "Manage Plugins")
        # notebook panel is composed of two sections, a header and
        # the "plugin panel". The latter is a scrolled window that
        # has a row for each plugin.
        header_panel = wx.Panel(self.panel, wx.ID_ANY)
        header = wx.StaticText(header_panel, wx.ID_ANY, "Installed Plugins")
        header.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        plugin_panel = ScrolledPanel(self.panel, wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        plugin_panel.SetupScrolling()
        plugin_panel_sizer = wx.FlexGridSizer(1, 2, hgap=8, vgap=8)
        plugin_panel_sizer.AddGrowableCol(1, 1)
        plugin_panel.SetSizer(plugin_panel_sizer)
        line = wx.StaticLine(self.panel)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(main_sizer)
        main_sizer.Add(header_panel, 0, wx.LEFT|wx.RIGHT|wx.TOP, border=16)
        main_sizer.Add(line, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border=16)
        main_sizer.Add(plugin_panel, 1, wx.EXPAND|wx.ALL, border=16)
        self.plugin_panel = plugin_panel

    def _add_to_toolbar(self):
        pass

    def _add_to_menubar(self):
        """Add a menu item on the Tools menu"""
        menubar = self.get_menu_bar()
        if menubar:
            pos = menubar.FindMenu("Tools")
            tools_menu = menubar.GetMenu(pos)
            tools_menu.Append(ID_PLUGIN_MANAGER, "Manage Plugins")
            wx.EVT_MENU(self._frame, ID_PLUGIN_MANAGER, self.OnShowManager)
                   
        
class PluginPanel(wx.Panel):
    """Panel to display the details and configuration options of a plugin."""

    # TODO: there needs to be some smarter handling of long descriptions,
    # such as having them auto-wrap to the size of the window and/or
    # accept some basic HTML.tags.
    def __init__(self, parent, id, plugin):
        wx.Panel.__init__(self, parent, id)
        config = plugin.config_panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, plugin.name), 0)
        # TODO: Add plugin metadata 
        sizer.Add(self._get_description(plugin), 0, wx.EXPAND)
        if config:
            sizer.Add(config, 1, wx.EXPAND|wx.LEFT, border=16)
        self.SetSizer(sizer)

    def _name_ctrl(self):
        """Return a suitable control for displaying the plugin name

        This will return a HyperlinkCtrl if an url is defined,
        a StaticText otherwise.
        """
        text = self.plugin.name + " (version %s)" % self.plugin.version
        if self.plugin.url:
            ctrl = wx.HyperlinkCtrl(self, wx.ID_ANY, text, self.plugin.url)
        else:
            ctrl = None
        return ctrl

    def _get_description(self, plugin):
        """Returns an appropriate descriptive string for a plugin"""
        if not plugin.error:
            return wx.StaticText(self, label=plugin.doc)
        text = "This plugin is disabled because it failed to load properly.\n" \
               + "Error: " + plugin.error
        desc = wx.StaticText(self, label=text)
        desc.SetForegroundColour("firebrick")
        return desc
