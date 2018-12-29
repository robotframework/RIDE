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

from robotide.utils import PY3
if PY3:
    from robotide.utils import basestring, unicode

try:
    from pubsub import Publisher
    WxPublisher = Publisher()
except ImportError:
    from pubsub import pub
    WxPublisher = pub.getDefaultPublisher()


class Publisher(object):

    def __init__(self):
        self._listeners = {}

    def publish(self, topic, data):
        self._sendMessage(topic, data)

    def subscribe(self, listener, topic, key=None):
        """Start to listen to messages with the specified ``topic``.

        The ``topic`` can be either a message class or a dot separated topic
        string, and the ``listener`` must be a callable accepting a message
        instance. See the generic documentation of the `robotide.publish`
        module for more details.

        The ``key`` is used for keeping a reference of the listener so that
        all listeners with the same key can be unsubscribed at once using
        ``unsubscribe_all``.
        """
        wrapper = _ListenerWrapper(listener, topic)
        self._listeners.setdefault(key, []).append(wrapper)

    def _sendMessage(self, topic, data):
        current_wrappers = self._listeners.values()
        for wrappers in list(current_wrappers):  # DEBUG
            for wrapper in wrappers:
                if wrapper.listens(topic):
                    wrapper(data)

    def unsubscribe(self, listener, topic, key=None):
        """Stop listening for messages with the specified ``topic``.

        The ``topic``, the ``listener``, and the ``key`` must match the
        values passed to `subscribe` earlier.
        """
        for wrapper in self._listeners[key]:
            if wrapper.wraps(listener, topic):
                wrapper.unsubscribe()
                self._listeners[key].remove(wrapper)
                break

    def unsubscribe_all(self, key=None):
        """Unsubscribe all listeners registered with the given ``key``"""
        for wrapper in self._listeners[key]:
            wrapper.unsubscribe()
        del self._listeners[key]


class _ListenerWrapper(object):

    def __init__(self, listener, topic):
        self.listener = listener
        self.topic = self._get_topic(topic)
        WxPublisher.subscribe(self, self.topic)

    def _get_topic(self, topic):
        # DEBUG RecursionError on python 3
        # print("DEBUG: topic(%s) is %s" % (topic, type(topic)))
        if not isinstance(topic, basestring):
            topic = topic.topic
        return topic.lower()

    def wraps(self, listener, topic):
        return self.listener == listener and self.topic == self._get_topic(topic)

    def listens(self, topic):
        return self._get_topic(topic).startswith(self.topic)

    def unsubscribe(self):
        WxPublisher.unsubscribe(self, self.topic)

    def __call__(self, data):
        from .messages import RideLogException
        try:
            self.listener(data)
        except Exception as err:
            # Prevent infinite recursion if RideLogMessage listener is broken,
            if not isinstance(data, RideLogException):
                RideLogException(message='Error in listener: %s\n' \
                                         'While handling %s' % (unicode(err),
                                                                unicode(data)),
                                 exception=err, level='ERROR').publish()


"""Global `Publisher` instance for subscribing to and unsubscribing from messages."""
PUBLISHER = Publisher()
