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

from ..controller.basecontroller import _BaseController
from ..pluginapi import Plugin
from ..action import ActionInfo, SeparatorInfo
from ..run.configmanagerui import ConfigManagerDialog
from ..run.ui import Runner

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class RunAnything(Plugin):
    __doc__ = _("""A plugin for executing commands on the system.

    This plugin enables creation of persistent run configurations and
    execution of those. Output of the executed command is displayed in a
    separate tab.""")

    def __init__(self, app):
        Plugin.__init__(self, app, default_settings={'configs': []})
        self._configs = RunConfigs(self.configs)
        self.runner = None

    def enable(self):
        self._create_menu(self._configs)

    def on_manage_configurations(self, event):
        dlg = ConfigManagerDialog(self._configs, self)
        if dlg.ShowModal() == wx.ID_OK:
            self._configs.update(dlg.get_data())
            self.save_setting('configs', self._configs.data_to_save())
            self._create_menu(self._configs)
        self._configs = RunConfigs(self.configs)
        dlg.Destroy()

    def _create_menu(self, configs):
        self.unregister_actions()
        self.register_action(ActionInfo(_('Macros'), _('Manage Run Configurations'),
                                        self.on_manage_configurations))
        self.register_action(SeparatorInfo(_('Macros')))
        for index, cfg in enumerate(configs):
            self._add_config_to_menu(cfg, index+1)

    def _add_config_to_menu(self, config, index):
        def run(event):
            self.runner = Runner(config, self.notebook)
            self.runner.run()
        info = ActionInfo(_('Macros'), name='%d: %s' % (index, config.name),
                          doc=config.help, action=run)
        self.register_action(info)
        # self.register_shortcut('CtrlCmd-C', lambda e: self.runner.output_panel.Copy())


class RunConfigs(_BaseController):

    def __init__(self, saved_data):
        self._configs = []
        for item in saved_data:
            self.add(item[0], item[1], item[2])

    def __iter__(self):
        return iter(self._configs)

    def __len__(self):
        return len(self._configs)

    def __getitem__(self, index):
        return self._configs[index]

    def add(self, name, command, doc):
        config = RunConfig(name, command, doc)
        self._configs.append(config)
        return config

    def update(self, data):
        for index, datum in enumerate(data):
            self.edit(index, *datum)

    def move_up(self, index):
        self._swap(index-1, index)

    def move_down(self, index):
        self._swap(index, index+1)

    def _swap(self, index1, index2):
        self._configs[index1], self._configs[index2] = self._configs[index2], self._configs[index1]

    def edit(self, index, name, command, doc):
        config = self._configs[index]
        config.name, config.command, config.doc = name, command, doc

    def delete(self, index):
        if index < len(self._configs):
            self._configs.pop(index)

    def data_to_save(self):
        return [ (c.name, c.command, c.doc) for c in self._configs ]


class RunConfig(object):
    help = property(lambda self: '%s (%s)' % (self.doc, self.command))

    def __init__(self, name, command, doc):
        self.name = name
        self.command = command
        self.doc = doc
        self._finished = False
        self._error = False

