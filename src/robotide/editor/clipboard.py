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
import pickle


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
        return self._grid.active_coords.topleft

    def _write_cell(self, row, col, value):
        self._grid.write_cell(row, col, value)

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


ClipboardHandler = os.name == 'nt' and _WindowsClipboardHandler or _ClipboardHandler


class _GridClipboard(object):
    """Implements a "smart" clipboard. String objects are saved as usual, but
    other python objects can be saved as well. The primary purpose is to place
    a list of grid rows on the clipboard.
    """

    def set_contents(self, data):
        if not data:
            return
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(self._get_data_object(data))
        wx.TheClipboard.Close()

    def _get_data_object(self, data):
        if os.name == 'nt' and  self._is_single_cell_data(data):

            do = wx.TextDataObject()
            do.SetText(data[0][0])
        else:
            do = _PythonDataObject()
            do.SetData(pickle.dumps(data))
        return do

    def _is_single_cell_data(self, clipboard):
        return len(clipboard) == 1 and len(clipboard[0]) == 1

    def get_contents(self):
        """Gets contents of the clipboard, returning a python object if
        possible, otherwise returns plain text or None if the clipboard is
        empty.
        """
        wx.TheClipboard.Open()
        try:
            return self._get_value()
        finally:
            wx.TheClipboard.Close()

    def _get_value(self):
        try:
            do = _PythonDataObject()
            wx.TheClipboard.GetData(do)
            return pickle.loads(do.GetDataHere())
        except TypeError:
            try:
                do = wx.TextDataObject()
                wx.TheClipboard.GetData(do)
                # For some reason, when getting string contents from the 
                # clipboard on Windows '\x00' is inserted between each char.
                # WTF?!?!?!?
                data =  do.GetDataHere()
                if data:
                    return data.replace('\x00', '')
            except TypeError:
                pass
        return None


class _PythonDataObject(wx.PyDataObjectSimple):

    def __init__(self):
        wx.PyDataObjectSimple.__init__(self, wx.CustomDataFormat('PythonDataObject'))
        self.data = None

    def GetDataSize(self):
        return len(self.data)

    def GetDataHere(self):
        return self.data

    def SetData(self, data):
        self.data = data
        return True
