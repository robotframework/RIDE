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
import subprocess

from robotide.pluginapi import Plugin, ActionInfo, SeparatorInfo


class RunAnything(Plugin):

    def __init__(self, app):
        Plugin.__init__(self, app, default_settings={'configs': []})

    def enable(self):
        self.register_action(ActionInfo('Run', 'New Run Configuration',
                                        self.OnNewConfiguration))
        self.register_action(SeparatorInfo('Run'))
        self._configs = _RunConfigs(self.configs)
        for config in self._configs:
            self._add_config_to_menu(config)

    def OnNewConfiguration(self, event):
        dlg = _ConfigDialog()
        if dlg.ShowModal() == wx.ID_OK:
            config = self._configs.add(*dlg.get_value())
            self._add_config_to_menu(config)
            self.save_setting('configs', self._configs.data_to_save())

    def _add_config_to_menu(self, config):
        def _run(event):
            _Runner(_OutputWindow(self.notebook, config), config).run()
        info = ActionInfo('Run', name='%d: %s' % (config.index, config.name),
                          doc=config.help, action=_run) 
        self.register_action(info)


class _RunConfigs(object):

    def __init__(self, saved_data):
        self._configs = []
        for item in saved_data:
            self.add(item[0], item[1], item[2])

    def __iter__(self):
        return iter(self._configs)

    def add(self, name, doc, command):
        config = _RunConfig(name, doc, command, len(self._configs)+1)
        self._configs.append(config)
        return config

    def data_to_save(self):
        return [ (c.name, c.doc, c.command) for c in self._configs ]


class _RunConfig(object):
    help = property(lambda self: '%s (%s)' % (self.doc, self.command))

    def __init__(self, name, doc, command, index):
        self.name = name
        self.doc = doc
        self.command = command
        self.index = index

    def run(self):
        self._process = subprocess.Popen(self.command, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, shell=True)

    def finished(self):
        return self._process.poll() is not None

    def get_output(self):
        return self._process.stdout.read()


class _ConfigDialog(wx.Dialog):

    def __init__(self):
        wx.Dialog.__init__(self, wx.GetTopLevelWindows()[0],
                           title='New Run Configuration')
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._editors = []
        for label in ['Name', 'Documentation', 'Command']:
            self.Sizer.Add(self._get_entry_field(label))
        line = wx.StaticLine(self, size=(20,-1), style=wx.LI_HORIZONTAL)
        self.Sizer.Add(line, border=5,
                       flag=wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP)
        self.Sizer.Add(self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL),
                       flag=wx.ALIGN_CENTER|wx.ALL, border=5)
        self.Fit()

    def _get_entry_field(self, label):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, label=label, size=(100, -1)))
        editor = wx.TextCtrl(self, size=(200,-1))
        sizer.Add(editor)
        self._editors.append(editor)
        return sizer

    def get_value(self):
        return [ e.GetValue() for e in self._editors ]


class _Runner(wx.EvtHandler):

    def __init__(self, window, config):
        wx.EvtHandler.__init__(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self._timer = wx.Timer(self)
        self._window = window
        self._config = config

    def run(self):
        self._config.run()
        self._timer.Start(100)

    def OnTimer(self, event):
        if self._config.finished():
            self._timer.Stop()
            self._window.publish_result()


class _OutputWindow(wx.ScrolledWindow):

    def __init__(self, parent, config):
        wx.ScrolledWindow.__init__(self, parent)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.output = wx.StaticText(self)
        self.Sizer.Add(self.output)
        parent.add_tab(self, '%s (running)' % config.name)
        parent.show_tab(self)
        self._config = config

    def publish_result(self):
        self.output.SetLabel(self._config.get_output())
        self.Parent.rename_tab(self, '%s (finished)' % self._config.name)
