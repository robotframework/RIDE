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

from os.path import relpath, dirname, isdir
from sys import platform

import wx
from wx import Colour
from wx.lib.expando import ExpandoTextCtrl
from wx.lib.filebrowsebutton import FileBrowseButton

from .. import context, utils
from ..context import IS_MAC, IS_WX_410_OR_HIGHER
from ..namespace.suggesters import SuggestionSource
from ..spec.iteminfo import VariableInfo
from .popupwindow import RidePopupWindow, HtmlPopupWindow
from ..publish import PUBLISHER
from ..publish.messages import RideSettingsChanged


_PREFERRED_POPUP_SIZE = (400, 200)
_AUTO_SUGGESTION_CFG_KEY = "disable auto suggestions"


class _ContentAssistTextCtrlBase(wx.TextCtrl):

    def __init__(self, suggestion_source, **kw):
        super().__init__(**kw)
        from ..preferences import RideSettings
        _settings = RideSettings()
        self.general_settings = _settings['General']
        self.color_background = self.general_settings['background']
        self.color_foreground = self.general_settings['foreground']
        self.color_secondary_background = self.general_settings['secondary background']
        self.color_secondary_foreground = self.general_settings['secondary foreground']
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        self._popup = ContentAssistPopup(self, suggestion_source)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.pop_event_handlers)
        self._row = None
        self.gherkin_prefix = ''
        # Store gherkin prefix from input to add \
        # later after search is performed
        if IS_MAC and IS_WX_410_OR_HIGHER:
            self.OSXDisableAllSmartSubstitutions()
        self._is_auto_suggestion_disabled = self._get_auto_suggestion_config()
        PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)

    @staticmethod
    def _get_auto_suggestion_config():
        from robotide.context import APP
        settings = APP.settings['Grid']
        return settings.get(_AUTO_SUGGESTION_CFG_KEY, False)

    def OnSettingsChanged(self, message):
        """Update auto suggestion settings from PUBLISHER message"""
        section, setting = message.keys
        if section == 'Grid':
            if _AUTO_SUGGESTION_CFG_KEY in setting:
                self._is_auto_suggestion_disabled = message.new

    def set_row(self, row):
        self._row = row

    def is_shown(self):
        return self._popup.is_shown()

    def OnKeyDown(self, event):
        key_code, control_down, alt_down = event.GetKeyCode(), event.CmdDown(), event.AltDown()
        # Ctrl-Space handling needed for dialogs # DEBUG add Ctrl-m
        if (control_down or alt_down) and key_code in [wx.WXK_SPACE, ord('m')]:
            self.show_content_assist()
        elif key_code == wx.WXK_BACK:
            event.Skip()
            wx.CallAfter(self._show_auto_suggestions_when_enabled)

        # Can not catch the following keyEvent from grid cell
        elif key_code == wx.WXK_RETURN:
            # fill suggestion in dialogs when pressing enter
            self.fill_suggestion()
            event.Skip()

        # Can not catch the following keyEvent at all
        # elif key_code == wx.WXK_TAB:
        #     self.fill_suggestion()
        # elif key_code == wx.WXK_ESCAPE and self.is_shown():
        #     self._popup.hide()

        elif key_code in [wx.WXK_UP, wx.WXK_DOWN, wx.WXK_PAGEUP, wx.WXK_PAGEDOWN] \
                and self.is_shown():
            self._popup.select_and_scroll(key_code)
        elif key_code in (ord('1'), ord('2'), ord('5')) and control_down and not \
                alt_down:
            self.execute_variable_creator(list_variable=(key_code == ord('2')),
                                          dict_variable=(key_code == ord('5')))
        else:
            event.Skip()

    def _show_auto_suggestions_when_enabled(self):
        if not self._is_auto_suggestion_disabled or self.is_shown():
            self.show_content_assist()

    def OnChar(self, event):
        key_char = event.GetUnicodeKey()
        if key_char != wx.WXK_RETURN:
            self._show_auto_suggestions_when_enabled()
        if key_char == wx.WXK_NONE:
            event.Skip()
            return
        if key_char in [ord('['), ord('{'), ord('('), ord("'"), ord('\"'), ord('`')]:
            # TODO fix recursion error in Linux
            if platform.lower().startswith('linux'):
                event.Skip()
            else:
                self.execute_enclose_text(chr(key_char))
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
            self.SetInsertionPoint(to_ + 3)
            self.SetSelection(from_ + 2, to_ + 2)

    def _variable_creator_value(self, value, symbol, from_, to_):
        return value[:from_] + symbol + '{' + value[from_:to_] + '}' + value[to_:]

    def execute_enclose_text(self, keycode):
        # TODO move this code to kweditor and fix when in cell editor in Linux
        from_, to_ = self.GetSelection()
        self.SetValue(self._enclose_text(self.Value, keycode, from_, to_))
        elem = self
        if from_ == to_:
            elem.SetInsertionPoint(from_ + 1)
        else:
            elem.SetInsertionPoint(to_ + 2)
            elem.SetSelection(from_ + 1, to_ + 1)

    def _enclose_text(self, value, open_symbol, from_, to_):
        if open_symbol == '[':
            close_symbol = ']'
        elif open_symbol == '{':
            close_symbol = '}'
        elif open_symbol == '(':
            close_symbol = ')'
        else:
            close_symbol = open_symbol
        return value[:from_] + open_symbol + value[from_:to_] + close_symbol + value[to_:]

    def fill_suggestion(self):
        if self.gherkin_prefix:
            value = self.gherkin_prefix + self._popup.get_value() or self.GetValue()
        else:
            value = self._popup.get_value() or self.GetValue()

        if value:
            wrapper_view = self.GetParent().GetParent()
            if hasattr(wrapper_view, 'open_cell_editor'):
                # in grid cell, need to make sure cell editor is open
                wrapper_view.open_cell_editor()
            self.SetValue(value)
            self.SetInsertionPoint(len(value))

        self.hide()

    def pop_event_handlers(self, event):
        # all pushed eventHandlers need to be popped before close
        # the last event handler is window object itself - do not pop itself
        if self:
            while self.GetEventHandler() is not self:
                self.PopEventHandler()

    def reset(self):
        self._popup.reset()

    def show_content_assist(self):
        if self._populate_content_assist():
            self._show_content_assist()

    def _populate_content_assist(self):
        value = self.GetValue()
        (self.gherkin_prefix, value) = self._remove_bdd_prefix(value)
        return self._popup.content_assist_for(value, row=self._row)

    def _remove_bdd_prefix(self, name):
        for match in ['given ', 'when ', 'then ', 'and ', 'but ']:
            if name.lower().startswith(match):
                return name[:len(match)], name[len(match):]
        return '', name

    def _show_content_assist(self):
        _, height = self.GetSize()
        x, y = self.ClientToScreen((0, 0))
        self._popup.show(x, y, height)

    def content_assist_value(self):
        suggestion = self._popup.content_assist_value(self.Value)
        if suggestion is None:
            return suggestion
        else:
            return self.gherkin_prefix + suggestion

    def hide(self):
        if not self.is_shown():
            return
        self._popup.hide()

    def dismiss(self):
        if not self.is_shown():
            return
        self._popup.dismiss()


class ExpandingContentAssistTextCtrl(_ContentAssistTextCtrlBase, ExpandoTextCtrl):

    def __init__(self, parent, plugin, controller):
        """ According to class MRO, super().__init__ in  _ContentAssistTextCtrlBase will init ExpandoTextCtrl
        instance """

        _ContentAssistTextCtrlBase.__init__(self, SuggestionSource(plugin, controller),
                                            parent=parent, size=wx.DefaultSize,
                                            style=wx.WANTS_CHARS | wx.TE_NOHIDESEL)
        self.SetBackgroundColour(context.POPUP_BACKGROUND)
        # self.SetOwnBackgroundColour(Colour(200, 222, 40))
        self.SetForegroundColour(context.POPUP_FOREGROUND)
        # self.SetOwnForegroundColour(Colour(7, 0, 70)


class ContentAssistTextCtrl(_ContentAssistTextCtrlBase):

    def __init__(self, parent, suggestion_source, size=wx.DefaultSize):
        super().__init__(suggestion_source, parent=parent,
                         size=size, style=wx.WANTS_CHARS | wx.TE_NOHIDESEL)
        wx.TextCtrl.__init__(self, parent, size=size, style=wx.WANTS_CHARS|wx.TE_NOHIDESEL)
        _ContentAssistTextCtrlBase.__init__(self, suggestion_source)
        self.SetBackgroundColour(Colour(self.color_background_help))
        self.SetOwnBackgroundColour(Colour(self.color_background_help))
        self.SetForegroundColour(Colour(self.color_foreground_text))
        self.SetOwnForegroundColour(Colour(self.color_foreground_text))


class ContentAssistTextEditor(_ContentAssistTextCtrlBase):

    def __init__(self, parent, suggestion_source, pos, size=wx.DefaultSize):
        super().__init__(suggestion_source,
                         parent=parent, id=-1, value="", pos=pos, size=size,
                         style=wx.WANTS_CHARS | wx.BORDER_NONE | wx.WS_EX_TRANSIENT | wx.TE_PROCESS_ENTER |
                         wx.TE_NOHIDESEL)
        wx.TextCtrl.__init__(self, parent, -1, "", pos, size=size, style=wx.WANTS_CHARS|wx.BORDER_NONE|wx.WS_EX_TRANSIENT|wx.TE_PROCESS_ENTER|wx.TE_NOHIDESEL)
        _ContentAssistTextCtrlBase.__init__(self, suggestion_source)
        self.SetBackgroundColour(Colour(self.color_background_help))
        self.SetOwnBackgroundColour(Colour(self.color_background_help))
        self.SetForegroundColour(Colour(self.color_foreground_text))
        self.SetOwnForegroundColour(Colour(self.color_foreground_text))
        """
        self.SetBackgroundColour(Colour(200, 222, 40))
        self.SetOwnBackgroundColour(Colour(200, 222, 40))
        self.SetForegroundColour(Colour(7, 0, 70))
        self.SetOwnForegroundColour(Colour(7, 0, 70))
        """


class ContentAssistFileButton(FileBrowseButton):

    def __init__(self, parent, suggestion_source, label, controller, size=wx.DefaultSize):
        self.suggestion_source = suggestion_source
        FileBrowseButton.__init__(self, parent, labelText=label,
                                  size=size, fileMask="*",
                                  changeCallback=self.OnFileChanged)
        self._parent = parent
        self._controller = controller
        self._browsed = False

        _ContentAssistTextCtrlBase.__init__(self, suggestion_source)
        self.SetBackgroundColour(Colour(context.POPUP_BACKGROUND))
        self.SetOwnBackgroundColour(Colour(context.POPUP_BACKGROUND))
        self.SetForegroundColour(Colour(context.POPUP_FOREGROUND))
        self.SetOwnForegroundColour(Colour(context.POPUP_FOREGROUND))

    def Bind(self, *args):
        self.textControl.Bind(*args)

    def createTextControl(self):
        """Create the text control"""
        textControl = _ContentAssistTextCtrlBase(parent=self, id=-1, suggestion_source=self.suggestion_source)
        textControl.SetToolTip(self.toolTip)
        if self.changeCallback:
            textControl.Bind(wx.EVT_TEXT, self.OnChanged)
            textControl.Bind(wx.EVT_COMBOBOX, self.OnChanged)
        return textControl

    def __getattr__(self, item):
        return getattr(self.textControl, item)

    def OnBrowse(self, evt=None):
        self._browsed = True
        FileBrowseButton.OnBrowse(self, evt)
        self._browsed = False

    def OnFileChanged(self, evt):
        if self._browsed:
            self._browsed = False
            self.SetValue(self._relative_path(self.GetValue()))
            self._parent.setFocusToOK()

    def _relative_path(self, value):
        src = self._controller.datafile.source
        if utils.is_same_drive(src, value):
            path = relpath(value, src if isdir(src) else dirname(src))
        else:
            path = value
        return path.replace('\\', '/') if context.IS_WINDOWS else \
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
        raise Exception('Item not in choices "%s"' % name)

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
        self._list: ContentAssistList = ContentAssistList(self._main_popup,
                                                          self.OnListItemSelected,
                                                          self.OnListItemActivated)
        self._suggestions = Suggestions(suggestion_source)

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
            if self._list.GetItemCount() - self._selection > 14:
                self._select_and_scroll(self._selection + 14)
            else:
                self._select_and_scroll(self._list.GetItemCount() - 1)
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

    def dismiss(self):
        if not self._list.HasFocus():
            self.hide()

    def hide(self):
        self._selection = -1
        self._main_popup.Show(False)
        self._details_popup.Show(False)

    def OnListItemActivated(self, event):
        self._parent.fill_suggestion()

    def OnListItemSelected(self, event):
        self._selection = event.GetIndex()
        item = self._suggestions.get_item(event.GetText())
        if item.details:
            self._details_popup.Show()
            self._details_popup.set_content(item.details, item.name)
        elif self._details_popup.IsShown():
            self._details_popup.Show(False)


class ContentAssistList(wx.ListCtrl):

    def __init__(self, parent, selection_callback, activation_callback=None):
        self.parent = parent
        from ..preferences import RideSettings
        _settings = RideSettings()
        self.general_settings = _settings['General']
        self.color_background_help = self.general_settings['background help']
        self.color_foreground_text = self.general_settings['foreground text']
        style = wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_NO_HEADER
        wx.ListCtrl.__init__(self, parent, style=style)
        self._selection_callback = selection_callback
        self._activation_callback = activation_callback
        self.SetSize(parent.GetSize())
        self.SetBackgroundColour(self.color_background_help)
        self.SetForegroundColour(self.color_foreground_text)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, selection_callback)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, activation_callback)

    def populate(self, data):
        self.ClearAll()
        self.InsertColumn(0, '', width=self.Size[0])
        for row, item in enumerate(data):
            self.InsertItem(row, item)
        self.Select(0)

    def get_text(self, index):
        return self.GetItem(index).GetText()
