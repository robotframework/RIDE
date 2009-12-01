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
import re

from shortcut import Shortcut


def ActionInfoCollection(data, eventhandler, container=None):
    menu = None
    actions = []
    for row in data.splitlines():
        row = row.strip()
        if not row:
            continue
        elif row.startswith('[') and row.endswith(']'):
            menu = row[1:-1].strip()
        else:
            actions.append(_create_action_info(eventhandler, menu, container, row))
    return actions


def _create_action_info(eventhandler, menu, container, row):
    if row.startswith('---'):
        return SeparatorInfo(menu)
    tokens = [ t.strip() for t in row.split('|') ]
    tokens += [''] * (4-len(tokens))
    name, doc, shortcut, icon =  tokens
    if name.startswith('!'):
        name = name[1:]
        container = None
    action = getattr(eventhandler, 'On%s' % name.replace(' ', '').replace('&', ''))
    return ActionInfo(menu, name, action, container, shortcut, icon, doc)


class MenuInfo(object):
    """Base class for `ActionInfo` and `SeparatorInfo`."""

    def __init__(self):
        self.insertion_point = _InsertionPoint()

    def is_separator(self):
        return False

    def set_menu_position(self, before=None, after=None):
        """Sets the position of this menu entry.

        :Parameters:
          before
            Place this menu entry before the specified entry.
          after
            Place this menu entry after the specified entry.

        Use either `before` or `after` and give the name without the possible
        shortcut.
        """
        self.insertion_point = _InsertionPoint(before, after)


class ActionInfo(MenuInfo):
    """Used to create menu entries, keyboard shortcuts and/or toolbar buttons."""

    def __init__(self, menu_name, name, action=None, container=None,
                 shortcut=None, icon=None, doc=''):
        """Initializes information needed to create actions in RIDE.

        :Parameters:
          menu_name
            The name of the menu where the new entry will be added.
          name
            The name of the new menu entry.
          action
            The callable which will be called when a user does any of the
            associated actions (selects menu entry, pushes toolbar button or 
            selects shortcut).
          container
            The wxPython element containing the UI components associated with 
            this ActionInfo's actions. When any of the actions is executed,
            container is used to check whether to call the `action` or not.
            `container` must be visible and it must have focus, otherwise the 
            `action` is not called. If `container` is None, `action` is 
            considered global and it is always called.
          shortcut
            The keyboard shortcut associated to the `action`.
          icon
            The icon added to the toolbar as a toolbar button. It can be either
            a 16x16 bitmap or a string presenting one of the icons provided by
            `wxPython's ArtProvider class`__ (e.g. 'ART_FILE_OPEN').

            __ http://www.wxpython.org/docs/api/wx.ArtProvider-class.html
          doc
            The documentation shown on the statusbar when selection is on
            the associated menu entry or toolbar button.
        """
        MenuInfo.__init__(self)
        self.menu_name = menu_name
        self.name = name
        self.action = action
        self.container = container
        self.shortcut = Shortcut(shortcut)
        self.icon = self._get_icon(icon)
        self.doc = doc

    def _get_icon(self, icon):
        if not icon:
            return None
        if isinstance(icon, basestring):
            # TODO: The icon should be created in the client code
            return wx.ArtProvider.GetBitmap(getattr(wx, icon), wx.ART_TOOLBAR, (16, 16))
        return icon


class SeparatorInfo(MenuInfo):
    """Used to create separators to menus."""

    def __init__(self, menu_name):
        """Initializes information needed to add separators to menus.
        
        :Parameters:
          menu_name
            The name of the menu where the separator will be added.
        """
        MenuInfo.__init__(self)
        self.menu_name = menu_name

    def is_separator(self):
        return True


class _InsertionPoint(object):
    _shortcut_remover = re.compile(' {2,}\([^()]+\)$')

    def __init__(self, before=None, after=None):
        self._item = before or after
        self._insert_before = before is not None

    def get_index(self, menu):
        if not self._item:
            return menu.GetMenuItemCount()
        index = self._find_position_in_menu(menu)
        if not index:
            return menu.GetMenuItemCount()
        if not self._insert_before:
            index += 1
        return index

    def _find_position_in_menu(self, menu):
        for index in range(0, menu.GetMenuItemCount()):
            item = menu.FindItemByPosition(index)
            if self._get_menu_item_name(item).lower() == self._item.lower():
                return index
        return None

    def _get_menu_item_name(self, item):
        return self._shortcut_remover.split(item.GetLabel())[0]
