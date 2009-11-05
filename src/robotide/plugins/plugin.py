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

import inspect
import wx
from  wx.lib.pubsub import Publisher

from robotide import utils
from robotide.context import SETTINGS, PUBLISHER


class Plugin(object):

    def __init__(self, application, name=None, doc=None, metadata=None,
                 settings=None, initially_active=False):
        """Initialize the plugin. 

        This shouldn't create any user interface elements, only initialize the
        data used by the plugin loader and manager UI. Any user interface 
        elements that need to be created should be done in the activate() method.
        """
        self._app = application
        self._frame = application.frame
        self.name = name or utils.name_from_class(self, drop='Plugin')
        self.doc = doc or inspect.getdoc(self) or ''
        self.metadata = metadata or {}
        self.__settings = SETTINGS['Plugins'].add_section(self.name)
        self.__settings.set_defaults(settings)
        self.initially_active = initially_active
        self._menu_items = []
        # TODO: _listeners is needed to keep references to wrapped listeners in
        # subscribe(), because Publisher only keeps weak references of listeners
        # and without appending them to this list, they are garbage collected
        # immediately. Is there a better way to keep the references?
        #self._listeners = []

    def activate(self):
        """Create necessary user interface components."""
        pass

    def deactivate(self):
        """Undo whatever was done in the activate method."""
        pass

    def config_panel(self, parent):
        """Returns a panel for configuring this plugin

           This can return None if there are no values to configure.
        """
        return None

    def get_menu_bar(self):
        return self._frame.GetMenuBar()

    def get_menu(self, name):
        menubar = self.get_menu_bar()
        menu_pos = menubar.FindMenu(name)
        if menu_pos == -1:
            raise AttributeError('Menu "%s" cannot be found from the menubar' % (name))
        return menubar.GetMenu(menu_pos)

    def add_to_menu(self, menu_name, item_name, index=-1, 
                    action=None, item_doc='', enabled=True):
        """Create a menu item into an existing menu.

        `menu_name` is the name of the toplevel menu
        `item_name` is the visible name of the item
        `index` is the position of the item in the menu, negative index is 
        counted from the end
        `action` is a callable that is bound to the menu event
        `item_doc` is the documentation visible in status bar
        `enabled` specifies whether the item is enabled, defaults to True
        """
        menu = self.get_menu(menu_name)
        pos = self._resolve_position_from_index(menu, index)
        id = wx.NewId()
        menu_item = menu.Insert(pos, id, item_name, item_doc)
        menu_item.Enable(enabled)
        wx.EVT_MENU(self.get_frame(), id, action)
        self._menu_items.append((menu_name, menu_item))
        return id

    def _resolve_position_from_index(self, menu, index):
        if index > 0:
            return index
        pos = menu.GetMenuItemCount() + index
        if pos < 0:
            return 0
        return pos

    def add_separator_to_menu(self, menu_name, index):
        menu = self.get_menu(menu_name)
        pos = self._resolve_position_from_index(menu, index)
        menu_item = menu.InsertSeparator(pos)
        self._menu_items.append((menu_name, menu_item))

    def remove_added_menu_items(self):
        for menu_name, menu_item in self._menu_items:
            self.get_menu(menu_name).RemoveItem(menu_item)
        self._menu_items = []

    def remove_from_menu(self, menu_name, id):
        menubar = self.get_menu_bar()
        pos = menubar.FindMenu(menu_name)
        menu = menubar.GetMenu(pos)
        menu.Remove(id)

    def get_tool_bar(self):
        return self._frame.GetToolBar()

    def get_frame(self):
        return self._frame

    def get_notebook(self):
        return self._frame.notebook

    def get_model(self):
        return self._app.model

    def get_tree(self):
        return self._frame.tree

    def show_page(self, page):
        self._frame.show_page(page)

    def delete_page(self, page):
        if page:
            self._frame.delete_page(page)

    def new_suite_can_be_opened(self):
        return self._app.ok_to_open_new()

    def open_suite(self, path):
        self._frame.open_suite(path)

    def subscribe(self, listener, event):
        # FIXME: rewrite documentation to include event objects
        """Subscribe to notifications for the given event.

        A event is a dot-separated string (eg: "core.open_suite") or
        a tuple ("core","open_suite") representing a hierarchy. All
        publications at or below the given hierarchy will call the
        given function (ie: subscribing to ("core") will cause the
        function to be called for ("core"), ("core","anything"), etc.

        This just wraps wxPython's built-in Publisher object, so that plugins
        need not be changed in case the underlying message passing mechanism
        is changed later.
        """
        PUBLISHER.subscribe(listener, event)

    def unsubscribe(self, listener, event):
        """Unsubscribe to notifications for the given topic."""
        PUBLISHER.unsubscribe(listener, event)

    def publish(self, topic, data):
        """Publish a message to all subscribers"""
        Publisher().sendMessage(topic, data)

