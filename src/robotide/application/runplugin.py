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

import os
import subprocess
import tempfile
import wx
from wx.lib.mixins.listctrl import TextEditMixin

from robotide.pluginapi import Plugin, ActionInfo, SeparatorInfo
from robotide.editor.listeditor import ListEditor, AutoWidthColumnList


class RunAnything(Plugin):

    def __init__(self, app):
        Plugin.__init__(self, app, default_settings={'configs': []})

    def enable(self):
        self._create_menu(_RunConfigs(self.configs))

    def OnManageConfigurations(self, event):
        dlg = _ManageConfigsDialog(_RunConfigs(self.configs))
        if dlg.ShowModal() == wx.ID_OK:
            configs = _RunConfigs(dlg.get_data())
            self.save_setting('configs', configs.data_to_save())
            self._create_menu(configs)
        dlg.Destroy()

    def _create_menu(self, configs):
        self.unregister_actions()
        self.register_action(ActionInfo('Run', 'Manage Run Configurations',
                                        self.OnManageConfigurations))
        self.register_action(SeparatorInfo('Run'))
        for index, cfg in enumerate(configs):
            self._add_config_to_menu(cfg, index+1)

    def _add_config_to_menu(self, config, index):
        def run(event):
            _Runner(_OutputWindow(self.notebook, config.name), config).run()
        info = ActionInfo('Run', name='%d: %s' % (index, config.name),
                          doc=config.help, action=run) 
        self.register_action(info)


class _RunConfigs(object):

    def __init__(self, saved_data):
        self._configs = []
        for item in saved_data:
            self.add(item[0], item[1], item[2])

    def __iter__(self):
        return iter(self._configs)

    def __len__(self):
        return len(self._configs)

    def add(self, name, command, doc):
        config = _RunConfig(name, command, doc)
        self._configs.append(config)
        return config

    def swap(self, index1, index2):
        self._configs[index1], self._configs[index2] = \
                self._configs[index2], self._configs[index1]

    def pop(self, index):
        self._configs.pop(index)

    def data_to_save(self):
        return [ (c.name, c.command, c.doc) for c in self._configs ]


class _RunConfig(object):
    help = property(lambda self: '%s (%s)' % (self.doc, self.command))

    def __init__(self, name, command, doc):
        self.name = name
        self.command = command
        self.doc = doc

    def run(self, output):
        # TODO: check subprocess usage in Windows
        self._process = subprocess.Popen(self.command, stdout=output,
                                         stderr=subprocess.STDOUT, shell=True)

    def finished(self):
        return self._process.poll() is not None


class _ManageConfigsDialog(wx.Dialog):

    def __init__(self, configs):
        wx.Dialog.__init__(self, wx.GetTopLevelWindows()[0],
                           title='Manage Run Configurations')
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._editor = _ConfigListEditor(self, configs)
        self.Sizer.Add(self._editor, flag=wx.GROW, proportion=1)
        line = wx.StaticLine(self, size=(20,-1), style=wx.LI_HORIZONTAL)
        self.Sizer.Add(line, border=5,
                       flag=wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP)
        buttons = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        self.Bind(wx.EVT_BUTTON, self.OnOk, buttons.GetAffirmativeButton())
        self.Sizer.Add(buttons, flag=wx.ALIGN_CENTER|wx.ALL, border=5)
        self.SetSize((750, 200))

    def OnOk(self, event):
        event.Skip()

    def get_data(self):
        return self._editor.get_data()


class _ConfigListEditor(ListEditor):
    _buttons = ['New']
    _columns = ['Name', 'Command', 'Documentation']

    def __init__(self, parent, configs):
        ListEditor.__init__(self, parent, self._columns, configs)

    def _create_list(self, columns, data):
        return _TextEditListCtrl(self, columns, data, self._new_config)

    def get_column_values(self, config):
        return config.name, config.command, config.doc

    def get_data(self):
        return self._list.get_data()

    def OnEdit(self, event):
        self._list.open_editor(self._selection)

    def OnNew(self, event):
        self._list.new_item()

    def _new_config(self, data):
        print data
        self._data.add(*data)


class _TextEditListCtrl(AutoWidthColumnList, TextEditMixin):
    last_index = property(lambda self: self.ItemCount-1)

    def __init__(self, parent, columns, data, new_item_callback):
        AutoWidthColumnList.__init__(self, parent, columns, data)
        TextEditMixin.__init__(self)
        self.col_locs = self._calculate_col_locs()
        self._new_item_callback = new_item_callback
        self._new_item_creation = False

    def _calculate_col_locs(self):
        """Calculates and returns initial locations of colums.
        
        This is needed so that TextEditMixin can work from context menu,
        without selecting the row first.
        """
        locations = [0]
        loc = 0
        for n in range(self.GetColumnCount()):
            loc = loc + self.GetColumnWidth(n)
            locations.append(loc)
        return locations

    def open_editor(self, row):
        self.OpenEditor(0, row)

    def new_item(self):
        self._new_item_creation = True
        self.InsertStringItem(self.ItemCount, '')
        self.open_editor(self.last_index)

    def get_data(self):
        return [ self._get_row(row) for row in range(self.ItemCount) ]

    def _get_row(self, row):
        return [ self.GetItem(row, col).GetText() for col in range(3)]

    def CloseEditor(self, event=None):
        TextEditMixin.CloseEditor(self, event)
        # It seems that this is called twice per editing action and in the
        # first time the value may be empty. 
        # End new item creation only when there really is a value
        lastrow = self._get_row(self.last_index)
        if self._new_item_creation and any(lastrow):
            self._new_item_creation = False
            self._new_item_callback(lastrow)


class _Runner(wx.EvtHandler):

    def __init__(self, window, config):
        wx.EvtHandler.__init__(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self._timer = wx.Timer(self)
        self._window = window
        self._config = config

    def run(self):
        self._out_fd, self._out_path \
                      = tempfile.mkstemp(prefix='riderun_', text=True)
        self._out_file = open(self._out_path)
        self._config.run(self._out_fd)
        self._timer.Start(500)

    def OnTimer(self, event):
        finished = self._config.finished()
        self._window.update_output(self._out_file.read(), finished)
        if finished:
            self._timer.Stop()
            self._out_file.close()
            os.close(self._out_fd)
            os.remove(self._out_path)


class _OutputWindow(wx.ScrolledWindow):

    def __init__(self, parent, name):
        wx.ScrolledWindow.__init__(self, parent)
        self.SetScrollRate(10, 10)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self._output = wx.StaticText(self)
        self.Sizer.Add(self._output)
        self._name = name
        parent.add_tab(self, '%s (running)' % name)
        parent.show_tab(self)

    def update_output(self, output, finished=False):
        if output:
            self._output.SetLabel(self._output.GetLabel() + output)
            self.SetVirtualSize(self._output.Size)
        if finished:
            self.Parent.rename_tab(self, '%s (finished)' % self._name)
