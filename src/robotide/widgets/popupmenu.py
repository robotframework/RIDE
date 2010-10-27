#  Copyright 2008-2010 Nokia Siemens Networks Oyj
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
        handler_name = name.replace(' ', '').split('\t')[0]  # split shortcut
        return getattr(parent, 'On'+handler_name)

    def is_separator(self):
        return self.name == '---'


