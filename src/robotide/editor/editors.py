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
from robotide.utils import RideEventHandler, RideHtmlWindow
from robotide.widgets import ButtonWithHandler, HorizontalSizer
from robotide.controller.chiefcontroller import ChiefController
from robotide.controller.settingcontrollers import (DocumentationController,
                                                    VariableController, TagsController)
from robotide.robotapi import (ResourceFile, TestCaseFile, TestDataDirectory,
                               TestCase, UserKeyword, Variable)

from gridcolorizer import ColorizationSettings
from kweditor import KeywordEditor
from listeditor import ListEditor
from popupwindow import Tooltip
from editordialogs import (EditorDialog, DocumentationDialog, MetadataDialog,
                           ScalarVariableDialog, ListVariableDialog,
                           LibraryDialog, ResourceDialog, VariablesDialog)
from robotide.publish.messages import (RideItemSettingsChanged,
                                       RideItemNameChanged,
                                       RideInitFileRemoved, 
                                       RideImportSetting,
                                       RideChangeFormat)
from robot.parsing.settings import _Setting
from robotide.controller.commands import UpdateVariable
from robotide.publish import PUBLISHER
from robotide.usages.UsageRunner import Usages
from robotide.editor.tags import TagsDisplay
from robotide.context import SETTINGS


class WelcomePage(RideHtmlWindow):
    undo = cut = copy = paste = delete = comment = uncomment = save \
        = show_content_assist = tree_item_selected = lambda *args: None

    def __init__(self, parent):
        RideHtmlWindow.__init__(self, parent, text=context.ABOUT_RIDE)

    def close(self):
        self.Show(False)

    def destroy(self):
        self.close()
        self.Destroy()


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

    def tree_item_selected(self, item):
        pass


class _RobotTableEditor(EditorPanel):
    name = 'table'
    doc = 'table editor'
    _settings_open_id = 'robot table settings open'

    def __init__(self, plugin, parent, controller, tree):
        EditorPanel.__init__(self, plugin, parent, controller, tree)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.SetSizer(self.sizer)
        if self.title:
            self.sizer.Add(self._create_header(self.title),
                           0, wx.EXPAND|wx.ALL, 5)
            self.sizer.Add((0,10))
        self._editors = []
        self._reset_last_show_tooltip()
        self._populate()
        self.plugin.subscribe(self._settings_changed, RideItemSettingsChanged)

    def _should_settings_be_open(self):
        if self._settings_open_id not in SETTINGS:
            return False
        return SETTINGS[self._settings_open_id]

    def _store_settings_open_status(self):
        SETTINGS[self._settings_open_id] = self._settings.IsExpanded()

    def _settings_changed(self, data):
        if data.item == self.controller:
            for editor in self._editors:
                editor.update_value()

    def OnIdle(self, event):
        if self._last_shown_tooltip and self._mouse_outside_tooltip():
            self._last_shown_tooltip.hide()
            self._reset_last_show_tooltip()

    def _mouse_outside_tooltip(self):
        mx, my = wx.GetMousePosition()
        tx, ty = self._last_shown_tooltip.screen_position
        dx, dy = self._last_shown_tooltip.size
        return (mx<tx or mx>tx+dx) or (my<ty or my>ty+dy)

    def tooltip_allowed(self, tooltip):
        if wx.GetMouseState().ControlDown() or \
                self._last_shown_tooltip is tooltip:
            return False
        self._last_shown_tooltip = tooltip
        return True

    def _reset_last_show_tooltip(self):
        self._last_shown_tooltip = None

    def close(self):
        self.plugin.unsubscribe(self._settings_changed, RideItemSettingsChanged)
        self.Unbind(wx.EVT_MOTION)
        self.Show(False)

    def destroy(self):
        self.close()
        self.Destroy()

    def _create_header(self, text):
        header = wx.StaticText(self, -1, text)
        header.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
        return header

    def _add_settings(self):
        self._settings = self._create_settings()
        self._restore_settings_open_status()
        self._editors.append(self._settings)
        self.sizer.Add(self._settings, 0, wx.ALL|wx.EXPAND, 2)

    def _create_settings(self):
        settings = Settings(self, self.plugin, self._tree)
        settings.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._collabsible_changed)
        for setting in self.controller.settings:
            editor = settings.create_editor_for(setting)
            settings.add(editor)
        settings.build()
        return settings

    def _restore_settings_open_status(self):
        if self._should_settings_be_open():
            self._settings.Expand()
        else:
            self._settings.Collapse()

    def _collabsible_changed(self, event):
        self._store_settings_open_status()
        self.GetSizer().Layout()
        self.Refresh()
        event.Skip()

    def highlight_cell(self, obj, row, column):
        '''Highlight the given object at the given row and column'''
        if obj and isinstance(obj, _Setting):
            setting_editor = self._get_settings_editor(obj)
            if setting_editor and hasattr(setting_editor, "highlight"):
                setting_editor.highlight(column)
        else:
            self.kweditor.select(row, column)

    def _get_settings_editor(self, setting):
        '''Return the settings editor for the given setting object'''
        for child in self.GetChildren():
            if isinstance(child, SettingEditor):
                if child._item == setting:
                    return child
        return None

    def highlight(self, text, expand=True):
        for editor in self._editors:
            editor.highlight(text, expand=expand)


class Settings(wx.CollapsiblePane):
    BORDER = 2

    def __init__(self, parent, plugin, tree):
        wx.CollapsiblePane.__init__(self, parent, wx.ID_ANY, 'Settings',
                                    style=wx.CP_DEFAULT_STYLE|wx.CP_NO_TLW_RESIZE)
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._plugin = plugin
        self._tree = tree
        self._editors = []

    def GetPane(self):
        pane = wx.CollapsiblePane.GetPane(self)
        pane.tooltip_allowed = self.GetParent().tooltip_allowed
        return pane

    def close(self):
        for editor in self._editors:
            editor.close()

    def update_value(self):
        for editor in self._editors:
            editor.update_value()

    def create_editor_for(self, controller):
        editor_cls = self._get_editor_class(controller)
        return editor_cls(self.GetPane(), controller, self._plugin, self._tree)

    def _get_editor_class(self, controller):
        if isinstance(controller, DocumentationController):
            return DocumentationEditor
        if isinstance(controller, TagsController):
            return TagsEditor
        return SettingEditor

    def add(self, editor):
        self._sizer.Add(editor, 0, wx.ALL|wx.EXPAND, self.BORDER)
        self._editors.append(editor)

    def build(self):
        self.GetPane().SetSizer(self._sizer)
        self._sizer.SetSizeHints(self.GetPane())
        self.Bind(wx.EVT_SIZE, self._recalc_size)

    def _recalc_size(self, event):
        if self.IsExpanded():
            diff_to_pane = self.Size[1]-self.GetPane().Size[1]
            height = sum(editor.Size[1]+2*self.BORDER for editor in self._editors)+diff_to_pane
            self.SetSizeHints(-1, height)
        event.Skip()

    def highlight(self, text, expand=True):
        match = False
        for editor in self._editors:
            if editor.contains(text):
                editor.highlight(text)
                match = True
            else:
                editor.clear_highlight()
        if match and expand:
            self.Expand()
            self.Parent.GetSizer().Layout()


class ResourceFileEditor(_RobotTableEditor):
    _settings_open_id = 'resource file settings open'

    def __init__(self, *args):
        _RobotTableEditor.__init__(self, *args)
        self.plugin.subscribe(self._update_source, RideChangeFormat)

    def _update_source(self, message):
        self._source.SetLabel(self.controller.data.source)

    def tree_item_selected(self, item):
        if isinstance(item, VariableController):
            self._var_editor.select(item.name)

    def _populate(self):
        datafile = self.controller.data
        self.sizer.Add(self._create_header(datafile.name), 0, wx.EXPAND|wx.ALL, 5)
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
        self._source = wx.StaticText(self, label=source)
        sizer.Add(self._source)
        return sizer

    def _add_import_settings(self):
        import_editor = ImportSettingListEditor(self, self._tree, self.controller.imports)
        self.sizer.Add(import_editor, 1, wx.EXPAND)
        self._editors.append(import_editor)

    def _add_variable_table(self):
        self._var_editor = VariablesListEditor(self, self._tree, self.controller.variables)
        self.sizer.Add(self._var_editor, 1, wx.EXPAND)
        self._editors.append(self._var_editor)

    def close(self):
        self.plugin.unsubscribe(self._update_source, RideChangeFormat)
        for editor in self._editors:
            editor.close()
        self._editors = []
        _RobotTableEditor.close(self)


class TestCaseFileEditor(ResourceFileEditor):
    _settings_open_id = 'test case file settings open'

    def _populate(self):
        ResourceFileEditor._populate(self)
        self.sizer.Add((0, 10))
        self._add_metadata()

    def _add_metadata(self):
        metadata_editor = MetadataListEditor(self, self._tree, self.controller.metadata)
        self.sizer.Add(metadata_editor, 1, wx.EXPAND)
        self._editors.append(metadata_editor)


class InitFileEditor(TestCaseFileEditor):
    _settings_open_id = 'init file settings open'

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
        self.plugin.subscribe(self.update_value, RideImportSetting)

    def _create_controls(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((5,0))
        sizer.Add(wx.StaticText(self, label=self._controller.label,
                                size=(context.SETTING_LABEL_WIDTH,
                                      context.SETTING_ROW_HEIGTH)))
        self._value_display = self._create_value_display()
        self.update_value()
        self._tooltip = self._get_tooltip()
        sizer.Add(self._value_display, 1, wx.EXPAND)
        self._add_edit(sizer)
        sizer.Add(ButtonWithHandler(self, 'Clear'))
        sizer.Layout()
        self.SetSizer(sizer)

    def _add_edit(self, sizer):
        sizer.Add(ButtonWithHandler(self, 'Edit'), flag=wx.LEFT|wx.RIGHT, border=5)

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

    def _get_tooltip(self):
        return Tooltip(self, (500, 350))

    def OnKey(self, event):
        self._tooltip.hide()
        event.Skip()

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
            self.popup_timer = wx.CallLater(500, self.OnPopupTimer)

    def _mainframe_has_focus(self):
        return wx.GetTopLevelParent(self.FindFocus()) == \
                wx.GetTopLevelParent(self)

    def OnLeaveWindow(self, event):
        self._stop_popup_timer()

    def OnPopupTimer(self, event):
        if self.Parent.tooltip_allowed(self._tooltip):
            details, title = self._get_details_for_tooltip()
            if details:
                self._tooltip.set_content(details, title)
                self._tooltip.show_at(self._tooltip_position())

    def _get_details_for_tooltip(self):
        kw = self._controller.keyword_name
        return self.plugin.get_keyword_details(kw), kw

    def _tooltip_position(self):
        ms = wx.GetMouseState()
        # -1 ensures that the popup gets focus immediately
        return ms.x-3, ms.y-3

    def OnLeftUp(self, event):
        if event.ControlDown() or event.CmdDown():
            self._navigate_to_user_keyword()
        else:
            if self._has_selected_area() and not self._editing:
                wx.CallAfter(self.OnEdit, event)
            event.Skip()

    def _has_selected_area(self):
        selection = self._value_display.GetSelection()
        if selection is None:
            return False
        return selection[0] == selection[1]

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

    def update_value(self, event=None):
        if self._controller is None:
            return
        if self._controller.is_set:
            self._value_display.set_value(self._controller, self.plugin)
        else:
            self._value_display.clear()

    def get_selected_datafile_controller(self):
        return self._controller.datafile_controller

    def close(self):
        self._controller = None
        self.plugin.unsubscribe(self.update_value, RideImportSetting)

    def highlight(self, text):
        return self._value_display.highlight(text)

    def clear_highlight(self):
        return self._value_display.clear_highlight()

    def contains(self, text):
        return self._value_display.contains(text)


class SettingValueDisplay(wx.TextCtrl):

    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, size=(-1, context.SETTING_ROW_HEIGTH),
                             style=wx.TE_RICH|wx.TE_MULTILINE)
        self.SetEditable(False)
        self._colour_provider = ColorizationSettings(context.SETTINGS)
        self._empty_values()

    def _empty_values(self):
        self._value = None
        self._is_user_keyword = False

    def set_value(self, controller, plugin):
        self._value = controller.display_value
        self._keyword_name = controller.keyword_name
        self._is_user_keyword = plugin.is_user_keyword(self._keyword_name)
        self.SetValue(self._value)
        self._colorize_data()

    def _colorize_data(self, match=None):
        self._colorize_background(match)
        self._colorize_possible_user_keyword()

    def _colorize_background(self, match=None):
        self.SetBackgroundColour(self._get_background_colour(match))

    def _get_background_colour(self, match=None):
        if self._value is None:
            return 'light grey'
        if match is not None and self.contains(match):
            return self._colour_provider.get_highlight_color()
        return 'white'

    def _colorize_possible_user_keyword(self):
        if not self._is_user_keyword:
            return
        font = self.GetFont()
        font.SetUnderlined(True)
        self.SetStyle(0, len(self._keyword_name),
                      wx.TextAttr('blue', self._get_background_colour(), font))

    def clear(self):
        self.Clear()
        self._empty_values()
        self._colorize_background()

    def contains(self, text):
        if self._value is None:
            return False
        return [item for item in self._value.split(' | ') if utils.highlight_matcher(text, item)] != []

    def highlight(self, text):
        self._colorize_data(match=text)

    def clear_highlight(self):
        self._colorize_data()


class DocumentationEditor(SettingEditor):

    def _value_display_control(self):
        ctrl = RideHtmlWindow(self, (-1, 100))
        ctrl.Bind(wx.EVT_LEFT_DOWN, self.OnEdit)
        return ctrl

    def update_value(self, event=None):
        self._value_display.SetPage(self._controller.visible_value)

    def _get_tooltip(self):
        return Tooltip(self, (500, 350), detachable=False)

    def _get_details_for_tooltip(self):
        return self._controller.visible_value, None

    def _crete_editor_dialog(self):
        return DocumentationDialog(self._datafile,
                                   self._controller.editable_value)

    def _set_value(self, value_list, comment):
        if value_list:
            self._controller.editable_value = value_list[0]

    def contains(self, text):
        return False

    def highlight(self, text):
        pass

    def clear_highlight(self):
        pass


class TagsEditor(SettingEditor):

    def __init__(self, parent, controller, plugin, tree):
        SettingEditor.__init__(self, parent, controller, plugin, tree)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        self.SetSizeHints(-1, max(self._tags_display.get_height(), 25))
        event.Skip()

    def _value_display_control(self):
        self._tags_display = TagsDisplay(self, self._controller)
        self._tags_display.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self._tags_display.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        return self._tags_display

    def _add_edit(self, sizer):
        pass

    def contains(self, text):
        return False

    def highlight(self, text):
        pass

    def clear_highlight(self):
        pass

    def close(self):
        self._tags_display.close()
        SettingEditor.close(self)


class TestCaseEditor(_RobotTableEditor):
    _settings_open_id = 'test case settings open'

    def _populate(self):
        self.header = self._create_header(self.controller.name)
        self.sizer.Add(self.header, 0, wx.EXPAND|wx.ALL, 5)
        self._add_settings()
        self.sizer.Add((0,10))
        self._create_kweditor()
        self.plugin.subscribe(self._name_changed, RideItemNameChanged)

    def _create_kweditor(self):
        self.kweditor = KeywordEditor(self, self.controller, self._tree)
        self.sizer.Add(self.kweditor, 1, wx.EXPAND|wx.ALL, 2)
        self._editors.append(self.kweditor)

    def _name_changed(self, data):
        if data.item == self.controller:
            self.header.SetLabel(data.item.name)

    def close(self):
        for editor in self._editors:
            editor.close()
        _RobotTableEditor.close(self)
        self.kweditor.close()
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


class UserKeywordHeader(HorizontalSizer):

    def __init__(self):
        HorizontalSizer.__init__(self)

    def SetLabel(self, label):
        self._header.SetLabel(label)

    def add_header(self, header):
        self._header = header
        self.add_expanding(self._header)


class UserKeywordEditor(TestCaseEditor):
    _settings_open_id = 'user keyword settings open'

    def _create_header(self, name):
        sizer = UserKeywordHeader()
        sizer.add_header(_RobotTableEditor._create_header(self, name))
        sizer.add(ButtonWithHandler(self, 'Find Usages', self._on_show_usages))
        return sizer

    def _on_show_usages(self, event):
        Usages(self.controller, self._tree.highlight).show()


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

    def update_value(self):
        pass

    def close(self):
        pass

    def highlight(self, text, expand=False):
        pass


class VariablesListEditor(_AbstractListEditor):
    _titles = ['Variable', 'Value', 'Comment']
    _buttons = ['Add Scalar', 'Add List']

    def __init__(self, parent, tree, controller):
        PUBLISHER.subscribe(self._update_vars, 'ride.variable.added', key=self)
        PUBLISHER.subscribe(self._update_vars, 'ride.variable.updated', key=self)
        PUBLISHER.subscribe(self._update_vars, 'ride.variable.removed', key=self)
        _AbstractListEditor.__init__(self, parent, tree, controller)

    def _update_vars(self, event):
        ListEditor.update_data(self)

    def get_column_values(self, item):
        return [item.name, item.value if isinstance(item.value, basestring)
                            else ' | '.join(item.value), item.comment]

    def OnMoveUp(self, event):
        _AbstractListEditor.OnMoveUp(self, event)
        self._list.SetFocus()

    def OnMoveDown(self, event):
        _AbstractListEditor.OnMoveDown(self, event)
        self._list.SetFocus()

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
            name, value = dlg.get_value()
            var.execute(UpdateVariable(name, value, dlg.get_comment()))
            self.update_data()
        dlg.Destroy()

    def close(self):
        PUBLISHER.unsubscribe_all(key=self)


class ImportSettingListEditor(_AbstractListEditor):
    _titles = ['Import', 'Name / Path', 'Arguments', 'Comment']
    _buttons = ['Add Library', 'Add Resource', 'Add Variables']

    def OnLeftClick(self, event):
        if not self.is_selected:
            return
        if wx.GetMouseState().ControlDown() or wx.GetMouseState().CmdDown():
            self.navigate_to_tree()

    def navigate_to_tree(self):
        setting = self._get_setting()
        if self.has_link_target(setting):
            self._tree.select_node_by_data(setting.get_target_controller())

    def has_link_target(self, controller):
        return controller.type == 'Resource' and controller.resolved_path

    def OnEdit(self, event):
        setting = self._get_setting()
        self._show_import_editor_dialog(EditorDialog(setting),
                                        setting.set_value, setting)

    def OnAddLibrary(self, event):
        self._show_import_editor_dialog(LibraryDialog,
                                        self._controller.add_library)

    def OnAddResource(self, event):
        self._show_import_editor_dialog(ResourceDialog,
                                        self._controller.add_resource)

    def OnAddVariables(self, event):
        self._show_import_editor_dialog(VariablesDialog,
                                        self._controller.add_variables)

    def _get_setting(self):
        return self._controller[self._selection]

    def _show_import_editor_dialog(self, dialog, creator_or_setter, item=None):
        dlg = dialog(self._controller.datafile, item=item)
        if dlg.ShowModal() == wx.ID_OK:
            ctrl = creator_or_setter(*dlg.get_value())
            ctrl.set_comment(dlg.get_comment())
            self.update_data()
        dlg.Destroy()

    def get_column_values(self, item):
        return [item.type, item.name, item.display_value, item.comment]


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


class EditorCreator(object):
    # TODO: Should not use robot.model classes here
    _EDITORS = ((TestDataDirectory, InitFileEditor),
                (ResourceFile, ResourceFileEditor),
                (TestCase, TestCaseEditor),
                (TestCaseFile, TestCaseFileEditor),
                (UserKeyword, UserKeywordEditor),
                (Variable, VariableEditorChooser))

    def __init__(self, editor_registerer):
        self._editor_registerer = editor_registerer
        self._editor = None

    def register_editors(self):
        for item, editorclass in self._EDITORS:
            self._editor_registerer(item, editorclass)

    def editor_for(self, plugin, editor_panel, tree):
        controller = plugin.get_selected_item()
        if not controller or not controller.data or \
                isinstance(controller, ChiefController):
            if self._editor:
                return self._editor
            self._editor = WelcomePage(editor_panel)
            return self._editor
        if self._editor and isinstance(controller, VariableController) and \
                controller.datafile_controller is self._editor.controller:
            return self._editor
        editor_class = plugin.get_editor(controller.data.__class__)
        if self._editor:
            self._editor.destroy()
        editor_panel.Show(False)
        self._editor = editor_class(plugin, editor_panel, controller, tree)
        return self._editor
