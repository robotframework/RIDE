from wx.lib import wordwrap
import wx.grid


class CellRenderer(wx.grid.GridCellRenderer):
    """
    GridCellAutoWrapStringRenderer()

    This class may be used to format string data in a cell.
    """

    def __init__(self, default_width, max_width, auto_fit):
        wx.grid.GridCellRenderer.__init__(self)
        self.default_width = default_width
        self.max_width = max_width
        self.auto_fit = auto_fit

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        text = wordwrap.wordwrap(text, grid.GetColSize(col), dc, breakLongWords=False)
        hAlign, vAlign = attr.GetAlignment()
        if isSelected:
            bg = grid.GetSelectionBackground()
            fg = grid.GetSelectionForeground()
        else:
            bg = attr.GetBackgroundColour()
            fg = attr.GetTextColour()
        dc.SetTextBackground(bg)
        dc.SetTextForeground(fg)
        dc.SetBrush(wx.Brush(bg, wx.SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)
        grid.DrawTextRectangle(dc, text, rect, hAlign, vAlign)

    def GetBestSize(self, grid, attr, dc, row, col):
        """The width will be between values `col size` and `max col size`
        These can be changed in user preferences.
        """

        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())

        col_width = grid.GetColSize(col)
        margin = 0

        if self.auto_fit:
            if col_width < self.max_width:
                col_width = self.max_width
                margin = 2  # get border width into account when submitting optimal col size

        text = wordwrap.wordwrap(text, col_width, dc, breakLongWords=False, margin=margin)
        w, h = dc.GetMultiLineTextExtent(text)

        if self.auto_fit:
            w = w if w >= self.default_width else self.default_width

        return wx.Size(w, h)

    def Clone(self):  # real signature unknown; restored from __doc__
        """ Clone(self) -> GridCellRenderer """
        return CellRenderer
