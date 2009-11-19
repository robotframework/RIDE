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

    def register_menu_entry(self, entry):
        # registering to action_registry needs to happen first
        self._action_registry.register(entry)
        self._menubar.register_menu_entry(entry)
        self._toolbar.register_toolbar_entry(entry)

    def register_menu_entries(self, entries):
        for entry in entries:
            self.register_menu_entry(entry)


def MenuEntries(data, component, container=None):
    menu = None
    entries = []
    for row in data.splitlines():
        row = row.strip()
        if not row:
            continue
        elif row.startswith('[') and row.endswith(']'):
            menu = row[1:-1].strip()
        else:
            entries.append(_create_entry(component, menu, container, row))
    return entries

def _create_entry(component, menu, container, row):
    if row.startswith('---'):
        return MenuSeparator(menu)
    tokens = [ t.strip() for t in row.split('|') ]
    tokens += [''] * (4-len(tokens))
    name, doc, shortcut, icon =  tokens
    if name.startswith('!'):
        name = name[1:]
        container = None
    action = getattr(component, 'On%s' % name.replace(' ', '').replace('&', ''))
    return MenuEntry(menu, name, action, container, shortcut, icon, doc)


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

    def register_menu_entry(self, entry):
        menu = self._find_menu(entry.menu_name)
        if not menu:
            menu = self._create_menu(entry.menu_name)
        menu.add_menu_item(entry)

    def _find_menu(self, name):
        registered = self._name_builder.get_registered_name(name)
        if not registered:
            return None
        for menu in self._menus:
            if menu.name == registered:
                return menu

    def remove_menu_entry(self, entry):
        menu = self._find_menu(entry.menu_name)
        menu.remove_menu_item(entry)


class Menu(object):

    def __init__(self, name, frame):
        self.name = name
        self._frame = frame
        self.wx_menu = wx.Menu()
        self._menu_items = {}
        self._name_builder = _NameBuilder()

    def add_menu_item(self, entry):
        if isinstance(entry, MenuSeparator):
            menu_item = SeparatorMenuItem(self._frame, self, entry)
        else:
            menu_item = self._get_or_insert_menu_item(entry)
        self._menu_items[menu_item.id] = menu_item
        menu_item.register(entry)

    def _get_or_insert_menu_item(self, entry):
        menu_item = self._get_menu_item(entry)
        if not menu_item:
            name_with_accerelator = self._get_name(entry, build_new=True)
            menu_item = MenuItem(self._frame, self, entry, name_with_accerelator)
        return menu_item

    def _get_name(self, entry, build_new):
        get_name = build_new and self._name_builder.get_name or \
                                 self._name_builder.get_registered_name
        if not entry.shortcut:
            return get_name(entry.name)
        return '%s\t%s' % (get_name(entry.name), entry.shortcut)

    def _get_menu_item(self, entry):
        for menu_item in self._menu_items.values():
            if menu_item.name == self._get_name(entry, build_new=False):
                return menu_item
        return None

    def remove(self, id):
        self.wx_menu.Remove(id)
        del(self._menu_items[id])


class _MenuItem(object):

    def __init__(self, frame, menu, name):
        self._frame = frame
        self._menu = menu
        self.name = name
        self.id = wx.NewId()
        self._bound = False
        self._entries = []
        self._wx_menu_item = None

    def register(self, entry):
        self._entries.append(entry)
        entry.register(self, id=self.id)

    def unregister(self, entry):
        self._entries.remove(entry)
        if not self._entries:
            self._menu.remove(entry.id)


class MenuItem(_MenuItem):

    def __init__(self, frame, menu, entry, name):
        _MenuItem.__init__(self, frame, menu, name)
        pos = entry._get_insertion_index(menu.wx_menu)
        self._wx_menu_item = menu.wx_menu.Insert(pos, self.id, name, entry.doc)
        self._frame.Bind(wx.EVT_MENU_OPEN, self.OnMenuOpen)

    def OnMenuOpen(self, event):
        self._wx_menu_item.Enable(self._is_enabled())
        event.Skip()

    def _is_enabled(self):
        for entry in self._entries:
            if entry.is_active():
                return True
        return False

    def register(self, entry):
        if entry.action_delegator and not self._bound:
            # This binds also the possible tool bar action for this entry
            self._frame.Bind(wx.EVT_MENU, entry.action_delegator, id=self.id)
            self._bound = True
        return _MenuItem.register(self, entry)


class SeparatorMenuItem(_MenuItem):

    def __init__(self, frame, menu, entry):
        _MenuItem.__init__(self, frame, menu, '---')
        pos = entry._get_insertion_index(self.wx_menu)
        self._wx_menu_item = self.wx_menu.InsertSeparator(pos)
        self._wx_menu_item.SetId(self.id)


class ToolBar(object):

    def __init__(self, frame):
        self._tb = wx.ToolBar(frame)
        self._tb.SetToolBitmapSize((16,16))
        self._frame = frame
        self._frame.SetToolBar(self._tb)
        self._tb.Realize()
        self._icons = []

    def register_toolbar_entry(self, entry):
        if entry.icon and entry.icon not in self._icons:
            entry.insert_to_toolbar(self._tb)
            self._icons.append(entry.icon)
            self._tb.Realize()


class _MenuEntry(object):
    _insertion_point = None

    def __init__(self):
        self.id = None
        self._registered_to = []
        self.action = None

    def set_menu_position(self, before=None, after=None):
        self._insertion_point = before or after
        self._insert_before = before is not None

    def _get_insertion_index(self, menu):
        if not self._insertion_point:
            return menu.GetMenuItemCount()
        item = menu.FindItemById(menu.FindItem(self._insertion_point))
        index = menu.GetMenuItems().index(item)
        if not self._insert_before:
            index += 1
        return index

    def register(self, registerer, **update_attrs):
        self._registered_to.append(registerer)
        for key, value in update_attrs:
            setattr(self, key, value)

    def unregister(self):
        for registerer in self._registered_to:
            registerer.unregister(self)


class MenuEntry(_MenuEntry):

    def __init__(self, menu_name, name, action=None, container=None,
                 shortcut=None, icon=None, doc=''):
        _MenuEntry.__init__(self)
        self.menu_name = menu_name
        self.shortcut = shortcut
        self.name = name
        self.doc = doc
        self.icon = self._get_icon(icon)
        self._container = container
        self.action = action

    def _get_icon(self, icon):
        if not icon:
            return None
        if isinstance(icon, basestring):
            return wx.ArtProvider.GetBitmap(getattr(wx, icon), wx.ART_TOOLBAR, (16, 16))
        return icon

    def insert_to_toolbar(self, toolbar):
        toolbar.AddLabelTool(self.id, self.name, self.icon,
                             shortHelp=self.name, longHelp=self.doc)

    def act(self, event):
        if self.is_active():
            self._action(event)

    def is_active(self):
        if self._is_always_inactive():
            return False
        if self._is_always_active():
            return True
        return self._container_is_active()

    def _is_always_inactive(self):
        return self.action is None

    def _is_always_active(self):
        return self._container is None

    def _container_is_active(self):
        if not self._container.IsShownOnScreen():
            return False
        widget = self._container.FindFocus()
        while widget:
            if widget == self._container.Parent:
                return True
            widget = widget.GetParent()
        return False


class MenuSeparator(_MenuEntry):

    def __init__(self, menu):
        _MenuEntry.__init__(self)
        self.menu_name = menu
        self.icon = None
        self.name = '---'


class ActionRegistry(object):

    def __init__(self):
        self._actions = {}

    def register(self, entry):
        if isinstance(entry, MenuSeparator):
            return
        key = self._get_key(entry)
        delegator = self._actions.setdefault(key, ActionDelegator())
        delegator.add(entry)
        entry.register(self, action_delegator=delegator)

    def unregister(self, entry):
        key = self._get_key(entry)
        self._actions[key].remove(entry)

    def _get_key(self, entry):
        return entry.shortcut or (entry.menu_name, entry.name)


class ActionDelegator(object):

    def __init__(self):
        self._actors = []

    def add(self, actor):
        self._actors.append(actor)

    def remove(self, actor):
        self._actors.remove(actor)

    def __call__(self, event):
        for actor in self._actors:
            actor.act(event)
