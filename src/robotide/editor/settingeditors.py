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

import wx
from wx import Colour

from .editordialogs import editor_dialog, DocumentationDialog, MetadataDialog, \
    ScalarVariableDialog, ListVariableDialog, DictionaryVariableDialog, LibraryDialog, \
    ResourceDialog, VariablesDialog
from .formatters import ListToStringFormatter
from .gridcolorizer import ColorizationSettings
from .listeditor import ListEditor
from .popupwindow import HtmlPopupWindow
from .tags import TagsDisplay
from .. import context
from .. import utils
from ..controller import ctrlcommands
from ..publish import PUBLISHER
from ..publish.messages import (RideImportSetting, RideOpenVariableDialog, RideExecuteSpecXmlImport, RideSaving,
                                RideVariableAdded, RideVariableUpdated, RideVariableRemoved)
from ..utils.highlightmatcher import highlight_matcher
from ..widgets import ButtonWithHandler, Label, HtmlWindow, PopupMenu, PopupMenuItems, HtmlDialog


class SettingEditor(wx.Panel):
    popup_timer = None

    def __init__(self, parent, controller, plugin, tree):
        wx.Panel.__init__(self, parent)
        from ..preferences import RideSettings
        _settings = RideSettings()
        self.general_settings = _settings['General']
        self.color_background = self.general_settings.get('background', 'light grey')
        self.color_foreground = self.general_settings.get('foreground', 'black')
        self.color_secondary_background = self.general_settings.get('secondary background', 'light grey')
        self.color_secondary_foreground = self.general_settings.get('secondary foreground', 'black')
        self.color_background_help = self.general_settings.get('background help', (240, 242, 80))
        self.color_foreground_text = self.general_settings.get('foreground text', (7, 0, 70))
        self.font_face = self.general_settings.get('font face', '')
        self.font_size = self.general_settings.get('font size', 11)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetOwnBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        self.SetOwnForegroundColour(Colour(self.color_foreground))
        self._controller = controller
        self.plugin = plugin
        self._datafile = controller.datafile
        self._create_controls()
        self._tree = tree
        self._editing = False
        self.font = self._tree.GetFont()
        self.font.SetFaceName(self.font_face)
        self.font.SetPointSize(self.font_size)
        self._tree.SetFont(self.font)
        self._tree.Refresh()
        self.plugin.subscribe(self._ps_on_update_value, RideImportSetting)

    def _create_controls(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((5, 0))
        sizer.Add(Label(
            self, label=self._controller.label,
            size=(context.SETTING_LABEL_WIDTH, context.SETTING_ROW_HEIGHT)))
        self._value_display = self._create_value_display()
        self.update_value()
        self._tooltip = self._get_tooltip()
        sizer.Add(self._value_display, 1, wx.EXPAND)
        self._add_edit(sizer)
        sizer.Add(ButtonWithHandler(self, 'Clear', color_secondary_foreground=self.color_secondary_foreground,
                                    color_secondary_background=self.color_secondary_background))
        sizer.Layout()
        self.SetSizer(sizer)

    def _add_edit(self, sizer):
        sizer.Add(
            ButtonWithHandler(self, 'Edit', color_secondary_foreground=self.color_secondary_foreground,
                                    color_secondary_background=self.color_secondary_background),
            flag=wx.LEFT | wx.RIGHT, border=5)

    def _create_value_display(self):
        display = self._value_display_control()
        display.Bind(wx.EVT_ENTER_WINDOW, self.on_enter_window)
        display.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window)
        display.Bind(wx.EVT_WINDOW_DESTROY, self.on_window_destroy)
        display.Bind(wx.EVT_MOTION, self.on_display_motion)
        return display

    def _value_display_control(self):
        ctrl = SettingValueDisplay(self)
        ctrl.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        ctrl.Bind(wx.EVT_KEY_DOWN, self.on_key)
        return ctrl

    def _get_tooltip(self):
        return HtmlPopupWindow(self, (500, 350))

    def on_key(self, event):
        try:
            self._tooltip.hide()
        except AttributeError:
            pass
        event.Skip()

    def on_display_motion(self, event):
        try:
            self._tooltip.hide()
        except AttributeError:
            pass

    def refresh(self, controller):
        self._controller = controller
        self.update_value()

    def refresh_datafile(self, item, event):
        self._tree.refresh_datafile(item, event)

    def on_edit(self, event=None):
        self._hide_tooltip()
        self._editing = True
        dlg = self._create_editor_dialog()
        if dlg.ShowModal() == wx.ID_OK:
            value = dlg.get_value()
            comment = dlg.get_comment()
            if value != ['']:
                self._set_value(value, comment)
                self._update_and_notify()
            else:
                wx.CallAfter(self.on_clear, event)
        dlg.Destroy()
        self._editing = False

    def _create_editor_dialog(self):
        dlg_class = editor_dialog(self._controller)
        return dlg_class(self._datafile, self._controller, self.plugin)

    def _set_value(self, value_list, comment):
        self._controller.execute(ctrlcommands.SetValues(value_list, comment))

    def _hide_tooltip(self):
        self._stop_popup_timer()
        try:
            self._tooltip.hide()
        except AttributeError:
            pass

    def _stop_popup_timer(self):
        if hasattr(self, 'popup_timer') and self.popup_timer is not None:
            self.popup_timer.Stop()

    def on_enter_window(self, event):
        if self._mainframe_has_focus():
            self.popup_timer = wx.CallLater(500, self.on_popup_timer, event)

    def _mainframe_has_focus(self):
        return wx.GetTopLevelParent(self.FindFocus()) == \
            wx.GetTopLevelParent(self)

    def on_window_destroy(self, event):
        self._stop_popup_timer()
        try:
            self._tooltip.hide()
        except AttributeError:
            pass
        event.Skip()

    def on_leave_window(self, event):
        self.on_window_destroy(event)

    def on_popup_timer(self, event):
        _ = event
        _tooltipallowed = False
        # DEBUG: This prevents tool tip for ex. Template edit field in wxPhoenix
        try:
            _tooltipallowed = self.Parent.tooltip_allowed(self._tooltip)
        except AttributeError:
            # print("DEBUG: There was an attempt to show a Tool Tip.\n")
            pass
        if _tooltipallowed:
            details, title = self._get_details_for_tooltip()
            if details:
                self._tooltip.set_content(details, title)
                self._tooltip.show_at(self._tooltip_position())

    def _get_details_for_tooltip(self):
        kw = self._controller.keyword_name
        return self.plugin.get_keyword_details(kw), kw

    @staticmethod
    def _tooltip_position():
        ms = wx.GetMouseState()
        # ensure that the popup gets focus immediately
        return ms.x-3, ms.y-3

    def on_left_up(self, event):
        if event.ControlDown() or event.CmdDown():
            self._navigate_to_user_keyword()
        else:
            if self._has_selected_area() and not self._editing:
                wx.CallAfter(self.on_edit, event)
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

    def on_clear(self, event):
        _ = event
        self._controller.execute(ctrlcommands.ClearSetting())
        self._update_and_notify()

    def _ps_on_update_value(self, message):
        _ = message
        self.update_value()

    def update_value(self):
        if self._controller is None:
            return
        if self._controller.is_set:
            self._value_display.set_value(self._controller, self.plugin)
        else:
            self._value_display.clear_field()

    def get_selected_datafile_controller(self):
        return self._controller.datafile_controller

    def close(self):
        self._controller = None
        self.plugin.unsubscribe(self._ps_on_update_value, RideImportSetting)

    def highlight(self, text):
        return self._value_display.highlight(text)

    def clear_highlight(self):
        return self._value_display.clear_highlight()

    def contains(self, text):
        return self._value_display.contains(text)


class SettingValueDisplay(wx.TextCtrl, HtmlPopupWindow):
    _is_user_keyword = False
    _keyword_name = None
    _value = None

    def __init__(self, parent):
        wx.TextCtrl.__init__(
            self, parent, size=(-1, context.SETTING_ROW_HEIGHT),
            style=wx.TE_RICH | wx.TE_MULTILINE | wx.TE_NOHIDESEL)
        """
        self.SetBackgroundColour(Colour(200, 222, 40))
        self.SetOwnBackgroundColour(Colour(200, 222, 40))
        self.SetForegroundColour(Colour(7, 0, 70))
        self.SetOwnForegroundColour(Colour(7, 0, 70))
        """
        self.color_secondary_background = parent.color_secondary_background
        self.SetBackgroundColour(Colour(self.color_secondary_background))
        self.SetEditable(False)
        self._colour_provider = ColorizationSettings(
            parent.plugin.global_settings['Grid'])
        self._empty_values()

    def _empty_values(self):
        self._value = None
        self._is_user_keyword = False

    def set_value(self, controller, plugin):
        self._value = controller.display_value
        self._keyword_name = controller.keyword_name
        try:
            self._is_user_keyword = plugin.is_user_keyword(self._keyword_name)
        except AttributeError:
            self._is_user_keyword = False
        self.SetValue(self._value)
        self._colorize_data()

    def _colorize_data(self, match=None):
        self._colorize_background(match)
        self._colorize_possible_user_keyword()

    def _colorize_background(self, match=None):
        self.SetBackgroundColour(self._get_background_colour(match))

    def _get_background_colour(self, match=None):
        if self._value is None:
            return Colour(self.color_secondary_background)
        if match is not None and self.contains(match):
            return self._colour_provider.get_highlight_color()
        return Colour(self.color_secondary_background)  # 'white'  # Colour(200, 222, 40)

    def _colorize_possible_user_keyword(self):
        if not self._is_user_keyword:
            return
        font = self.GetFont()
        font.SetUnderlined(True)
        user_kw_color = self._colour_provider.get_text_color('user keyword')
        self.SetStyle(0, len(self._keyword_name),
                      wx.TextAttr(user_kw_color, self._get_background_colour(), font))

    def clear_field(self):
        self.Clear()
        self._empty_values()
        self._colorize_background()

    def contains(self, text):
        if self._value is None:
            return False
        return [item for item in self._value.split(' | ')
                if highlight_matcher(text, item)] != []

    def highlight(self, text):
        self._colorize_data(match=text)

    def clear_highlight(self):
        self._colorize_data()


class DocumentationEditor(SettingEditor):

    def __init__(self, parent, controller, plugin, tree):
        # print(f"DEBUG: DocumentationEditor parent={parent} controller={controller}")
        SettingEditor.__init__(self, parent, controller, plugin, tree)

    def _value_display_control(self):
        ctrl = HtmlWindow(self, (-1, 100), color_background=self.color_secondary_background,
                          color_foreground=self.color_secondary_foreground)
        ctrl.SetBackgroundColour(Colour(self.color_secondary_background))
        ctrl.SetForegroundColour(Colour(self.color_secondary_foreground))
        ctrl.Bind(wx.EVT_LEFT_DOWN, self.on_edit)
        return ctrl

    def update_value(self):
        if self._controller:
            self._value_display.set_content(self._controller.visible_value)

    def on_key(self, event):
        event.Skip()

    def on_display_motion(self, event):
        """ Just ignoring it """
        pass

    def _hide_tooltip(self):
        """ Just ignoring it """
        pass

    def _create_editor_dialog(self):
        return DocumentationDialog(self._datafile,
                                   self._controller.editable_value)

    def _set_value(self, value_list, comment):
        if value_list:
            self._controller.execute(ctrlcommands.UpdateDocumentation(value_list[0]))

    def contains(self, text):
        return False

    def highlight(self, text):
        """ Just ignoring it """
        pass

    def clear_highlight(self):
        """ Just ignoring it """
        pass


class TagsEditor(SettingEditor):

    def __init__(self, parent, controller, plugin, tree):
        SettingEditor.__init__(self, parent, controller, plugin, tree)
        self.plugin.subscribe(self._saving, RideSaving)

    def _saving(self, message):
        _ = message
        self._tags_display.saving()

    def _value_display_control(self):
        self._tags_display = TagsDisplay(self, self._controller)
        self._tags_display.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self._tags_display.Bind(wx.EVT_KEY_DOWN, self.on_key)
        return self._tags_display

    def contains(self, text):
        return False

    def highlight(self, text):
        """ Just ignoring it """
        pass

    def clear_highlight(self):
        """ Just ignoring it """
        pass

    def close(self):
        self._tags_display.close()
        self.plugin.unsubscribe(self._saving, RideSaving)
        SettingEditor.close(self)


class _AbstractListEditor(ListEditor):
    _titles = []

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

    def update_value(self):
        """ Just ignoring it """
        pass

    def close(self):
        """ Just ignoring it """
        pass

    def highlight(self, text, expand=False):
        """ Just ignoring it """
        pass


class VariablesListEditor(_AbstractListEditor):
    _titles = ['Variable', 'Value', 'Comment']
    _buttons = ['Add Scalar', 'Add List', 'Add Dict']

    def __init__(self, parent, tree, controller):
        PUBLISHER.subscribe(
            self._update_vars, RideVariableAdded)
        PUBLISHER.subscribe(
            self._update_vars, RideVariableUpdated)
        PUBLISHER.subscribe(
            self._update_vars, RideVariableRemoved)
        PUBLISHER.subscribe(self._open_variable_dialog, RideOpenVariableDialog)
        _AbstractListEditor.__init__(self, parent, tree, controller)

    def _update_vars(self, message):
        _ = message
        ListEditor.update_data(self)

    @staticmethod
    def get_column_values(item):
        return [item.name, item.value
                if isinstance(item.value, str)
                else ' | '.join(item.value),
                ListToStringFormatter(item.comment).value]

    def on_move_up(self, event):
        _AbstractListEditor.on_move_up(self, event)
        self._list.SetFocus()

    def on_move_down(self, event):
        _AbstractListEditor.on_move_down(self, event)
        self._list.SetFocus()

    def on_add_scalar(self, event):
        _ = event
        self._show_dialog(
            ScalarVariableDialog(self._controller))

    def on_add_list(self, event):
        _ = event
        self._show_dialog(
            ListVariableDialog(self._controller, plugin=self.Parent.plugin))

    def on_add_dict(self, event):
        _ = event
        self._show_dialog(
            DictionaryVariableDialog(self._controller,
                                     plugin=self.Parent.plugin))

    def _show_dialog(self, dlg):
        if dlg.ShowModal() == wx.ID_OK:
            ctrl = self._controller.add_variable(*dlg.get_value())
            ctrl.set_comment(dlg.get_comment())
            self.update_data()
        dlg.Destroy()

    def on_edit(self, event):
        var = self._controller[self._selection]
        self._open_var_dialog(var)

    def _open_variable_dialog(self, message):
        # Prevent opening a dialog if self has been destroyed
        if self:
            self._open_var_dialog(message.controller)

    def _open_var_dialog(self, var):
        var_name = var.name.lower()
        dlg = None
        if var_name.startswith('${'):
            dlg = ScalarVariableDialog(self._controller, item=var)
        elif var_name.startswith('@{'):
            dlg = ListVariableDialog(self._controller, item=var,
                                     plugin=self.Parent.plugin)
        elif var_name.startswith('&{'):
            dlg = DictionaryVariableDialog(self._controller, item=var,
                                           plugin=self.Parent.plugin)
        if dlg:  # DEBUG robot accepts % variable definition
            if dlg.ShowModal() == wx.ID_OK:
                name, value = dlg.get_value()
                var.execute(ctrlcommands.UpdateVariable(name, value, dlg.get_comment()))
                self.update_data()
            dlg.Destroy()

    def close(self):
        PUBLISHER.unsubscribe_all(self)


class ImportSettingListEditor(_AbstractListEditor):
    _titles = ['Import', 'Name / Path', 'Arguments', 'Comment']
    _buttons = ['Library', 'Resource', 'Variables', 'Import Failed Help']

    def __init__(self, parent, tree, controller):
        self._import_failed_shown = False
        _AbstractListEditor.__init__(self, parent, tree, controller)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetOwnBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        self.SetOwnForegroundColour(Colour(self.color_foreground))

    def _create_buttons(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(Label(
            self, label='Add Import', size=wx.Size(120, 20),
            style=wx.ALIGN_CENTER))
        for label in self._buttons:
            sizer.Add(ButtonWithHandler(self, label, width=120,
                                        color_secondary_foreground=self.color_secondary_foreground,
                                        color_secondary_background=self.color_secondary_background), 0, wx.ALL, 1)
        return sizer

    def on_left_click(self, event):
        if not self.is_selected:
            return
        if wx.GetMouseState().ControlDown() or wx.GetMouseState().CmdDown():
            self.navigate_to_tree()

    def navigate_to_tree(self):
        setting = self._get_setting()
        if self.has_link_target(setting):
            self._tree.select_node_by_data(setting.get_imported_controller())

    def has_link_target(self, controller):
        return controller.is_resource and controller.get_imported_controller()

    def has_error(self, controller):
        return controller.has_error()

    def on_right_click(self, event):
        PopupMenu(self, PopupMenuItems(self, self._create_item_menu()))

    def _create_item_menu(self):
        menu = self._menu
        item = self._controller[self._selection]
        if item.has_error() and item.type == 'Library':
            menu = menu[:] + ['Import Library Spec XML']
        return menu

    @staticmethod
    def on_import_library_spec_xml(event):
        _ = event
        RideExecuteSpecXmlImport().publish()

    def on_edit(self, event):
        setting = self._get_setting()
        self._show_import_editor_dialog(
            editor_dialog(setting),
            lambda v, c: setting.execute(ctrlcommands.SetValues(v, c)),
            setting, on_empty=self._delete_selected)

    def on_library(self, event):
        _ = event
        self._show_import_editor_dialog(
            LibraryDialog,
            lambda v, c: self._controller.execute(ctrlcommands.AddLibrary(v, c)))

    def on_resource(self, event):
        _ = event
        self._show_import_editor_dialog(
            ResourceDialog,
            lambda v, c: self._controller.execute(ctrlcommands.AddResource(v, c)))

    def on_variables(self, event):
        _ = event
        self._show_import_editor_dialog(
            VariablesDialog,
            lambda v, c:
                self._controller.execute(ctrlcommands.AddVariablesFileImport(v, c)))

    def on_import_failed_help(self, event):
        _ = event
        if self._import_failed_shown:
            return
        dialog = HtmlDialog('Import failure handling', '''
        <br>Possible corrections and notes:<br>
        <ul>
            <li>Import failure is shown with red color.</li>
            <li>See Tools / View RIDE Log for detailed information about the failure.</li>
            <li>If the import contains a variable that RIDE has not initialized, consider adding the variable
            to variable table with a default value.</li>
            <li>For library import failure: Consider importing library spec XML (Tools / Import Library Spec XML or by
            adding the XML file with the correct name to PYTHONPATH) to enable keyword completion
            for example for Java libraries.
            Library spec XML can be created using libdoc tool from Robot Framework.
            For more information see 
            <a href="https://github.com/robotframework/RIDE/wiki/Keyword-Completion#wiki-using-library-specs">wiki</a>.
            </li>
        </ul>''')
        dialog.Bind(wx.EVT_CLOSE, self._import_failed_help_closed)
        dialog.Show()
        self._import_failed_shown = True

    def _import_failed_help_closed(self, event):
        self._import_failed_shown = False
        event.Skip()

    def _get_setting(self):
        return self._controller[self._selection]

    def _show_import_editor_dialog(
            self, dialog, creator_or_setter, item=None, on_empty=None):
        dlg = dialog(self._controller, item=item)
        if dlg.ShowModal() == wx.ID_OK:
            value = dlg.get_value()
            if not self._empty_name(value):
                creator_or_setter(value, dlg.get_comment())
            elif on_empty:
                on_empty()
            self.update_data()
        dlg.Destroy()

    @staticmethod
    def _empty_name(value):
        return not value[0]

    @staticmethod
    def get_column_values(item):
        return [item.type, item.name, item.display_value,
                ListToStringFormatter(item.comment).value]


class MetadataListEditor(_AbstractListEditor):
    _titles = ['Metadata', 'Value', 'Comment']
    _buttons = ['Add Metadata']
    _sortable = False

    def on_edit(self, event):
        meta = self._controller[self._selection]
        dlg = MetadataDialog(self._controller.datafile, item=meta)
        if dlg.ShowModal() == wx.ID_OK:
            meta.set_value(*dlg.get_value())
            meta.set_comment(dlg.get_comment())
            self.update_data()
        dlg.Destroy()

    def on_add_metadata(self, event):
        _ = event
        dlg = MetadataDialog(self._controller.datafile)
        if dlg.ShowModal() == wx.ID_OK:
            ctrl = self._controller.add_metadata(*dlg.get_value())
            ctrl.set_comment(dlg.get_comment())
            self.update_data()
        dlg.Destroy()

    @staticmethod
    def get_column_values(item):
        return [item.name, utils.html_escape(item.value),
                ListToStringFormatter(item.comment).value]
