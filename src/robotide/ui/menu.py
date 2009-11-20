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


class ActionRegisterer(object):

    def __init__(self, menubar, toolbar):
        self._menubar  = menubar
        self._toolbar = toolbar
        self._action_registry = ActionRegistry()

    def register_action(self, action_info):
        action = Action(action_info)
        # registering order have to be 1.action_registry,  2.menubar, 3.toolbar
        self._action_registry.register(action)
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
            return SeparatorMenuItem(self._frame, self, action)
        return self._get_or_create_menu_item(action)

    def _get_or_create_menu_item(self, action):
        menu_item = self._get_menu_item(action)
        if not menu_item:
            name_with_accerelator = self._get_name(action, build_new=True)
            menu_item = MenuItem(self._frame, self, action, name_with_accerelator)
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
        return '%s\t%s' % (get_name(action.name), action.shortcut)

    def remove(self, id):
        self.wx_menu.Delete(id)
        del(self._menu_items[id])


class _MenuItem(object):

    def __init__(self, frame, menu, name):
        self._frame = frame
        self._menu = menu
        self.name = name
        self.id = wx.NewId()
        self._bound = False
        self._actions = []
        self._wx_menu_item = None

    def register(self, action):
        self._actions.append(action)
        action.register(self, id=self.id)

    def unregister(self, action):
        self._actions.remove(action)
        if not self._actions:
            self._menu.remove(action.id)

    def refresh_availability(self):
        self._wx_menu_item.Enable(self._is_enabled())

    def set_enabled(self):
        self._wx_menu_item.Enable(True)


class MenuItem(_MenuItem):

    def __init__(self, frame, menu, action, name):
        _MenuItem.__init__(self, frame, menu, name)
        pos = action._get_insertion_index(menu.wx_menu)
        self._wx_menu_item = menu.wx_menu.Insert(pos, self.id, name, action.doc)

    def _is_enabled(self):
        for action in self._actions:
            if action.is_active():
                return True
        return False

    def register(self, action):
        if action.has_action() and not self._bound:
            self._frame.Bind(wx.EVT_MENU, action.action_delegator, id=self.id)
            self._bound = True
        return _MenuItem.register(self, action)


class SeparatorMenuItem(_MenuItem):

    def __init__(self, frame, menu, action):
        _MenuItem.__init__(self, frame, menu, action.name)
        pos = action._get_insertion_index(menu.wx_menu)
        self._wx_menu_item = menu.wx_menu.InsertSeparator(pos)
        self._wx_menu_item.SetId(self.id)

    def _is_enabled(self):
        return False

class ToolBar(object):

    def __init__(self, frame):
        self._frame = frame
        self.wx_toolbar = wx.ToolBar(frame)
        self.wx_toolbar.SetToolBitmapSize((16,16))
        self._frame.SetToolBar(self.wx_toolbar)
        self.wx_toolbar.Realize()
        self._toolbar_buttons = []

    def register(self, action):
        if action.has_icon():
            toolbar_button = self._get_toolbar(action)
            if not toolbar_button:
                toolbar_button = ToolBarButton(self._frame, self, action)
                self._toolbar_buttons.append(toolbar_button)
            toolbar_button.register(action)

    def _get_toolbar(self, action):
        for toolbar_button in self._toolbar_buttons:
            if toolbar_button.icon == action.icon:
                return toolbar_button
        return None

    def remove(self, toolbar_button):
        self._toolbar_buttons.remove(toolbar_button)
        self.wx_toolbar.RemoveTool(toolbar_button.id)
        self.wx_toolbar.Realize()


class ToolBarButton(object):

    def __init__(self, frame, toolbar, action):
        self._toolbar = toolbar
        self.id = wx.NewId()
        self.icon = action.icon
        name = action.name.replace('&', '')
        toolbar.wx_toolbar.AddLabelTool(self.id, label=name, bitmap=action.icon, 
                                        shortHelp=name, longHelp=action.doc)
        self._action_delegator = ActionDelegator()
        frame.Bind(wx.EVT_MENU, self._action_delegator, id=self.id)

    def register(self, action):
        self._action_delegator.add(action)
        action.register(self)

    def unregister(self, action):
        if self._action_delegator.remove(action):
            self._toolbar.remove(self)


class _Registrable(object):

    def __init__(self, action_info):
        self.id = None
        self._registered_to = []
        self.action = None
        self.icon = None
        self.insertion_point = action_info.insertion_point

    def _get_insertion_index(self, menu):
        if not self.insertion_point:
            return menu.GetMenuItemCount()
        item = menu.FindItemById(menu.FindItem(self.insertion_point.item))
        index = menu.GetMenuItems().index(item)
        if not self.insertion_point.insert_before:
            index += 1
        return index

    def register(self, registerer, **update_attrs):
        self._registered_to.append(registerer)
        for key, value in update_attrs.items():
            setattr(self, key, value)

    def unregister(self):
        for registerer in self._registered_to:
            registerer.unregister(self)
        self._registered_to = []

    def has_action(self):
        return self.action is not None

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
        self.insertion_point = None

    def set_menu_position(self, before=None, after=None):
        self.insertion_point = InsertionPoint(before, after)


class InsertionPoint(object):

    def __init__(self, before=None, after=None):
        self.item = before or after
        self.insert_before = before is not None


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
        self.shortcut = self._get_shortcut(shortcut)
        self.icon = self._get_icon(icon)
        self.doc = doc

    def _get_shortcut(self, shortcut):
        if not shortcut:
            return None
        order = ['Shift', 'Ctrl', 'Alt']
        tokens = [ t.title() for t in shortcut.replace('+', '-').split('-') ]
        tokens.sort(key=lambda t: t in order and order.index(t) or 42)
        return '-'.join(tokens)

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


class ActionRegistry(object):

    def __init__(self):
        self._actions = {}

    def register(self, action):
        if action.has_action():
            key = self._get_key(action)
            delegator = self._actions.setdefault(key, ActionDelegator())
            delegator.add(action)
            action.register(self, action_delegator=delegator)

    def unregister(self, action):
        key = self._get_key(action)
        if self._actions[key].remove(action):
            del(self._actions[key])

    def _get_key(self, action):
        return action.shortcut or (action.menu_name, action.name)


class ActionDelegator(object):

    def __init__(self):
        self._actions = []

    def add(self, action):
        self._actions.append(action)

    def remove(self, action):
        """Removes action and returns True if delegator is empty."""
        self._actions.remove(action)
        return len(self._actions) == 0

    def __call__(self, event):
        for action in self._actions:
            action.act(event)
