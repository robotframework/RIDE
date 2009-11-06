#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

import wx
import os

from robotide import context
from robotide import utils
from robotide.model.settings import Documentation, ResourceImport
from robotide.publish import RideDatafileEdited

from eventhandler import RideEventHandler
from kweditor import KeywordEditor
from listeditor import ListEditor
from editordialogs import *


def Editor(item, editor_panel): #, tree):
    editor_class = globals()[item.__class__.__name__ + 'Editor']
    return editor_class(editor_panel, item) #, tree)


def dialog_from_class(obj):
    return globals()[obj.__class__.__name__ + 'Dialog']


class _RobotTableEditor(wx.Panel):
    title = None

    def __init__(self, parent, item): #, tree):
        wx.Panel.__init__(self, parent)
        self.Show(False)   
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        if self.title is not None:
            self.sizer.Add(self._create_header(self.title), 0, wx.ALL, 5)
            self.sizer.Add((0,10))
        self.item = item
#        self.tree = tree
        self._populate()

#    def view(self):
#        self.GetParent().set_editor(self)

    def close(self):
        self.Show(False)
    
    def save(self):
        pass
    
    def _create_header(self, text):
        header = wx.StaticText(self, -1, text)
        header.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
        return header

    def _add_settings(self):
        for setting in self.item.settings:
            if isinstance(setting, Documentation):
                editor_class = _DocumentationEditor
            else:
                editor_class = _SettingEditor
            editor = editor_class(self, setting) #, self.tree)
            self.sizer.Add(editor, 0, wx.ALL|wx.EXPAND, 1)        


class ResourceFileEditor(_RobotTableEditor):

    def _populate(self):
        self.sizer.Add(self._create_header(self.item.name), 0, wx.ALL, 5)
        self.sizer.Add(self._create_source_label(self._get_source()), 0, wx.ALL, 1)
        self._add_settings()
        self.sizer.Add((0, 10))
        self._add_import_settings()
        self._add_variable_table()

    def _get_source(self):
        return self.item.source

    def _create_source_label(self, source):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((5,0))
        sizer.Add(wx.StaticText(self, label='Source',
                                size=(context.SETTING_LABEL_WIDTH,
                                      context.SETTING_ROW_HEIGTH)))
        sizer.Add(wx.StaticText(self, label=source))
        return sizer
     
    def _add_import_settings(self):
        editor = ImportSettingListEditor(self, self.item.settings.imports) #, self.tree)
        self.sizer.Add(editor, 1, wx.EXPAND)

    def _add_variable_table(self):
        editor = VariablesListEditor(self, self.item.variables) #, self.tree)
        self.sizer.Add(editor, 1, wx.EXPAND)


class TestCaseFileEditor(ResourceFileEditor):

    def _populate(self):
        ResourceFileEditor._populate(self)
        self.sizer.Add((0, 10))
        self._add_metadata()

    def _add_metadata(self):
        editor = MetadataListEditor(self, self.item.settings.metadata) #, self.tree)
        self.sizer.Add(editor, 1, wx.EXPAND)


class InitFileEditor(TestCaseFileEditor):

    def _get_source(self):
        return os.path.split(self.item.source)[0] + os.sep


class _SettingEditor(wx.Panel, RideEventHandler):
    
    def __init__(self, parent, item): #, tree):
        wx.Panel.__init__(self, parent)
        self._item = item
        self._datafile = parent.item.get_datafile()
#        self.tree = tree
        self._create_controls(utils.name_from_class(item))
        self._dialog = dialog_from_class(item)
        self._editing = False

    def _create_controls(self, label):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((5,0))
        sizer.Add(wx.StaticText(self, label=label,
                                size=(context.SETTING_LABEL_WIDTH,
                                      context.SETTING_ROW_HEIGTH)))
        self._value_display = self._get_value_display()
        self._update_value() 
        sizer.Add(self._value_display, 1, wx.EXPAND)
        sizer.Add(utils.create_button(self, 'Edit', self.OnEdit),
                  flag=wx.LEFT|wx.RIGHT, border=5)
        sizer.Add(utils.create_button(self, 'Clear', self.OnClear))
        sizer.Layout()
        self.SetSizer(sizer)
        
    def _get_value_display(self):
        display = wx.TextCtrl(self, size=(-1, context.SETTING_ROW_HEIGTH))
        display.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        display.SetEditable(False)
        return display

    def OnEdit(self, event=None):
        self._editing = True
        dlg = self._dialog(self.GetGrandParent(), self._item, self._datafile)
        if dlg.ShowModal() == wx.ID_OK:
            self._item.set_str_value(dlg.get_value())
            self._update_and_notify()
        dlg.Destroy()
        self._editing = False

    def OnLeftUp(self, event):
        selection = self._value_display.GetSelection()
        if selection[0] == selection[1] and not self._editing:
            wx.CallAfter(self.OnEdit, event)
        event.Skip()
        
    def _update_and_notify(self):
        self._update_value()
        if not self._datafile.dirty:
            self._datafile.dirty = True
            #FIXME: We need to decide whether we want to expose the model object 
            #or subset of those attributes 
            # self.tree.set_dirty(self._datafile)
            RideDatafileEdited(datafile=self._datafile).publish()
        
    def OnClear(self, event):
        self._item.clear()
        self._update_and_notify()
        
    def _update_value(self):
        if self._item.active():
            self._value_display.SetBackgroundColour('white')
            self._value_display.SetValue(self._item.get_str_value())
        else:
            self._value_display.Clear()
            self._value_display.SetBackgroundColour('light grey')

    def _get_active_item(self):
        return self._datafile


class _DocumentationEditor(_SettingEditor):

    def __init__(self, parent, item): #, tree):
        wx.Panel.__init__(self, parent)
        self._item = item
        self._datafile = parent.item.get_datafile()
#        self.tree = tree
        self._create_controls('Documentation')

    def _get_value_display(self):
        display = utils.RideHtmlWindow(self, (-1, 60))
        display.Bind(wx.EVT_LEFT_DOWN, self.OnEdit)
        return display

    def _update_value(self):
        value = self._item.get_str_value()
        self._value_display.SetPage(utils.html_escape(value, formatting=True))

    def OnEdit(self, event):
        editor = DocumentationDialog(self.GetGrandParent(),
                                     self._item.get_str_value())
        if editor.ShowModal() == wx.ID_OK:
            self._item.set_str_value(editor.get_value())
            self._update_and_notify()
        editor.Destroy()

    def OnClear(self, event):
        self._item.clear()
        self._update_and_notify()


class TestCaseEditor(_RobotTableEditor):

    def _populate(self):
        self.header = self._create_header(self.item.name)
        self.sizer.Add(self.header, 0, wx.ALL, 5)
        self._add_settings()
        self.sizer.Add((0,10))
        self._create_kweditor()

    def _create_add_buttons(self, kweditor):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(utils.create_button(self, 'Add Row', kweditor.OnInsertRows),
                                      0, wx.ALL, 2)
        sizer.Add(utils.create_button(self, 'Add Column', kweditor.OnInsertCol),
                                      0, wx.ALL, 2)
        self.sizer.Add(sizer)
    
    def _create_kweditor(self):
        self.kweditor = KeywordEditor(self, self.item.keywords)
        self._create_add_buttons(self.kweditor)
        self.sizer.Add(self.kweditor, 1, wx.EXPAND|wx.ALL, 2)

    def set_dirty(self):
        self.item.datafile.set_dirty()
        RideDatafileEdited(datafile=self.item.datafile).publish()
#        self.tree.set_dirty(self.item.datafile)

    def Show(self, show):
        if hasattr(self, 'kweditor') and not show:
            self.kweditor.hide_popup()
        wx.Panel.Show(self, show)

    def close(self):
        self.Show(False)
        self.kweditor.save()
    
    def save(self):
        self.kweditor.save()
      
    def view(self):
        _RobotTableEditor.view(self)
        self.kweditor.SetFocus()


class UserKeywordEditor(TestCaseEditor):
    pass


class _AbstractListEditor(ListEditor, RideEventHandler):

    def __init__(self, parent, data): #, tree):
        ListEditor.__init__(self, parent, self._titles, data)
#        self.tree = tree

    def _get_active_item(self):
        return None
#        return self.tree.get_active_item()


class VariablesListEditor(_AbstractListEditor):
    _titles = ['Variable', 'Value']
    _buttons = ['Add Scalar', 'Add List']

    def get_column_values(self, item):
        return [item, self._data.value_as_string(item)]

    def OnAddScalar(self, event):
        dlg = ScalarVariableDialog(self.GetGrandParent())
        if dlg.ShowModal() == wx.ID_OK:
            self._data.new_scalar_var(*dlg.get_value())
            self.update_data()
        dlg.Destroy()

    def OnAddList(self, event):
        dlg = ListVariableDialog(self.GetGrandParent())
        if dlg.ShowModal() == wx.ID_OK:
            self._data.new_list_var(*dlg.get_value())
            self.update_data()
        dlg.Destroy()

    def OnEdit(self, event):
        var_tuple = self._data.get_name_and_value(self._selection)
        if var_tuple[0].startswith('${'): 
            dlg = ScalarVariableDialog(self.GetGrandParent(), var_tuple)
        else:
            dlg = ListVariableDialog(self.GetGrandParent(), var_tuple)
        if dlg.ShowModal() == wx.ID_OK:
            self._data.set_name_and_value(self._selection, *dlg.get_value())
            self.update_data()
        dlg.Destroy()


class ImportSettingListEditor(_AbstractListEditor):
    _titles = ['Import', 'Name / Path', 'Arguments']
    _buttons = ['Add Library', 'Add Resource', 'Add Variables']

    def OnEdit(self, event):
        setting = self._get_setting()
        dlg = dialog_from_class(setting)(self.GetGrandParent(), setting)
        if dlg.ShowModal() == wx.ID_OK:
            setting.set_str_value(dlg.get_value())
            self.update_data()
            if self.resource_modified():
                self._data.resource_updated(self._selection)
        dlg.Destroy()

    def OnAddLibrary(self, event):
        self._show_import_editor_dialog(LibraryImportDialog, self._data.new_library)

    def OnAddResource(self, event):
        self._show_import_editor_dialog(ResourceImportDialog, self._data.new_resource)

    def OnAddVariables(self, event):
        self._show_import_editor_dialog(VariablesImportDialog, self._data.new_variables)
    
    def _show_import_editor_dialog(self, dialog, creator):
        dlg = dialog(self.GetGrandParent())
        if dlg.ShowModal() == wx.ID_OK:
            creator(dlg.get_value())
            self.update_data()
        dlg.Destroy()

    def get_column_values(self, item):
        return [utils.name_from_class(item, 'Import'), item.name, 
                utils.join_value(item.args)]

    def resource_modified(self):
        return self._get_setting().__class__ == ResourceImport

    def _get_setting(self):
        return self._data[self._selection]


class MetadataListEditor(_AbstractListEditor):
    _titles = ['Metadata', 'Value']
    _buttons = ['Add Metadata']
    _sortable = False

    def OnEdit(self, event):
        meta = self._data[self._selection]
        dlg = MetadataDialog(self.GetGrandParent(), meta)
        if dlg.ShowModal() == wx.ID_OK:
            meta.name, meta.value = dlg.get_value()
            self.update_data()
        dlg.Destroy()

    def OnAddMetadata(self, event):
        dlg = MetadataDialog(self.GetGrandParent())
        if dlg.ShowModal() == wx.ID_OK:
            self._data.new_metadata(*dlg.get_value())
            self.update_data()
        dlg.Destroy()
        
    def get_column_values(self, item):
        return [utils.printable_name(item.name), utils.html_escape(item.value)]
