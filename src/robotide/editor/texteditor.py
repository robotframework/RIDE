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
try:
    from StringIO import StringIO
except ImportError:  # py3
    from io import StringIO, BytesIO
import string
import wx
from wx import stc

from robotide import robotapi
from robotide.context import IS_WINDOWS, IS_MAC
from robotide.controller.ctrlcommands import SetDataFile
from robotide.publish import RideSettingsChanged, PUBLISHER
from robotide.publish.messages import RideMessage
from robotide.utils import PY2
from robotide.namespace.suggesters import (SuggestionSource,
                                           BuiltInLibrariesSuggester)
from robotide.widgets import VerticalSizer, HorizontalSizer, ButtonWithHandler
from robotide.pluginapi import (Plugin, RideSaving, TreeAwarePluginMixin,
                                RideTreeSelection, RideNotebookTabChanging,
                                RideDataChanged, RideOpenSuite,
                                RideDataChangedToDirty)
from robotide.widgets import TextField, Label, HtmlDialog
from robotide.preferences.editors import ReadFonts


if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
    from wx.adv import HyperlinkCtrl, EVT_HYPERLINK
else:
    from wx import HyperlinkCtrl, EVT_HYPERLINK

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
        if not self._editor_component:
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
        self.register_shortcut('Del', focused(lambda e: self._editor.delete()))
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
            # self.show_tab(self._editor)
            self._editor.store_position()

    def OnSaving(self, message):
        # print("DEBUG: Text Edit onsave enter")
        if self.is_focused():
            # print("DEBUG: Text Edit onsave is with focus")
            self._editor.save()
            self._editor.GetFocus(None)
            # print("DEBUG: Text Edit onsave leave with focus")
        else:
            # print("DEBUG: Text Edit ENTER onsave from other Editor")
            self._open()  # Was saved from other Editor
            # print("DEBUG: Text Edit onsave from other Editor")

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
        # DEBUG self._editor.set_editor_caret_position()
        event.Skip()

    def _should_process_data_changed_message(self, message):
        return isinstance(message, RideDataChanged) and \
               not isinstance(message, RideDataChangedToDirty)

    def OnTreeSelection(self, message):
        self._editor.store_position()
        if self.is_focused():
            next_datafile_controller = message.item and\
                                       message.item.datafile_controller
            if self._editor.dirty and not self._apply_txt_changes_to_model():
                if self._editor.datafile_controller !=\
                        next_datafile_controller:
                    self.tree.select_controller_node(
                        self._editor.datafile_controller)
                self._editor.set_editor_caret_position()
                return
            if next_datafile_controller:
                self._open_data_for_controller(next_datafile_controller)
            self._editor.set_editor_caret_position()
        else:
            self._editor.GetFocus(None)

    def _open_tree_selection_in_editor(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            self._editor.open(DataFileWrapper(datafile_controller,
                                              self.global_settings))
        self._editor.set_editor_caret_position()

    def _open_data_for_controller(self, datafile_controller):
        self._editor.selected(DataFileWrapper(datafile_controller,
                                              self.global_settings))

    def OnTabChange(self, message):
        if message.newtab == self.title:
            self._register_shortcuts()
            self._open()
            self._editor.set_editor_caret_position()
        elif message.oldtab == self.title:
            # print("DEBUG: OnTabChange move to another from Text Editor.")
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
        # print("DEBUG: self.notebook.current_page_title %s == self.title %s" % (self.notebook.current_page_title, self.title))
        return self.notebook.current_page_title == self.title


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
        # print("DEBUG: updating text")  # %s" % (self._editor.GetCurrentPos()))
        data.update_from(m_text)
        # print("DEBUG: AFTER updating text")
        self._editor.set_editor_caret_position()
        # %s" % (self._editor.GetCurrentPos()))
        return True

    def _sanity_check(self, data, text):
        formatted_text = data.format_text(text)
        c = self._normalize(formatted_text)
        e = self._normalize(text)
        return len(c) == len(e)

    def _normalize(self, text):
        for item in tuple(string.whitespace) + ('...', '*'):
            if item in text:
                # print("DEBUG: _normaliz item %s txt %s" % (item, text))
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
        if PY2:
            src = StringIO(content.encode("utf-8"))
        else:   # DEBUG because Apply Changes
            src = BytesIO(content.encode("utf-8"))
        target = self._create_target()
        FromStringIOPopulator(target).populate(src)
        return target

    def format_text(self, text):
        return self._txt_data(self._create_target_from(text))

    def mark_data_dirty(self):
        self._data.mark_dirty()

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
        self._dirty = False
        self._position = None
        self._tab_open = None
        PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)
        PUBLISHER.subscribe(self.OnTabChange, RideNotebookTabChanging)

    def is_focused(self):
        # foc = wx.Window.FindFocus()
        # return any(elem == foc for elem in [self]+list(self.GetChildren()))
        return self._tab_open == self._title

    def OnTabChange(self, message):
        self._tab_open = message.newtab

    def _create_ui(self, title):
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
            # ins_pos = self._editor.GetInsertionPoint()
            if cur_pos > 0:  # Cheating because it always go to zero
                # self._positions[self.datafile_controller.name] = cur_pos
                self._position = cur_pos
                # self._editor.SetAnchor(self._editor.GetCurrentPos())
                self._editor.GotoPos(self._position)
            # print("DEBUG: Called store caret self.datafile_controller.name=%s position=%s, ins_po=%s" % (self.datafile_controller.name, self._position, ins_pos))

    def set_editor_caret_position(self):
        if not self.is_focused():  # DEBUG was typing text when at Grid Editor
            # print("DEBUG: Text Edit avoid set caret pos")
            return
        # position = self._positions.get(self.datafile_controller.name, 0)
        position = self._position
        self._editor.SetFocus()
        if position:
            self._editor.SetCurrentPos(position)
            self._editor.SetSelection(position, position)
            self._editor.SetAnchor(position)
            self._editor.GotoPos(position)
            # ins_pos = self._editor.GetInsertionPoint()
            # linewithcursor = self._editor.GetCurrentLine()
            # print("DEBUG: Called set caret position=%s line %s" % (position, linewithcursor,) )
            # self._editor.ScrollToLine(linewithcursor)
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
            # print("DEBUG: Find text:%s" % text)
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
        # print("DEBUG: Content assist called Focused: %s" % self.is_focused())
        if not self.is_focused():
            return
        #  if wx.Window.FindFocus() is self._editor:
        self.store_position()
        # self._editor.SetAnchor(self._editor.GetCurrentPos())
        selected = self._editor.get_selected_or_near_text()
        sugs = [s.name for s in self._suggestions.get_suggestions(
            selected or '')]
        if sugs:
            # caretpos = self._editor.AutoCompPosStart() # Never used :(
            self._editor.AutoCompSetDropRestOfWord(True)
            self._editor.AutoCompSetSeparator(ord(';'))
            self._editor.AutoCompShow(0, ";".join(sugs))
        # event.Skip()

    def open(self, data):
        self.reset()
        self._data = data
        try:
            self._suggestions = SuggestionSource(None, data._data.tests[0])
        except IndexError:  # It is a new project, no content yet
            self._suggestions = SuggestionSource(None,
                                                 BuiltInLibrariesSuggester())
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

    def reset(self):
        self._dirty = False

    def save(self, *args):
        self.store_position()
        if self.dirty and not self._data_validator.validate_and_update(
                self._data, self._editor.utf8_text):
            return False
        self.GetFocus(None)  # DEBUG
        return True

    def delete(self):
        if IS_WINDOWS:
            if self._editor.GetSelectionStart() == self._editor.GetSelectionEnd():
                self._editor.CharRight()
            self._editor.DeleteBack()

    def cut(self):
        self._editor.Cut()

    def copy(self):
        self._editor.Copy()

    def paste(self):
        focus = wx.Window.FindFocus()
        if focus == self._editor:
            self._editor.Paste()
        elif focus == self._search_field:
            self._search_field.Paste()

    def select_all(self):
        self._editor.SelectAll()

    def undo(self):
        self._editor.Undo()
        self.store_position()

    def redo(self):
        self._editor.Redo()
        self.store_position()

    def remove_and_store_state(self):
        if self._editor:
            self.store_position()
            self._stored_text = self._editor.GetText()
            # self._editor.Destroy()  # DEBUG Pressing F8 would crash
            # self._editor = None

    def _create_editor_text_control(self, text=None):
        self._editor = RobotDataEditor(self)
        self.Sizer.add_expanding(self._editor)
        self.Sizer.Layout()
        if text is not None:
            self._editor.set_text(text)
        self._editor.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self._editor.Bind(wx.EVT_KEY_UP, self.OnEditorKey)
        self._editor.Bind(wx.EVT_KILL_FOCUS, self.LeaveFocus)
        self._editor.Bind(wx.EVT_SET_FOCUS, self.GetFocus)
        # self._editor.Bind(wx.EVT_CHILD_FOCUS, self.GetFocus)
        # TODO Add here binding for keyword help

    def LeaveFocus(self, event):
        self._editor.AcceptsFocusFromKeyboard()
        self.store_position()
        self._editor.SetCaretPeriod(0)
        # self.save()

    def GetFocus(self, event):
        self._editor.SetFocus()
        self._editor.AcceptsFocusFromKeyboard()
        self._editor.SetCaretPeriod(500)
        if self._position:
            self.set_editor_caret_position()
            # innerfocus = self._editor.GetSTCFocus()
            # print("DEBUG: Get Focus: %s STCfocus is: %s" % (self.is_focused(), innerfocus))
        if event:
            event.Skip()

    def _revert(self):
        self.reset()
        self._editor.set_text(self._data.content)

    def OnEditorKey(self, event):
        #print("DEBUG: Text Edit enter keypress")
        if not self.is_focused():  # DEBUG was typing text when at Grid Editor
            # print("DEBUG: Text Edit skip keypress")
            return
        if not self.dirty and self._editor.GetModify():
            # print("DEBUG: Text Edit keyup Marked Dirty")
            self._mark_file_dirty()
        event.Skip()

    def OnKeyDown(self, event):
        if not self.is_focused():
            self.GetFocus(None)
            # DEBUG return
        # Process Tab key
        if event.GetKeyCode() == wx.WXK_TAB and not event.ControlDown() and not event.ShiftDown():
            spaces = ' ' * self._tab_size
            self._editor.WriteText(spaces)
        elif event.GetKeyCode() == wx.WXK_TAB and event.ShiftDown():
            pos = self._editor.GetCurrentPos()
            self._editor.SetCurrentPos(max(0, pos - self._tab_size))
            self.store_position()
            if not event.ControlDown(): # No text selection
                pos = self._editor.GetCurrentPos()
                self._editor.SetSelection(pos, pos)
        # elif event.GetKeyCode() == wx.WXK_SPACE and event.ControlDown():  # Process Ctrl-Space on MacOS too
        #    self.OnContentAssist()
        #    print("DEBUG: Text Edit called ContentAssist")
        else:
            event.Skip()

    def OnSettingsChanged(self, data):
        """Update tab size if txt spaces size setting is modified"""
        _, setting = data.keys
        if setting == 'txt number of spaces':
            self._tab_size = self._parent._app.settings.get(
                      'txt number of spaces', 4)

    def _mark_file_dirty(self):
        if self._data:
            self._dirty = True
            self._data.mark_data_dirty()


class RobotDataEditor(stc.StyledTextCtrl):
    margin = 1

    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent)
        self._settings = parent._parent._app.settings
        self.SetMarginType(self.margin, stc.STC_MARGIN_NUMBER)
        self.SetLexer(stc.STC_LEX_CONTAINER)
        self.SetReadOnly(True)
        self.Bind(stc.EVT_STC_STYLENEEDED, self.OnStyle)
        self.Bind(stc.EVT_STC_ZOOM, self.OnZoom)
        self.stylizer = RobotStylizer(self, self._settings)

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
    def __init__(self, editor, settings):
        self.editor = editor
        self.lexer = None
        self.settings = settings
        self._ensure_default_font_is_valid()
        if robotframeworklexer:
            self.lexer = robotframeworklexer.RobotFrameworkLexer()
        else:
            self.editor.GetParent().create_syntax_colorization_help()
        self._set_styles()
        PUBLISHER.subscribe(self.OnSettingsChanged, RideSettingsChanged)

    def OnSettingsChanged(self, data):
        '''Redraw the colors if the color settings are modified'''
        section, setting = data.keys
        if section == 'Text Edit':
            self._set_styles()

    def _font_size(self):
        return self.settings['Text Edit'].get('font size', 10)

    def _font_face(self):
        return self.settings['Text Edit'].get('font face', 'Courier New')

    def _zoom_factor(self):
        return self.settings['Text Edit'].get('zoom factor', 0)

    def _set_styles(self):
        color_settings = self.settings.get_without_default('Text Edit')
        background = color_settings.get('background', '#FFFFFF')
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
            self.editor.StartStyling(position+shift, 31)
            # DEBUG Solution for non-utf-8 like emojii, 'surrogateescape')
            try:
                self.editor.SetStyling(len(value.encode('utf-8')), self.tokens[token])
                shift += len(value.encode('utf-8'))-len(value)
            except UnicodeEncodeError:
                self.editor.SetStyling(len(value), self.tokens[token])
                shift += len(value) - len(value)
