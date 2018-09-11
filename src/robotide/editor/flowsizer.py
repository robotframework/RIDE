#-------------------------------------------------------------------------------
#  Class: FlowSizer
#  Defines a horizontal or vertical flow layout sizer for wxPython
#  Written by: David C. Morrill
#  Date: 01/12/2006
#  (c) Copyright 2006 by Enthought, Inc.
#  License: BSD Style.
#-------------------------------------------------------------------------------

# This code has been modified after inclusion and is no longer generic.
# You should probably not use this in your own projects.

import wx

if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
    from wx import Sizer  # wxPhoenix
else:
    from wx import PySizer as Sizer


class HorizontalFlowSizer(Sizer):
    """
    A sizer which lays out component left to right top to bottom. Java uses
    these quite heavily
    """
    _DEFAUL_WIDTH = 200

    def __init__(self):
        '''
        Initializes the object:
        '''
        Sizer.__init__(self)
        self._frozen       = False
        self._needed_size  = None
        self._height = 0

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
        dy = self._height or dy
        if self._is_error_width(dx):
            dx = HorizontalFlowSizer._DEFAUL_WIDTH
        else:
            HorizontalFlowSizer._DEFAUL_WIDTH = dx
        x_border = x0 + dx
        x, y = x0, y0
        mdy = sdy = 0
        cur_max = 0
        for item in self.GetChildren():
            idx, idy = item.CalcMin()
            expand  = item.GetFlag() & wx.EXPAND
            if (x > x0) and ((x + idx) > x_border):
                x   = x0
                y  += (mdy + sdy)
                mdy = sdy = 0
            cur_max = max(idy, cur_max)
            if expand:
                idy = cur_max
            if item.IsSpacer():
                sdy = max(sdy, idy)
                if x == x0:
                    idx = 0
            item.SetDimension(wx.Point(x, y), wx.Size(idx, idy))
            item.Show(True)
            x += idx
            mdy = max(mdy, idy)
        newheight = y + mdy + sdy - y0
        if newheight != self._height:
            self._height = newheight
            # Enforce that the parent window recalculates needed height
            self._send_resize_event()

    def _send_resize_event(self):
        frame = self.GetContainingWindow().GetTopLevelParent()
        frame.ProcessEvent(wx.SizeEvent(frame.Size, frame.Id))

    def _is_error_width(self, dx):
        # It seems that there are several widths that notify that the width
        # calculation was unsuccessful. The erroneous widths are:
        # 94 in windows xp
        # 100 in windows 7
        # 0 everywhere
        return dx in [0, 94, 100]

    @property
    def height(self):
        return self._height
