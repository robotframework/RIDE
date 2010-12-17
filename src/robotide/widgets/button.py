import wx


class ButtonWithHandler(wx.Button):

    def __init__(self, parent, label, handler=None, width=-1,
                 height=25):
        wx.Button.__init__(self, parent, label=label,
                           size=(width, height))
        if not handler:
            handler = getattr(parent, 'On'+label.replace(' ', ''))
        parent.Bind(wx.EVT_BUTTON, handler, self)
