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
        elements that need to be created should be done in the enable() method.
        """
        self.name = name or utils.name_from_class(self, drop='Plugin')
        self.doc = doc or inspect.getdoc(self) or ''
        self.metadata = metadata or {}
        self.initially_active = initially_active
        self.__app = application
        self.__frame = application.frame
        self.__settings = SETTINGS['Plugins'].add_section(self.name)
        self.__settings.set_defaults(default_settings)
        self._actions = []

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

    def enable(self):
        """This method is called when the plugin is enabled.

        Possible integration to UI should be done in this method.
        """
        pass

    def disable(self):
        """Undo whatever was done in the enable method."""
        pass

    def config_panel(self, parent):
        """Returns a panel for configuring this plugin

        The panel returned will be integrated in the Plugin Manager UI, and can
        be used e.g. to configure settings to be stored in the settings file.

        The default implementation returns None, meaning there are no values to
        configure.
        """
        return None

    def register_action(self, action_info):
        """Registers action to the UI.

        `action_info` is ActionInfo class containing needed attributes for
        creating menu and possible shortcut and/or icon to toolbar. See more
        from TODO."""
        action = self.__frame.actions.register_action(action_info)
        self._actions.append(action)

    def register_actions(self, action_infos):
        """Registers actions to the UI.

        `action_infos` is a list of ActionInfo items.
        """
        for action_info in action_infos:
            self.register_action(action_info)

    def unregister_actions(self):
        """Unregisters all actions added to the UI with register_action(s) methods."""
        for action in self._actions:
            action.unregister()
        self._actions = []

    def add_tab(self, tab, title, allow_closing=True):
        """Adds given `tab` with given `title` to the right side view.

        `tab` can be any wx container.

        Defining `allow_closing` to be False disallows closing the tab while
        the plugin is active.
        """
        self.notebook.add_tab(tab, title, allow_closing)

    def show_tab(self, tab):
        """Makes the `tab` visible.

        `tab` need to have been added previously with `add_tab`.
        """
        self.notebook.show_tab(tab)

    def delete_tab(self, tab):
        """Deletes `tab` added with `add_tab`."""
        self.notebook.delete_tab(tab)

    def tab_is_visible(self, tab):
        """Returns whether the `tab` added with add_tab is visible or not."""
        return self.notebook.tab_is_visible(tab)

    def new_suite_can_be_opened(self):
        """Checks is there modified files and asks user to decide what to do.

        In case there are modified files and user cancels, False is returned."""
        return self.__app.ok_to_open_new()

    def open_suite(self, path):
        """Opens test suite from the given `path`.

        If the parsing of the data source given with `path` fails, there will
        be no suite opened at all"""
        self.__frame.open_suite(path)

    def get_selected_datafile(self):
        """Returns the datafile which is currently selected in the tree.

        In case test case or keyword is selected, returns datafile containing
        selected item.
        """
        return self.tree.get_selected_datafile()

    def save_selected_datafile(self):
        """Saves the datafile which is currently selected in the tree.

        In case test case or keyword is selected, saves datafile containing
        selected item.
        """
        self.__frame.save(self.get_selected_datafile())

    def get_selected_item(self):
        """Returns the model item which is currently selected in the tree.

        Model item can be test suite, resource file, test case or user keyword.
        """
        return self.tree.get_selected_item()

    def subscribe(self, listener, *topics):
        """Subscribe to notifications for the given `topic(s)`.

        A topic is a dot-separated string (e.g.: 'ride.notebook.tabchange') or
        a reference to the corresponding message class (e.g.
        RideNotebookTabchange).

        The topic represents a hierarchy, and all publications at or below the
        given hierarchy will call the given `listener` (i.e.: subscribing to
        'Ride' or class RideMessage will cause the `listener` to be called for 'Ride',
        'Ride.anything' etc.)
        """
        for topic in topics:
            PUBLISHER.subscribe(listener, topic, key=self)

    def unsubscribe(self, listener, *topics):
        """Unsubscribes notifications from the given `topic(s)`.

        `topics` are same as those used in subscribe."""
        for topic in topics:
            PUBLISHER.unsubscribe(listener, topic, key=self)

    def unsubscribe_all(self):
        """Unsubscribes all the notifications from topics subscribed by this Plugin."""
        PUBLISHER.unsubscribe_all(key=self)

