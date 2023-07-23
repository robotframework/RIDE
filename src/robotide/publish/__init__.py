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

"""Message publishing and subscribing.

.. contents::
   :depth: 2
   :local:

Introduction
------------

RIDE uses messages for communication when something of interest happens, for
example a suite is loaded or item is selected in the tree. This module provides
means both for subscribing to listen to those messages and for sending them.
Messages are used for communication between the different components of the
core application, but their main usage is notifying plugins about various events.
Plugins can also send messages themselves, and also create custom messages, if
they have a need.

Subscribing
-----------

The core application uses the global `PUBLISHER` object (an instance of the
`Publisher` class) for subscribing to and unsubscribing from the messages.
Plugins should use the helper methods of the `Plugin` class instead of using
the `PUBLISHER` directly.

Message topics
~~~~~~~~~~~~~~

Regardless the method, subscribing to messages requires a message topic.
Topics can be specified using the actual message classes in
`robotide.publish.messages` module or with their dot separated topic strings.
It is, for example, equivalent to use the `RideTreeSelection` class and a
string ``ride.tree.selection``. Topic strings can normally, but not always, be
mapped directly to the class names.

The topic strings represents a hierarchy where the dots separate the hierarchy
levels. All messages with a topic at or below the given level will match the
subscribed topic. For example, subscribing to the ``ride.notebook`` topic means
that `RideNotebookTabChanged` or any other message with a topic starting with
``ride.notebook`` will match.

Listeners
~~~~~~~~~

Another thing needed when subscribing is a listener, which must be a callable
accepting one argument. When the corresponding message is published, the listener
will be called with an instance of the message class as an argument. That instance
contains the topic and possibly some additional information in its attributes.

The following example demonstrates how a plugin can subscribe to an event.
In this example the ``on_tree_selection`` method is the listener and the
``message`` it receives is an instance of the `RideTreeSelection` class.
::

    from robotide.pluginapi import Plugin, RideTreeSelection

    class MyFancyPlugin(Plugin):
       def activate(self):
           self.subscribe(self.on_tree_selection, RideTreeSelection)

       def on_tree_selection(self, message):
           print(message.topic, message.node)

Unsubscribing
~~~~~~~~~~~~~

Unsubscribing from a single message requires passing the same topic and listener
to the unsubscribe method that were used for subscribing. Additionally both
the `PUBLISHER` object and the `Plugin` class provide a method for unsubscribing
all listeners registered by someone.


Publishing messages
-------------------

Both the core application and plugins can publish messages using message
classes in the `publish.messages` module directly. Sending a message is as easy
as creating an instance of the class and calling its ``publish`` method. What
parameters are need when the instance is created depends on the message.

Custom messages
~~~~~~~~~~~~~~~

Most of the messages in the `publish.messages` module are to be sent only by
the core application. If plugins need their own messages, for example for
communication between different plugins, they can easily create custom messages
by extending the `RideMessage` base class::

    from robotide.pluginapi import Plugin, RideMessage

    class FancyImportantMessage(RideMessage):
        data = ['importance']

    class MyFancyPlugin(Plugin):
        def important_action(self):
            # some code ...
            MyImportantMessage(importance='HIGH').publish()

Plugins interested about this message can subscribe to it using either
the class ``FancyImportantMessage`` or its automatically generated title
``fancy.important``. Notice also that all the messages are exposed also through
the `robotide.pluginapi` module and plugins should import them there.
"""


import os

from .messages import *
from .publisher import PUBLISHER


def get_html_message(name):
    return open(os.path.join(
        os.path.dirname(__file__), 'htmlmessages', '{}.html'.format(name))).read()
