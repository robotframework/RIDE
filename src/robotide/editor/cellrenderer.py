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
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())

        col_width = grid.GetColSize(col)
        margin = 0

        if self.auto_fit:
            if col_width < self.max_width:
                col_width = self.max_width
                margin = 2

        text = wordwrap.wordwrap(text, col_width, dc, breakLongWords=False, margin=margin)
        w, h = dc.GetMultiLineTextExtent(text)

        if self.auto_fit:
            w = w if w >= self.default_width else self.default_width

        return wx.Size(w, h)

    def Clone(self):  # real signature unknown; restored from __doc__
        """ Clone(self) -> GridCellRenderer """
        return CellRenderer


class GridEditorTest(wx.grid.Grid):
    def __init__(self, parent, log):
        wx.grid.Grid.__init__(self, parent, -1)
        self.log = log

        self.CreateGrid(10, 3)

        # Somebody changed the grid so the type registry takes precedence
        # over the default attribute set for editors and renderers, so we
        # have to set null handlers for the type registry before the
        # default editor will get used otherwise...
        #self.RegisterDataType(wx.GRID_VALUE_STRING, None, None)
        #self.SetDefaultEditor(MyCellEditor(self.log))

        # Or we could just do it like this:
        #self.RegisterDataType(wx.GRID_VALUE_STRING,
        #                      wx.GridCellStringRenderer(),
        #                      MyCellEditor(self.log))

        # but for this example, we'll just set the custom editor on one cell
        self.SetDefaultRenderer(CellRenderer(100, 150, True))
        self.SetCellValue(1, 0, "11")


        self.SetColSize(0, 150)
        self.SetColSize(1, 150)
        self.SetColSize(2, 75)


#---------------------------------------------------------------------------

class TestFrame(wx.Frame):
    def __init__(self, parent, log):
        wx.Frame.__init__(self, parent, -1, "Custom Grid Cell Editor Test",
                         size=(640,480))
        grid = GridEditorTest(self, log)

#---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    app = wx.App(False)
    frame = TestFrame(None, sys.stdout)
    frame.Show(True)
    app.MainLoop()