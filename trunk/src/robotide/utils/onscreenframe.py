# This code is copied from http://wiki.wxpython.org/EnsureFrameIsOnScreen,
# and adapted to fit our code style. 

import wx


class OnScreenEnsuringFrame(object):

    def ensure_on_screen(self):
        try:
            display_id = wx.Display.GetFromWindow(self)
        except NotImplementedError:
            display_id = 0
        if display_id == -1:
            display_id = 0
        geometry = wx.Display(display_id).GetGeometry()
        position = self.GetPosition()
        if position.x < geometry.x:
            position.x = geometry.x
        if position.y < geometry.y:
            position.y = geometry.y
        size = self.GetSize()
        if size.width > geometry.width:
            size.width = geometry.width
            position.x = geometry.x
        elif position.x + size.width > geometry.x + geometry.width:
            position.x = geometry.x + geometry.width - size.width
        if size.height > geometry.height:
            size.height = geometry.height
            position.y = geometry.y
        elif position.y + size.height > geometry.y + geometry.height:
            position.y = geometry.y + geometry.height - size.height
        self.SetPosition(position)
        self.SetSize(size)
