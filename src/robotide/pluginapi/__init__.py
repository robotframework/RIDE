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

"""RIDE Plugin API

.. contents::
   :depth: 2
   :local:

Introduction
------------

RIDE can be extended with plugins written in Python starting with version 0.16.
The plugin API went through a major overhaul in the 0.20 release and this 
documentation describes how to write plugins against the new API. After the
changes in RIDE 0.20, the goal is to limit backwards incompatible changes to 
the minimum at least until the 1.0 release sometime in the spring 2010.

Finding plugins
---------------

Plugins are loaded automatically when RIDE starts up. RIDE will look in the
following directories for plugins:

- ``<RIDE_INSTALLATION_DIR>/site-plugins``
- ``<USER_DATA>/plugins``

Location of the ``<USER_DATA>`` directory will vary depending on your platform.
On Linux and OSX this will be ``~/.robotframework/ride`` while on Windows the 
location is ``%APPDATA%\\RobotFramework\\ride``.

Each Python file that is found in these directories is dynamically imported and
inspected. Every subclass of the `Plugin` class in these files will be
instantiated as a plugin. This has a few noteworthy consequences:

- Common utility code may be distributed as separate files, located in the
  plugin directories.
- All the top level code in the found Python files is executed as they are
  imported. Beware of the side effects.
- A Python file may contain more than one plugin.

Initialization
--------------

As stated earlier, every plugin *must* inherit from the `Plugin` base class.
This class is exposed directly from the `pluginapi` module, similarly as all 
other classes that plugins most often need, and can thus be imported like::

    from robotide.pluginapi import Plugin

When a plugin class is found, an instance of it will be created. Different
initialization options are explained in the documentation of the 
`Plugin.__init__` method. If creating an instance of a plugin class fails, an 
error message is shown to the user and the plugin is disabled.

Enabling and disabling
----------------------

Plugins can control are they enabled by default when they are loaded for the
first time. Afterwards users can enable and disable plugins from the plugin
manager, which is available from the menu through ``Tools > Manage Plugins``.
Plugins' enabled/disabled state is stored into RIDE's settings file and read
from there when plugins are loaded again later.

When the plugin is enabled, the `Plugin.enable` method is called. This is the 
point where the plugin is actually turned on and also the time when possible 
integration into RIDE UI should happen. The `Plugin.disable` method is called
when the plugin is disabled, and its purpose is to undo whatever was done in
the `Plugin.enable` method.

Creating menu entries and shortcuts
-----------------------------------

Plugins can create new entries to menus, buttons to the toolbar, and register
shortcuts using `ActionInfo` objects and the `Plugin.register_action` method. 
Registering actions is thoroughly documented in the `robotide.action` module.
Notice that all the relevant action classes are exposed also through the 
`pluginapi` module and plugins should import them like::

    from robotide.pluginapi import ActionInfo

Messaging
---------

RIDE has a messaging system that allows both sending messages when something
happens and subscribing to certain messages. Messages sent upon some
user action, like selecting an item in the tree or saving a file, are the
main communication mechanism from RIDE to plugins, but sometimes plugins may
also have a need to sent their own messages. Plugins can subscribe to messages
using the `Plugin.subscribe` method. The whole messaging system is documented
in the `robotide.publish` module, but plugins can import the relevant classes
through the `pluginapi` module like::

    from robotide.pluginapi import RideTreeSelection, RideSaved

Settings
--------

Plugin can store information persistently to RIDE's setting file. The initial
values can be given to the `Plugin.__init__` method and new values saved using
`Plugin.save_setting`. Saved settings can be accessed using direct attribute
access via `Plugin.__getattr__`.

Settings are stored into the setting file under ``[Plugins]`` section into
plugin specific subsections. Settings names starting with an underscore 
(currently only ``_enabled``) are reserved for RIDE's internal usage. The saved
settings may look something like this::

    [Plugins]
    [[Release Notes]]
    version_shown = 'trunk'
    _enabled = True
    [[Recent Files]]
    max_number_of_files = 4
    recent_files = []
    _enabled = False
"""

from ..action import action_info_collection, ActionInfo
from .plugin import Plugin
from .tree_aware_plugin_mixin import TreeAwarePluginMixin
