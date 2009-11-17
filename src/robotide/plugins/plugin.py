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

from robotide.ui import MenuEntry
from robotide.context import SETTINGS
from robotide.publish import PUBLISHER
from robotide import utils


class Plugin(object):

    def __init__(self, application, name=None, doc=None, metadata=None,
                 default_settings=None, initially_active=False):
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
        self.__settings.set_defaults(default_settings)
        self.initially_active = initially_active
        self._menu_items = []

    def __getattr__(self, name):
        """Provides convenient attribute access to saved settings.
        
        I.e. when you have setting 'color', you can access it with self.color
        """
        if not '__settings' in name and self.__settings.has_setting(name):
            return self.__settings[name]
        raise AttributeError("No attribute or settings with name '%s' found"
                                 % (name))

    def save_setting(self, name, value, override=True):
        """Saves setting to ride settings under [Plugins] [[Plugin Name]] section """
        self.__settings.set(name, value, override=override)

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

    def register_menu_entry(self, entry):
        self._frame.actions.register_menu_entry(entry)

    def register_menu_entries(self, entries):
        self._frame.actions.register_menu_entries(entries)

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

    def subscribe(self, listener, *topics):
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
        for topic in topics:
            PUBLISHER.subscribe(listener, topic, key=self)

    def unsubscribe(self, listener, *topics):
        """Unsubscribe to notifications for the given topic."""
        for topic in topics:
            PUBLISHER.unsubscribe(listener, topic, key=self)

    def unsubscribe_all(self):
        PUBLISHER.unsubscribe_all(key=self)
