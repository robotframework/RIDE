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

from wx.lib.pubsub import Publisher as WxPublisher


class Publisher(object):

    def __init__(self):
        self._listeners = {}

    def subscribe(self, listener, topic, key=None):
        wrapper = _ListenerWrapper(listener, topic)
        self._listeners.setdefault(key, []).append(wrapper)

    def unsubscribe(self, listener, topic, key=None):
        for wrapper in self._listeners[key]:
            if wrapper.wraps(listener, topic):
                wrapper.unsubscribe()
                self._listeners[key].remove(wrapper)
                break

    def unsubscribe_all(self, key):
        for wrapper in self._listeners[key]:
            wrapper.unsubscribe()
        del self._listeners[key]


class _ListenerWrapper(object):

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
        self.listener(event.data)
