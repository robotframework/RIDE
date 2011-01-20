# Copyright 2010 Orbitz WorldWide
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''runProfiles.py

This module contains profiles for running robot tests via the
runnerPlugin.

Each class that is a subclass as BaseProfile will appear in a
drop-down list within the plugin. The chosen profile will be used to
build up a command that will be passed in the tests to run as well as
any additional arguments.
'''

import wx
import re
import os

class BaseProfile(object):
    '''Base class for all test runner profiles

    At a minimum each profile must set the name attribute, which is
    how the profile will appear in the dropdown list.
    
    This class (BaseProfile) will _not_ appear as one of the choices.
    Think of it as an abstract class, if Python 2.5 had such a thing.
    '''

    # this will be set to the plugin instance at runtime
    plugin = None

    def __init__(self, plugin):
        '''plugin is required so that the profiles can save their settings'''
        self.plugin = plugin
        self.toolbar = None
        self.include = False
        self.exclude = False
        self.include_tags = []
        self.exclude_tags = []

    def get_toolbar(self, parent):
        '''Returns a panel with toolbar controls to be shown for this profile'''
        if self.toolbar is None:
            self.toolbar = self.TagsPanel(parent)
        self.update()
        return self.toolbar
        
    def update(self):
        '''Refresh the GUI with values from the settings'''
        self.includeTags.SetValue(self.plugin.settings["include_tags"])
        self.excludeTags.SetValue(self.plugin.settings["exclude_tags"])
        self.includecb.SetValue(bool(self.plugin.settings["apply_include_tags"]))
        self.excludecb.SetValue(bool(self.plugin.settings["apply_exclude_tags"]))

    def get_custom_args(self):
        '''Return a list of arguments unique to this profile'''
        args = []
        if self.plugin.settings["apply_include_tags"] and \
                len(self.plugin.settings["include_tags"].strip()) > 0:
            for include in self.plugin.settings["include_tags"].split(","):
                include = include.strip()
                if len(include) > 0:
                    args.append("--include=%s" % include)
        if self.plugin.settings["apply_exclude_tags"] and \
                len(self.plugin.settings["exclude_tags"].strip()) > 0:
            for exclude in self.plugin.settings["exclude_tags"].split(","):
                exclude = exclude.strip()
                if len(exclude) > 0:
                    args.append("--exclude=%s" % exclude)
        return args

    def get_command_prefix(self):
        '''Returns a command and any special arguments for this profile'''
        if os.name == "nt":
            return ["pybot.bat"]
        else:
            return ["pybot"]

    def TagsPanel(self, parent):
        '''Create a panel to input include/exclude tags'''
        panel = wx.Panel(parent, wx.ID_ANY)
        self.includecb = wx.CheckBox(panel, wx.ID_ANY, 
                                "Only run tests with these tags")
        self.excludecb = wx.CheckBox(panel, wx.ID_ANY, 
                                "Skip tests with these tags")
        self.includeTags = wx.TextCtrl(panel, wx.ID_ANY, size=(150,-1))
        self.excludeTags = wx.TextCtrl(panel, wx.ID_ANY, size=(150,-1))
        
        panel.Bind(wx.EVT_CHECKBOX, self.OnIncludeCheckbox, self.includecb)
        panel.Bind(wx.EVT_CHECKBOX, self.OnExcludeCheckbox, self.excludecb)
        panel.Bind(wx.EVT_TEXT, self.OnTagsChanged)

        panelsizer = wx.GridBagSizer(2,2)
        panelsizer.Add(self.includecb, (0,0), flag=wx.EXPAND)
        panelsizer.Add(self.excludecb, (0,1), flag=wx.EXPAND)
        panelsizer.Add(self.includeTags, (1,0), flag=wx.EXPAND)
        panelsizer.Add(self.excludeTags, (1,1), flag=wx.EXPAND)
        panelsizer.AddGrowableCol(0)
        panelsizer.AddGrowableCol(1)
        panel.SetSizerAndFit(panelsizer)

        return panel

    def set_setting(self, name, value):
        '''Sets a plugin setting'''
        self.plugin.settings[name] = value
        self.plugin.save_settings()
        
    def OnExcludeCheckbox(self, evt):
        '''Called when user clicks on exclude checkbox'''
        self.exclude = evt.IsChecked()
        self.set_setting("apply_exclude_tags", evt.IsChecked())

    def OnIncludeCheckbox(self, evt):
        '''Called when user clicks on include checkbox'''
        self.include = evt.IsChecked()
        self.set_setting("apply_include_tags", evt.IsChecked())

    def OnTagsChanged(self, evt):
        '''Called whenever the user modifies the list of tags'''
        # should probably look for commas and/or vertical bars and/or spaces?
        if evt.GetEventObject() == self.includeTags:
            value = self.includeTags.GetValue()
            self.set_setting("include_tags", value)
            include = [s.strip() for s in re.split("[,|]", value)]
            self.include_tags = filter(lambda x: len(x) > 0, include)
        else:
            value = self.excludeTags.GetValue()
            self.set_setting("exclude_tags", value)
            exclude = [s.strip() for s in re.split("[,|]", value)]
            self.exclude_tags = filter(lambda x: len(x) > 0, exclude)
