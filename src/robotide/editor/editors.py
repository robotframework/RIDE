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

import builtins
import wx

from abc import abstractmethod
from wx import Colour
from .settingeditors import (
    DocumentationEditor, SettingEditor, TagsEditor,
    ImportSettingListEditor, VariablesListEditor, MetadataListEditor)
from .. import robotapi, context
from ..controller.settingcontrollers import (
    DocumentationController, VariableController, TagsController)
from ..publish import (
    RideItemSettingsChanged, RideInitFileRemoved, RideFileNameChanged)
from ..usages.UsageRunner import ResourceFileUsages
from ..widgets import (
    ButtonWithHandler, Label, HeaderLabel, HorizontalSizer, HtmlWindow)

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

LIGHT_GREY = 'light grey'


class WelcomePage(HtmlWindow):
    undo = cut = copy = paste = delete = comment = uncomment = save \
        = show_content_assist = tree_item_selected = lambda *args: None

    def __init__(self, parent):
        HtmlWindow.__init__(self, parent, text=context.get_about_ride())

    def close(self):
        self.Show(False)

    def w_destroy(self):
        self.close()
        self.Destroy()


class EditorPanel(wx.lib.scrolledpanel.ScrolledPanel):
    """Base class for all editor panels"""
    # DEBUG: Move outside default editor package, document
    name = doc = ''
    title = None
    undo = cut = copy = paste = delete = comment = uncomment = save \
        = show_content_assist = lambda self: None

    def __init__(self, plugin, parent, controller, tree):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        from ..preferences import RideSettings
        _settings = RideSettings()
        self.general_settings = _settings['General']
        self.color_background = self.general_settings.get('background', LIGHT_GREY)
        self.color_foreground = self.general_settings.get('foreground', 'black')
        self.color_secondary_background = self.general_settings.get('secondary background', LIGHT_GREY)
        self.color_secondary_foreground = self.general_settings.get('secondary foreground', 'black')
        self.color_background_help = self.general_settings.get('background help', (240, 242, 80))
        self.color_foreground_text = self.general_settings.get('foreground text', (7, 0, 70))
        self.font_face = self.general_settings.get('font face', '')
        self.font_size = self.general_settings.get('font size', 11)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        self.plugin = plugin
        self.controller = controller
        try:
            self.language = controller.datafile_controller.language
        except AttributeError:
            self.language = ['en']
        self._tree = tree

    def tree_item_selected(self, item):
        """ Maybe this needs to be published """
        pass


class _RobotTableEditor(EditorPanel):
    name = 'table'
    doc = 'table editor'
    kweditor = None
    _settings_open_id = 'robot table settings open'

    def __init__(self, plugin, parent, controller, tree):
        EditorPanel.__init__(self, plugin, parent, controller, tree)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.Bind(wx.EVT_IDLE, self.on_idle)
        self.SetSizer(self.sizer)
        if self.title:
            self.sizer.Add(self._create_header(self.title),
                           0, wx.EXPAND | wx.ALL, 6)
        self._editors = []
        self._last_shown_tooltip = None
        self._reset_last_show_tooltip()
        self._populate()
        self.plugin.subscribe(self._settings_changed, RideItemSettingsChanged)

    @abstractmethod
    def _populate(self):
        pass

    def _should_settings_be_open(self):
        if self._settings_open_id not in self.plugin.global_settings:
            return False
        return self.plugin.global_settings[self._settings_open_id]

    def _store_settings_open_status(self):
        self.plugin.global_settings[self._settings_open_id] = \
            self._settings.IsExpanded()

    def _settings_changed(self, message):
        if message.item == self.controller:
            for editor in self._editors:
                editor.update_value()

    def on_idle(self, event):
        __ = event
        if self._last_shown_tooltip and self._mouse_outside_tooltip():
            self._last_shown_tooltip.hide()
            self._reset_last_show_tooltip()

    def _mouse_outside_tooltip(self):
        mx, my = wx.GetMousePosition()
        tx, ty = self._last_shown_tooltip.screen_position
        dx, dy = self._last_shown_tooltip.pw_size
        return (mx < tx or mx > tx+dx) or (my < ty or my > ty+dy)

    def tooltip_allowed(self, tooltip):
        if wx.GetMouseState().ControlDown() or \
                self._last_shown_tooltip is tooltip:
            return False
        self._last_shown_tooltip = tooltip
        return True

    def _reset_last_show_tooltip(self):
        self._last_shown_tooltip = None

    def close(self):
        self.plugin.unsubscribe(
            self._settings_changed, RideItemSettingsChanged)
        self.Unbind(wx.EVT_MOTION)
        self.Show(False)

    def w_destroy(self):
        self.close()
        self.DestroyLater()

    def _create_header(self, text, readonly=False):
        if readonly:
            text += _(' (READ ONLY)')
        self._title_display = HeaderLabel(self, text)
        return self._title_display

    def _add_settings(self):
        self._settings = self._create_settings()
        self._restore_settings_open_status()
        self._editors.append(self._settings)
        self.sizer.Add(self._settings, 0, wx.ALL | wx.EXPAND, 2)

    def _create_settings(self):
        settings = Settings(self)
        settings.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._collabsible_changed)
        settings.build(self.controller.settings, self.plugin, self._tree)
        return settings

    def _restore_settings_open_status(self):
        if self._should_settings_be_open():
            self._settings.Expand()
            wx.CallAfter(self._collabsible_changed)
        else:
            self._settings.Collapse()
            self.GetSizer().Layout()
            self.Refresh()
        self.Parent.GetSizer().Layout()
        self.Parent.Refresh()

    def _collabsible_changed(self, event=None):
        self._store_settings_open_status()
        self.GetSizer().Layout()
        self.Refresh()
        self.Parent.GetSizer().Layout()
        self.Parent.Refresh()
        if event:
            event.Skip()

    def highlight_cell(self, obj, row, column):
        """Highlight the given object at the given row and column"""
        if isinstance(obj, robotapi.Setting):
            setting_editor = self._get_settings_editor(obj)
            if setting_editor and hasattr(setting_editor, "highlight"):
                setting_editor.highlight(column)
        elif row >= 0 and column >= 0:
            self.kweditor.select(row, column)

    def _get_settings_editor(self, setting):
        """Return the settings editor for the given setting object"""
        for child in self.GetChildren():
            if isinstance(child, SettingEditor) and child._item == setting:
                return child
        return None

    def highlight(self, text, expand=True):
        for editor in self._editors:
            editor.highlight(text, expand=expand)


class Settings(wx.CollapsiblePane):
    BORDER = 2

    def __init__(self, parent):
        wx.CollapsiblePane.__init__(
            self, parent, wx.ID_ANY, _('Settings'),
            style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE)
        from ..preferences import RideSettings
        _settings = RideSettings()
        self.general_settings = _settings['General']
        self.color_background = self.general_settings.get('background', LIGHT_GREY)
        self.color_foreground = self.general_settings.get('foreground', 'black')
        self.color_secondary_background = self.general_settings.get('secondary background', LIGHT_GREY)
        self.color_secondary_foreground = self.general_settings.get('secondary foreground', 'black')
        self.color_background_help = self.general_settings.get('background help', (240, 242, 80))
        self.color_foreground_text = self.general_settings.get('foreground text', (7, 0, 70))
        self.font_face = self.general_settings.get('font face', '')
        self.font_size = self.general_settings.get('font size', 11)
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self._editors = []
        self.Bind(wx.EVT_SIZE, self._recalc_size)

    def Expand(self):
        wx.CollapsiblePane.Expand(self)

    def GetPane(self):
        pane = wx.CollapsiblePane.GetPane(self)
        """
        pane.SetBackgroundColour(Colour(200, 222, 40))
        pane.SetOwnBackgroundColour(Colour(200, 222, 40))
        pane.SetForegroundColour(Colour(7, 0, 70))
        pane.SetOwnForegroundColour(Colour(7, 0, 70))
        """
        pane.tooltip_allowed = self.GetParent().tooltip_allowed
        return pane

    def close(self):
        for editor in self._editors:
            editor.close()

    def update_value(self):
        for editor in self._editors:
            editor.update_value()

    def create_editor_for(self, controller, plugin, tree):
        editor_cls = self._get_editor_class(controller)
        return editor_cls(self.GetPane(), controller, plugin, tree)

    @staticmethod
    def _get_editor_class(controller):
        if isinstance(controller, DocumentationController):
            return DocumentationEditor
        if isinstance(controller, TagsController):
            return TagsEditor
        return SettingEditor

    def build(self, settings, plugin, tree):
        for setting in settings:
            # print(f"DEBUG: editors.py Settings build plugin={plugin.name} setting={setting.label}")
            editor = self.create_editor_for(setting, plugin, tree)
            self._sizer.Add(editor, 0, wx.ALL | wx.EXPAND, self.BORDER)
            self._editors.append(editor)
            editor.Refresh()
        self.GetPane().SetSizer(self._sizer)
        self._sizer.Layout()

    def _recalc_size(self, event=None):
        expand_button_height = 34
        total_height = 0
        if self.IsExpanded():
            for editor in self._editors:
                total_height += editor.BestSize[1]
                total_height += 2 * self.BORDER + 1
        self.SetSizeHints(-1, total_height + expand_button_height)
        if event:
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


class _FileEditor(_RobotTableEditor):

    def __init__(self, *args):
        _RobotTableEditor.__init__(self, *args)
        self.SetupScrolling()
        self.plugin.subscribe(
            self._update_source_and_name, RideFileNameChanged)

    def _update_source(self, message=None):
        _ = message
        self._source.SetValue(self.controller.data.source)

    def _update_source_and_name(self, message):
        _ = message
        self._title_display.SetLabel(self.controller.name)
        self._update_source()

    def tree_item_selected(self, item):
        if isinstance(item, VariableController):
            self._var_editor.select(item.name)

    def _populate(self):
        datafile = self.controller.data
        header = self._create_header(
            datafile.name, not self.controller.is_modifiable())
        self.sizer.Add(header, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(self._create_source_label(datafile.source), 0, wx.EXPAND | wx.ALL, 1)
        self.sizer.Add((0, 10))
        self._add_settings()
        self._add_import_settings()
        self._add_variable_table()

    def _create_source_label(self, source):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((5, 0))
        sizer.Add(Label(self, label=_('Source'), size=(context.SETTING_LABEL_WIDTH, context.SETTING_ROW_HEIGHT)))
        self._source = wx.TextCtrl(self, style=wx.TE_READONLY | wx.NO_BORDER)
        self._source.SetBackgroundColour(Colour(self.color_background))
        self._source.SetForegroundColour(Colour(self.color_foreground))

        self._source.SetValue(source)
        self._source.SetMaxSize(wx.Size(-1, context.SETTING_ROW_HEIGHT))
        sizer.Add(self._source, 1, wx.EXPAND)
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
        self.plugin.unsubscribe(self._update_source_and_name, RideFileNameChanged)
        for editor in self._editors:
            editor.close()
        self._editors = []
        _RobotTableEditor.close(self)

    # Stubs so that ctrl+d ctrl+i don't throw exceptions
    delete_rows = insert_rows = lambda s: None


class FindUsagesHeader(HorizontalSizer):

    def __init__(self, parent, header, usages_callback, color_foreground, color_background):
        HorizontalSizer.__init__(self)
        self._header = HeaderLabel(parent, header)
        self.add_expanding(self._header)
        self.add_sizer(ButtonWithHandler(parent, _('Find Usages'), handler=usages_callback,
                                         color_secondary_foreground=color_foreground,
                                         color_secondary_background=color_background))

    def SetLabel(self, label):
        self._header.SetLabel(label)


class ResourceFileEditor(_FileEditor):
    _settings_open_id = 'resource file settings open'

    def _create_header(self, text, readonly=False):
        if readonly:
            text += _(' (READ ONLY)')

        def cb(event):
            __ = event
            ResourceFileUsages(self.controller, self._tree.highlight).show()
        self._title_display = FindUsagesHeader(self, text, cb, color_foreground=self.color_secondary_foreground,
                                               color_background=self.color_secondary_background)
        return self._title_display


class TestCaseFileEditor(_FileEditor):
    __test__ = False
    _settings_open_id = 'test case file settings open'

    def _populate(self):
        _FileEditor._populate(self)
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
        _ = message
        for setting, editor in zip(self.controller.settings, self._editors):
            editor.refresh_items(setting)

    def close(self):
        self.plugin.unsubscribe(self._init_file_removed, RideInitFileRemoved)
        super().close()
