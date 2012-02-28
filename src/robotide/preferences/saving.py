import wx
import textwrap

from robotide.preferences import PreferencesPanel, PreferencesComboBox
from robotide.context import SETTINGS
from robotide.widgets import HelpLabel


class SavingPreferences(PreferencesPanel):
    '''Preferences panel for general preferences'''
    location = ("Saving",)
    title = "Saving Preferences"
    def __init__(self, *args, **kwargs):
        super(SavingPreferences, self).__init__(*args, **kwargs)
        self.SetSizer(wx.FlexGridSizer(rows=4, cols=2))
        self._add_saving_preference('TXT format separator:',
                                    'txt format separator',
                                    ('pipe', 'space'),
                                    )
        help = 'Possible values are native (of current OS), CRLF (Windows) and LF (Unixy)'
        self._add_saving_preference('Line separator:',
                                    'line separator',
                                    ('native', 'CRLF', 'LF'),
                                    help)


    def _add_saving_preference(self, label, setting_name, choices, help=''):
        combo = PreferencesComboBox(self, wx.ID_ANY,
                                    SETTINGS,
                                    key=setting_name,
                                    choices=choices
                                    )
        label = wx.StaticText(self, wx.ID_ANY, label)
        self.Sizer.AddMany([label, (combo,)])
        help = '\n'.join(textwrap.wrap(help, 60))
        if help:
            self.Sizer.AddMany([HelpLabel(self, help), wx.Window(self)])
