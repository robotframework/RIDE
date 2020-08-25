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

from pubsub import pub
from types import MethodType


class _Publisher(object):

    def __init__(self):
        self._publisher = pub.getDefaultPublisher()

    def publish(self, topic, data):
        self._publisher.sendMessage(topic, message=data)

    def subscribe(self, listener, topic):
        if not isinstance(topic, str):
            topic = topic.topic
        self._publisher.subscribe(listener, topic)

    def unsubscribe(self, listener, topic):
        self._publisher.unsubscribe(listener, topic)

    def unsubscribe_all(self, obj):
        def _listener_filter(listener):
            _callable = listener.getCallable()
            if isinstance(_callable, MethodType):
                if _callable.__self__ is obj:
                    return True
        self._publisher.unsubAll(listenerFilter=_listener_filter)


"""Global `Publisher` instance for subscribing to and unsubscribing from messages."""
PUBLISHER = _Publisher()
