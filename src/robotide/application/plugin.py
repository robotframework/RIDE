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

from robotide.context import SETTINGS, PersistentAttributes
from robotide import utils


class Plugin(PersistentAttributes):

    def __init__(self, application, name=None, doc=None, metadata=None,
                 initially_active=False):
        """Initialize the plugin. 

        This shouldn't create any user interface elements, only initialize the
        data used by the plugin loader and manager UI. Any user interface 
        elements that need to be created should be done in the activate() method.
        """
        self._app = application
        self._frame = application.frame
        self.name = name or utils.name_from_class(self, drop='Plugin')
        PersistentAttributes.__init__(self, SETTINGS['Plugins'].add_section(self.name))
        self.doc = doc or inspect.getdoc(self) or ''
        self.metadata = metadata or {}
        self.initially_active = initially_active

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
