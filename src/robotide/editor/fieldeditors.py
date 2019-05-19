#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

import wx
import wx.grid

from robotide.context import ctrl_or_cmd, bind_keys_to_evt_menu
from robotide.editor.contentassist import ContentAssistFileButton
from robotide.namespace.suggesters import SuggestionSource
from robotide.widgets import Label

from .contentassist import ContentAssistTextCtrl
from .gridbase import GridEditor


class ValueEditor(wx.Panel):
    expand_factor = 0
    _sizer_flags_for_editor = wx.ALL
    _sizer_flags_for_label = wx.ALL

    def __init__(self, parent, value, label=None, validator=None,
                 settings=None):
        wx.Panel.__init__(self, parent)
        self._label = label
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._create_editor(value, label, settings)
        if validator:
            self.set_validator(validator)
        self.SetSizer(self._sizer)

    def _create_editor(self, value, label, settings):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if self._label:
            sizer.Add(Label(self, label=self._label, size=(80, -1)), 0,
                      self._sizer_flags_for_label, 5)
        self._editor = self._get_text_ctrl()
        # self._editor.SetDefaultStyle(wx.TextAttr(wx.TEXT_ATTR_CHARACTER))
        self._editor.AppendText(value)
        sizer.Add(self._editor, 1, self._sizer_flags_for_editor, 3)
        self._sizer.Add(sizer, 1, wx.EXPAND)
        self._editor.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        # print("DEBUG: ValueEditor _create_editor: %s\n" % (self._editor.__repr__()))

    def _get_text_ctrl(self):
        return wx.TextCtrl(self, size=(600, -1))

    def set_validator(self, validator):
        self._editor.SetValidator(validator)

    def get_value(self):
        # print("DEBUG: ValueEditor get_value: %s" % self._editor.GetValue())
        return self._editor.GetValue()

    def set_focus(self):
        self._editor.SetFocus()
        self._editor.SelectAll()

    def on_key_down(self, event):
        character = None
        keycode, control_down = event.GetKeyCode(), event.CmdDown()
        # print("DEBUG: ValueEditor on_key_down: k=%s Ctrl=%s\n" % (keycode, control_down))
        if event.CmdDown() and event.GetKeyCode() == ord('1'):
            character = '$'
        elif event.CmdDown() and event.GetKeyCode() == ord('2'):
            character = '@'
        elif event.CmdDown() and event.GetKeyCode() == ord('5'):  # DEBUG New
            character = '&'
        if character:
            if len(self.get_value()) == 0:
                self._editor.WriteText(character + "{}")
            else:
                self._editor.AppendText(" | " + character + "{}")
            _from, _ = self._editor.GetSelection()
            self._editor.SetInsertionPoint(_from-1)
        else:
            event.Skip()


class ArgumentEditor(ValueEditor):

    def _create_editor(self, value, label, settings):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if self._label:
            sizer.Add(Label(self, label=self._label, size=(80, -1)), 0,
                      self._sizer_flags_for_label, 5)
        self._editor = self._get_text_ctrl()
        self._editor.AppendText(value)
        sizer.Add(self._editor, 1, self._sizer_flags_for_editor, 3)
        self._sizer.Add(sizer, 1, wx.EXPAND)


class FileNameEditor(ValueEditor):

    _sizer_flags_for_editor = 0
    _sizer_flags_for_label = wx.TOP | wx.BOTTOM | wx.LEFT

    def __init__(self, parent, value, label, controller, validator=None,
                 settings=None, suggestion_source=None):
        self._suggestion_source = suggestion_source or SuggestionSource(
            parent.plugin, None)
        self._controller = controller
        self._label = label
        self._parent = parent
        ValueEditor.__init__(self, parent, value, label, validator, settings)

    def setFocusToOK(self):
        self._parent.setFocusToOK()

    def _get_text_ctrl(self):
        return ContentAssistFileButton(self, self._suggestion_source, '',
                                       self._controller, (500, -1))


class VariableNameEditor(ValueEditor):

    def _get_text_ctrl(self):
        textctrl = ValueEditor._get_text_ctrl(self)
        textctrl.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        return textctrl

    def OnFocus(self, event):
        wx.CallAfter(self.SetSelection, event.GetEventObject())
        event.Skip()

    def SetSelection(self, event):
        self._editor.SetSelection(2, len(self._editor.Value) - 1)


class ListValueEditor(ValueEditor):
    expand_factor = 1
    _sizer_flags_for_editor = wx.ALL | wx.EXPAND

    def _create_editor(self, value, label, settings):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._settings = settings
        cols = self._settings.get("list variable columns", 4)
        sizer.Add(self._create_components(label, cols))
        self._editor = _EditorGrid(self, value, cols)
        sizer.Add(self._editor, 1, self._sizer_flags_for_editor, 3)
        self._sizer.Add(sizer, 1, wx.EXPAND)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def _create_components(self, label, cols):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._create_label(label), 0, wx.ALL, 5)
        sizer.Add((-1, 10))
        sizer.Add(self._create_column_selector(cols))
        return sizer

    def _create_label(self, label_text):
        return Label(self, label=label_text, size=(80, -1))

    def _create_column_selector(self, cols):
        sizer = wx.BoxSizer(wx.VERTICAL)
        col_label = Label(self, label="Columns", size=(80, -1))
        sizer.Add(col_label, 0, wx.ALL, 5)
        combo = wx.ComboBox(self, value=str(cols), size=(60, 25),
                            choices=[str(i) for i in range(1, 11)])
        combo.SetToolTip(wx.ToolTip("Number of columns that are shown in this "
                                    "editor. Selected value is stored and used"
                                    " globally."))
        self.Bind(wx.EVT_COMBOBOX, self.OnColumns, source=combo)
        sizer.Add(combo)
        return sizer

    def OnColumns(self, event):
        num_cols = int(event.String)
        self._settings["list variable columns"] = num_cols
        self._editor.set_number_of_columns(num_cols)

    def OnAddRow(self, event):
        self._editor.add_row()

    def OnSize(self, event):
        self._editor.resize_columns(event.Size[0] - 110)
        event.Skip()

    def get_value(self):
        return self._editor.get_value()


class _EditorGrid(GridEditor):
    _col_add_threshold = 0

    def __init__(self, parent, value, num_cols):
        num_rows = len(value) / num_cols + 2
        GridEditor.__init__(self, parent, num_rows, num_cols)
        self._set_default_sizes()
        self._bind_actions()
        self._write_content(value)

    def _set_default_sizes(self):
        self.SetColLabelSize(wx.grid.GRID_AUTOSIZE)
        self.SetRowLabelSize(wx.grid.GRID_AUTOSIZE)
        self.SetDefaultColSize(20)
        self.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())

    def _bind_actions(self):
        bind_keys_to_evt_menu(self, self._get_bind_keys())
        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.OnEditorShown)

    def _get_bind_keys(self):
        return [(ctrl_or_cmd(), ord('c'), self.OnCopy),
                (ctrl_or_cmd(), ord('x'), self.OnCut),
                (ctrl_or_cmd(), ord('v'), self.OnPaste),
                (ctrl_or_cmd(), ord('z'), self.OnUndo),
                (ctrl_or_cmd(), ord('a'), self.OnSelectAll),
                (wx.ACCEL_NORMAL, wx.WXK_DELETE, self.OnDelete)]

    def _write_content(self, value):
        self.BeginBatch()
        self.ClearGrid()
        for index, item in enumerate(value):
            row, col = divmod(index, self.NumberCols)
            self.write_cell(row, col, item, False)
        self.EndBatch()
        self.AutoSizeRows()

    def get_value(self):
        value = []
        for row in range(self.NumberRows):
            for col in range(self.NumberCols):
                value.append(self.GetCellValue(row, col))
        while value and not value[-1]:
            value.pop()
        return value

    def OnEditorShown(self, event):
        if event.Row >= self.NumberRows - 1:
            self.AppendRows(1)

    def OnInsertCells(self, event):
        if len(self.selection.rows()) != 1:
            self._insert_cells_to_multiple_rows(event)
            return

        def insert_cells(data, start, end):
            return data[:start] + [''] * (end - start) + data[start:]
        self._insert_or_delete_cells_on_single_row(insert_cells, event)

    def OnDeleteCells(self, event):
        # print("DEBUG delete cells %s" % self.selection.rows())
        if len(self.selection.rows()) != 1:
            self._delete_cells_from_multiple_rows(event)
            return

        def delete_cells(data, start, end):
            return data[:start] + data[end:]
        self._insert_or_delete_cells_on_single_row(delete_cells, event)

    def _insert_or_delete_cells_on_single_row(self, action, event):
        self._update_history()
        value = self.get_value()
        row, col = self.selection.cell
        start = row * self.NumberCols + col
        data = action(value, start, start + len(self.selection.cols()))
        self._write_content(data)
        event.Skip()

    def _insert_cells_to_multiple_rows(self, event):
        GridEditor.OnInsertCells(self, event)

    def _delete_cells_from_multiple_rows(self, event):
        GridEditor.OnDeleteCells(self, event)

    def OnCopy(self, event):
        self.copy()

    def OnCut(self, event):
        self.cut()

    def OnPaste(self, event):
        self.paste()

    def OnDelete(self, event):
        self.delete()

    def OnUndo(self, event):
        self.undo()

    def OnSelectAll(self, event):
        self.SelectAll()

    def resize_columns(self, width):
        print("DEBUG: Called resize coluumns, width=%d" % width)
        self.SetDefaultColSize(max(width / self.NumberCols, 100), True)

    def set_number_of_columns(self, columns):
        new_cols = columns - self.NumberCols
        if not new_cols:
            return
        width = self.NumberCols * self.GetDefaultColSize()
        data = self.get_value()
        self._set_cols(new_cols)
        self.resize_columns(width)
        self._write_content(data)

    def _set_cols(self, new_cols):
        if new_cols > 0:
            self.AppendCols(numCols=new_cols)
        else:
            self.DeleteCols(numCols=-new_cols)


class MultiLineEditor(ValueEditor):
    _sizer_flags_for_editor = wx.ALL | wx.EXPAND

    def _get_text_ctrl(self):
        return wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(600, 400))


class ContentAssistEditor(ValueEditor):

    def __init__(self, parent, value, label=None, validator=None,
                 settings=None, suggestion_source=None):
        self._suggestion_source = suggestion_source or SuggestionSource(
            parent.plugin, None)
        ValueEditor.__init__(self, parent, value, label, validator, settings)

    def _get_text_ctrl(self):
        return ContentAssistTextCtrl(self, self._suggestion_source)
        #DEBUG size, (500, -1))
