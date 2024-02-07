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
        """
        parent.SetBackgroundColour(Colour(200, 222, 40))
        parent.SetOwnBackgroundColour(Colour(200, 222, 40))
        parent.SetForegroundColour(Colour(7, 0, 70))
        parent.SetOwnForegroundColour(Colour(7, 0, 70))
        """
        for item in menu_items:
            if item.is_separator():
                self.AppendSeparator()
            else:
                self._add_item(item)
        parent.PopupMenu(self)
        self.Destroy()

    def _add_item(self, item):
        id_ = wx.NewIdRef()
        self.Append(id_, item.name)
        self.Bind(wx.EVT_MENU, item.callable, id=id_)


class PopupMenuItems(object):

    def __init__(self, parent=None, menu_names=None, menu_names_nt=None):
        self._items = []
        if menu_names is None:
            menu_names = []
        if not menu_names_nt:
            menu_names_nt = menu_names
        for item, item_nt in zip(menu_names, menu_names_nt):
            # print(f"DEBUG: PopupMenuItems value of item={item} item_nt={item_nt}")
            self.add_menu_item(PopupMenuItem(item, name_nt=item_nt, parent=parent))

    def __iter__(self):
        return iter(self._items)

    def add_menu_item(self, item):
        self._items.append(item)

    def add_separator(self):
        self.add_menu_item(PopupMenuItem('---'))


class PopupMenuItem(object):

    def __init__(self, name, name_nt=None, ccallable=None, parent=None):
        self.name = name
        nname = name_nt if name_nt else name
        # print(f"DEBUG: PopupMenuItem value of nname={nname}")
        self.callable = self._get_callable(nname, ccallable, parent)
        # print(f"DEBUG: PopupMenuItem value of name_nt={name_nt} callable={self.callable}")

    @staticmethod
    def _get_callable(name, ccallable, parent):
        from ..action.actioninfo import get_eventhandler_name_and_parsed_name
        if ccallable:
            return ccallable
        if name == '---':
            return None
        new_name = name.split('\t')[0].lower()
        handler_name, new_name = get_eventhandler_name_and_parsed_name(new_name)
        return getattr(parent, handler_name)

    def is_separator(self):
        return self.name == '---'
