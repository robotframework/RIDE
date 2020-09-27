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

import sys
import inspect
from pubsub import pub
from typing import Type, Callable
from robotide.publish.messages import RideMessage


class _Publisher:

    def __init__(self):
        self._publisher = pub.getDefaultPublisher()
        self._publisher.setListenerExcHandler(ListenerExceptionHandler())

    @staticmethod
    def _get_topic(topic_cls: Type[RideMessage]) -> str:
        if inspect.isclass(topic_cls) and issubclass(topic_cls, RideMessage):
            return topic_cls.topic()
        raise TypeError('Expected topic type {}, actual {}.'.format(RideMessage, topic_cls))

    @staticmethod
    def _validate_listener(listener: Callable):
        sig = inspect.signature(listener)
        params = sig.parameters
        error_msg = 'only 1 required param (message) is expected.'
        assert len(params) == 1, 'Too many listener params, ' + error_msg
        assert str(list(params.values())[0]) == 'message', 'Invalid listener param, ' + error_msg

    def subscribe(self, listener: Callable, topic: Type[RideMessage]):
        """ The listener's param signature must be (message) """
        self._validate_listener(listener)
        self._publisher.subscribe(listener, self._get_topic(topic))

    def publish(self, topic: Type[RideMessage], message):
        """ All subscribed listeners' param signatures have been guaranteed """
        self._publisher.sendMessage(self._get_topic(topic), message=message)

    def unsubscribe(self, listener: Callable, topic: Type[RideMessage]):
        self._publisher.unsubscribe(listener, self._get_topic(topic))

    def unsubscribe_all(self, obj=None):
        """ If the given object's:

            1. object method
            2. class static function
            3. class function

            is subscribed into PUBLISHER, call this method to unsubscribe all its topics.

            Unsubscribe all topics when input is None.
        """

        def _listener_filter(listener):
            _callable = listener.getCallable()
            functions = [func for _, func in inspect.getmembers(obj, inspect.isfunction)]
            methods = [method for _, method in inspect.getmembers(obj, inspect.ismethod)]
            if _callable in functions or _callable in methods:
                return True

        _listener_filter = _listener_filter if obj is not None else None
        self._publisher.unsubAll(listenerFilter=_listener_filter)


class ListenerExceptionHandler(pub.IListenerExcHandler):

    def __call__(self, listenerID: str, topicObj: pub.Topic):
        from .messages import RideLogException
        topic_name = topicObj.getName()
        if topic_name != RideLogException.topic():
            error_msg = 'Error in listener: {}, topic: {}'.format(listenerID, topic_name)
            log_message = RideLogException(message=error_msg,
                                           exception=None, level='ERROR')
            sys.stderr.write(log_message.__getattribute__('message'))
            log_message.publish()


"""Global `Publisher` instance for subscribing to and unsubscribing from RideMessages."""
PUBLISHER = _Publisher()
