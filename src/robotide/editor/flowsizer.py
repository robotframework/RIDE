#-------------------------------------------------------------------------------
#  Class: FlowSizer
#  Defines a horizontal or vertical flow layout sizer for wxPython
#  Written by: David C. Morrill
#  Date: 01/12/2006
#  (c) Copyright 2006 by Enthought, Inc.
#  License: BSD Style.
#-------------------------------------------------------------------------------
import wx

class HorizontalFlowSizer(wx.PySizer):
    """
    A sizer which lays out component left to right top to bottom. Java uses
    these quite heavily
    """
    _DEFAUL_WIDTH = 100

    def __init__(self):
        '''
        Initializes the object:
        '''
        wx.PySizer.__init__(self)
        self._frozen       = False
        self._needed_size  = None
        self._height = 20

    def CalcMin(self):
        """
        Calculates the minimum size needed by the sizer.
        """
        return wx.Size(0, 0)

    def RecalcSizes(self):
        """
        Layout the contents of the sizer based on the sizer's current size
        and position.
        """
        x0, y0 = self.GetPosition()
        dx, dy = self.GetSize()
        if dx == 0:
            dx = HorizontalFlowSizer._DEFAUL_WIDTH
        else:
            HorizontalFlowSizer._DEFAUL_WIDTH = dx
        x_border = x0 + dx
        y_border = y0 + dy
        x, y = x0, y0
        mdy = sdy = 0
        visible = True
        cur_max = 0
        for item in self.GetChildren():
            idx, idy = item.CalcMin()
            expand  = item.GetFlag() & wx.EXPAND
            if (x > x0) and ((x + idx) > x_border):
                x   = x0
                y  += (mdy + sdy)
                mdy = sdy = 0
                visible &= (y < y_border)
            cur_max = max(idy, cur_max)
            if expand:
                idy = cur_max
            if item.IsSpacer():
                sdy = max(sdy, idy)
                if x == x0:
                    idx = 0
            item.SetDimension(wx.Point(x, y), wx.Size(idx, idy))
            item.Show(visible)
            x += idx
            mdy = max(mdy, idy)
        self._height = y + mdy + sdy - y0

    @property
    def height(self):
        return self._height