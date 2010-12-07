import wx


class VerticalSizer(wx.BoxSizer):

    def __init__(self):
        wx.BoxSizer.__init__(self, wx.VERTICAL)

    def add(self, component):
        self.Add(component)

    def add_with_padding(self, component, padding):
        self.Add(component, flag=wx.ALL, border=padding)

    def add_expanding(self, component):
        self.Add(component, 1, wx.EXPAND)
