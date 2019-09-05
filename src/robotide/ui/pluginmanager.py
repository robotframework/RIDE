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

import wx
from wx.lib.scrolledpanel import ScrolledPanel

from robotide.context import LOG
from robotide.publish import RideLogException
from robotide.widgets import Label

if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
    from wx.adv import HyperlinkCtrl
else:
    from wx import HyperlinkCtrl


class PluginManager(object):

    def __init__(self, notebook):
        self._notebook = notebook
        self._tab = None

    def show(self, plugins):
        if not self._tab:
            self._tab = _PluginPanel(self._notebook, plugins, self._show_tab)
            self._notebook.add_tab(self._tab, 'Manage Plugins',
                                   allow_closing=True)
        self._show_tab()

    def _show_tab(self):
        self._notebook.show_tab(self._tab)


class _PluginPanel(wx.Panel):

    def __init__(self, notebook, plugins, activation_callback):
        wx.Panel.__init__(self, notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._create_header(), 0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
                  border=16)
        sizer.Add(self._create_info_text(), 0,
                  flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=16)
        sizer.Add(self._create_line(), 0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)
        sizer.Add(self._create_body(plugins, activation_callback), 1,
                  flag=wx.EXPAND | wx.ALL, border=16)
        self.SetSizer(sizer)

    def _create_header(self):
        header_panel = wx.Panel(self, wx.ID_ANY)
        header = Label(header_panel, wx.ID_ANY, "Installed Plugins")
        if wx.VERSION >= (4, 0, 0, ''):  # DEBUG wxPhoenix
            header.SetFont(wx.Font(wx.FontInfo(14).Family(wx.FONTFAMILY_SWISS).Bold()))
        else:
            header.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
        return header

    def _create_line(self):
        return wx.StaticLine(self)

    def _create_body(self, plugins, activation_callback):
        panel = ScrolledPanel(self, wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        panel.SetupScrolling()
        sizer = wx.FlexGridSizer(0, 2, hgap=8, vgap=8)
        sizer.AddGrowableCol(1, 1)
        sizer.Add(self._create_label(panel, 'Enabled'), 0, wx.BOTTOM, border=8)
        sizer.Add(self._create_label(panel, 'Plugin'), 0, wx.BOTTOM |
                  wx.EXPAND, border=8)
        for plugin in sorted(plugins, key=lambda p: p.name):
            sizer.Add(_PluginEnablationCheckBox(panel, plugin,
                                                activation_callback),
                      flag=wx.ALIGN_CENTER_HORIZONTAL)
            sizer.Add(_PluginRow(panel, plugin), 0, wx.EXPAND)
        panel.SetSizer(sizer)
        return panel

    def _create_info_text(self):
        info = wx.StaticText(self, wx.ID_ANY,
                             "Info. Enabling and disabling plugins might \
require RIDE restart for menus to work.")
        if wx.VERSION >= (4, 0, 0, ''):  # DEBUG wxPhoenix
            info.SetFont(wx.Font(wx.FontInfo(12).Family(wx.FONTFAMILY_SWISS).Bold(False)))
        else:
            info.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.FONTWEIGHT_NORMAL))
        return info

    def _create_label(self, parent, text):
        if wx.VERSION >= (3, 0, 2, 0, ''):
            boldFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        else:
            boldFont = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        boldFont.SetWeight(wx.FONTWEIGHT_BOLD)
        label = Label(parent, wx.ID_ANY, text)
        label.SetFont(boldFont)
        return label


class _PluginEnablationCheckBox(wx.CheckBox):

    def __init__(self, parent, plugin, activation_callback):
        wx.CheckBox.__init__(self, parent)
        self.SetValue(plugin.enabled)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)
        if plugin.error:
            self.Enable(False)
        self._plugin = plugin
        self._callback = activation_callback

    def OnCheckBox(self, event):
        if event.IsChecked():
            self._execute(self._plugin.enable)
        else:
            self._execute(self._plugin.disable)
        self._callback()

    def _execute(self, method):
        try:
            method()
        except Exception as err:
            self.SetValue(False)
            self.Enable(False)
            msg = 'Failed to %s plugin %s:\n%s\n\nYou should restart RIDE now!' % (method.__name__,
                                                   self._plugin.name, err)
            self._plugin.error = err
            self._plugin.doc = msg
            LOG.error(msg)
            RideLogException(message=msg, exception=err,
                             level='ERROR').publish()


class _PluginRow(wx.Panel):

    def __init__(self, parent, plugin):
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._get_name(plugin))
        for name, value in plugin.metadata.items():
            sizer.Add(self._get_metadata(name, value))
        sizer.Add(self._get_description(plugin), 0, wx.EXPAND)
        config = plugin.config_panel(self)
        if config:
            sizer.Add(config, 1, wx.EXPAND | wx.LEFT, border=16)
        self.SetSizer(sizer)

    def _get_name(self, plugin):
        return Label(self, label=plugin.name)

    def _get_metadata(self, name, value):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(Label(self, label='%s: ' % name))
        if value.split('://')[0] in ['http', 'https']:
            sizer.Add(HyperlinkCtrl(self, -1, label=value, url=value))
        else:
            sizer.Add(Label(self, label=value))
        return sizer

    def _get_description(self, plugin):
        desc = Label(self, label=plugin.doc)
        if plugin.error:
            desc.SetForegroundColour("firebrick")
        return desc
