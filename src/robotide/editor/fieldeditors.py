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

import builtins
import wx
import wx.grid
from wx import Colour

from .contentassist import ContentAssistTextCtrl
from .gridbase import GridEditor
from ..context import ctrl_or_cmd, bind_keys_to_evt_menu
from ..editor.contentassist import ContentAssistFileButton
from ..namespace.suggesters import SuggestionSource
from ..utils import split_value
from ..widgets import Label

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class ValueEditor(wx.Panel):
    expand_factor = 0
    _sizer_flags_for_editor = wx.ALL
    _sizer_flags_for_label = wx.ALL

    def __init__(self, parent, value, label=None, validator=None, settings=None, split=False):
        wx.Panel.__init__(self, parent)
        self._label = label
        self.split = split
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        from ..preferences import RideSettings
        _settings = RideSettings()
        self.general_settings = _settings['General']
        self.color_background = self.general_settings['background']
        self.color_foreground = self.general_settings['foreground']
        self.color_secondary_background = self.general_settings['secondary background']
        self.color_secondary_foreground = self.general_settings['secondary foreground']
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        self._create_editor(value, label, settings)
        if validator:
            self.set_validator(validator)
        self.SetSizer(self._sizer)
        self._sizer.Fit(self)
        self.Layout()

    def _create_editor(self, value, label, settings):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if self._label:
            sizer.Add(Label(self, label=self._label, size=(80, -1)), 0,
                      self._sizer_flags_for_label, 5)
        self._editor = self._get_text_ctrl()
        self._editor.AppendText(value)
        sizer.Add(self._editor, 1, self._sizer_flags_for_editor, 3)
        self._sizer.Add(sizer, 1, wx.EXPAND)
        self._editor.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        # print("DEBUG: ValueEditor _create_editor: %s\n" % (self._editor.__repr__()))

    def _get_text_ctrl(self):
        editor = wx.TextCtrl(self, size=(600, -1))
        editor.SetBackgroundColour(Colour(self.color_secondary_background))
        # editor.SetOwnBackgroundColour(Colour(self.color_secondary_background))
        editor.SetForegroundColour(Colour(self.color_secondary_foreground))
        # editor.SetOwnForegroundColour(Colour(self.color_secondary_foreground))
        return editor

    def set_validator(self, validator):
        self._editor.SetValidator(validator)

    def get_value(self):
        # print("DEBUG: ValueEditor get_value: %s" % self.source_editor.GetValue())
        value = self._editor.GetValue()
        if not self.split:
            return value
        return split_value(value)

    def set_focus(self):
        self._editor.SetFocus()
        self._editor.SelectAll()

    def on_key_down(self, event):
        character = None
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
        self._editor.Bind(wx.EVT_KEY_DOWN, self.on_key_down)


class FileNameEditor(ValueEditor):

    _sizer_flags_for_editor = 0
    _sizer_flags_for_label = wx.TOP | wx.BOTTOM | wx.LEFT

    def __init__(self, parent, value, label, controller, validator=None, settings=None, suggestion_source=None):
        self._suggestion_source = suggestion_source or SuggestionSource(parent.plugin, None)
        self._controller = controller
        self._label = label
        self._parent = parent
        ValueEditor.__init__(self, parent, value, label, validator, settings)

    def setFocusToOK(self):
        self._parent.setFocusToOK()

    def _get_text_ctrl(self):
        filename_ctrl = ContentAssistFileButton(self, self._suggestion_source, '', self._controller, (500, -1))
        filename_ctrl.SetBackgroundColour(Colour(self.color_secondary_background))
        filename_ctrl.SetForegroundColour(Colour(self.color_secondary_foreground))
        return filename_ctrl


class VariableNameEditor(ValueEditor):

    def _get_text_ctrl(self):
        textctrl = ValueEditor._get_text_ctrl(self)
        textctrl.Bind(wx.EVT_SET_FOCUS, self.on_focus)
        return textctrl

    def on_focus(self, event):
        wx.CallAfter(self.SetSelection, event.GetEventObject())
        event.Skip()

    def SetSelection(self, event):
        __ = event
        self._editor.SetSelection(2, len(self._editor.Value) - 1)


class ListValueEditor(ValueEditor):
    expand_factor = 1
    _sizer_flags_for_editor = wx.ALL | wx.EXPAND

    def _create_editor(self, value, label, settings):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._settings = settings
        cols = self._settings.get("list variable columns", 4)
        # print(f"DEBUG: ListValueEditor before calling sizer.Add _create_components label={label} cols={cols}")
        sizer.Add(self._create_components(label, cols))
        self._editor = _EditorGrid(self, value, cols)
        sizer.Add(self._editor, 1, self._sizer_flags_for_editor, 3)
        self._sizer.Add(sizer, 1, wx.EXPAND)
        self.Bind(wx.EVT_SIZE, self.on_size)

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
        col_label = Label(self, label=_("Columns"), size=(80, -1))
        sizer.Add(col_label, 0, wx.ALL, 5)
        combo = wx.ComboBox(self, value=str(cols), size=(60, 25),
                            choices=[str(i) for i in range(1, 11)])
        tool_tip = wx.ToolTip(_("Number of columns that are shown in this editor."
                              " Selected value is stored and used globally."))
        combo.SetToolTip(tool_tip)
        tool_tip.GetWindow().SetBackgroundColour(Colour(self.color_background_help))
        tool_tip.GetWindow().SetForegroundColour(Colour(self.color_foreground_text))
        # DEBUG attributes = self.GetClassDefaultAttributes()
        combo.SetBackgroundColour(Colour(self.color_secondary_background))
        # combo.SetOwnBackgroundColour(Colour(self.color_secondary_background))
        combo.SetForegroundColour(Colour(self.color_secondary_foreground))
        # combo.SetOwnForegroundColour(Colour(self.color_secondary_foreground))
        self.Bind(wx.EVT_COMBOBOX, self.on_columns, source=combo)
        sizer.Add(combo)
        # DEBUG children = self.GetChildren()
        # print(f"DEBUG: Creating columns size selector: attributes bg ={attributes.colBg}\n children={children}")
        return sizer

    def on_columns(self, event):
        num_cols = int(event.String)
        self._settings["list variable columns"] = num_cols
        self._editor.set_number_of_columns(num_cols)

    def on_size(self, event):
        self._editor.resize_columns(event.Size[0] - 110)
        event.Skip()

    def get_value(self):
        return self._editor.get_value()


class _EditorGrid(GridEditor):

    def __init__(self, parent, value, num_cols):
        num_rows = round(len(value) / num_cols + 2)
        # print(f"DEBUG: _EditorGrid __init__ calc num_rows={num_rows}  num_cols={num_cols}")
        GridEditor.__init__(self, parent, num_rows, num_cols)
        """
        self.SetBackgroundColour(Colour(200, 222, 40))
        self.SetOwnBackgroundColour(Colour(200, 222, 40))
        self.SetForegroundColour(Colour(7, 0, 70))
        self.SetOwnForegroundColour(Colour(7, 0, 70))
        """
        self._set_default_sizes()
        self._bind_actions()
        self._write_content(value)
        self.Refresh(True)
        """
        self._colorize()
        """

    def _set_default_sizes(self):
        self.SetColLabelSize(wx.grid.GRID_AUTOSIZE)
        self.SetRowLabelSize(wx.grid.GRID_AUTOSIZE)
        self.SetDefaultColSize(20)
        self.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())

    def _bind_actions(self):
        bind_keys_to_evt_menu(self, self._get_bind_keys())
        self.Bind(wx.grid.EVT_GRID_EDITOR_SHOWN, self.on_editor_shown)

    def _get_bind_keys(self):
        return [(ctrl_or_cmd(), ord('c'), self.on_copy),
                (ctrl_or_cmd(), ord('x'), self.on_cut),
                (ctrl_or_cmd(), ord('v'), self.on_paste),
                (ctrl_or_cmd(), ord('z'), self.on_undo),
                (ctrl_or_cmd(), ord('a'), self.on_select_all),
                (wx.ACCEL_NORMAL, wx.WXK_DELETE, self.on_delete)]

    def _write_content(self, value):
        self.BeginBatch()
        self.ClearGrid()
        for index, item in enumerate(value):
            row, col = divmod(index, self.NumberCols)
            self.write_cell(row, col, item, False)
        self.EndBatch()
        self.AutoSizeRows()

    def _colorize(self):
        """ Just ignore it """
        pass

    def get_value(self):
        value = []
        for row in range(self.NumberRows):
            for col in range(self.NumberCols):
                value.append(self.GetCellValue(row, col))
        while value and not value[-1]:
            value.pop()
        return value

    def on_editor_shown(self, event):
        if event.Row >= self.NumberRows - 1:
            self.AppendRows(1)

    def on_insert_cells(self, event):
        if len(self.selection.rows()) != 1:
            self._insert_cells_to_multiple_rows(event)
            return

        def insert_cells(data, start, end):
            return data[:start] + [''] * (end - start) + data[start:]
        self._insert_or_delete_cells_on_single_row(insert_cells, event)

    def on_delete_cells(self, event):
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
        GridEditor.on_insert_cells(self, event)

    def _delete_cells_from_multiple_rows(self, event):
        GridEditor.on_delete_cells(self, event)

    def on_copy(self, event):
        __ = event
        self.copy()

    def on_cut(self, event):
        __ = event
        self.cut()

    def on_paste(self, event):
        __ = event
        self.paste()

    def on_delete(self, event):
        __ = event
        self.delete()

    def on_undo(self, event):
        __ = event
        self.undo()

    def on_select_all(self, event):
        __ = event
        self.SelectAll()

    def resize_columns(self, width):
        # print("DEBUG: Called resize coluumns, width=%d" % width)
        self.SetDefaultColSize(max(int(width / self.NumberCols), 100), True)

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
        editor = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_NOHIDESEL, size=(600, 400))
        editor.SetBackgroundColour(Colour(self.color_secondary_background))
        editor.SetForegroundColour(Colour(self.color_secondary_foreground))
        """
        editor.SetBackgroundColour(Colour(200, 222, 40))
        editor.SetOwnBackgroundColour(Colour(200, 222, 40))
        editor.SetForegroundColour(Colour(7, 0, 70))
        editor.SetOwnForegroundColour(Colour(7, 0, 70))
        """
        return editor


class ContentAssistEditor(ValueEditor):

    def __init__(self, parent, value, label=None, validator=None,
                 settings=None, suggestion_source=None):
        self._suggestion_source = suggestion_source or SuggestionSource(
            parent.plugin, None)
        ValueEditor.__init__(self, parent, value, label, validator, settings)

    def _get_text_ctrl(self):
        editor_ctrl = ContentAssistTextCtrl(self, self._suggestion_source)
        editor_ctrl.SetBackgroundColour(Colour(self.color_background_help))
        editor_ctrl.SetForegroundColour(Colour(self.color_foreground_text))
        return editor_ctrl
        # DEBUG size, (500, -1))
