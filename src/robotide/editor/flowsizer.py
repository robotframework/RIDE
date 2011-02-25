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

    def _do_parent(self, func):
        """
        Does a specified operation on the sizer's parent window.
        """
        for item in self.GetChildren():
            if item.IsWindow():
                func(item.GetWindow().GetParent())
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
