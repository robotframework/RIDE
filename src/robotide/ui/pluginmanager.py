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
from wx.lib.scrolledpanel import ScrolledPanel


class PluginManager(object):
    _title = 'Manage Plugins'

    def __init__(self, notebook):
        self._notebook = notebook
        self._panel = None

    def show(self, plugins):
        if not self._panel:
            self._panel = PluginPanel(self._notebook, plugins)
        if not self._is_notebook_tab_created():
            self._add_to_notebook()
        self._notebook.SetSelection(self._notebook.GetPageIndex(self._panel))

    def _is_notebook_tab_created(self):
        for index in range(self._notebook.GetPageCount()):
            if self._notebook.GetPageText(index) == self._title:
                return True
        return False

    def _add_to_notebook(self):
        self._notebook.AddPage(self._panel, self._title)
        self._notebook.SetSelection(self._notebook.GetPageIndex(self._panel))


class PluginPanel(wx.Panel):

    def __init__(self, notebook, plugins):
        wx.Panel.__init__(self, notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._create_header(), 0, wx.LEFT|wx.RIGHT|wx.TOP, border=16)
        sizer.Add(self._create_line(), 0, wx.EXPAND|wx.LEFT|wx.RIGHT, border=16)
        sizer.Add(self._create_body(plugins), 1, wx.EXPAND|wx.ALL, border=16)
        self.SetSizer(sizer)

    def _create_header(self):
        header_panel = wx.Panel(self, wx.ID_ANY)
        header = wx.StaticText(header_panel, wx.ID_ANY, "Installed Plugins")
        header.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        return header

    def _create_line(self):
        return wx.StaticLine(self)

    def _create_body(self, plugins):
        panel = ScrolledPanel(self, wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        panel.SetupScrolling()
        sizer = wx.FlexGridSizer(1, 2, hgap=8, vgap=8)
        sizer.AddGrowableCol(1, 1)
        sizer.Add(self._create_label(panel, 'Enabled'), 0, wx.BOTTOM, border=8)
        sizer.Add(self._create_label(panel, 'Plugin'), 0,
                  wx.BOTTOM|wx.EXPAND, border=8)
        for plugin in plugins:
            sizer.Add(PluginActivationCheckBox(panel, plugin), 0,
                      wx.ALIGN_CENTER_HORIZONTAL)
            sizer.Add(PluginRow(panel, plugin), 0, wx.EXPAND)
        panel.SetSizer(sizer)
        return panel

    def _create_label(self, parent, text):
        boldFont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        boldFont.SetWeight(wx.FONTWEIGHT_BOLD)
        label = wx.StaticText(parent, wx.ID_ANY, text)
        label.SetFont(boldFont)
        return label

# TODO: Is this dead code? At least commenting it out does not affect loading plugins.
#    def OnCheckbox(self, plugin, evt):
#        """Handle checkbox events"""
#        if evt.IsChecked():
#            plugin.activate()
#        else:
#            plugin.deactivate()
        # TODO: move to Plugin
        #nb = self.get_notebook()
        #nb.SetSelection(nb.GetPageIndex(self.panel))


class PluginActivationCheckBox(wx.CheckBox):

    def __init__(self, parent, plugin):
        wx.CheckBox.__init__(self, parent)
        self.SetValue(plugin.active)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)
        if plugin.error:
            self.Enable(False)
        self._plugin = plugin

    def OnCheckBox(self, event):
        if event.IsChecked():
            self._plugin.activate()
        else:
            self._plugin.deactivate()


class PluginRow(wx.Panel):

    def __init__(self, parent, plugin):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._get_name(plugin))
        for name, value in plugin.metadata.items():
            sizer.Add(self._get_metadata(name, value))
        sizer.Add(self._get_description(plugin), 0, wx.EXPAND)
        config = plugin.config_panel(self)
        if config:
            sizer.Add(config, 1, wx.EXPAND|wx.LEFT, border=16)
        self.SetSizer(sizer)

    def _get_name(self, plugin):
        return wx.StaticText(self, label=plugin.name)

    def _get_metadata(self, name, value):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label='%s: ' % name))
        if value.split('://')[0] in ['http', 'https']:
            sizer.Add(wx.HyperlinkCtrl(self, -1, label=value, url=value))
        else:
            sizer.Add(wx.StaticText(self, label=value))
        return sizer

    def _get_description(self, plugin):
        desc = wx.StaticText(self, label=plugin.doc)
        if plugin.error:
            desc.SetForegroundColour("firebrick")
        return desc
