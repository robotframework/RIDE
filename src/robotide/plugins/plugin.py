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
        self.name = name or utils.name_from_class(self, drop='Plugin')
        self.doc = doc or inspect.getdoc(self) or ''
        self.metadata = metadata or {}
        self.initially_active = initially_active
        self.__app = application
        self.__frame = application.frame
        self.__settings = SETTINGS['Plugins'].add_section(self.name)
        self.__settings.set_defaults(default_settings)
        self._menu_entries = []

    tree = property(lambda self: self.__frame.tree)
    menubar = property(lambda self: self.__frame.GetMenuBar())
    toolbar = property(lambda self: self.__frame.GetToolBar())
    notebook = property(lambda self: self.__frame.notebook)
    model = property(lambda self: self.__app.model)

    def __getattr__(self, name):
        """Provides convenient attribute access to saved settings.

        For example, setting 'color' can be accessed with self.color
        """
        if '__settings' not in name and self.__settings.has_setting(name):
            return self.__settings[name]
        raise AttributeError("No attribute or settings with name '%s' found"
                                 % (name))

    def save_setting(self, name, value, override=True):
        """Saves setting with `name` and `value` to settings file. 

        Setting is stored in section [Plugins] [[Plugin Name]].

        `override` controls whether possibly already existing value is 
        overridden or not. 
        """
        self.__settings.set(name, value, override=override)

    def activate(self):
        """This method is called when the plugin is activated.

        Possible integration to UI should be done in this method.
        """
        pass

    def deactivate(self):
        """Undo whatever was done in the activate method."""
        pass

    def config_panel(self, parent):
        """Returns a panel for configuring this plugin

        This can return None if there are no values to configure.
        """
        return None

    def register_menu_entry(self, entry):
        self._menu_entries.append(entry)
        self._frame.actions.register_menu_entry(entry)

    def register_menu_entries(self, entries):
        self._menu_entries.extend(entries)
        self._frame.actions.register_menu_entries(entries)

    def unergister_menu_entries(self):
        raise NotImplementedError()
        self._menu_entries = []

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
