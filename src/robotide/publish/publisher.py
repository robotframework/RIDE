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
import types
from pubsub import pub
from typing import Type, Callable
from ..publish.messages import RideMessage


class _Publisher:

    def __init__(self):
        self.publisher = pub.getDefaultPublisher()
        self.publisher.setListenerExcHandler(ListenerExceptionHandler())

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
        assert str(list(params.values())[0]) in ['message', 'data'], 'Invalid listener param, ' + error_msg

    def subscribe(self, listener: Callable, topic: Type[RideMessage]):
        """ The listener's param signature must be (message) """
        self._validate_listener(listener)
        self.publisher.subscribe(listener, self._get_topic(topic))

    def publish(self, topic: Type[RideMessage], message):
        """ All subscribed listeners' param signatures have been guaranteed """
        self.publisher.sendMessage(self._get_topic(topic), message=message)

    def unsubscribe(self, listener: Callable, topic: Type[RideMessage]):
        self.publisher.unsubscribe(listener, self._get_topic(topic))

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
            functions = [func for _, func in _get_members_safely(obj, inspect.isfunction)]
            methods = [method for _, method in _get_members_safely(obj, inspect.ismethod)]
            if _callable in functions or _callable in methods:
                return True

        _listener_filter = _listener_filter if obj is not None else None
        self.publisher.unsubAll(listenerFilter=_listener_filter)


class ListenerExceptionHandler(pub.IListenerExcHandler):

    def __call__(self, listener_id: str, topic_obj: pub.Topic):
        from .messages import RideLogException
        topic_name = topic_obj.getName()
        if topic_name != RideLogException.topic():
            error_msg = 'Error in listener: {}, topic: {}'.format(listener_id, topic_name)
            log_message = RideLogException(message=error_msg,
                                           exception=None, level='ERROR')
            sys.stderr.write(log_message.__getattribute__('message'))
            log_message.publish()


def _get_members_safely(obj, predicate=None):
    """Return all members of an object as (name, value) pairs sorted by name.
    Optionally, only return members that satisfy a given predicate.

    Copied from inspect.getmembers().

    Added protection logic to bypass unexpected exceptions in object attribute iterations.
    """
    if inspect.isclass(obj):
        mro = (obj,) + inspect.getmro(obj)
    else:
        mro = ()
    results = []
    processed = set()
    names = dir(obj)
    # :dd any DynamicClassAttributes to the list of names if object is a class;
    # this may result in duplicate entries if, for example, a virtual
    # attribute with the same name as a DynamicClassAttribute exists
    try:
        for base in obj.__bases__:
            for k, v in base.__dict__.items():
                if isinstance(v, types.DynamicClassAttribute):
                    names.append(k)
    except AttributeError:
        pass
    for key in names:
        # First try to get the value via getattr.  Some descriptors don't
        # like calling their __get__ (see bug #1785), so fall back to
        # looking in the __dict__.
        try:
            value = getattr(obj, key)
            # handle the duplicate key
            if key in processed:
                raise AttributeError
        except Exception as e:
            """ UPDATED HERE: Catch all types of exceptions. """
            if isinstance(e, AttributeError):
                """ UPDATED HERE: Use old logic if exception is AttributeError. """
                for base in mro:
                    if key in base.__dict__:
                        value = base.__dict__[key]
                        break
                else:
                    # could be a (currently) missing slot member, or a buggy
                    # __dir__; discard and move on
                    continue
            else:
                """ UPDATED HERE: Ignore this attribute when other types of exception raised. """
                continue
        if not predicate or predicate(value):
            results.append((key, value))
        processed.add(key)
    results.sort(key=lambda pair: pair[0])
    return results


"""Global `Publisher` instance for subscribing to and unsubscribing from RideMessages."""
PUBLISHER = _Publisher()
