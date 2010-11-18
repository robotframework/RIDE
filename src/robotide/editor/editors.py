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

from robotide import context
from robotide import utils
from robotide.utils import RideEventHandler, RideHtmlWindow, ButtonWithHandler
from robotide.controller.settingcontrollers import DocumentationController

from kweditor import KeywordEditor
from listeditor import ListEditor
from popupwindow import RideToolTipWindow
from editordialogs import (EditorDialog, DocumentationDialog, MetadataDialog,
                           ScalarVariableDialog, ListVariableDialog,
                           LibraryDialog, ResourceDialog, VariablesDialog)
from robotide.publish.messages import (RideItemSettingsChanged,
                                       RideItemNameChanged,
                                       RideInitFileRemoved)


def Editor(plugin, editor_panel, tree):
    controller = plugin.get_selected_item()
    if not controller:
        return WelcomePage(editor_panel)
    editor_class = plugin.get_editor(controller.data.__class__)
    return editor_class(plugin, editor_panel, controller, tree)


class WelcomePage(RideHtmlWindow):
    undo = cut = copy = paste = delete = comment = uncomment = save \
        = show_content_assist = lambda self: None

    def __init__(self, parent):
        RideHtmlWindow.__init__(self, parent, text=context.ABOUT_RIDE)

    def close(self):
        self.Show(False)


class EditorPanel(wx.Panel):
    """Base class for all editor panels"""
    # TODO: Move outside default editor package, document
    name = doc = ''
    title = None
    undo = cut = copy = paste = delete = comment = uncomment = save \
        = show_content_assist = lambda self: None

    def __init__(self, plugin, parent, controller, tree):
        wx.Panel.__init__(self, parent)
        self.plugin = plugin
        self.controller = controller
        self._tree = tree


class _RobotTableEditor(EditorPanel):
    name = 'table'
    doc = 'table editor'

    def __init__(self, plugin, parent, controller, tree):
        EditorPanel.__init__(self, plugin, parent, controller, tree)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.SetSizer(self.sizer)
        if self.title:
            self.sizer.Add(self._create_header(self.title), 0, wx.ALL, 5)
            self.sizer.Add((0,10))
        self._editors = []
        self.reset_last_show_tooltip()
        self._populate()

    def OnMotion(self, event):
        for editor in self._editors:
            editor.OnMotion(event)
        self.reset_last_show_tooltip()

    def tooltip_allowed(self, editor):
        if wx.GetMouseState().ControlDown() or \
                self._last_shown_tooltip is editor:
            return False
        self._last_shown_tooltip = editor
        return True

    def reset_last_show_tooltip(self):
        self._last_shown_tooltip = None

    def close(self):
        self.Unbind(wx.EVT_MOTION, handler=self.OnMotion)
        self.Show(False)

    def _create_header(self, text):
        header = wx.StaticText(self, -1, text)
        header.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
        return header

    def _add_settings(self):
        for setting in self.controller.settings:
            editor = self._create_editor_for(setting)
            self.sizer.Add(editor, 0, wx.ALL|wx.EXPAND, 1)
            self._editors.append(editor)

    def _create_editor_for(self, controller):
        editor_cls = DocumentationEditor if isinstance(controller, DocumentationController) \
                else SettingEditor
        return editor_cls(self, controller, self.plugin, self._tree)


class ResourceFileEditor(_RobotTableEditor):

    def _populate(self):
        datafile = self.controller.data
        self.sizer.Add(self._create_header(datafile.name), 0, wx.ALL, 5)
        self.sizer.Add(self._create_source_label(datafile.source), 0, wx.ALL, 1)
        self.sizer.Add((0, 10))
        self._add_settings()
        self._add_import_settings()
        self._add_variable_table()

    def _create_source_label(self, source):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((5,0))
        sizer.Add(wx.StaticText(self, label='Source',
                                size=(context.SETTING_LABEL_WIDTH,
                                      context.SETTING_ROW_HEIGTH)))
        sizer.Add(wx.StaticText(self, label=source))
        return sizer

    def _add_import_settings(self):
        editor = ImportSettingListEditor(self, self._tree, self.controller.imports)
        self.sizer.Add(editor, 1, wx.EXPAND)

    def _add_variable_table(self):
        editor = VariablesListEditor(self, self._tree, self.controller.variables)
        self.sizer.Add(editor, 1, wx.EXPAND)


class TestCaseFileEditor(ResourceFileEditor):

    def _populate(self):
        ResourceFileEditor._populate(self)
        self.sizer.Add((0, 10))
        self._add_metadata()

    def _add_metadata(self):
        editor = MetadataListEditor(self, self._tree, self.controller.metadata)
        self.sizer.Add(editor, 1, wx.EXPAND)


class InitFileEditor(TestCaseFileEditor):

    def _populate(self):
        TestCaseFileEditor._populate(self)
        self.plugin.subscribe(self._init_file_removed, RideInitFileRemoved)

    def _init_file_removed(self, message):
        for setting, editor in zip(self.controller.settings, self._editors):
            editor.refresh(setting)


class SettingEditor(wx.Panel, RideEventHandler):

    def __init__(self, parent, controller, plugin, tree):
        wx.Panel.__init__(self, parent)
        self._controller = controller
        self.plugin = plugin
        self._datafile = controller.datafile
        self._create_controls()
        self._tree = tree
        self._editing = False
        self.Bind(wx.EVT_MOTION, self.OnMotion)

    def _create_controls(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((5,0))
        sizer.Add(wx.StaticText(self, label=self._controller.label,
                                size=(context.SETTING_LABEL_WIDTH,
                                      context.SETTING_ROW_HEIGTH)))
        self._value_display = self._create_value_display()
        self.update_value()
        self._tooltip = RideToolTipWindow(self, (500, 350))
        sizer.Add(self._value_display, 1, wx.EXPAND)
        sizer.Add(ButtonWithHandler(self, 'Edit'), flag=wx.LEFT|wx.RIGHT, border=5)
        sizer.Add(ButtonWithHandler(self, 'Clear'))
        sizer.Layout()
        self.SetSizer(sizer)

    def _create_value_display(self):
        display = self._value_display_control()
        display.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
        display.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)
        display.Bind(wx.EVT_MOTION, self.OnDisplayMotion)
        return display

    def _value_display_control(self):
        ctrl = SettingValueDisplay(self)
        ctrl.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        ctrl.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        return ctrl

    def OnKey(self, event):
        self._tooltip.hide()

    def OnMotion(self, event):
        self._tooltip.hide()
        self.Parent.reset_last_show_tooltip()

    def OnDisplayMotion(self, event):
        self._tooltip.hide()

    def refresh(self, controller):
        self._controller = controller
        self.update_value()

    def refresh_datafile(self, item, event):
        self._tree.refresh_datafile(item, event)

    def OnEdit(self, event=None):
        self._hide_tooltip()
        self._editing = True
        dlg = self._crete_editor_dialog()
        if dlg.ShowModal() == wx.ID_OK:
            self._set_value(dlg.get_value(), dlg.get_comment())
            self._update_and_notify()
        dlg.Destroy()
        self._editing = False

    def _crete_editor_dialog(self):
        dlg_class = EditorDialog(self._controller)
        return dlg_class(self._datafile, self._controller, self.plugin)

    def _set_value(self, value_list, comment):
        self._controller.set_value(*value_list)
        self._controller.set_comment(comment)

    def _hide_tooltip(self):
        self._stop_popup_timer()
        self._tooltip.hide()

    def _stop_popup_timer(self):
        if hasattr(self, 'popup_timer'):
            self.popup_timer.Stop()

    def OnEnterWindow(self, event):
        if self._mainframe_has_focus():
            self._value_display.SetFocus()
            self.popup_timer = wx.CallLater(500, self.OnPopupTimer)

    def _mainframe_has_focus(self):
        return wx.GetTopLevelParent(self.FindFocus()) == \
                wx.GetTopLevelParent(self)

    def OnLeaveWindow(self, event):
        self._stop_popup_timer()

    def OnPopupTimer(self, event):
        if self.Parent.tooltip_allowed(self):
            details = self._get_details_for_tooltip()
            if details:
                self._tooltip.set_content(details)
                self._tooltip.show_at(self._tooltip_position())

    def _get_details_for_tooltip(self):
        kw = self._controller.keyword_name
        return self.plugin.get_keyword_details(kw)

    def _tooltip_position(self):
        ms = wx.GetMouseState()
        # -1 ensures that the popup gets focus immediately
        return ms.x-3, ms.y-3

    def OnLeftUp(self, event):
        if event.ControlDown():
            self._navigate_to_user_keyword()
        else:
            selection = self._value_display.GetSelection()
            if selection[0] == selection[1] and not self._editing:
                wx.CallAfter(self.OnEdit, event)
            event.Skip()

    def _navigate_to_user_keyword(self):
        uk = self.plugin.get_user_keyword(self._controller.keyword_name)
        if uk:
            self._tree.select_user_keyword_node(uk)

    def _update_and_notify(self):
        self.update_value()
        self._tree.mark_dirty(self._controller)

    def OnClear(self, event):
        self._controller.clear()
        self._update_and_notify()

    def update_value(self):
        if self._controller.is_set:
            self._value_display.set_value(self._controller, self.plugin)
        else:
            self._value_display.clear()

    def get_selected_datafile_controller(self):
        return self._controller.datafile_controller


class SettingValueDisplay(wx.TextCtrl):

    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, size=(-1, context.SETTING_ROW_HEIGTH),
                             style=wx.TE_RICH|wx.TE_MULTILINE)
        self.SetEditable(False)

    def set_value(self, controller, plugin):
        self.SetBackgroundColour('white')
        self.SetValue(controller.display_value)
        name = controller.keyword_name
        if plugin.is_user_keyword(name):
            self._style_user_keyword_name(name)

    def _style_user_keyword_name(self, name):
        font = self.GetFont()
        font.SetUnderlined(True)
        self.SetStyle(0, len(name), wx.TextAttr('blue', wx.NullColour, font))

    def clear(self):
        self.Clear()
        self.SetBackgroundColour('light grey')


class DocumentationEditor(SettingEditor):

    def _value_display_control(self):
        ctrl = RideHtmlWindow(self, (-1, 100))
        ctrl.Bind(wx.EVT_LEFT_DOWN, self.OnEdit)
        return ctrl

    def update_value(self):
        self._value_display.SetPage(self._controller.visible_value)

    def _get_details_for_tooltip(self):
        return self._controller.visible_value

    def _crete_editor_dialog(self):
        return DocumentationDialog(self._datafile,
                                   self._controller.editable_value)

    def _set_value(self, value_list, comment):
        if value_list:
            self._controller.editable_value = value_list[0]


class TestCaseEditor(_RobotTableEditor):

    def _populate(self):
        self.header = self._create_header(self.controller.name)
        self.sizer.Add(self.header, 0, wx.ALL, 5)
        self._add_settings()
        self.sizer.Add((0,10))
        self._create_kweditor()
        self.plugin.subscribe(self._settings_changed, RideItemSettingsChanged)
        self.plugin.subscribe(self._name_changed, RideItemNameChanged)

    def _create_kweditor(self):
        self.kweditor = KeywordEditor(self, self.controller, self._tree)
        self.sizer.Add(self.kweditor, 1, wx.EXPAND|wx.ALL, 2)

    def _settings_changed(self, data):
        if data.item == self.controller:
            for editor in self._editors:
                editor.update_value()

    def _name_changed(self, data):
        if data.item == self.controller:
            self.header.SetLabel(data.item.name)

    def Show(self, show):
        if hasattr(self, 'kweditor') and not show:
            self.kweditor.hide_tooltip()
        wx.Panel.Show(self, show)

    def close(self):
        _RobotTableEditor.close(self)
        self.kweditor.close()
        self.plugin.unsubscribe(self._settings_changed, RideItemSettingsChanged)
        self.plugin.unsubscribe(self._name_changed, RideItemNameChanged)

    def save(self):
        self.kweditor.save()

    def undo(self):
        self.kweditor.OnUndo()

    def redo(self):
        self.kweditor.OnRedo()

    def cut(self):
        self.kweditor.OnCut()

    def copy(self):
        self.kweditor.OnCopy()

    def paste(self):
        self.kweditor.OnPaste()

    def delete(self):
        self.kweditor.OnDelete()

    def comment(self):
        self.kweditor.OnCommentRows()

    def uncomment(self):
        self.kweditor.OnUncommentRows()

    def show_content_assist(self):
        self.kweditor.show_content_assist()

    def view(self):
        _RobotTableEditor.view(self)
        self.kweditor.SetFocus()


class UserKeywordEditor(TestCaseEditor): pass


class _AbstractListEditor(ListEditor):

    def __init__(self, parent, tree, controller):
        ListEditor.__init__(self, parent, self._titles, controller)
        self._datafile = controller.datafile
        self._tree = tree

    def get_selected_datafile_controller(self):
        return self._controller.datafile_controller

    def refresh_datafile(self, item, event):
        self._tree.refresh_datafile(item, event)

    def update_data(self):
        ListEditor.update_data(self)
        self._tree.mark_dirty(self._controller)


class VariablesListEditor(_AbstractListEditor):
    _titles = ['Variable', 'Value', 'Comment']
    _buttons = ['Add Scalar', 'Add List']

    def get_column_values(self, item):
        return [item.name, item.value if isinstance(item.value, basestring)
                            else ' | '.join(item.value), item.comment]

    def OnAddScalar(self, event):
        dlg = ScalarVariableDialog(self._controller)
        if dlg.ShowModal() == wx.ID_OK:
            ctrl = self._controller.add_variable(*dlg.get_value())
            ctrl.set_comment(dlg.get_comment())
            self.update_data()
        dlg.Destroy()

    def OnAddList(self, event):
        dlg = ListVariableDialog(self._controller)
        if dlg.ShowModal() == wx.ID_OK:
            ctrl = self._controller.add_variable(*dlg.get_value())
            ctrl.set_comment(dlg.get_comment())
            self.update_data()
        dlg.Destroy()

    def OnEdit(self, event):
        var = self._controller[self._selection]
        if var.name.startswith('${'):
            dlg = ScalarVariableDialog(self._controller, item=var)
        else:
            dlg = ListVariableDialog(self._controller, item=var)
        if dlg.ShowModal() == wx.ID_OK:
            var.set_value(*dlg.get_value())
            var.set_comment(dlg.get_comment())
            self.update_data()
        dlg.Destroy()


class ImportSettingListEditor(_AbstractListEditor):
    _titles = ['Import', 'Name / Path', 'Arguments', 'Comment']
    _buttons = ['Add Library', 'Add Resource', 'Add Variables']

    def OnEdit(self, event):
        setting = self._get_setting()
        dlg = EditorDialog(setting)(self._controller.datafile, item=setting)
        if dlg.ShowModal() == wx.ID_OK:
            # TODO: Tree should listen to chief controller
            controller = setting.set_value(*dlg.get_value())
            setting.set_comment(dlg.get_comment())
            if controller:
                self._tree.add_resource(controller)
            self.update_data()
        dlg.Destroy()

    def OnAddLibrary(self, event):
        self._show_import_editor_dialog(LibraryDialog,
                                        self._controller.add_library)

    def OnAddResource(self, event):
        self._show_import_editor_dialog(ResourceDialog,
                                        self._controller.add_resource)

    def OnAddVariables(self, event):
        self._show_import_editor_dialog(VariablesDialog,
                                        self._controller.add_variables)

    def _show_import_editor_dialog(self, dialog, creator):
        dlg = dialog(self._controller.datafile)
        if dlg.ShowModal() == wx.ID_OK:
            ctrl = creator(*dlg.get_value())
            ctrl.set_comment(dlg.get_comment())
            self.update_data()
        dlg.Destroy()

    def get_column_values(self, item):
        return [item.type, item.name, item.display_value, item.comment]

    def _get_setting(self):
        return self._controller[self._selection]


class MetadataListEditor(_AbstractListEditor):
    _titles = ['Metadata', 'Value', 'Comment']
    _buttons = ['Add Metadata']
    _sortable = False

    def OnEdit(self, event):
        meta = self._controller[self._selection]
        dlg = MetadataDialog(self._controller.datafile, item=meta)
        if dlg.ShowModal() == wx.ID_OK:
            meta.set_value(*dlg.get_value())
            meta.set_comment(dlg.get_comment())
            self.update_data()
        dlg.Destroy()

    def OnAddMetadata(self, event):
        dlg = MetadataDialog(self._controller.datafile)
        if dlg.ShowModal() == wx.ID_OK:
            ctrl = self._controller.add_metadata(*dlg.get_value())
            ctrl.set_comment(dlg.get_comment())
            self.update_data()
        dlg.Destroy()

    def get_column_values(self, item):
        return [item.name, utils.html_escape(item.value), item.comment]


def VariableEditorChooser(plugin, parent, controller, tree):
    controller = controller.datafile_controller
    editor_class = plugin.get_editor(controller.data.__class__)
    return editor_class(plugin, parent, controller, tree)
