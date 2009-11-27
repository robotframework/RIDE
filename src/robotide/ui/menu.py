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
import re

import wx

import keymapping


class ActionRegisterer(object):

    def __init__(self, frame, menubar, toolbar):
        self._menubar  = menubar
        self._toolbar = toolbar
        self._shortcut_registry = ShortcutRegistry(frame)

    def register_action(self, action_info):
        action = Action(action_info)
        self._shortcut_registry.register(action)
        self._menubar.register(action)
        self._toolbar.register(action)
        return action

    def register_actions(self, actions):
        for action in actions:
            self.register_action(action)


def Actions(data, component, container=None):
    menu = None
    actions = []
    for row in data.splitlines():
        row = row.strip()
        if not row:
            continue
        elif row.startswith('[') and row.endswith(']'):
            menu = row[1:-1].strip()
        else:
            actions.append(_create_action_info(component, menu, container, row))
    return actions

def _create_action_info(component, menu, container, row):
    if row.startswith('---'):
        return SeparatorInfo(menu)
    tokens = [ t.strip() for t in row.split('|') ]
    tokens += [''] * (4-len(tokens))
    name, doc, shortcut, icon =  tokens
    if name.startswith('!'):
        name = name[1:]
        container = None
    action = getattr(component, 'On%s' % name.replace(' ', '').replace('&', ''))
    return ActionInfo(menu, name, action, container, shortcut, icon, doc)


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
        if char not in self._accelerators and char != ' ':
            self._accelerators.append(char)
            return True
        return False


class MenuBar(object):

    def __init__(self, frame):
        self._mb = wx.MenuBar()
        self._name_builder = _NameBuilder()
        self._frame = frame
        self._accelerators = []
        self._menus =[]
        self._create_default_menus()
        self._frame.SetMenuBar(self._mb)

    def _create_default_menus(self):
        for name in ['File', 'Edit', 'Tools', 'Help']:
            self._create_menu(name, before_help=False)

    def _create_menu(self, name, before_help=True):
        menu = Menu(self._name_builder.get_name(name), self._frame)
        self._insert_menu(menu, before_help)
        return menu

    def _insert_menu(self, menu, before_help):
        if before_help:
            index = self._mb.FindMenu('Help')
        else:
            index = self._mb.GetMenuCount()
        self._mb.Insert(index, menu.wx_menu, menu.name)
        self._menus.insert(index, menu)

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


class Menu(object):

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
        if isinstance(action, _MenuSeparator):
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
        if not action.shortcut:
            return get_name(action.name)
        return '%s   (%s)' % (get_name(action.name), action.shortcut)

    def _create_menu_item(self, action):
        name_with_accerelator = self._get_name(action, build_new=True)
        menu_item = MenuItem(self._frame, self, name_with_accerelator)
        pos = action.get_insertion_index(self.wx_menu)
        _wx_menu_item = self.wx_menu.Insert(pos, menu_item.id, 
                                            menu_item.name, action.doc)
        menu_item.set_wx_menu_item(_wx_menu_item)
        return menu_item

    def remove_menu_item(self, id):
        self.wx_menu.Delete(id)
        del(self._menu_items[id])


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
        self._wx_menu_item.SetId(self.id)

    def _is_enabled(self):
        return False

    def set_enabled(self):
        pass


class ToolBar(object):

    def __init__(self, frame):
        self._frame = frame
        self._wx_toolbar = wx.ToolBar(frame)
        self._wx_toolbar.SetToolBitmapSize((16,16))
        self._frame.SetToolBar(self._wx_toolbar)
        self._buttons = []

    def register(self, action):
        if action.has_icon():
            button = self._get_existing_button(action)
            if not button:
                button = self._create_button(action)
            button.register(action)

    def _get_existing_button(self, action):
        for button in self._buttons:
            if button.icon == action.icon:
                return button
        return None

    def _create_button(self, action):
        button = ToolBarButton(self._frame, self, action)
        name = action.name.replace('&', '')
        self._wx_toolbar.AddLabelTool(button.id, label=name, bitmap=action.icon,
                                      shortHelp=name, longHelp=action.doc)
        self._wx_toolbar.Realize()
        self._buttons.append(button)
        return button

    def remove_toolbar_button(self, button):
        self._buttons.remove(button)
        self._wx_toolbar.RemoveTool(button.id)
        self._wx_toolbar.Realize()


class ToolBarButton(object):

    def __init__(self, frame, toolbar, action):
        self._toolbar = toolbar
        self.icon = action.icon
        self._action_delegator = ActionDelegator(frame)
        self.id = self._action_delegator.id

    def register(self, action):
        self._action_delegator.add(action)
        action.register(self)

    def unregister(self, action):
        if self._action_delegator.remove(action):
            self._toolbar.remove_toolbar_button(self)


class _Registrable(object):

    def __init__(self, action_info):
        self._registered_to = []
        self.action = None
        self.shortcut = None
        self.icon = None
        self._insertion_point = action_info.insertion_point

    def get_insertion_index(self, menu):
        return self._insertion_point.get_index(menu)

    def register(self, registerer):
        self._registered_to.append(registerer)

    def unregister(self):
        for registerer in self._registered_to:
            registerer.unregister(self)
        self._registered_to = []

    def has_action(self):
        return self.action is not None

    def has_shortcut(self):
        return self.shortcut is not None

    def has_icon(self):
        return self.icon is not None


class _Action(_Registrable):

    def __init__(self, action_info):
        _Registrable.__init__(self, action_info)
        self.menu_name = action_info.menu_name
        self.name = action_info.name
        self.action = action_info.action
        self.container = action_info.container
        self.shortcut = action_info.shortcut
        self.icon = action_info.icon
        self.doc = action_info.doc

    def act(self, event):
        if self.is_active():
            self.action(event)

    def is_active(self):
        if self._is_always_inactive():
            return False
        if self._is_always_active():
            return True
        return self._container_is_active()

    def _is_always_inactive(self):
        return self.action is None

    def _is_always_active(self):
        return self.container is None

    def _container_is_active(self):
        if not self.container.IsShownOnScreen():
            return False
        widget = self.container.FindFocus()
        while widget:
            if widget == self.container.Parent:
                return True
            widget = widget.GetParent()
        return False


class _MenuSeparator(_Registrable):

    def __init__(self, action_info):
        _Registrable.__init__(self, action_info)
        self.menu_name = action_info.menu_name
        self.name = '---'


class _MenuInfo(object):

    def __init__(self):
        self.insertion_point = InsertionPoint()

    def set_menu_position(self, before=None, after=None):
        self.insertion_point = InsertionPoint(before, after)


class InsertionPoint(object):
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


def Action(action_info):
    if isinstance(action_info, SeparatorInfo):
        return _MenuSeparator(action_info)
    return _Action(action_info)


class ActionInfo(_MenuInfo):

    def __init__(self, menu_name, name, action=None, container=None,
                 shortcut=None, icon=None, doc=''):
        _MenuInfo.__init__(self)
        self.menu_name = menu_name
        self.name = name
        self.action = action
        self.container = container
        self.shortcut = keymapping.normalize_shortcut(shortcut)
        self.icon = self._get_icon(icon)
        self.doc = doc

    def _get_icon(self, icon):
        if not icon:
            return None
        if isinstance(icon, basestring):
            return wx.ArtProvider.GetBitmap(getattr(wx, icon), wx.ART_TOOLBAR, (16, 16))
        return icon


class SeparatorInfo(_MenuInfo):

    def __init__(self, menu_name):
        _MenuInfo.__init__(self)
        self.menu_name = menu_name


class ShortcutRegistry(object):

    def __init__(self, frame):
        self._frame = frame
        self._actions = {}

    def register(self, action):
        if action.has_shortcut() and action.has_action():
            delegator = self._actions.setdefault(action.shortcut,
                                                 ActionDelegator(self._frame))
            delegator.add(action)
            action.register(self)
            self._update_accerelator_table()

    def unregister(self, action):
        key = action.shortcut
        if self._actions[key].remove(action):
            del(self._actions[key])
        self._update_accerelator_table()

    def _update_accerelator_table(self):
        accerelators = []
        for shortcut, delegator in self._actions.items():
            if not isinstance(shortcut, basestring):
                continue
            flags, key_code = keymapping.parse_shortcut(shortcut)
            accerelators.append(wx.AcceleratorEntry(flags, key_code, delegator.id))
        self._frame.SetAcceleratorTable(wx.AcceleratorTable(accerelators))


class ActionDelegator(object):

    def __init__(self, frame):
        self._frame = frame
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
        event.Skip()
