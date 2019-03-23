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
import wx.lib.agw.aui as aui

from robotide.context import IS_WINDOWS, IS_MAC

ID_CustomizeToolbar = wx.ID_HIGHEST + 1


class MenuBar(object):

    def __init__(self, frame):
        self._mb = wx.MenuBar()
        self._name_builder = _NameBuilder()
        self._frame = frame
        self._accelerators = []
        self._menus = []
        self._create_default_menus()

    def take_menu_bar_into_use(self):
        """This should be called after fully populating menus.
        Otherwise help menu will not be functional in osx."""
        self._frame.SetMenuBar(self._mb)

    def _create_default_menus(self):
        for name in ['File', 'Edit', 'Tools', 'Help']:
            self._create_menu(name, before_help=False)

    def _create_menu(self, name, before_help=True):
        menu = _Menu(self._name_builder.get_name(name), self._frame)
        self._insert_menu(menu, before_help)
        return menu

    def _insert_menu(self, menu, before_help):
        if before_help:
            index = [m.name for m in self._menus].index('&Help')
        else:
            index = len(self._menus)
        self._menus.insert(index, menu)
        self._mb.Insert(index, menu.wx_menu, menu.name)

    def register(self, action):
        menu = self._find_menu(action.menu_name)
        if not menu:
            menu = self._create_menu(action.menu_name)
        menu.add_menu_item(action)

    def _find_menu(self, name):
        registered = self._name_builder.get_registered_name(name)
        if not registered:
            return None
        for menu in self._menus:
            if menu.name == registered:
                return menu


class _Menu(object):

    def __init__(self, name, frame):
        self.name = name
        self._frame = frame
        self.wx_menu = wx.Menu()
        self._menu_items = {}
        self._name_builder = _NameBuilder()
        self._open = False
        self._frame.Bind(wx.EVT_MENU_OPEN, self.OnMenuOpen)
        self._frame.Bind(wx.EVT_MENU_CLOSE, self.OnMenuClose)

    def OnMenuOpen(self, event):
        if self.wx_menu == event.GetMenu() and not self._open:
            self._open = True
            for menu_item in self._menu_items.values():
                menu_item.refresh_availability()
        event.Skip()

    def OnMenuClose(self, event):
        if self._open:
            self._open = False
            for menu_item in self._menu_items.values():
                menu_item.set_enabled()
        event.Skip()

    def add_menu_item(self, action):
        menu_item = self._construct_menu_item(action)
        self._menu_items[menu_item.id] = menu_item
        menu_item.register(action)

    def _construct_menu_item(self, action):
        if action.is_separator():
            return self._create_separator(action)
        menu_item = self._get_menu_item(action)
        if not menu_item:
            menu_item = self._create_menu_item(action)
        return menu_item

    def _create_separator(self, action):
        menu_item = SeparatorMenuItem(self._frame, self, action)
        pos = action.get_insertion_index(self.wx_menu)
        menu_item.set_wx_menu_item(self.wx_menu.InsertSeparator(pos))
        return menu_item

    def _get_menu_item(self, action):
        for menu_item in self._menu_items.values():
            if self._names_equal(menu_item, action):
                return menu_item
        return None

    def _names_equal(self, menu_item, action):
        return menu_item.name == self._get_name(action, build_new=False)

    def _get_name(self, action, build_new):
        get_name = build_new and self._name_builder.get_name or \
                                 self._name_builder.get_registered_name
        if not action.shortcut:  # DEBUG not action.shortcut:
            return get_name(action.name)
        sht = action.get_shortcut()
        if sht:
            # print("DEBUG: actiontriggers name:%s shtcut:(%s)" % (get_name(action.name), action.get_shortcut()))
            return '%s    (%s)' % (get_name(action.name), sht)
        return '%s' % get_name(action.name)

    def _create_menu_item(self, action):
        name_with_accerelator = self._get_name(action, build_new=True)
        menu_item = MenuItem(self._frame, self, name_with_accerelator)
        pos = action.get_insertion_index(self.wx_menu)
        wx_menu_item = self.wx_menu.Insert(pos, menu_item.id,
                                           menu_item.name, action.doc)
        menu_item.set_wx_menu_item(wx_menu_item)
        return menu_item

    def remove_menu_item(self, id):
        self.wx_menu.Delete(id)
        del(self._menu_items[id])


class _NameBuilder(object):

    def __init__(self):
        self._names = {}
        self._accelerators = []

    def get_name(self, name):
        registered = self.get_registered_name(name)
        if registered:
            return registered
        try:
            name = self._use_given_accelerator(name)
        except ValueError:
            name = self._generate_accelerator(name)
            # print("DEBUG: actiontriggers get_name on ValueErr: %s" % name)
        self._register(name)
        return name

    def get_registered_name(self, name):
        try:
            return self._names[name.replace('&', '').upper()]
        except KeyError:
            return None

    def _register(self, name):
        self._names[name.replace('&', '').upper()] = name

    def _use_given_accelerator(self, name):
        index = name.find('&') + 1
        if 0 < index < len(name) and self._accelerator_is_free(name[index]):
            return name
        raise ValueError

    def _generate_accelerator(self, name):
        name = name.replace('&', '')
        for pos, char in enumerate(name):
            if self._accelerator_is_free(char):
                return '%s&%s' % (name[:pos], name[pos:])
        return name

    def _accelerator_is_free(self, char):
        char = char.upper()
        if char not in self._accelerators and char != u' ':
            self._accelerators.append(char)
            return True
        return False


class _MenuItem(object):

    def __init__(self, frame, menu, name):
        self._frame = frame
        self._menu = menu
        self.name = name
        self._action_delegator = ActionDelegator(self._frame)
        self.id = self._action_delegator.id

    def set_wx_menu_item(self, wx_menu_item):
        self._wx_menu_item = wx_menu_item

    def register(self, action):
        self._action_delegator.add(action)
        action.register(self)

    def unregister(self, action):
        if self._action_delegator.remove(action):
            self._menu.remove_menu_item(self.id)

    def refresh_availability(self):
        self._wx_menu_item.Enable(self._is_enabled())

    def set_enabled(self):
        self._wx_menu_item.Enable(True)


class MenuItem(_MenuItem):

    def _is_enabled(self):
        return self._action_delegator.is_active()


class SeparatorMenuItem(_MenuItem):

    def set_wx_menu_item(self, wx_menu_item):
        _MenuItem.set_wx_menu_item(self, wx_menu_item)
        # Should get  ITEM_SEPARATOR
        self.id = wx.ID_SEPARATOR
        # self._wx_menu_item.SetId(self.id)  # DEBUG Not in wxPhoenix

    def _is_enabled(self):
        return False

    def set_enabled(self):
        pass


class _RideSearchMenuItem(object):

    def __init__(self, handler, icon):
        self._handler = handler
        self.icon = icon

    def __call__(self, *args, **kwargs):
        self._handler(*args, **kwargs)


class ToolBarButton(object):

    def __init__(self, frame, toolbar, action):
        self._toolbar = toolbar
        self.icon = action.icon
        self._action_delegator = ActionDelegator(frame)
        self.id = self._action_delegator.id

    def register(self, action):
        self._action_delegator.add(action)
        action.register(self)
        action.inform_changes_in_enabled_status(self)

    def unregister(self, action):
        if self._action_delegator.remove(action):
            self._toolbar.remove_toolbar_button(self)

    def enabled_status_changed(self, action):
        self._toolbar.enabled_status_changed(self.id, action)


class ShortcutRegistry(object):

    def __init__(self, frame):
        self._frame = frame
        self._actions = {}

    def register(self, action):
        if action.has_shortcut() and action.has_action():
            delegator = self._actions.setdefault(action.get_shortcut(),
                                                 ActionDelegator(self._frame, action.shortcut))
            delegator.add(action)
            action.register(self)
            self._update_accerelator_table()

    def unregister(self, action):
        key = action.get_shortcut()
        if self._actions[key].remove(action):
            del(self._actions[key])
        self._update_accerelator_table()

    def _update_accerelator_table(self):
        accerelators = []
        for delegator in self._actions.values():
            # print("DEBUG: actiontrigger updateacelerators  delegator %s" % delegator)
            try:
                flags, key_code = delegator.shortcut.parse()
            except TypeError:
                continue
            accerelators.append(wx.AcceleratorEntry(flags, key_code, delegator.id))
        self._frame.SetAcceleratorTable(wx.AcceleratorTable(accerelators))


class ActionDelegator(object):

    def __init__(self, frame, shortcut=None):
        self._frame = frame
        self.shortcut = shortcut
        self.id = wx.NewId()
        self._actions = []

    def add(self, action):
        self._actions.append(action)
        if len(self._actions) == 1:
            self._frame.Bind(wx.EVT_MENU, self, id=self.id)

    def remove(self, action):
        """Removes action and returns True if delegator is empty."""
        self._actions.remove(action)
        if len(self._actions) == 0:
            self._frame.Unbind(wx.EVT_MENU, id=self.id)
            return True
        return False

    def is_active(self):
        for action in self._actions:
            if action.is_active():
                return True
        return False

    def __call__(self, event):
        for action in self._actions:
            action.act(event)
        if not (IS_WINDOWS or IS_MAC):
            event.Skip()
