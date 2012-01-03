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


class SourceEditorPlugin(Plugin, TreeAwarePluginMixin):
    title = 'Text Edit'

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._editor_component = None

    @property
    def _editor(self):
        if not self._editor_component:
            self._editor_component = SourceEditor(self.notebook, self.title)
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
        self._open_data_in_editor()
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
            self._open_data_in_editor()

    def _should_process_data_changed_message(self, message):
        return self.is_focused() and \
               isinstance(message, RideDataChanged) and \
               not isinstance(message, RideDataChangedToDirty)

    def OnTreeSelection(self, message):
        if self.is_focused():
            if self._editor.dirty:
                self._apply_txt_changes_to_model()
            self._open_from_tree_selection(message.item and message.item.datafile_controller)

    def _open_data_in_editor(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            data = DataFileWrapper(datafile_controller)
            self._editor.open(data)

    def _open_from_tree_selection(self, datafile_controller):
        if datafile_controller:
            data = DataFileWrapper(datafile_controller)
            self._editor.selected(data)

    def OnTabChange(self, message):
        if message.newtab == self.title:
            self._open()
        if message.oldtab == self.title:
            if self._editor.dirty:
                self._apply_txt_changes_to_model()

    def _apply_txt_changes_to_model(self):
        self._editor.save()
        self._editor.reset()

    def is_focused(self):
        return self.notebook.current_page_title == self.title


class DataFileWrapper(object): # TODO: bad class name

    def __init__(self, data):
        self._data = data

    def __eq__(self, other):
        if other is None:
            return False
        return self._data == other._data

    def update_from(self, content):
        src = StringIO(content)
        target = self._create_target()
        FromStringIOPopulator(target).populate(src)
        # this is to prevent parsing errors from spoiling all data
        self._sanity_check(target, content)
        self._data.execute(SetDataFile(target))

    def _sanity_check(self, candidate, current):
        candidate_txt = self._txt_data(candidate).encode('UTF-8')
        c = self._remove_all(candidate_txt, ' ', '\n', '...', '\r')
        e = self._remove_all(current, ' ', '\n', '...', '\r')
        if len(c) != len(e):
            raise AssertionError('Sanity Check Failed')

    def _remove_all(self, original_txt, *to_remove):
        txt = original_txt
        for item in to_remove:
            txt = txt.replace(item, '')
        return txt

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

    def __init__(self, parent, title):
        wx.Panel.__init__(self, parent)
        self._parent = parent
        self._create_ui(title)
        self._editor.Bind(wx.EVT_KEY_DOWN, self.OnEditorKey)
        self._data = None
        self._dirty = False

    def _create_ui(self, title):
        button_sizer = HorizontalSizer()
        button_sizer.add_with_padding(ButtonWithHandler(self, 'Apply Changes',
                                      handler=lambda e: self.save()))
        self.SetSizer(VerticalSizer())
        self.Sizer.add(button_sizer)
        self._editor = RobotDataEditor(self)
        self.Sizer.add_expanding(self._editor)
        self._parent.add_tab(self, title, allow_closing=False)

    @property
    def dirty(self):
        return self._dirty

    def open(self, data):
        self._data = data
        self._editor.set_text(self._data.content)

    def selected(self, data):
        if self._data == data:
            return
        self.open(data)

    def reset(self):
        self._dirty = False

    def save(self):
        if self.dirty:
            self.reset()
            editor_txt = self._editor.utf8_text
            try:
                self._data.update_from(editor_txt)
            except AssertionError:
                self._handle_sanity_check_failure()

    def _handle_sanity_check_failure(self):
        # TODO: use widgets.Dialog
        id = wx.MessageDialog(self._editor,
                         'ERROR: Data sanity check failed!\n'\
                         'Reset changes?',
                         'Can not apply changes from Txt Editor',
                          style=wx.YES|wx.NO).ShowModal()
        if id == wx.ID_NO:
            self._mark_file_dirty()
        else:
            self._revert()

    def _revert(self):
        self._dirty = False
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
