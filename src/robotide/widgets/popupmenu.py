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


class PopupCreator(object):

    def __init__(self):
        self._external_hooks = []

    def add_hook(self, hook):
        self._external_hooks.append(hook)

    def remove_hook(self, hook):
        self._external_hooks.remove(hook)

    def _get_all_actions(self, fixed_menu_items, data):
        menu_items = fixed_menu_items
        external_items = self._get_external_menu_items(data)
        if external_items:
            menu_items.add_separator()
            for item in external_items:
                menu_items.add_menu_item(item)
        return menu_items

    def _get_external_menu_items(self, data):
        menu_items = []
        for hook in self._external_hooks:
            menu_items.extend(hook(data))
        return menu_items

    def show(self, parent, fixed_menu_items, data):
        PopupMenu(parent, self._get_all_actions(fixed_menu_items, data))


class PopupMenu(wx.Menu):

    def __init__(self, parent, menu_items):
        wx.Menu.__init__(self)
        for item in menu_items:
            if item.is_separator():
                self.AppendSeparator()
            else:
                self._add_item(parent, item)
        parent.PopupMenu(self)
        self.Destroy()

    def _add_item(self, parent, item):
        id_ = wx.NewId()
        self.Append(id_, item.name)
        parent.Bind(wx.EVT_MENU, item.callable, id=id_)


class PopupMenuItems(object):

    def __init__(self, parent=None, menu_names=[]):
        self._items = []
        for item in menu_names:
            self.add_menu_item(PopupMenuItem(item, parent=parent))

    def __iter__(self):
        return iter(self._items)

    def add_menu_item(self, item):
        self._items.append(item)

    def add_separator(self):
        self.add_menu_item(PopupMenuItem('---'))


class PopupMenuItem(object):

    def __init__(self, name, callable=None, parent=None):
        self.name = name
        self.callable = self._get_callable(name, callable, parent)

    def _get_callable(self, name, callable, parent):
        if callable:
            return callable
        if name == '---':
            return None
        handler_name = ''.join(x for x in name.split('\t')[0].title() if not x.isspace())
        return getattr(parent, 'On'+handler_name)

    def is_separator(self):
        return self.name == '---'


