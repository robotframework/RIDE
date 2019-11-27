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

    def _wordwrap(self, text, width, dc, breakLongWords=True, margin=0):
        ''' modification of original wordwrap function without extra space'''
        wrapped_lines = []
        text = text.split('\n')
        for line in text:
            pte = dc.GetPartialTextExtents(line)
            wid = (width - (2 * margin + 1) * dc.GetTextExtent(' ')[0])
            idx = 0
            start = 0
            startIdx = 0
            spcIdx = -1
            while idx < len(line):
                # remember the last seen space
                if line[idx] == ' ':
                    spcIdx = idx

                # have we reached the max width?
                if pte[idx] - start > wid and (spcIdx != -1 or breakLongWords):
                    if spcIdx != -1:
                        idx = min(spcIdx + 1, len(pte) - 1)
                    wrapped_lines.append(' ' * margin + line[startIdx: idx] + ' ' * margin)
                    start = pte[idx]
                    startIdx = idx
                    spcIdx = -1

                idx += 1

            wrapped_lines.append(' ' * margin + line[startIdx: idx] + ' ' * margin)

        return '\n'.join(wrapped_lines)

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        suggest_width = grid.GetColSize(col)
        text = self._wordwrap(text, suggest_width, dc, breakLongWords=False)
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

        w, h = dc.GetTextExtent('00')  # use 2 digits for size reference
        if self.auto_fit:
            grid.SetRowMinimalAcceptableHeight(h+h/2)
            grid.SetColMinimalAcceptableWidth(w+w/2)

        w, h = dc.GetTextExtent(text)
        if self.auto_fit:
            col_width = min(w, self.max_width)
        else:
            col_width = min(w, self.default_width)

        if self.word_wrap:
            suggest_width = max(grid.GetColSize(col), col_width)
            text = self._wordwrap(text, suggest_width, dc, breakLongWords=False)
            w, h = dc.GetMultiLineTextExtent(text)
            if self.auto_fit:
                col_width = min(w, col_width)
            else:
                col_width = min(w, self.default_width)
        row_height = h
        return wx.Size(col_width, row_height)

    def Clone(self):  # real signature unknown; restored from __doc__
        """ Clone(self) -> GridCellRenderer """
        return CellRenderer
