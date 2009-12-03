#  Copyright 2008-2009 Nokia Siemens Networks Oyj
#  
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#  
#      http://www.apache.org:licenses/LICENSE-2.0
#  
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
UNDER CONSTRUCTION

== Messaging ==

A plugin may want to get notifications of different events. With messaging
mechanism a plugin may subscribe to any number of topics. RIDE creates and
sends messages with a topic whenever something of interest happens (e.g.
A suite is loaded, item is selected in the tree etc.)

=== Subscribing ===

A plugin subscribes to a topic by using method `subscribe`, defined in the
`Plugin` class. That method takes as a first argument a listener, a callable
object to be called when the subscribed message is sent, and as a second
argument it takes a list of topics. A topic is a reference to class that
inherits from `robotide.publish.RideMessage`. All messages created and sent by
RIDE inherit from this class.  For instance, to subscribe to tree selection
event, a plugin may do this:

{{{
# TODO: Fix import
from robotide import Plugin, RideTreeSelection

class MyFancyPlugin(Plugin):
   def activate(self):
       self.subscribe(self.OnTreeSelection, RideTreeSelection)

   def OnTreeSelection(self, message):
       print message.topic, message.node
}}}

Note that the class itself is used as a topic and that an instance of
that class is actually passed to the listener.

=== Unsubscribing ===

There are two methods for unsubsrcibing from an event. The individual `unsubscribe` has signature similar to `subsribe`. There is also a convenience method `unsubscribe_all`, which can be used for example in `disable` mehthod to unsubscribe from all topics.

=== Creating own messages ===

If a plugin wants to send messages of its own actions, the most convenient way is to create a subclass of `RideMessage`, and use its `publish` method, like this:

{{{
from robotide.plugin import Plugin, RideMessage

class FancyImportantMessage(RideMessage):
    data = ['importance']

class MyFancyPlugin(Plugin):
    def important_action(self):
         ...
         MyImportantMessage(importance='HIGH').publish()

}}}

Note that in the above example, a listener may subscribe to `FancyImportantMessage` with either of these (the first argument is the listener, whose name can obviously be freely chosen):
{{{
self.subscribe(self.OnFancy, 'fancy.important')
self.subscribe(self.OnFancy, FancyImportantMessage)
}}}
"""

from messages import *
from publisher import Publisher

PUBLISHER = Publisher()
