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
import os
import imp
from  wx.lib.pubsub import Publisher

from robotide.context import SETTINGS

from plugin import Plugin
from releasenotes import ReleaseNotesPlugin
from plugingui import PluginManagerPlugin
from recentfiles import RecentFilesPlugin 
from preview import PreviewPlugin
from keywordcolorizer import Colorizer


CORE_PLUGINS = [ReleaseNotesPlugin, PluginManagerPlugin, RecentFilesPlugin,
                PreviewPlugin, Colorizer]


class PluginLoader(object):
    """Defines a class for managing RIDE plugins"""

    def __init__(self, manager, dirs=None):
        user_plugin_directory = SETTINGS.get_path("plugins")
        self.plugins = {}
        self.manager = manager
        if dirs:
            self.plugindirs = dirs
        else:
            self.plugindirs = [
                user_plugin_directory,
                os.path.join(SETTINGS['install root'], "site-plugins")
                ]
        self.settings = SETTINGS.add_section("plugins")

    def load_plugins(self):
        """Finds and imports all plugins

           Right now this is rather simplistic. It looks for files named *.py
           in specific directories, tries to load the file, and then tries
           to run the function init_plugin() in the loaded module.

        """
        plugin_classes = list(self._find_plugins_from_dirs())
        plugin_instances = []
        for _class in CORE_PLUGINS + plugin_classes:
            try:
                plugin_instances.append(_class(self.manager))
            except Exception, e:
                raise
                # I should be logging this exception somewhere...where?
                id = str(_class)
                self._create_disabled_plugin(id, e)
        for plugin in plugin_instances:
            enabled = self._get_enabled_state(plugin)
            if enabled:
                plugin.activate()
            self.register_plugin(plugin)
        return self.plugins

    def _find_plugins_from_dirs(self):
        pluginclasses = []
        for dir in self.plugindirs:
            if not os.path.exists(dir):
                continue
            for filename in os.listdir(os.path.abspath(dir)):
                try:
                    module_name, extension = os.path.splitext(filename)
                    # for now, only import .py files. Later we can support
                    # loading other files (eg: directories, .zip files)
                    if extension == ".py":
                        file, pathname, description = imp.find_module(module_name, [dir])
                        try:
                            module = imp.load_module(module_name, file, pathname, description)
                            pluginclasses.extend(self._find_plugins(module))
                        finally:
                            if file:
                                file.close()
                except Exception, e:
                    self._create_disabled_plugin(os.path.join(dir, filename), e)
        return pluginclasses

    def register_plugin(self, plugin):
        """Register the plugin so we can find it by id"""
        self.plugins[plugin.id] = plugin

    def _create_disabled_plugin(self, id, error):
        """Create an instance of a plugin to represent a plugin that failed to load

        This is done so that the plugin can appear in the plugin manager GUI.
        """
        plugin = Plugin()
        plugin.id = plugin.name = id
        plugin.error = error
        self.register_plugin(plugin)

    def _find_plugins(self, module):
        """Find all classes in a module that inherit from Plugin"""
        for name in dir(module):
            _class = getattr(module, name)
            try:
                if _class != Plugin and issubclass(_class, Plugin):
                    yield _class
            except TypeError: 
                pass

    def _get_enabled_state(self, plugin):
        """Get enabled status of plugin from settings file"""
        try:
            if plugin.is_internal():
                enabled = True
            else:
                enabled = bool(self.settings[plugin.id])
        except Exception, e:
            # I should be logging this exception somewhere...where?
            enabled = False
        return enabled


class PluginManager(object):

    def __init__(self, app):
        self._app = app
        self._frame = app.frame
        self.settings = SETTINGS.add_section("plugins")

    def create_menu_item(self, menu_name, item_name, action, item_doc='',
                         index=0):
        """Create a menu item in an existing menu.

        `menu_name` is the name of the toplevel menu
        `item_name` is the visible name of the item
        `action` is a callable that is bound to the menu event
        `index` is the position of the item in the menu
        """
        # TODO: it would be better to be able to insert after a certain item
        # not by position. Also, should the args be wrapped in an object?
        menubar = self.get_menu_bar()
        menu = menubar.GetMenu(menubar.FindMenu(menu_name))
        id = wx.NewId()
        if index < 0:
            index = menu.GetMenuItemCount() + index + 1
        menu.Insert(index, id, item_name, item_doc)
        wx.EVT_MENU(self._frame, id, action)

    def get_menu_bar(self):
        """Returns the menu bar of the main RIDE window."""
        return self._frame.GetMenuBar()

    def get_tool_bar(self):
        """Returns the menu bar of the main RIDE window."""
        return self._frame.GetToolBar()

    def save_settings(self):
        """Saves the state of the plugins to the settings file"""
        for plugin in self._app.plugins.values():
            if not plugin.is_internal():
                self.settings[plugin.id] = plugin.active
        self.settings.save()

    def get_frame(self):
        return self._frame

    def get_notebook(self):
        return self._frame.notebook

    def get_model(self):
        return self._app.model

    def get_tree(self):
        return self._frame.tree

    def get_plugins(self):
        return self._app.plugins

    def show_page(self, page):
        self._frame.show_page(page)

    def new_suite_can_be_opened(self):
        return self._app.ok_to_open_new()

    def open_suite(self, path):
        self._frame.open_suite(path)

    def subscribe(self, listener, topic=''):
        """Subscribe to notifications for the given topic.

        A topic is a dot-separated string (eg: "core.open_suite") or
        a tuple ("core","open_suite") representing a hierarchy. All
        publications at or below the given hierarchy will call the
        given function (ie: subscribing to ("core") will cause the
        function to be called for ("core"), ("core","anything"), etc.

        This just wraps wxPython's built-in Publisher object, so that plugins
        need not be changed in case the underlying message passing mechanism
        is changed later.
        """
        Publisher().subscribe(listener,topic)

    def unsubscribe(self, listener, topics=None):
        """Unsubscribe to notifications for the given topic."""
        Publisher().unsubscribe(listener, topics)

    def publish(self, topic, data):
        """Publish a message to all subscribers"""
        Publisher().sendMessage(topic, data)
