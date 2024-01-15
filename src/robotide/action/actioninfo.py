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
import re

import wx

from ..widgets import ImageProvider
from .shortcut import Shortcut

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation


def action_info_collection(data, event_handler, data_nt=None, container=None):
    """Parses the ``data`` into a list of `ActionInfo` and `SeparatorInfo` objects.

    The data is parsed based on the simple DSL documented below.

    :Parameters:
      data
        The data to be parsed into `ActionInfo` and `SeparatorInfo` objects.
      event_handler
        The event handler that implements the actions. See `finding handlers`_
        for more information.
      data_nt
        Since RIDE 2.1, this is the original English menudata, or None which will be a copy of data
        This is due to the way menu is created for translations, which will not build the correct handler names.
      container
        the wxPython element containing the UI components associated with
        the `ActionInfo`.

    DSL syntax
    ----------
    ::

      [menu]
      name | documentation | shortcut | icon

    Fields
    ------

    menu
      The name of the menu under which the entries below it are inserted.
    name
      The name of the menu entry to be added. If name is ``---``, a
      `SeparatorInfo` object is created instead of an `ActionInfo` object.
      If name is post fixed with shortcuts between parenthesis and separated
      with ' or ', these shortcuts are parsed to machine local presentation
      and shown after the name. This can be used instead of shotrcut-element
      if you want to add shortcuts that you want to bind yourself and/or add
      several shortcuts.
    documentation
      Documentation for the action.
    shortcut
      Keyboard shortcut to invoke the action.
    icon
      Icon for the toolbar button.
    position
      Value for menu item ordering.

    See the `ActionInfo` attributes with same/similar names for more
    information about the fields and their possible values. Three
    last fields are optional.

    Finding handlers
    ----------------

    (Note: before v2.0.7)
    The given ``event_handler`` must have handler methods that map to the
    specified action names. The mapping is done by prefixing the name with
    ``On``, removing spaces, and capitalizing all words. For example ``Save``
    and ``My Action`` must have handler methods ``OnSave`` and ``OnMyAction``,
    respectively. If name has content between parenthesis at the end, this
    content is ignored when creating handler mapping.

    (Note: since v2.0.7)
    The given ``event_handler`` must have handler methods that map to the
    specified action names. The mapping is done by prefixing the name with
    ``on``, replacing spaces by ``_``, and lowercasing all words. For example ``Save``
    and ``My Action`` must have handler methods ``on_save`` and ``on_my_action``,
    respectively. If name has content between parenthesis at the end, this
    content is ignored when creating handler mapping.

    Specifying container
    --------------------

    By default, the given ``container`` is passed to the `ActionInfo.__init__`
    method directly. This can be altered by prefixing the ``name`` with an
    exclamation mark (e.g. ``!Save`` or ``!My Action``) to make that action
    global. With these actions the container given to the `ActionInfo.__init__`
    is always ``None``.

    Example
    -------
    ::

        [File]
        !&Open | Open file containing tests | Ctrl-O | ART_FILE_OPEN
        !Open &Resource | Open a resource file | Ctrl-R
        ---
        &Save | Save selected datafile | Ctrl-S | ART_FILE_SAVE

        [Tools]
        !Manage Plugins  | | | | POSITION-80

        [Content]
        Content Assist (Ctrl-Space or Ctrl-Alt-Space) | Has two shortcuts.
    """

    if not data_nt:
        data_nt = data
    menu = None
    actions = []
    for row, row_nt in zip(data.splitlines(), data_nt.splitlines()):
        row = row.strip()
        row_nt = row_nt.strip()
        # print(f"DEBUG: actioninfo.py action_info_collection in loop row={row}\noriginal={row_nt} ")
        if not row and not row_nt:
            continue
        elif row.startswith('[') and row.endswith(']'):
            menu = row[1:-1].strip()
            # print(f"DEBUG: actioninfo.py action_info_collection menu={menu}")
        else:
            actions.append(_create_action_info(event_handler, menu, container, row, row_nt))
    return actions


def _create_action_info(eventhandler, menu, container, row, row_nt):
    # print(f"DEBUG: actioninfo.py _create_action_info menu={menu} row={row} row_nt={row_nt}")
    t_menu = _(menu)
    # if t_menu.startswith('[') and t_menu.endswith(']'):
    #     t_menu = t_menu[1:-1].strip()
    t_row = _(row)  # .replace('&', ''))
    # print(f"DEBUG: actioninfo.py _create_action_info menu={t_menu} t_row={t_row} row_nt={row_nt}")
    if row_nt.startswith('---'):
        return SeparatorInfo(menu)
    tokens = [t.strip() for t in t_row.split('|')]
    tokens += [''] * (5-len(tokens))
    name, doc, shortcut, icon, position = tokens
    tokens_nt = [t.strip() for t in row_nt.split('|')]
    tokens_nt += [''] * (5-len(tokens_nt))
    name_nt, __, __, __, __ = tokens_nt
    if name_nt.startswith('!'):
        name = name[1:]
        name_nt = name_nt[1:]
        container = None
    eventhandler_name, name_nt = get_eventhandler_name_and_parsed_name(name_nt)
    action = getattr(eventhandler, eventhandler_name)
    # print(f"DEBUG: actioninfo.py _create_action_info menu={menu} eventhandler_name={eventhandler_name},"
    #       f" name_nt={name_nt}")
    return ActionInfo(menu, name, action, container, shortcut, icon, doc, position)


def get_eventhandler_name_and_parsed_name(name):
    eventhandler_name, name = _parse_shortcuts_from_name(name)
    # DEBUG: before v2.0.7 return 'On%s' % eventhandler_name.replace(' ', '').replace('&', ''), name
    return 'on_%s' % eventhandler_name.strip().replace(' ', '_').replace('&', '').lower(), name


def _parse_shortcuts_from_name(name):
    if '(' in name:
        eventhandler_name, shortcuts = name.split('(', 1)
        shortcuts = shortcuts.split(')')[0]
        elements = shortcuts.split(' or ')
        name = '%s (%s)' % (eventhandler_name, ' or '.join(Shortcut(e).printable for e in elements))
        return eventhandler_name, name
    return name, name


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

        Use either ``before`` or ``after`` and give the name without the
        possible shortcut.
        """
        self.insertion_point = _InsertionPoint(before, after)


class ActionInfo(MenuInfo):
    """Used to create menu entries, keyboard shortcuts and/or toolbar buttons."""

    def __init__(self, menu_name, name, action=None, container=None,
                 shortcut=None, icon=None, doc='', position=-1):
        """Initializes information needed to create actions...

        :Parameters:
          menu_name
            The name of the menu where the new entry will be added. The menu is
            created if it does not exist.
          name
            The name of the new menu entry. The name may contain an accelerator
            key prefixed by an ampersand like ``New &Action``. If an accelerator
            is not specified, or the one requested is already taken, the next
            free key is selected.
          action
            The callable which will be called when a user does any of the
            associated UI actions.
          container
            The wxPython element containing the UI components associated with
            the ``action``. When any of the registered UI actions is executed,
            the ``action`` is called only if the ``container`` or any of its
            child components has focus. It is possible to make the ``action``
            always active by using ``None`` as the ``container``.
          shortcut
            The keyboard shortcut associated to the ``action``. The ``shortcut``
            must be a string constructed from optional modifiers (``Ctrl, Shift,
            Alt``) and the actual shortcut key separating the parts with a hyphen.
            The shortcut key can be either a single character or any of the
            `wx keycodes`__ without the ``WXK_`` prefix. Examples: ``Ctrl-C``,
            ``Shift-Ctrl-6``, ``Alt-Left``, ``F6``.
          icon
            The icon added to the toolbar as a toolbar button. It can be either
            a 16x16 bitmap or a string presenting one of the icons provided by
            `wxPython's ArtProvider`__ like ``ART_FILE_OPEN``.
          doc
            The documentation shown on the statusbar when selection is on
            the associated menu entry or toolbar button.
          position
            The positional value of an item in the menu. Provided for ordering
            Tools menu. Defaults to -1.

        __ https://docs.wxwidgets.org/stable/wx_keycodes.html#keycodes
        __ https://www.wxpython.org/docs/api/wx.ArtProvider-class.html
        """
        MenuInfo.__init__(self)
        self.menu_name = menu_name
        self.name = name
        self.action = action
        self.container = container
        self.shortcut = Shortcut(shortcut)
        self._icon = None
        self._icon_source = icon
        self.doc = doc
        self._position = position

    @property
    def icon(self):
        if not self._icon:
            self._icon = self._get_icon()
        return self._icon

    def _get_icon(self):
        if not self._icon_source:
            return None
        if isinstance(self._icon_source, str):
            if self._icon_source.startswith("CUSTOM_"):
                return ImageProvider().get_image_by_name(self._icon_source[len("CUSTOM_"):])
            return wx.ArtProvider.GetBitmap(getattr(wx, self._icon_source),
                                            wx.ART_TOOLBAR, (16, 16))
        return self._icon_source

    @property
    def position(self):
        if isinstance(self._position, int):
            return self._position
        elif isinstance(self._position, str) and len(self._position) > 0:
            return int(self._position.split("POSITION-")[-1])
        return -1


class SeparatorInfo(MenuInfo):
    """Used to create separators to menus."""

    def __init__(self, menu_name):
        """Initializes information needed to add separators to menus.

        :Parameters:
          menu_name
            The name of the menu where the separator will be added. If menu does
            not exist, it is created automatically.
        """
        MenuInfo.__init__(self)
        self.menu_name = menu_name

    def is_separator(self):
        return True


class _InsertionPoint(object):
    _shortcut_remover = re.compile(r" {2,}\([^()]+\)$")

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
        if wx.VERSION < (4, 1, 0):
            return self._shortcut_remover.split(item.GetLabel())[0]
        return self._shortcut_remover.split(item.GetItemLabel())[0]
