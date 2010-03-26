#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

import os
import wx

from robotide import utils


class _ClipboardHandler(object):

    def __init__(self, grid):
        self._grid = grid
        self._clipboard = _GridClipboard()

    def copy(self):
        """Copy the contents of the selected cell(s). This does a normal copy
        action if the user is editing a cell, otherwise it places the selected
        range of cells on the data.
        """
        self._add_selected_data_to_clipboard()

    def cut(self):
        """Cuts the contents of the selected cell(s). This does a normal cut
        action if the user is editing a cell, otherwise it places the selected
        range of cells on the clipboard.
        """
        self._add_selected_data_to_clipboard()

    def _add_selected_data_to_clipboard(self):
        self._clipboard.set_contents(self._grid.get_selected_content())

    def paste(self):
        """Paste the contents of the clipboard. If a cell is being edited just
        do a normal paste. If a cell is not being edited, paste whole rows.
        """
        if self._edit_control_shown():
            self._paste_to_cell_editor()
        else:
            self._paste_to_grid()

    def _paste_to_cell_editor(self):
        clipboard = self._clipboard.get_contents()
        if isinstance(clipboard, list):
            cells_as_text = ' '.join([' '.join(row) for row in clipboard])
            self._get_edit_control().WriteText(cells_as_text)

    def _paste_to_grid(self):
        clipboard = self._clipboard.get_contents()
        if not clipboard:
            return
        cell = self._get_starting_cell()
        if not isinstance(clipboard, list):
            self._write_cell(cell.row, cell.col, clipboard)
        else:
            row = cell.row
            for datarow in clipboard:
                col = cell.col
                for value in datarow:
                    self._write_cell(row, col, value)
                    col += 1
                row += 1

    def _get_starting_cell(self):
        return self._grid.selection.topleft

    def _write_cell(self, row, col, value):
        self._grid.write_cell(row, col, value, update_history=False)

    def _get_edit_control(self):
        return self._grid.get_cell_edit_control()

    def _edit_control_shown(self):
        return self._grid.IsCellEditControlShown()


class _WindowsClipboardHandler(_ClipboardHandler):

    def copy(self):
        if self._edit_control_shown():
            self._get_edit_control().Copy()
        else:
            _ClipboardHandler.copy(self)

    def cut(self):
        if self._edit_control_shown():
            self._get_edit_control().Cut()
        else:
            _ClipboardHandler.copy(self)

    def _paste_to_cell_editor(self):
        self._get_edit_control().Paste()


ClipboardHandler = utils.is_windows and _WindowsClipboardHandler\
                                    or _ClipboardHandler


class _GridClipboard(object):
    """Implements a "smart" clipboard."""

    def set_contents(self, data):
        """Insert `data` to the system clipboard

        `data` may be either a string or list of lists representing rows of
        grid data. Other data is ignored
        """
        data = self._format_data(data)
        if not data:
            return
        dataobject = wx.TextDataObject()
        dataobject.SetText(data)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(dataobject)
        wx.TheClipboard.Close()

    def _format_data(self, data):
        if isinstance(data, list):
            return os.linesep.join('\t'.join(row) for row in data)
        if isinstance(data, basestring):
            return data
        return None

    def get_contents(self):
        """Gets contents of the clipboard.

        Returns either a string or a list of rows to be pasted into clipboard.
        """
        return self._split_string_from_tabs_and_newlines(self._get_contents())

    def _get_contents(self):
        wx.TheClipboard.Open()
        try:
            return self._get_value_from_clipboard()
        finally:
            wx.TheClipboard.Close()

    def _get_value_from_clipboard(self):
        # TODO: This method can be inlined with the previous, when
        # try-except-finally works.
        try:
            do = wx.TextDataObject()
            wx.TheClipboard.GetData(do)
            data =  do.GetDataHere()
        except TypeError:
            return ''
        # For some reason, when getting string contents from the
        # clipboard on Windows '\x00' is inserted between each char.
        # WTF?!?!?!?
        return data and data.replace('\x00', '') or ''

    def _split_string_from_tabs_and_newlines(self, string):
        return [ line.split('\t') for line in string.splitlines()]
