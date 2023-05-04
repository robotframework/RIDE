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

import string
from io import StringIO, BytesIO
from time import time

import wx
from wx import stc, Colour
from wx.adv import HyperlinkCtrl, EVT_HYPERLINK

from .. import robotapi
from ..context import IS_WINDOWS, IS_MAC
from ..controller.ctrlcommands import SetDataFile, INDENTED_START
from ..controller.filecontrollers import ResourceFileController
from ..controller.macrocontrollers import WithStepsController
from ..namespace.suggesters import SuggestionSource
from ..pluginapi import Plugin, TreeAwarePluginMixin
from ..publish.messages import (RideSaving, RideTreeSelection, RideNotebookTabChanging, RideDataChanged, RideOpenSuite,
                                RideDataChangedToDirty)
from ..preferences.editors import read_fonts
from ..publish import RideSettingsChanged, PUBLISHER
from ..publish.messages import RideMessage
from ..widgets import TextField, Label, HtmlDialog
from ..widgets import VerticalSizer, HorizontalSizer, ButtonWithHandler, RIDEDialog

try:  # import installed version first
    from pygments.lexers import robotframework as robotframeworklexer
except ImportError:
    robotframeworklexer = None

PLUGIN_NAME = 'Text Edit'
TXT_NUM_SPACES = 'txt number of spaces'
ZOOM_FACTOR = 'zoom factor'


class TextEditorPlugin(Plugin, TreeAwarePluginMixin):
    title = PLUGIN_NAME

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._editor_component = None
        self.reformat = application.settings.get('reformat', False)

    @property
    def _editor(self):
        if self._editor_component is None:
            self._editor_component = SourceEditor(self.notebook,
                                                  self.title,
                                                  DataValidationHandler(self))
            self._refresh_timer = wx.Timer(self._editor_component)
            self._editor_component.Bind(wx.EVT_TIMER, self._on_timer)
        return self._editor_component

    def enable(self):
        self.add_self_as_tree_aware_plugin()
        self.subscribe(self.OnSaving, RideSaving)
        self.subscribe(self.OnTreeSelection, RideTreeSelection)
        self.subscribe(self.OnDataChanged, RideMessage)
        self.subscribe(self.OnTabChange, RideNotebookTabChanging)
        if self._editor.is_focused():
            self._register_shortcuts()
            self._open()

    def _register_shortcuts(self):
        def focused(func):
            def f(event):
                if self.is_focused() and self._editor.is_focused():
                    func(event)

            return f

        self.register_shortcut('CtrlCmd-X', focused(lambda e: self._editor.cut()))
        self.register_shortcut('CtrlCmd-C', focused(lambda e: self._editor.copy()))
        if IS_MAC:  # Mac needs this key binding
            self.register_shortcut('CtrlCmd-A', focused(lambda e: self._editor.select_all()))
        if IS_WINDOWS or IS_MAC:  # Linux does not need this key binding
            self.register_shortcut('CtrlCmd-V', focused(lambda e: self._editor.paste()))
        self.register_shortcut('CtrlCmd-Z', focused(lambda e: self._editor.undo()))
        self.register_shortcut('CtrlCmd-Y', focused(lambda e: self._editor.redo()))
        # self.register_shortcut('Del', focused(lambda e: self.source_editor.delete()))
        self.register_shortcut('CtrlCmd-S', focused(lambda e: self.OnSaving(e)))
        self.register_shortcut('CtrlCmd-Shift-I', focused(lambda e: self._editor.insert_cell(e)))
        # self.register_shortcut('CtrlCmd-Shift-D', focused(lambda e: self.source_editor.delete_cell(e)))
        self.register_shortcut('Alt-Up', focused(lambda e: self._editor.move_row_up(e)))
        self.register_shortcut('Alt-Down', focused(lambda e: self._editor.move_row_down(e)))
        # self.register_shortcut('CtrlCmd-D', focused(lambda e: self.source_editor.delete_row(e)))
        self.register_shortcut('CtrlCmd-I', focused(lambda e: self._editor.insert_row(e)))
        self.register_shortcut('CtrlCmd-3', focused(lambda e: self._editor.execute_comment(e)))
        self.register_shortcut('CtrlCmd-Shift-3', focused(lambda e: self._editor.execute_sharp_comment(e)))
        self.register_shortcut('CtrlCmd-4', focused(lambda e: self._editor.execute_uncomment(e)))
        self.register_shortcut('CtrlCmd-Shift-4', focused(lambda e: self._editor.execute_sharp_uncomment(e)))
        self.register_shortcut('CtrlCmd-F', lambda e: self._editor.search_field.SetFocus())
        self.register_shortcut('CtrlCmd-G', lambda e: self._editor.OnFind(e))
        self.register_shortcut('CtrlCmd-Shift-G', lambda e: self._editor.OnFindBackwards(e))
        self.register_shortcut('Ctrl-Space', lambda e: focused(self._editor.OnContentAssist(e)))
        self.register_shortcut('CtrlCmd-Space', lambda e: focused(self._editor.OnContentAssist(e)))
        self.register_shortcut('Alt-Space', lambda e: focused(self._editor.OnContentAssist(e)))

    def disable(self):
        self.remove_self_from_tree_aware_plugins()
        self.unsubscribe_all()
        self.unregister_actions()
        self.delete_tab(self._editor)
        self._editor_component = None

    def OnOpen(self, event):
        _ = event
        self._open()

    def _open(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            self._open_data_for_controller(datafile_controller)
            self._editor.store_position()

    def OnSaving(self, message):
        _ = message
        if self.is_focused():
            self._editor.save()
        elif isinstance(message, RideSaving):
            # print(f"DEBUG: textedit OnSaving Open Saved from other {message=} isfocused={self.is_focused()}")
            self._open()  # Was saved from other Editor

    def OnDataChanged(self, message):
        """ This block is now inside try/except to avoid errors from unit test """
        try:
            # print(f"DEBUG: textedit OnDataChanged message={message}")
            if self._should_process_data_changed_message(message):
                if isinstance(message, RideOpenSuite):
                    self._editor.reset()
                    self._editor.set_editor_caret_position()
                if isinstance(message, RideNotebookTabChanging):
                    return
                if self._editor.dirty and not self._apply_txt_changes_to_model():
                    return
                self._refresh_timer.Start(500, True)
                # For performance reasons only run after all the data changes
        except AttributeError:
            pass

    def _on_timer(self, event):
        self._editor.store_position()
        self._open_tree_selection_in_editor()
        event.Skip()

    @staticmethod
    def _should_process_data_changed_message(message):
        return isinstance(message, RideDataChanged) and \
            not isinstance(message, RideDataChangedToDirty)

    def OnTreeSelection(self, message):
        self._editor.store_position()
        if self.is_focused():
            next_datafile_controller = message.item and message.item.datafile_controller
            if self._editor.dirty and not self._apply_txt_changes_to_model():
                if self._editor.datafile_controller != next_datafile_controller:
                    self.tree.select_controller_node(self._editor.datafile_controller)
                self._editor.set_editor_caret_position()
                return
            if next_datafile_controller:
                self._open_data_for_controller(next_datafile_controller)
            self._set_read_only(message)
            self._editor.set_editor_caret_position()
        else:
            self._editor.GetFocus(None)

    def _set_read_only(self, message):
        if not isinstance(message, bool):
            self._editor.source_editor.readonly = not message.item.datafile_controller.is_modifiable()
        self._editor.source_editor.SetReadOnly(self._editor.source_editor.readonly)
        self._editor.source_editor.stylizer.set_styles(self._editor.source_editor.readonly)
        self._editor.source_editor.Update()

    def _open_tree_selection_in_editor(self):
        try:
            datafile_controller = self.tree.get_selected_datafile_controller()
        except AttributeError:
            return
        if datafile_controller:
            self._editor.open(DataFileWrapper(datafile_controller, self.global_settings))
            self._editor.source_editor.readonly = not datafile_controller.is_modifiable()
        self._editor.set_editor_caret_position()

    def _open_data_for_controller(self, datafile_controller):
        self._editor.selected(DataFileWrapper(datafile_controller, self.global_settings))
        self._editor.source_editor.readonly = not datafile_controller.is_modifiable()

    def OnTabChange(self, message):
        if message.newtab == self.title:
            self._register_shortcuts()
            self._open()
            self._editor.set_editor_caret_position()
            try:
                self._set_read_only(self._editor.source_editor.readonly)
            except Exception:  # DEBUG: When using only Text Editor exists error in message topic
                pass
        elif message.oldtab == self.title:
            self._editor.remove_and_store_state()
            self.unregister_actions()
            self._editor_component.save()

    def OnTabChanged(self, event):
        _ = event
        self._show_editor()

    def OnTabChanging(self, message):
        if 'Edit' in message.oldtab:
            self._editor.save()

    def _apply_txt_changes_to_model(self):
        if not self._editor.save():
            return False
        self._editor.reset()
        self._editor.set_editor_caret_position()
        return True

    def is_focused(self):
        return self.notebook.current_page_title == self.title


class DummyController(WithStepsController):
    _populator = robotapi.UserKeywordPopulator
    filename = ""

    def _init(self, data=None):
        self.data = data

    @staticmethod
    def get_local_variables():
        return {}

    def __eq__(self, other):
        if self is other:
            return True
        if other.__class__ != self.__class__:
            return False
        return self.data == other.data

    def __hash__(self):
        return hash(repr(self))


class DataValidationHandler(object):

    def __init__(self, plugin):
        self._plugin = plugin
        self._last_answer = None
        self._last_answer_time = 0
        self._editor = None

    def set_editor(self, editor):
        self._editor = editor

    def validate_and_update(self, data, text):
        m_text = text.decode("utf-8")
        if not self._sanity_check(data, m_text):
            handled = self._handle_sanity_check_failure()
            if not handled:
                return False
        self._editor.reset()
        data.update_from(m_text)
        """
        # DEBUG: This is the area where we will implement to not reformat code
        if self.source_editor._reformat:
            data.update_from(m_text)
        else:
            data.update_from(m_text)  # TODO: This is the same code as _reformat == True
            # There is no way to update the model without reformatting
            # TODO this only updates the editor, but not the model, changes in Text Editor are not reflected in Grid or
            # when saving
            #  self.source_editor.source_editor.set_text(m_text)
        """
        self._editor.set_editor_caret_position()
        return True

    def _sanity_check(self, data, text):
        # First remove all lines starting with #
        for line in text.split('\n'):
            comment = line.strip().startswith('#')
            if comment:
                text = text.replace(line, '')
        formatted_text = data.format_text(text)
        c = self._normalize(formatted_text)
        e = self._normalize(text)
        return len(c) == len(e)

    @staticmethod
    def _normalize(text):
        for item in tuple(string.whitespace) + ('...', '*'):
            if item in text:
                text = text.replace(item, '')
        return text

    def _handle_sanity_check_failure(self):
        if self._last_answer == wx.ID_NO and time() - self._last_answer_time <= 0.2:
            # self.source_editor._mark_file_dirty(True)
            return False
        # DEBUG: use widgets.Dialog
        dlg = wx.MessageDialog(self._editor, 'ERROR: Data sanity check failed!\n'
                                             'Reset changes?',
                               'Can not apply changes from Txt Editor', style=wx.YES | wx.NO)
        dlg.InheritAttributes()
        """
        dlg.SetBackgroundColour(Colour(200, 222, 40))
        dlg.SetOwnBackgroundColour(Colour(200, 222, 40))
        dlg.SetForegroundColour(Colour(7, 0, 70))
        dlg.SetOwnForegroundColour(Colour(7, 0, 70))
        """
        # dlg.Refresh(True)
        did = dlg.ShowModal()
        self._last_answer = did
        self._last_answer_time = time()
        if did == wx.ID_YES:
            self._editor.revert()
            return True
        # else:
        #    self.source_editor._mark_file_dirty()
        return False


class DataFileWrapper(object):  # DEBUG: bad class name

    def __init__(self, data, settings):
        self.wrapper_data = data
        self._settings = settings
        self._tab_size = self._settings.get(TXT_NUM_SPACES, 2) if self._settings else 2

    def __eq__(self, other):
        if other is None:
            return False
        return self.wrapper_data == other.wrapper_data

    def update_from(self, content):
        self.wrapper_data.execute(SetDataFile(self._create_target_from(content)))

    def _create_target_from(self, content):
        src = BytesIO(content.encode("utf-8"))
        target = self._create_target()
        FromStringIOPopulator(target).populate(src, self._tab_size)
        return target

    def format_text(self, text):
        return self._txt_data(self._create_target_from(text))

    def mark_data_dirty(self):
        self.wrapper_data.mark_dirty()

    def mark_data_pristine(self):
        self.wrapper_data.unmark_dirty()

    def _create_target(self):
        data = self.wrapper_data.data
        target_class = type(data)
        if isinstance(data, robotapi.TestDataDirectory):
            target = robotapi.TestDataDirectory(source=self.wrapper_data.directory)
            target.initfile = data.initfile
            return target
        return target_class(source=self.wrapper_data.source)

    @property
    def content(self):
        return self._txt_data(self.wrapper_data.data)

    def _txt_data(self, data):
        output = StringIO()
        data.save(output=output, format='txt', txt_separating_spaces=self._settings.get(TXT_NUM_SPACES, 4))
        return output.getvalue()


class SourceEditor(wx.Panel):

    def __init__(self, parent, title, data_validator):
        wx.Panel.__init__(self, parent)
        self.dlg = RIDEDialog()
        self.SetBackgroundColour(Colour(self.dlg.color_background))
        self.SetForegroundColour(Colour(self.dlg.color_foreground))
        self._syntax_colorization_help_exists = False
        self._data_validator = data_validator
        self._data_validator.set_editor(self)
        self.source_editor_parent = parent
        self._title = title
        self.tab_size = self.source_editor_parent.app.settings.get(TXT_NUM_SPACES, 4)
        self._reformat = self.source_editor_parent.app.settings.get('reformat', False)
        self._create_ui(title)
        self._data = None
        self._dirty = 0  # 0 is False and 1 is True, when changed on this editor
        self._position = None
        self._showing_list = False
        self._tab_open = None
        self._controller_for_context = None
        self._suggestions = None
        self._stored_text = None
        PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)
        PUBLISHER.subscribe(self.OnTabChange, RideNotebookTabChanging)

    def is_focused(self):
        # DEBUG: foc = wx.Window.FindFocus()
        # DEBUG: return any(elem == foc for elem in [self]+list(self.GetChildren()))
        return self._tab_open == self._title

    def OnTabChange(self, message):
        self._tab_open = message.newtab

    def _create_ui(self, title):
        cnt = self.source_editor_parent.GetPageCount()
        if cnt >= 0:
            editor_created = False
            while cnt > 0 and not editor_created:
                cnt -= 1
                editor_created = self.source_editor_parent.GetPageText(cnt) == self._title
                # DEBUG: Later we can adjust for several Text Editor tabs
            if not editor_created:
                self.SetSizer(VerticalSizer())
                self._create_editor_toolbar()
                self._create_editor_text_control()
                self.source_editor_parent.add_tab(self, title, allow_closing=False)

    def _create_editor_toolbar(self):
        # needs extra container, since we might add helper
        # text about syntax colorization
        self.editor_toolbar = HorizontalSizer()
        default_components = HorizontalSizer()
        button = ButtonWithHandler(self, 'Apply Changes', handler=lambda e: self.save())
        button.SetBackgroundColour(Colour(self.dlg.color_secondary_background))
        button.SetForegroundColour(Colour(self.dlg.color_secondary_foreground))
        default_components.add_with_padding(button)
        self._create_search(default_components)
        self.editor_toolbar.add_expanding(default_components)
        self.Sizer.add_expanding(self.editor_toolbar, propotion=0)

    def _create_search(self, container_sizer):
        container_sizer.AddSpacer(20)
        self.search_field = TextField(self, '', process_enters=True)
        self.search_field.SetBackgroundColour(Colour(self.dlg.color_secondary_background))
        self.search_field.SetForegroundColour(Colour(self.dlg.color_secondary_foreground))
        self.search_field.Bind(wx.EVT_TEXT_ENTER, self.OnFind)
        container_sizer.add_with_padding(self.search_field)
        button = ButtonWithHandler(self, 'Search', handler=self.OnFind)
        button.SetBackgroundColour(Colour(self.dlg.color_secondary_background))
        button.SetForegroundColour(Colour(self.dlg.color_secondary_foreground))
        container_sizer.add_with_padding(button)
        self._search_field_notification = Label(self, label='')
        container_sizer.add_with_padding(self._search_field_notification)

    def create_syntax_colorization_help(self):
        if self._syntax_colorization_help_exists:
            return
        label = Label(self, label="Syntax colorization disabled due to missing requirements.")
        link = HyperlinkCtrl(self, -1, label="Get help", url="")
        link.Bind(EVT_HYPERLINK, self.show_help_dialog)
        flags = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        syntax_colorization_help_sizer = wx.BoxSizer(wx.VERTICAL)
        syntax_colorization_help_sizer.AddMany([
            (label, 0, flags),
            (link, 0, flags)
        ])
        self.editor_toolbar.add_expanding(syntax_colorization_help_sizer)
        self.Layout()
        self._syntax_colorization_help_exists = True

    @staticmethod
    def show_help_dialog(event):
        _ = event
        content = """<h1>Syntax colorization</h1>
        <p>
        Syntax colorization for Text Edit uses <a href='http://pygments.org/'>Pygments</a> syntax highlighter.
        </p>
        <p>
        Install Pygments from command line with:
        <pre>
            pip install pygments
        </pre>
        Or:
        <pre>
            easy_install pygments
        </pre>
        Then, restart RIDE.
        </p>
        <p>
        If you do not have pip or easy_install,
        <a href='http://pythonhosted.org/an_example_pypi_project/setuptools.html#installing-setuptools-and-easy-install'
        >follow these instructions</a>.
        </p>
        <p>
        For more information about installing Pygments, <a href='http://pygments.org/download/'>see the site</a>.
        </p>
        """
        HtmlDialog("Getting syntax colorization", content).Show()

    def store_position(self, force=False):
        _ = force
        if self.source_editor and self.datafile_controller:
            cur_pos = self.source_editor.GetCurrentPos()
            if cur_pos > 0:  # Cheating because it always goes to zero
                self._position = cur_pos
                self.source_editor.GotoPos(self._position)

    def set_editor_caret_position(self):
        if not self.is_focused():  # DEBUG was typing text when at Grid Editor
            return
        position = self._position
        self.source_editor.SetFocus()
        if position:
            self.source_editor.SetCurrentPos(position)
            self.source_editor.SetSelection(position, position)
            self.source_editor.SetAnchor(position)
            self.source_editor.GotoPos(position)
            self.source_editor.Refresh()
            self.source_editor.Update()

    @property
    def dirty(self):
        return self._dirty == 1  # self.source_editor.IsModified() and self._dirty == 1

    @property
    def datafile_controller(self):
        return self._data.wrapper_data if self._data else None

    def OnFind(self, event):
        if self.source_editor:
            text = self.source_editor.GetSelectedText()
            if len(text) > 0 and text.lower() != self.search_field.GetValue().lower() and \
                    event.GetEventType() == wx.wxEVT_TOOL:
                # if a search string selected in text and CTRL+G is pressed
                # put the string into the search_field
                self.search_field.SelectAll()
                self.search_field.Clear()
                self.search_field.Update()
                self.search_field.SetValue(text)
                self.search_field.SelectAll()
                self.search_field.Update()
                # and set the start position to the beginning of the editor
                self.source_editor.SetAnchor(0)
                self.source_editor.SetCurrentPos(0)
                self.source_editor.Update()

            self._find()

    def OnFindBackwards(self, event):
        _ = event
        if self.source_editor:
            self._find(forward=False)

    def _find(self, forward=True):
        txt = self.search_field.GetValue().encode('utf-8')
        position = self._find_text_position(forward, txt)
        self._show_search_results(position, txt)

    # DEBUG: This must be cleaned up
    def _find_text_position(self, forward, txt):
        file_end = len(self.source_editor.utf8_text)
        search_end = file_end if forward else 0
        anchor = self.source_editor.GetAnchor()
        anchor += 1 if forward else 0
        position = self.source_editor.FindText(anchor, search_end, txt, 0)
        if position == -1:
            start, end = (0, file_end) if forward else (file_end - 1, 0)
            position = self.source_editor.FindText(start, end, txt, 0)
        return position

    def _show_search_results(self, position, txt):
        # if text is found start and end of the found text is returned,
        # but we do need just starting position which is the first value
        if type(position) is tuple:
            position = position[0]

        if position != -1:
            self.source_editor.SetCurrentPos(position)
            self.source_editor.SetSelection(position, position + len(txt))
            self.source_editor.ScrollToLine(self.source_editor.GetCurrentLine())
            self._search_field_notification.SetLabel('')
        else:
            self._search_field_notification.SetLabel('No matches found.')

    def OnContentAssist(self, event):
        _ = event
        self._showing_list = False
        # if not self.is_focused():
        #    return
        self.store_position()
        selected = self.source_editor.get_selected_or_near_text()
        sugs = [s.name for s in self._suggestions.get_suggestions(
            selected or '')]
        if sugs:
            self.source_editor.AutoCompSetDropRestOfWord(True)
            self.source_editor.AutoCompSetSeparator(ord(';'))
            self.source_editor.AutoCompShow(0, ";".join(sugs))
            self._showing_list = True

    def open(self, data):
        self.reset()
        self._data = data
        try:
            if isinstance(self._data.wrapper_data, ResourceFileController):
                self._controller_for_context = DummyController(self._data.wrapper_data, self._data.wrapper_data)
                self._suggestions = SuggestionSource(None, self._controller_for_context)
            else:
                self._suggestions = SuggestionSource(None, self._data.wrapper_data.tests[0])
        except IndexError:  # It is a new project, no content yet
            self._controller_for_context = DummyController(self._data.wrapper_data, self._data.wrapper_data)
            self._suggestions = SuggestionSource(None, self._controller_for_context)
        if not self.source_editor:
            self._stored_text = self._data.content
        else:
            self.source_editor.set_text(self._data.content)
            self.set_editor_caret_position()

    def selected(self, data):
        if not self.source_editor:
            self._create_editor_text_control(self._stored_text)
        if self._data == data:
            return
        self.open(data)

    def _add_auto_indent(self, line: str):
        lenline = len(line)
        linenum = self.source_editor.GetCurrentLine()
        idx = 0
        while idx < lenline and line[idx] == ' ':
            idx += 1
        tsize = idx // self.tab_size
        block_line = line.strip().split(' ')[0]
        if idx < lenline and (block_line in INDENTED_START):
            tsize += 1
        elif linenum > 0 and tsize == 0:  # Advance if first task/test case or keyword
            prevline = self.source_editor.GetLine(linenum - 1).lower()
            if prevline.startswith("**") and not ("variables" in prevline or "settings" in prevline):
                tsize = 1
        elif line.strip().startswith("END"):
            pos = self.source_editor.GetCurrentPos()
            self.source_editor.SetCurrentPos(pos)
            self.source_editor.SetSelection(pos, pos)
        self.source_editor.NewLine()
        while tsize > 0:
            self.write_ident()
            tsize -= 1

    def auto_indent(self):
        line, _ = self.source_editor.GetCurLine()
        lenline = len(line)
        if lenline > 0:
            self._add_auto_indent(line)
        else:
            self.source_editor.NewLine()
        pos = self.source_editor.GetCurrentLine()
        self.source_editor.SetCurrentPos(self.source_editor.GetLineEndPosition(pos))
        self.store_position()

    def deindent_block(self):
        start, end = self.source_editor.GetSelection()
        caret = self.source_editor.GetCurrentPos()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        count = 0
        self.source_editor.SelectNone()
        line = ini_line
        inconsistent = False
        self.source_editor.BeginUndoAction()
        while line <= end_line:
            inconsistent = False
            pos = self.source_editor.PositionFromLine(line)
            self.source_editor.SetCurrentPos(pos)
            self.source_editor.SetSelection(pos, pos)
            self.source_editor.SetInsertionPoint(pos)
            content = self.source_editor.GetRange(pos, pos + self.tab_size)
            if content == (' ' * self.tab_size):
                self.source_editor.DeleteRange(pos, self.tab_size)
                count += 1
                line += 1
            else:
                inconsistent = True
                break
        self.source_editor.EndUndoAction()
        if inconsistent:
            self.source_editor.Undo()
            return
        new_start = max(0, start - self.tab_size)
        new_end = max(0, end - (count * self.tab_size))
        if caret == start:
            ini = new_start
            fini = new_end
        else:
            ini = new_end
            fini = new_start
        self.source_editor.SetSelection(new_start, new_end)
        self.source_editor.SetCurrentPos(ini)
        self.source_editor.SetAnchor(fini)

    def _calc_indent_size(self, text: str):
        lenline = len(text)
        idx = 0
        block_line = text.strip().split(' ')[0]
        while idx < lenline and text[idx] == ' ':
            idx += 1
        tsize = idx // self.tab_size
        if idx < lenline and (block_line in INDENTED_START):
            tsize += 1
        elif tsize == 0:
            text = text.lower()
            if text.startswith("**"):
                if not ("variables" in text or "settings" in text):
                    tsize = 1
        return tsize

    def indent_line(self, line):
        if line > 0:
            pos = self.source_editor.PositionFromLine(line)
            text = self.source_editor.GetLine(line - 1)
            lenline = len(text)
            if lenline > 0:
                tsize = self._calc_indent_size(text)
                self.source_editor.SetCurrentPos(pos)
                self.source_editor.SetSelection(pos, pos)
                self.source_editor.SetInsertionPoint(pos)
                for _ in range(tsize):
                    self.write_ident()

    def indent_block(self):
        start, end = self.source_editor.GetSelection()
        caret = self.source_editor.GetCurrentPos()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        count = 0
        self.source_editor.SelectNone()
        line = ini_line
        while line <= end_line:
            pos = self.source_editor.PositionFromLine(line)
            self.source_editor.SetCurrentPos(pos)
            self.source_editor.SetSelection(pos, pos)
            self.source_editor.SetInsertionPoint(pos)
            self.write_ident()
            count += 1
            line += 1
        new_start = start + self.tab_size
        new_end = end + (count * self.tab_size)
        if caret == start:
            ini = new_start
            fini = new_end
        else:
            ini = new_end
            fini = new_start
        self.source_editor.SetSelection(new_start, new_end)
        self.source_editor.SetCurrentPos(ini)
        self.source_editor.SetAnchor(fini)

    def write_ident(self):
        spaces = ' ' * self.tab_size
        self.source_editor.WriteText(spaces)

    def reset(self):
        self._dirty = 0
        self._mark_file_dirty(False)

    def save(self, *args):
        _ = args
        self.store_position()
        if self.dirty:
            if not self._data_validator.validate_and_update(self._data, self.source_editor.utf8_text):
                return False
        # DEBUG: Was resetting when leaving editor
        # self.reset()
        self.GetFocus(None)
        return True

    """
    # DEBUG: 
    def direct_save(self, text):
        print(f"DEBUG: direct_save path={self.datafile_controller.source}")
        f = open(self.datafile_controller.source, "wb")
        try:
            f.write(text)
            self._mark_file_dirty(False)
            print(f"DEBUG: direct_save Content:\n{text}")
        except Exception as e:
            raise e
        finally:
            f.close()
    """

    def cut(self):
        self.source_editor.Cut()
        self._mark_file_dirty(self.source_editor.GetModify())

    def copy(self):
        self.source_editor.Copy()

    def paste(self):
        focus = wx.Window.FindFocus()
        if focus == self.source_editor:
            self.source_editor.Paste()
        elif focus == self.search_field:
            self.search_field.Paste()
        self._mark_file_dirty(self.source_editor.GetModify())

    def select_all(self):
        self.source_editor.SelectAll()

    def undo(self):
        self.source_editor.Undo()
        self.store_position()
        self._mark_file_dirty(self._dirty == 1 and self.source_editor.GetModify())

    def redo(self):
        self.source_editor.Redo()
        self.store_position()
        self._mark_file_dirty(self.source_editor.GetModify())

    def remove_and_store_state(self):
        if self.source_editor:
            self.store_position()
            self._stored_text = self.source_editor.GetText()

    def _create_editor_text_control(self, text=None):
        self.source_editor = RobotDataEditor(self)
        self.Sizer.add_expanding(self.source_editor)
        self.Sizer.Layout()
        if text is not None:
            self.source_editor.set_text(text)
        self.source_editor.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.source_editor.Bind(wx.EVT_CHAR, self.OnChar)
        self.source_editor.Bind(wx.EVT_KEY_UP, self.OnEditorKey)
        self.source_editor.Bind(wx.EVT_KILL_FOCUS, self.LeaveFocus)
        self.source_editor.Bind(wx.EVT_SET_FOCUS, self.GetFocus)
        # DEBUG: Add here binding for keyword help

    def LeaveFocus(self, event):
        _ = event
        self.source_editor.AcceptsFocusFromKeyboard()
        self.store_position()
        self.source_editor.SetCaretPeriod(0)

    def GetFocus(self, event):
        self.source_editor.SetFocus()
        self.source_editor.AcceptsFocusFromKeyboard()
        self.source_editor.SetCaretPeriod(500)
        if self._position:
            self.set_editor_caret_position()
        if event:
            event.Skip()

    def revert(self):
        self.reset()
        self.source_editor.set_text(self._data.content)

    def OnEditorKey(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE:  # DEBUG on Windows we only get here, single Text Editor
            selected = self.source_editor.GetSelection()
            if selected[0] == selected[1]:
                pos = self.source_editor.GetInsertionPoint()
                if pos != self.source_editor.GetLastPosition():
                    self.source_editor.DeleteRange(selected[0], 1)
            else:
                self.source_editor.DeleteRange(selected[0], selected[1] - selected[0])
        if keycode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            return
        if self.is_focused() and keycode != wx.WXK_CONTROL and self._dirty == 0:
            self._mark_file_dirty(self.source_editor.GetModify())
        event.Skip()

    def OnKeyDown(self, event):
        keycode = event.GetUnicodeKey()
        if event.GetKeyCode() == wx.WXK_DELETE:
            return
        if event.GetKeyCode() == wx.WXK_TAB and not event.ControlDown() and not event.ShiftDown():
            if self._showing_list:  # Allows to use Tab for keyword selection
                self._showing_list = False
                event.Skip()
                return
            selected = self.source_editor.GetSelection()
            if selected[0] == selected[1]:
                self.write_ident()
            else:
                self.indent_block()
        elif event.GetKeyCode() == wx.WXK_TAB and event.ShiftDown():
            selected = self.source_editor.GetSelection()
            if selected[0] == selected[1]:
                pos = self.source_editor.GetCurrentPos()
                self.source_editor.SetCurrentPos(max(0, pos - self.tab_size))
                self.store_position()
                if not event.ControlDown():  # No text selection
                    pos = self.source_editor.GetCurrentPos()
                    self.source_editor.SetSelection(pos, pos)
            else:
                self.deindent_block()
        elif event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            if not self._showing_list:
                self.auto_indent()
            else:
                self._showing_list = False
                event.Skip()
        elif keycode in (ord('1'), ord('2'), ord('5')) and event.ControlDown():
            self.execute_variable_creator(list_variable=(keycode == ord('2')),
                                          dict_variable=(keycode == ord('5')))
            self.store_position()
        elif keycode == ord('D') and event.ControlDown():
            if event.ShiftDown():
                self.delete_cell(event)
            else:
                self.delete_row(event)
        else:
            event.Skip()
        """
        elif keycode == ord('3') and event.ControlDown() and event.ShiftDown():
            self.execute_sharp_comment()
            self.store_position()
        elif keycode == ord('4') and event.ControlDown() and event.ShiftDown():
            self.execute_sharp_uncomment()
            self.store_position()
        """

    def OnChar(self, event):
        if not self.is_focused():
            self.GetFocus(None)
        keycode = event.GetUnicodeKey()
        if chr(keycode) in ['[', '{', '(', "'", '\"', '`']:
            self.execute_enclose_text(chr(keycode))
            self.store_position()
        else:
            event.Skip()

    def execute_variable_creator(self, list_variable=False, dict_variable=False):
        from_, to_ = self.source_editor.GetSelection()
        text = self.source_editor.SelectedText
        size = len(bytes(text, encoding='utf-8'))
        to_ = from_ + size
        if list_variable:
            symbol = '@'
        elif dict_variable:
            symbol = '&'
        else:
            symbol = '$'
        if size == 0:
            self.source_editor.SetInsertionPoint(to_)
            self.source_editor.InsertText(from_, self._variable_creator_value(symbol))
            self.source_editor.SetInsertionPoint(from_ + 2)
        else:
            self.source_editor.DeleteRange(from_, size)
            self.source_editor.SetInsertionPoint(from_)
            self.source_editor.ReplaceSelection(self._variable_creator_value(symbol, text))
            self.source_editor.SetSelection(from_ + 2, from_ + size + 2)

    @staticmethod
    def _variable_creator_value(symbol, value=''):
        return symbol + '{' + value + '}'

    def execute_enclose_text(self, keycode):
        from_, to_ = self.source_editor.GetSelection()
        text = self.source_editor.SelectedText
        size = len(bytes(text, encoding='utf-8'))
        to_ = from_ + size
        if size == 0:
            self.source_editor.SetInsertionPoint(to_)
            self.source_editor.InsertText(from_, self._enclose_text(keycode))
            pos = self.source_editor.GetCurrentPos()
            self.source_editor.SetSelection(pos + 1, pos + 1)
        else:
            self.source_editor.DeleteRange(from_, size)
            self.source_editor.SetInsertionPoint(from_)
            self.source_editor.ReplaceSelection(self._enclose_text(keycode, text))
            self.source_editor.SetSelection(from_ + 1, from_ + size + 1)

    @staticmethod
    def _enclose_text(open_symbol, value=''):
        if open_symbol == '[':
            close_symbol = ']'
        elif open_symbol == '{':
            close_symbol = '}'
        elif open_symbol == '(':
            close_symbol = ')'
        else:
            close_symbol = open_symbol
        return open_symbol + value + close_symbol

    def move_row_up(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        ini_line = self.source_editor.LineFromPosition(start)
        # selection not on top?
        if ini_line > 0:
            end_line = self.source_editor.LineFromPosition(end)
            # get the previous row content and length
            rowabove = self.source_editor.GetLine(ini_line - 1)
            lenabove = len(rowabove.encode('utf-8'))
            # get the content of the block rows
            rowselblock = ''
            rowcnt = ini_line
            while rowcnt <= end_line:
                rowselblock += self.source_editor.GetLine(rowcnt)
                rowcnt += 1
            # add the content of previous row
            rowselblock += rowabove
            begpos = self.source_editor.PositionFromLine(ini_line - 1)
            endpos = self.source_editor.PositionFromLine(end_line + 1)
            self.source_editor.Replace(begpos, endpos, rowselblock)
            self.source_editor.SetSelection(begpos, endpos - lenabove - 1)
            # DEBUG: recalculate line identation for new position and old

    def move_row_down(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        # get the next row content and length
        rowbelow = self.source_editor.GetLine(end_line + 1)
        lenbelow = len(rowbelow.encode('utf-8'))
        # get the content of the block rows after adding the content below first
        # no new rows anymore?
        if lenbelow == 0:
            rowselblock = '\n'
            lenbelow = 1
        else:
            rowselblock = rowbelow
        rowcnt = ini_line
        while rowcnt <= end_line:
            rowselblock += self.source_editor.GetLine(rowcnt)
            rowcnt += 1
        begpos = self.source_editor.PositionFromLine(ini_line)
        endpos = self.source_editor.PositionFromLine(end_line + 2)
        self.source_editor.Replace(begpos, endpos, rowselblock)
        self.source_editor.SetSelection(begpos + lenbelow, endpos - 1)
        # DEBUG: recalculate line identation for new position and old

    def delete_row(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        cursor = self.source_editor.GetCurrentPos()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        begpos = self.source_editor.PositionFromLine(ini_line)
        self.source_editor.SelectNone()
        if start == end:
            end_line = ini_line
        for _ in range(ini_line, end_line + 1):
            self.source_editor.GotoLine(ini_line)
            self.source_editor.LineDelete()
        # cursor position when doing block select is always the end of the selection
        if ini_line != end_line:
            self.source_editor.SetCurrentPos(begpos)
            self.source_editor.SetAnchor(begpos)
        else:
            self.source_editor.SetCurrentPos(cursor)
            self.source_editor.SetAnchor(cursor)
        self.store_position()

    def insert_row(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        delta = end_line - ini_line
        positionfromline = self.source_editor.PositionFromLine(ini_line)
        self.source_editor.SelectNone()
        self.source_editor.InsertText(positionfromline, '\n')
        for nl in range(delta):
            self.source_editor.InsertText(positionfromline + nl, '\n')
        self.source_editor.SetCurrentPos(positionfromline)
        self.source_editor.SetAnchor(positionfromline)
        self.source_editor.GotoLine(ini_line)
        self.indent_line(ini_line)
        self.store_position()

    def execute_comment(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        cursor = self.source_editor.GetCurrentPos()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        spaces = ' ' * self.tab_size
        comment = 'Comment' + spaces
        count = 0
        self.source_editor.SelectNone()
        row = ini_line
        while row <= end_line:
            pos = self.source_editor.PositionFromLine(row)
            self.source_editor.SetCurrentPos(pos)
            self.source_editor.SetSelection(pos, pos)
            self.source_editor.SetInsertionPoint(pos)
            line = self.source_editor.GetLine(row)
            lenline = len(line)
            if lenline > 0:
                idx = 0
                while idx < lenline and line[idx] == ' ':
                    idx += 1
                self.source_editor.InsertText(pos + idx, comment)
            count += 1
            row += 1
        new_start = start
        new_end = end + (count * len(comment))
        if cursor == start:
            ini = new_start
            fini = new_end
        else:
            ini = new_end
            fini = new_start
        self.source_editor.SetSelection(new_start, new_end)
        self.source_editor.SetCurrentPos(ini)
        self.source_editor.SetAnchor(fini)
        self.store_position()

    def execute_uncomment(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        cursor = self.source_editor.GetCurrentPos()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        spaces = ' ' * self.tab_size
        comment = 'Comment' + spaces
        commentlong = 'BuiltIn.Comment' + spaces
        self.source_editor.SelectNone()
        count = 0
        row = ini_line
        while row <= end_line:
            pos = self.source_editor.PositionFromLine(row)
            self.source_editor.SetCurrentPos(pos)
            self.source_editor.SetSelection(pos, pos)
            self.source_editor.SetInsertionPoint(pos)
            line = self.source_editor.GetLine(row)
            lenline = len(line)
            if lenline > 0:
                idx = 0
                while idx < lenline and line[idx] == ' ':
                    idx += 1
                if (line[idx:len(comment) + idx]).lower() == comment.lower():
                    self.source_editor.DeleteRange(pos + idx, len(comment))
                if (line[idx:len(commentlong) + idx]).lower() == commentlong.lower():
                    self.source_editor.DeleteRange(pos + idx, len(commentlong))
            count += 1
            row += 1
        new_start = start
        new_end = end - (count * len(comment))
        if cursor == start:
            ini = new_start
            fini = new_end
        else:
            ini = new_end
            fini = new_start
        self.source_editor.SetSelection(new_start, new_end)
        self.source_editor.SetCurrentPos(ini)
        self.source_editor.SetAnchor(fini)
        self.store_position()

    def insert_cell(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        begpos = self.source_editor.PositionFromLine(ini_line)
        endpos = self.source_editor.PositionFromLine(end_line + 1)
        cell_no_beg = self._get_cell_no(begpos, endpos, start)
        cell_pos_beg = self._get_position_of_cell(begpos, endpos, cell_no_beg)
        # if there is a selection subtract 1 from endpos to circumvent cursor being on end of cell
        # --> otherwise no will be next cell no
        if start != end:
            cell_no_end = self._get_cell_no(begpos, endpos, end - 1)
        else:
            cell_no_end = cell_no_beg
        #  print(f"DEBUG: cell range to handle beg={cell_no_beg} end={cell_no_end}")
        celltab = ' ' * self.tab_size
        # If the selection spans more than one line:
        if ini_line < end_line:  # DEBUG: do inserts in such a way that they can be undone in 1 undo
            new_start = cell_pos_beg
            for line in range(ini_line, end_line + 1):
                begthis = self.source_editor.PositionFromLine(line)
                endthis = self.source_editor.PositionFromLine(line + 1)
                cell_pos_beg = self._get_position_of_cell(begthis, endthis, cell_no_beg)
                self.source_editor.InsertText(cell_pos_beg, celltab)
            new_end = cell_pos_beg + (len(celltab.encode('utf-8')))
        elif start == end:  # On a single row, no selection
            self.source_editor.InsertText(cell_pos_beg, celltab)
            new_start = cell_pos_beg
            new_end = cell_pos_beg + len(celltab.encode('utf-8'))
        else:  # On a single row, with selection
            cells_to_insert = cell_no_end - cell_no_beg + 1
            # insert at once so undo handles it correct
            self.source_editor.InsertText(cell_pos_beg, celltab * cells_to_insert)
            new_start = cell_pos_beg
            new_end = cell_pos_beg + (len(celltab.encode('utf-8')) * cells_to_insert)
        # SetSelection and SetCurrentPos + Store_position overrule each other so only use one of them
        self.source_editor.SetSelection(new_start, new_end)
        # @Helio: SetAnchor overrules the SetSelection if it specifies a different start than
        # SetSelection (but I left your code for now)
        self.source_editor.SetAnchor(new_end)

    def delete_cell(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        begpos = self.source_editor.PositionFromLine(ini_line)
        endpos = self.source_editor.PositionFromLine(end_line + 1)
        cell_no_beg = self._get_cell_no(begpos, endpos, start)
        cell_pos_beg = self._get_position_of_cell(begpos, endpos, cell_no_beg)
        # if there is a selection subtract 1 from endpos to circumvent cursor being on end of cell
        # --> otherwise no will be next cell no
        if start != end:
            cell_no_end = self._get_cell_no(begpos, endpos, end - 1)
        else:
            cell_no_end = cell_no_beg
        cell_pos_end = self._get_position_of_cell(begpos, endpos, cell_no_end + 1)
        self.source_editor.Remove(cell_pos_beg, cell_pos_end)
        new_start = cell_pos_beg
        new_end = new_start + (end - start)
        # SetSelection and SetCurrentPos + Store_position overrule each other so only use one of them
        self.source_editor.SetSelection(new_start, new_end)
        # @Helio: SetAnchor overrules the SetSelection if it specifies a different start than SetSelection
        # I am not sure what any selection should be after deleting big ranges
        self.source_editor.SetAnchor(new_start)

    def _get_cell_no(self, begpos, endpos, findpos):
        # get cell number from range begpos-endpos using findpos 
        cell_no = 0
        celltot = self._get_number_of_cells(begpos, endpos)
        while cell_no < celltot:
            cell_no += 1
            cellpos = self._get_position_of_cell(begpos, endpos, cell_no)
            if cellpos > findpos:
                cell_no -= 1
                break
        return cell_no

    def _get_number_of_cells(self, begpos, endpos):
        # get number of cells in range begpos-endpos
        # Warning! GetStringSelection does not work properly if there are diacritics in the content above (!)
        # the selected range
        the_content = self.source_editor.GetTextRange(begpos, endpos)
        celltab = ' ' * self.tab_size
        return the_content.count(celltab)

    def calc_cellpos(self, begpos, endpos, cell_no):
        _cellpos = 0
        celltab = ' ' * self.tab_size
        cellencode = celltab.encode('utf-8')
        # Warning! GetStringSelection does not work properly if there are diacritics in
        # the content above (!) the selected range
        textrange = self.source_editor.GetTextRange(begpos, endpos)
        textencode = textrange.encode('utf-8')
        fndcnt = 1  # begpos is always in a cell
        fndidx = 0
        while fndidx != -1:
            fndidx = textencode.find(cellencode, fndidx)
            if fndidx != -1:
                if fndcnt == 1 and fndidx == 0:  # check if begpos is at the beginning of a cell
                    fndcnt -= 1
                fndcnt += 1
                if cell_no == fndcnt:
                    _cellpos = begpos + fndidx
                    break
                fndidx += 1  # for next search
        return _cellpos

    def _get_position_of_cell(self, begpos, endpos, cell_no):
        # get position of cell number within range begpos-endpos 
        # DEBUG:  this does not work correctly if first cell within the range is totally empty (so not as \ sanitized)
        cellcnt = self._get_number_of_cells(begpos, endpos)
        if cell_no <= cellcnt:  # encode is needed for finding correct position when there are special characters
            # in the content
            cellpos = self.calc_cellpos(begpos, endpos, cell_no)
        else:  # cell_no does not exist -- return endpos-1
            cellpos = endpos - 1
        return cellpos

    def execute_sharp_comment(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        cursor = self.source_editor.GetCurrentPos()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        spaces = ' ' * self.tab_size
        count = 0
        maxsize = self.source_editor.GetLineCount()
        # If the selection spans on more than one line:
        if ini_line < end_line:
            for line in range(ini_line, end_line + 1):
                count += 1
                if line < maxsize:
                    self.source_editor.GotoLine(line)
                else:
                    self.source_editor.GotoLine(maxsize)
                pos = self.source_editor.PositionFromLine(line)
                self.source_editor.SetCurrentPos(pos)
                self.source_editor.SetSelection(pos, pos)
                self.source_editor.SetInsertionPoint(pos)
                row = self.source_editor.GetLine(line)
                lenline = len(row)
                if lenline > 0:
                    idx = 0
                    while idx < lenline and row[idx] == ' ':
                        idx += 1
                    self.source_editor.InsertText(pos + idx, '# ')
        elif start == end:  # On a single row, no selection
            count += 1
            pos = self.source_editor.PositionFromLine(ini_line)
            row = self.source_editor.GetLine(ini_line)
            lenline = len(row)
            if lenline > 0:
                idx = 0
                while idx < lenline and row[idx] == ' ':
                    idx += 1
                self.source_editor.InsertText(pos + idx, '# ')
        else:  # On a single row, with selection
            count += 1
            pos = self.source_editor.PositionFromLine(ini_line)
            row = self.source_editor.GetLine(ini_line)
            if cursor > pos:
                idx = cursor - pos
                while idx >= len(spaces):
                    if row[idx - len(spaces):idx] != spaces:
                        idx -= 1
                    else:
                        break
                if idx < len(spaces):
                    idx = 0
                self.source_editor.InsertText(pos + idx, '# ')
        new_start = start
        new_end = end + (count * 2)
        if cursor == start:
            ini = new_start
            fini = new_end
        else:
            ini = new_end
            fini = new_start
        self.source_editor.SetSelection(new_start, new_end)  # DEBUG: For some reason the selection is not restored!
        self.source_editor.SetCurrentPos(ini)
        self.source_editor.SetAnchor(fini)
        self.source_editor.SetCurrentPos(cursor + count * 2)
        self.store_position()

    def execute_sharp_uncomment(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        cursor = self.source_editor.GetCurrentPos()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        spaces = ' ' * self.tab_size
        # self.source_editor.SelectNone()
        count = 0
        # maxsize = self.source_editor.GetLineCount()
        # If the selection spans on more than one line:
        if ini_line < end_line:
            for line in range(ini_line, end_line + 1):
                pos = self.source_editor.PositionFromLine(line)
                row = self.source_editor.GetLine(line)
                lenline = len(row)
                if lenline > 0:
                    idx = 0
                    while idx < lenline and row[idx] == ' ':
                        idx += 1
                    size = 1
                    if idx + 1 < lenline and row[idx:idx + 1] == '#':
                        if idx + 2 < lenline and row[idx + 1:idx + 2] == ' ':
                            size = 2
                        # Here we clean up escaped spaces from Apply
                        if idx + size < lenline:
                            newrow = row[idx + size:]
                            newrow = newrow.replace('\\ ', ' ')
                            size += len(row[idx:]) - len(newrow) - size
                            self.source_editor.DeleteRange(pos + idx, len(newrow) + size)
                            self.source_editor.InsertText(pos + idx, newrow)
                        count += size
        elif start == end:  # On a single row, no selection
            pos = self.source_editor.PositionFromLine(ini_line)
            row = self.source_editor.GetLine(ini_line)
            lenline = len(row)
            if lenline > 0:
                idx = 0
                while idx < lenline and row[idx] == ' ':
                    idx += 1
                while count == 0 and idx < lenline:
                    size = 1
                    if idx + 1 < lenline and row[idx:idx + 1] == '#':
                        if idx + 2 < lenline and row[idx + 1:idx + 2] == ' ':
                            size = 2
                        # Here we clean up escaped spaces from Apply
                        if idx + size < lenline:
                            newrow = row[idx + size:]
                            newrow = newrow.replace('\\ ', ' ')
                            size += len(row[idx:]) - len(newrow) - size
                            self.source_editor.DeleteRange(pos + idx, len(newrow) + size)
                            self.source_editor.InsertText(pos + idx, newrow)
                        count += size
                    else:
                        idx += 1
        else:  # On a single row, with selection
            pos = self.source_editor.PositionFromLine(ini_line)
            row = self.source_editor.GetLine(ini_line)
            lenline = len(row)
            if cursor > pos:
                idx = cursor - pos
                while idx >= len(spaces):
                    if row[idx - len(spaces):idx] != spaces:
                        idx -= 1
                    else:
                        break
                if idx < len(spaces):
                    idx = 0
                while count == 0 and idx > 0:
                    size = 1
                    if idx + 1 < lenline and row[idx:idx + 1] == '#':
                        if idx + 2 < lenline and row[idx + 1:idx + 2] == ' ':
                            size = 2
                        # Here we clean up escaped spaces from Apply
                        if idx + size < lenline:
                            newrow = row[idx + size:]
                            newrow = newrow.replace('\\ ', ' ')
                            size += len(row[idx:]) - len(newrow) - size
                            self.source_editor.DeleteRange(pos + idx, len(newrow) + size)
                            self.source_editor.InsertText(pos + idx, newrow)
                        count += size
                    else:
                        idx -= 1
        if count == 0:
            return
        new_start = start
        new_end = end - count
        self.source_editor.SetSelection(new_start, new_end)  # DEBUG: For some reason the selection is not restored!
        self.source_editor.SetCurrentPos(cursor - count)
        self.store_position()

    def OnSettingsChanged(self, message):
        """Update tab size if txt spaces size setting is modified"""
        _, setting = message.keys
        if setting == TXT_NUM_SPACES:
            self.tab_size = self.source_editor_parent.app.settings.get(TXT_NUM_SPACES, 4)
        if setting == 'reformat':
            self._reformat = self.source_editor_parent.app.settings.get('reformat', False)

    def _mark_file_dirty(self, dirty=True):
        if not self.is_focused():  # DEBUG: Was marking file clean from Grid Editor
            return
        if self._data:
            if self._dirty == 0 and dirty:
                self._data.mark_data_dirty()
                self._dirty = 1
            elif self._dirty == 1:
                self._data.mark_data_pristine()
                self._dirty = 0


class RobotDataEditor(stc.StyledTextCtrl):
    margin = 1

    def __init__(self, parent, readonly=False):
        stc.StyledTextCtrl.__init__(self, parent)
        self._settings = parent.source_editor_parent.app.settings
        self.readonly = readonly
        self.SetMarginType(self.margin, stc.STC_MARGIN_NUMBER)
        self.SetLexer(stc.STC_LEX_CONTAINER)
        self.SetReadOnly(True)
        self.SetUseTabs(False)
        self.SetTabWidth(parent.tab_size)
        self.Bind(stc.EVT_STC_STYLENEEDED, self.OnStyle)
        self.Bind(stc.EVT_STC_ZOOM, self.OnZoom)
        self.stylizer = RobotStylizer(self, self._settings, self.readonly)

    def set_text(self, text):
        self.SetReadOnly(False)
        self.SetText(text)
        self.stylizer.stylize()
        self.EmptyUndoBuffer()
        self.SetMarginWidth(self.margin, self.calc_margin_width())

    @property
    def utf8_text(self):
        return self.GetText().encode('UTF-8')

    def OnStyle(self, event):
        _ = event
        self.stylizer.stylize()

    def OnZoom(self, event):
        _ = event
        self.SetMarginWidth(self.margin, self.calc_margin_width())
        self._set_zoom()

    def _set_zoom(self):
        new = self.GetZoom()
        old = self._settings[PLUGIN_NAME].get(ZOOM_FACTOR, 0)
        if new != old:
            self._settings[PLUGIN_NAME].set(ZOOM_FACTOR, new)

    def calc_margin_width(self):
        style = stc.STC_STYLE_LINENUMBER
        width = self.TextWidth(style, str(self.GetLineCount()))
        return width + self.TextWidth(style, "1")

    def get_selected_or_near_text(self):
        # First get selected text
        selected = self.GetSelectedText()
        self.SetInsertionPoint(self.GetInsertionPoint() - len(selected))
        if selected:
            return selected
        # Next get text on the left
        self.SetSelectionEnd(self.GetInsertionPoint())
        self.WordLeftEndExtend()
        selected = self.GetSelectedText()
        select = selected.strip()
        self.SetInsertionPoint(self.GetInsertionPoint() + len(selected)
                               - len(select))
        if select and len(select) > 0:
            return select
        # Finally get text on the right
        self.SetSelectionStart(self.GetInsertionPoint())
        self.WordRightEndExtend()
        selected = self.GetSelectedText()
        select = selected.strip()
        self.SetInsertionPoint(self.GetInsertionPoint() - len(select))
        if select and len(select) > 0:
            return select


class FromStringIOPopulator(robotapi.populators.FromFilePopulator):

    def populate(self, content: [str, BytesIO], tab_size: int):
        robotapi.RobotReader(spaces=tab_size).read(content, self)


class RobotStylizer(object):
    def __init__(self, editor, settings, readonly=False):
        self.tokens = {}
        self.editor = editor
        self.lexer = None
        self.settings = settings
        self._readonly = readonly
        self._ensure_default_font_is_valid()
        if robotframeworklexer:
            self.lexer = robotframeworklexer.RobotFrameworkLexer()
        else:
            self.editor.GetParent().create_syntax_colorization_help()
        self.set_styles(self._readonly)
        PUBLISHER.subscribe(self.on_settings_changed, RideSettingsChanged)

    def on_settings_changed(self, message):
        """Redraw the colors if the color settings are modified"""
        section, setting = message.keys
        if section == PLUGIN_NAME:
            self.set_styles(self._readonly)  # DEBUG: When on read-only file changing background color ignores flag

    def _font_size(self):
        return self.settings[PLUGIN_NAME].get('font size', 10)

    def _font_face(self):
        return self.settings[PLUGIN_NAME].get('font face', 'Courier New')

    def _zoom_factor(self):
        return self.settings[PLUGIN_NAME].get(ZOOM_FACTOR, 0)

    def set_styles(self, readonly=False):
        color_settings = self.settings.get_without_default(PLUGIN_NAME)
        background = color_settings.get('background', '#FFFFFF')
        if readonly:
            h = background.lstrip('#')
            if h.upper() == background.upper():
                from wx import ColourDatabase
                cdb = ColourDatabase()
                bkng = cdb.Find(h.upper())
                bkg = (bkng[0], bkng[1], bkng[2])
            else:
                bkg = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
            if bkg >= (180, 180, 180):
                bkg = (max(160, bkg[0] - 80), max(160, bkg[1] - 80),
                       max(160, bkg[2] - 80))
            else:
                bkg = (min(255, bkg[0] + 180), min(255, bkg[1] + 180),
                       min(255, bkg[2] + 180))
            background = '#%02X%02X%02X' % bkg
        if robotframeworklexer:
            styles = {
                robotframeworklexer.ARGUMENT: {
                    'fore': color_settings.get('argument', '#bb8844')
                },
                robotframeworklexer.COMMENT: {
                    'fore': color_settings.get('comment', 'black')
                },
                robotframeworklexer.ERROR: {
                    'fore': color_settings.get('error', 'black')
                },
                robotframeworklexer.GHERKIN: {
                    'fore': color_settings.get('gherkin', 'black')
                },
                robotframeworklexer.HEADING: {
                    'fore': color_settings.get('heading', '#999999'),
                    'bold': 'true'
                },
                robotframeworklexer.IMPORT: {
                    'fore': color_settings.get('import', '#555555')
                },
                robotframeworklexer.KEYWORD: {
                    'fore': color_settings.get('keyword', '#990000'),
                    'bold': 'true'
                },
                robotframeworklexer.SEPARATOR: {
                    'fore': color_settings.get('separator', 'black')
                },
                robotframeworklexer.SETTING: {
                    'fore': color_settings.get('setting', 'black'),
                    'bold': 'true'
                },
                robotframeworklexer.SYNTAX: {
                    'fore': color_settings.get('syntax', 'black')
                },
                robotframeworklexer.TC_KW_NAME: {
                    'fore': color_settings.get('tc_kw_name', '#aaaaaa')
                },
                robotframeworklexer.VARIABLE: {
                    'fore': color_settings.get('variable', '#008080')
                }
            }
            for index, token in enumerate(styles):
                self.tokens[token] = index
                self.editor.StyleSetSpec(index,
                                         self._get_style_string(back=background,
                                                                **styles[token]))
        else:
            foreground = color_settings.get('setting', 'black')
            self.editor.StyleSetSpec(0, self._get_style_string(back=background,
                                                               fore=foreground))
        self.editor.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, background)
        self.editor.SetZoom(self._zoom_factor())
        self.editor.Refresh()

    def _get_word_and_length(self, current_position):
        word = self.editor.GetTextRange(current_position,
                                        self.editor.WordEndPosition(
                                            current_position,
                                            False))
        return word, len(word)

    def _get_style_string(self, back='#FFFFFF', fore='#000000', bold='', underline=''):
        settings = locals()
        settings.update(size=self._font_size())
        settings.update(face=self._font_face())
        return ','.join('%s:%s' % (name, value)
                        for name, value in settings.items() if value)

    def _ensure_default_font_is_valid(self):
        """Checks if default font is installed"""
        default_font = self._font_face()
        if default_font not in read_fonts():
            sys_font = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)
            self.settings[PLUGIN_NAME]['font face'] = sys_font.GetFaceName()

    def stylize(self):
        if not self.lexer:
            return
        self.editor.ConvertEOLs(2)
        shift = 0
        for position, token, value in self.lexer.get_tokens_unprocessed(self.editor.GetText()):
            if wx.VERSION < (4, 1, 0):
                self.editor.StartStyling(position + shift, 31)
            else:
                self.editor.StartStyling(position + shift)
            try:
                self.editor.SetStyling(len(value.encode('utf-8')), self.tokens[token])
                shift += len(value.encode('utf-8')) - len(value)
            except UnicodeEncodeError:
                self.editor.SetStyling(len(value), self.tokens[token])
                shift += len(value) - len(value)
