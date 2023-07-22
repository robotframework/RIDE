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

    @staticmethod
    def _wordwrap(text, width, dc, break_long_words=True, margin=0):
        """ modification of original wordwrap function without extra space """
        wrapped_lines = []
        text = text.split('\n')
        for line in text:
            pte = dc.GetPartialTextExtents(line)
            wid = (width - (2 * margin + 1) * dc.GetTextExtent(' ')[0])
            idx = 0
            start = 0
            start_idx = 0
            spc_idx = -1
            while idx < len(line):
                # remember the last seen space
                if line[idx] == ' ':
                    spc_idx = idx

                # have we reached the max width?
                if pte[idx] - start > wid and (spc_idx != -1 or break_long_words):
                    if spc_idx != -1:
                        idx = min(spc_idx + 1, len(pte) - 1)
                    wrapped_lines.append(' ' * margin + line[start_idx: idx] + ' ' * margin)
                    start = pte[idx]
                    start_idx = idx
                    spc_idx = -1

                idx += 1

            wrapped_lines.append(' ' * margin + line[start_idx: idx] + ' ' * margin)

        return '\n'.join(wrapped_lines)

    def Draw(self, grid, attr, dc, rect, row, col, is_selected):
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        suggest_width = grid.GetColSize(col)
        text = self._wordwrap(text, suggest_width, dc, break_long_words=False)
        h_align, v_align = attr.GetAlignment()
        if is_selected:
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
        grid.DrawTextRectangle(dc, text, rect, h_align, v_align)

    def GetBestSize(self, grid, attr, dc, row, col):
        """The width will be between values `col size` and `max col size`
        These can be changed in user preferences.
        """
        text = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())

        w, h = dc.GetTextExtent('00')  # use 2 digits for size reference
        if self.auto_fit:
            grid.SetRowMinimalAcceptableHeight(int(h+h/2))
            grid.SetColMinimalAcceptableWidth(int(w+w/2))

        w, h = dc.GetTextExtent(text)
        if self.auto_fit:
            col_width = min(w, self.max_width)
        else:
            col_width = min(w, self.default_width)

        if self.word_wrap:
            suggest_width = max(grid.GetColSize(col), col_width)
            text = self._wordwrap(text, suggest_width, dc, break_long_words=False)
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
