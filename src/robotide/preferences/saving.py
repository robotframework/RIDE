import wx
from robotide.preferences import PreferencesPanel, PreferencesComboBox
from robotide.context import SETTINGS

class SavingPreferences(PreferencesPanel):
    '''Preferences panel for general preferences'''
    location = ("Saving",)
    title = "Saving Preferences"
    def __init__(self, *args, **kwargs):
        super(SavingPreferences, self).__init__(*args, **kwargs)

        sizer = wx.FlexGridSizer(rows=2, cols=2)
        label = wx.StaticText(self, wx.ID_ANY, "TXT format separator:")
        combo = PreferencesComboBox(self, wx.ID_ANY,
                                    SETTINGS,
                                    "txt format separator",
                                    choices=("pipe","space")
                                    )
        sizer.AddMany([(label,0,wx.LEFT, 10), (combo,)])
        self.SetSizer(sizer)

