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

    def register_menu_entry(self, entry):
        self._menubar.register_menu_entry(entry)
        self._toolbar.register_toolbar_entry(entry)

    def register_menu_entries(self, entries):
        for entry in entries:
            self.register_menu_entry(entry)


def MenuEntries(data, component, container=None):
    menu = None
    for row in data.splitlines():
        if not row:
            menu = None
        elif menu:
            yield Entry(component, menu, container, row)
        else:
            menu = row

def Entry(component, menu, container, row):
    if is_separator(row):
        return MenuSeparator(menu)
    return create_entry(component, menu, container, row)

def is_separator(row):
    return row.startswith('---')

def create_entry(component, menu, container, row):
    tokens = [ t.strip() for t in row.split(',') ]
    tokens += [''] * (4-len(tokens))
    name, doc, shortcut, icon =  tokens
    if name.startswith('!'):
        name = name[1:]
        container = None
    action = getattr(component, 'On%s' % name.replace(' ', ''))
    return MenuEntry(menu, name, action, container, shortcut, icon, doc)


class MenuBar(object):

    def __init__(self, frame):
        self._mb = wx.MenuBar()
        self._frame = frame
        self._accelerators = []
        self._create_default_menus()
        self._frame.SetMenuBar(self._mb)

    def _create_default_menus(self):
        for name in ['File', 'Edit', 'Tools', 'Help']:
            self._mb.Append(wx.Menu(), self._get_name_with_accelerator(name))

    def _get_name_with_accelerator(self, name):
        name = name.replace('&', '')
        for pos, char in enumerate(name.upper()):
            if char not in self._accelerators:
                self._accelerators.append(char)
                return '%s&%s' % (name[:pos], name[pos:])
        return name 

    def register_menu_entry(self, entry):
        menu = self._get_or_create_menu(entry.menu_name)
        entry.insert_to_menu(menu, self._frame)

    def _get_or_create_menu(self, name):
        position = self._mb.FindMenu(name)
        if position == -1:
            self._mb.Insert(self._mb.FindMenu('Help'), wx.Menu(),
                            self._get_name_with_accelerator(name))
            position = self._mb.FindMenu(name)
        return self._mb.GetMenu(position)


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


class MenuEntry(object):

    def __init__(self, menu_name, name, action, container=None, shortcut=None,
                 icon=None, doc=''):
        self.id = wx.NewId()
        self.menu_name = menu_name
        self.name = shortcut and '%s\t%s' % (name, shortcut) or name
        self.doc = doc
        self.icon = self._get_icon(icon)
        self.action = self._get_action_for(shortcut, action, container)

    def _get_icon(self, icon):
        if not icon:
            return None
        if isinstance(icon, basestring):
            return wx.ArtProvider.GetBitmap(getattr(wx, icon), wx.ART_TOOLBAR, (16, 16))
        return icon

    def _get_action_for(self, shortcut, action, container):
        key = shortcut or (self.menu_name, self.name)
        action_delegator = ACTIONREGISTRY.register_action(key)
        action_delegator.add(action, container)
        return action_delegator

    def insert_to_menu(self, menu, frame):
        id = self._get_existing_id(menu)
        if id is None:
            menu.Append(self.id, self.name, self.doc)
            # This binds also the possible tool bar action for this entry
            frame.Bind(wx.EVT_MENU, self.action, id=self.id)
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


class MenuSeparator(object):

    def __init__(self, menu):
        self.menu_name = menu
        self.icon = None

    def insert_to_menu(self, menu, frame):
        menu.AppendSeparator()


class ActionRegistry(object):

    def __init__(self):
        self._actions = {}

    def register_action(self, key):
        return self._actions.setdefault(key, ActionDelegator())


ACTIONREGISTRY = ActionRegistry()


class ActionDelegator(object):

    def __init__(self):
        self._actors = []

    def add(self, action, container):
        self._actors.append(Actor(action, container))

    def __call__(self, event):
        for actor in self._actors:
            actor.act(event)
        event.Skip()


class Actor(object):

    def __init__(self, action, container):
        self._action = action
        self._container = container

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
