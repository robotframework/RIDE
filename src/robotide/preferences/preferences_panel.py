'''Base class for all preferences panels'''
import wx

class PreferencesPanel(wx.Panel):
    '''Base class for all preference panels used by PreferencesDialog'''
    location = ("Preferences",)
    title = "Preferences"

    def __init__(self, parent=None, *args, **kwargs):
        self.tree_item = None
        wx.Panel.__init__(self, parent, *args, **kwargs)

    def GetTitle(self):
        location = getattr(self, "location", ("Preferences",))
        title = getattr(self, "title", self.location[-1])
        return title

    def Separator(self, parent, title):
        '''Creates a simple horizontal separator with title'''
        container = wx.Panel(parent, wx.ID_ANY)
        label = wx.StaticText(container, wx.ID_ANY, label=title)
        sep = wx.StaticLine(container, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label, 0, wx.EXPAND|wx.TOP, 8)
        sizer.Add(sep, 0, wx.EXPAND|wx.TOP|wx.BOTTOM, 2)
        container.SetSizerAndFit(sizer)
        return container

# these are standard widgets that are tied to a specific
# setting; when the widget is changed the setting is
# automaticaly saved
class PreferencesComboBox(wx.ComboBox):
    '''A combobox tied to a specific setting'''
    def __init__(self, parent, id, settings, key, choices):
        self.settings = settings
        self.key = key
        value = settings[key]
        super(PreferencesComboBox, self).__init__(parent, id, value,
                                                  choices=choices)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelect)

    def OnSelect(self, event):
        value = str(event.GetEventObject().GetValue())
        self.settings[self.key] = value
        self.settings.save()


class PreferencesColorPicker(wx.ColourPickerCtrl):
    '''A colored button that opens a color picker dialog'''
    def __init__(self, parent, id, settings, key):
        self.settings = settings
        self.key = key
        value = settings[key]
        super(PreferencesColorPicker, self).__init__(parent, id, col=value)
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.OnPickColor)

    def OnPickColor(self, event):
        '''Set the color for the given key to the color of the widget'''
        color = event.GetColour()
        rgb = "#%02X%02X%02X" % color.asTuple()
        self.settings[self.key] = rgb
        self.settings.save()
