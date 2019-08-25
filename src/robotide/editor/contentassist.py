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

import os
from os.path import relpath, dirname, isdir
import wx
from wx.lib.expando import ExpandoTextCtrl
from wx.lib.filebrowsebutton import FileBrowseButton

from robotide import context, utils
from robotide.namespace.suggesters import SuggestionSource
from robotide.spec.iteminfo import VariableInfo
from .popupwindow import RidePopupWindow, HtmlPopupWindow
from robotide.utils import PY3
if PY3:
    from robotide.utils import unichr


_PREFERRED_POPUP_SIZE = (400, 200)


class _ContentAssistTextCtrlBase(object):

    def __init__(self, suggestion_source):
        self._popup = ContentAssistPopup(self, suggestion_source)
        self.Bind(wx.EVT_KEY_DOWN, self.OnChar)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnFocusLost)
        self.Bind(wx.EVT_MOVE, self.OnFocusLost)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        self._showing_content_assist = False
        self._row = None
        self.gherkin_prefix = ''  # Store gherkin prefix from input to add \
        # later after search is performed

    def set_row(self, row):
        self._row = row

    def OnChar(self, event):
        # TODO: This might benefit from some cleanup
        keycode, control_down = event.GetKeyCode(), event.CmdDown()
        # print("DEBUG:  before processing" + str(keycode) + " + " +  str(control_down))
        # Ctrl-Space handling needed for dialogs # DEBUG add Ctrl-m
        if (control_down or event.AltDown()) and keycode in (wx.WXK_SPACE, ord('m')):
            self.show_content_assist()
        elif keycode in [wx.WXK_UP, wx.WXK_DOWN, wx.WXK_PAGEUP, wx.WXK_PAGEDOWN]\
                and self._popup.is_shown():
            self._popup.select_and_scroll(keycode)
        elif keycode == wx.WXK_RETURN and self._popup.is_shown():
            self.OnFocusLost(event)
        elif keycode == wx.WXK_TAB:
            self.OnFocusLost(event, False)
        elif keycode == wx.WXK_ESCAPE and self._popup.is_shown():
            self._popup.hide()
        elif self._popup.is_shown() and keycode < 256:
            wx.CallAfter(self._populate_content_assist)
            event.Skip()
        elif keycode in (ord('1'), ord('2'), ord('5')) and event.ControlDown() and not \
                event.AltDown():
            self.execute_variable_creator(list_variable=(keycode == ord('2')),
                                          dict_variable=(keycode == ord('5')))
        else:
            event.Skip()

    def execute_variable_creator(self, list_variable=False, dict_variable=False):
        from_, to_ = self.GetSelection()
        if list_variable:
            symbol = '@'
        elif dict_variable:
            symbol = '&'
        else:
            symbol = '$'
        self.SetValue(self._variable_creator_value(
            self.Value, symbol, from_, to_))
        if from_ == to_:
            self.SetInsertionPoint(from_ + 2)
        else:
            self.SetSelection(from_ + 2, to_ + 2)

    def _variable_creator_value(self, value, symbol, from_, to_):
        return value[:from_]+symbol+'{'+value[from_:to_]+'}'+value[to_:]

    def OnFocusLost(self, event, set_value=True):
        event.Skip()
        if not self._popup.is_shown():
            return
        if self.gherkin_prefix:
            value = self.gherkin_prefix + self._popup.get_value() or self.GetValue()
        else:
            value = self._popup.get_value() or self.GetValue()
        if set_value and value:
            self.SetValue(value)
            self.SetInsertionPoint(len(value))  # DEBUG was self.Value
        else:
            self.Clear()
        self.hide()

    def OnDestroy(self, event):
        # all pushed eventHandlers need to be popped before close
        # the last event handler is window object itself - do not pop itself
        while self.GetEventHandler() is not self:
            self.PopEventHandler()

    def reset(self):
        self._popup.reset()
        self._showing_content_assist = False

    def show_content_assist(self):
        if self._showing_content_assist:
            return
        self._showing_content_assist = True
        if self._populate_content_assist():
            self._show_content_assist()

    def _populate_content_assist(self):
        value = self.GetValue()
        (self.gherkin_prefix, value) = self._remove_bdd_prefix(value)
        return self._popup.content_assist_for(value, row=self._row)

    def _remove_bdd_prefix(self, name):
        for match in ['given ', 'when ', 'then ', 'and ', 'but ']:
            if name.lower().startswith(match):
                return (name[:len(match)], name[len(match):])
        return ('', name)

    def _show_content_assist(self):
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            _, height = self.GetSize()
            x, y = self.ClientToScreen((0, 0))
        else:
            height = self.GetSizeTuple()[1]
            x, y = self.ClientToScreenXY(0, 0)
        self._popup.show(x, y, height)

    def content_assist_value(self):
        suggestion = self._popup.content_assist_value(self.Value)
        if suggestion is None:
            return suggestion
        else:
            return self.gherkin_prefix + suggestion

    def hide(self):
        self._popup.hide()
        self._showing_content_assist = False


class ExpandingContentAssistTextCtrl(_ContentAssistTextCtrlBase,
                                     ExpandoTextCtrl):

    def __init__(self, parent, plugin, controller):
        ExpandoTextCtrl.__init__(self, parent, size=wx.DefaultSize,
                                 style=wx.WANTS_CHARS)
        _ContentAssistTextCtrlBase.__init__(self,
                                            SuggestionSource(plugin,
                                                             controller))


class ContentAssistTextCtrl(_ContentAssistTextCtrlBase, wx.TextCtrl):

    def __init__(self, parent, suggestion_source, size=wx.DefaultSize):
        wx.TextCtrl.__init__(self, parent, size=size, style=wx.WANTS_CHARS)
        _ContentAssistTextCtrlBase.__init__(self, suggestion_source)


class ContentAssistFileButton(_ContentAssistTextCtrlBase, FileBrowseButton):

    def __init__(self, parent, suggestion_source, label, controller,
                 size=wx.DefaultSize):
        FileBrowseButton.__init__(self, parent, labelText=label,
                                  size=size, fileMask="*",
                                  changeCallback=self.OnFileChanged)
        self._parent = parent
        self._controller = controller
        self._browsed = False
        _ContentAssistTextCtrlBase.__init__(self, suggestion_source)

    # TODO Re-enable ContentAssist for Library and Resources
    # DEBUG With this commented, at least we can type Libraries and Resources on Windows
    def Bind(self, *args):
        # print("DEBUG: Bind ContentAssistFileButton: %s\n" % args.__repr__())
        self.textControl.Bind(*args)

    def SetInsertionPoint(self, pos):
        self.textControl.SetInsertionPoint(pos)

    @property
    def Value(self):
        return self.textControl.Value

    def AppendText(self, *args):
        return self.textControl.AppendText(*args)

    def OnBrowse(self, evt):
        self._browsed = True
        FileBrowseButton.OnBrowse(self, evt)
        self._browsed = False

    def OnFileChanged(self, evt):
        if self._browsed:
            self._browsed = False
            self.SetValue(self._relative_path(self.GetValue()))
            self._parent.setFocusToOK()
        # print("DEBUG: FileBrowseButton: %s\n" % evt.GetString())

    def SelectAll(self):
        self.textControl.SelectAll()

    def _relative_path(self, value):
        src = self._controller.datafile.source
        if utils.is_same_drive(src, value):
            path = relpath(value, src if isdir(src) else dirname(src))
        else:
            path = value
        return path.replace('\\', '/') if context.IS_WINDOWS else\
            path.replace('\\', '\\\\')


class Suggestions(object):

    def __init__(self, suggestion_source):
        self._suggestion_source = suggestion_source
        self._previous_value = None
        self._previous_choices = []

    def get_for(self, value, row=None):
        self._previous_choices = self._get_choices(value, row)
        self._previous_value = value
        return [k for k, _ in self._previous_choices]

    def get_item(self, name):
        for k, v in self._previous_choices:
            if k == name:
                return v
        raise Exception('Item not in choices "%s"' % (name))

    def _get_choices(self, value, row):
        if self._previous_value and value.startswith(self._previous_value):
            return [(key, val) for key, val in self._previous_choices
                    if utils.normalize(key).startswith(utils.normalize(value))]
        choices = self._suggestion_source.get_suggestions(value, row)
        duplicate_names = self._get_duplicate_names(choices)
        return self._format_choices(choices, value, duplicate_names)

    def _get_duplicate_names(self, choices):
        results = set()
        normalized_names = [utils.normalize(ch.name) for ch in choices]
        for choice in choices:
            normalized = utils.normalize(choice.name)
            if normalized_names.count(normalized) > 1:
                results.add(normalized)
        return results

    def _format_choices(self, choices, prefix, duplicate_names):
        return [(self._format(val, prefix, duplicate_names), val) for val in
                choices]

    def _format(self, choice, prefix, duplicate_names):
        return choice.name if self._matches_unique_shortname(
            choice, prefix, duplicate_names) else choice.longname

    def _matches_unique_shortname(self, choice, prefix, duplicate_names):
        if isinstance(choice, VariableInfo):
            return True
        if not utils.normalize(choice.name).startswith(
                utils.normalize(prefix)):
            return False
        if utils.normalize(choice.name) in duplicate_names:
            return False
        return True


class ContentAssistPopup(object):

    def __init__(self, parent, suggestion_source):
        self._parent = parent
        self._main_popup = RidePopupWindow(parent, _PREFERRED_POPUP_SIZE)
        self._details_popup = HtmlPopupWindow(parent, _PREFERRED_POPUP_SIZE)
        self._selection = -1
        self._list = ContentAssistList(self._main_popup,
                                       self.OnListItemSelected,
                                       self.OnListItemActivated)
        self._suggestions = Suggestions(suggestion_source)
        # TODO Add detach popup from list with mouse drag or key
        # self._details_popup.Bind(wx.EVT_MIDDLE_DOWN, self.OnDetach)
        # self._main_popup.Bind(wx.EVT_MIDDLE_DOWN, self.OnDetach)
        # self._list.Bind(wx.EVT_MIDDLE_DOWN, self.OnDetach)

    def reset(self):
        self._selection = -1

    def get_value(self):
        return self._selection != -1 and self._list.get_text(
            self._selection) or None

    def content_assist_for(self, value, row=None):
        self._choices = self._suggestions.get_for(value, row=row)
        if not self._choices:
            self._list.ClearAll()
            self._parent.hide()
            return False
        self._list.populate(self._choices)
        return True

    def _starts(self, val1, val2):
        return val1.lower().startswith(val2.lower())

    def content_assist_value(self, value):
        if self._selection > -1:
            return self._list.GetItem(self._selection).GetText()
        return None

    def show(self, xcoord, ycoord, cell_height):
        self._main_popup.SetPosition((xcoord,
                                      self._move_y_where_room(ycoord,
                                                              cell_height)))
        self._details_popup.SetPosition((self._move_x_where_room(xcoord),
                                         self._move_y_where_room(ycoord,
                                                                 cell_height)))
        self._main_popup.Show()
        self._list.SetFocus()

    def _move_x_where_room(self, start_x):
        width = _PREFERRED_POPUP_SIZE[0]
        max_horizontal = wx.GetDisplaySize()[0]
        free_right = max_horizontal - start_x - width
        free_left = start_x - width
        if max_horizontal - start_x < 2 * width:
            if free_left > free_right:
                return start_x - width
        return start_x + width

    def _move_y_where_room(self, start_y, cell_height):
        height = _PREFERRED_POPUP_SIZE[1]
        max_vertical = wx.GetDisplaySize()[1]
        if max_vertical - start_y - cell_height < height:
            return start_y - height
        return start_y + cell_height

    def is_shown(self):
        return self._main_popup.IsShown()

    def select_and_scroll(self, keycode):
        sel = self._list.GetFirstSelected()
        if keycode == wx.WXK_DOWN:
            if sel < (self._list.GetItemCount() - 1):
                self._select_and_scroll(sel + 1)
            else:
                self._select_and_scroll(0)
        elif keycode == wx.WXK_UP:
            if sel > 0:
                self._select_and_scroll(sel - 1)
            else:
                self._select_and_scroll(self._list.GetItemCount() - 1)
        elif keycode == wx.WXK_PAGEDOWN:
            if self._list.ItemCount - self._selection > 14:
                self._select_and_scroll(self._selection + 14)
            else:
                self._select_and_scroll(self._list.ItemCount - 1)
        elif keycode == wx.WXK_PAGEUP:
            if self._selection > 14:
                self._select_and_scroll(self._selection - 14)
            else:
                self._select_and_scroll(0)

    def _select_and_scroll(self, selection):
        self._selection = selection
        self._list.Select(self._selection)
        self._list.EnsureVisible(self._selection)
        value = self.get_value()
        if value:
            self._parent.SetValue(value)

    def hide(self):
        self._selection = -1
        self._main_popup.Show(False)
        self._details_popup.Show(False)

    def OnListItemActivated(self, event):
        self._parent.OnFocusLost(event)

    def OnListItemSelected(self, event):
        self._selection = event.GetIndex()
        item = self._suggestions.get_item(event.GetText())
        if item.details:
            self._details_popup.Show()
            self._details_popup.set_content(item.details, item.name)
        elif self._details_popup.IsShown():
            self._details_popup.Show(False)

    # def OnDetach(self, event):  # DEBUG Attempt to activate detach on Windows and wxPython >3.0.3
    #     print("DEBUG Contentassist Called Detach")
    #     if not self._details_popup.IsShown():
    #         return
    #     self._details_popup._detach(event)


class ContentAssistList(wx.ListCtrl):

    def __init__(self, parent, selection_callback, activation_callback=None):
        style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER
        wx.ListCtrl.__init__(self, parent, style=style)
        self._selection_callback = selection_callback
        self._activation_callback = activation_callback
        self.SetSize(parent.GetSize())
        self.SetBackgroundColour(context.POPUP_BACKGROUND)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, selection_callback)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, activation_callback)

    def populate(self, data):
        self.ClearAll()
        self.InsertColumn(0, '', width=self.Size[0])
        if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
            for row, item in enumerate(data):
                self.InsertItem(row, item)
        else:
            for row, item in enumerate(data):
                self.InsertStringItem(row, item)
        self.Select(0)

    def get_text(self, index):
        return self.GetItem(index).GetText()
