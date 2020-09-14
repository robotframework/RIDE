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

import unittest
from unittest.mock import patch
from nose.tools import assert_equal, assert_raises, assert_true
from robotide.publish.messages import (RideMessage, RideLogMessage,
                                       RideLogException)
from robotide.publish.publisher import PUBLISHER


class RideTestMessage(RideMessage):
    _topic = 'My.Topic'


class RideTestMessageWithAttrs(RideMessage):
    data = ['foo', 'bar']


class RideSubTestMessageWithAttrs(RideTestMessageWithAttrs):
    _topic = 'My.Topic.With.Attrs'
    data = ['foo', 'bar', 'test']


class RideSubTestMessageWithAttrsChild(RideSubTestMessageWithAttrs):
    pass


class RideTestMessageWithLongName(RideMessage):
    pass


class RideSubTestMessage(RideTestMessage):
    pass


class RideNoneTopicTestMessage(RideTestMessage):
    _topic = None
    pass


class TestMessage(unittest.TestCase):

    def test_topic(self):
        assert_equal(RideMessage.topic(), 'ride')
        assert_equal(RideTestMessage.topic(), 'my.topic')
        assert_equal(RideTestMessageWithLongName.topic(),
                     'ride.test.message.with.long.name')

    def test_sub_topic(self):
        assert_equal(RideSubTestMessage.topic(), 'my.topic')
        assert_equal(RideNoneTopicTestMessage.topic(), 'ride.none.topic.test')
        assert_equal(RideTestMessageWithAttrs.topic(),
                     'ride.test.message.with.attrs')
        assert_equal(RideSubTestMessageWithAttrs.topic(),
                     'my.topic.with.attrs')

    def test_all_attributes_given(self):
        msg = RideTestMessageWithAttrs(foo='bar', bar='foo')
        assert_equal(msg.foo, 'bar')
        assert_equal(msg.bar, 'foo')

    def test_all_attributes_override(self):
        msg = RideSubTestMessageWithAttrs(foo='bar', bar='foo', test=None)
        assert_equal(msg.foo, 'bar')
        assert_equal(msg.bar, 'foo')
        assert_equal(msg.test, None)

    def test_all_attributes_inherit(self):
        msg = RideSubTestMessageWithAttrsChild(foo='bar', bar='foo', test=None)
        assert_equal(msg.foo, 'bar')
        assert_equal(msg.bar, 'foo')
        assert_equal(msg.test, None)

    def test_missing_mandatory_attribute(self):
        assert_raises(TypeError, RideTestMessageWithAttrs, foo='bar')

    def test_missing_many_mandatory_attributes(self):
        assert_raises(TypeError, RideTestMessageWithAttrs)

    def test_no_such_attribute_should_fail(self):
        assert_raises(TypeError, RideTestMessageWithAttrs, foo='', bar='',
                      quux='camel')


class TestRideLogMessage(unittest.TestCase):

    def test_log_message(self):
        msg = RideLogMessage(message='Some error text', level='ERROR')
        assert_equal(msg.message, 'Some error text')
        assert_equal(msg.level, 'ERROR')
        assert_true(msg.timestamp.startswith('20'))

    def test_log_exception(self):
        try:
            1 / 0
        except Exception as err:
            msg = RideLogException(
                message='Some error text', exception=err, level='ERROR')
            assert_true(msg.message.startswith(
                'Some error text\n\nTraceback (most recent call last):'))
            assert_equal(msg.level, 'ERROR')
            assert_true(msg.timestamp.startswith('20'))


def _common_listener(message):
    TestPublisher.cls_msg = message
    TestPublisher.cls_msgs.append(message)


def _invalid_common_listener(message=None):
    pass


class DummyClass:

    def __init__(self):
        PUBLISHER.subscribe(self._dummy_listener, RideTestMessageWithAttrs)

    def _dummy_listener(self, message):
        TestPublisher.cls_msg = message
        TestPublisher.cls_msgs.append('_dummy_listener, {}'.format(message))


class TestPublisher(unittest.TestCase):
    cls_msg = ''
    cls_msgs = list()

    def setUp(self):
        self._msg = ''
        TestPublisher.cls_msg = ''
        TestPublisher.cls_msgs.clear()
        PUBLISHER.unsubscribe_all()
        PUBLISHER._publisher.getTopicMgr().clearTree()

    def test_invalid_topic(self):
        assert_raises(TypeError, PUBLISHER.subscribe, self._listener, 'test.message1')
        assert_raises(TypeError, PUBLISHER.subscribe, self._listener, TestPublisher)
        assert_raises(TypeError, PUBLISHER.subscribe, self._listener, None)
        assert_raises(TypeError, PUBLISHER.subscribe, self._listener, list)

    def test_invalid_listener(self):
        assert_raises(AssertionError, PUBLISHER.subscribe, self._invalid_listener_empty_arg, RideTestMessage)
        assert_raises(AssertionError, PUBLISHER.subscribe, self._invalid_listener_long_arg, RideTestMessage)
        assert_raises(AssertionError, PUBLISHER.subscribe, self._invalid_listener_many_args, RideTestMessage)
        assert_raises(AssertionError, PUBLISHER.subscribe, self._invalid_listener_non_required_arg, RideTestMessage)
        assert_raises(AssertionError, PUBLISHER.subscribe, self._invalid_listener_wrong_arg, RideTestMessage)
        assert_raises(AssertionError, PUBLISHER.subscribe, self._invalid_listener_wrong_arg, 'RideTestMessage')
        assert_raises(AssertionError, PUBLISHER.subscribe, self._invalid_listener_static, RideTestMessage)
        assert_raises(AssertionError, PUBLISHER.subscribe, self._invalid_listener_class_method, RideTestMessage)
        assert_raises(AssertionError, PUBLISHER.subscribe, _invalid_common_listener, RideTestMessage)

    def test_publishing_ride_message(self):
        PUBLISHER.subscribe(self._listener, RideMessage)
        PUBLISHER.publish(RideTestMessageWithAttrs, 'content3')
        assert_equal(self._msg, 'content3')

    def test_publishing_invalid_topic(self):
        PUBLISHER.subscribe(self._listener, RideMessage)
        assert_raises(TypeError, PUBLISHER.publish, 'RideTestMessageWithAttrs', 'content3')
        assert_equal(self._msg, '')

    def test_publishing_ride_message_from_msg_obj(self):
        PUBLISHER.subscribe(self._listener, RideMessage)
        msg_obj = RideMessage()
        msg_obj.publish()
        assert_equal(self._msg, msg_obj)

    def test_publishing_ride_message_with_args(self):
        PUBLISHER.subscribe(self._listener, RideMessage)
        msg_obj = RideTestMessageWithAttrs(foo='bar', bar='foo')
        msg_obj.publish()
        assert_equal(self._msg, msg_obj)
        assert_equal(self._msg.foo, 'bar')
        assert_equal(self._msg.bar, 'foo')

    def test_publishing_common_listener(self):
        PUBLISHER.subscribe(_common_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(TestPublisher.cls_msg, msg_obj)

    def test_unsubscribe_ride_message(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.unsubscribe(self._listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(self._msg, '')

    def test_unsubscribe_ride_message_publish(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.unsubscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.publish(RideTestMessageWithAttrs, 'test')
        assert_equal(self._msg, '')

    def test_unsubscribe_invalid_topic(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        assert_raises(TypeError, PUBLISHER.unsubscribe, self._listener, 'RideTestMessageWithAttrs')
        PUBLISHER.publish(RideTestMessageWithAttrs, 'test')
        assert_equal(self._msg, 'test')

    def test_subscribe_multi_listeners(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(_common_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 4)

    def test_subscribe_multi_listeners_publish(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(_common_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        PUBLISHER.publish(RideTestMessageWithAttrs, 'test')
        assert_equal(len(TestPublisher.cls_msgs), 4 * 2)

    def test_subscribe_multi_listeners_inherit_topic(self):
        PUBLISHER.subscribe(self._listener, RideMessage)
        PUBLISHER.subscribe(_common_listener, RideMessage)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        PUBLISHER.publish(RideTestMessageWithAttrs, 'test')
        assert_equal(len(TestPublisher.cls_msgs), 4 * 2)

    @patch('robotide.context.LOG.error')
    def test_subscribe_broken_listener(self, p_log):
        PUBLISHER.subscribe(self._broken_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(self._msg, msg_obj)
        p_log.assert_called_once()

    @patch('robotide.context.LOG.error')
    def test_subscribe_broken_listener_ride_log(self, p_log):
        PUBLISHER.subscribe(self._broken_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._listener, RideLogException)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        p_log.assert_called_once()
        assert_true(isinstance(self._msg, RideLogException))
        assert_equal(len(TestPublisher.cls_msgs), 2)

    @patch('robotide.context.LOG.error')
    def test_subscribe_broken_listener_ride_log_broken(self, p_log):
        PUBLISHER.subscribe(self._broken_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._broken_listener, RideLogException)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        p_log.assert_called_once()
        assert_true(isinstance(self._msg, RideLogException))
        assert_equal(len(TestPublisher.cls_msgs), 2)

    def test_unsubscribe_all(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 3)
        PUBLISHER.unsubscribe_all(self)
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 3)

    def test_unsubscribe_all_only_input_obj(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(_common_listener, RideTestMessageWithAttrs)
        dummy_obj = DummyClass()
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 5)
        PUBLISHER.unsubscribe_all(self)
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 7)

    def test_unsubscribe_all_exclude_common(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(_common_listener, RideTestMessageWithAttrs)
        dummy_obj = DummyClass()
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 5)
        PUBLISHER.unsubscribe_all(dummy_obj)
        PUBLISHER.unsubscribe_all(self)
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 6)

    def test_unsubscribe_all_invalid_input(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(_common_listener, RideTestMessageWithAttrs)
        dummy_obj = DummyClass()
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 5)
        PUBLISHER.unsubscribe_all('dummy_obj')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 5 * 2)

    def test_unsubscribe_all_input_none(self):
        PUBLISHER.subscribe(self._listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        PUBLISHER.subscribe(_common_listener, RideTestMessageWithAttrs)
        dummy_obj = DummyClass()
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 5)
        PUBLISHER.unsubscribe_all()
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 5)

    def test_subscribe_obj_weak_ref(self):
        dummy_obj = DummyClass()
        dummy_obj = DummyClass()
        dummy_obj = DummyClass()
        dummy_obj = DummyClass()
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(len(TestPublisher.cls_msgs), 1)

    def test_subscribe_static_method(self):
        PUBLISHER.subscribe(self._static_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(TestPublisher.cls_msg, msg_obj)

    def test_subscribe_class_method(self):
        PUBLISHER.subscribe(self._class_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(TestPublisher.cls_msg, msg_obj)

    def test_subscribe_common_method(self):
        PUBLISHER.subscribe(_common_listener, RideTestMessageWithAttrs)
        msg_obj = RideTestMessageWithAttrs(foo='one', bar='two')
        msg_obj.publish()
        assert_equal(TestPublisher.cls_msg, msg_obj)

    def _listener(self, message):
        self._msg = message
        TestPublisher.cls_msgs.append('_listener, {}'.format(message))

    def _invalid_listener_wrong_arg(self, event):
        pass

    def _invalid_listener_non_required_arg(self, message=None):
        pass

    def _invalid_listener_long_arg(self, message, foo=None):
        pass

    def _invalid_listener_many_args(self, message, foo, bar):
        pass

    def _invalid_listener_empty_arg(self):
        pass

    @staticmethod
    def _invalid_listener_static():
        pass

    @classmethod
    def _invalid_listener_class_method(cls):
        pass

    def _listener_multi_args(self, foo, bar):
        self._msg = foo
        TestPublisher.cls_msgs.append('_listener_multi_args, {}, {}'.format(foo, bar))

    def _broken_listener(self, message):
        self._msg = message
        TestPublisher.cls_msgs.append('_broken_listener, {}'.format(message))
        raise RuntimeError(message)

    @staticmethod
    def _static_listener(message):
        TestPublisher.cls_msg = message
        TestPublisher.cls_msgs.append('_static_listener, {}'.format(message))

    @classmethod
    def _class_listener(cls, message):
        cls.cls_msg = message
        TestPublisher.cls_msgs.append('_class_listener, {}'.format(message))


if __name__ == '__main__':
    unittest.main()
