import wx
from robotide.preferences import PreferencesPanel, PreferencesComboBox
from robotide.context import SETTINGS

class GeneralPreferences(PreferencesPanel):
    '''Preferences panel for general preferences'''
    location = ("General",)
    title = "General Preferences"
    def __init__(self, *args, **kwargs):
        super(GeneralPreferences, self).__init__(*args, **kwargs)
        
        sizer = wx.FlexGridSizer(rows=2, cols=2)
        label = wx.StaticText(self, wx.ID_ANY, "TXT format separator:")
        combo = PreferencesComboBox(self, wx.ID_ANY,
                                    SETTINGS,
                                    "txt format separator",
                                    choices=("pipe","space")
                                    )
        sizer.AddMany([(label,0,wx.LEFT, 10), (combo,)])
        self.SetSizer(sizer)

