import wx
import subprocess
from StringIO import StringIO

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
        info = ActionInfo('Run', name='%d: %s' % (config.index, config.name),
                          doc=config.help, action=lambda event: config.run())
        self.register_action(info)


class _RunConfigs(object):

    def __init__(self, saved_data):
        self._configs = []
        for item in saved_data:
            self.add(item[0], item[1], item[2])

    def __iter__(self):
        for index, config in enumerate(self._configs):
            config.index = index+1
            yield config

    def add(self, name, doc, command):
        config = _RunConfig(name, doc, command, len(self._configs)+1)
        self._configs.append(config)
        return config

    def data_to_save(self):
        return [ (c.name, c.doc, c.command) for c in self._configs ]


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


class _RunConfig(object):
    help = property(lambda self: '%s (%s)' % (self.doc, self.command))

    def __init__(self, name, doc, command, index):
        self.name = name
        self.doc = doc
        self.command = command
        self.index = index

    def run(self):
        # TODO: check subprocess usage, also in Windows
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, shell=True)
        output = process.communicate()[0]
        return output
