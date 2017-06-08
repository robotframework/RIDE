#  Copyright 2008-2015 Nokia Solutions and Networks
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

import inspect
import sys
import traceback

from robotide.utils import unicode
from robotide import utils

from robotide.publish import messagetype
from robotide.publish import publisher


class RideMessage(object, metaclass=messagetype.messagetype):
    """Base class for all messages sent by RIDE.

    :CVariables:
      topic
        Topic of this message. If not overridden, value is got from the class
        name by lowercasing it, separating words with a dot and dropping possible
        ``Message`` from the end. For example classes ``MyExample`` and
        ``AnotherExampleMessage`` get titles ``my.example`` and
        ``another.example``, respectively.
      data
        Names of attributes this message provides. These must be given as
        keyword arguments to `__init__` when an instance is created.
    """

    topic = None  # DEBUG None
    data = []

    def __init__(self, **kwargs):
        """Initializes message based on given keyword arguments.

        Names of the given keyword arguments must match to names in `data`
        class attribute, otherwise the initialization fails.

        Must be called explicitly by subclass if overridden.
        """
        if sorted(kwargs.keys()) != sorted(self.data):
            raise TypeError('Argument mismatch, expected: %s' % self.data)
        self.__dict__.update(kwargs)

    def publish(self):
        """Publishes the message.

        All listeners that have subscribed to the topic of this message will be
        called with the this instance as an argument.

        Notifications are sent sequentially. Due to the limitations of current
        implementation, if any of the listeners raises an exception, subsequent
        listeners will not get the notification.
        """
        try:
            self._publish(self)
        except Exception as err:
            self._publish(RideLogException(
                message='Error in publishing message: ' + str(err),
                exception=err, level='ERROR'))

    def _publish(self, msg):
        publisher.PUBLISHER.publish(msg.topic, msg)
