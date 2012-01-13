#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
import wx
from wx import stc
from StringIO import StringIO
from robot.parsing.model import TestDataDirectory
from robot.parsing.populators import FromFilePopulator
from robot.parsing.txtreader import TxtReader

from robotide.controller.commands import SetDataFile
from robotide.publish.messages import RideMessage
from robotide.widgets import VerticalSizer, HorizontalSizer, ButtonWithHandler
from robotide.pluginapi import (Plugin, RideSaving, TreeAwarePluginMixin,
        RideTreeSelection, RideNotebookTabChanging, RideDataChanged,
        RideOpenSuite, RideDataChangedToDirty)


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
        return self._editor_component

    def enable(self):
        self.add_self_as_tree_aware_plugin()
        self.subscribe(self.OnSaving, RideSaving)
        self.subscribe(self.OnTreeSelection, RideTreeSelection)
        self.subscribe(self.OnDataChanged, RideMessage)
        self.subscribe(self.OnTabChange, RideNotebookTabChanging)
        self._open()

    def disable(self):
        self.unsubscribe_all()
        self.remove_self_from_tree_aware_plugins()
        self.unregister_actions()
        self._editor_component = None

    def OnOpen(self, event):
        self._open()

    def _open(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            self._open_data_for_controller(datafile_controller)
        self.show_tab(self._editor)

    def OnSaving(self, message):
        if self.is_focused():
            self._editor.save()

    def OnDataChanged(self, message):
        if self._should_process_data_changed_message(message):
            if isinstance(message, RideOpenSuite):
                self._editor.reset()
            if self._editor.dirty:
                self._apply_txt_changes_to_model()
            self._open_tree_selection_in_editor()

    def _should_process_data_changed_message(self, message):
        return isinstance(message, RideDataChanged) and \
               not isinstance(message, RideDataChangedToDirty)

    def OnTreeSelection(self, message):
        if self.is_focused():
            next_datafile_controller = message.item and message.item.datafile_controller
            if self._editor.dirty:
                if not self._apply_txt_changes_to_model():
                    if self._editor.datafile_controller != next_datafile_controller:
                        self.tree.select_controller_node(self._editor.datafile_controller)
                    return
            if next_datafile_controller:
                self._open_data_for_controller(next_datafile_controller)

    def _open_tree_selection_in_editor(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            self._editor.open(DataFileWrapper(datafile_controller))

    def _open_data_for_controller(self, datafile_controller):
        self._editor.selected(DataFileWrapper(datafile_controller))

    def OnTabChange(self, message):
        if message.newtab == self.title:
            self._open()

    def _apply_txt_changes_to_model(self):
        if not self._editor.save():
            return False
        self._editor.reset()
        return True

    def is_focused(self):
        return self.notebook.current_page_title == self.title


class DataValidationHandler(object):

    def __init__(self, plugin):
        self._plugin = plugin
        self._last_answer = None
        self._last_answer_time = 0

    def set_editor(self, editor):
        self._editor = editor

    def validate_and_update(self, data, text):
        if not self._sanity_check(data, text):
            self._handle_sanity_check_failure()
            return False
        else:
            self._editor.reset()
            data.update_from(text)
            return True

    def _sanity_check(self, data, text):
        formatted_text = data.format_text(text)
        c = self._remove_all(formatted_text, ' ', '\n', '...', '\r', '*')
        e = self._remove_all(text, ' ', '\n', '...', '\r', '*')
        return len(c) == len(e)

    def _remove_all(self, original_txt, *to_remove):
        txt = original_txt
        for item in to_remove:
            txt = txt.replace(item, '')
        return txt

    def _handle_sanity_check_failure(self):
        if self._last_answer == wx.ID_NO and \
            time() - self._last_answer_time <= 0.2:
            self._editor._mark_file_dirty()
            return
        # TODO: use widgets.Dialog
        id = wx.MessageDialog(self._editor,
                         'ERROR: Data sanity check failed!\n'\
                         'Reset changes?',
                         'Can not apply changes from Txt Editor',
                          style=wx.YES|wx.NO).ShowModal()
        self._last_answer = id
        self._last_answer_time = time()
        if id == wx.ID_NO:
            self._editor._mark_file_dirty()
        else:
            self._editor._revert()


class DataFileWrapper(object): # TODO: bad class name

    def __init__(self, data):
        self._data = data

    def __eq__(self, other):
        if other is None:
            return False
        return self._data == other._data

    def update_from(self, content):
        self._data.execute(SetDataFile(self._create_target_from(content)))

    def _create_target_from(self, content):
        src = StringIO(content)
        target = self._create_target()
        FromStringIOPopulator(target).populate(src)
        return target

    def format_text(self, text):
        return self._txt_data(self._create_target_from(text)).encode('UTF-8')

    def mark_data_dirty(self):
        self._data.mark_dirty()

    def _create_target(self):
        target_class = type(self._data.data)
        if target_class is TestDataDirectory:
            target = TestDataDirectory(source=self._data.directory)
            target.initfile = self._data.data.initfile
            return target
        return target_class(source=self._data.source)

    @property
    def content(self):
        return self._txt_data(self._data.data)

    def _txt_data(self, data):
        output = StringIO()
        data.save(output=output, format='txt')
        return output.getvalue()


class SourceEditor(wx.Panel):

    def __init__(self, parent, title, data_validator):
        wx.Panel.__init__(self, parent)
        self._data_validator = data_validator
        self._data_validator.set_editor(self)
        self._parent = parent
        self._create_ui(title)
        self._editor.Bind(wx.EVT_KEY_DOWN, self.OnEditorKey)
        self._editor.Bind(wx.EVT_KILL_FOCUS, self.save)
        self._data = None
        self._dirty = False

    def _create_ui(self, title):
        button_sizer = HorizontalSizer()
        button_sizer.add_with_padding(ButtonWithHandler(self, 'Apply Changes', handler=lambda e: self.save()))
        self.SetSizer(VerticalSizer())
        self.Sizer.add(button_sizer)
        self._editor = RobotDataEditor(self)
        self.Sizer.add_expanding(self._editor)
        self._parent.add_tab(self, title, allow_closing=False)

    @property
    def dirty(self):
        return self._dirty

    @property
    def datafile_controller(self):
        return self._data._data

    def open(self, data):
        self.reset()
        self._data = data
        self._editor.set_text(self._data.content)

    def selected(self, data):
        if self._data == data:
            return
        self.open(data)

    def reset(self):
        self._dirty = False

    def save(self, *args):
        if self.dirty:
            if not self._data_validator.validate_and_update(self._data,
                                                     self._editor.utf8_text):
                return False
        return True

    def _revert(self):
        self.reset()
        self._editor.set_text(self._data.content)

    def OnEditorKey(self, event):
        if not self.dirty:
            self._mark_file_dirty()
        event.Skip()

    def _mark_file_dirty(self):
        if self._data:
            self._dirty = True
            self._data.mark_data_dirty()


class RobotDataEditor(stc.StyledTextCtrl):

    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent)
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'fore:#000000,back:#FFFFFF,face:Courier New,size:12')
        self.SetMarginType(0, stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(0, self.TextWidth(stc.STC_STYLE_LINENUMBER,'1234'))
        self.SetReadOnly(True)

    def set_text(self, text):
        self.SetReadOnly(False)
        self.SetText(text)

    @property
    def utf8_text(self):
        return self.GetText().encode('UTF-8')


class FromStringIOPopulator(FromFilePopulator):

    def populate(self, content):
        TxtReader().read(content, self)
