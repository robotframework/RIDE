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

from time import time
from io import StringIO, BytesIO
import string
import wx
from wx import stc
from robotide import robotapi
from robotide.context import IS_WINDOWS, IS_MAC
from robotide.controller.ctrlcommands import SetDataFile
from robotide.publish import RideSettingsChanged, PUBLISHER
from robotide.publish.messages import RideMessage
from robotide.namespace.suggesters import SuggestionSource, BuiltInLibrariesSuggester
from robotide.widgets import VerticalSizer, HorizontalSizer, ButtonWithHandler
from robotide.pluginapi import (Plugin, RideSaving, TreeAwarePluginMixin,
                                RideTreeSelection, RideNotebookTabChanging,
                                RideDataChanged, RideOpenSuite,
                                RideDataChangedToDirty)
from robotide.widgets import TextField, Label, HtmlDialog
from robotide.preferences.editors import ReadFonts
from wx.adv import HyperlinkCtrl, EVT_HYPERLINK
from .contentassist import ContentAssistTextEditor
from robotide.controller.filecontrollers import ResourceFileController
from robotide.controller.macrocontrollers import _WithStepsController

try:  # import installed version first
    import robotframeworklexer
except ImportError:
    try:  # then import local version
        from . import robotframeworklexer
    except ImportError:  # Pygments is not installed
        robotframeworklexer = None


class TextEditorPlugin(Plugin, TreeAwarePluginMixin):
    title = 'Text Edit'

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._editor_component = None

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
        if IS_MAC: # Mac needs this key binding
            self.register_shortcut('CtrlCmd-A', focused(lambda e: self._editor.select_all()))
        if IS_WINDOWS or IS_MAC: # Linux does not need this key binding
            self.register_shortcut('CtrlCmd-V', focused(lambda e: self._editor.paste()))
        self.register_shortcut('CtrlCmd-Z', focused(lambda e: self._editor.undo()))
        self.register_shortcut('CtrlCmd-Y', focused(lambda e: self._editor.redo()))
        # self.register_shortcut('Del', focused(lambda e: self._editor.delete()))
        self.register_shortcut('CtrlCmd-3', focused(lambda e: self._editor.execute_comment(e)))
        self.register_shortcut('CtrlCmd-4', focused(lambda e: self._editor.execute_uncomment(e)))
        self.register_shortcut('CtrlCmd-F', lambda e: self._editor._search_field.SetFocus())
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
        self._open()

    def _open(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            self._open_data_for_controller(datafile_controller)
            self._editor.store_position()

    def OnSaving(self, message):
        if self.is_focused():
            self._editor.save()
            self._editor.GetFocus(None)
        else:
            self._open()  # Was saved from other Editor

    def OnDataChanged(self, message):
        if self._should_process_data_changed_message(message):
            if isinstance(message, RideOpenSuite):
                self._editor.reset()
                self._editor.set_editor_caret_position()
            if self._editor.dirty and not self._apply_txt_changes_to_model():
                return
            self._refresh_timer.Start(500, True)
            # For performance reasons only run after all the data changes

    def _on_timer(self, event):
        self._editor.store_position()
        self._open_tree_selection_in_editor()
        event.Skip()

    def _should_process_data_changed_message(self, message):
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
            self._editor._editor.readonly = not message.item.datafile_controller.is_modifiable()
        self._editor._editor.SetReadOnly(self._editor._editor.readonly)
        self._editor._editor.stylizer._set_styles(self._editor._editor.readonly)
        self._editor._editor.Update()

    def _open_tree_selection_in_editor(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            self._editor.open(DataFileWrapper(datafile_controller, self.global_settings))
            self._editor._editor.readonly = not datafile_controller.is_modifiable()
        self._editor.set_editor_caret_position()

    def _open_data_for_controller(self, datafile_controller):
        self._editor.selected(DataFileWrapper(datafile_controller, self.global_settings))
        self._editor._editor.readonly = not datafile_controller.is_modifiable()

    def OnTabChange(self, message):
        if message.newtab == self.title:
            self._register_shortcuts()
            self._open()
            self._editor.set_editor_caret_position()
            self._set_read_only(self._editor._editor.readonly)
        elif message.oldtab == self.title:
            self._editor.remove_and_store_state()
            self.unregister_actions()
            self._editor_component.save()

    def OnTabChanged(self, event):
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


class DummyController(_WithStepsController):

    _populator = robotapi.UserKeywordPopulator
    filename = ""

    def _init(self, data=None):
        self._data = data

    def get_local_variables(self):
        return {}

    def __eq__(self, other):
        if self is other:
            return True
        if other.__class__ != self.__class__:
            return False
        return self._data == other._data

    def __hash__(self):
        return hash(repr(self))


class DataValidationHandler(object):

    def __init__(self, plugin):
        self._plugin = plugin
        self._last_answer = None
        self._last_answer_time = 0

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
        self._editor.set_editor_caret_position()
        return True

    def _sanity_check(self, data, text):
        formatted_text = data.format_text(text)
        c = self._normalize(formatted_text)
        e = self._normalize(text)
        return len(c) == len(e)

    def _normalize(self, text):
        for item in tuple(string.whitespace) + ('...', '*'):
            if item in text:
                text = text.replace(item, '')
        return text

    def _handle_sanity_check_failure(self):
        if self._last_answer == wx.ID_NO and \
        time() - self._last_answer_time <= 0.2:
            self._editor._mark_file_dirty()
            return False
        # TODO: use widgets.Dialog
        id = wx.MessageDialog(self._editor,
                              'ERROR: Data sanity check failed!\n'
                              'Reset changes?',
                              'Can not apply changes from Txt Editor',
                              style=wx.YES|wx.NO).ShowModal()
        self._last_answer = id
        self._last_answer_time = time()
        if id == wx.ID_YES:
            self._editor._revert()
            return True
        else:
            self._editor._mark_file_dirty()
        return False


class DataFileWrapper(object): # TODO: bad class name

    def __init__(self, data, settings):
        self._data = data
        self._settings = settings

    def __eq__(self, other):
        if other is None:
            return False
        return self._data == other._data

    def update_from(self, content):
        self._data.execute(SetDataFile(self._create_target_from(content)))

    def _create_target_from(self, content):
        src = BytesIO(content.encode("utf-8"))
        target = self._create_target()
        FromStringIOPopulator(target).populate(src)
        return target

    def format_text(self, text):
        return self._txt_data(self._create_target_from(text))

    def mark_data_dirty(self):
        self._data.mark_dirty()

    def mark_data_pristine(self):
        self._data.unmark_dirty()

    def _create_target(self):
        data = self._data.data
        target_class = type(data)
        if isinstance(data, robotapi.TestDataDirectory):
            target = robotapi.TestDataDirectory(source=self._data.directory)
            target.initfile = data.initfile
            return target
        return target_class(source=self._data.source)

    @property
    def content(self):
        return self._txt_data(self._data.data)

    def _txt_data(self, data):
        output = StringIO()
        data.save(output=output, format='txt',
                  txt_separating_spaces=self._settings.get(
                      'txt number of spaces', 4))
        return output.getvalue()  # DEBUG .decode('utf-8')


class SourceEditor(wx.Panel):

    def __init__(self, parent, title, data_validator):
        wx.Panel.__init__(self, parent)
        self._syntax_colorization_help_exists = False
        self._data_validator = data_validator
        self._data_validator.set_editor(self)
        self._parent = parent
        self._title = title
        self._tab_size = self._parent._app.settings.get(
                      'txt number of spaces', 4)
        self._create_ui(title)
        self._data = None
        self._dirty = 0  # 0 is False and 1 is True, when changed on this editor
        self._position = None
        self._showing_list = False
        self._tab_open = None
        # self._autocomplete = None
        self._controller_for_context = None
        PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)
        PUBLISHER.subscribe(self.OnTabChange, RideNotebookTabChanging)

    def is_focused(self):
        # foc = wx.Window.FindFocus()
        # return any(elem == foc for elem in [self]+list(self.GetChildren()))
        return self._tab_open == self._title

    def OnTabChange(self, message):
        self._tab_open = message.newtab

    def _create_ui(self, title):
        cnt = self._parent.GetPageCount()
        if cnt >= 0:
            editor_created = False
            while cnt > 0 and not editor_created:
                cnt -= 1
                editor_created = self._parent.GetPageText(cnt) == self._title  # TODO: Later we can adjust for several Text Editor tabs
            if not editor_created:
                self.SetSizer(VerticalSizer())
                self._create_editor_toolbar()
                self._create_editor_text_control()
                self._parent.add_tab(self, title, allow_closing=False)

    def _create_editor_toolbar(self):
        # needs extra container, since we might add helper
        # text about syntax colorization
        self.editor_toolbar = HorizontalSizer()
        default_components = HorizontalSizer()
        default_components.add_with_padding(
            ButtonWithHandler(self, 'Apply Changes', handler=lambda
                e: self.save()))
        self._create_search(default_components)
        self.editor_toolbar.add_expanding(default_components)
        self.Sizer.add_expanding(self.editor_toolbar, propotion=0)

    def _create_search(self, container_sizer):
        container_sizer.AddSpacer(20)
        self._search_field = TextField(self, '', process_enters=True)
        self._search_field.Bind(wx.EVT_TEXT_ENTER, self.OnFind)
        container_sizer.add_with_padding(self._search_field)
        container_sizer.add_with_padding(
            ButtonWithHandler(self, 'Search', handler=self.OnFind))
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

    def show_help_dialog(self, event):
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
        <a href='http://pythonhosted.org/an_example_pypi_project/setuptools.html#installing-setuptools-and-easy-install'>follow
        these instructions</a>.
        </p>
        <p>
        For more information about installing Pygments, <a href='http://pygments.org/download/'>see the site</a>.
        </p>
        """
        HtmlDialog("Getting syntax colorization", content).Show()

    def store_position(self, force=False):
        if self._editor and self.datafile_controller:
            cur_pos = self._editor.GetCurrentPos()
            if cur_pos > 0:  # Cheating because it always go to zero
                self._position = cur_pos
                self._editor.GotoPos(self._position)

    def set_editor_caret_position(self):
        if not self.is_focused():  # DEBUG was typing text when at Grid Editor
            return
        position = self._position
        self._editor.SetFocus()
        if position:
            self._editor.SetCurrentPos(position)
            self._editor.SetSelection(position, position)
            self._editor.SetAnchor(position)
            self._editor.GotoPos(position)
            self._editor.Refresh()
            self._editor.Update()

    @property
    def dirty(self):
        return self._dirty

    @property
    def datafile_controller(self):
        return self._data._data if self._data else None

    def OnFind(self, event):
        if self._editor:
            text = self._editor.GetSelectedText()
            if len(text)>0 and text.lower() != self._search_field.GetValue().lower():
                self._search_field.SelectAll()
                self._search_field.Clear()
                self._search_field.Update()
                self._search_field.SetValue(text)
                self._search_field.SelectAll()
                self._search_field.Update()
            self._find()

    def OnFindBackwards(self, event):
        if self._editor:
            self._find(forward=False)

    def _find(self, forward=True):
        txt = self._search_field.GetValue().encode('utf-8')
        position = self._find_text_position(forward, txt)
        self._show_search_results(position, txt)

    # FIXME: This must be cleaned up
    def _find_text_position(self, forward, txt):
        file_end = len(self._editor.utf8_text)
        search_end = file_end if forward else 0
        anchor = self._editor.GetAnchor()
        anchor += 1 if forward else 0
        position = self._editor.FindText(anchor, search_end, txt, 0)
        if position == -1:
            start, end = (0, file_end) if forward else (file_end - 1, 0)
            position = self._editor.FindText(start, end, txt, 0)
        return position

    def _show_search_results(self, position, txt):
        if position != -1:
            self._editor.SetCurrentPos(position)
            self._editor.SetSelection(position, position + len(txt))
            self._editor.ScrollToLine(self._editor.GetCurrentLine())
            self._search_field_notification.SetLabel('')
        else:
            self._search_field_notification.SetLabel('No matches found.')

    def OnContentAssist(self, event):
        self._showing_list = False
        #if not self.is_focused():
        #    return
        self.store_position()
        selected = self._editor.get_selected_or_near_text()
        sugs = [s.name for s in self._suggestions.get_suggestions(
            selected or '')]
        if sugs:
            self._editor.AutoCompSetDropRestOfWord(True)
            self._editor.AutoCompSetSeparator(ord(';'))
            self._editor.AutoCompShow(0, ";".join(sugs))
            self._showing_list = True

    def open(self, data):
        # print(f"DEBUG: Textedit enter open")
        self.reset()
        self._data = data
        # print(f"DEBUG: Textedit in open before getting SuggestionSource {self._data._data}\n Type data is {type(self._data._data)}")
        try:
            if isinstance(self._data._data, ResourceFileController):
                # from robotide.namespace import Namespace
                # self._namespace = Namespace(self._editor._settings)
                # self._namespace.get_resource(self._data._data.source)
                self._controller_for_context = DummyController(self._data._data, self._data._data)
                # print(f"DEBUG: Textedit in before getting to RESOURCE")
                self._suggestions = SuggestionSource(None,self._controller_for_context)
            else:
                self._suggestions = SuggestionSource(None, self._data._data.tests[0])
            # print(f"DEBUG: Textedit in open After getting SuggestionSource")
        except IndexError:  # It is a new project, no content yet
            # print(f"DEBUG: Textedit in open Exception SuggestionSource")
            self._controller_for_context = DummyController(self._data._data, self._data._data)
            self._suggestions = SuggestionSource(None, self._controller_for_context)
            # self._suggestions = SuggestionSource(None, BuiltInLibrariesSuggester())
        if not self._editor:
            self._stored_text = self._data.content
        else:
            self._editor.set_text(self._data.content)
            self.set_editor_caret_position()

    def selected(self, data):
        if not self._editor:
            self._create_editor_text_control(self._stored_text)
        if self._data == data:
            return
        self.open(data)

    def auto_ident(self):
        # if not self.is_focused():
        #    return
        line, _ = self._editor.GetCurLine()
        lenline = len(line)
        linenum = self._editor.GetCurrentLine()
        if lenline > 0:
            idx = 0
            while idx<lenline and line[idx] == ' ':
                idx += 1
            tsize = idx // self._tab_size
            if 3 < idx < lenline and line.strip().startswith("FOR"):
                tsize += 1
            elif linenum > 0 and tsize == 0:  # Advance if first task/test case or keyword
                prevline = self._editor.GetLine(linenum-1).lower()
                if prevline.startswith("**") and not ("variables" in prevline
                or "settings" in prevline):
                    tsize = 1
            self._editor.NewLine()
            while tsize > 0:
                self.write_ident()
                tsize -= 1
        else:
            self._editor.NewLine()
        pos = self._editor.GetCurrentLine()
        self._editor.SetCurrentPos(self._editor.GetLineEndPosition(pos))
        self.store_position()

    def deindent_block(self):
        start, end = self._editor.GetSelection()
        caret = self._editor.GetCurrentPos()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        count = 0
        self._editor.SelectNone()
        line = ini_line
        inconsistent = False
        self._editor.BeginUndoAction()
        while line <= end_line:
            inconsistent = False
            pos = self._editor.PositionFromLine(line)
            self._editor.SetCurrentPos(pos)
            self._editor.SetSelection(pos, pos)
            self._editor.SetInsertionPoint(pos)
            content = self._editor.GetRange(pos, pos + self._tab_size)
            if content == (' ' * self._tab_size):
                self._editor.DeleteRange(pos, self._tab_size)
                count += 1
                line += 1
            else:
                inconsistent = True
                break
        self._editor.EndUndoAction()
        if inconsistent:
            self._editor.Undo()
            return
        new_start = max(0, start - self._tab_size)
        new_end = max(0, end - (count * self._tab_size))
        if caret == start:
            ini = new_start
            fini = new_end
        else:
            ini = new_end
            fini = new_start
        self._editor.SetSelection(new_start, new_end)
        self._editor.SetCurrentPos(ini)
        self._editor.SetAnchor(fini)

    def indent_block(self):
        start, end = self._editor.GetSelection()
        caret = self._editor.GetCurrentPos()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        count = 0
        self._editor.SelectNone()
        line = ini_line
        while line <= end_line:
            pos = self._editor.PositionFromLine(line)
            self._editor.SetCurrentPos(pos)
            self._editor.SetSelection(pos, pos)
            self._editor.SetInsertionPoint(pos)
            self.write_ident()
            count += 1
            line += 1
        new_start = start + self._tab_size
        new_end = end + (count * self._tab_size)
        if caret == start:
            ini = new_start
            fini = new_end
        else:
            ini = new_end
            fini = new_start
        self._editor.SetSelection(new_start, new_end)
        self._editor.SetCurrentPos(ini)
        self._editor.SetAnchor(fini)

    def write_ident(self):
        spaces = ' ' * self._tab_size
        self._editor.WriteText(spaces)

    def reset(self):
        self._dirty = 0

    def save(self, *args):
        self.store_position()
        if self.dirty and not self._data_validator.validate_and_update(
                self._data, self._editor.utf8_text):
            return False
        self.reset()
        self.GetFocus(None)
        return True

    """
    # DEBUG Code not in use
    def delete(self):
        if IS_WINDOWS:
            # print(f"DEBUG: Delete called")
            if self._editor.GetSelectionStart() == self._editor.GetSelectionEnd():
                self._editor.CharRight()
            self._editor.DeleteBack()
        self._mark_file_dirty(self._editor.GetModify())
    """

    def cut(self):
        self._editor.Cut()
        self._mark_file_dirty(self._editor.GetModify())

    def copy(self):
        self._editor.Copy()

    def paste(self):
        focus = wx.Window.FindFocus()
        if focus == self._editor:
            self._editor.Paste()
        elif focus == self._search_field:
            self._search_field.Paste()
        self._mark_file_dirty(self._editor.GetModify())

    def select_all(self):
        self._editor.SelectAll()

    def undo(self):
        self._editor.Undo()
        self.store_position()
        self._mark_file_dirty(self._editor.GetModify())

    def redo(self):
        self._editor.Redo()
        self.store_position()
        self._mark_file_dirty(self._editor.GetModify())

    def remove_and_store_state(self):
        if self._editor:
            self.store_position()
            self._stored_text = self._editor.GetText()

    def _create_editor_text_control(self, text=None):
        self._editor = RobotDataEditor(self)
        self.Sizer.add_expanding(self._editor)
        self.Sizer.Layout()
        if text is not None:
            self._editor.set_text(text)
        self._editor.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self._editor.Bind(wx.EVT_CHAR, self.OnChar)
        self._editor.Bind(wx.EVT_KEY_UP, self.OnEditorKey)
        self._editor.Bind(wx.EVT_KILL_FOCUS, self.LeaveFocus)
        self._editor.Bind(wx.EVT_SET_FOCUS, self.GetFocus)
        # TODO Add here binding for keyword help

    def LeaveFocus(self, event):
        self._editor.AcceptsFocusFromKeyboard()
        self.store_position()
        self._editor.SetCaretPeriod(0)

    def GetFocus(self, event):
        self._editor.SetFocus()
        self._editor.AcceptsFocusFromKeyboard()
        self._editor.SetCaretPeriod(500)
        if self._position:
            self.set_editor_caret_position()
        if event:
            event.Skip()

    def _revert(self):
        self.reset()
        self._editor.set_text(self._data.content)

    def OnEditorKey(self, event):
        # if not self.is_focused():  # DEBUG was typing text when at Grid Editor
        #    self.GetFocus(event)
        #    print(f"DEBUG: EditorKey Got Focus")
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE:  # DEBUG on Windows we only get here, single Text Editor
            selected = self._editor.GetSelection()
            if selected[0] == selected[1]:
                pos = self._editor.GetInsertionPoint()
                if pos != self._editor.GetLastPosition():
                    self._editor.DeleteRange(selected[0], 1)
            else:
                self._editor.DeleteRange(selected[0], selected[1] - selected[0])
        self._mark_file_dirty(self._editor.GetModify())
        if keycode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            # print(f"DEBUG: Enter released {keycode}")
            return
        event.Skip()

    def OnKeyDown(self, event):
        # if not self.is_focused():
        #    self.GetFocus(event)
        #    print(f"DEBUG: KeyDown Got Focus")
        keycode = event.GetUnicodeKey()
        if event.GetKeyCode() == wx.WXK_DELETE:
            # print(f"DEBUG: Delete pressed {event.GetKeyCode()}")  # Code never reached on Windows
            return
        if event.GetKeyCode() == wx.WXK_TAB and not event.ControlDown() and not event.ShiftDown():
            if self._showing_list:  # Allows to use Tab for keyword selection
                self._showing_list = False
                event.Skip()
                return
            selected = self._editor.GetSelection()
            if selected[0] == selected[1]:
                self.write_ident()
            else:
                self.indent_block()
        elif event.GetKeyCode() == wx.WXK_TAB and event.ShiftDown():
            selected = self._editor.GetSelection()
            if selected[0] == selected[1]:
                pos = self._editor.GetCurrentPos()
                self._editor.SetCurrentPos(max(0, pos - self._tab_size))
                self.store_position()
                if not event.ControlDown():  # No text selection
                    pos = self._editor.GetCurrentPos()
                    self._editor.SetSelection(pos, pos)
            else:
                self.deindent_block()
        elif event.GetKeyCode() in [ wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER ]:
            if not self._showing_list:
                self.auto_ident()
            else:
                self._showing_list = False
                event.Skip()
        elif keycode in (ord('1'), ord('2'), ord('5')) and event.ControlDown():
            self.execute_variable_creator(list_variable=(keycode == ord('2')),
                                          dict_variable=(keycode == ord('5')))
            self.store_position()
        else:
            event.Skip()

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
        from_, to_ = self._editor.GetSelection()
        text = self._editor.SelectedText
        size = len(bytes(text, encoding='utf-8'))
        to_ = from_ + size
        if list_variable:
            symbol = '@'
        elif dict_variable:
            symbol = '&'
        else:
            symbol = '$'
        if size == 0:
            self._editor.SetInsertionPoint(to_)
            self._editor.InsertText(from_, self._variable_creator_value(symbol))
            self._editor.SetInsertionPoint(from_ + 2)
        else:
            self._editor.DeleteRange(from_, size)
            self._editor.SetInsertionPoint(from_)
            self._editor.ReplaceSelection(self._variable_creator_value(symbol, text))
            self._editor.SetSelection(from_ + 2, from_ + size + 2)

    @staticmethod
    def _variable_creator_value(symbol, value=''):
        return symbol + '{' + value + '}'

    def execute_enclose_text(self, keycode):
        from_, to_ = self._editor.GetSelection()
        text = self._editor.SelectedText
        size = len(bytes(text, encoding='utf-8'))
        to_ = from_ + size
        if size == 0:
            self._editor.SetInsertionPoint(to_)
            self._editor.InsertText(from_, self._enclose_text(keycode))
            pos = self._editor.GetCurrentPos()
            self._editor.SetSelection(pos + 1, pos + 1)
        else:
            self._editor.DeleteRange(from_, size)
            self._editor.SetInsertionPoint(from_)
            self._editor.ReplaceSelection(self._enclose_text(keycode, text))
            self._editor.SetSelection(from_ + 1, from_ + size + 1)

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
        return open_symbol+value+close_symbol

    def execute_comment(self, event):
        cursor = self._editor.GetCurrentPos()
        line, pos = self._editor.GetCurLine()
        spaces = ' ' * self._tab_size
        comment = 'Comment' + spaces
        cpos = cursor + len(comment)
        lenline = len(line)
        if lenline > 0:
            idx = 0
            while idx<lenline and line[idx] == ' ':
                idx += 1
            self._editor.InsertText(cursor - pos + idx, comment)
        else:
            self._editor.InsertText(cursor, comment)
        self._editor.SetCurrentPos(cpos)
        self._editor.SetSelection(cpos, cpos)
        self.store_position()

    def execute_uncomment(self, event):
        cursor = self._editor.GetCurrentPos()
        line, pos = self._editor.GetCurLine()
        spaces = ' ' * self._tab_size
        comment = 'Comment' + spaces
        cpos = cursor - len(comment)
        lenline = len(line)
        if lenline > 0:
            idx = 0
            while idx<lenline and line[idx] == ' ':
                idx += 1
            if (line[idx:len(comment) + idx]).lower() == comment.lower():
                self._editor.DeleteRange(cursor - pos + idx, len(comment))
                self._editor.SetCurrentPos(cpos)
                self._editor.SetSelection(cpos, cpos)
                self.store_position()

    def OnSettingsChanged(self, data):
        """Update tab size if txt spaces size setting is modified"""
        _, setting = data.keys
        if setting == 'txt number of spaces':
            self._tab_size = self._parent._app.settings.get('txt number of spaces', 4)

    def _mark_file_dirty(self, dirty=True):
        if self._data:
            if dirty:
                self._data.mark_data_dirty()
                self._dirty = 1
            elif self._dirty == 1:
                self._data.mark_data_pristine()
                self._dirty = 0


class RobotDataEditor(stc.StyledTextCtrl):
    margin = 1

    def __init__(self, parent, readonly=False):
        stc.StyledTextCtrl.__init__(self, parent)
        self._settings = parent._parent._app.settings
        self.readonly=readonly
        self.SetMarginType(self.margin, stc.STC_MARGIN_NUMBER)
        self.SetLexer(stc.STC_LEX_CONTAINER)
        self.SetReadOnly(True)
        self.SetUseTabs(False)
        self.SetTabWidth(parent._tab_size)
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
        self.stylizer.stylize()

    def OnZoom(self, event):
        self.SetMarginWidth(self.margin, self.calc_margin_width())
        self._set_zoom()

    def _set_zoom(self):
        new = self.GetZoom()
        old = self._settings['Text Edit'].get('zoom factor', 0)
        if new != old:
            self._settings['Text Edit'].set('zoom factor', new)

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


class FromStringIOPopulator(robotapi.FromFilePopulator):

    def populate(self, content):
        robotapi.TxtReader().read(content, self)


class RobotStylizer(object):
    def __init__(self, editor, settings, readonly=False):
        self.editor = editor
        self.lexer = None
        self.settings = settings
        self._readonly = readonly
        self._ensure_default_font_is_valid()
        if robotframeworklexer:
            self.lexer = robotframeworklexer.RobotFrameworkLexer()
        else:
            self.editor.GetParent().create_syntax_colorization_help()
        self._set_styles(self._readonly)
        PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)

    def OnSettingsChanged(self, data):
        '''Redraw the colors if the color settings are modified'''
        section, setting = data.keys
        if section == 'Text Edit':
            self._set_styles(self._readonly)  # TODO: When on read-only file changing background color ignores flag

    def _font_size(self):
        return self.settings['Text Edit'].get('font size', 10)

    def _font_face(self):
        return self.settings['Text Edit'].get('font face', 'Courier New')

    def _zoom_factor(self):
        return self.settings['Text Edit'].get('zoom factor', 0)

    def _set_styles(self, readonly=False):
        color_settings = self.settings.get_without_default('Text Edit')
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
                bkg = (max(160, bkg[0]-80), max(160, bkg[1]-80),
                       max(160, bkg[2]-80))
            else:
                bkg = (min(255, bkg[0]+180), min(255, bkg[1]+180),
                       min(255, bkg[2]+180))
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
            self.tokens = {}
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
        '''Checks if default font is installed'''
        default_font = self._font_face()
        if default_font not in ReadFonts():
            sys_font = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)
            self.settings['Text Edit']['font face'] = sys_font.GetFaceName()

    def stylize(self):
        if not self.lexer:
            return
        self.editor.ConvertEOLs(2)
        shift = 0
        for position, token, value in self.lexer.get_tokens_unprocessed(self.editor.GetText()):
            if wx.VERSION < (4, 1, 0):
                self.editor.StartStyling(position+shift, 31)
            else:
                self.editor.StartStyling(position + shift)
            try:
                self.editor.SetStyling(len(value.encode('utf-8')), self.tokens[token])
                shift += len(value.encode('utf-8'))-len(value)
            except UnicodeEncodeError:
                self.editor.SetStyling(len(value), self.tokens[token])
                shift += len(value) - len(value)
