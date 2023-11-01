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
from .popupwindow import HtmlPopupWindow
from . import _EDIT
from .. import robotapi
from ..context import IS_WINDOWS, IS_MAC
from ..controller.ctrlcommands import SetDataFile, INDENTED_START
from ..controller.filecontrollers import ResourceFileController
from ..controller.macrocontrollers import WithStepsController
from ..namespace.suggesters import SuggestionSource
from ..pluginapi import Plugin, action_info_collection, TreeAwarePluginMixin
from ..publish.messages import (RideSaved, RideTreeSelection, RideNotebookTabChanging, RideDataChanged, RideOpenSuite,
                                RideDataChangedToDirty, RideBeforeSaving, RideSaving, RideDataDirtyCleared)
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
        self._tab = None
        self._save_flag = 0  # See
        self.reformat = application.settings.get('reformat', False)
        self._register_shortcuts()

    @property
    def _editor(self):
        if self._editor_component is None:
            self._editor_component = SourceEditor(self, self.notebook,
                                                  self.title,
                                                  DataValidationHandler(self))
            self._refresh_timer = wx.Timer(self._editor_component)
            self._editor_component.Bind(wx.EVT_TIMER, self._on_timer)
        return self._editor_component

    def enable(self):
        self._tab = self._editor
        self.register_actions(action_info_collection(_EDIT, self._tab, self._tab))
        self.subscribe(self.on_tree_selection, RideTreeSelection)
        self.subscribe(self.on_data_changed, RideMessage)
        self.subscribe(self.on_tab_change, RideNotebookTabChanging)
        self.add_self_as_tree_aware_plugin()
        if self._editor.is_focused():
            self._register_shortcuts()
            self._open()

    def _register_shortcuts(self):
        def focused(func):
            def f(event):
                if self.is_focused() and self._editor.is_focused():
                    func(event)

            return f

        if IS_MAC:  # Mac needs this key binding
            self.register_shortcut('CtrlCmd-A', focused(lambda e: self._editor.select_all()))
        # No system needs this key binding, because is already global
        # self.register_shortcut('CtrlCmd-V', focused(lambda e: self._editor.paste()))
        self.register_shortcut('CtrlCmd-F', focused(lambda e: self._editor.search_field.SetFocus()))
        # To avoid double actions these moved to on_key_down
        # self.register_shortcut('CtrlCmd-G', focused(lambda e: self._editor.on_find(e)))
        # self.register_shortcut('CtrlCmd-Shift-G', focused(lambda e: self._editor.on_find_backwards(e)))
        self.register_shortcut('Ctrl-Space', lambda e: focused(self._editor.on_content_assist(e)))
        self.register_shortcut('CtrlCmd-Space', lambda e: focused(self._editor.on_content_assist(e)))
        self.register_shortcut('Alt-Space', lambda e: focused(self._editor.on_content_assist(e)))

    def disable(self):
        self.remove_self_from_tree_aware_plugins()
        self.unsubscribe_all()
        self.unregister_actions()
        self.delete_tab(self._editor)
        wx.CallLater(500, self.unregister_actions())
        self._tab = None
        self._editor_component = None

    def on_open(self, event):
        _ = event
        self._open()

    def _open(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            self._save_flag = 0
            """ DEBUG: To be used in Localization
            if hasattr(datafile_controller, 'preamble'):  # DEBUG: Is failing at resource files
                print(f"DEBUG: texteditor _open preamble={datafile_controller.preamble}")
            self._open_data_for_controller(datafile_controller)
            """
            self._editor.store_position()

    def on_data_changed(self, message):
        """ This block is now inside try/except to avoid errors from unit test """
        try:
            # print(f"DEBUG: textedit OnDataChanged message={message}")
            if self._should_process_data_changed_message(message):
                if isinstance(message, RideOpenSuite):  # Not reached
                    self._editor.reset()
                    self._editor.set_editor_caret_position()
                if isinstance(message, RideNotebookTabChanging):  # Not reached
                    return
                # Workaround for remarked dirty with Ctrl-S
                if self.is_focused() and self._save_flag == 0 and isinstance(message, RideSaving):
                    self._save_flag = 1
                if self.is_focused() and self._save_flag == 1 and isinstance(message, RideDataDirtyCleared):
                    self._save_flag = 2
                if self.is_focused() and self._save_flag == 2 and isinstance(message, RideSaved):
                    self._save_flag = 3
                    wx.CallAfter(self._editor.mark_file_dirty, False)
                # DEBUG: This is the unwanted chnge after saving but excluded in this block for performance
                # if self.is_focused() and self._save_flag == 3 and isinstance(message, RideDataChangedToDirty):
                #     self._save_flag = 4
                #     wx.CallAfter(self._editor.mark_file_dirty, False)
                if self.is_focused() and isinstance(message, RideBeforeSaving):
                    self._editor.is_saving = False
                    # Reset counter for Workaround for remarked dirty with Ctrl-S
                    self._save_flag = 0
                    self._apply_txt_changes_to_model()
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
        return isinstance(message, (RideDataChanged, RideBeforeSaving, RideSaved, RideSaving, RideDataDirtyCleared))\
                          and not isinstance(message, RideDataChangedToDirty)

    def on_tree_selection(self, message):
        self._editor.store_position()
        if self.is_focused():
            next_datafile_controller = message.item and message.item.datafile_controller
            if self._editor.datafile_controller == message.item.datafile_controller == next_datafile_controller:
                # print(f"DEBUG: OnTreeSelection Same FILE item type={type(message.item)}")
                self._editor.locate_tree_item(message.item)
                return
            if self._editor.dirty and not self._apply_txt_changes_to_model():
                if self._editor.datafile_controller != next_datafile_controller:
                    self.tree.select_controller_node(self._editor.datafile_controller)
                self._editor.set_editor_caret_position()
                return
            if next_datafile_controller:
                self._open_data_for_controller(next_datafile_controller)
                wx.CallAfter(self._editor.locate_tree_item, message.item)
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

    def on_tab_change(self, message):
        if message.newtab == self.title:
            self._open()
            self._editor.set_editor_caret_position()
            try:
                self._set_read_only(self._editor.source_editor.readonly)
            except Exception as e:  # DEBUG: When using only Text Editor exists error in message topic
                print(e)
        elif message.oldtab == self.title:
            self._editor.remove_and_store_state()
            self._editor_component.is_saving = False
            self._editor_component.content_save()

    def on_tab_changed(self, event):
        _ = event
        self._show_editor()
        event.Skip()

    def _apply_txt_changes_to_model(self):
        self._editor.is_saving = False
        if not self._editor.content_save():
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
        if self._editor.reformat:
            data.update_from(data.format_text(m_text))
        else:
            # DEBUG: This is the area where we will implement to not reformat code
            data.update_from(m_text)
            # There is no way to update the model without reformatting
            # DEBUG: this only updates the editor, but not the model, changes in Text Editor are not reflected
            # in Grid or when saving
            # self.source_editor.source_editor.set_text(m_text)
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
        if not self.wrapper_data.is_dirty:
            self.wrapper_data.mark_dirty()

    def mark_data_pristine(self):
        if self.wrapper_data.is_dirty:
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

    def __init__(self, plugin, parent, title, data_validator):
        wx.Panel.__init__(self, parent)
        self.dlg = RIDEDialog()
        self.SetBackgroundColour(Colour(self.dlg.color_background))
        self.SetForegroundColour(Colour(self.dlg.color_foreground))
        self._syntax_colorization_help_exists = False
        self._data_validator = data_validator
        self._data_validator.set_editor(self)
        self.source_editor_parent = parent
        self.plugin = plugin
        self.datafile = None
        self._title = title
        self.tab_size = self.source_editor_parent.app.settings.get(TXT_NUM_SPACES, 4)
        self.reformat = self.source_editor_parent.app.settings.get('reformat', False)
        self._create_ui(title)
        self._data = None
        self._position = 0  # Start at 0 if first time access
        self.restore_start_pos = self._position
        self.restore_end_pos = self._position
        self.restore_anchor = self._position
        self._showing_list = False
        self.autocomp_pos = None
        self._tab_open = self._title  # When starting standalone this was not being set
        self._controller_for_context = None
        self._suggestions = None
        self._stored_text = None
        self._ctrl_action = None
        self.is_saving = False  # To avoid double calls to save
        self.old_information_popup = None
        PUBLISHER.subscribe(self.on_settings_changed, RideSettingsChanged)
        PUBLISHER.subscribe(self.on_tab_change, RideNotebookTabChanging)

    def is_focused(self):
        # DEBUG: original method: foc = wx.Window.FindFocus()
        # DEBUG: any(elem == foc for elem in [self]+list(self.GetChildren()))
        return self._tab_open == self._title

    def on_tab_change(self, message):
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
        button = ButtonWithHandler(self, 'Apply Changes', handler=lambda e: self.content_save())
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
        self.search_field.Bind(wx.EVT_TEXT_ENTER, self.on_find)
        container_sizer.add_with_padding(self.search_field)
        button = ButtonWithHandler(self, 'Search', handler=self.on_find)
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
        Syntax colorization for Text Edit uses <a href='https://pygments.org/'>Pygments</a> syntax highlighter.
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
        <a 
        href='https://pythonhosted.org/an_example_pypi_project/setuptools.html#installing-setuptools-and-easy-install'
        >follow these instructions</a>.
        </p>
        <p>
        For more information about installing Pygments, <a href='https://pygments.org/download/'>see the site</a>.
        </p>
        """
        HtmlDialog("Getting syntax colorization", content).Show()

    def store_position(self, force=False):
        if self.source_editor:  # We don't necessarily need a data controller, was: "and self.datafile_controller:"
            cur_pos = self.source_editor.GetCurrentPos()
            self.restore_start_pos = self.source_editor.GetSelectionStart()
            self.restore_end_pos = self.source_editor.GetSelectionEnd()
            self.restore_anchor = self.source_editor.GetAnchor()
            if cur_pos > 0:  # Cheating because it always goes to zero
                self._position = cur_pos
                if force:
                    self.source_editor.GotoPos(self._position)

    def set_editor_caret_position(self):
        if not self.is_focused():  # DEBUG was typing text when at Grid Editor
            return
        position = self._position
        self.source_editor.SetFocus()
        if position:
            self.source_editor.SetCurrentPos(position)
            self.source_editor.SetSelection(self.restore_start_pos, self.restore_end_pos)
            self.source_editor.SetAnchor(self.restore_anchor)
            self.source_editor.GotoPos(position)
            self.source_editor.Refresh()
            self.source_editor.Update()

    @property
    def dirty(self):
        return self._data.wrapper_data.is_dirty if self._data else False

    @property
    def datafile_controller(self):
        return self._data.wrapper_data if self._data else None

    def on_find(self, event, forward=True):
        if self.source_editor:
            if event.GetEventType() != wx.wxEVT_TEXT_ENTER:  # Was getting selected item from Tree
                text = self.source_editor.GetSelectedText()
            else:
                text = ''
            if (len(text) > 0 and text.lower() != self.search_field.GetValue().lower() and
                    event.GetEventType() != wx.wxEVT_TOOL):
                # if a search string selected in text and CTRL+G is pressed
                # put the string into the search_field
                self.search_field.SelectAll()
                self.search_field.Clear()
                self.search_field.Update()
                self.search_field.SetValue(text)
                self.search_field.SelectAll()
                self.search_field.Update()
                if forward:
                    # and set the start position to the beginning of the editor
                    self.source_editor.SetAnchor(0)
                    self.source_editor.SetCurrentPos(0)
                    self.source_editor.Update()
            self._find(forward)

    def on_find_backwards(self, event):
        if self.source_editor:
            self.on_find(event, forward=False)

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

    def locate_tree_item(self, item):
        """ item is object received from message """
        from wx.stc import STC_FIND_REGEXP
        search_end = len(self.source_editor.utf8_text)
        section_start = 0
        name_to_locate = r'^'+item.name
        position = self.source_editor.FindText(section_start, search_end, name_to_locate, STC_FIND_REGEXP)
        # print(f"DEBUG: TextEditor locate_tree_item name_to_locate={name_to_locate} position={position}")
        if position[0] != -1:
            # DEBUG: Make colours configurable?
            self.source_editor.SetSelBackground(True, Colour('orange'))
            self.source_editor.SetSelForeground(True, Colour('white'))
            self.source_editor.SetFocus()
            self.source_editor.GotoPos(position[1]+1)
            self.source_editor.LineScrollUp()
            self.source_editor.SetCurrentPos(position[1])
            self.source_editor.SetAnchor(position[0])
            self.source_editor.SetSelection(position[0], position[1])
            self.source_editor.SetFocusFromKbd()
            self.source_editor_parent.SetFocus()
            self.source_editor.Update()

    def on_content_assist(self, event):
        """
        Produces an Auto Complete Suggestions list, from Scintilla. Based on selected content or nearby text.
        Always add actual imported libraries and resources keywords and BuiltIn.
        :param event: Not used
        :return:
        """
        if not self.is_focused():  # DEBUG was typing text when at Grid Editor
            return
        _ = event
        if self._showing_list:
            self._showing_list = False  # Avoid double calls
            return
        self.store_position()
        selected = self.source_editor.get_selected_or_near_text()
        self.set_editor_caret_position()
        sugs = []
        if selected:
            for start in selected:
                sugs.extend(s.name for s in self._suggestions.get_suggestions(start))
            # DEBUG: Here, if sugs is still [], then we can get all words from line and repeat suggestions
            # In another evolution, we can use database of words by frequency (considering future by project db)
        sel = [s for s in selected] if selected else []
        entry_word = sel[0].split('.')[-1].strip()
        length_entered = len(entry_word)  # Because Libraries prefixed
        sugs.extend(s.name for s in self._suggestions.get_suggestions(''))
        if len(sugs) > 0:
            sugs = [s for s in sugs if s != '']
        if sugs:
            self.source_editor.AutoCompSetDropRestOfWord(False)
            self.source_editor.AutoCompSetIgnoreCase(True)
            self.source_editor.AutoCompSetSeparator(ord(';'))
            self.source_editor.AutoCompShow(length_entered, ";".join(sugs))
            self.autocomp_pos = self.source_editor.AutoCompPosStart()
            self._showing_list = True
            # DEBUG: self.set_editor_caret_position()
            # Needs proper calculation of position to delete already suggestion.
            # This will be done when selection is effective at on_key_down
        """
        else:
            # self.set_editor_caret_position() # Restore selected text and caret
            self.source_editor.SetInsertionPoint(self._position)  # We should know if list was canceled or value change
        """

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
        if self.plugin.datafile:
            self.datafile = self.plugin.datafile
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
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
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
                line += 1
            else:
                inconsistent = True
                break
        self.source_editor.EndUndoAction()
        if inconsistent:
            self.source_editor.Undo()
            return
        tnew_start = self.source_editor.GetLineEndPosition(ini_line) - len(self.source_editor.GetLine(ini_line)) + 1
        tnew_end = self.source_editor.GetLineEndPosition(end_line)
        self.source_editor.SetSelection(tnew_start, tnew_end)
        self.source_editor.SetCurrentPos(tnew_end)
        self.source_editor.SetAnchor(tnew_start)

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

    def deindent_line(self, line):
        self.indent_line(line, reverse=True)

    def indent_line(self, line, reverse=False):
        last_line = self.source_editor.GetLineCount()
        if line > 0 and not reverse:
            pos = self.source_editor.PositionFromLine(line)
            text = self.source_editor.GetLine(line)
            lenline = len(text)
            if lenline > 0:
                self.source_editor.SetCurrentPos(pos)
                self.source_editor.SetSelection(pos, pos)
                self.source_editor.SetInsertionPoint(pos)
                self.source_editor.InsertText(pos, ' ' * self.tab_size)
        elif line < last_line and reverse:
            pos = self.source_editor.PositionFromLine(line)
            text = self.source_editor.GetLine(line)
            idx = self.first_non_space(text)
            if idx >= self.tab_size:
                self.source_editor.DeleteRange(pos, self.tab_size)

    def indent_block(self):
        start, end = self.source_editor.GetSelection()
        ini_line = self.source_editor.LineFromPosition(start)
        end_line = self.source_editor.LineFromPosition(end)
        self.source_editor.SelectNone()
        line = ini_line
        while line <= end_line:
            pos = self.source_editor.PositionFromLine(line)
            self.source_editor.SetCurrentPos(pos)
            self.source_editor.SetSelection(pos, pos)
            self.source_editor.SetInsertionPoint(pos)
            self.write_ident()
            line += 1
        tnew_start = self.source_editor.GetLineEndPosition(ini_line) - len(self.source_editor.GetLine(ini_line)) + 1
        tnew_end = self.source_editor.GetLineEndPosition(end_line)
        self.source_editor.SetSelection(tnew_start, tnew_end)
        self.source_editor.SetCurrentPos(tnew_end)
        self.source_editor.SetAnchor(tnew_start)

    def write_ident(self):
        spaces = ' ' * self.tab_size
        self.source_editor.WriteText(spaces)

    def reset(self):
        if self._data and not self._data.wrapper_data.is_dirty:
            self.mark_file_dirty(False)

    def content_save(self, *args):
        _ = args
        self.store_position()
        if self.dirty and not self.is_saving:
            self.is_saving = True
            if not self._data_validator.validate_and_update(self._data, self.source_editor.utf8_text):
                self.is_saving = False
                return False
        # self.GetFocus(None)
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
    # Callbacks taken from __init__.py
    def on_undo(self, event):
        _ = event
        self.undo()

    def on_redo(self, event):
        _ = event
        self.redo()

    def on_cut(self, event):
        _ = event
        self.cut()

    def on_copy(self, event):
        _ = event
        self.copy()

    def on_paste(self, event):
        _ = event
        self.paste()

    @staticmethod
    def on_insert(event):
        _ = event
        print(f"DEBUG: TextEditor called on_insert event={event}\n TO BE IMPLEMENTED")
        # self.insert_row()

    @staticmethod
    def on_delete(self, event=None):
        """ Not used """

    def on_insert_cells(self, event):
        self.insert_cell(event)

    def on_delete_cells(self, event):
        self.delete_cell(event)

    def on_comment_rows(self, event):
        self.execute_comment(event)

    def on_uncomment_rows(self, event):
        self.execute_uncomment(event)

    def on_sharp_comment_rows(self, event):
        self.execute_sharp_comment(event)

    def on_sharp_uncomment_rows(self, event):
        self.execute_sharp_uncomment(event)

    def on_comment_cells(self, event):
        self.execute_sharp_comment(event)

    def on_uncomment_cells(self, event):
        self.execute_sharp_uncomment(event)

    def on_insert_rows(self, event):
        self.insert_row(event)

    def on_delete_rows(self, event):
        wx.CallAfter(self.delete_row, event)

    def on_move_rows_up(self, event):
        self.move_row_up(event)

    def on_move_rows_down(self, event):
        self.move_row_down(event)

    def on_content_assistance(self, event):
        self.on_content_assist(event)

    def on_key(self, *args):
        """ Intentional override """
        pass

    def cut(self):
        self.source_editor.Cut()
        self.mark_file_dirty(self.source_editor.GetModify())

    def copy(self):
        self.source_editor.Copy()

    def paste(self):
        focus = wx.Window.FindFocus()
        if focus == self.source_editor:
            self.source_editor.Paste()
        self.mark_file_dirty(self.source_editor.GetModify())

    def select_all(self):
        self.source_editor.SelectAll()

    def undo(self):
        self.source_editor.Undo()
        self.store_position()
        self.mark_file_dirty(self.source_editor.GetModify())  # self._dirty == 1 and

    def redo(self):
        self.source_editor.Redo()
        self.store_position()
        self.mark_file_dirty(self.source_editor.GetModify())

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
        self._kw_doc_timer = wx.Timer(self.source_editor)
        self.source_editor.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self.source_editor.Bind(wx.EVT_CHAR, self.on_char)
        self.source_editor.Bind(wx.EVT_KEY_UP, self.on_editor_key)
        self.source_editor.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.source_editor.Bind(wx.EVT_KILL_FOCUS, self.LeaveFocus)
        self.source_editor.Bind(wx.EVT_SET_FOCUS, self.GetFocus)
        # DEBUG: Add here binding for keyword help

    def LeaveFocus(self, event):
        _ = event
        self.source_editor.hide_kw_doc()
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

    def on_editor_key(self, event):
        if not self.is_focused():
            event.Skip()
            return
        keycode = event.GetKeyCode()
        keyvalue = event.GetUnicodeKey()
        # print(f"DEBUG: TextEditor key up focused={self.is_focused()} modify {self.source_editor.GetModify()}")
        if keycode == wx.WXK_DELETE:  # DEBUG on Windows we only get here, single Text Editor
            selected = self.source_editor.GetSelection()
            if selected[0] == selected[1]:
                pos = self.source_editor.GetInsertionPoint()
                if pos != self.source_editor.GetLastPosition():
                    self.source_editor.DeleteRange(selected[0], 1)
            else:
                self.source_editor.DeleteRange(selected[0], selected[1] - selected[0])
            self.mark_file_dirty(self.source_editor.GetModify())
        if keycode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            self.mark_file_dirty(self.source_editor.GetModify())
            return
        if keyvalue == wx.WXK_NONE and keycode in [wx.WXK_CONTROL, wx.WXK_RAW_CONTROL]:
            self.source_editor.hide_kw_doc()
        if self.is_focused():  # DEBUG and keycode != wx.WXK_CONTROL and keyvalue >= ord(' ') and self.dirty:
            self.mark_file_dirty(self.source_editor.GetModify())
        event.Skip()

    def on_key_down(self, event):
        """
        Some events are also in registered actions, because they are caught by kweditor before reaching here.
        When we use on the Text Editor (Grid Editor plugin disables), we need to catch these keys. This is the
        case of Ctrl-(Shift)-3 and Ctrl-(Shift)-4.

        :param event:
        :return:
        """
        if not self.is_focused():
            event.Skip()
            return
        keycode = event.GetUnicodeKey()
        raw_key = event.GetKeyCode()
        # print(f"DEBUG: TextEditor on_key_down event={event} raw_key={raw_key} wx.WXK_C ={wx.WXK_CONTROL}")
        if event.GetKeyCode() == wx.WXK_DELETE:
            self.mark_file_dirty(self.source_editor.GetModify())
            return
        if raw_key != wx.WXK_CONTROL:  # We need to clear doc as soon as possible
            self.source_editor.hide_kw_doc()
        if event.GetKeyCode() == wx.WXK_TAB and not event.ControlDown() and not event.ShiftDown():
            if self._showing_list:  # Allows to use Tab for keyword selection
                self._showing_list = False
                wx.CallAfter(self.write_ident)  # DEBUG: Make this configurable?
                event.Skip()
                self.mark_file_dirty(self.source_editor.GetModify())
                return
            selected = self.source_editor.GetSelection()
            if selected[0] == selected[1]:
                self.write_ident()
            else:
                self.indent_block()
            self.mark_file_dirty(self.source_editor.GetModify())
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
                self.mark_file_dirty(self.source_editor.GetModify())
        elif event.GetKeyCode() in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            if not self._showing_list:
                self.auto_indent()
            else:
                self._showing_list = False
                wx.CallAfter(self.write_ident)  # DEBUG: Make this configurable?
                event.Skip()
            self.mark_file_dirty(self.source_editor.GetModify())
        elif keycode in (ord('1'), ord('2'), ord('5')) and event.ControlDown():
            self.execute_variable_creator(list_variable=(keycode == ord('2')),
                                          dict_variable=(keycode == ord('5')))
            self.store_position()
            self.mark_file_dirty(self.source_editor.GetModify())
        elif (not IS_WINDOWS and not IS_MAC and keycode in (ord('v'), ord('V'))
              and event.ControlDown() and not event.ShiftDown()):
            # We need to ignore this in Linux, because it does double-action
            self.mark_file_dirty(self.source_editor.GetModify())
            return
        elif keycode in (ord('g'), ord('G')) and event.ControlDown():
            if event.ShiftDown():
                wx.CallAfter(self.on_find_backwards, event)
            else:
                wx.CallAfter(self.on_find, event)
            return
        elif keycode in (ord('d'), ord('D')) and event.ControlDown() and not event.ShiftDown():
            # We need to ignore because Scintilla does Duplicate line
            self.mark_file_dirty(self.source_editor.GetModify())
            return
        elif event.ControlDown() and raw_key == wx.WXK_CONTROL:
            # This must be the last branch to activate actions before doc
            # DEBUG: coords = self._get_screen_coordinates()
            self.source_editor.show_kw_doc()
            event.Skip()
        else:
            # if self.dirty and keycode >= ord(' '):
            self.mark_file_dirty(self.source_editor.GetModify())
            event.Skip()

        # These commands are duplicated by global actions
        """ DEBUG
            else:
        self.source_editor.hide_kw_doc()
        elif keycode == ord('D') and event.ControlDown():
            if event.ShiftDown():
                self.delete_cell(event)
            else:
                self.delete_row(event)
        elif keycode == ord('3') and event.ControlDown():
            if event.ShiftDown():
                self.execute_sharp_comment(event)
            else:
                self.execute_comment(event)
        elif keycode == ord('4') and event.ControlDown():
            if event.ShiftDown():
                self.execute_sharp_uncomment(event)
            else:
                self.execute_uncomment(event)
        """

    @staticmethod
    def _get_screen_coordinates():
        point = wx.GetMousePosition()
        point.x += 25
        point.y += 25
        return point

    def on_char(self, event):
        if not self.is_focused():
            self.GetFocus(None)
        keycode = event.GetUnicodeKey()
        if chr(keycode) in ['[', '{', '(', "'", '\"', '`']:
            self.execute_enclose_text(chr(keycode))
            self.store_position()
        else:
            event.Skip()

    def on_mouse_motion(self, event):
        if event.CmdDown():
            self._kw_doc_timer.Stop()
            # self.source_editor.show_kw_doc()
        else:
            if self.old_information_popup != self.source_editor._information_popup:
                self.source_editor.hide_kw_doc()
                self.old_information_popup = self.source_editor._information_popup
                self._start_kw_doc_timer()
        event.Skip()

    def _start_kw_doc_timer(self):
        self._kw_doc_timer.Start(1000, True)

    def execute_variable_creator(self, list_variable=False, dict_variable=False):
        from_, to_ = self.source_editor.GetSelection()
        text = self.source_editor.GetSelectedText()
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
            self.source_editor.SetSelection(from_ + 2, from_ + 2,)
            self.source_editor.SetInsertionPoint(from_ + 2)
        else:
            self.source_editor.DeleteRange(from_, size)
            self.source_editor.SetInsertionPoint(from_)
            self.source_editor.ReplaceSelection(self._variable_creator_value(symbol, text))
            self.source_editor.SetSelection(from_ + size + 2, from_ + size + 2)
            self.source_editor.SetInsertionPoint(from_ + size + 2)

    @staticmethod
    def _variable_creator_value(symbol, value=''):
        return symbol + '{' + value + '}'

    def execute_enclose_text(self, keycode):
        from_, to_ = self.source_editor.GetSelection()
        text = self.source_editor.GetSelectedText()
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
        new_ini_line = ini_line = self.source_editor.LineFromPosition(start)
        new_end_line = end_line = self.source_editor.LineFromPosition(end)
        last_line = self.source_editor.GetLineCount()
        # selection not on top?
        if ini_line > 0:
            # get the next row content
            if end_line + 1 < last_line - 3:
                rowbelow = self.source_editor.GetLine(end_line + 1)
                # exception if moving block is long assignemnt or arguments with continuation markers extend selection
                is_marker = self.first_non_space_content(rowbelow)
                if is_marker == '...':
                    new_end_line = self.find_initial_keyword(end_line, up=False)
            if new_end_line != end_line:  # Extend selection
                new_end_pos = self.source_editor.GetLineEndPosition(new_end_line - 1)
                self.source_editor.SetSelection(start, new_end_pos-1)
            # exception if is long assignemnt or arguments with continuation markers get top line
            # get the previous row content
            rowabove = self.source_editor.GetLine(ini_line - 1)
            is_marker = self.first_non_space_content(rowabove)
            if is_marker == '...':
                new_ini_line = max(1, self.find_initial_keyword(ini_line))
            self.source_editor.BeginUndoAction()
            if new_ini_line != ini_line:
                # Move block to up new_ini_line
                delta = ini_line - new_ini_line
                for _ in range(0, delta):
                    self.source_editor.MoveSelectedLinesUp()
            else:
                self.source_editor.MoveSelectedLinesUp()
            self.source_editor.EndUndoAction()
            # New selection
            start, end = self.source_editor.GetSelection()
            new_end_line = self.source_editor.LineFromPosition(end - 1)  # One char before
            nendpos = self.source_editor.GetLineEndPosition(new_end_line)
            self.source_editor.SetAnchor(nendpos)
            new_ini_line = self.source_editor.LineFromPosition(start)
            # indentation after move
            new_top = self.source_editor.GetLine(new_ini_line)
            rowbelow = self.source_editor.GetLine(new_end_line + 1)
            old_start = self.first_non_space(rowbelow)
            new_start = self.first_non_space(new_top)
            was_end_old = rowbelow[old_start:old_start+3] == 'END'
            was_end_new = new_top[new_start:new_start+3] == 'END'
            if new_start == old_start and was_end_old and was_end_new:
                self.deindent_line(new_end_line + 1)
                self.indent_block()
            elif new_start == old_start and was_end_old:
                self.indent_block()
            start, end = self.source_editor.GetSelection()
            if old_start > new_start and was_end_new:
                self.deindent_line(new_end_line + 1)
                if was_end_old:
                    self.indent_block()
            if new_start < old_start and not was_end_new:
                self.indent_block()
            elif new_start > old_start:
                self.deindent_block()

    def find_initial_keyword(self, start: int, up=True):
        if up:
            if start <= 3:
                return
            text = self.source_editor.GetLine(start)
            is_marker = self.first_non_space_content(text)  # check if selection starts with marker
            if is_marker == '...':
                return start
            is_marker = '...'
            found = False
            line = start - 2
            while is_marker == '...' and line > 2:
                row = self.source_editor.GetLine(line)
                is_marker = self.first_non_space_content(row)
                if is_marker != '...':
                    found = True
                    break
                line -= 1
            return line if found else start - 1
        else:
            last_line = self.source_editor.GetLineCount()
            if start > last_line - 3:
                return
            text = self.source_editor.GetLine(start)
            is_marker = self.first_non_space_content(text)  # check if selection starts with marker
            if is_marker == '...':
                return start
            is_marker = '...'
            found = False
            line = start + 2
            while is_marker == '...' and line < last_line - 2:
                row = self.source_editor.GetLine(line)
                is_marker = self.first_non_space_content(row)
                if is_marker != '...':
                    found = True
                    break
                line += 1
            return line if found else start + 1

    def first_non_space_content(self, text):
        start = self.first_non_space(text)
        end = self.last_non_space(text[start:])
        return text[start:start+end]

    @staticmethod
    def first_non_space(text):
        idx = 0
        for idx in range(0, len(text)):
            if text[idx] != ' ':
                break
        return idx

    @staticmethod
    def last_non_space(text):
        idx = 0
        for idx in range(0, len(text)):
            if text[idx] == ' ':
                break
        return idx

    def move_row_down(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        new_ini_line = ini_line = self.source_editor.LineFromPosition(start)
        new_end_line = end_line = self.source_editor.LineFromPosition(end)
        last_line = self.source_editor.GetLineCount()
        # If line to move starts with ... move block without changes
        top_content = self.source_editor.GetLine(ini_line)
        # exception if is long assignement or arguments with continuation markers get below line
        is_marker = self.first_non_space_content(top_content)
        # get the next row content and length
        rowbelow = self.source_editor.GetLine(end_line + 1)
        if is_marker != '...':
            if end_line + 2 < last_line - 1:
                # exception if is long assignement or arguments with continuation markers get below line
                is_marker = self.first_non_space_content(rowbelow)
                if is_marker == '...':
                    new_end_line = self.find_initial_keyword(end_line, up=False)
            if new_end_line != end_line:  # Extend selection
                new_end_pos = self.source_editor.GetLineEndPosition(new_end_line-1)
                self.source_editor.SetSelection(start, new_end_pos - 1)
                self.source_editor.SetAnchor(start)
            # exception if target is long assignemnt or arguments with continuation markers get end line
            # get the after below row content
            rowafterbelow = self.source_editor.GetLine(new_end_line + 2)  # Checking if is continuation arguments
            is_marker = self.first_non_space_content(rowafterbelow)
            if is_marker == '...':
                new_ini_line = self.find_initial_keyword(new_end_line + 1, up=False)
        self.source_editor.BeginUndoAction()
        if new_ini_line != ini_line:
            # Move block to down new_ini_line
            delta = new_ini_line - ini_line - 1
            for _ in range(0, delta):
                self.source_editor.MoveSelectedLinesDown()
        else:
            self.source_editor.MoveSelectedLinesDown()
        self.source_editor.EndUndoAction()
        self.source_editor.EnsureCaretVisible()
        # New selection
        start, end = self.source_editor.GetSelection()
        new_end_line = self.source_editor.LineFromPosition(end - 1)  # One char before
        new_ini_line = self.source_editor.LineFromPosition(start)
        rowtop = self.source_editor.GetLine(new_ini_line - 1)  # content before block
        nendpos = self.source_editor.GetLineEndPosition(new_end_line)
        self.source_editor.SetAnchor(nendpos)
        # indentation after move
        newstart = self.source_editor.GetLine(new_ini_line)
        new_start = self.first_non_space(newstart)
        old_start = self.first_non_space(rowtop)
        was_end_old = rowtop[old_start:old_start + 3] == 'END'
        old_size = self.last_non_space(rowtop[old_start:])
        was_indent_old = rowtop[old_start:old_start+old_size] in INDENTED_START
        was_end_new = newstart[new_start:new_start + 3] == 'END'
        if new_start == old_start and was_end_new:
            self.indent_line(new_ini_line - 1)
        if new_start == old_start and was_indent_old:
            self.indent_block()
        if new_start > old_start and not was_indent_old:
            self.deindent_block()
        elif new_start < old_start and not was_end_new:
            self.indent_block()
        if new_start > old_start and was_end_new and was_end_old:
            self.indent_line(new_ini_line - 1)
        # New selection
        nstartpos = self.source_editor.PositionFromLine(new_ini_line)
        nendpos = self.source_editor.GetLineEndPosition(new_end_line)
        self.source_editor.SetSelection(nstartpos, nendpos)
        self.source_editor.SetAnchor(nstartpos)

    def delete_row(self, event):
        _ = event
        start, end = self.source_editor.GetSelection()
        ini_line = self.source_editor.LineFromPosition(start)
        self.source_editor.SelectNone()
        if start == end:
            end_line = ini_line
        else:
            end_line = self.source_editor.LineFromPosition(end)
        for _ in range(ini_line, end_line + 1):
            self.source_editor.GotoLine(ini_line)
            self.source_editor.LineDelete()
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

    def on_settings_changed(self, message):
        """Update tab size if txt spaces size setting is modified"""
        _, setting = message.keys
        if setting == TXT_NUM_SPACES:
            self.tab_size = self.source_editor_parent.app.settings.get(TXT_NUM_SPACES, 4)
        if setting == 'reformat':
            self.reformat = self.source_editor_parent.app.settings.get('reformat', False)

    def mark_file_dirty(self, dirty=True):
        if not self.is_focused():  # DEBUG: Was marking file clean from Grid Editor
            return
        if self._data:  # and self._dirty == 1:
            if dirty:
                self._data.mark_data_dirty()
            else:
                self._data.mark_data_pristine()


class RobotDataEditor(stc.StyledTextCtrl):
    margin = 1

    def __init__(self, parent, readonly=False):
        stc.StyledTextCtrl.__init__(self, parent)
        self.parent = parent
        self._plugin = parent.plugin
        self._settings = parent.source_editor_parent.app.settings
        self._information_popup = None
        self._old_details = None
        self.readonly = readonly
        self.SetMarginType(self.margin, stc.STC_MARGIN_NUMBER)
        self.SetLexer(stc.STC_LEX_CONTAINER)
        self.SetReadOnly(True)
        self.SetUseTabs(False)
        self.SetTabWidth(parent.tab_size)
        self.Bind(stc.EVT_STC_UPDATEUI, self.on_update_ui)
        self.Bind(stc.EVT_STC_STYLENEEDED, self.on_style)
        self.Bind(stc.EVT_STC_ZOOM, self.on_zoom)
        # DEBUG:
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_pressed)
        self.stylizer = RobotStylizer(self, self._settings, self.readonly)
        # register some images for use in the AutoComplete box.
        # self.RegisterImage(1, Smiles.GetBitmap())  # DEBUG was images.
        self.RegisterImage(1, wx.ArtProvider.GetBitmap(wx.ART_FLOPPY, size=(16, 16)))
        self.RegisterImage(2, wx.ArtProvider.GetBitmap(wx.ART_NEW, size=(16, 16)))
        self.RegisterImage(3, wx.ArtProvider.GetBitmap(wx.ART_COPY, size=(16, 16)))

    def show_kw_doc(self, coords=None):
        if self.AutoCompActive():
            selected = [self.AutoCompGetCurrentText()]
        else:
            selected = self.get_selected_or_near_text(keep_cursor_pos=True)
        if selected:
            for kw in selected:
                self._show_keyword_details(kw, coords)

    def hide_kw_doc(self):
        list_of_popups = self.parent.GetChildren()
        for popup in list_of_popups:
            if isinstance(popup, HtmlPopupWindow):
                popup.hide()
                self._old_details = None

    def on_key_pressed(self, event):
        if self.CallTipActive():
            self.CallTipCancel()
        key = event.GetKeyCode()
        if key == 32 and event.ControlDown():
            # Tips
            if event.ShiftDown():
                self.show_kw_doc()
                '''
                self.CallTipSetBackground("yellow")
                self.CallTipShow(pos, f"lots of of text: blah, blah, blah\n\n"
                                 "show some suff, maybe parameters..\n\n"
                                 f"fubar(param1, param2)\n\nContext: {selected}"
                                  )
                '''
            # Code completion
            else:
                self.parent.on_content_assist(event)
        event.Skip()

    def set_text(self, text):
        self.SetReadOnly(False)
        self.SetText(text)
        self.stylizer.stylize()
        self.EmptyUndoBuffer()
        self.SetMarginWidth(self.margin, self.calc_margin_width())

    @property
    def utf8_text(self):
        return self.GetText().encode('UTF-8')

    def on_style(self, event):
        _ = event
        self.stylizer.stylize()

    def on_zoom(self, event):
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

    def get_selected_or_near_text(self, keep_cursor_pos=False):
        content = set()
        if keep_cursor_pos:
            restore_cursor_pos = self.GetInsertionPoint()
        else:
            restore_cursor_pos = None
        # First get selected text
        selected = self.GetSelectedText()
        restore_start_pos = self.GetSelectionStart()
        restore_end_pos = self.GetSelectionEnd()
        # print(f"DEBUG: TextEditor RobotDataEditor  get_selected_or_near_text, restore_cursor={restore_cursor_pos} "
        #       f"restore_start_pos={restore_start_pos} restore_end_pos={restore_end_pos} anchor={self.GetAnchor()}")
        if selected:
            start_pos = self.GetSelectionStart()
            if selected.endswith('.'):  # Special cases for libraries prefix
                if restore_cursor_pos:
                    self.SetInsertionPoint(restore_cursor_pos)
                else:
                    self.SetInsertionPoint(start_pos + len(selected))
            elif len(selected.split('.')) > 1:
                parts = selected.split('.')
                self.SetSelectionStart(start_pos + len(parts[0]) + 1)
                self.SetSelectionEnd(start_pos + len(selected))
                if restore_cursor_pos:
                    self.SetInsertionPoint(restore_cursor_pos)
                else:
                    self.SetInsertionPoint(start_pos + len(parts[0]) + 1)
            else:
                self.SetSelectionStart(start_pos)
                self.SetSelectionEnd(start_pos + len(selected))
                if restore_cursor_pos:
                    self.SetInsertionPoint(restore_cursor_pos)
                else:
                    self.SetInsertionPoint(start_pos + len(selected))
            content.add(selected.strip())
        # Next get text on the left
        text = self.GetCurLine()[0]
        start_pos = self.GetInsertionPoint()
        line = self.GetCurrentLine()
        line_end = self.GetLineEndPosition(line)
        size = self.GetLineLength(line)
        star = self.GetLineRaw(line)
        sz_star = len(star) - 1
        min_pos = line_end - sz_star
        pos_in_line = start_pos - min_pos
        # print(f"DEBUG: line={text}\nstar={star}\nmin_pos={min_pos} start_pos={start_pos}"
        #       f" line_end={line_end}\nline={line}"
        #       f" pos_in_line={pos_in_line} size={size} sz_star={sz_star} lentext={len(text)}")
        # if pos_in_line > 0:
        start_chr = end_chr = None
        try:
            for i in range(max(1, min(size, pos_in_line-1)), 1, -1):
                if text[i] == ' ' and text[i-1] == ' ':
                    start_chr = i + 1
                    break
            if pos_in_line >= 0:
                for i in range(pos_in_line, size):
                    if text[i] == ' ' and text[i+1] == ' ':
                        end_chr = i
                        break
        except IndexError:
            pass
        value = None
        if start_chr is not None:
            if end_chr is not None:
                value = text[start_chr:end_chr]
            else:
                value = text[start_chr:].strip()
        elif end_chr is not None:
            value = text[pos_in_line:end_chr]
        if value:
            # self.SetInsertionPoint(self.GetSelectionStart())
            if start_chr:
                start_pos = min_pos + start_chr
            else:
                start_pos = min_pos + pos_in_line
            if value.endswith('.'):  # Special cases for libraries prefix
                if restore_cursor_pos:
                    self.SetInsertionPoint(restore_cursor_pos)
                else:
                    self.SetInsertionPoint(start_pos + len(value))
            elif len(value.split('.')) > 1:
                if restore_cursor_pos:
                    self.SetInsertionPoint(restore_cursor_pos)
                else:
                    parts = value.split('.')
                    self.SetSelectionStart(start_pos + len(parts[0]) + 1)
                    self.SetSelectionEnd(start_pos + len(value))
                    self.SetInsertionPoint(start_pos + len(parts[0]) + 1)
            else:
                if restore_cursor_pos:
                    self.SetInsertionPoint(restore_cursor_pos)
                else:
                    self.SetSelectionStart(start_pos)
                    self.SetSelectionEnd(start_pos + len(value))
                    self.SetInsertionPoint(start_pos)
            content.add(value)
        if restore_cursor_pos:
            self.SetAnchor(restore_cursor_pos)
            self.SetInsertionPoint(restore_cursor_pos)
        if restore_start_pos:
            self.SetSelection(restore_start_pos, restore_end_pos)
        return content if content else ['']

    def on_update_ui(self, evt):
        _ = evt
        # check for matching braces
        brace_at_caret = -1
        brace_opposite = -1
        char_before = None
        caret_pos = self.GetCurrentPos()

        if caret_pos > 0:
            char_before = self.GetCharAt(caret_pos - 1)

        # check before
        if char_before and chr(char_before) in "[]{}()":
            brace_at_caret = caret_pos - 1

        # check after
        if brace_at_caret < 0:
            char_after = self.GetCharAt(caret_pos)

            if char_after and chr(char_after) in "[]{}()":
                brace_at_caret = caret_pos

        if brace_at_caret >= 0:
            brace_opposite = self.BraceMatch(brace_at_caret)

        if brace_at_caret != -1 and brace_opposite == -1:
            self.BraceBadLight(brace_at_caret)
        else:
            self.BraceHighlight(brace_at_caret, brace_opposite)

    def _show_keyword_details(self, value, coords=None):
        """
        Shows the keyword documentation in value at coordinates, coords.
        :param value: The content to show in detacheable window
        :param coords: If None they will be mouse pointer coordinates
        """
        details = self._plugin.get_keyword_details(value)
        if details and details != self._old_details:  # This is because on Windows keys are sent in repeat
            if not coords:
                position = wx.GetMousePosition()
            else:
                position = coords
            self._information_popup = HtmlPopupWindow(self.parent, (450, 300))
            self._information_popup.set_content(details, value)
            self._information_popup.show_at(position)
            self._old_details = details


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
        section, _ = message.keys
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
