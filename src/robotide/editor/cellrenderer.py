
#  Copyright 2019-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from wx.lib import wordwrap
import wx.grid


class CellRenderer(wx.grid.GridCellRenderer):
    """
    GridCellAutoWrapStringRenderer()

    This class may be used to format string data in a cell.
    """

    def __init__(self, default_width, max_width, auto_fit, word_wrap=True):
        wx.grid.GridCellRenderer.__init__(self)
        self.default_width = default_width
        self.max_width = max_width
        self.auto_fit = auto_fit
        self.word_wrap = word_wrap

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

        _font = attr.GetFont()
        dc.SetFont(_font)

        if len(text) == 0:
            return dc.GetTextExtent("__")  # self.default_width

        w, h = dc.GetTextExtent(text + "__")

        if self.word_wrap:
            if self.auto_fit:
                col_width = min(w, self.max_width)
                suggest_width = grid.GetColSize(col)
            else:
                col_width = self.default_width
                suggest_width = col_width
            text = wordwrap.wordwrap(text, suggest_width, dc, breakLongWords=False)
            w, h = dc.GetMultiLineTextExtent(text)
            row_height = h
        else:
            row_height = h
            if self.auto_fit:
                col_width = min(w, self.max_width)
            else:
                col_width = min(w, grid.GetColSize(col))

        return wx.Size(col_width, row_height)

    def Clone(self):  # real signature unknown; restored from __doc__
        """ Clone(self) -> GridCellRenderer """
        return CellRenderer
