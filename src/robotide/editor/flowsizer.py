#-------------------------------------------------------------------------------
#  Class: FlowSizer
#  Defines a horizontal or vertical flow layout sizer for wxPython
#  Written by: David C. Morrill
#  Date: 01/12/2006
#  (c) Copyright 2006 by Enthought, Inc.
#  License: BSD Style.
#-------------------------------------------------------------------------------
import wx

class FlowSizer(wx.PySizer):
    """
    A sizer which lays out component left to right top to bottom. Java uses
    these quite heavily
    """

    def __init__(self, orient = wx.HORIZONTAL):
        '''
        Initializes the object:
        '''
        super(FlowSizer, self).__init__()
        self._orient       = orient
        self._frozen       = False
        self._needed_size  = None
        self.height = 0

    def CalcMin(self):
        """
        Calculates the minimum size needed by the sizer.
        """
        if self._needed_size is not None:
            return self._needed_size
        horizontal  = (self._orient == wx.HORIZONTAL)
        dx = dy = i = 0
        while True:
            try:
                item = self.GetItem(i)
                if item is None:
                    break
                i += 1
            except:
                break
            idx, idy = item.CalcMin()
            if horizontal:
                dy = max(dy, idy)
            else:
                dx = max(dx, idx)
        return wx.Size(dx, dy)

    def RecalcSizes(self):
        """
        Layout the contents of the sizer based on the sizer's current size
        and position.
        """
        horizontal = (self._orient == wx.HORIZONTAL)
        x,   y     = self.GetPosition()
        dx, dy     = self.GetSize()
        x0, y0     = x, y
        ex         = x + dx
        ey         = y + dy
        mdx = mdy  = sdx = sdy = 0
        visible = True
        cur_max = 0
        for item in self.GetChildren():
            idx, idy  = item.CalcMin()
            expand    = item.GetFlag() & wx.EXPAND
            if horizontal:
                if (x > x0) and ((x + idx) > ex):
                    x   = x0
                    y  += (mdy + sdy)
                    mdy = sdy = 0
                    if y >= ey:
                        visible = False
                cur_max = max(idy, cur_max)
                if expand:
                    idy = cur_max
                if item.IsSpacer():
                    sdy = max(sdy, idy)
                    if x == x0:
                        idx = 0
                item.SetDimension(wx.Point(x, y), wx.Size(idx, idy))
                item.Show(visible)
                x  += idx
                mdy = max(mdy, idy)
                self.height = y+idy
            else:
                if (y > y0) and ((y + idy) > ey):
                    y   = y0
                    x  += (mdx + sdx)
                    mdx = sdx = 0
                    if x >= ex:
                        visible = False
                cur_max = max(idx, cur_max)
                if expand:
                    idx = cur_max
                if item.IsSpacer():
                    sdx = max(sdx, idx)
                    if y == y0:
                        idy = 0
                item.SetDimension(wx.Point(x, y), wx.Size(idx, idy))
                item.Show(visible)
                y  += idy
                mdx = max(mdx, idx)
        if (not visible) and (self._needed_size is None):
            max_dx = max_dy = 0
            if horizontal:
                max_dy = max(dy, y + mdy + sdy - y0)
            else:
                max_dx = max(dx, x + mdx + sdx - x0)
            self._needed_size = wx.Size(max_dx, max_dy)
            if not self._frozen:
                self._do_parent('_freeze')
            do_later(self._do_parent, '_thaw')
        else:
            self._needed_size = None

    def _freeze(self, window):
        """
        Prevents the specified window from doing any further screen updates.
        """
        window.Freeze()
        self._frozen = True

    def _thaw(self, window):
        """
        Lays out a specified window and then allows it to be updated again.
        """
        window.Layout()
        window.Refresh()
        if self._frozen:
            self._frozen = False
            window.Thaw()

    def _do_parent(self, method):
        """
        Does a specified operation on the sizer's parent window.
        """
        i = 0
        while True:
            try:
                item = self.GetItem(i)
                if item is None:
                    break
                i += 1
            except:
                return
            if item.IsWindow():
                getattr(self, method)(item.GetWindow().GetParent())
                return

#-------------------------------------------------------------------------------
#  Author: David C. Morrill
#  Date: 05/18/2005
#  (c) Copyright 2005 by Enthought, Inc.
#  License: BSD Style.
#-------------------------------------------------------------------------------
class DoLaterTimer(wx.Timer):
    """
    Provides a simple function for scheduling some code to run at some time in
    the future.
    """
    # List of currently active timers:
    active_timers = []
    def __init__(self, interval, callable, args, kw_args):
        """
        Initializes the object:
        """
        global active_timers
        wx.Timer.__init__(self)
        for timer in self.active_timers:
            if ((timer.callable == callable) and
                (timer.args     == args)     and
                (timer.kw_args  == kw_args)):
                timer.Start(interval, True)
                return
        self.active_timers.append(self)
        self.callable = callable
        self.args     = args
        self.kw_args  = kw_args
        self.Start(interval, True)

    def Notify(self):
        """
        Handles the timer pop event:
        """
        global active_timers
        self.active_timers.remove(self)
        self.callable(*self.args, **self.kw_args)

def do_later(callable, *args, **kw_args):
    """
    Does something 50 milliseconds from now.
    """
    DoLaterTimer(50, callable, args, kw_args)

def do_after(interval, callable, *args, **kw_args):
    """
    Does something after some specified time interval.
    """
    DoLaterTimer(interval, callable, args, kw_args)
