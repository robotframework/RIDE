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

    """Entry point to RIDE plugin API - all plugins must extend this class.

    Plugins can use the helper methods implemented in this class to interact
    with the core application. The methods and their arguments are kept stable
    across the different RIDE releases to the extent that it is possible.

    If the provided methods are not enough, plugins can also interact with the 
    core directly using properties `tree`, `menubar`, `toolbar`, etc. Although
    these attributes themselves are stable, the functionality behind them may
    change radically between releases. Users are recommended to propose new 
    helper methods, preferably with patches, for often needed functionality 
    not yet available through them.

    :IVariables:
      name
        Plugin name. Set in `__init__` based on the given name or the class name.
      doc
        Plugin documentation. Set in `__init__` based on the given doc or
        the class docstring.
      metadata
        Plugin metadata. Set in `__init__` based on the given metadata.
      initially_enabled
        Specifies should the plugin be enabled when first loaded.
        Set in `__init__`.
    """

    tree = property(lambda self: self.__frame.tree, 
                    doc='Provides access to the suite and resource tree')
    menubar = property(lambda self: self.__frame.GetMenuBar(),
                       doc='Provides access to the application menubar')
    toolbar = property(lambda self: self.__frame.GetToolBar(),
                       doc='Provides access to the application toolbar')
    notebook = property(lambda self: self.__frame.notebook,
                       doc='Provides access to the tabbed notebook')
    model = property(lambda self: self.__app.model,
                       doc='Provides access to the data model')

    def __init__(self, application, name=None, doc=None, metadata=None,
                 default_settings=None, initially_enabled=True):
        """Initialize the plugin - must be called explicitly if overridden.

        Mainly used to initialize the data shown in the plugin manager. 
        Any user interface elements that need to be created should be done in
        the `enable` method.

        :Parameters:
          application
            RIDE application reference.
          name
            Name of the plugin. If not specified, the name is got from the
            plugin class name dropping possible 'Plugin' from the end.
          doc
            Plugin documentation. If not specified, the doc is got from the
            plugin class docstring.
          metadata
            A dictionary of free metadata shown on the plugin manager. Values
            containing URLs will be shown as links.
          default_settings
            A dictionary of settings and their default values. Settings are
            automatically stored onto RIDE configuration file, can be 
            accessed using direct attribute access via `__getattr__`, and new
            settings can be saved using `save_setting`.
          initially_enabled
            Specifies should the plugin be enabled when loaded for the first
            time. The status can be changed later from the plugin manager.
        """
        self.name = name or utils.name_from_class(self, drop='Plugin')
        self.doc = self._get_doc(doc)
        self.metadata = metadata or {} 
        self.initially_enabled = initially_enabled
        self.__app = application
        self.__frame = application.frame
        self.__settings = SETTINGS['Plugins'].add_section(self.name)
        self.__settings.set_defaults(default_settings)
        self.__actions = []

    def _get_doc(self, given_doc):
        if given_doc:
            return given_doc
        if self.__doc__ == Plugin.__doc__:
            return ''
        return inspect.getdoc(self) or ''

    def __getattr__(self, name):
        """Provides convenient attribute access to saved settings.

        For example, setting ``color`` can be accessed directly like
        ``self.color``.
        """
        if '__settings' not in name and self.__settings.has_setting(name):
            return self.__settings[name]
        raise AttributeError("No attribute or settings with name '%s' found" % name)

    def save_setting(self, name, value, override=True):
        """Saves the specified setting into the RIDE configuration file.

        Plugin settings are stored into ``[[Plugin Name]]`` subsection
        under ``[Plugins]`` section. They can be accessed using direct attribute
        access via `__getattr__`.

        ``override`` controls whether a possibly already existing value is
        overridden or not.
        """
        self.__settings.set(name, value, override=override)

    def enable(self):
        """This method is called by RIDE when the plugin is enabled.

        Possible integration to UI should be done in this method and removed
        when `disable` is called.
        """
        pass

    def disable(self):
        """Called by RIDE when the plugin is disabled.

        Undo whatever was done in the `enable` method.
        """
        pass

    # TODO: Should this be get_config_panel instead?
    def config_panel(self, parent):
        """Called by RIDE to get the plugin configuration panel.

        The panel returned will be integrated into the plugin manager UI, and
        can be used e.g. to display configurable settings.

        By default there is no configuration panel.
        """
        return None

    def register_action(self, action_info):
        """Registers a menu entry and optionally a shortcut and a toolbar icon.

        ``action_info`` is an instance of `ActionInfo` class containing needed
        information about the registered action.
        """
        action = self.__frame.actions.register_action(action_info)
        self.__actions.append(action)

    def register_actions(self, action_infos):
        """Registers multiple menu entries and shortcuts/icons.

        ``action_infos`` is a list of same `ActionInfo` objects that 
        `register_action` method accepts.
        """
        for action_info in action_infos:
            self.register_action(action_info)

    def unregister_actions(self):
        """Unregisters all actions registered by this plugin.

        Actions can be registered via `register_action` and `register_actions`
        methods.
        """
        for action in self.__actions:
            action.unregister()
        self.__actions = []

    def add_tab(self, tab, title, allow_closing=True):
        """Adds the ``tab`` with the ``title`` to the tabbed notebook and shows it.

        The ``tab`` can be any wxPython container. ``allow_closing`` defines
        can users close the tab while the plugin is enabled or not.
        """
        self.notebook.add_tab(tab, title, allow_closing)

    def show_tab(self, tab):
        """Makes the ``tab`` added using `add_tab` visible."""
        self.notebook.show_tab(tab)

    def delete_tab(self, tab):
        """Deletes the ``tab`` added using `add_tab`."""
        self.notebook.delete_tab(tab)

    def tab_is_visible(self, tab):
        """Returns is the ``tab`` added using `add_tab` visible or not."""
        return self.notebook.tab_is_visible(tab)

    def new_suite_can_be_opened(self):
        """Checks are there modified files and asks user what to do if there are.

        Returns False if there were modified files and user canceled the dialog,
        otherwise returns True.
        """
        return self.__app.ok_to_open_new()

    def open_suite(self, path):
        """Opens a test suite specified by the ``path``.

        No suite is opened if parsing the suite fails.
        """
        self.__frame.open_suite(path)

    # TODO: Should we somehow specify the API of the object returned by
    # this and subsequent methods?
    def get_selected_datafile(self):
        """Returns the data file that is currently selected in the tree.

        If a test case or a keyword is selected, the data file containing the
        selected item is returned.
        """
        return self.tree.get_selected_datafile()

    def save_selected_datafile(self):
        """Saves the data file that is currently selected in the tree.

        If a test case or a keyword is selected, the data file containing the
        selected item is saved.
        """
        self.__frame.save(self.get_selected_datafile())

    def get_selected_item(self):
        """Returns the item that is currently selected in the tree.

        The item can be a test suite, a resource file, a test case or a keyword.
        """
        return self.tree.get_selected_item()

    def subscribe(self, listener, *topics):
        """Start to listen to messages with the given ``topics``.

        Topics can be specified using message classes in `robotide.publish.messages` 
        module or with dot separated topic strings. For example these two are
        equivelant::

          self.subscribe('ride.tree.selection')
          self.subscribe(RideTreeSelection)

        Topic strings represents a hierarchy, and all publications at or below
        the given hierarchy level will match the topic. For example, subscribing
        to ``ride.notebook`` topic means that `RideNotebookTabChanged` or any
        other message with a topic starting with ``ride.notebook`` will match.
        
        ``listener`` needs to be a callable that accepts one argument. When the
        corresponding message is published, the ``listener`` will be called
        with an instance of the message class as an argument. That instance
        contains topic and possibly some additional information in its attributes.
        
        `unsubscribe` and `unsubscribe_all` can be used to stop listening to
        certain or all messages.
        """
        for topic in topics:
            PUBLISHER.subscribe(listener, topic, key=self)

    def unsubscribe(self, listener, *topics):
        """Stops listening to messages with the given ``topics``.

        ``listener`` and ``topics`` have the same meaning as in `subscribe`
        and a listener/topic combination is unsubscribed only when both of them
        match. 
        """
        for topic in topics:
            PUBLISHER.unsubscribe(listener, topic, key=self)

    def unsubscribe_all(self):
        """Stops to listen to all messages"""
        PUBLISHER.unsubscribe_all(key=self)

