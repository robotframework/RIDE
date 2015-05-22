#  Copyright 2008-2015 Nokia Solutions and Networks
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

from wx.lib.pubsub import Publisher as WxPublisher

from messages import RideLogException


class Publisher(object):

    def __init__(self):
        self._listeners = {}

    def publish(self, topic, data):
        WxPublisher().sendMessage(topic, data)

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


class _ListenerWrapper:
    # Must be an old-style class because wxPython's pubsub doesn't handle
    # new-style classes in 2.8.7.1. Newer versions have that bug fixed.

    def __init__(self, listener, topic):
        self.listener = listener
        self.topic = self._get_topic(topic)
        WxPublisher().subscribe(self, self.topic)

    def _get_topic(self, topic):
        if not isinstance(topic, basestring):
            topic = topic.topic
        return topic.lower()

    def wraps(self, listener, topic):
        return self.listener == listener and self.topic == self._get_topic(topic)

    def unsubscribe(self):
        WxPublisher().unsubscribe(self, self.topic)

    def __call__(self, event):
        try:
            self.listener(event.data)
        except Exception, err:
            # Prevent infinite recursion if RideLogMessage listener is broken,
            if not isinstance(event.data, RideLogException):
                RideLogException(message='Error in listener: %s\n' \
                                         'While handling %s' % (unicode(err),
                                                                unicode(event.data)),
                                 exception=err, level='ERROR').publish()
