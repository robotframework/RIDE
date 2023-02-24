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
from ..controller.ctrlcommands import SetDataFile
from ..controller.filecontrollers import ResourceFileController
from ..controller.macrocontrollers import _WithStepsController
from ..namespace.suggesters import SuggestionSource
from ..pluginapi import Plugin, TreeAwarePluginMixin
from ..publish.messages import (RideSaving, RideTreeSelection, RideNotebookTabChanging, RideDataChanged, RideOpenSuite,
                                RideDataChangedToDirty)
from ..preferences.editors import ReadFonts
from ..publish import RideSettingsChanged, PUBLISHER
from ..publish.messages import RideMessage
from ..widgets import TextField, Label, HtmlDialog
from ..widgets import VerticalSizer, HorizontalSizer, ButtonWithHandler, RIDEDialog

try:  # import installed version first
    from pygments.lexers import robotframework as robotframeworklexer
except ImportError:
    robotframeworklexer = None


class TextEditorPlugin(Plugin, TreeAwarePluginMixin):
    title = 'Text Edit'

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
        if IS_MAC: # Mac needs this key binding
            self.register_shortcut('CtrlCmd-A', focused(lambda e: self._editor.select_all()))
        if IS_WINDOWS or IS_MAC: # Linux does not need this key binding
            self.register_shortcut('CtrlCmd-V', focused(lambda e: self._editor.paste()))
        self.register_shortcut('CtrlCmd-Z', focused(lambda e: self._editor.undo()))
        self.register_shortcut('CtrlCmd-Y', focused(lambda e: self._editor.redo()))
        # self.register_shortcut('Del', focused(lambda e: self._editor.delete()))
        self.register_shortcut('CtrlCmd-Shift-I', focused(lambda e: self._editor.insert_cell(e)))
        # self.register_shortcut('CtrlCmd-Shift-D', focused(lambda e: self._editor.delete_cell(e)))
        self.register_shortcut('Alt-Up', focused(lambda e: self._editor.move_row_up(e)))
        self.register_shortcut('Alt-Down', focused(lambda e: self._editor.move_row_down(e)))
        # self.register_shortcut('CtrlCmd-D', focused(lambda e: self._editor.delete_row(e)))
        self.register_shortcut('CtrlCmd-I', focused(lambda e: self._editor.insert_row(e)))
        self.register_shortcut('CtrlCmd-3', focused(lambda e: self._editor.execute_comment(e)))
        self.register_shortcut('CtrlCmd-Shift-3', focused(lambda e: self._editor.execute_sharp_comment(e)))
        self.register_shortcut('CtrlCmd-4', focused(lambda e: self._editor.execute_uncomment(e)))
        self.register_shortcut('CtrlCmd-Shift-4', focused(lambda e: self._editor.execute_sharp_uncomment(e)))
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
            # print(f"DEBUG: _open called and datafile_controller exist")
            self._open_data_for_controller(datafile_controller)
            self._editor.store_position()

    def OnSaving(self, message):
        if self.is_focused():
            self._editor.save()
            self._editor.GetFocus(None)
        else:
            # print(f"DEBUG: OnSaving open because was saved from other editor {message}")
            self._open()  # Was saved from other Editor

    def OnDataChanged(self, message):
        # print(f"DEBUG: OnDataChanged entering function {message}")
        if self._should_process_data_changed_message(message):
            if isinstance(message, RideOpenSuite):
                # print(f"DEBUG: OnDataChanged message {message}")
                self._editor.reset()
                self._editor.set_editor_caret_position()
            if isinstance(message, RideNotebookTabChanging):
                return
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
        # print(f"DEBUG: OnTreeSelection entering function {message}")
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
        try:
            datafile_controller = self.tree.get_selected_datafile_controller()
        except AttributeError:
            return
        if datafile_controller:
            # print(f"DEBUG: _open_tree_selection_in_editor going to open data")
            self._editor.open(DataFileWrapper(datafile_controller, self.global_settings))
            self._editor._editor.readonly = not datafile_controller.is_modifiable()
        self._editor.set_editor_caret_position()

    def _open_data_for_controller(self, datafile_controller):
        # print(f"DEBUG: _open_data_for_controller going to open data")
        self._editor.selected(DataFileWrapper(datafile_controller, self.global_settings))
        self._editor._editor.readonly = not datafile_controller.is_modifiable()

    def OnTabChange(self, message):
        # print(f"DEBUG: OnTabChange entering function {message}")
        if message.newtab == self.title:
            self._register_shortcuts()
            self._open()
            self._editor.set_editor_caret_position()
            try:
                self._set_read_only(self._editor._editor.readonly)
            except Exception:  # When using only Text Editor exists error in message topic
                pass
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
        # print(f"DEBUG: texteditor _apply_txt_changes_to_model going to RESET dirty={self._editor.dirty}")
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
        # print(f"DEBUG: validate ENTER type(text)={type(text)}")
        m_text = text.decode("utf-8")
        if not self._sanity_check(data, m_text):
            handled = self._handle_sanity_check_failure()
            if not handled:
                return False
        self._editor.reset()
        if self._editor._reformat:
            data.update_from(m_text)
        else:
            data.update_from(m_text)  # TODO: This is the same code as _reformat == True
            # There is no way to update the model without reformatting
            # TODO this only updates the editor, but not the model, changes in Text Editor are not reflected in Grid or
            # when saving
            #  self._editor._editor.set_text(m_text)
            # print(f"DEBUG: validate Non reformatting:")  # {m_text}")
        self._editor.set_editor_caret_position()
        return True

    def _sanity_check(self, data, text):
        # print(f"DEBUG: _sanity_check ENTER type(text)={type(text)}")
        # First remove all lines starting with #
        for line in text.split('\n'):
            comment = line.strip().startswith('#')
            # print(f"DEBUG: _sanity_check comment={comment} line={line}")
            if comment:
                text = text.replace(line, '')
        # print(f"DEBUG: _sanity_check cleaned text={text}")
        formatted_text = data.format_text(text)
        c = self._normalize(formatted_text)
        e = self._normalize(text)
        # print(f"DEBUG: _sanity_check compare c={c}\n e={e}")
        return len(c) == len(e)

    def _normalize(self, text):
        for item in tuple(string.whitespace) + ('...', '*'):
            if item in text:
                text = text.replace(item, '')
        return text

    def _handle_sanity_check_failure(self):
        if self._last_answer == wx.ID_NO and \
        time() - self._last_answer_time <= 0.2:
            # self._editor._mark_file_dirty(True)
            return False
        # TODO: use widgets.Dialog
        dlg = wx.MessageDialog(self._editor,
                              'ERROR: Data sanity check failed!\n'
                              'Reset changes?',
                              'Can not apply changes from Txt Editor',
                              style=wx.YES|wx.NO)
        dlg.InheritAttributes()
        """
        dlg.SetBackgroundColour(Colour(200, 222, 40))
        dlg.SetOwnBackgroundColour(Colour(200, 222, 40))
        dlg.SetForegroundColour(Colour(7, 0, 70))
        dlg.SetOwnForegroundColour(Colour(7, 0, 70))
        """
        # dlg.Refresh(True)
        id = dlg.ShowModal()
        self._last_answer = id
        self._last_answer_time = time()
        if id == wx.ID_YES:
            self._editor._revert()
            return True
        # else:
        #    self._editor._mark_file_dirty()
        return False


class DataFileWrapper(object): # TODO: bad class name

    def __init__(self, data, settings):
        self._data = data
        self._settings = settings
        self._tab_size = self._settings.get('txt number of spaces', 2) if self._settings else 2

    def __eq__(self, other):
        if other is None:
            return False
        return self._data == other._data

    def update_from(self, content):
        # print(f"DEBUG: ENTER update_from type self._data={type(self._data)}")
        self._data.execute(SetDataFile(self._create_target_from(content)))

    def _create_target_from(self, content):
        src = BytesIO(content.encode("utf-8"))
        target = self._create_target()
        FromStringIOPopulator(target).populate(src, self._tab_size)
        # print(f"DEBUG: After populate: type target={type(target)}")
        # print(f"DEBUG: After populate:\n{target.__reduce__()}")
        return target

    def format_text(self, text):
        return self._txt_data(self._create_target_from(text))

    def mark_data_dirty(self):
        self._data.mark_dirty()

    def mark_data_pristine(self):
        # print(f"DEBUG: texteditor mark_data_pristine calling unmark_dirty")
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
        # print(f"DEBUG: In _txt_data returning content {output.getvalue()}")
        return output.getvalue()  # DEBUG .decode('utf-8')


class SourceEditor(wx.Panel):

    def __init__(self, parent, title, data_validator):
        wx.Panel.__init__(self, parent)
        self.dlg = RIDEDialog()
        self.SetBackgroundColour(Colour(self.dlg.color_background))
        self.SetForegroundColour(Colour(self.dlg.color_foreground))
        self._syntax_colorization_help_exists = False
        self._data_validator = data_validator
        self._data_validator.set_editor(self)
        self._parent = parent
        self._title = title
        self._tab_size = self._parent._app.settings.get(
                      'txt number of spaces', 4)
        self._reformat = self._parent._app.settings.get('reformat', False)
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
        button = ButtonWithHandler(self, 'Apply Changes', handler=lambda e: self.save())
        button.SetBackgroundColour(Colour(self.dlg.color_secondary_background))
        button.SetForegroundColour(Colour(self.dlg.color_secondary_foreground))
        default_components.add_with_padding(button)
        self._create_search(default_components)
        self.editor_toolbar.add_expanding(default_components)
        self.Sizer.add_expanding(self.editor_toolbar, propotion=0)

    def _create_search(self, container_sizer):
        container_sizer.AddSpacer(20)
        self._search_field = TextField(self, '', process_enters=True)
        self._search_field.SetBackgroundColour(Colour(self.dlg.color_secondary_background))
        self._search_field.SetForegroundColour(Colour(self.dlg.color_secondary_foreground))
        self._search_field.Bind(wx.EVT_TEXT_ENTER, self.OnFind)
        container_sizer.add_with_padding(self._search_field)
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
        return self._dirty == 1 # self._editor.IsModified() and self._dirty == 1

    @property
    def datafile_controller(self):
        return self._data._data if self._data else None

    def OnFind(self, event):
        if self._editor:
            text = self._editor.GetSelectedText()
            if len(text) > 0 and text.lower() != self._search_field.GetValue().lower() and event.GetEventType() == wx.wxEVT_TOOL:
                # if a search string selected in text and CTRL+G is pressed
                # put the string into the _search_field
                self._search_field.SelectAll()
                self._search_field.Clear()
                self._search_field.Update()
                self._search_field.SetValue(text)
                self._search_field.SelectAll()
                self._search_field.Update()
                # and set the start position to the beginning of the editor
                self._editor.SetAnchor(0)
                self._editor.SetCurrentPos(0)
                self._editor.Update()

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
        # if text is found start end end of the found text is returned but we do need just starting position which is the first value
        if type(position) is tuple:
            position = position[0]

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
            # print(f"DEBUG: open not editor yet self._stored_text= {self._stored_text}")
        else:
            self._editor.set_text(self._data.content)
            # print(f"DEBUG: open ->existing editor set_text: {self._data.content}")
            self.set_editor_caret_position()

    def selected(self, data):
        if not self._editor:
            self._create_editor_text_control(self._stored_text)
        if self._data == data:
            return
        # print(f"DEBUG: selected going to open data")
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
            if idx < lenline and (line.strip().startswith("FOR") or line.strip().startswith("IF")
                                      or line.strip().startswith("ELSE")):
                tsize += 1
                # print(f"DEBUG: SourceEditor auto_indent after block kw tsize={tsize} linenum={linenum}")
            elif linenum > 0 and tsize == 0:  # Advance if first task/test case or keyword
                prevline = self._editor.GetLine(linenum-1).lower()
                if prevline.startswith("**") and not ("variables" in prevline or "settings" in prevline):
                    tsize = 1
                elif prevline.startswith("\n"):
                    tsize = 1
            elif line.strip().startswith("END"):
                pos = self._editor.GetCurrentPos()
                self._editor.SetCurrentPos(pos)
                self._editor.SetSelection(pos, pos)
                self.deindent_block()
                tsize -= 1
                # print(f"DEBUG: SourceEditor auto_indent after END block kw tsize={tsize} linenum={linenum}")
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

    def indent_line(self, line):
        if line > 0:
            pos = self._editor.PositionFromLine(line)
            text = self._editor.GetLine(line-1)
            lenline = len(text)
            if lenline > 0:
                idx = 0
                while idx < lenline and text[idx] == ' ':
                    idx += 1
                tsize = idx // self._tab_size
                if idx < lenline and (text.strip().startswith("FOR") or text.strip().startswith("IF")
                                      or text.strip().startswith("ELSE") or text.strip().startswith("TRY")
                                      or text.strip().startswith("EXCEPT") or text.strip().startswith("WHILE")):
                    tsize += 1
                elif tsize == 0:
                    text = text.lower()
                    if text.startswith("**"):
                        if not ("variables" in text or "settings" in text):
                            tsize = 1
                self._editor.SetCurrentPos(pos)
                self._editor.SetSelection(pos, pos)
                self._editor.SetInsertionPoint(pos)
                for _ in range(tsize):
                    self.write_ident()

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
        # print(f"DEBUG: textedit enter RESET calling _mark_file_dirty")
        self._dirty = 0
        self._mark_file_dirty(False)

    def save(self, *args):
        # print(f"DEBUG: enter save path={self.datafile_controller.source}")
        self.store_position()
        if self.dirty:
            if not self._data_validator.validate_and_update(self._data, self._editor.utf8_text):
                return False
        # DEBUG: Was resetting when leaving editor
        # self.reset()
        self.GetFocus(None)
        return True

    """
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
        # print(f"DEBUG: TextEditor calling dirty from Undo self._dirty={self._dirty}")
        self._mark_file_dirty(self._dirty == 1 and self._editor.GetModify())

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
        if keycode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            # print(f"DEBUG: Enter released {keycode}")
            return
        if self.is_focused() and keycode != wx.WXK_CONTROL and self._dirty == 0:
            # print(f"DEBUG: texteditor OnKeyDown calling _mark_file_dirty  event={event}")
            self._mark_file_dirty(self._editor.GetModify())
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

    def move_row_up(self, event):
        start, end = self._editor.GetSelection()
        cursor = self._editor.GetCurrentPos()
        ini_line = self._editor.LineFromPosition(start)
        # selection not on top?
        if ini_line > 0:
            end_line = self._editor.LineFromPosition(end)
            # get the previous row content and length
            rowabove = self._editor.GetLine(ini_line-1)
            lenabove = len(rowabove.encode('utf-8'))
            # get the content of the block rows
            rowselblock = ''
            rowcnt = ini_line
            while rowcnt <= end_line:
                rowselblock += self._editor.GetLine(rowcnt)
                rowcnt += 1
            # add the content of previous row
            rowselblock += rowabove
            begpos = self._editor.PositionFromLine(ini_line-1)
            endpos = self._editor.PositionFromLine(end_line+1)
            self._editor.Replace(begpos, endpos, rowselblock)
            self._editor.SetSelection(begpos, endpos-lenabove-1)
            # TODO: recalculate line identation for new position and old
            #print(f"DEBUG: move_row_up Variables: select start={start}, end={end} cursor={cursor}"
            #    f" ini_line={ini_line} end_line={end_line} begpos={begpos} endpos={endpos} lenabove={lenabove}")

    def move_row_down(self, event):
        start, end = self._editor.GetSelection()
        cursor = self._editor.GetCurrentPos()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        # get the next row content and length
        rowbelow = self._editor.GetLine(end_line+1)
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
            rowselblock += self._editor.GetLine(rowcnt)
            rowcnt += 1
        begpos = self._editor.PositionFromLine(ini_line)
        endpos = self._editor.PositionFromLine(end_line+2)
        self._editor.Replace(begpos, endpos, rowselblock)
        self._editor.SetSelection(begpos+lenbelow, endpos-1)
        # TODO: recalculate line identation for new position and old
        #print(f"DEBUG: move_row_down Variables: select start={start}, end={end} cursor={cursor}"
        #    f" ini_line={ini_line} end_line={end_line} begpos={begpos} endpos={endpos} lenbelow={lenbelow}")

    def delete_row(self, event):
        start, end = self._editor.GetSelection()
        cursor = self._editor.GetCurrentPos()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        begpos = self._editor.PositionFromLine(ini_line)
        self._editor.SelectNone()
        # print(f"DEBUG: delete_row Variables: select start={start}, end={end} cursor={cursor}"
        #       f" ini_line={ini_line} end_line={end_line} begpos={begpos} endpos={endpos}")
        if start == end:
            end_line = ini_line
        for line in range(ini_line, end_line + 1):
            self._editor.GotoLine(ini_line)
            self._editor.LineDelete()
        # cursor position when doing block select is always the end of the selection
        if ini_line != end_line:
            self._editor.SetCurrentPos(begpos)
            self._editor.SetAnchor(begpos)
        else:
            self._editor.SetCurrentPos(cursor)
            self._editor.SetAnchor(cursor)
        self.store_position()

    def insert_row(self, event):
        start, end = self._editor.GetSelection()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        delta = end_line - ini_line
        positionfromline = self._editor.PositionFromLine(ini_line)
        self._editor.SelectNone()
        self._editor.InsertText(positionfromline, '\n')
        for nl in range(delta):
            self._editor.InsertText(positionfromline + nl, '\n')
        self._editor.SetCurrentPos(positionfromline)
        self._editor.SetAnchor(positionfromline)
        self._editor.GotoLine(ini_line)
        self.indent_line(ini_line)
        self.store_position()

    def execute_comment(self, event):
        start, end = self._editor.GetSelection()
        cursor = self._editor.GetCurrentPos()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        spaces = ' ' * self._tab_size
        comment = 'Comment' + spaces
        cpos = cursor + len(comment)
        count = 0
        self._editor.SelectNone()
        row = ini_line
        # print(f"DEBUG: execute_comment Variables: select start={start}, end={end} cursor={cursor}"
        #      f" ini_line={ini_line} end_line={end_line} positionfromline={self._editor.PositionFromLine(row)}")
        while row <= end_line:
            pos = self._editor.PositionFromLine(row)
            self._editor.SetCurrentPos(pos)
            self._editor.SetSelection(pos, pos)
            self._editor.SetInsertionPoint(pos)
            line = self._editor.GetLine(row)
            lenline = len(line)
            # print(f"DEBUG: execute_comment Line={line}: pos={pos}, row={row} lenline={lenline}")
            if lenline > 0:
                idx = 0
                while idx < lenline and line[idx] == ' ':
                    idx += 1
                self._editor.InsertText(pos + idx, comment)
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
        self._editor.SetSelection(new_start, new_end)
        self._editor.SetCurrentPos(ini)
        self._editor.SetAnchor(fini)
        self.store_position()

    def execute_uncomment(self, event):
        start, end = self._editor.GetSelection()
        cursor = self._editor.GetCurrentPos()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        spaces = ' ' * self._tab_size
        comment = 'Comment' + spaces
        commentlong = 'BuiltIn.Comment' + spaces
        cpos = cursor - len(comment)
        self._editor.SelectNone()
        count = 0
        row = ini_line
        while row <= end_line:
            pos = self._editor.PositionFromLine(row)
            self._editor.SetCurrentPos(pos)
            self._editor.SetSelection(pos, pos)
            self._editor.SetInsertionPoint(pos)
            line = self._editor.GetLine(row)
            lenline = len(line)
            if lenline > 0:
                idx = 0
                while idx<lenline and line[idx] == ' ':
                    idx += 1
                if (line[idx:len(comment) + idx]).lower() == comment.lower():
                    self._editor.DeleteRange(pos + idx, len(comment))
                if (line[idx:len(commentlong) + idx]).lower() == commentlong.lower():
                    self._editor.DeleteRange(pos + idx, len(commentlong))
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
        self._editor.SetSelection(new_start, new_end)
        self._editor.SetCurrentPos(ini)
        self._editor.SetAnchor(fini)
        self.store_position()

    def insert_cell(self, event):
        start, end = self._editor.GetSelection()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        begpos = self._editor.PositionFromLine(ini_line)
        begend = self._editor.PositionFromLine(ini_line+1)
        endpos = self._editor.PositionFromLine(end_line+1)
        # print(f"DEBUG: insert_cell Variables: select start={start}, end={end}"
        #     f" ini_line={ini_line} end_line={end_line} begpos={begpos} endpos={endpos}")
        cell_no_beg = self._get_cell_no(begpos, endpos, start)
        cell_pos_beg = self._get_position_of_cell(begpos, endpos, cell_no_beg)
        # if there is a selection subtract 1 from endpos to circumvent cursor being on end of cell
        # --> otherwise no will be next cell no
        if start != end:
            cell_no_end = self._get_cell_no(begpos, endpos, end-1)
        else:
            cell_no_end = cell_no_beg
        #  print(f"DEBUG: cell range to handle beg={cell_no_beg} end={cell_no_end}")
        celltab = ' ' * self._tab_size
        # If the selection spans more than one line:
        if ini_line < end_line:   # TODO: do inserts in such a way that they can be undone in 1 undo
            new_start = cell_pos_beg
            for line in range(ini_line, end_line+1):
                begthis = self._editor.PositionFromLine(line)
                endthis = self._editor.PositionFromLine(line+1)
                cell_pos_beg = self._get_position_of_cell(begthis, endthis, cell_no_beg)
                self._editor.InsertText(cell_pos_beg, celltab)
            new_end = cell_pos_beg + (len(celltab.encode('utf-8')))
        elif start == end:  # On a single row, no selection
            # print(f"DEBUG: insert 1 cell before cell={cell_no_beg} on line={ini_line}")
            self._editor.InsertText(cell_pos_beg, celltab)
            new_start = cell_pos_beg
            new_end = cell_pos_beg + len(celltab.encode('utf-8'))
        else:  # On a single row, with selection
            cells_to_insert = cell_no_end - cell_no_beg + 1
            #  print(f"DEBUG: insert {cells_to_insert} cell(s) before cell={cell_no_beg} on line={ini_line}")
            # insert at once so undo handles it correct
            self._editor.InsertText(cell_pos_beg, celltab * cells_to_insert)
            new_start = cell_pos_beg
            new_end = cell_pos_beg + (len(celltab.encode('utf-8')) * cells_to_insert)
        # SetSelection and SetCurrentPos + Store_position overrule each other so only use one of them
        self._editor.SetSelection(new_start, new_end)
        # @Helio: SetAnchor overrules the SetSelection if it specifies a different start than SetSelection (but I left your code for now)
        self._editor.SetAnchor(new_end)

    def delete_cell(self, event):
        start, end = self._editor.GetSelection()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        begpos = self._editor.PositionFromLine(ini_line)
        begend = self._editor.PositionFromLine(ini_line+1)
        endpos = self._editor.PositionFromLine(end_line+1)
        #print(f"DEBUG: delete_cell Variables: select start={start}, end={end}"
        #     f" ini_line={ini_line} end_line={end_line} begpos={begpos} endpos={endpos}")
        cell_no_beg = self._get_cell_no(begpos, endpos, start)
        cell_pos_beg = self._get_position_of_cell(begpos, endpos, cell_no_beg)
        # if there is a selection subtract 1 from endpos to circumvent cursor being on end of cell
        # --> otherwise no will be next cell no
        if start != end:
            cell_no_end = self._get_cell_no(begpos, endpos, end-1)
        else:
            cell_no_end = cell_no_beg
        cell_pos_end = self._get_position_of_cell(begpos, endpos, cell_no_end+1)
        #print(f"DEBUG: cell range to handle beg={cell_no_beg} end={cell_no_end} begpos_begcell={cell_pos_beg} endpos_endcell={cell_pos_end}")
        # If the selection spans more than one line:
        if ini_line < end_line:
            self._editor.Remove(cell_pos_beg, cell_pos_end)
            new_start = cell_pos_beg
            new_end = new_start + (end - start)
        elif start == end:  # On a single row, no selection
            self._editor.Remove(cell_pos_beg, cell_pos_end)
            new_start = cell_pos_beg
            new_end = new_start + (end - start)
        else:  # On a single row, with selection
            self._editor.Remove(cell_pos_beg, cell_pos_end)
            new_start = cell_pos_beg
            new_end = new_start + (end - start)
        # SetSelection and SetCurrentPos + Store_position overrule each other so only use one of them
        #print(f"DEBUG: new range {new_start} to {new_end}")
        self._editor.SetSelection(new_start, new_end)
        # @Helio: SetAnchor overrules the SetSelection if it specifies a different start than SetSelection
        # I am not sure what any selection should be after deleting big ranges
        self._editor.SetAnchor(new_start)

    def _get_cell_no(self, begpos, endpos, findpos):
        # get cell number from range begpos-endpos using findpos 
        cell_no = 0
        celltot = self._get_number_of_cells(begpos, endpos)
        while cell_no < celltot:
            cell_no += 1
            cellpos = self._get_position_of_cell(begpos, endpos, cell_no)
            #print(f"DEBUG loop: celltot={celltot} cell_no={cell_no} cellpos={cellpos} findpos={findpos}")
            if cellpos > findpos:
                cell_no -= 1
                break
        return cell_no

    def _get_number_of_cells(self, begpos, endpos):
        # get number of cells in range begpos-endpos
        # Warning! GetStringSelection does not work properly if there are diacritics in the content above (!) the selected range
        the_content = self._editor.GetTextRange(begpos, endpos)
        celltab = ' ' * self._tab_size
        return the_content.count(celltab)

    def _get_position_of_cell(self, begpos, endpos, cell_no):
        # get position of cell number within range begpos-endpos 
        # TODO: this does not work correctly if first cell within the range is totally empty (so not as \ sanitized)
        cellpos = 0
        cellcnt = self._get_number_of_cells(begpos, endpos)
        #print(f"DEBUG: cellcnt={cellcnt} cell_no={cell_no}")
        if cell_no <= cellcnt:    # encode is needed for finding correct position when there are special characters in the content
            celltab = ' ' * self._tab_size
            cellencode = celltab.encode('utf-8')
            # Warning! GetStringSelection does not work properly if there are diacritics in the content above (!) the selected range
            textrange = self._editor.GetTextRange(begpos, endpos)
            textencode = textrange.encode('utf-8')
            fndcnt = 1  # begpos is always in a cell
            fndidx = 0
            while fndidx != -1:
                fndidx = textencode.find(cellencode, fndidx)
                #print(f"DEBUG searched: fndidx={fndidx} text={textencode}")
                if fndidx != -1:
                    if fndcnt == 1 and fndidx == 0:    # check if begpos is at the beginning of a cell
                        fndcnt -= 1
                    fndcnt += 1
                    if cell_no == fndcnt:
                        cellpos = begpos + fndidx
                        break
                    fndidx += 1   # for next search
        else:  # cell_no does not exist -- return endpos-1
            cellpos = endpos-1
        #print(f"DEBUG cellpos: cellpos={cellpos}")
        return cellpos

    def execute_sharp_comment(self, event):
        start, end = self._editor.GetSelection()
        cursor = self._editor.GetCurrentPos()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        spaces = ' ' * self._tab_size
        count = 0
        maxsize = self._editor.GetLineCount()
        # If the selection spans on more than one line:
        if ini_line < end_line:
            for line in range(ini_line, end_line+1):
                count += 1
                if line < maxsize:
                    self._editor.GotoLine(line)
                else:
                    self._editor.GotoLine(maxsize)
                pos = self._editor.PositionFromLine(line)
                self._editor.SetCurrentPos(pos)
                self._editor.SetSelection(pos, pos)
                self._editor.SetInsertionPoint(pos)
                row = self._editor.GetLine(line)
                lenline = len(row)
                if lenline > 0:
                    idx = 0
                    while idx < lenline and row[idx] == ' ':
                        idx += 1
                    self._editor.InsertText(pos + idx, '# ')
        elif start == end:  # On a single row, no selection
            count += 1
            pos = self._editor.PositionFromLine(ini_line)
            row = self._editor.GetLine(ini_line)
            lenline = len(row)
            if lenline > 0:
                idx = 0
                while idx < lenline and row[idx] == ' ':
                    idx += 1
                self._editor.InsertText(pos + idx, '# ')
        else:  # On a single row, with selection
            count += 1
            pos = self._editor.PositionFromLine(ini_line)
            row = self._editor.GetLine(ini_line)
            if cursor > pos:
                idx = cursor - pos
                while idx >= len(spaces):
                    if row[idx-len(spaces):idx] != spaces:
                        idx -= 1
                    else:
                        break
                if idx < len(spaces):
                    idx = 0
                self._editor.InsertText(pos + idx, '# ')
        new_start = start
        new_end = end + (count * 2)
        if cursor == start:
            ini = new_start
            fini = new_end
        else:
            ini = new_end
            fini = new_start
        self._editor.SetSelection(new_start, new_end)  # TODO: For some reason the selection is not restored!
        self._editor.SetCurrentPos(ini)
        self._editor.SetAnchor(fini)
        self._editor.SetCurrentPos(cursor + count * 2)
        self.store_position()

    def execute_sharp_uncomment(self, event):
        start, end = self._editor.GetSelection()
        cursor = self._editor.GetCurrentPos()
        ini_line = self._editor.LineFromPosition(start)
        end_line = self._editor.LineFromPosition(end)
        spaces = ' ' * self._tab_size
        # self._editor.SelectNone()
        count = 0
        maxsize = self._editor.GetLineCount()
        # If the selection spans on more than one line:
        if ini_line < end_line:
            for line in range(ini_line, end_line+1):
                pos = self._editor.PositionFromLine(line)
                row = self._editor.GetLine(line)
                lenline = len(row)
                if lenline > 0:
                    idx = 0
                    while idx < lenline and row[idx] == ' ':
                        idx += 1
                    size = 1
                    if idx + 1 < lenline and row[idx:idx+1] == '#':
                        if idx + 2 < lenline and row[idx+1:idx+2] == ' ':
                            size = 2
                        # Here we clean up escaped spaces from Apply
                        if idx + size < lenline:
                            newrow = row[idx + size:]
                            newrow = newrow.replace('\\ ', ' ')
                            size += len(row[idx:]) - len(newrow) - size
                            self._editor.DeleteRange(pos + idx, len(newrow) + size)
                            self._editor.InsertText(pos + idx, newrow)
                        count += size
        elif start == end:  # On a single row, no selection
            pos = self._editor.PositionFromLine(ini_line)
            row = self._editor.GetLine(ini_line)
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
                            self._editor.DeleteRange(pos + idx, len(newrow) + size)
                            self._editor.InsertText(pos + idx, newrow )
                        count += size
                    else:
                        idx += 1
        else:  # On a single row, with selection
            pos = self._editor.PositionFromLine(ini_line)
            row = self._editor.GetLine(ini_line)
            lenline = len(row)
            if cursor > pos:
                idx = cursor - pos
                while idx >= len(spaces):
                    if row[idx-len(spaces):idx] != spaces:
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
                            self._editor.DeleteRange(pos + idx, len(newrow) + size)
                            self._editor.InsertText(pos + idx, newrow)
                        count += size
                    else:
                        idx -= 1
        if count == 0:
            return
        new_start = start
        new_end = end - count
        if cursor == start:
            ini = new_start
            fini = new_end
        else:
            ini = new_end
            fini = new_start
        self._editor.SetSelection(new_start, new_end)  # TODO: For some reason the selection is not restored!
        self._editor.SetCurrentPos(cursor - count)
        self.store_position()

    def OnSettingsChanged(self, message):
        """Update tab size if txt spaces size setting is modified"""
        _, setting = message.keys
        if setting == 'txt number of spaces':
            self._tab_size = self._parent._app.settings.get('txt number of spaces', 4)
        if setting == 'reformat':
            self._reformat = self._parent._app.settings.get('reformat', False)

    def _mark_file_dirty(self, dirty=True):
        if not self.is_focused():  # DEBUG: Was marking file clean from Grid Editor
            return
        if self._data:
            if self._dirty == 0 and dirty:
                self._data.mark_data_dirty()
                self._dirty = 1
            elif self._dirty == 1:
                # print(f"DEBUG: texteditor _mark_file_dirty calling mark_data_pristine _dirty={self._dirty}")
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


class FromStringIOPopulator(robotapi.populators.FromFilePopulator):

    def populate(self, content, tab_size):
        # print(f"DEBUG: FromStringIOPopulator spaces={tab_size} populate:\n{content}")
        robotapi.RobotReader(spaces=tab_size).read(content, self)


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

    def OnSettingsChanged(self, message):
        '''Redraw the colors if the color settings are modified'''
        section, setting = message.keys
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
