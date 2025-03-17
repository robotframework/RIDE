#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

from .. import utils
from ..action.actioninfo import ActionInfo
from ..publish import PUBLISHER


class Plugin(object):
    """Entry point to RIDE plugin API -- all plugins must extend this class.

    Plugins can use the helper methods implemented in this class to interact
    with the core application. The methods and their arguments are kept stable
    across the different RIDE releases to the extent that it is possible.

    If the provided methods are not enough, plugins can also interact with the
    core directly using properties `tree`, `menubar`, `toolbar`, `notebook` and
    `model`. Although these attributes themselves are stable, the functionality
    behind them may still change between releases. Users are thus recommended
    to propose new helper methods, preferably with patches, for often needed
    functionality that is only available through these properties.

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
    tree = property(lambda self: self.__frame.tree, doc='Provides access to the suite and resource tree')
    filemgr = property(lambda self: self.__frame.filemgr, doc='Provides access to the files and folders explorer')
    menubar = property(lambda self: self.__frame.GetMenuBar(), doc='Provides access to the application menubar')
    toolbar = property(lambda self: self.__frame.GetToolBar(), doc='Provides access to the application toolbar')
    notebook = property(lambda self: self.__frame.notebook, doc='Provides access to the tabbed notebook')
    model = property(lambda self: self.__app.model, doc='Provides access to the data model')
    frame = property(lambda self: self.__frame, doc='Reference to the RIDE main frame')
    datafile = property(lambda self: self.get_selected_datafile(), doc='Currently selected datafile')
    global_settings = property(lambda self: self.__app.settings, doc='Settings read from settings.cfg')

    def __init__(self, application, name=None, doc=None, metadata=None, default_settings=None, initially_enabled=True):
        """Initialize the plugin with the provided data.

        The provided information is mainly used by the plugin manager. Simple
        plugins are often fine with the defaults. If this method is overridden,
        the plugin must call it explicitly::

            from robotide.pluginapi import Plugin

            class MyCoolPluginExample(Plugin):
                \"\"\"This extra cool docstring is used as the plugin doc.\"\"\"
                def __init__(self, application):
                    Plugin.__init__(self, application, metadata={'version': '0.1'},
                                    default_settings={'color': 'red', 'x': 42})

        Plugins should not create any user interface elements at this point but
        wait until the `enable` method is called.

        :Parameters:
          application
            RIDE application reference.
          name
            Name of the plugin. If not specified, the name is got from the
            plugin class name-dropping possible ``Plugin`` from the end.
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
            time. Users can change the status later from the plugin manager.
        """
        self.name = name or utils.name_from_class(self, drop='Plugin')
        self.doc = self._get_doc(doc)
        self.metadata = metadata or {}
        self.initially_enabled = initially_enabled
        self._save_timer = None
        self.__app = application
        self.__frame = application.frame
        self.__namespace = application.namespace
        self.__settings = application.settings['Plugins'].add_section(self.name)
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
        if name in ('_Plugin__settings', '_parent'):
            return
        if '__settings' not in name and self.__settings.has_setting(name):
            return self.__settings[name]
        raise AttributeError("No attribute or settings with name '%s' found" % name)

    def save_setting(self, name, value, override=True, delay=0):
        """Saves the specified setting into the RIDE configuration file.

        ``override`` controls whether a possibly already existing value is
        overridden or not. Saved settings can be accessed using direct attribute
        access via `__getattr__`.
        ``delay`` is number defining how many seconds is waited before setting
        is saved. This can be used to prevent saving the value while user is
        typing it.
        """
        self.__settings.set(name, value, autosave=delay == 0, override=override)
        self._delay_saving(delay)

    def _delay_saving(self, delay):
        if not delay:
            return
        delay = delay * 1000
        if not self._save_timer:
            self._save_timer = wx.CallLater(delay, self._save_setting_after_delay)
        else:
            self._save_timer.Restart(delay)

    def _save_setting_after_delay(self):
        self.__settings.save()
        self._save_timer = None

    def enable(self):
        """This method is called by RIDE when the plugin is enabled.

        Possible integration to UI should be done in this method and removed
        when the `disable` method is called.
        """
        pass

    def disable(self):
        """Called by RIDE when the plugin is disabled.

        Undo whatever was done in the `enable` method.
        """
        pass

    def config_panel(self, parent):
        """Called by RIDE to get the plugin configuration panel.

        The panel returned will be integrated into the plugin manager UI, and
        can be used e.g. to display configurable settings.

        By default, there is no configuration panel.
        """
        _ = parent
        return None

    def register_action(self, action_info):
        """Registers a menu entry and optionally a shortcut and a toolbar icon.

        ``action_info`` is an instance of `ActionInfo` class containing needed
        information to create menu entry, keyboard shortcut and/or toolbar
        button for the action.

        All registered actions can be un-registered using the
        `unregister_actions` method.

        If register action is used in menu event handler, and it modifies the
        menu that triggered the event, it is safest to wrap register action
        call inside wx.CallAfter function.

        Returns created `Action` object.
        """
        action = self.__frame.actions.register_action(action_info)
        self.__actions.append(action)
        return action

    def register_shortcut(self, shortcut, callback):
        action_info = ActionInfo(None, None, action=callback, shortcut=shortcut)
        action = self.__frame.actions.register_shortcut(action_info)
        self.__actions.append(action)
        return action

    def register_actions(self, action_infos):
        """Registers multiple menu entries and shortcuts/icons.

        ``action_infos`` is a list of same `ActionInfo` objects that
        `register_action` method accepts.

        Returns list of created `Action` objects.
        """
        return [self.register_action(info) for info in action_infos]

    def register_search_action(self, description, handler, icon, default=False):
        self.__frame.toolbar.register_search_handler(description, handler, icon, default=default)

    def unregister_actions(self):
        """Unregisters all actions registered by this plugin."""
        for action in self.__actions:
            action.unregister()
        self.__actions = []

    def add_tab(self, tab, title, allow_closing=True):
        """Adds the ``tab`` with the ``title`` to the tabbed notebook and shows it.

        The ``tab`` can be any wxPython container. ``allow_closing`` defines
        can users close the tab while the plugin is enabled.
        """
        self.notebook.add_tab(tab, title, allow_closing)

    def show_tab(self, tab):
        """Makes the ``tab`` added using `add_tab` visible."""
        self.notebook.show_tab(tab)

    def delete_tab(self, tab):
        """Deletes the ``tab`` added using `add_tab`."""
        self.notebook.delete_tab(tab)

    def allow_tab_closing(self, tab):
        """Allows closing a tab that has been created using allow_closing=False."""
        self.notebook.allow_closing(tab)

    def disallow_tab_closing(self, tab):
        """Disallows closing a tab by user"""
        self.notebook.disallow_closing(tab)

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

    def get_selected_datafile(self):
        """Returns the data file that is currently selected in the tree.

        If a test case or a keyword is selected, the data file containing the
        selected item is returned.

        :rtype:
            `InitFile`, `TestCaseFile` or `ResourceFile`
        """
        if not self.tree:
            return
        return self.tree.get_selected_datafile()

    def save_selected_datafile(self):
        """Saves the data file that is currently selected in the tree.

        If a test case or a keyword is selected, the data file containing the
        selected item is saved.
        """
        self.__frame.save(self.tree.get_selected_datafile_controller())

    def is_unsaved_changes(self):
        """Returns True if there is any unsaved changes, otherwise False"""
        return self.__frame.has_unsaved_changes()

    def save_all_unsaved_changes(self):
        """Saves all the data files that are modified."""
        self.__frame.save_all()

    def get_selected_item(self):
        """Returns the item that is currently selected in the tree.

        The item can be a test suite, a resource file, a test case or a keyword.

        :rtype:
            `InitFile`, `TestCaseFile`, `ResourceFile`, `TestCase` or `UserKeyword`
        """
        if not self.tree:
            return
        if hasattr(self, 'model'):
            return self.tree.get_selected_item() or self.model
        else:
            return self.tree.get_selected_item()

    def content_assist_values(self, value=''):
        """Returns content assist values for currently selected item."""
        return self.__namespace.get_suggestions_for(self.get_selected_item(), value)

    def get_user_keyword(self, name):
        """Returns user keyword instance whose name is ``name`` or None."""
        keyword_info = self.__namespace.find_user_keyword(self.datafile, name)
        return keyword_info.item if keyword_info else None

    def select_user_keyword_node(self, uk):
        """Selects node containing the given ``uk`` in the tree."""
        if not self.tree:
            return
        self.tree.select_user_keyword_node(uk)

    def get_keyword(self, name):
        """Returns the keyword object with the given name or None"""
        return self.__namespace.find_keyword(self.datafile, name)

    def get_keyword_details(self, name):
        """Returns details (documentation, source) of keyword with name ``name``.

        Returns None if no matching keyword is found.
        """
        return self.__namespace.keyword_details(self.datafile, name)

    def is_user_keyword(self, name):
        """Returns whether ``name`` is a user keyword of current datafile.

        Checks both the datafile's own and imported user keywords for match.
        """
        return self.__namespace.is_user_keyword(self.datafile, name)

    def is_library_keyword(self, name):
        """Returns whether ``name`` is a keyword imported by current datafile."""
        return self.__namespace.is_library_keyword(self.datafile, name)

    def all_testcases(self):
        """Returns all test cases from all suites in one, unsorted list"""
        return self.model.all_testcases()

    def register_content_assist_hook(self, hook):
        """Allows plugin to insert values in content assist dialog.

        ``hook`` must be a callable, which should take two arguments and
        return a list of instances of `ItemInfo` class. When content
        assist is requested by user, ``hook`` will be called with the current
        dataitem and current value of cell as parameters.
        """
        self.__namespace.register_content_assist_hook(hook)

    def get_plugins(self):
        """Returns list containing plugin wrapper for every loaded plugin.

        Wrapper is an instance of `PluginConnector` if the plugin has loaded
        successfully, otherwise it's an instance of `BrokenPlugin`."""
        return self.__app.get_plugins()

    def publish(self, topic, data):
        """Publishes a message with given topic and client data.

        Purpose of this method is to support inter-plugin communication which
        is not possible to achieve using custom message classes.

        `data` will be passed as an argument to registered listener methods.
        """
        PUBLISHER.publish(topic, data)

    def subscribe(self, listener, *topics):
        """Start to listen to messages with the given ``topics``.

        See the documentation of the `robotide.publish` module for more
        information about subscribing to messages and the messaging system

        `unsubscribe` and `unsubscribe_all` can be used to stop listening to
        certain or all messages.
        """
        for topic in topics:
            PUBLISHER.subscribe(listener, topic)

    def unsubscribe(self, listener, *topics):
        """Stops listening to messages with the given ``topics``.

        ``listener`` and ``topics`` have the same meaning as in `subscribe`
        and a listener/topic combination is unsubscribed only when both of them
        match.
        """
        for topic in topics:
            PUBLISHER.unsubscribe(listener, topic)

    def unsubscribe_all(self):
        """Stops to listen to all messages this plugin has subscribed to."""
        PUBLISHER.unsubscribe_all(self)

    def register_editor(self, item_class, editor_class, activate=True):
        """Register ``editor_class`` as an editor class for model items of type ``item_class``

        If ``activate`` is True, the given editor is automatically activated
        using `set_active_editor`.
        """
        self.__app.register_editor(item_class, editor_class, activate)

    def unregister_editor(self, item_class, editor_class):
        """Unregisters ``editor_class`` as an editor class for model items of type ``item_class``"""
        self.__app.unregister_editor(item_class, editor_class)

    def set_active_editor(self, item_class, editor_class):
        """Activates the specified editor to be used with the specified model item.

        The editor must have been registered first by using `register_editor`.
        """
        self.__app.activate_editor(item_class, editor_class)

    def get_editors(self, item_class):
        """Return all registered editors for the given model item class.

        The last editor in the list is the currently active editor.
        """
        return self.__app.get_editors(item_class)

    def get_editor(self, item_class):
        """Return the current editor class for the given model item class"""
        return self.__app.get_editor(item_class)

    def highlight_cell(self, tcuk, obj=None, row=-1, column=-1):
        """Highlight a specific row/column of a test case or user keyword"""
        if not self.tree:
            return
        self.tree.select_node_by_data(tcuk)
        self.__app.editor.highlight_cell(obj, row, column)

    def highlight(self, data, text):
        """Highlight a specific text of a given data's editor"""
        if not self.tree:
            return
        self.tree.highlight(data, text)
