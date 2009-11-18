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
        entry.register_to_action_registry(self._action_registry)
        self._menubar.register_menu_entry(entry)
        self._toolbar.register_toolbar_entry(entry)

    def register_menu_entries(self, entries):
        for entry in entries:
            self.register_menu_entry(entry)

    def unregister_menu_entry(self, entry):
        self._menubar.remove_menu_entry(entry)

    def unregister_menu_entries(self, entries):
        for entry in entries:
            self.unregister_menu_entry(entry)


def MenuEntries(data, component, container=None):
    menu = None
    entries = []
    for row in data.splitlines():
        if not row:
            menu = None
        elif menu:
            entries.append(_create_entry(component, menu, container, row))
        else:
            menu = row
    return entries

def _create_entry(component, menu, container, row):
    if row.startswith('---'):
        return MenuSeparator(menu)
    tokens = [ t.strip() for t in row.split(',') ]
    tokens += [''] * (4-len(tokens))
    name, doc, shortcut, icon =  tokens
    if name.startswith('!'):
        name = name[1:]
        container = None
    action = getattr(component, 'On%s' % name.replace(' ', ''))
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
        self._mb.Insert(index, menu._menu, menu.name)
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
        self._menu = wx.Menu()
        self._menu_item_entries = {}
        self._name_builder = _NameBuilder()

    def add_menu_item(self, entry):
        self._update_name(entry)
        entry.insert_to_menu(self._menu, self._frame)
        if not entry.id in self._menu_item_entries:
            self._menu_item_entries[entry.id] = []
        self._menu_item_entries[entry.id].append(entry)

    def _update_name(self, entry):
        # FIXME: This is a horrible hack. Menu entry shouldn't even have shortcut
        # included in its name at this point. Requires a bit more thinking...
        if entry.name == '---':
            return
        if '\t' in entry.name:
            name, shortcut = entry.name.split('\t')
            entry.name = '%s\t%s' % (self._name_builder.get_name(name), shortcut)
        else:
            entry.name = self._name_builder.get_name(entry.name)

    def remove_menu_item(self, entry):
        entries = self._menu_item_entries[entry.id]
        entries.remove(entry)
        if not entries:
            self._menu.Remove(entry.id)
            del(self._menu_item_entries[entry.id])


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

    def register_to_action_registry(self, registerer):
        pass


class MenuEntry(_MenuEntry):

    def __init__(self, menu_name, name, action=None, container=None,
                 shortcut=None, icon=None, doc=''):
        self.id = wx.NewId()
        self.menu_name = menu_name
        self.name = shortcut and '%s\t%s' % (name, shortcut) or name
        self.doc = doc
        self.shortcut = shortcut
        self.icon = self._get_icon(icon)
        self._container = container
        self._action = action
        self._registered_to = []

    def _get_icon(self, icon):
        if not icon:
            return None
        if isinstance(icon, basestring):
            return wx.ArtProvider.GetBitmap(getattr(wx, icon), wx.ART_TOOLBAR, (16, 16))
        return icon

    def insert_to_menu(self, menu, frame):
        id = self._get_existing_id(menu)
        if id is None:
            menu_item = menu.Insert(self._get_insertion_index(menu), self.id,
                               self.name, self.doc)
            if self._action:
                # This binds also the possible tool bar action for this entry
                frame.Bind(wx.EVT_MENU, self._action_delegator, id=self.id)
            else:
                menu_item.Enable(False)
        else:
            self.id = id

    def _get_existing_id(self, menu):
        id = menu.FindItem(self.name)
        if id != -1 and menu.FindItemById(id).GetItemLabel() == self.name:
            return id
        return None

    def insert_to_toolbar(self, toolbar):
        toolbar.AddLabelTool(self.id, self.name, self.icon,
                             shortHelp=self.name, longHelp=self.doc)

    def act(self, event):
        if self._should_act():
            self._action(event)

    def _should_act(self):
        if self._is_always_active():
            return True
        return self._container_is_active()

    def _is_always_active(self):
        return self._container is None

    def _container_is_active(self):
        if not self._container.IsShownOnScreen():
            return False
        widget = wx.GetActiveWindow()
        while widget:
            if widget == self._container.Parent:
                return True
            widget = widget.GetParent()
        return False

    def register_to_action_registry(self, registerer):
        if self._action:
            self._action_delegator = registerer.register(self)
            self._registered_to.append(registerer)


class MenuSeparator(_MenuEntry):

    def __init__(self, menu):
        self.id = wx.NewId()
        self.menu_name = menu
        self.icon = None
        self.name = '---'

    def insert_to_menu(self, menu, frame):
        menu_item = menu.InsertSeparator(self._get_insertion_index(menu))
        menu_item.SetId(self.id)


class ActionRegistry(object):

    def __init__(self):
        self._actions = {}

    def register(self, entry):
        key = entry.shortcut or (entry.menu_name, entry.name)
        delegator = self._actions.setdefault(key, ActionDelegator())
        delegator.add(entry)
        return delegator


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
        event.Skip()

