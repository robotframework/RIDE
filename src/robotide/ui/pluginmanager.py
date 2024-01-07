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
import wx
from wx import Colour
from wx.adv import HyperlinkCtrl
from wx.lib.scrolledpanel import ScrolledPanel

from ..context import LOG
from ..publish import RideLogException
from ..widgets import Label, RIDEDialog

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class PluginManager(object):

    def __init__(self, notebook):
        self._notebook = notebook
        self._panel = None

    def show(self, plugins):
        if not self._panel:
            self._panel = _PluginPanel(self._notebook.GetParent(), plugins, self._show_panel)
        self._show_panel()

    def _show_panel(self):
        self._panel.Show()


class _PluginPanel(RIDEDialog):

    def __init__(self, notebook, plugins, activation_callback):
        RIDEDialog.__init__(self, parent=notebook, title=_("Manage Plugins"), size=(800, 600))
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._create_header(), 0, flag=wx.EXPAND | wx.LEFT |
                                                 wx.RIGHT | wx.TOP, border=16)
        sizer.Add(self._create_info_text(), 0,
                  flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=16)
        sizer.Add(self._create_line(), 0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)
        sizer.Add(self._create_body(plugins, activation_callback), 1,
                  flag=wx.EXPAND | wx.ALL, border=16)
        self.SetSizer(sizer)
        self.CenterOnParent()

    def _create_header(self):
        header = Label(self, wx.ID_ANY, _("Installed Plugins\n"))
        self.font = self.GetFont()
        self.font.SetPointSize(self.font_size)
        if self.font_face is None:
            self.font_face = self.font.GetFaceName()
        else:
            self.font.SetFaceName(self.font_face)
        self.SetFont(self.font)
        header.SetFont(wx.Font(wx.FontInfo(14 if self.font_size<=11 else self.font_size + 3).Bold()))
        return header

    def _create_line(self):
        return wx.StaticLine(self)

    def _create_body(self, plugins, activation_callback):
        panel = ScrolledPanel(self, wx.ID_ANY, style=wx.TAB_TRAVERSAL | wx.SIZE_AUTO)
        panel.SetupScrolling()
        sizer = wx.FlexGridSizer(0, 2, hgap=8, vgap=8)
        sizer.AddGrowableCol(1, 1)
        sizer.Add(self._create_label(panel, _('Enabled')), 0, wx.BOTTOM, border=8)
        sizer.Add(self._create_label(panel, _('Plugin')), 0, wx.BOTTOM | wx.EXPAND, border=8)
        for plugin in sorted(plugins, key=lambda p: p.name):
            sizer.Add(_PluginEnablationCheckBox(panel, plugin,
                                                activation_callback),
                      flag=wx.ALIGN_CENTER_HORIZONTAL)
            sizer.Add(_PluginRow(panel, plugin), 0, wx.EXPAND)
        panel.SetSizer(sizer)
        return panel

    def _create_info_text(self):
        info = wx.StaticText(self, wx.ID_ANY, _("Info. Enabling and disabling plugins might"
                                                " require RIDE restart for menus to work."))
        info.SetFont(wx.Font(wx.FontInfo(12).Family(wx.FONTFAMILY_SWISS).Bold(False)))
        return info

    def _create_label(self, parent, text):
        bold_font = self.GetFont()
        if self.font_face:
            bold_font.SetFaceName(self.font_face)
        bold_font.SetWeight(wx.FONTWEIGHT_BOLD)
        bold_font.SetPointSize(self.font_size)
        label = Label(parent, wx.ID_ANY, text)
        label.SetFont(bold_font)
        return label


class _PluginEnablationCheckBox(wx.CheckBox):

    def __init__(self, parent, plugin, activation_callback):
        wx.CheckBox.__init__(self, parent)
        self.SetValue(plugin.enabled)
        self.Bind(wx.EVT_CHECKBOX, self.on_check_box)
        if plugin.error:
            self.Enable(False)
        self._plugin = plugin
        self._callback = activation_callback

    def on_check_box(self, event):
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
                                                                                   self._plugin.name,
                                                                                   err)
            self._plugin.error = err
            self._plugin.doc = msg
            LOG.error(msg)
            RideLogException(message=msg, exception=err, level='ERROR').publish()


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
