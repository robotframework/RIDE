import wx


class _BoxSizer(wx.BoxSizer):

    def __init__(self):
        wx.BoxSizer.__init__(self, self.direction)

    def add(self, component):
        self.Add(component)

    def add_with_padding(self, component, padding):
        self.Add(component, flag=wx.ALL, border=padding)

    def add_expanding(self, component):
        self.Add(component, 1, wx.EXPAND)


class VerticalSizer(_BoxSizer):
    direction = wx.VERTICAL


class HorizontalSizer(_BoxSizer):
    direction = wx.HORIZONTAL

    def add_to_end(self, component):
        self.Add(component, flag=wx.ALIGN_RIGHT)

