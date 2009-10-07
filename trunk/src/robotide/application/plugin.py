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


class Plugin(object):
    """Base class for all RIDE plugins"""

    def __init__(self, manager=None):
        """Initialize the plugin. It shouldn't create any interface
           elements. This should only initialize the data used
           by the plugin manager. Any interface elements that need
           to be created should be done in the activate() method
        """

        # This should only be set by the code that loads a plugin. If 
        # there is a problem loading the plugin this will be set to
        # the exception
        self.error = None
        
        # Defines the version of this plugin.
        self.version = "unknown"

        # Internal plugins are plugins that are part of the core
        # ride and can't be disabled by the user
        self.internal = False

        # The id uniquely identifies this plugin. For lack of a better
        # idea, perhaps java package naming convents should be used
        # (eg: com.orbitz.helloWorld)
        #
        # (do we really need a unique id, or can we just the name
        # of the file that implements the plugin?)
        self.id = None

        # This determines whether the plugin is active or not.
        # Only active plugins will be loaded into the GUI.
        self.active = False
        
        # A human-friendly name for the plugin. Mostly for displaying
        # in a GUI or web page.
        self.name = ""
        
        # A short description of the plugin
        self.description = self.__doc__

        # A URL to the plugin home page. The idea being, if this is
        # set, the plugin manager can display the link so the user
        # can get documentation, download new versions, etc.
        self.url = None

        # A handle to a plugin manager object to communicate with RIDE
        self.manager = manager

    def is_internal(self):
        """Return True if this plugin is marked as 'internal'"""
        # This method is primarily to support the plugin manager GUI
        # to prevent users from disabling important plugins. Is this
        # really necessary? Woe to the user that disables the plugin
        # manager GUI!
        if self.__dict__.has_key("internal"):
            return self.internal
        else:
            return False

    def activate(self):
        """Create the plugin window components or whatever else
           it needs to do to become active 
        """
        self.active = True

    def deactivate(self):
        """Undo whatever was done in the activate method"""
        self.active = False

    def config_panel(self, parent, id):
        """Returns a panel for configuring this plugin

           This can return None if there are no values to configure.
        """
        return None
