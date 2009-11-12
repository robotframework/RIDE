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

from robot.utils import NormalizedDict


KEY_MAPPINGS = NormalizedDict({'DEL': wx.WXK_DELETE,
                'DELETE': wx.WXK_DELETE,
                'INS': wx.WXK_INSERT,
                'INSERT':  wx.WXK_INSERT,
                'ENTER': wx.WXK_RETURN, 
                'RETURN': wx.WXK_RETURN,
                'PGUP': wx.WXK_PAGEUP,
                'PGDN': wx.WXK_PAGEDOWN, 
                'SPACE': wx.WXK_SPACE})

#FIXME: Add also other needed key names
#LEFT     Left cursor arrow key
#RIGHT     Right cursor arrow key
#UP     Up cursor arrow key
#DOWN     Down cursor arrow key
#HOME     Home key
#END     End key
#SPACE     Space
#TAB     Tab key
#ESC or ESCAPE
#TODO: Should we add support for shortcut to be a tuple?

CTRL_KEY_MAPPINGS = {
                    'Ctrl': wx.ACCEL_CTRL,
                    'Shift': wx.ACCEL_SHIFT,
                    'Cmd': wx.ACCEL_CMD,
                    'Alt': wx.ACCEL_ALT}

def parse_shortcut(shortcut):
    keys = shortcut.split('-')
    if len(keys) == 1:
        flags = wx.ACCEL_NORMAL
    else:
        flags = sum(CTRL_KEY_MAPPINGS[key] for key in keys[:-1])
    return flags, _get_key(keys[-1])

def _get_key(key):
    if key in KEY_MAPPINGS:
        return KEY_MAPPINGS[key]
    elif len(key) == 1:
        return ord(key)
    raise AttributeError("Invalid key '%s'" % (key))


class KeyboardShortcutHandler(object):

    def __init__(self, frame, event_connector):
        self._frame = frame
        self._accerelator_tables = {}

    def add_keyboard_shortcut(self, shortcut, action, container=None):
        flags, key_code = parse_shortcut(shortcut)
        _id = wx.NewId()
        widget = container or self._frame
        widget.Bind(wx.EVT_MENU, action, id=_id)
        self._add_to_accerelator_table( widget, flags, key_code, _id)

    def _add_to_accerelator_table(self, widget, flags, key_code, _id):
        entry = wx.AcceleratorEntry(flags, key_code, _id)
        if not widget in self._accerelator_tables:
            self._accerelator_tables[widget] = []
        self._accerelator_tables[widget].append(entry)
        widget.SetAcceleratorTable(wx.AcceleratorTable(self._accerelator_tables[widget]))


class MenuBuilder(object):

    def __init__(self, frame, event_connector):
        self._frame = frame
        self._menu_items = []
        self._connector = event_connector


    def _get_menu(self, name):
        menubar = self._frame.GetMenuBar()
        menu_pos = menubar.FindMenu(name)
        if menu_pos == -1:
            #FIXME: Create non existing menu
            raise AttributeError('Menu "%s" cannot be found from the menubar' % (name))
        return menubar.GetMenu(menu_pos)

    def add_to_menu(self, menu, name, action, doc, shortcut, container):
        #TODO: Makes sure no dublicate menu items are created
        menu = self._get_menu(menu)
        id = wx.NewId()
        name = shortcut and '%s\t%s' % (name, shortcut) or name
        menu_item = menu.Append(id, name, doc)
        self._bind_handler(shortcut, action, container, id)
        self._menu_items.append((menu, menu_item, action, container))
        return id

    def _bind_handler(self, shortcut, handler, container, id):
        if shortcut:
            flags, key_code = parse_shortcut(shortcut)
            handler = self._connector.get_event_handler(flags, key_code,
                                                        handler, container)
        #FIXME: Incase of two bindings to same menu item, fire active one
        #TODO: Check can bind be used
        self._frame.Connect(id, -1, wx.wxEVT_COMMAND_MENU_SELECTED, handler)


class EventConnector(object):

    def __init__(self):
        self._event_delegators = {}

    #TODO: Change key to be a) flags/key_code tuple, menu item or toolbar item
    def get_event_handler(self, flags, key_code, callable, container):
        key = (flags, key_code)
        if not key in self._event_delegators:
            self._event_delegators[key] = EventDelegetor(key)
        self._event_delegators[key].add(callable, container)
        return self._event_delegators[key].handle


class EventDelegetor(object):
    
    def __init__(self, name):
        self.name = name
        self._callables = []

    def add(self, callable, container):
        self._callables.append((callable, container))

    def handle(self, event):
        for callable, container in self._callables:
            if self._active_container(container):
                callable(event)

    def _active_container(self, container):
        if container is None:
            return True
        widget = wx.GetActiveWindow()
        while widget:
            if widget == container:
                return True
            widget = widget.GetParent()
        return False

