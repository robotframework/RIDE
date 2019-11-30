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

from robotide.ui.searchdots import DottedSearch

from robotide.widgets import (Dialog, VirtualList, VerticalSizer, ImageList,
                              ImageProvider, ButtonWithHandler)
import wx
from robotide.widgets.list import ListModel

class UsagesDialog(Dialog):

    def __init__(self, name, usages=None):
        self._name = name
        self._selection_listeners = []
        title = "'%s'" % (name)
        Dialog.__init__(self, title=title, size=(650, 400))
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetSizer(VerticalSizer())
        self._add_view_components()
        self.usages = usages or UsagesListModel([])
        self.usage_list = VirtualList(self, self.usages.headers,
                                      self.usages)
        self.usage_list.add_selection_listener(self._usage_selected)
        self.Sizer.add_expanding(self.usage_list)

    def add_usage(self, usage):
        self.usages.add_usage(usage)

    def begin_searching(self):
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

    def _add_view_components(self):
        pass


class UsagesDialogWithUserKwNavigation(UsagesDialog):

    def __init__(self, name, highlight, controller, usages=None):
        self.OnGotodefinition = lambda evt: highlight(controller, name)
        UsagesDialog.__init__(self, name, usages=usages)

    def _add_view_components(self):
        self.Sizer.Add(ButtonWithHandler(self, 'Go to definition'), 0, wx.ALL, 3)


def ResourceImportUsageDialog(name, highlight, controller):
    return UsagesDialogWithUserKwNavigation(name, highlight, controller, usages=ResourceImportListModel([]))


class _UsagesListModel(ListModel):

    def __init__(self, usages):
        self._usages = usages
        self._create_image_list()

    def _create_image_list(self):
        images = ImageList(16, 16)
        provider = ImageProvider()
        images.add(provider.TESTCASEIMG)
        images.add(provider.KEYWORDIMG)
        images.add(provider.DATAFILEIMG)
        images.add(provider.DATADIRIMG)
        self._images = images

    @property
    def images(self):
        return self._images

    def image(self, item):
        # TODO: better mechanism for item type recognition
        parent_type = self._usages[item].parent.__class__.__name__
        return {'TestCaseController': 0,
                'UserKeywordController': 1,
                'TestCaseFileController': 2,
                'ResourceFileController': 2,
                'TestDataDirectoryController': 3}.get(parent_type, -1)

    def add_usage(self, usage):
        self._usages.append(usage)

    def usage(self, idx):
        return self._usages[idx]

    @property
    def total_usages(self):
        return sum(u.count for u in self._usages)

    @property
    def count(self):
        return len(self._usages)


class UsagesListModel(_UsagesListModel):

    def __init__(self, usages):
        _UsagesListModel.__init__(self, usages)
        self.headers = ['Location', 'Usage', 'Source']

    def item_text(self, row, col):
        u = self.usage(row)
        return [u.location,  u.usage, u.source][col]


class ResourceImportListModel(_UsagesListModel):

    def __init__(self, usages):
        _UsagesListModel.__init__(self, usages)
        self.headers = ['Name', 'Location']
        self._cannot_rename_item_attr = wx.ListItemAttr()
        self._cannot_rename_item_attr.SetBackgroundColour(wx.Colour(255, 64, 64))

    def item_text(self, row, col):
        u = self.usage(row)
        return [u.name, u.location][col]

    def item_attributes(self, idx):
        if self._usages[idx].can_be_renamed:
            return None
        return self._cannot_rename_item_attr

    @property
    def total_usages(self):
        return len(self._usages)


class RecursiveResourceImportListModel(_UsagesListModel):

    def __init__(self, usages):
        _UsagesListModel.__init__(self, usages)
        self.headers = ['Imported name', 'Imported Location', 'Importing Name', 'Importing Location']

    def item_text(self, row, col):
        u = self.usage(row)
        return [u.res_name, u.res_src, u.name, u.location][col]
