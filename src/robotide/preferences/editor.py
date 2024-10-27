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

"""A generic, extensible preferences dialog

Usage:

    dialog = PreferenceEditor(parent, title, preferences, style)
    dialog.ShowModal()

preferences is an any object with attribute preferecne_panels, which in turn
is a list or tuple of classes that inherit from PreferencesPanel.

style may have any of the values "auto", "notebook", "tree" or
"single". If style is "auto", the choice of using a single window, a
notebook, or a tree will depend on how many pages will be in the
dialog.

"""

import builtins
import wx
from wx import Colour
from wx.lib.scrolledpanel import ScrolledPanel

from .settings import RideSettings

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

# any more than TREE_THRESHOLD panels when style is "auto" forces
# the UI into showing a hierarchical tree
TREE_THRESHOLD = 5
FONT_SIZE = 'font size'
FONT_FACE = 'font face'


class PreferenceEditor(wx.Dialog):
    """A dialog for showing the preference panels"""
    def __init__(self, parent, title, preferences, style="auto"):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, title, size=(850, 700),
                           style=wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE)
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self._current_panel = None
        self._panels = []
        self._settings = preferences.settings
        self._general_settings = self._settings['General']
        self.font = self.GetFont()
        self.font.SetFaceName(self._general_settings[FONT_FACE])
        self.font.SetPointSize(self._general_settings[FONT_SIZE])
        self.SetFont(self.font)
        self.SetBackgroundColour(Colour(self._general_settings['background']))
        self.SetForegroundColour(Colour(self._general_settings['foreground']))
        self._closing = False

        panels = preferences.preference_panels
        if style not in ("tree", "notebook", "single", "auto"):
            raise AttributeError("invalid style; must be one of 'tree','notebook','single' or 'auto'")

        if style == "tree" or (style == "auto" and len(panels) > TREE_THRESHOLD):
            self._sw = wx.SplitterWindow(self, wx.ID_ANY, style=wx.SP_LIVE_UPDATE | wx.SP_3D)
            self._tree = wx.TreeCtrl(self._sw, wx.ID_ANY, style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS)
            # create a single container which will hold all the
            # preference panels
            self._container = PanelContainer(self._sw, wx.ID_ANY)
            self._sw.SplitVertically(self._tree, self._container, 210)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self._sw, 1, wx.EXPAND)
            self._tree.SetFont(self.font)
            self._tree.SetBackgroundColour(Colour(self._general_settings['background']))
            self._tree.SetOwnBackgroundColour(Colour(self._general_settings['secondary background']))
            self._tree.SetForegroundColour(Colour(self._general_settings['foreground']))
            self._tree.SetOwnForegroundColour(Colour(self._general_settings['secondary foreground']))
            self._tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_tree_selection)
            self._populate_tree(panels)
            self._tree.SelectItem(self._tree.GetFirstChild(self._tree.GetRootItem())[0])
            self.SetSizer(sizer)

        elif style == "notebook" or (style == "auto" and len(panels) > 1):
            # the tabs appear in alphabetical order based on their
            # location. This has the pleasant side effect of "General"
            # coming before "Plugins", but if some plugin adds a
            # location of ("aaa","me first!") it will come before
            # "General". I need some way to order them, though maybe
            # just special-casing "General" to come first might be
            # good enough?
            self._notebook = wx.Notebook(self)
            for panel_class in sorted(panels, key=lambda p: p.location):
                # for a notebook, each notebook page gets a container,
                # and that container will only show one panel
                container = PanelContainer(self._notebook)
                panel = container.AddPanel(panel_class, self._settings)
                container.ShowPanel(panel)
                self._notebook.AddPage(container, panel.GetTitle())
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self._notebook, 1, wx.EXPAND)
            self.SetSizer(sizer)

        else:
            self._container = PanelContainer(self, wx.ID_ANY)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self._container, 1, wx.EXPAND)
            self.SetSizer(sizer)

            panel = self._container.AddPanel(panels[0], self._settings)
            self._container.ShowPanel(panel)

    def on_close(self, evt):
        self._closing = True
        evt.Skip()

    def on_tree_selection(self, event):
        """Show panel that corresponds to selected tree item

        Used only when the hierarchical tree is shown.
        """
        # On Windows, closing the Dialog causes tree selection events to be
        # triggered. This is a workaround to ignore those events, which might
        # try to access dead objects.
        if self._closing:
            return
        instance_or_class = self._tree.GetItemData(event.GetItem())
        if isinstance(instance_or_class, wx.Panel):
            panel = instance_or_class
        else:
            # not an instance, assume it's a class
            panel = self._container.AddPanel(instance_or_class, self._settings)
            self._panels.append(panel)
            self._tree.SetItemData(event.GetItem(), panel)
        self._container.ShowPanel(panel)

    def _populate_tree(self, panels):
        """Recreate the hierarchical tree of preferences panels

        Used only when the hierarchical tree is shown.
        """
        self._tree.AddRoot("Root")
        for panel_class in panels:
            location = panel_class.location
            if not isinstance(location, tuple):
                # location should be a tuple, but it's easy to accidentally
                # make it not a tuple (eg: ("Plugins")). This fixes that.
                location = (location,)
            item = self._get_item(location)
            self._tree.SetItemData(item, panel_class)
        self._tree.ExpandAll()

    def _get_item(self, location):
        item = self._tree.GetRootItem()
        for text in location:
            item = self._get_child_item(item, _(text))
        return item

    def _get_child_item(self, parent, text):
        """Returns the tree item with the given text under the given parent

        This will create the item if it doesn't exist
        """
        if self._tree.ItemHasChildren(parent):
            item, cookie = self._tree.GetFirstChild(parent)
            while item:
                if self._tree.GetItemText(item).strip().lower() == text.strip().lower():
                    return item
                item, cookie = self._tree.GetNextChild(parent, cookie)
        # if we get here we didn't find the item
        item = self._tree.AppendItem(parent, text)
        return item

    def _get_children(self, parent):
        if self._tree.ItemHasChildren(parent):
            item, cookie = self._tree.GetFirstChild(parent)
            while item:
                yield item
                item, cookie = self._tree.GetNextChild(parent, cookie)


class PanelContainer(wx.Panel):
    """This contains a preference panel.

    This container has the ability to hold several panels,
    and to be able to switch between them. For some modes, however,
    the container will only hold a single panel.

    Each page has a title area, and an area for a preferences panel
    """
    def __init__(self, *args, **kwargs):
        super(PanelContainer, self).__init__(*args, **kwargs)

        self._current_panel = None
        self._settings = RideSettings()
        self.settings = self._settings['General']
        self.title = wx.StaticText(self, label="Your message here")
        self.panels_container = ScrolledPanel(self, wx.ID_ANY, style=wx.TAB_TRAVERSAL)
        self.panels_container.SetupScrolling()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.title, 0, wx.TOP | wx.LEFT | wx.EXPAND, 4)
        sizer.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 4)
        sizer.Add(self.panels_container, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.panels_container.SetSizer(wx.BoxSizer(wx.VERTICAL))

        font = self.title.GetFont()
        font.SetFaceName(self.settings[FONT_FACE])
        font.SetPointSize(self.settings[FONT_SIZE])
        font.MakeLarger()
        self.title.SetFont(font)
        self.title.SetForegroundColour(self.settings['foreground'])
        self.title.SetBackgroundColour(self.settings['background'])
        self.SetForegroundColour(self.settings['foreground'])
        self.SetBackgroundColour(self.settings['background'])

    def AddPanel(self, panel_class, settings):
        """Add a panel to the dialog"""
        panel = panel_class(parent=self.panels_container, settings=settings)
        self.panels_container.GetSizer().Add(panel, 1, wx.EXPAND)
        return panel

    def ShowPanel(self, panel):
        """Arrange for the given panel to be shown"""
        if self._current_panel is not None:
            self._current_panel.Hide()
        self._current_panel = panel
        panel.SetForegroundColour(self.settings['foreground'])  # Critical text all black on
        panel.SetBackgroundColour(self.settings['background'])  # Black background
        panel.Show()
        sizer = self.panels_container.GetSizer()
        item = sizer.GetItem(panel)
        title = getattr(panel, "title", panel.location[-1])
        self.SetTitle(title)
        font = self.title.GetFont()
        font.SetFaceName(self.settings[FONT_FACE])
        font.SetPointSize(self.settings[FONT_SIZE])
        self.SetFont(font)
        font.MakeLarger()
        self.title.SetFont(font)
        self.title.SetForegroundColour(self.settings['foreground'])
        self.title.SetBackgroundColour(self.settings['background'])
        if item is None:
            sizer.Add(panel, 1, wx.EXPAND)
        sizer.Layout()

    def SetTitle(self, title):
        """Set the title of the panel"""
        self.title.SetLabel(title)
