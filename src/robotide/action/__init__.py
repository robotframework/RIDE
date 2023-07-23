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

"""Module for handling UI actions.

.. contents::
   :depth: 2
   :local:

Introduction
------------

This module is used both by the core application and plugins to create and
register menu entries, toolbar buttons and keyboard shortcuts. All these are
created using the `ActionInfo` and `SeparatorInfo` classes.

Registering actions
-------------------

Actions are registered by creating an instance of the `ActionInfo` class with
the needed data. After configuring the instance it can be registered. The core
application handles registration itself, but plugins should always use the
`pluginapi.Plugin.register_action` method.

Menu separators
~~~~~~~~~~~~~~~

Menu separators are created using instances of the `SeparatorInfo` class. 
They must be registered using the same methods as the `ActionInfo` instances. 

Registering multiple actions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If there is a need to create a larger number of actions, it might be convenient
to use a simple DSL understood by the `ActionInfoCollection` factory method.
This factory creates a list containing `ActionInfo` and `SeparatorInfo` objects
which can be registered in a one go.

Handling actions
----------------

When any of the registered user actions is executed, RIDE decides which
registered event handlers should be called. It is possible to register a handler
globally or so that it is called only when the plugin is considered active
(i.e. it has focus).

The registering mechanism allows multiple handlers to be registered to the same
menu entry, toolbar button, or shortcut. It is thus possible that, for example,
one keyboard shortcut calls multiple handlers. 

It is also possible to enable/disable action's menu entry, toolbar button,
and shortcut by enabling/disabling those with `action.Action.enable` and 
`action.Action.disable` methods. Action is returned by 
`pluginapi.Plugin.register_action` method.
"""


from .action import action_factory
from .actioninfo import action_info_collection, SeparatorInfo, ActionInfo
