import wx
from wx import stc
from StringIO import StringIO
from robot.parsing.model import TestDataDirectory
from robot.parsing.populators import FromFilePopulator
from robot.parsing.txtreader import TxtReader
from robotide.controller.commands import _Command
from robotide.publish.messages import RideMessage, RideOpenSuite, RideDataChangedToDirty

from robotide.widgets import VerticalSizer
from robotide.pluginapi import (Plugin, ActionInfo, RideSaving,
        TreeAwarePluginMixin, RideTreeSelection, RideNotebookTabChanging)


class SourceEditorPlugin(Plugin, TreeAwarePluginMixin):
    title = 'Txt Edit'

    def __init__(self, application):
        Plugin.__init__(self, application)
        self._editor_component = None

    @property
    def _editor(self):
        if not self._editor_component:
            self._editor_component = SourceEditor(self.notebook, self.title)
        return self._editor_component

    def enable(self):
        self.register_action(ActionInfo('Tools', 'Txt Edit', self.OnOpen))
        self.add_self_as_tree_aware_plugin()
        self.subscribe(self.OnSaving, RideSaving)
        self.subscribe(self.OnTreeSelection, RideTreeSelection)
        self.subscribe(self.OnTreeSelection, RideMessage)
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

    def OnTreeSelection(self, message):
        if isinstance(message, RideDataChangedToDirty):
            return
        if self.is_focused():
            if isinstance(message, RideOpenSuite):
                self._editor.reset()
            if self._editor.dirty:
                self._apply_txt_changes_to_model()
            self._open_data_in_editor()

    def _open_data_in_editor(self):
        datafile_controller = self.tree.get_selected_datafile_controller()
        if datafile_controller:
            data = DataFileWrapper(datafile_controller)
            self._editor.open(data)

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


class SetDataFile(_Command):

    def __init__(self, datafile):
        self._datafile = datafile

    def execute(self, context):
        context.mark_dirty()
        context.set_datafile(self._datafile)


class DataFileWrapper(object): # TODO: bad class name

    def __init__(self, data):
        self._data = data

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
        if isinstance(data, TestDataDirectory) and not data.initfile:
            return ''
        output = StringIO()
        data.save(output=output, format='txt')
        return output.getvalue()


class SourceEditor(wx.Panel):

    def __init__(self, parent, title):
        wx.Panel.__init__(self, parent)
        self._parent = parent
        self.SetSizer(VerticalSizer())
        self._editor = RobotDataEditor(self)
        self.Sizer.add_expanding(self._editor)
        self._parent.AddPage(self, title)
        self._editor.Bind(wx.EVT_KEY_DOWN, self.OnEditorKey)
        self._data = None
        self._dirty = False

    @property
    def dirty(self):
        return self._dirty

    def open(self, data):
        self._data = data
        self._editor.set_text(self._data.content)

    def reset(self):
        self._dirty = False

    def save(self):
        if self.dirty:
            self.reset()
            try:
                self._data.update_from(self._editor.utf8_text)
            except AssertionError:
                # TODO: use widgets.Dialog
                wx.MessageDialog(self._editor,
                                 'ERROR: Data sanity check failed!\n'\
                                 'All changes made in Txt Editor\n'\
                                 'since last save are disregarded',
                                 'Can not apply changes from Txt Editor',
                                  style=wx.OK).ShowModal()

    def OnEditorKey(self, event):
        if not self.dirty:
            self._mark_file_dirty()
        event.Skip()

    def _mark_file_dirty(self):
        self._dirty = True
        self._data.mark_data_dirty()


class RobotDataEditor(stc.StyledTextCtrl):

    def __init__(self, parent):
        stc.StyledTextCtrl.__init__(self, parent)
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'fore:#000000,back:#FFFFFF,face:Courier New,size:12')
        self.SetMarginType(0, stc.STC_MARGIN_NUMBER)
        self.SetMarginWidth(0, self.TextWidth(stc.STC_STYLE_LINENUMBER,'1234'))

    def set_text(self, text):
        self.SetText(text)

    @property
    def utf8_text(self):
        return self.GetText().encode('UTF-8')


class FromStringIOPopulator(FromFilePopulator):

    def populate(self, content):
        TxtReader().read(content, self)
