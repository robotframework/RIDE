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

from wx import Colour
from ..widgets import RIDEDialog, VirtualList, VerticalSizer, ImageList, ImageProvider, ButtonWithHandler
from ..widgets.list import ListModel

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


class UsagesDialog(RIDEDialog):

    def __init__(self, name, usages=None, prefix=None):
        self._dots = None
        self._name = name
        self._selection_listeners = []
        title = "'%s'" % name
        RIDEDialog.__init__(self, title=title, size=(650, 400))
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        self.SetSizer(VerticalSizer())
        self.SetBackgroundColour(Colour(self.color_background))
        self.SetForegroundColour(Colour(self.color_foreground))
        self._add_view_components()
        self.usages = usages or UsagesListModel([])
        # print(f"DEBUG: usagesdialog.py UsagesDialog INIT: usages={self.usages} NAME={name} prefix={prefix}")
        self.usage_list = VirtualList(self, self.usages.headers, self.usages)
        self.usage_list.SetBackgroundColour(Colour(self.color_secondary_background))
        self.usage_list.SetForegroundColour(Colour(self.color_secondary_foreground))
        self.usage_list.add_selection_listener(self._usage_selected)
        self.Sizer.add_expanding(self.usage_list)

    def add_usage(self, usage):
        self.usages.add_usage(usage)

    def begin_searching(self):
        from ..ui.searchdots import DottedSearch
        self._dots = DottedSearch(self, self._update_searching)
        self._dots.start()

    def _update_searching(self, dots):
        self.SetTitle(_("'%s' - %d matches found - Searching%s") % (self._name, self.usages.total_usages, dots))
        self.usage_list.refresh_items()

    def end_searching(self):
        self._dots.stop()
        self.SetTitle(_("'%s' - %d matches") % (self._name, self.usages.total_usages))
        self.usage_list.refresh_items()

    def _usage_selected(self, idx):
        for listener in self._selection_listeners:
            listener(self.usages.usage(idx).item.parent, self._name)

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)

    def _add_view_components(self):
        """ Just ignore it """
        pass


class UsagesDialogWithUserKwNavigation(UsagesDialog):

    def __init__(self, name, highlight, controller, usages=None, prefix=None):
        """
        import os
        if not prefix:
            prefix = os.path.basename(controller.source).split('.')[0]
        """
        # print(f"DEBUG: usagesdialog.py UsagesDialogWithUserKwNavigation ENTER name={name},"
        #       f" controller_name={controller.name}  usages={usages}"
        #       f" source={controller.source} prefix={prefix}")
        self.on_go_to_definition = lambda evt: highlight(controller, name)
        UsagesDialog.__init__(self, name, usages=usages, prefix=prefix)

    def _add_view_components(self):
        button = ButtonWithHandler(self, _('Go to definition'), mk_handler='Go to definition',
                                   handler=self.on_go_to_definition)
        button.SetBackgroundColour(Colour(self.color_secondary_background))
        button.SetForegroundColour(Colour(self.color_secondary_foreground))
        self.Sizer.Add(button, 0, wx.ALL, 3)


def resource_import_usage_dialog(name, highlight, controller):
    return UsagesDialogWithUserKwNavigation(name, highlight, controller, usages=ResourceImportListModel([]))


class _UsagesListModel(ListModel):

    def __init__(self, usages):
        self._usages = usages
        self._create_image_list()

    def _create_image_list(self):
        images = ImageList(16, 16)
        provider = ImageProvider()
        images.add_image(provider.TESTCASEIMG)
        images.add_image(provider.KEYWORDIMG)
        images.add_image(provider.DATAFILEIMG)
        images.add_image(provider.DATADIRIMG)
        self._images = images

    @property
    def images(self):
        return self._images

    def image(self, item):
        # DEBUG: better mechanism for item type recognition
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
        self.headers = [_('Location'), _('Usage'), _('Source')]

    def item_text(self, row, col):
        u = self.usage(row)
        return [u.location,  u.usage, u.source][col]


class ResourceImportListModel(_UsagesListModel):

    def __init__(self, usages):
        _UsagesListModel.__init__(self, usages)
        self.headers = ['Name', 'Location']
        # wxPyDeprecationWarning: Using deprecated class. Use ItemAttr instead
        self._cannot_rename_item_attr = wx.ItemAttr()  # wx.ListItemAttr()
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
        self.headers = [_('Imported name'), _('Imported Location'), _('Importing Name'), _('Importing Location')]

    def item_text(self, row, col):
        u = self.usage(row)
        return [u.res_name, u.res_src, u.name, u.location][col]
