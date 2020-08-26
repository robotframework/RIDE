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

import inspect
from pubsub import pub


class _Publisher(object):

    def __init__(self):
        self._publisher = pub.getDefaultPublisher()
        self._publisher.setListenerExcHandler(ListenerExceptionHandler())

    @staticmethod
    def _get_topic(topic):
        if not isinstance(topic, str):
            topic = topic.topic
        return topic

    def publish(self, topic, data):
        self._publisher.sendMessage(self._get_topic(topic), message=data)

    def subscribe(self, listener, topic):
        self._publisher.subscribe(listener, self._get_topic(topic))

    def unsubscribe(self, listener, topic):
        self._publisher.unsubscribe(listener, self._get_topic(topic))

    def unsubscribe_all(self, obj):
        """ If the given object's:

            1. object method
            2. class static function
            3. class function

            is subscribed into PUBLISHER, call this method to unsubscribe all its topics.
        """

        def _listener_filter(listener):
            _callable = listener.getCallable()
            functions = [func for _, func in inspect.getmembers(obj, inspect.isfunction)]
            methods = [method for _, method in inspect.getmembers(obj, inspect.ismethod)]
            if _callable in functions or _callable in methods:
                return True

        self._publisher.unsubAll(listenerFilter=_listener_filter)


class ListenerExceptionHandler(pub.IListenerExcHandler):

    def __call__(self, listenerID: str, topicObj: pub.Topic):
        from .messages import RideLogException
        topic_name = topicObj.getName()
        if topic_name != RideLogException:
            error_msg = 'Error in listener: {}, topic: {}'.format(listenerID, topic_name)
            RideLogException(message=error_msg,
                             exception=None, level='ERROR').publish()


"""Global `Publisher` instance for subscribing to and unsubscribing from messages."""
PUBLISHER = _Publisher()
