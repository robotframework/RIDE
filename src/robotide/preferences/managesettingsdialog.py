#  Copyright 2020-     Robot Framework Foundation
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
from ..widgets import RIDEDialog, VirtualList, VerticalSizer, ImageList, ImageProvider, ButtonWithHandler
from ..widgets.list import ListModel

from ..context import SETTINGS_DIRECTORY


class SaveLoadSettings(RIDEDialog):

    def __init__(self, parent, section):
        self._section = section
        self._selection_listeners = []
        title = "Save or Load Settings"
        RIDEDialog.__init__(self, parent=parent, title=title, size=(650, 400))
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetSizer(VerticalSizer())
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        directory = wx.StaticText(self, label=f"Current directory: {SETTINGS_DIRECTORY}")
        """self.usage_list = VirtualList(self, self.usages.headers,
                                      self.usages)
        self.usage_list.SetBackgroundColour(Colour(self.color_secondary_background))
        self.usage_list.SetForegroundColour(Colour(self.color_secondary_foreground))
        self.usage_list.add_selection_listener(self._usage_selected)
        """
        self.Sizer.add_expanding(directory)

    def add_usage(self, usage):
        self.usages.add_usage(usage)

    def begin_searching(self):
        from ..ui.searchdots import DottedSearch
        self._dots = DottedSearch(self, self._update_searching)
        self._dots.start()

    def _update_searching(self, dots):
        self.SetTitle("'%s' - %d matches found - Searching%s" % (self._name, self.usages.total_usages, dots))
        self.usage_list.refresh()

    def end_searching(self):
        self._dots.stop()
        self.SetTitle("'%s' - %d matches" % (self._name, self.usages.total_usages))
        self.usage_list.refresh()

    def _usage_selected(self, idx):
        for listener in self._selection_listeners:
            listener(self.usages.usage(idx).item.parent, self._name)

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)
